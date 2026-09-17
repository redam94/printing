#!/usr/bin/env python
"""Publish the customer help space (Confluence) from Markdown in ``docs/help/``.

    uv run python scripts/confluence.py                 # what would change
    uv run python scripts/confluence.py push            # create/update every page
    uv run python scripts/confluence.py push --only prices-and-turnaround
    uv run python scripts/confluence.py list            # pages in the space right now

``docs/help/*.md`` is the source of truth: one file per page, front matter (``title:``,
``order:``, ``summary:``) then Markdown. Pages are matched to Confluence by title, created
under the space home when missing and updated in place otherwise, so running twice is a no-op.
Numbers in the text come from the repo, not from the prose: ``{price.design_fee}``,
``{printer.bed}``, ``{portal}`` and friends are filled in from ``tickets/pricing.json``,
``scripts/_common.PRINTER``, ``tickets/jira.json`` and ``site.json``.

The look follows the Augur design system used by the public site and the quotes: cream panels,
hairline borders, sage headings, JetBrains-style monospace for numbers. Confluence allows no
stylesheet of its own, so the styling is what storage format supports: panel macros with
explicit colours, coloured heading text and highlighted table headers.

Markdown supported: #/##/### headings, paragraphs, **bold**, *italic*, `code`, [links](url),
- and 1. lists (one level), tables with a header row, ``` code blocks, --- rules, and
::: panel / tip / warn / quote blocks (closed by :::), and [[children]] for the page tree.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import jira_api  # noqa: E402
from scripts._common import PRINTER, ROOT  # noqa: E402

DOCS = ROOT / "docs" / "help"
SPACE_KEY = "PRINTHELP"

# Augur tokens (Claude Design), the same values as the site and the quote e-mails
INK = "#2a3528"
SAGE = "#5a7a3a"
CREAM = "#faf8f3"
WELL = "#f3f0e6"
LINE = "#e8e4d5"
PANELS = {                       # ::: name -> (background, border, default title)
    "panel": (CREAM, LINE, ""),
    "tip": (WELL, SAGE, "Worth knowing"),
    "warn": ("#f4e3df", "#a04535", "Read this before you confirm"),
    "quote": (WELL, LINE, ""),
}


# ---------------------------------------------------------------- values from the repo

def values() -> dict[str, str]:
    pricing = json.loads((ROOT / "tickets" / "pricing.json").read_text(encoding="utf-8"))
    jira = json.loads((ROOT / "tickets" / "jira.json").read_text(encoding="utf-8"))
    site_cfg = json.loads((ROOT / "site.json").read_text(encoding="utf-8")) if (ROOT / "site.json").exists() else {}
    site = (jira.get("site") or "").rstrip("/")
    bed = PRINTER["bed"]
    cur = pricing.get("currency", "USD")

    def m(x, cents=True):
        return (f"${x:,.2f}" if cents else f"${x:,.0f}") if cur == "USD" else f"{x:,.2f} {cur}"

    v = {
        "portal": f"{site}/servicedesk/customer/portal/{jira['service_desk_id']}" if site and jira.get("service_desk_id") else "",
        "site": "https://redam94.github.io/printing/",
        "brand": site_cfg.get("brand", "3D Printing Service"),
        "printer.name": PRINTER["name"],
        "printer.bed": f"{bed[0]:.0f} × {bed[1]:.0f} × {bed[2]:.0f} mm",
        "printer.bed_short": f"{bed[0]:.0f} mm",
        "printer.nozzle": f"{PRINTER['nozzle']:g} mm",
        "printer.layer": "0.2 mm",
        "printer.toolheads": str(PRINTER["toolheads"]),
        "price.design_fee": m(pricing["design_fee"], cents=False),
        "price.min_charge": m(pricing["min_charge"], cents=False),
        "price.machine_per_h": m(pricing["machine_per_h"]),
        "price.labor_per_h": m(pricing["labor_per_h"], cents=False),
        "price.setup_min": str(pricing["setup_min"]),
        "price.post_min": str(pricing["post_min_per_part"]),
        "price.queue_days": str(pricing["queue_days"]),
        "price.margin": f"{pricing['margin'] * 100:g}%",
        "price.shell": f"{pricing['shell_mm']:g} mm",
        "price.infill": f"{pricing['infill'] * 100:g}%",
        "price.hours_per_day": str(pricing["hours_per_day"]),
    }
    for name, mat in pricing["materials"].items():
        v[f"price.{name.lower()}_kg"] = m(mat["cost_per_kg"], cents=False)
    return v


def fill(text: str, vals: dict[str, str]) -> str:
    def sub(mo):
        key = mo.group(1)
        if key not in vals:
            raise SystemExit(f"unknown placeholder {{{key}}}")
        return vals[key]
    return re.sub(r"\{([a-z][a-z0-9_.]*)\}", sub, text)


# ---------------------------------------------------------------- markdown -> storage format

def inline(text: str) -> str:
    """Escape, then apply `code`, **bold**, *italic*, [text](url) and the mono/number styling."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", lambda m: f'<code>{m.group(1)}</code>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", out)
    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', out)
    return out


