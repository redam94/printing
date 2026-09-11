"""A small Jira Cloud client for the design request tickets (scripts/tickets.py), stdlib only.

Jira Service Management (JSM) is the front door: its customer portal is the request form, its
project settings decide who may see that form (anyone, or only customers you add), the people
raising requests need no Jira licence, and JSM e-mails them every public comment — including the
quote and its attachments — and files their e-mail replies back as comments on the request.

Configuration: ``tickets/jira.json`` (committed, no secrets) and three environment variables:

    JIRA_SITE=https://<your-site>.atlassian.net
    JIRA_EMAIL=<the Atlassian account that owns the API token>
    JIRA_API_TOKEN=<https://id.atlassian.com/manage-profile/security/api-tokens>

tickets/jira.json:

    {"project": "PRINT",                     # the JSM project key
     "service_desk_id": "",                  # resolved from the project by `tickets.py jira check`
     "request_type": "",                     # optional: only pull requests of this type
     "jql": "",                              # optional: replaces the default `project = <key>` search
     "transitions": {"designing": ["Start progress", "In progress"],
                     "quoted": ["Respond to customer", "Waiting for customer"],
                     "changes": ["Back to support", "Waiting for support"],
                     "approved": ["Approved", "Approve"],
                     "printing": ["Printing", "In progress"],
                     "done": ["Resolve this issue", "Done", "Resolved", "Close"],
                     "declined": ["Cancel request", "Cancel", "Declined", "Won't do"]},
     "field_labels": {"Sizes": "dimensions"}}   # extra portal field label -> request field key

Every function that talks to Jira takes a ``JiraClient``; ``JiraClient(transport=...)`` accepts a
callable ``(method, url, headers, body_bytes) -> (status, body_bytes)`` so tests can run without a
network.  Everything else is plain dicts, so scripts/tickets.py never sees an HTTP call.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Callable

Transport = Callable[[str, str, dict, bytes | None], tuple[int, bytes]]

DEFAULT_TRANSITIONS = {
    "designing": ["Start progress", "In progress"],
    "quoted": ["Respond to customer", "Waiting for customer"],
    "changes": ["Back to support", "Waiting for support"],
    "approved": ["Approved", "Approve"],
    "printing": ["Printing", "In progress"],
    "done": ["Resolve this issue", "Done", "Resolved", "Close"],
    "declined": ["Cancel request", "Cancel", "Declined", "Won't do"],
}


class JiraError(RuntimeError):
    pass


def credentials() -> dict | None:
    site = os.environ.get("JIRA_SITE", "").strip().rstrip("/")
    email = os.environ.get("JIRA_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()
    return {"site": site, "email": email, "token": token} if site and email and token else None


def _urllib_transport(method: str, url: str, headers: dict, body: bytes | None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class JiraClient:
    def __init__(self, site: str, email: str, token: str, transport: Transport | None = None):
        self.site = site.rstrip("/")
        self.auth = "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()
        self.transport = transport or _urllib_transport
        self._me: dict | None = None

    # -- transport -------------------------------------------------------------------------
    def call(self, method: str, path: str, params: dict | None = None, body: dict | None = None,
             raw: tuple[bytes, str] | None = None, ok: tuple[int, ...] = (200, 201, 204)) -> dict | list | None:
        url = self.site + path + (("?" + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})) if params else "")
        headers = {"Authorization": self.auth, "Accept": "application/json"}
        data = None
        if raw is not None:
            data, headers["Content-Type"] = raw
            headers["X-Atlassian-Token"] = "no-check"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        status, out = self.transport(method, url, headers, data)
        if status not in ok:
            raise JiraError(f"{method} {path} -> HTTP {status}: {out[:300].decode('utf-8', 'replace')}")
        return json.loads(out) if out.strip() else None

    def get(self, path, **params):
        return self.call("GET", path, params=params or None)

    # -- identity ---------------------------------------------------------------------------
    def myself(self) -> dict:
        if self._me is None:
            self._me = self.get("/rest/api/3/myself") or {}
        return self._me

    # -- reading requests -------------------------------------------------------------------
    def search(self, jql: str, fields: str = "summary,status,created,updated,reporter,description,issuetype", limit: int = 500) -> list[dict]:
        """Issues matching a JQL, through the paginated /search/jql endpoint (the old /search is gone)."""
        issues, token = [], ""
        while True:
            page = self.get("/rest/api/3/search/jql", jql=jql, fields=fields, maxResults=100, nextPageToken=token) or {}
            issues += page.get("issues", [])
            token = page.get("nextPageToken", "")
            if not token or len(issues) >= limit:
                return issues

    def request(self, key: str) -> dict | None:
        """The JSM view of one issue: portal field values by label, reporter with e-mail, current status.  None if not a JSM request."""
        try:
            return self.get(f"/rest/servicedeskapi/request/{key}")
        except JiraError as e:
            if "HTTP 404" in str(e) or "HTTP 403" in str(e):
                return None
            raise

    def comments(self, key: str, jsm: bool = True) -> list[dict]:
        """Comments on one issue as {id, body(text), public, author{accountId, emailAddress, displayName}, created}."""
        out = []
        if jsm:
            start = 0
            while True:
                page = self.get(f"/rest/servicedeskapi/request/{key}/comment", start=start, limit=100) or {}
                for c in page.get("values", []):
                    out.append({"id": str(c.get("id")), "body": str(c.get("body") or ""), "public": bool(c.get("public", True)),
                                "author": c.get("author") or {}, "created": ((c.get("created") or {}).get("iso8601") or "")[:19]})
                if page.get("isLastPage", True) or not page.get("values"):
                    return out
                start += len(page["values"])
        page = self.get(f"/rest/api/3/issue/{key}/comment", maxResults=100) or {}
        for c in page.get("comments", []):
            out.append({"id": str(c.get("id")), "body": adf_text(c.get("body")), "public": (c.get("jsdPublic", True)),
                        "author": c.get("author") or {}, "created": str(c.get("created") or "")[:19]})
        return out

    # -- writing ----------------------------------------------------------------------------
    def add_comment(self, key: str, text: str, public: bool = True, jsm: bool = True) -> dict:
        if jsm:
            return self.call("POST", f"/rest/servicedeskapi/request/{key}/comment", body={"body": text, "public": public}) or {}
        return self.call("POST", f"/rest/api/3/issue/{key}/comment", body={"body": adf_from_text(text)}) or {}

    def attach(self, key: str, service_desk_id: str, files: list[Path], comment: str = "", public: bool = True, jsm: bool = True) -> dict:
        """Attach files so the customer can see them (JSM: temporary upload, then attach with a public comment)."""
        if not files:
            return {}
        if jsm and service_desk_id:
            body, ctype = multipart(files)
            tmp = self.call("POST", f"/rest/servicedeskapi/servicedesk/{service_desk_id}/attachTemporaryFile", raw=(body, ctype)) or {}
            ids = [t["temporaryAttachmentId"] for t in tmp.get("temporaryAttachments", [])]
            payload = {"temporaryAttachmentIds": ids, "public": public}
            if comment:
                payload["additionalComment"] = {"body": comment}
            return self.call("POST", f"/rest/servicedeskapi/request/{key}/attachment", body=payload) or {}
        body, ctype = multipart(files)
        res = self.call("POST", f"/rest/api/3/issue/{key}/attachments", raw=(body, ctype)) or []
        if comment:
            self.add_comment(key, comment, public=public, jsm=False)
        return {"attachments": res}

    def transitions(self, key: str) -> list[dict]:
        """Available transitions as {id, name, to} (to = target status name when Jira tells us)."""
        page = self.get(f"/rest/api/3/issue/{key}/transitions") or {}
        return [{"id": str(t["id"]), "name": t.get("name", ""), "to": ((t.get("to") or {}).get("name") or "")} for t in page.get("transitions", [])]

    def transition(self, key: str, wanted: list[str], comment: str = "") -> dict | None:
        """Move the issue through the first available transition whose name or target status matches `wanted` (case-insensitive)."""
        avail = self.transitions(key)
        want = [w.lower() for w in wanted]
        pick = next((t for w in want for t in avail if t["name"].lower() == w or t["to"].lower() == w), None)
        if not pick:
            return None
        body: dict = {"transition": {"id": pick["id"]}}
        if comment:
            body["update"] = {"comment": [{"add": {"body": adf_from_text(comment)}}]}
        self.call("POST", f"/rest/api/3/issue/{key}/transitions", body=body)
        return pick

    # -- discovery ------------------------------------------------------------------------
    def service_desks(self) -> list[dict]:
        page = self.get("/rest/servicedeskapi/servicedesk", limit=100) or {}
        return [{"id": str(s.get("id")), "projectKey": s.get("projectKey", ""), "projectName": s.get("projectName", "")} for s in page.get("values", [])]

    def request_types(self, service_desk_id: str) -> list[dict]:
        page = self.get(f"/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype", limit=100) or {}
        return [{"id": str(r.get("id")), "name": r.get("name", ""), "description": r.get("description", "")} for r in page.get("values", [])]

    def request_type_fields(self, service_desk_id: str, request_type_id: str) -> list[dict]:
        page = self.get(f"/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype/{request_type_id}/field") or {}
        return [{"fieldId": f.get("fieldId", ""), "name": f.get("name", ""), "required": bool(f.get("required")), "type": (f.get("jiraSchema") or {}).get("type", "")}
                for f in page.get("requestTypeFields", [])]


# ---------------------------------------------------------------- helpers

def multipart(files: list[Path], field: str = "file") -> tuple[bytes, str]:
    boundary = "----printing" + uuid.uuid4().hex
    out = bytearray()
    for p in files:
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{p.name}\"\r\n"
                f"Content-Type: {ctype}\r\n\r\n").encode()
        out += p.read_bytes() + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def adf_text(node) -> str:
    """Flatten an Atlassian Document Format tree (api/3 description and comment bodies) to plain text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(adf_text(n) for n in node)
    t = node.get("type")
    if t == "text":
        return node.get("text", "")
    if t == "hardBreak":
        return "\n"
    inner = adf_text(node.get("content", []))
    if t in ("paragraph", "heading", "listItem", "blockquote", "codeBlock", "tableRow"):
        return inner + "\n"
    if t == "tableCell" or t == "tableHeader":
        return inner.rstrip("\n") + "\t"
    return inner


