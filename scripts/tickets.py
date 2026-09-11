#!/usr/bin/env python
"""Design request tickets: the loop from "can you print me a ..." to a part on the bed.

    uv run python scripts/tickets.py                       # the board: every ticket by status and what it needs next
    uv run python scripts/tickets.py show REQ-0001         # one ticket: request, quotes, thread, history
    uv run python scripts/tickets.py new --name "Ana" --email ana@x.org --title "Drip tray" [--field key=value ...]
    uv run python scripts/tickets.py fetch                 # IMAP: new requests and replies -> .sync/tickets/mail.json
    uv run python scripts/tickets.py ingest [.sync]        # file mail.json (+ the board page's `requests` dump) into tickets/
    uv run python scripts/tickets.py quote REQ-0001 --model <project> [--material PLA] [--qty 1] [--note "..."]
    uv run python scripts/tickets.py send REQ-0001 [--dry-run]   # e-mail the latest quote (SMTP), or print the outbox
    uv run python scripts/tickets.py set REQ-0001 approved|printing|done|declined [--note "..."]
    uv run python scripts/tickets.py --html                # exports/requests.html (public form) + exports/tickets.html (board)

A ticket is a directory ``tickets/REQ-0001/`` holding ``ticket.json`` (the record: requester, the
request as they wrote it, status, every message either way, every quote, the history of status
changes) and ``quotes/r<N>/`` (one package per quote revision: ``quote.json`` with the estimate and
the rates it used, ``measurements.md``, ``email.html`` / ``email.txt`` — the message the requester
got — and, gitignored, the copied 3D viewer and render that were attached).

The person asking is outside the repo, so the channel is e-mail.  A ticket starts from a mail with
``[print request]`` in the subject (the public Request page composes one; ``tickets.py new``
files one by hand), the quote goes out with ``[REQ-0001]`` in the subject, and every reply on that
subject is a message on the ticket: ``ingest`` reads "confirm / go ahead / approved" as approval
and anything else as change notes — Claude reads both before acting.

Statuses (the board columns):

  new        filed, nobody has looked at it            -> design it (printable-parts skill), then quote
  designing  a model is being built for it             -> build, then quote
  quoted     a quote is with the requester             -> wait; fetch + ingest picks up the reply
  changes    the requester sent notes on a quote       -> revise the model, quote again
  approved   the requester confirmed a quote           -> slice models/<p>/exports/<p>.3mf and print
  printing   on the bed                                -> when it is off and checked: set done
  done       delivered / collected                     (a print report on the review page validates the components)
  declined   the requester or you stopped it

Mail needs a Gmail app password in the environment (PRINTING_MAIL_USER, PRINTING_MAIL_PASS); without
it ``send`` prints the outbox and ``fetch`` explains, and Claude does both through the Gmail connector
(the design-requests skill says how) with the same files.

**Jira mode.**  With ``tickets/jira.json`` (project key etc., see scripts/jira_api.py) and
JIRA_SITE / JIRA_EMAIL / JIRA_API_TOKEN in the environment, Jira Service Management is the front
door instead of the mailbox: the portal form is the request form (and the project's customer
permissions decide who may see it), a ticket's id is the Jira key (``PRINT-12``), ``fetch`` pulls
the requests and their comments, ``send`` posts the quote as a public comment with the viewer,
renders and measurements attached (JSM e-mails the requester; their e-mail reply lands back as a
comment), and ``set`` moves the request through the workflow.  ``tickets.py jira check`` verifies
the connection and reports how the portal fields map.  E-mail is still sent too when the SMTP
password is set, so the requester also gets the 3D viewer in their inbox.
"""
from __future__ import annotations

import argparse
import email
import email.utils
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import jira_api  # noqa: E402
from scripts._common import MODELS_DIR, ROOT, list_projects  # noqa: E402

TICKETS_DIR = ROOT / "tickets"
PRICING_JSON = TICKETS_DIR / "pricing.json"
JIRA_JSON = TICKETS_DIR / "jira.json"
PAGES_JSON = ROOT / "tickets.json"                 # URLs of the published Request page and Tickets board
TEMPLATE = Path(__file__).resolve().parent / "tickets_template.html"
OUT_REQUESTS = ROOT / "exports" / "requests.html"
OUT_BOARD = ROOT / "exports" / "tickets.html"
SYNC_DIR = ROOT / ".sync" / "tickets"

STATUSES = ("new", "designing", "quoted", "changes", "approved", "printing", "done", "declined")
NEXT = {"new": "design it: printable-parts skill, then `tickets.py quote`",
        "designing": "build the model, then `tickets.py quote <id> --model <project>`",
        "quoted": "waiting on the requester: `tickets.py fetch` + `ingest` files the reply",
        "changes": "read the notes, revise the model, quote again",
        "approved": "slice models/<p>/exports/<p>.3mf, print, `tickets.py set <id> printing`",
        "printing": "when it is off the bed and checked: `tickets.py set <id> done`",
        "done": "", "declined": ""}
REQUEST_TAG = "[print request]"
ID_RE = re.compile(r"\b((?:REQ|[A-Z][A-Z0-9]{1,9})-\d+)\b")     # REQ-0001 (mail mode) or a Jira key (PRINT-12)
REQ_RE = re.compile(r"^REQ-(\d{4,})$")
CONFIRM_RE = re.compile(r"\b(confirm(ed)?|approved?|go ahead|looks good|lgtm|yes please|please print|print it|accept(ed)?)\b", re.I)
DECLINE_RE = re.compile(r"\b(cancel|decline|no thanks|never ?mind|don'?t print|not interested|withdraw)\b", re.I)

PRINTER = {"machine": "Snapmaker U1", "bed": "270 mm cube", "nozzle": "0.4 mm", "layer": "0.2 mm",
           "toolheads": 4, "materials": ["PLA", "PETG", "TPU", "ASA"]}

# The request form: what a person fills in on the public page (and what a request mail's body lines
# are parsed into).  ``ask`` is the label on the form and in the mail; ``aliases`` other spellings.
REQUEST_FIELDS: list[dict] = [
    {"key": "name", "ask": "Your name", "required": True, "rows": 1, "aliases": ["from", "requester"],
     "hint": "", "placeholder": "Ana Ruiz"},
    {"key": "email", "ask": "Your e-mail", "required": True, "rows": 1, "aliases": ["mail", "e-mail", "reply to"],
     "hint": "The quote and every follow-up go here.", "placeholder": "ana@example.org"},
    {"key": "title", "ask": "What do you need", "required": True, "rows": 1, "aliases": ["what", "part", "subject", "request"],
     "hint": "One line, the thing not the shape.", "placeholder": "A tray that catches drips under the dish rack"},
    {"key": "purpose", "ask": "What is it for", "required": True, "rows": 3, "aliases": ["why", "use", "problem"],
     "hint": "What it holds, mounts, fixes or decorates, and where it lives.",
     "placeholder": "The rack sits on the counter next to the sink; water runs out under it and pools."},
    {"key": "dimensions", "ask": "Sizes it must fit (mm)", "required": True, "rows": 3, "aliases": ["size", "sizes", "measurements", "dims"],
     "hint": "Everything it has to fit around or inside, measured. Mark a guess with ~. The bed is a 270 mm cube.",
     "placeholder": "Rack footprint 300 x 240, feet 12 tall. Gap to the wall 20. Counter edge lip 4."},
    {"key": "quantity", "ask": "How many", "required": False, "rows": 1, "aliases": ["qty", "count", "number"],
     "hint": "", "placeholder": "1"},
    {"key": "material", "ask": "Material and colour", "required": False, "rows": 1, "aliases": ["colour", "color", "filament"],
     "hint": "PLA, PETG, TPU or ASA, or say what it is up against (heat, water, sun, food, load) and leave the choice open.",
     "placeholder": "Something that shrugs off water; grey or black"},
    {"key": "deadline", "ask": "When do you need it", "required": False, "rows": 1, "aliases": ["when", "by", "date", "due"],
     "hint": "", "placeholder": "No rush / before the 20th"},
    {"key": "links", "ask": "Photos or links", "required": False, "rows": 2, "aliases": ["photos", "photo", "reference", "references", "url"],
     "hint": "A photo of the spot, a product page, something similar you have seen.", "placeholder": ""},
    {"key": "notes", "ask": "Anything else", "required": False, "rows": 3, "aliases": ["note", "other", "comments", "details"],
     "hint": "Must / must not: no screws into the wall, has to come apart, dishwasher safe...", "placeholder": ""},
]
FIELD_BY_KEY = {f["key"]: f for f in REQUEST_FIELDS}
ALIAS = {a.lower(): f["key"] for f in REQUEST_FIELDS for a in [f["key"], f["ask"]] + f["aliases"]}