def heading(level: int, text: str) -> str:
    colour = SAGE if level == 2 else INK
    return f'<h{level}><span style="color: {colour};">{inline(text)}</span></h{level}>'


def table(rows: list[list[str]]) -> str:
    head, body = rows[0], rows[1:]
    th = "".join(f'<th style="background-color: {WELL};"><strong>{inline(c)}</strong></th>' for c in head)
    trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
    return f"<table data-layout=\"default\"><tbody><tr>{th}</tr>{trs}</tbody></table>"


def panel(kind: str, title: str, inner: str) -> str:
    bg, border, default_title = PANELS[kind]
    title = title or default_title
    params = [f'<ac:parameter ac:name="bgColor">{bg}</ac:parameter>',
              f'<ac:parameter ac:name="borderColor">{border}</ac:parameter>',
              '<ac:parameter ac:name="borderStyle">solid</ac:parameter>',
              '<ac:parameter ac:name="borderWidth">1</ac:parameter>']
    if title:
        params += [f'<ac:parameter ac:name="title">{html.escape(title)}</ac:parameter>',
                   f'<ac:parameter ac:name="titleBGColor">{bg}</ac:parameter>']
    return ('<ac:structured-macro ac:name="panel" ac:schema-version="1">' + "".join(params)
            + f"<ac:rich-text-body>{inner}</ac:rich-text-body></ac:structured-macro>")


BLOCK_START = re.compile(r"^(#|\||:::|```|---$|\d+\.\s|[-*]\s)")   # a line that starts a new block, never a paragraph continuation