def adf_from_text(text: str) -> dict:
    paras = [p for p in re.split(r"\n\s*\n", text.strip())] or [""]
    content = []
    for p in paras:
        lines = p.split("\n")
        nodes = []
        for i, ln in enumerate(lines):
            if i:
                nodes.append({"type": "hardBreak"})
            if ln:
                nodes.append({"type": "text", "text": ln})
        content.append({"type": "paragraph", "content": nodes or [{"type": "text", "text": " "}]})
    return {"type": "doc", "version": 1, "content": content}


def browse_url(site: str, key: str) -> str:
    return f"{site.rstrip('/')}/browse/{key}"


def portal_url(site: str, service_desk_id: str) -> str:
    return f"{site.rstrip('/')}/servicedesk/customer/portal/{service_desk_id}" if service_desk_id else f"{site.rstrip('/')}/servicedesk/customer/portals"


# ---------------------------------------------------------------- the pull: Jira -> plain dicts for tickets.py

def pull(client: JiraClient, cfg: dict, field_map: Callable[[str], str | None]) -> list[dict]:
    """Every request in the project as {key, url, summary, status, created, updated, reporter{name,email,accountId},
    fields{<request field key>: value}, description, comments[...], jsm}.  Pure data; tickets.py ingests it."""
    jql = cfg.get("jql") or f'project = "{cfg["project"]}" ORDER BY created ASC'
    me = client.myself().get("accountId", "")
    out = []
    for iss in client.search(jql):
        key = iss["key"]; f = iss.get("fields") or {}
        req = client.request(key)
        fields: dict[str, str] = {}
        if req:
            for fv in req.get("requestFieldValues", []):
                k = field_map(str(fv.get("label") or fv.get("fieldId") or ""))
                v = fv.get("value")
                if k and v not in (None, ""):
                    fields[k] = v if isinstance(v, str) else (v.get("value") if isinstance(v, dict) and "value" in v else json.dumps(v))
            rep = req.get("reporter") or {}
        else:
            rep = f.get("reporter") or {}
        reporter = {"name": rep.get("displayName", ""), "email": (rep.get("emailAddress") or "").lower(), "accountId": rep.get("accountId", "")}
        desc = adf_text(f.get("description")) if f.get("description") else ""
        fields.setdefault("title", f.get("summary") or "")
        if desc and "purpose" not in fields:
            fields["purpose"] = desc.strip()
        fields.setdefault("name", reporter["name"]); fields.setdefault("email", reporter["email"])
        if cfg.get("request_type") and req and str((req.get("requestType") or {}).get("name") or req.get("requestTypeId") or "") not in ("", cfg["request_type"]):
            continue
        comments = []
        for c in client.comments(key, jsm=bool(req)):
            a = c["author"]
            who = "requester" if a.get("accountId") == reporter["accountId"] or (a.get("emailAddress") or "").lower() == reporter["email"] and reporter["email"] \
                else ("me" if a.get("accountId") == me else "agent")
            comments.append({"id": c["id"], "who": who, "public": c["public"], "text": c["body"], "created": c["created"],
                             "author": a.get("displayName", ""), "email": (a.get("emailAddress") or "").lower()})
        status = ((req or {}).get("currentStatus") or {}).get("status") or ((f.get("status") or {}).get("name") or "")
        out.append({"key": key, "url": browse_url(client.site, key), "summary": f.get("summary") or "", "status": status,
                    "created": str(((req or {}).get("createdDate") or {}).get("iso8601") or f.get("created") or "")[:19],
                    "updated": str(f.get("updated") or "")[:19], "reporter": reporter, "fields": fields, "description": desc,
                    "comments": comments, "jsm": bool(req)})
    return out