# ---------------------------------------------------------------- store

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def ticket_path(tid: str) -> Path:
    return TICKETS_DIR / tid / "ticket.json"


def load_ticket(tid: str) -> dict:
    p = ticket_path(tid)
    if not p.exists():
        raise SystemExit(f"no ticket {tid} (tickets/{tid}/ticket.json)")
    return json.loads(p.read_text(encoding="utf-8"))


def save_ticket(t: dict) -> Path:
    t["updated"] = now_iso()
    p = ticket_path(t["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def list_tickets() -> list[dict]:
    out = []
    for p in sorted(TICKETS_DIR.glob("*/ticket.json")) if TICKETS_DIR.exists() else []:
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


def next_id(existing: list[dict] | None = None) -> str:
    ids = [int(m.group(1)) for t in (existing if existing is not None else list_tickets()) if (m := REQ_RE.match(t.get("id", "")))]
    return f"REQ-{(max(ids) + 1 if ids else 1):04d}"


def new_ticket(*, name: str, mail: str, title: str, fields: dict | None = None, text: str = "", source: str = "cli",
               mail_id: str = "", when: str | None = None, existing: list[dict] | None = None, tid: str = "") -> dict:
    when = when or now_iso()
    fields = {k: str(v).strip() for k, v in (fields or {}).items() if str(v).strip()}
    fields.setdefault("name", name); fields.setdefault("email", mail); fields.setdefault("title", title)
    t = {"id": tid or next_id(existing), "title": title.strip() or "untitled request", "status": "new", "created": when, "updated": when,
         "requester": {"name": name.strip(), "email": mail.strip().lower()},
         "request": {"fields": fields, "text": text.strip(), "source": source},
         "model": "", "quotes": [],
         "messages": [{"id": mail_id or f"m-{when}", "when": when, "from": "requester", "kind": "request",
                       "subject": f"{REQUEST_TAG} {title}".strip(), "text": text.strip() or request_text(fields)}],
         "history": [{"when": when, "from": "", "to": "new", "by": source, "note": ""}]}
    return t


def request_text(fields: dict) -> str:
    """The request as the mail body the Request page composes: one `Label: value` block per field."""
    lines = []
    for f in REQUEST_FIELDS:
        v = str(fields.get(f["key"]) or "").strip()
        if v:
            lines.append(f"{f['ask']}: {v}" if "\n" not in v else f"{f['ask']}:\n{v}")
    return "\n".join(lines)


def parse_request_text(text: str) -> dict:
    """Inverse of request_text, tolerant: `Label: value` lines, continuation lines join the previous field."""
    fields: dict[str, str] = {}
    key = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^\s*([A-Za-z][A-Za-z ()/-]{0,40}?)\s*:\s*(.*)$", line)
        k = ALIAS.get(m.group(1).strip().lower()) if m else None
        if k:
            key = k
            fields[key] = (fields.get(key, "") + "\n" + m.group(2)).strip() if fields.get(key) else m.group(2).strip()
        elif key and line.strip():
            fields[key] = (fields[key] + "\n" + line.strip()).strip()
    return fields


def set_status(t: dict, status: str, *, by: str = "me", note: str = "") -> dict:
    if status not in STATUSES:
        raise SystemExit(f"unknown status {status!r}; one of {', '.join(STATUSES)}")
    if t.get("status") != status:
        t["history"].append({"when": now_iso(), "from": t.get("status", ""), "to": status, "by": by, "note": note})
        t["status"] = status
    elif note:
        t["history"].append({"when": now_iso(), "from": status, "to": status, "by": by, "note": note})
    return t


def add_message(t: dict, *, frm: str, kind: str, text: str, subject: str = "", mail_id: str = "", when: str | None = None) -> dict | None:
    if mail_id and any(m.get("id") == mail_id for m in t["messages"]):
        return None
    m = {"id": mail_id or f"m-{now_iso()}-{len(t['messages'])}", "when": when or now_iso(), "from": frm, "kind": kind,
         "subject": subject, "text": text.strip()}
    t["messages"].append(m)
    return m


# ---------------------------------------------------------------- estimate

def load_pricing() -> dict:
    return json.loads(PRICING_JSON.read_text(encoding="utf-8"))


def _round(x: float, step: float) -> float:
    return round(math.ceil(x / step) * step, 2) if step else round(x, 2)


def estimate(report: dict, material: str = "PLA", qty: int = 1, pricing: dict | None = None) -> dict:
    """Cost and time for printing every part of one build report, `qty` times.

    Mass is the honest part: solid volume is known exactly, and a print is a shell plus sparse infill,
    so printed volume ~ shell (surface area x shell thickness, capped at the solid) + infill fraction of
    the rest.  Time is mass over a typical deposition rate plus setup and per-part finishing.  Both are
    labelled estimates on the quote; the slicer's numbers replace them the day the part is sliced.
    """
    pr = pricing or load_pricing()
    material = (material or "PLA").upper()
    mat = pr["materials"].get(material) or pr["materials"]["PLA"]
    qty = max(1, int(qty or 1))
    parts = []
    for name, p in (report.get("parts") or {}).items():
        m = p.get("metrics") or {}
        vol = float(m.get("volume") or 0.0)
        area = float(m.get("surface_area") or 0.0)
        shell = min(vol, area * pr["shell_mm"])
        printed = shell + pr["infill"] * max(0.0, vol - shell)
        if str(p.get("print_mode") or "normal") == "vase":
            printed = min(vol, area * 0.5)          # one wall, no infill
        mass = printed / 1000.0 * mat["density_g_cm3"]
        parts.append({"name": name, "bbox_mm": [round(x, 1) for x in (m.get("bbox_size") or [0, 0, 0])],
                      "volume_cm3": round(vol / 1000.0, 2), "mass_g": round(mass, 1),
                      "print_h": round(mass / pr["flow_g_per_h"], 2), "wall_min_mm": (p.get("printability") or {}).get("wall_min_mm"),
                      "print_mode": p.get("print_mode") or "normal"})
    mass_g = sum(p["mass_g"] for p in parts) * qty
    print_h = sum(p["print_h"] for p in parts) * qty + pr["setup_min"] / 60.0
    post_h = pr["post_min_per_part"] / 60.0 * len(parts) * qty
    material_cost = mass_g / 1000.0 * mat["cost_per_kg"]
    machine_cost = print_h * pr["machine_per_h"]
    labor_cost = (post_h + pr["setup_min"] / 60.0) * pr["labor_per_h"]
    subtotal = material_cost + machine_cost + labor_cost + pr["design_fee"]
    total = max(pr["min_charge"], subtotal * (1 + pr["margin"]))
    total = _round(total, pr.get("round_to", 0.5))
    lead_days = pr["queue_days"] + math.ceil((print_h + post_h) / pr["hours_per_day"])
    return {"material": material, "qty": qty, "currency": pr.get("currency", "USD"), "parts": parts,
            "mass_g": round(mass_g, 1), "print_h": round(print_h, 1), "post_h": round(post_h, 1), "lead_days": lead_days,
            "material_cost": round(material_cost, 2), "machine_cost": round(machine_cost, 2), "labor_cost": round(labor_cost, 2),
            "design_fee": round(pr["design_fee"], 2), "subtotal": round(subtotal, 2), "margin": pr["margin"],
            "total": total, "per_unit": round(total / qty, 2),
            "rates": {k: pr[k] for k in ("shell_mm", "infill", "flow_g_per_h", "setup_min", "post_min_per_part",
                                         "machine_per_h", "labor_per_h", "design_fee", "min_charge", "margin", "queue_days")}
            | {"material": mat}}


def measurements_md(report: dict, est: dict) -> str:
    """The detailed numbers: every part's envelope, volume, thinnest wall; every named parameter with its comment."""
    out = [f"# {report.get('project')} — measurements", "",
           f"Built {report.get('built_at', '')} (build {report.get('build_id', '')}). Every number in millimetres unless marked.", ""]
    doc = (report.get("docstring") or "").strip()
    if doc:
        out += [doc, ""]
    out += ["## Parts", "", "| part | X x Y x Z (mm) | volume (cm³) | est. mass (g) | thinnest wall (mm) | print mode |", "|---|---|---|---|---|---|"]
    for p in est["parts"]:
        bb = " x ".join(f"{x:g}" for x in p["bbox_mm"])
        out.append(f"| {p['name']} | {bb} | {p['volume_cm3']:g} | {p['mass_g']:g} | {p['wall_min_mm'] if p['wall_min_mm'] is not None else '—'} | {p['print_mode']} |")
    plate = report.get("plate") or {}
    if plate.get("extent"):
        out += ["", f"Plate extent {' x '.join(f'{x:g}' for x in plate['extent'])} mm on the {plate.get('printer', PRINTER['machine'])}"
                + (" (fits the bed)" if plate.get("fits_bed") else " (does NOT fit the bed in one plate)")]
    params = [p for p in report.get("params") or [] if p.get("value") is not None]
    if params:
        out += ["", "## Dimensions and choices", "", "| parameter | value | meaning |", "|---|---|---|"]
        for p in params:
            out.append(f"| {p['name']} | {p['value']} | {p.get('comment') or ''} |")
    fits = report.get("fit_checks") or {}
    if fits:
        out += ["", "## Fit checks", ""] + [f"- {k}: {'clear' if not v else f'{v} mm³ overlap'}" for k, v in fits.items()]
    comps = report.get("components") or []
    if comps:
        out += ["", "## Proven pieces it is built from", ""]
        for c in comps:
            proof = ", ".join(c.get("field_validated") or c.get("validated") or []) or "not yet test-printed"
            out.append(f"- {c['id']} v{c['version']}: {c['summary']} (printed in: {proof})")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- quote

def quote_dir(t: dict, rev: int) -> Path:
    return TICKETS_DIR / t["id"] / "quotes" / f"r{rev}"


def make_quote(t: dict, project: str, *, material: str = "", qty: int = 0, note: str = "", sender: str = "") -> dict:
    """Package quote revision N for a ticket from a built model: estimate, measurements, e-mail, attachments."""
    if project not in set(list_projects()):
        raise SystemExit(f"no model {project} under models/")
    rp = MODELS_DIR / project / "exports" / "build_report.json"
    if not rp.exists():
        raise SystemExit(f"{project} has no build report — run `uv run python scripts/build.py {project}` first")
    report = json.loads(rp.read_text(encoding="utf-8"))
    fields = t["request"].get("fields") or {}
    material = material or _material_in(fields.get("material", "")) or "PLA"
    qty = qty or _int_in(fields.get("quantity", "")) or 1
    est = estimate(report, material, qty)
    rev = len(t["quotes"]) + 1
    qd = quote_dir(t, rev)
    qd.mkdir(parents=True, exist_ok=True)
    viewer = MODELS_DIR / project / "exports" / "view.html"
    attachments = []
    if viewer.exists():
        shutil.copy(viewer, qd / f"{t['id']}-r{rev}-3d-viewer.html"); attachments.append(f"{t['id']}-r{rev}-3d-viewer.html")
    for png in sorted((MODELS_DIR / project / "exports" / "renders").glob("*.png")):
        shutil.copy(png, qd / png.name); attachments.append(png.name)
    (qd / "measurements.md").write_text(measurements_md(report, est), encoding="utf-8"); attachments.append("measurements.md")
    q = {"rev": rev, "created": now_iso(), "sent": "", "model": project, "build_id": report.get("build_id", ""),
         "material": material, "qty": qty, "estimate": est, "note": note, "attachments": attachments,
         "subject": f"[{t['id']}] Quote r{rev}: {t['title']}", "message_id": ""}
    q["email_html"] = quote_email_html(t, q, report, sender=sender)
    q["email_text"] = quote_email_text(t, q, report)
    (qd / "email.html").write_text(q["email_html"], encoding="utf-8")
    (qd / "email.txt").write_text(q["email_text"], encoding="utf-8")
    stored = {k: v for k, v in q.items() if k not in ("email_html", "email_text")}
    (qd / "quote.json").write_text(json.dumps(stored | {"report_params": report.get("params", [])}, indent=2) + "\n", encoding="utf-8")
    t["quotes"].append(stored)
    t["model"] = project
    return q


def _material_in(text: str) -> str:
    for m in sorted(PRINTER["materials"], key=len, reverse=True):
        if re.search(rf"\b{re.escape(m)}\b", text or "", re.I):
            return m
    return ""


def _int_in(text: str) -> int:
    m = re.search(r"\d+", text or "")
    return int(m.group()) if m else 0


def _money(x: float, cur: str) -> str:
    sym = {"USD": "$", "EUR": "€", "GBP": "£"}.get(cur, cur + " ")
    return f"{sym}{x:,.2f}"


def _hours(h: float) -> str:
    return f"{h:g} h" if h < 1 or h == int(h) else f"{int(h)} h {int(round((h % 1) * 60)):02d} min"


def quote_email_text(t: dict, q: dict, report: dict) -> str:
    e = q["estimate"]
    first = (t["requester"].get("name") or "there").split()[0]
    lines = [f"Hi {first},", "",
             f"Here is the design for your request \"{t['title']}\" ({t['id']}), revision {q['rev']}.",
             "The attached 3D viewer opens in any browser: orbit it, section it, and check every measurement against the spot it goes in.", ""]
    if q.get("note"):
        lines += [q["note"].strip(), ""]
    lines += ["MEASUREMENTS", ""]
    for p in e["parts"]:
        lines.append(f"  {p['name']}: {' x '.join(f'{x:g}' for x in p['bbox_mm'])} mm, {p['volume_cm3']:g} cm3, about {p['mass_g']:g} g")
    params = [p for p in report.get("params") or [] if p.get("value") is not None and not p.get("derived")]
    if params:
        lines += ["", "  Key dimensions and choices (all in mm unless said otherwise):"]
        for p in params[:24]:
            lines.append(f"  - {p['name']} = {p['value']}" + (f"  ({p['comment']})" if p.get("comment") else ""))
    lines += ["", "  The full list is in measurements.md, attached.", "",
              "ESTIMATE", "",
              f"  Material      {e['material']}, about {e['mass_g']:g} g",
              f"  Print time    about {_hours(e['print_h'])} (+ {_hours(e['post_h'])} finishing)",
              f"  Quantity      {e['qty']}",
              f"  Price         {_money(e['total'], e['currency'])} total" + (f" ({_money(e['per_unit'], e['currency'])} each)" if e['qty'] > 1 else ""),
              f"  Ready in      about {e['lead_days']} day(s) from your confirmation", "",
              "  Time and price are estimates from the model's geometry; the sliced print may differ a little either way.", "",
              "WHAT NEXT", "",
              "  Reply to this e-mail (keep the subject) with:",
              "    CONFIRM                 - to have it printed as shown, or",
              "    your notes              - anything to change: a size, a feature, the material, the count.",
              "  A revised design and estimate come back the same way, until you are happy.", "",
              "Thanks,", _sender_name(), ""]
    return "\n".join(lines)


def _sender_name() -> str:
    try:
        return subprocess.run(["git", "config", "user.name"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or "the print shop"
    except Exception:
        return "the print shop"


def quote_email_html(t: dict, q: dict, report: dict, sender: str = "") -> str:
    e = q["estimate"]
    first = html.escape((t["requester"].get("name") or "there").split()[0])
    cur = e["currency"]
    row = lambda k, v: f"<tr><td style='padding:4px 10px 4px 0;color:#5E6771;white-space:nowrap'>{k}</td><td style='padding:4px 0'>{v}</td></tr>"  # noqa: E731
    parts_rows = "".join(
        f"<tr><td style='padding:4px 10px 4px 0'>{html.escape(p['name'])}</td>"
        f"<td style='padding:4px 10px;font-family:Menlo,Consolas,monospace'>{' × '.join(f'{x:g}' for x in p['bbox_mm'])}</td>"
        f"<td style='padding:4px 10px;text-align:right'>{p['volume_cm3']:g}</td><td style='padding:4px 10px;text-align:right'>{p['mass_g']:g}</td>"
        f"<td style='padding:4px 10px;text-align:right'>{p['wall_min_mm'] if p['wall_min_mm'] is not None else '—'}</td></tr>"
        for p in e["parts"])
    params = [p for p in report.get("params") or [] if p.get("value") is not None and not p.get("derived")]
    param_rows = "".join(
        f"<tr><td style='padding:3px 10px 3px 0;font-family:Menlo,Consolas,monospace;font-size:12px'>{html.escape(str(p['name']))}</td>"
        f"<td style='padding:3px 10px;font-family:Menlo,Consolas,monospace;font-size:12px'>{html.escape(str(p['value']))}</td>"
        f"<td style='padding:3px 0;color:#5E6771;font-size:12px'>{html.escape(p.get('comment') or '')}</td></tr>" for p in params[:24])
    renders = [a for a in q.get("attachments", []) if a.endswith(".png")]
    img = f"<p><img src='cid:{html.escape(renders[0])}' alt='render' style='max-width:520px;border:1px solid #D9DDD8;border-radius:6px'></p>" if renders else ""
    note = f"<p>{html.escape(q['note']).replace(chr(10), '<br>')}</p>" if q.get("note") else ""
    price = _money(e["total"], cur) + (f" <span style='color:#5E6771'>({_money(e['per_unit'], cur)} each)</span>" if e["qty"] > 1 else "")
    return f"""<div style="font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;line-height:1.5;color:#1A1F25;max-width:640px">
<p>Hi {first},</p>
<p>Here is the design for your request <b>{html.escape(t['title'])}</b> ({t['id']}), revision {q['rev']}.
The attached <b>3D viewer</b> opens in any browser: orbit it, section it, and check every measurement against the spot it goes in.</p>
{note}{img}
<h3 style="font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#5E6771;margin:22px 0 6px">Measurements</h3>
<table style="border-collapse:collapse;font-size:13px"><tr style="color:#5E6771;text-align:left"><th style="padding:4px 10px 4px 0;font-weight:500">part</th>
<th style="padding:4px 10px;font-weight:500">X × Y × Z mm</th><th style="padding:4px 10px;font-weight:500;text-align:right">cm³</th>
<th style="padding:4px 10px;font-weight:500;text-align:right">≈ g</th><th style="padding:4px 10px;font-weight:500;text-align:right">thinnest wall</th></tr>{parts_rows}</table>
{"<p style='margin:12px 0 4px;color:#5E6771;font-size:12px'>Key dimensions and choices (mm unless said otherwise):</p><table style='border-collapse:collapse'>" + param_rows + "</table>" if param_rows else ""}
<p style="color:#5E6771;font-size:12px">The full list is in <b>measurements.md</b>, attached.</p>
<h3 style="font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#5E6771;margin:22px 0 6px">Estimate</h3>
<table style="border-collapse:collapse;font-size:13px">
{row('Material', f"{html.escape(e['material'])}, about {e['mass_g']:g} g")}
{row('Print time', f"about {_hours(e['print_h'])} <span style='color:#5E6771'>+ {_hours(e['post_h'])} finishing</span>")}
{row('Quantity', e['qty'])}
{row('Price', f"<b>{price}</b>")}
{row('Ready in', f"about {e['lead_days']} day{'s' if e['lead_days'] != 1 else ''} from your confirmation")}
</table>
<p style="color:#5E6771;font-size:12px">Time and price are estimates from the model's geometry; the sliced print may differ a little either way.</p>
<h3 style="font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#5E6771;margin:22px 0 6px">What next</h3>
<div style="border:1px solid #D9DDD8;border-left:3px solid #E8791D;border-radius:0 6px 6px 0;padding:10px 14px">
<p style="margin:0 0 6px">Reply to this e-mail (keep the subject line) with:</p>
<p style="margin:0 0 4px"><b>CONFIRM</b> — to have it printed as shown, or</p>
<p style="margin:0"><b>your notes</b> — anything to change: a size, a feature, the material, the count. A revised design and estimate come back the same way, until you are happy.</p>
</div>
<p style="margin-top:20px">Thanks,<br>{html.escape(sender or _sender_name())}</p>
</div>"""


def outbox(t: dict, q: dict | None = None) -> dict:
    """Everything a mail client needs to send the latest quote: the Gmail-connector path reads this."""
    q = q or (t["quotes"][-1] if t["quotes"] else None)
    if not q:
        raise SystemExit(f"{t['id']} has no quote yet — `tickets.py quote {t['id']} --model <project>`")
    qd = quote_dir(t, q["rev"])
    thread_ids = sorted({m.get("thread_id") for m in t["messages"] if m.get("thread_id")})
    return {"ticket": t["id"], "rev": q["rev"], "to": [t["requester"]["email"]], "subject": q["subject"],
            "html": str(qd / "email.html"), "text": str(qd / "email.txt"),
            "attachments": [str(qd / a) for a in q.get("attachments", []) if (qd / a).exists()],
            "reply_thread_id": thread_ids[-1] if thread_ids else ""}


# ---------------------------------------------------------------- Jira Service Management

def load_jira_cfg() -> dict | None:
    if not JIRA_JSON.exists():
        return None
    cfg = json.loads(JIRA_JSON.read_text(encoding="utf-8"))
    return cfg if cfg.get("project") else None


def jira_client(cfg: dict | None = None):
    """(client, cfg) when Jira is configured and the credentials are in the environment; SystemExit otherwise."""
    cfg = cfg or load_jira_cfg()
    if not cfg:
        raise SystemExit("Jira is not configured: write tickets/jira.json (uv run python scripts/tickets.py jira check --project <KEY>)")
    creds = jira_api.credentials()
    if not creds:
        raise SystemExit("Jira needs JIRA_SITE, JIRA_EMAIL and JIRA_API_TOKEN in the environment (an Atlassian API token)")
    return jira_api.JiraClient(creds["site"], creds["email"], creds["token"]), cfg


def jira_field_map(cfg: dict):
    """Portal field label -> request field key: our own labels and aliases, Jira's Summary/Description, plus cfg['field_labels']."""
    extra = {str(k).lower(): v for k, v in (cfg.get("field_labels") or {}).items()}
    def f(label: str) -> str | None:
        k = label.strip().lower()
        if k in extra:
            return extra[k]
        if k in ("summary", "what do you need?", "what do you need"):
            return "title"
        if k == "description":
            return "purpose"
        return ALIAS.get(k) or ALIAS.get(k.rstrip("?")) or ALIAS.get(k.replace("(mm)", "").strip())
    return f


def jira_fetch(cfg: dict | None = None) -> list[dict]:
    client, cfg = jira_client(cfg)
    return jira_api.pull(client, cfg, jira_field_map(cfg))


def jira_transition(t: dict, status: str, comment: str = "", client=None, cfg: dict | None = None) -> str:
    """Move the Jira request to the transition configured for `status`; returns what happened, for the report."""
    if not (t.get("jira") or {}).get("key"):
        return ""
    try:
        client, cfg = (client, cfg) if client else jira_client(cfg)
        wanted = (cfg.get("transitions") or {}).get(status) or jira_api.DEFAULT_TRANSITIONS.get(status) or []
        pick = client.transition(t["jira"]["key"], wanted, comment=comment) if wanted else None
    except (SystemExit, jira_api.JiraError) as e:
        return f"Jira transition skipped: {e}"
    if pick:
        t["jira"]["status"] = pick["to"] or pick["name"]
        return f"Jira: {pick['name']}" + (f" -> {pick['to']}" if pick["to"] else "")
    return f"Jira: no transition for '{status}' on {t['jira']['key']} (wanted one of {', '.join(wanted)}; set tickets/jira.json transitions)"


def jira_send_quote(t: dict, client=None, cfg: dict | None = None) -> dict:
    """Post the latest quote as a public comment with the package attached; JSM notifies the requester."""
    client, cfg = (client, cfg) if client else jira_client(cfg)
    ob = outbox(t)
    q = t["quotes"][-1]
    key = t["jira"]["key"]
    text = Path(ob["text"]).read_text(encoding="utf-8")
    files = [Path(a) for a in ob["attachments"]]
    jsm = bool(t["jira"].get("jsm", True))
    res = client.attach(key, str(cfg.get("service_desk_id") or ""), files, comment=text, public=True, jsm=jsm) if files else client.add_comment(key, text, jsm=jsm)
    cid = str((res.get("comment") or {}).get("id") or res.get("id") or "")
    moved = jira_transition(t, "quoted", client=client, cfg=cfg)
    return {"comment_id": cid, "attached": [p.name for p in files], "transition": moved, "rev": q["rev"], "key": key}


# ---------------------------------------------------------------- mail (stdlib SMTP / IMAP with a Gmail app password)

def mail_creds() -> tuple[str, str] | None:
    u, p = os.environ.get("PRINTING_MAIL_USER", "").strip(), os.environ.get("PRINTING_MAIL_PASS", "").strip()
    return (u, p) if u and p else None


def my_addresses() -> set[str]:
    out = set()
    if (c := mail_creds()):
        out.add(c[0].lower())
    try:
        out.add(subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True).stdout.strip().lower())
    except Exception:
        pass
    return {a for a in out if a}


def send_quote(t: dict, *, dry_run: bool = False) -> dict:
    ob = outbox(t)
    q = t["quotes"][-1]
    creds = mail_creds()
    if dry_run or not creds:
        return {"sent": False, "outbox": ob, "why": "dry run" if dry_run else "no PRINTING_MAIL_USER / PRINTING_MAIL_PASS in the environment"}
    import smtplib
    msg = EmailMessage()
    msg["From"] = f"{_sender_name()} <{creds[0]}>"
    msg["To"] = ", ".join(ob["to"])
    msg["Subject"] = ob["subject"]
    msg["Message-ID"] = email.utils.make_msgid(domain=creds[0].split("@")[-1])
    last = [m for m in t["messages"] if m.get("mail_message_id")]
    if last:
        msg["In-Reply-To"] = last[-1]["mail_message_id"]; msg["References"] = last[-1]["mail_message_id"]
    msg.set_content(Path(ob["text"]).read_text(encoding="utf-8"))
    msg.add_alternative(Path(ob["html"]).read_text(encoding="utf-8"), subtype="html")
    html_part = msg.get_payload()[-1]
    for a in ob["attachments"]:
        p = Path(a)
        data = p.read_bytes()
        if p.suffix == ".png":
            html_part.add_related(data, "image", "png", cid=f"<{p.name}>", filename=p.name)
        elif p.suffix == ".html":
            msg.add_attachment(data, maintype="text", subtype="html", filename=p.name)
        else:
            msg.add_attachment(data, maintype="text", subtype="markdown", filename=p.name)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as s:
        s.login(*creds)
        s.send_message(msg)
    return {"sent": True, "outbox": ob, "message_id": msg["Message-ID"]}


def record_sent(t: dict, message_id: str = "", thread_id: str = "") -> dict:
    q = t["quotes"][-1]
    q["sent"] = now_iso(); q["message_id"] = message_id
    add_message(t, frm="me", kind="quote", subject=q["subject"], text=f"quote r{q['rev']} sent: {q['model']} in {q['material']} x{q['qty']}, "
               f"{_money(q['estimate']['total'], q['estimate']['currency'])}, ~{q['estimate']['lead_days']} day(s)", mail_id=message_id or "")
    if message_id or thread_id:
        t["messages"][-1]["mail_message_id"] = message_id
        if thread_id:
            t["messages"][-1]["thread_id"] = thread_id
    return set_status(t, "quoted", by="me", note=f"quote r{q['rev']}")


def _mail_text(msg) -> str:
    if msg.is_multipart():
        plain = [p for p in msg.walk() if p.get_content_type() == "text/plain" and not p.get_filename()]
        if plain:
            return "\n".join(p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "replace") for p in plain)
        for p in msg.walk():
            if p.get_content_type() == "text/html":
                return strip_html(p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "replace"))
        return ""
    body = msg.get_payload(decode=True)
    text = body.decode(msg.get_content_charset() or "utf-8", "replace") if body else ""
    return strip_html(text) if msg.get_content_type() == "text/html" else text


def strip_html(s: str) -> str:
    s = re.sub(r"(?is)<(script|style).*?</\1>", "", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", s)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def strip_quoted(text: str) -> str:
    """Drop the quoted original below a reply ('On ... wrote:' / '> ' lines / a signature dash line)."""
    out = []
    for line in text.splitlines():
        if re.match(r"^\s*(On .{2,120} wrote:|-----\s*Original Message|From: .+|Le .+ a écrit ?:)\s*$", line):
            break
        if line.startswith(">"):
            continue
        if line.strip() == "--":
            break
        out.append(line)
    return "\n".join(out).strip()


def fetch_mail(since_days: int = 60) -> list[dict]:
    """IMAP: every message whose subject carries a ticket id or the request tag, as plain dicts for ingest."""
    creds = mail_creds()
    if not creds:
        raise SystemExit("fetch needs PRINTING_MAIL_USER and PRINTING_MAIL_PASS (a Gmail app password) in the environment;\n"
                         "without them, Claude reads the mailbox with the Gmail connector and writes .sync/tickets/mail.json itself.")
    import imaplib
    since = time.strftime("%d-%b-%Y", time.localtime(time.time() - since_days * 86400))
    out = []
    with imaplib.IMAP4_SSL("imap.gmail.com") as im:
        im.login(*creds)
        im.select('"[Gmail]/All Mail"', readonly=True)
        uids: set[bytes] = set()
        for crit in (f'(SINCE {since} SUBJECT "REQ-")', f'(SINCE {since} SUBJECT "print request")'):
            typ, data = im.search(None, crit)
            if typ == "OK" and data and data[0]:
                uids |= set(data[0].split())
        for uid in sorted(uids, key=int):
            typ, data = im.fetch(uid, "(RFC822)")
            if typ != "OK":
                continue
            msg = email.message_from_bytes(data[0][1])
            frm = email.utils.parseaddr(msg.get("From", ""))
            out.append({"id": (msg.get("Message-ID") or f"imap-{uid.decode()}").strip(), "from": frm[1].lower(), "from_name": frm[0],
                        "to": [a[1].lower() for a in email.utils.getaddresses(msg.get_all("To", []))],
                        "subject": str(email.header.make_header(email.header.decode_header(msg.get("Subject", "")))),
                        "date": _iso_date(msg.get("Date", "")), "in_reply_to": (msg.get("In-Reply-To") or "").strip(),
                        "text": _mail_text(msg)})
    return out


def _iso_date(s: str) -> str:
    try:
        return email.utils.parsedate_to_datetime(s).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return now_iso()


# ---------------------------------------------------------------- ingest (mail.json + the board page's `requests` dump)

def classify_reply(text: str) -> str:
    """'approved' | 'declined' | 'changes' for a requester's reply to a quote (Claude re-reads it either way)."""
    head = strip_quoted(text)[:600]
    if DECLINE_RE.search(head):
        return "declined"
    if CONFIRM_RE.search(head) and not re.search(r"\b(but|however|except|if you|could you|change|instead)\b", head, re.I):
        return "approved"
    return "changes"


def ingest(sync_dir: Path = SYNC_DIR, *, dry_run: bool = False, mine: set[str] | None = None) -> dict:
    mine = mine if mine is not None else my_addresses()
    tickets = {t["id"]: t for t in list_tickets()}
    by_mail_id = {m["id"]: (t["id"], m) for t in tickets.values() for m in t["messages"]}
    summary = {"new": [], "replies": [], "skipped": [], "requests_filed": [], "jira_updated": []}
    # Jira requests (fetch wrote .sync/tickets/jira.json in Jira mode)
    jp = sync_dir / "jira.json"
    if jp.exists():
        try:
            reqs = json.loads(jp.read_text(encoding="utf-8"))
            reqs = reqs.get("requests", reqs) if isinstance(reqs, dict) else reqs
        except json.JSONDecodeError:
            reqs = []; summary["skipped"].append("jira.json is not valid JSON")
        for r in reqs or []:
            if not isinstance(r, dict) or not r.get("key"):
                continue
            key = r["key"]; rep = r.get("reporter") or {}
            t = tickets.get(key)
            if not t:
                fields = {k: str(v) for k, v in (r.get("fields") or {}).items()}
                t = new_ticket(name=rep.get("name", ""), mail=rep.get("email", ""), title=fields.get("title") or r.get("summary", ""), fields=fields,
                               text=request_text(fields), source="jira", mail_id=f"jira-{key}", when=r.get("created") or None, tid=key)
                t["jira"] = {"key": key, "url": r.get("url", ""), "status": r.get("status", ""), "jsm": r.get("jsm", True), "synced": now_iso()}
                tickets[key] = t
                summary["new"].append({"ticket": key, "title": t["title"], "from": rep.get("email", ""), "missing": missing_fields(fields)})
            else:
                j = t.setdefault("jira", {"key": key})
                changed = j.get("status") != r.get("status")
                j.update({"url": r.get("url", j.get("url", "")), "status": r.get("status", ""), "jsm": r.get("jsm", True), "synced": now_iso()})
                if not t["requester"].get("email") and rep.get("email"):
                    t["requester"]["email"] = rep["email"]
                if changed:
                    summary["jira_updated"].append({"ticket": key, "jira_status": r.get("status", "")})
            for c in r.get("comments") or []:
                cid = f"jira-comment-{c.get('id')}"
                if any(m.get("id") == cid for m in t["messages"]):
                    continue
                if c.get("who") == "requester":
                    verdict = classify_reply(str(c.get("text") or ""))
                    msg = add_message(t, frm="requester", kind="reply", subject=f"comment on {key}", text=str(c.get("text") or "").strip(), mail_id=cid, when=c.get("created"))
                    if msg is None:
                        continue
                    msg["verdict"] = verdict
                    if t["status"] in ("quoted", "changes"):
                        set_status(t, "approved" if verdict == "approved" else "declined" if verdict == "declined" else "changes",
                                   by="requester", note=f"Jira comment read as {verdict}")
                        summary["replies"].append({"ticket": key, "verdict": verdict, "text": msg["text"][:200], "from": c.get("email") or rep.get("email", "")})
                    else:
                        summary["replies"].append({"ticket": key, "verdict": "note", "text": msg["text"][:200], "from": c.get("email") or rep.get("email", "")})
                else:
                    add_message(t, frm="me" if c.get("who") == "me" else "agent", kind="comment" if c.get("public") else "internal",
                                subject=f"comment on {key}", text=str(c.get("text") or "").strip()[:2000], mail_id=cid, when=c.get("created"))
    mails: list[dict] = []
    mp = sync_dir / "mail.json"
    if mp.exists():
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
            mails = data.get("messages", data) if isinstance(data, dict) else data
        except json.JSONDecodeError:
            summary["skipped"].append("mail.json is not valid JSON")
    for m in sorted(mails, key=lambda m: str(m.get("date") or "")):
        mid = str(m.get("id") or "")
        if mid and mid in by_mail_id:
            continue
        subj, frm, text = str(m.get("subject") or ""), str(m.get("from") or "").lower(), str(m.get("text") or "")
        hit = ID_RE.search(subj) or ID_RE.search(text[:200])
        if hit:
            tid = hit.group(1)
            t = tickets.get(tid)
            if not t:
                summary["skipped"].append(f"{mid or subj}: names {tid}, which does not exist"); continue
            if frm in mine:
                if not any(x.get("id") == mid for x in t["messages"]):
                    add_message(t, frm="me", kind="mail", subject=subj, text=strip_quoted(text)[:2000], mail_id=mid, when=m.get("date"))
                    t["messages"][-1]["thread_id"] = m.get("thread_id", "")
                continue
            if frm and frm != t["requester"]["email"]:
                summary["skipped"].append(f"{mid or subj}: on {tid} but from {frm}, not the requester"); continue
            verdict = classify_reply(text)
            msg = add_message(t, frm="requester", kind="reply", subject=subj, text=strip_quoted(text) or text.strip(), mail_id=mid, when=m.get("date"))
            if msg is None:
                continue
            msg["verdict"] = verdict
            msg["thread_id"] = m.get("thread_id", "")
            if t["status"] in ("quoted", "changes", "designing", "new"):
                set_status(t, "approved" if verdict == "approved" else "declined" if verdict == "declined" else "changes",
                           by="requester", note=f"reply read as {verdict}")
            summary["replies"].append({"ticket": tid, "verdict": verdict, "text": msg["text"][:200], "from": frm})
            continue
        if REQUEST_TAG.lower() in subj.lower() or REQUEST_TAG.lower() in text[:300].lower():
            if frm in mine and not m.get("from_name"):
                pass                                               # a request I forwarded to myself still counts
            fields = parse_request_text(text)
            title = fields.get("title") or subj.lower().replace(REQUEST_TAG, "").strip(" :-") or "untitled request"
            name = fields.get("name") or str(m.get("from_name") or "") or frm.split("@")[0]
            addr = (fields.get("email") or frm).lower()
            t = new_ticket(name=name, mail=addr, title=title, fields=fields, text=text, source="mail", mail_id=mid,
                           when=m.get("date") or None, existing=list(tickets.values()))
            t["messages"][0]["thread_id"] = m.get("thread_id", "")
            t["messages"][0]["mail_message_id"] = mid
            tickets[t["id"]] = t
            summary["new"].append({"ticket": t["id"], "title": t["title"], "from": addr, "missing": missing_fields(t["request"]["fields"])})
            continue
        summary["skipped"].append(f"{mid or subj}: neither a ticket id nor {REQUEST_TAG}")
    # requests entered on the (internal) board page
    rq = sync_dir / "requests.json"
    if rq.exists():
        try:
            docs = json.loads(rq.read_text(encoding="utf-8"))
            docs = docs.get("documents", docs) if isinstance(docs, dict) else docs
        except json.JSONDecodeError:
            docs = []; summary["skipped"].append("requests.json is not valid JSON")
        for d in docs or []:
            if not isinstance(d, dict) or d.get("ticket"):
                continue
            if any(t["request"].get("page_id") == d.get("id") for t in tickets.values()):
                continue
            f = {k: str(v) for k, v in (d.get("fields") or {}).items()}
            t = new_ticket(name=f.get("name", ""), mail=f.get("email", ""), title=f.get("title", ""), fields=f, text=request_text(f),
                           source="board page", when=str(d.get("created") or "")[:19] or None, existing=list(tickets.values()))
            t["request"]["page_id"] = d.get("id")
            tickets[t["id"]] = t
            summary["requests_filed"].append({"ticket": t["id"], "title": t["title"], "page_id": d.get("id"), "missing": missing_fields(f)})
    if not dry_run:
        for t in tickets.values():
            save_ticket(t)
        sync_dir.mkdir(parents=True, exist_ok=True)
        actions = [{"action": "write_db", "db_op": "update", "collection": "requests", "doc_id": r["page_id"], "data": {"ticket": r["ticket"], "status": "filed"}}
                   for r in summary["requests_filed"]]
        (sync_dir / "actions.json").write_text(json.dumps(actions, indent=2) + "\n", encoding="utf-8")
    return summary


def missing_fields(fields: dict) -> list[str]:
    return [f["ask"] for f in REQUEST_FIELDS if f["required"] and not str(fields.get(f["key"]) or "").strip()]


# ---------------------------------------------------------------- views

def ticket_summary(t: dict) -> dict:
    q = t["quotes"][-1] if t["quotes"] else None
    last_reply = next((m for m in reversed(t["messages"]) if m["from"] == "requester" and m["kind"] == "reply"), None)
    return {"id": t["id"], "title": t["title"], "status": t["status"], "created": t["created"][:10], "updated": t["updated"][:10],
            "requester": t["requester"], "model": t.get("model", ""), "fields": t["request"].get("fields", {}), "jira": t.get("jira") or {},
            "missing": missing_fields(t["request"].get("fields", {})),
            "quote": ({"rev": q["rev"], "sent": q["sent"][:10], "material": q["material"], "qty": q["qty"],
                       "total": q["estimate"]["total"], "currency": q["estimate"]["currency"], "lead_days": q["estimate"]["lead_days"],
                       "print_h": q["estimate"]["print_h"], "mass_g": q["estimate"]["mass_g"]} if q else None),
            "last_reply": ({"when": last_reply["when"][:10], "verdict": last_reply.get("verdict", ""), "text": last_reply["text"][:400]} if last_reply else None),
            "messages": [{k: m.get(k, "") for k in ("when", "from", "kind", "subject", "text", "verdict")} for m in t["messages"]],
            "history": t["history"], "next": NEXT.get(t["status"], "")}


def page_data() -> dict:
    from scripts.studio import git_head
    pages = json.loads(PAGES_JSON.read_text(encoding="utf-8")) if PAGES_JSON.exists() else {}
    creds = mail_creds()
    inbox = (creds[0] if creds else "") or next(iter(sorted(my_addresses())), "")
    jcfg = load_jira_cfg() or {}
    site = (jira_api.credentials() or {}).get("site") or jcfg.get("site", "")
    jira = ({"project": jcfg["project"], "site": site, "service_desk_id": str(jcfg.get("service_desk_id") or ""),
             "portal_url": jira_api.portal_url(site, str(jcfg.get("service_desk_id") or "")) if site else "",
             "browse_url": f"{site}/browse/{jcfg['project']}" if site else ""} if jcfg else {})
    return {"generated": time.strftime("%Y-%m-%d %H:%M"), "git": git_head(), "repo": ROOT.name,
            "fields": REQUEST_FIELDS, "statuses": list(STATUSES), "next": NEXT, "printer": PRINTER, "request_tag": REQUEST_TAG,
            "inbox": inbox, "sender": _sender_name(), "pricing": {k: v for k, v in load_pricing().items() if not k.startswith("_")},
            "jira": jira, "tickets": [ticket_summary(t) for t in list_tickets()], "pages": pages, "models": list_projects()}


def write_html(d: dict, mode: str, out: Path) -> Path:
    public = dict(d)
    if mode == "request":
        public = {k: v for k, v in d.items() if k not in ("tickets", "git", "pricing")} | {"tickets": []}
    data = json.dumps(public | {"mode": mode}).replace("</", "<\\/")
    title = "Request a print" if mode == "request" else f"{d['repo']} Tickets"
    page = TEMPLATE.read_text(encoding="utf-8").replace("__TITLE__", html.escape(title)).replace("__DATA__", data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def format_board(d: dict) -> str:
    ts = d["tickets"]
    j = d.get("jira") or {}
    front = (f"Jira project {j['project']} at {j.get('site') or '(JIRA_SITE not set)'}" + (f", portal {j['portal_url']}" if j.get("portal_url") else "")
             if j else f"mail via {d['inbox'] or '(no mailbox configured)'}" + ("" if mail_creds() else "  [no PRINTING_MAIL_USER/PASS: send/fetch go through the Gmail connector]"))
    lines = [f"{d['repo']} tickets — {len(ts)} total; {front}"]
    if j and not jira_api.credentials():
        lines.append("  JIRA_SITE / JIRA_EMAIL / JIRA_API_TOKEN are not in the environment: fetch/send/set cannot reach Jira")
    for s in STATUSES:
        mine = [t for t in ts if t["status"] == s]
        if not mine:
            continue
        lines.append(f"\n{s.upper()} ({len(mine)})" + (f"   -> {NEXT[s]}" if NEXT[s] else ""))
        for t in mine:
            q = t["quote"]
            lines.append(f"  {t['id']}  {t['title'][:48]:<48s}  {t['requester']['name'] or t['requester']['email']:<22s}  {t['updated']}"
                         + (f"  [{t['jira']['status']}]" if t.get("jira", {}).get("status") else "")
                         + (f"  model {t['model']}" if t["model"] else "")
                         + (f"  r{q['rev']} {q['currency']} {q['total']:g} ~{q['lead_days']}d" if q else "")
                         + (f"  MISSING: {', '.join(t['missing'])}" if t["missing"] else ""))
            if t["last_reply"] and s in ("changes", "approved", "declined"):
                lines.append(f"           reply ({t['last_reply']['verdict']}): {t['last_reply']['text'][:110]!r}")
    pages = d.get("pages") or {}
    lines.append("\nrequest page: " + (pages.get("request_url") or "not yet — publish exports/requests.html (no capabilities; share it publicly) and record tickets.json"))
    lines.append("board page:   " + (pages.get("board_url") or "not yet — publish exports/tickets.html (capabilities {\"db\": {}}) and record tickets.json"))
    return "\n".join(lines)


def format_ticket(t: dict) -> str:
    s = ticket_summary(t)
    lines = [f"{t['id']}  {t['title']}   [{t['status']}]   {t['requester']['name']} <{t['requester']['email']}>   created {t['created'][:16]}",
             f"  next: {s['next'] or '—'}"]
    if t.get("jira"):
        lines.append(f"  jira: {t['jira'].get('url') or t['jira'].get('key')}   status there: {t['jira'].get('status') or '?'}   synced {str(t['jira'].get('synced') or '')[:16]}")
    lines += ["", "REQUEST"]
    for f in REQUEST_FIELDS:
        v = t["request"]["fields"].get(f["key"], "")
        if v:
            lines.append(f"  {f['ask']:<26s} {v.splitlines()[0]}" + ("".join(f"\n{' ' * 29}{ln}" for ln in v.splitlines()[1:])))
    if s["missing"]:
        lines.append(f"  MISSING: {', '.join(s['missing'])}")
    if t.get("model"):
        lines += ["", f"MODEL  models/{t['model']}"]
    if t["quotes"]:
        lines += ["", "QUOTES"]
        for q in t["quotes"]:
            e = q["estimate"]
            lines.append(f"  r{q['rev']}  {q['created'][:16]}  {q['model']} @{q['build_id']}  {q['material']} x{q['qty']}  "
                         f"{e['currency']} {e['total']:g}  ~{e['print_h']:g} h print  ~{e['lead_days']} d   {'sent ' + q['sent'][:16] if q['sent'] else 'NOT SENT'}")
    lines += ["", "THREAD"]
    for m in t["messages"]:
        head = f"  {m['when'][:16]}  {m['from']:<9s} {m['kind']:<8s}" + (f" [{m['verdict']}]" if m.get("verdict") else "")
        lines.append(head + "  " + (m["text"].splitlines()[0][:100] if m["text"] else ""))
    lines += ["", "HISTORY"] + [f"  {h['when'][:16]}  {h['from'] or '·':<9s} -> {h['to']:<9s} by {h['by']}" + (f"  {h['note']}" if h.get("note") else "") for h in t["history"]]
    return "\n".join(lines)


# ---------------------------------------------------------------- cli

def jira_check(project: str = "") -> int:
    """Verify the connection, resolve the service desk, and say how the portal form maps onto the request fields."""
    cfg = load_jira_cfg() or {}
    if project:
        cfg["project"] = project
    if not cfg.get("project"):
        print("give the JSM project key: uv run python scripts/tickets.py jira check --project PRINT"); return 2
    cfg.setdefault("transitions", jira_api.DEFAULT_TRANSITIONS); cfg.setdefault("field_labels", {}); cfg.setdefault("request_type", ""); cfg.setdefault("jql", "")
    creds = jira_api.credentials()
    if not creds:
        JIRA_JSON.parent.mkdir(parents=True, exist_ok=True)
        JIRA_JSON.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {JIRA_JSON.relative_to(ROOT)} for project {cfg['project']}; set JIRA_SITE, JIRA_EMAIL and JIRA_API_TOKEN, then run this again to verify")
        return 0
    client = jira_api.JiraClient(creds["site"], creds["email"], creds["token"])
    me = client.myself()
    print(f"connected to {creds['site']} as {me.get('displayName')} ({me.get('emailAddress')})")
    cfg["site"] = creds["site"]
    desks = client.service_desks()
    desk = next((d for d in desks if d["projectKey"].upper() == cfg["project"].upper()), None)
    if desk:
        cfg["service_desk_id"] = desk["id"]
        print(f"service desk {desk['id']} = project {desk['projectKey']} ({desk['projectName']})\nportal: {jira_api.portal_url(creds['site'], desk['id'])}")
        fmap = jira_field_map(cfg)
        for rt in client.request_types(desk["id"]):
            fields = client.request_type_fields(desk["id"], rt["id"])
            print(f"\nrequest type '{rt['name']}' (id {rt['id']}):")
            for f in fields:
                k = fmap(f["name"])
                print(f"  {f['name']:<34s} {'required' if f['required'] else '        '}  -> {k or 'UNMAPPED (add to field_labels in tickets/jira.json)'}")
            asked = {fmap(f["name"]) for f in fields}
            missing = [f["ask"] for f in REQUEST_FIELDS if f["required"] and f["key"] not in asked and f["key"] not in ("name", "email")]
            if missing:
                print(f"  not on this form (the ticket will show them as MISSING): {', '.join(missing)}")
    else:
        print(f"no service desk for project {cfg['project']} — it is not a Jira Service Management project (or the token cannot see it);"
              f" plain Jira works too, but requesters then need Jira accounts and get no portal.  Projects seen: {', '.join(d['projectKey'] for d in desks) or 'none'}")
    issues = client.search(f'project = "{cfg["project"]}" ORDER BY created DESC', fields="summary,status", limit=1)
    if issues:
        k = issues[0]["key"]
        print(f"\nnewest request {k} ({(issues[0]['fields'].get('status') or {}).get('name')}); transitions available from there: "
              + ", ".join(f"{t['name']}" + (f" -> {t['to']}" if t["to"] else "") for t in client.transitions(k)))
        print("  tickets/jira.json 'transitions' maps each local status to transition names (or target status names) to try, in order")
    JIRA_JSON.parent.mkdir(parents=True, exist_ok=True)
    JIRA_JSON.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {JIRA_JSON.relative_to(ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html", action="store_true", help="write exports/requests.html and exports/tickets.html")
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("show").add_argument("ticket")
    n = sub.add_parser("new")
    n.add_argument("--name", required=True); n.add_argument("--email", required=True); n.add_argument("--title", required=True)
    n.add_argument("--field", action="append", default=[], help="key=value (keys: " + ", ".join(FIELD_BY_KEY) + ")")
    n.add_argument("--text", type=Path, help="file with the request as written (parsed for Label: value lines)")
    f = sub.add_parser("fetch"); f.add_argument("--days", type=int, default=60)
    i = sub.add_parser("ingest"); i.add_argument("sync_dir", nargs="?", type=Path, default=SYNC_DIR); i.add_argument("--dry-run", action="store_true")
    q = sub.add_parser("quote"); q.add_argument("ticket"); q.add_argument("--model", required=True); q.add_argument("--material", default="")
    q.add_argument("--qty", type=int, default=0); q.add_argument("--note", default="", help="a paragraph to the requester at the top of the mail")
    s = sub.add_parser("send"); s.add_argument("ticket"); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--sent", default="", help="record an id from a send done elsewhere (Gmail connector) instead of sending")
    s.add_argument("--thread", default="")
    st = sub.add_parser("set"); st.add_argument("ticket"); st.add_argument("status", choices=STATUSES); st.add_argument("--note", default="")
    st.add_argument("--model", default=""); st.add_argument("--no-jira", action="store_true", help="change the repo record only")
    s.add_argument("--no-mail", action="store_true", help="Jira mode: post to Jira only, skip the SMTP copy")
    jr = sub.add_parser("jira", help="jira check [--project KEY]: verify the connection, resolve the service desk, report the portal fields")
    jr.add_argument("what", choices=["check"]); jr.add_argument("--project", default="")
    a = ap.parse_args()

    if a.cmd == "jira":
        return jira_check(a.project)

    if a.cmd == "show":
        t = load_ticket(a.ticket)
        print(json.dumps(t, indent=1) if a.json else format_ticket(t)); return 0
    if a.cmd == "new":
        fields = dict(kv.split("=", 1) for kv in a.field)
        text = a.text.read_text(encoding="utf-8") if a.text else ""
        if text:
            fields = parse_request_text(text) | fields
        t = new_ticket(name=a.name, mail=a.email, title=a.title, fields=fields, text=text)
        p = save_ticket(t)
        print(f"{t['id']} filed at {p.relative_to(ROOT)}" + (f"   missing: {', '.join(missing_fields(t['request']['fields']))}" if missing_fields(t["request"]["fields"]) else ""))
        return 0
    if a.cmd == "fetch":
        SYNC_DIR.mkdir(parents=True, exist_ok=True)
        if load_jira_cfg():
            reqs = jira_fetch()
            (SYNC_DIR / "jira.json").write_text(json.dumps(reqs, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{len(reqs)} Jira request(s) -> .sync/tickets/jira.json; now: uv run python scripts/tickets.py ingest")
            if not mail_creds():
                return 0
        mails = fetch_mail(a.days)
        (SYNC_DIR / "mail.json").write_text(json.dumps(mails, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{len(mails)} message(s) -> .sync/tickets/mail.json; now: uv run python scripts/tickets.py ingest"); return 0
    if a.cmd == "ingest":
        s_ = ingest(a.sync_dir, dry_run=a.dry_run)
        print(("DRY RUN\n" if a.dry_run else "") + json.dumps(s_, indent=1, ensure_ascii=False))
        for r in s_["new"] + s_["requests_filed"]:
            print(f"  new {r['ticket']}: {r['title']}" + (f"   MISSING {', '.join(r['missing'])}" if r["missing"] else ""))
        for r in s_["replies"]:
            print(f"  reply on {r['ticket']} read as {r['verdict']}: {r['text'][:100]!r}")
        for r in s_["jira_updated"]:
            print(f"  {r['ticket']} is now '{r['jira_status']}' in Jira")
        return 0
    if a.cmd == "quote":
        t = load_ticket(a.ticket)
        q_ = make_quote(t, a.model, material=a.material, qty=a.qty, note=a.note)
        set_status(t, "designing" if t["status"] in ("new",) else t["status"], by="me", note=f"quote r{q_['rev']} packaged from {a.model}")
        save_ticket(t)
        e = q_["estimate"]
        print(f"{t['id']} quote r{q_['rev']} from {a.model}: {e['material']} x{e['qty']}, ~{e['mass_g']:g} g, ~{e['print_h']:g} h, "
              f"{e['currency']} {e['total']:g}, ~{e['lead_days']} day(s)\n  package: {quote_dir(t, q_['rev']).relative_to(ROOT)}/  "
              f"({', '.join(q_['attachments'])})\n  send:    uv run python scripts/tickets.py send {t['id']}")
        return 0
    if a.cmd == "send":
        t = load_ticket(a.ticket)
        if a.sent:
            record_sent(t, a.sent, a.thread); save_ticket(t); print(f"{t['id']} recorded as sent ({a.sent}); status {t['status']}"); return 0
        if (t.get("jira") or {}).get("key") and load_jira_cfg():
            if a.dry_run:
                print(f"dry run: would post quote r{t['quotes'][-1]['rev'] if t['quotes'] else '?'} as a public comment on {t['jira']['key']} with "
                      f"{', '.join(Path(x).name for x in outbox(t)['attachments'])} attached, then transition to 'quoted'"
                      + ("" if a.no_mail or not mail_creds() else ", and e-mail the same package"))
                return 0
            r = jira_send_quote(t)
            record_sent(t, f"jira-comment-{r['comment_id']}" if r["comment_id"] else f"jira-{r['key']}-r{r['rev']}")
            t["messages"][-1]["jira"] = r["transition"]
            mailed = ""
            if not a.no_mail and mail_creds():
                m = send_quote(t)
                mailed = f"; e-mailed to {', '.join(m['outbox']['to'])}" if m["sent"] else ""
            save_ticket(t)
            print(f"posted quote r{r['rev']} on {r['key']} with {', '.join(r['attached']) or 'no attachments'}; {r['transition'] or 'no transition'}{mailed}; {t['id']} is now quoted")
            return 0
        r = send_quote(t, dry_run=a.dry_run)
        if r["sent"]:
            record_sent(t, r["message_id"]); save_ticket(t)
            print(f"sent {r['outbox']['subject']} to {', '.join(r['outbox']['to'])}; {t['id']} is now quoted")
        else:
            print(f"not sent ({r['why']}). Outbox for the Gmail connector:\n" + json.dumps(r["outbox"], indent=1)
                  + f"\n\nafter sending: uv run python scripts/tickets.py send {t['id']} --sent <message id> [--thread <thread id>]")
        return 0
    if a.cmd == "set":
        t = load_ticket(a.ticket)
        if a.model:
            t["model"] = a.model
        set_status(t, a.status, note=a.note)
        moved = "" if a.no_jira or not load_jira_cfg() else jira_transition(t, a.status, comment=a.note)
        save_ticket(t)
        print(f"{t['id']} -> {t['status']}" + (f"   {moved}" if moved else "") + (f"   next: {NEXT[t['status']]}" if NEXT[t["status"]] else "")); return 0

    d = page_data()
    print(json.dumps(d, indent=1) if a.json else format_board(d))
    if a.html:
        r_ = write_html(d, "request", OUT_REQUESTS); b_ = write_html(d, "board", OUT_BOARD)
        print(f"\nrequest page {r_.relative_to(ROOT)} ({r_.stat().st_size // 1024} kB) — public form, publish with NO capabilities and share the link\n"
              f"board page   {b_.relative_to(ROOT)} ({b_.stat().st_size // 1024} kB) — internal, publish with capabilities {{\"db\": {{}}}}")
        pages = d.get("pages") or {}
        for k in ("request_url", "board_url"):
            if pages.get(k):
                print(f"  {k}: {pages[k]}  — republish with the Artifact tool, url=<that>, same file path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