def to_storage(md: str) -> str:
    """The Markdown subset in docs/help -> Confluence storage format."""
    out: list[str] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith(":::"):                                    # panel block
            spec = s[3:].strip().split(" ", 1)
            kind = spec[0] or "panel"
            title = spec[1] if len(spec) > 1 else ""
            body, i = [], i + 1
            while i < len(lines) and lines[i].strip() != ":::":
                body.append(lines[i])
                i += 1
            i += 1
            out.append(panel(kind if kind in PANELS else "panel", title, to_storage("\n".join(body))))
            continue
        if s.startswith("```"):                                    # code block
            lang = s[3:].strip()
            body, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            code = "\n".join(body)
            if "]]>" in code:
                out.append(f"<pre>{html.escape(code)}</pre>")
            else:
                out.append('<ac:structured-macro ac:name="code" ac:schema-version="1">'
                           + (f'<ac:parameter ac:name="language">{lang}</ac:parameter>' if lang else "")
                           + f"<ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>")
            continue
        if s == "[[children]]":                                     # the space's page tree, maintained by Confluence
            out.append('<ac:structured-macro ac:name="children" ac:schema-version="2">'
                       '<ac:parameter ac:name="all">true</ac:parameter>'
                       '<ac:parameter ac:name="excerpt">simple</ac:parameter></ac:structured-macro>')
            i += 1
            continue
        if s == "---":
            out.append("<hr />")
            i += 1
            continue
        if s.startswith("#"):
            level = len(s) - len(s.lstrip("#"))
            out.append(heading(min(max(level, 2), 4), s.lstrip("# ").strip()))
            i += 1
            continue
        if s.startswith("|"):                                      # table
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells):
                    rows.append(cells)
                i += 1
            out.append(table(rows))
            continue
        if re.match(r"^(\d+\.|[-*])\s", s):                        # list (one level)
            ordered = bool(re.match(r"^\d+\.", s))
            items = []
            while i < len(lines) and re.match(r"^(\d+\.|[-*])\s", lines[i].strip()):
                items.append(re.sub(r"^(\d+\.|[-*])\s+", "", lines[i].strip()))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        para = [s]                                                  # paragraph: this line, then any plain ones
        i += 1
        while i < len(lines) and lines[i].strip() and not BLOCK_START.match(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "".join(out)


# ---------------------------------------------------------------- pages

def read_docs(vals: dict[str, str]) -> list[dict]:
    pages = []
    for path in sorted(DOCS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta: dict[str, str] = {}
        if text.startswith("---\n"):
            fm, _, text = text[4:].partition("\n---\n")
            for line in fm.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
        body = fill(text, vals)
        pages.append({"slug": path.stem, "title": fill(meta.get("title") or path.stem, vals),
                      "order": int(meta.get("order") or 99), "home": meta.get("home", "").lower() == "true",
                      "summary": fill(meta.get("summary", ""), vals), "storage": to_storage(body)})
    return sorted(pages, key=lambda p: (not p["home"], p["order"]))


def client():
    creds = jira_api.credentials()
    if not creds:
        raise SystemExit("no Atlassian credentials: set JIRA_SITE, JIRA_EMAIL and JIRA_API_TOKEN (or CONFLUENCE_*) in .env")
    return jira_api.JiraClient(**creds)


def space(c) -> dict:
    res = (c.call("GET", "/wiki/api/v2/spaces", params={"keys": SPACE_KEY, "limit": 5}) or {}).get("results") or []
    if not res:
        raise SystemExit(f"no Confluence space {SPACE_KEY} on {c.site}")
    return res[0]


def existing(c, space_id: str) -> dict[str, dict]:
    """Every page in the space by title (the v2 API pages a cursor in the _links.next query)."""
    import urllib.parse
    out: dict[str, dict] = {}
    cursor = None
    while True:
        page = c.call("GET", f"/wiki/api/v2/spaces/{space_id}/pages",
                      params={"limit": 100, "body-format": "storage", "cursor": cursor}) or {}
        for p in page.get("results", []):
            out[p["title"]] = p
        nxt = (page.get("_links") or {}).get("next") or ""
        q = urllib.parse.parse_qs(urllib.parse.urlparse(nxt).query)
        nxt_cursor = (q.get("cursor") or [""])[0]
        if not nxt_cursor or nxt_cursor == cursor:
            return out
        cursor = nxt_cursor


def normalise(body: str) -> str:
    """Confluence rewrites what it stores (hex colours as rgb(), characters as entities, macro ids
    it assigns). Compare pages through this, or every run would rewrite every page."""
    out = html.unescape(body)
    out = re.sub(r"\s*ac:(macro-id|local-id)=\"[^\"]*\"", "", out)
    out = re.sub(r"#([0-9a-fA-F]{6})\b",
                 lambda m: "rgb(%d,%d,%d)" % tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)), out)
    out = re.sub(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", r"rgb(\1,\2,\3)", out)
    # Confluence also reorders a macro's parameters
    out = re.sub(r"(?:<ac:parameter\b[^>]*>.*?</ac:parameter>\s*){2,}",
                 lambda m: "".join(sorted(re.findall(r"<ac:parameter\b[^>]*>.*?</ac:parameter>", m.group(0)))), out)
    return re.sub(r"\s+", " ", out).strip()


def push(only: str = "", dry_run: bool = False) -> int:
    vals = values()
    docs = read_docs(vals)
    if not docs:
        raise SystemExit(f"no pages in {DOCS}")
    c = client()
    sp = space(c)
    live = existing(c, sp["id"])
    home_id = sp.get("homepageId")
    changed = 0
    for d in docs:
        if only and only not in (d["slug"], d["title"]):
            continue
        cur = live.get(d["title"])
        body = d["storage"]
        if cur and normalise((cur.get("body", {}).get("storage", {}) or {}).get("value", "")) == normalise(body):
            print(f"  = {d['title']}")
            continue
        changed += 1
        verb = "update" if cur else "create"
        print(f"  {verb[0].upper()} {d['title']}" + (f"  ({len(body)} chars)" if not dry_run else "  [dry run]"))
        if dry_run:
            continue
        if cur:
            c.call("PUT", f"/wiki/api/v2/pages/{cur['id']}", body={
                "id": cur["id"], "status": "current", "title": d["title"],
                "body": {"representation": "storage", "value": body},
                "version": {"number": cur["version"]["number"] + 1, "message": "synced from docs/help"}})
        else:
            new = c.call("POST", "/wiki/api/v2/pages", body={
                "spaceId": sp["id"], "status": "current", "title": d["title"],
                "parentId": None if d["home"] else home_id,
                "body": {"representation": "storage", "value": body}}) or {}
            live[d["title"]] = new
    print(f"{changed} page(s) {'would change' if dry_run else 'written'} in {SPACE_KEY} — {c.site}/wiki/spaces/{SPACE_KEY}")
    return 0


def show_list() -> int:
    c = client()
    sp = space(c)
    for title, p in sorted(existing(c, sp["id"]).items(), key=lambda kv: kv[1].get("parentId") or ""):
        body = (p.get("body", {}).get("storage", {}) or {}).get("value", "")
        print(f"{p['id']:>8}  v{p['version']['number']:<3} {len(body):>6} chars  {title}")
    print(f"{c.site}/wiki/spaces/{SPACE_KEY}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="dry-run", choices=["dry-run", "push", "list"])
    ap.add_argument("--only", default="", help="one page by slug or title")
    a = ap.parse_args()
    if a.cmd == "list":
        return show_list()
    return push(only=a.only, dry_run=a.cmd == "dry-run")


if __name__ == "__main__":
    raise SystemExit(main())
