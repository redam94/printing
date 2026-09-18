#!/usr/bin/env python
"""Build the public GitHub Pages site: a sales page for the print service, the work, and how to order.

    uv run python scripts/site.py                  # -> _site/  (open _site/index.html)
    uv run python scripts/site.py --serve          # build, then serve on http://localhost:8000
    uv run python scripts/site.py --deploy         # build, then force-push _site/ to the gh-pages branch

Everything comes from what the repo already has: each model's last build
(``models/<p>/exports/build_report.json``, STLs, ``view.html``, STL/STEP/3MF), its print reports
(``models/<p>/prints.json``), the rates (``tickets/pricing.json``), the Jira portal
(``tickets/jira.json``) and the sales copy (``site.json``). Build models first
(``scripts/build.py --all``). Product shots come from ``scripts/product_shot.py`` (headless
Chrome), cached next to the build as ``exports/renders/_shot.png``; without Chrome the build's
render PNGs are used.

The look is the Augur design system: warm cream paper, green-cast ink, sage primary, Fraunces
display type, IBM Plex Sans body, JetBrains Mono for every number. ``_site/brand/`` gets a logo
and a banner in the same palette for the Jira portal (Jira takes them as uploads).

Never published: anything from ``tickets/``, ``ideas/`` or inspiration photos, and any model a
ticket points at (a design made for someone is theirs, not a showcase piece). The 3D viewer is
copied with its Notes tab hidden (notes left on a static page would never reach the repo).

``gh-pages`` is an orphan branch rewritten on every deploy, so the exported meshes never
accumulate in history. Files over ``MAX_FILE_MB`` are skipped (GitHub refuses files over 100 MB).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR, PRINTER, ROOT, list_projects  # noqa: E402
from scripts.tickets import TICKETS_DIR, design_fee, estimate, load_pricing  # noqa: E402

OUT = ROOT / "_site"
REPO_URL = "https://github.com/redam94/printing"
MAX_FILE_MB = 50
ACRONYMS = {"esp32": "ESP32", "pi": "Pi", "pi5": "Pi 5", "devkit": "DevKit", "l": "L"}
# the viewer is written for the artifact host, which supplies the charset, viewport and [hidden] rule
VIEWER_HEAD = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               "<style>body{margin:0}[hidden]{display:none!important}#tabNotes,#segNotes,#paneNotes{display:none!important}</style>")

# Augur tokens (Claude Design), the same values as the author's site theme
AUGUR = {
    "cream": "#faf8f3", "card": "#ffffff", "well": "#f3f0e6", "line": "#e8e4d5",
    "ink": "#2a3528", "ink2": "#4a5a48", "sage": "#5a7a3a", "sage_dark": "#46612c",
    "sage_soft": "#e7eddc", "gold": "#b8860b", "gold_soft": "#f6edd4", "steel": "#4a6d8a", "rust": "#a04535",
    "rust_soft": "#f4e3df",
}

esc = html.escape


def title_of(project: str) -> str:
    words = [ACRONYMS.get(w, w) for w in project.split("_")]
    s = " ".join(words)
    return s[:1].upper() + s[1:]


LIB_CATEGORIES = {   # category -> (plain name, what a visitor would call the things in it)
    "fasteners": ("Fasteners", "Pockets for brass heat-set inserts, screw bosses, captive nuts and clearance holes."),
    "patterns": ("Hole patterns", "Raspberry Pi, ESP32, fan, VESA and DIN-rail footprints, with the connector windows to match."),
    "primitives": ("Enclosure parts", "Rounded boxes and lids, vent grids, cable grommets, feet, edge clips and slot racks."),
    "mechanisms": ("Mechanisms", "Snap fits, latches, living hinges and flexures that come off the printer ready to move."),
    "form": ("Shapes and textures", "Fluting, twists, surface textures and organic outlines for decorative pieces."),
}
LIB_NAMES = {"heat_set_boss": "Heat-set insert boss", "heat_set_pocket": "Heat-set insert pocket", "pi5_mount": "Raspberry Pi 5 mount",
             "pi4_mount": "Raspberry Pi 4 mount", "pi_zero_mount": "Raspberry Pi Zero mount", "pi5_port_cutouts": "Pi 5 port windows",
             "pi_board_outline": "Raspberry Pi outline", "esp32_footprint": "ESP32 board footprint", "esp32_header_rows": "ESP32 header pockets",
             "vesa_mount": "VESA mount pattern", "din_rail_ts35_profile": "DIN rail profile", "pcb_slot_cradle": "PCB slot cradle",
             "sdf_solid": "Sculpted solid", "l_bracket": "L bracket", "rubber_foot_recess": "Rubber-foot recess",
             "pip_hinge": "Print-in-place hinge", "flex_fingers": "Compliant finger comb", "zip_tie_slot": "Cable-tie slots",
             "living_hinge_web": "Living hinge", "living_hinge_lattice": "Lattice living hinge", "notch_rack": "Notch rack"}


def lib_name(cid: str) -> str:
    name = cid.split(".", 1)[-1]
    return LIB_NAMES.get(name) or (name.replace("_", " ")[:1].upper() + name.replace("_", " ")[1:])


def rst_inline(text: str) -> str:
    """Escape, then turn ``literal`` into <code>."""
    return re.sub(r"``(.+?)``", r"<code>\1</code>", esc(text))


def paragraphs(text: str) -> str:
    return "".join(f"<p>{rst_inline(' '.join(p.split()))}</p>" for p in text.strip().split("\n\n") if p.strip())


def fmt_size(b: int) -> str:
    return f"{b / 1e6:.1f} MB" if b >= 1e6 else f"{b / 1e3:.0f} KB"


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def report_text(text: str) -> str:
    """Drop the sync bookkeeping prefix ("Reported in chat, not on the review page:") and capitalise."""
    text = re.sub(r"^Reported in chat[^:]*:\s*", "", text)
    # build ids and commit hashes mean nothing to a visitor
    text = re.sub(r"\s*\((?:build|commit) [^)]*\)", "", text)
    text = re.sub(r"\bBuild \d{8}-\d{6}(?: \(commit \w+\))?\s*(?:—|-)?\s*", "", text)
    text = re.sub(r"\bbuild \d{8}-\d{6}\s*", "", text)
    text = re.sub(r"([.!?] )([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    return text[:1].upper() + text[1:]


def money(x: float, cur: str = "USD", cents: bool = True) -> str:
    s = f"{x:,.2f}" if cents else f"{x:,.0f}"
    return f"${s}" if cur == "USD" else f"{s} {cur}"


def dims(bb) -> str:
    return " × ".join(f"{x:.0f}" for x in bb)


# ---------------------------------------------------------------- data

def ticket_models() -> set[str]:
    """Models built for a ticket: private to that requester."""
    return {t.get("model") for t in (load_json(p, {}) for p in TICKETS_DIR.glob("*/ticket.json")) if t.get("model")}


def collect() -> dict:
    pricing = load_pricing()
    cfg = load_json(ROOT / "site.json", {})
    copy = cfg.get("models") or {}
    private = ticket_models() | set(cfg.get("hidden") or [])
    order = {p: i for i, p in enumerate(cfg.get("order") or [])}
    designs = []
    for p in list_projects():
        if p in private:
            continue
        exports = MODELS_DIR / p / "exports"
        report = load_json(exports / "build_report.json", {})
        if not report:
            continue
        prints = load_json(MODELS_DIR / p / "prints.json", {}).get("prints", [])
        doc = (report.get("docstring") or "").strip()
        summary, _, rest = doc.partition("\n\n")
        parts = []
        for name, rp in (report.get("parts") or {}).items():
            m, pr = rp.get("metrics") or {}, rp.get("printability") or {}
            parts.append({"name": name, "bbox": m.get("bbox_size") or [0, 0, 0], "volume": m.get("volume") or 0,
                          "wall_min": pr.get("wall_min_mm"), "ok": pr.get("ok"), "mode": rp.get("print_mode") or "normal",
                          "warnings": pr.get("warnings") or [], "problems": pr.get("problems") or [],
                          "render": exports / "renders" / f"{name}.png", "stl": exports / f"{name}.stl"})
        files = []
        names = {x["name"] for x in parts}
        for f in sorted(exports.glob("*")):
            if f.suffix in (".stl", ".step") and f.stem in names or f.suffix == ".3mf" and f.stem == p:
                files.append(f)
        outcomes = [x.get("outcome") for x in prints]
        ok_materials = sorted({x.get("material") for x in prints if x.get("outcome") == "ok" and x.get("material")})
        c = copy.get(p) or {}
        designs.append({
            "project": p, "title": c.get("title") or title_of(p), "kind": c.get("kind") or "",
            "tagline": c.get("tagline") or " ".join(summary.split()), "story": c.get("story") or "",
            "built_at": report.get("built_at", ""), "report": report,
            "summary": " ".join(summary.split()), "details": rest, "parts": parts, "prints": prints,
            "status": "printed" if "ok" in outcomes else "failed" if outcomes else "unprinted", "ok_materials": ok_materials,
            "components": report.get("components") or [], "plate": report.get("plate") or {},
            "viewer": exports / "view.html", "files": files,
            # a piece on this page already exists, so its price is the print price alone
            "estimate": estimate(report, "PLA", 1, pricing, design="none"),
        })
    designs.sort(key=lambda d: (order.get(d["project"], len(order)), d["title"]))
    j = load_json(ROOT / "tickets" / "jira.json", {})
    site = (j.get("site") or "").rstrip("/")
    portal = f"{site}/servicedesk/customer/portal/{j['service_desk_id']}" if site and j.get("service_desk_id") else ""
    return {"designs": designs, "pricing": pricing, "jira": j, "portal": portal,
            "help": f"{site}/wiki/spaces/PRINTHELP" if site else "", "cfg": cfg,
            "brand": cfg.get("brand") or "3D Printing Service", "library": library(designs)}


def library(designs: list[dict]) -> dict:
    """The component library as a visitor would see it: categories with counts, and each component
    with how many of the published designs use it and which materials it has been printed in."""
    comps = (load_json(ROOT / "parts.json", {}).get("components") or {})
    used: dict[str, set[str]] = {}
    printed: dict[str, set[str]] = {}
    for d in designs:
        for c in d["components"]:
            used.setdefault(c["id"], set()).add(d["project"])
            printed.setdefault(c["id"], set()).update(c.get("field_validated") or [])
    items = []
    for cid, c in comps.items():
        notes = c.get("material_notes") or {}
        mats = set(notes.get("validated") or []) | set(notes.get("field_validated") or []) | printed.get(cid, set())
        items.append({"id": cid, "name": lib_name(cid), "category": c.get("category") or cid.split(".")[0],
                      "summary": c.get("summary", ""), "used_in": sorted(used.get(cid, ())), "printed_in": sorted(mats),
                      "in_use": sorted(printed.get(cid, ()))})
    cats = []
    for key, (name, blurb) in LIB_CATEGORIES.items():
        n = sum(1 for x in items if x["category"] == key)
        if n:
            cats.append({"key": key, "name": name, "blurb": blurb, "count": n})
    return {"count": len(items), "categories": cats, "components": items,
            "printed": sum(1 for x in items if x["printed_in"]), "used": sum(1 for x in items if x["used_in"])}


# ---------------------------------------------------------------- page shell

CSS = """
:root{
  color-scheme:light;
  --cream:%(cream)s; --card:%(card)s; --well:%(well)s; --line:%(line)s;
  --ink:%(ink)s; --ink-2:%(ink2)s; --sage:%(sage)s; --sage-dark:%(sage_dark)s; --sage-soft:%(sage_soft)s;
  --gold:%(gold)s; --gold-soft:%(gold_soft)s; --steel:%(steel)s; --rust:%(rust)s; --rust-soft:%(rust_soft)s;
  --shadow:0 1px 2px 0 rgb(42 53 40 / .05);
  --display:"Fraunces",Georgia,"Times New Roman",serif;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;
  --wrap:1160px;
}
/* Augur is a light-only warm-paper identity: the same palette in every viewer theme */
*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
body{margin:0;background:var(--cream);color:var(--ink);font:16px/1.65 var(--sans);-webkit-font-smoothing:antialiased}
a{color:var(--sage)} a:hover{color:var(--sage-dark)}
:focus-visible{outline:2px dashed var(--sage);outline-offset:2px}
img{max-width:100%%;height:auto;display:block}
h1,h2,h3{font-family:var(--display);font-weight:600;letter-spacing:-.02em;line-height:1.12;margin:0;text-wrap:balance;color:var(--ink)}
h1{font-size:clamp(38px,5.4vw,64px);font-optical-sizing:auto}
h2{font-size:clamp(28px,3.4vw,40px)}
h3{font-size:21px;letter-spacing:-.01em}
p{margin:0}
.num,code{font-family:var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.01em}
code{font-size:.86em;background:var(--well);padding:1px 5px;border-radius:4px;overflow-wrap:anywhere}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2)}
.muted{color:var(--ink-2)}
.wrap{max-width:var(--wrap);margin-inline:auto;padding-inline:24px}
@media (max-width:520px){.wrap{padding-inline:18px}}
.band{padding-block:88px}
.band.well{background:var(--well);border-block:1px solid var(--line)}
.band.ink{background:var(--ink);color:var(--cream)}
.band.ink h2,.band.ink h3{color:var(--cream)}
.band.ink .eyebrow,.band.ink .muted{color:#c9d2bf}
@media (max-width:700px){.band{padding-block:60px}}
.head{display:grid;gap:12px;max-width:680px;margin-bottom:40px}
.head p{font-size:18px;color:var(--ink-2)}

/* header */
.top{position:sticky;top:env(safe-area-inset-top,0px);z-index:10;background:rgb(250 248 243 / .92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:center;gap:28px;min-height:64px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--ink);font-family:var(--display);font-weight:600;font-size:20px;letter-spacing:-.01em}
.brand svg{flex:none}
.nav{display:flex;gap:22px;margin-left:auto;align-items:center;flex-wrap:wrap}
.nav a{color:var(--ink-2);text-decoration:none;font-weight:500;font-size:15px}
.nav a:hover,.nav a[aria-current]{color:var(--ink)}
.nav a[aria-current]{text-decoration:underline wavy var(--sage);text-underline-offset:8px}
@media (max-width:760px){.nav .opt{display:none}}

/* buttons */
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 20px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);text-decoration:none;font-weight:600;font-size:15px;line-height:1.2;box-shadow:var(--shadow);transition:background .15s,border-color .15s,transform .15s}
.btn:hover{border-color:var(--ink-2);color:var(--ink)}
.btn.primary{background:var(--sage);border-color:var(--sage);color:#fff}
.btn.primary:hover{background:var(--sage-dark);border-color:var(--sage-dark);color:#fff}
.btn.small{padding:8px 14px;font-size:14px}
.btn .arr{transition:transform .15s}
.btn:hover .arr{transform:translateX(3px)}
.band.ink .btn:not(.primary){background:transparent;color:var(--cream);border-color:#5d6a59}
.actions{display:flex;gap:12px;flex-wrap:wrap}

/* hero */
.hero{padding-block:64px 80px}
.hero .wrap{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:56px;align-items:center}
@media (max-width:900px){.hero .wrap{grid-template-columns:1fr;gap:36px}}
.hero-copy{display:grid;gap:24px}
.hero-copy .lede{font-size:20px;color:var(--ink-2);max-width:34em}
.hero h1 em{font-style:italic;color:var(--sage)}
.assure{display:flex;gap:18px;flex-wrap:wrap;font-size:14px;color:var(--ink-2)}
.assure span{display:inline-flex;gap:7px;align-items:center}
.assure svg{color:var(--sage)}
.plate{position:relative;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);overflow:hidden}
.plate img{width:100%%;aspect-ratio:4/3;object-fit:cover;background:var(--cream)}
.plate .spec{position:absolute;left:14px;right:14px;bottom:14px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:end}
.tag{display:inline-flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:5px 10px;font-size:13px;box-shadow:var(--shadow)}
.tag .num{font-size:12.5px}
.tag.ok{background:var(--sage-soft);border-color:transparent;color:var(--sage-dark);font-weight:600}
.plate .grid-mark{position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:32px 32px;opacity:.35;mask-image:linear-gradient(to bottom,transparent 55%%,#000)}

/* proof strip */
.proof{border-block:1px solid var(--line);background:var(--card)}
.proof .wrap{display:grid;grid-template-columns:repeat(4,1fr);}
.proof div{padding:22px 18px;border-left:1px solid var(--line);display:grid;gap:2px}
.proof div:first-child{border-left:0}
.proof b{font-family:var(--mono);font-size:26px;font-weight:500;letter-spacing:-.02em}
.proof span{font-size:14px;color:var(--ink-2)}
@media (max-width:700px){.proof .wrap{grid-template-columns:1fr 1fr}.proof div:nth-child(3){border-left:0}.proof div:nth-child(n+3){border-top:1px solid var(--line)}}

/* steps */
.steps{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;counter-reset:s;border-top:2px solid var(--ink)}
.steps li{counter-increment:s;padding:22px 22px 0 0;display:grid;gap:8px;align-content:start}
.steps li::before{content:"Step " counter(s);font-family:var(--mono);font-size:12.5px;color:var(--sage);letter-spacing:.02em}
.steps p{color:var(--ink-2);font-size:15.5px}
.steps.five{grid-template-columns:repeat(5,minmax(0,1fr))}
@media (max-width:900px){.steps,.steps.five{grid-template-columns:1fr 1fr;row-gap:28px}}
@media (max-width:520px){.steps,.steps.five{grid-template-columns:1fr}}

/* work grid */
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px}
.filters button{font:inherit;font-size:14px;padding:6px 14px;border-radius:99px;border:1px solid var(--line);background:var(--card);color:var(--ink-2);cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--cream)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:22px}
@media (max-width:360px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;text-decoration:none;color:inherit;display:flex;flex-direction:column;box-shadow:var(--shadow);transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--sage);transform:translateY(-2px);color:inherit}
.card .img{background:var(--cream);border-bottom:1px solid var(--line)}
.card .img img{width:100%%;aspect-ratio:4/3;object-fit:cover}
.card .body{padding:18px 20px 20px;display:flex;flex-direction:column;gap:8px;flex:1}
.card .kind{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2)}
.card p{color:var(--ink-2);font-size:15px}
.card .foot{margin-top:auto;padding-top:12px;display:flex;justify-content:space-between;align-items:center;gap:8px;border-top:1px solid var(--line);font-size:14px}
.price{font-family:var(--mono);font-weight:500}
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;padding:3px 10px;border-radius:99px;background:var(--well);color:var(--ink-2)}
.pill.ok{background:var(--sage-soft);color:var(--sage-dark)}
.pill.bad{background:var(--rust-soft);color:var(--rust)}
.pill.gold{background:var(--gold-soft);color:#7d5b06}
.pill::before{content:"";width:6px;height:6px;border-radius:50%%;background:currentColor}

/* quote anatomy */
.quote-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:48px;align-items:center}
@media (max-width:900px){.quote-grid{grid-template-columns:1fr}}
.features{display:grid;gap:22px}
.feature{display:grid;grid-template-columns:40px 1fr;gap:14px}
.feature .ico{width:40px;height:40px;border-radius:10px;background:var(--sage-soft);color:var(--sage-dark);display:grid;place-items:center}
.feature h3{font-family:var(--sans);font-size:17px;letter-spacing:0;margin-bottom:2px}
.feature p{color:var(--ink-2);font-size:15.5px}
.sheet{background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:0 18px 40px -24px rgb(42 53 40 / .35);overflow:hidden}
.sheet .bar{display:flex;justify-content:space-between;gap:10px;padding:14px 20px;border-bottom:1px solid var(--line);font-size:14px;flex-wrap:wrap}
.sheet .bar b{font-family:var(--mono);font-weight:500}
.sheet .pic{background:var(--cream);border-bottom:1px solid var(--line)}
.sheet .pic img{aspect-ratio:16/9;object-fit:cover;width:100%%}
.rows{display:grid;grid-template-columns:auto 1fr;gap:0;font-size:14.5px}
.rows dt,.rows dd{margin:0;padding:9px 20px;border-bottom:1px solid var(--line)}
.rows dt{color:var(--ink-2)}
.rows dd{text-align:right;font-family:var(--mono);font-size:13.5px}
.rows .total{font-weight:600;color:var(--ink);font-size:15px}
.sheet .reply{padding:14px 20px;background:var(--well);font-size:14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.kbd{font-family:var(--mono);font-size:12.5px;background:var(--card);border:1px solid var(--line);border-bottom-width:2px;border-radius:5px;padding:2px 8px}

/* pricing + materials */
.price-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:40px;align-items:start}
@media (max-width:900px){.price-grid{grid-template-columns:1fr}}
.ledger{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.ledger table{width:100%%;border-collapse:collapse;font-size:15px}
.ledger th,.ledger td{padding:11px 18px;border-bottom:1px solid var(--line);text-align:left}
.ledger th{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);background:var(--well);font-weight:600}
.ledger td.r,.ledger th.r{text-align:right}
.ledger tr:last-child td{border-bottom:0}
.ledger a{color:var(--ink);text-decoration:none;font-weight:500}
.ledger a:hover{color:var(--sage)}
.tablewrap{overflow-x:auto}
.formula{display:grid;gap:14px;counter-reset:f}
.formula div{display:grid;grid-template-columns:130px 1fr;gap:14px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.formula dt{font-weight:600}
.formula dd{margin:0;color:var(--ink-2)}
@media (max-width:520px){.formula div{grid-template-columns:1fr;gap:2px}}
.mats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
@media (max-width:900px){.mats{grid-template-columns:1fr 1fr}}
@media (max-width:460px){.mats{grid-template-columns:1fr}}
.mat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;display:grid;gap:8px;align-content:start}
.mat .sw{height:8px;border-radius:4px}
.mat b{font-family:var(--display);font-size:24px;font-weight:600}
.mat p{color:var(--ink-2);font-size:15px}
.mat .num{font-size:13px;color:var(--ink-2)}
.tiers{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:28px}
@media (max-width:760px){.tiers{grid-template-columns:1fr}}
.tier{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;display:grid;gap:6px;align-content:start}
.tier .fee{font-family:var(--mono);font-size:30px;font-weight:500;letter-spacing:-.03em}
.tier .fee small{font-size:14px;color:var(--ink-2);font-family:var(--sans);letter-spacing:0;margin-left:6px}
.tier b{font-size:16px}
.tier p{color:var(--ink-2);font-size:15px}
.tier.hi{border-color:var(--sage);box-shadow:0 0 0 3px var(--sage-soft)}
.examples{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:28px}
.ex{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;display:grid;gap:10px;align-content:start}
.ex h3{font-family:var(--sans);font-size:16px;letter-spacing:0}
.ex p{color:var(--ink-2);font-size:14.5px}
.ex .sum{display:grid;grid-template-columns:1fr auto;gap:4px 12px;font-size:14px;border-top:1px solid var(--line);padding-top:10px;align-items:start}
.ex .sum>span:nth-child(even){font-family:var(--mono);text-align:right;white-space:nowrap}
.ex .sum .muted{font-size:13px}
.ex .sum .t{font-weight:600;border-top:1px solid var(--line);padding-top:6px;margin-top:2px}

/* library */
.cats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}
@media (max-width:1000px){.cats{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:640px){.cats{grid-template-columns:1fr 1fr}}
@media (max-width:400px){.cats{grid-template-columns:1fr}}
.cat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;display:grid;gap:6px;align-content:start}
.cat b{font-family:var(--mono);font-size:30px;font-weight:500;letter-spacing:-.03em;color:var(--sage-dark)}
.cat h3{font-family:var(--sans);font-size:16px;letter-spacing:0}
.cat p{color:var(--ink-2);font-size:14.5px}
.lib-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:48px;align-items:start;margin-top:48px}
@media (max-width:900px){.lib-grid{grid-template-columns:1fr;gap:28px}}
.lib-grid .prose p{color:var(--ink-2)}
.ledger td .muted{font-size:13px}

/* faq */
.faq{display:grid;gap:0;border-top:1px solid var(--line);max-width:820px}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{cursor:pointer;list-style:none;padding:20px 40px 20px 0;font-family:var(--display);font-size:20px;font-weight:600;position:relative}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";position:absolute;right:4px;top:16px;font-family:var(--mono);font-size:22px;color:var(--sage)}
.faq details[open] summary::after{content:"–"}
.faq details p{padding:0 40px 22px 0;color:var(--ink-2);max-width:66ch}

/* cta */
.cta .wrap{display:grid;grid-template-columns:minmax(0,1.3fr) auto;gap:32px;align-items:center}
@media (max-width:760px){.cta .wrap{grid-template-columns:1fr}}
.cta p{font-size:18px}

/* detail pages */
.crumbs{font-size:14px;color:var(--ink-2);padding-top:28px}
.crumbs a{color:var(--ink-2)}
.detail{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:48px;align-items:start;padding-block:24px 64px}
@media (max-width:900px){.detail{grid-template-columns:1fr;gap:28px}}
.detail .copy{display:grid;gap:20px;position:sticky;top:88px}
@media (max-width:900px){.detail .copy{position:static}}
.detail .copy .lede{font-size:19px;color:var(--ink-2)}
.facts{display:grid;grid-template-columns:auto 1fr;border-top:1px solid var(--line);font-size:15px}
.facts dt,.facts dd{margin:0;padding:10px 0;border-bottom:1px solid var(--line)}
.facts dt{color:var(--ink-2);padding-right:24px}
.facts dd{text-align:right}
.bigprice{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.bigprice b{font-family:var(--mono);font-weight:500;font-size:34px;letter-spacing:-.03em}
.gallery{display:grid;gap:16px}
.gallery figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.gallery figcaption{padding:10px 16px;font-size:14px;color:var(--ink-2);border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.tech{border:1px solid var(--line);border-radius:12px;background:var(--card);margin-top:8px}
.tech>summary{cursor:pointer;padding:18px 22px;font-weight:600;list-style:none;display:flex;justify-content:space-between}
.tech>summary::after{content:"Show";font-size:14px;color:var(--sage);font-weight:500}
.tech[open]>summary::after{content:"Hide"}
.tech>div{padding:0 22px 22px;display:grid;gap:22px}
.tech h3{font-family:var(--sans);font-size:15px;letter-spacing:0;margin-bottom:8px}
.tech table{width:100%%;border-collapse:collapse;font-size:14px}
.tech th,.tech td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.tech th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2);font-weight:600}
.files{list-style:none;margin:0;padding:0}
.files li{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px}
.log{list-style:none;margin:0;padding:0;display:grid;gap:14px}
.log li{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;display:grid;gap:8px}
.log .top-line{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:14px}
.log p{color:var(--ink-2);font-size:15px;max-width:75ch}
.prose{display:grid;gap:14px;max-width:68ch}
.prose p,.prose li{color:var(--ink-2)}
.fields{display:grid;gap:0;border-top:1px solid var(--line)}
.fields div{display:grid;grid-template-columns:220px 1fr;gap:18px;padding:14px 0;border-bottom:1px solid var(--line)}
.fields b{font-weight:600}
.fields p{color:var(--ink-2)}
@media (max-width:620px){.fields div{grid-template-columns:1fr;gap:4px}}
.status-flow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:14px}
.status-flow .arrow{color:var(--ink-2)}

footer{background:var(--ink);color:#c9d2bf;font-size:14px}
footer .wrap{padding-block:40px;display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap}
footer a{color:var(--cream)}
footer .brand{color:var(--cream)}
""" % AUGUR

LOGO_SVG = """<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="%(sage)s"/>
<path d="M11 6h10v5l-3 4h-4l-3-4z" fill="%(cream)s"/><rect x="7" y="19" width="18" height="2.4" rx="1.2" fill="%(cream)s"/>
<rect x="9" y="23.2" width="14" height="2.4" rx="1.2" fill="%(cream)s" opacity=".8"/><rect x="11" y="27.4" width="10" height="2" rx="1" fill="%(cream)s" opacity=".6"/></svg>""" % AUGUR

ICONS = {
    "check": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 8.5l3 3 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "cube": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M10 2l7 4v8l-7 4-7-4V6z M3 6l7 4 7-4 M10 10v8" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
    "ruler": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><rect x="2" y="7" width="16" height="6" rx="1" stroke="currentColor" stroke-width="1.6"/><path d="M6 7v3M10 7v3M14 7v3" stroke="currentColor" stroke-width="1.6"/></svg>',
    "tag": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M3 3h7l7 7-7 7-7-7z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><circle cx="7" cy="7" r="1.4" fill="currentColor"/></svg>',
    "chat": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M3 4h14v9H8l-4 3v-3H3z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
}
FONTS = ("https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500"
         "&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap")


def page(title: str, body: str, data: dict, *, depth: int, current: str = "", description: str = "") -> str:
    up = "../" * depth
    links = [("work", "index.html#work", "Work", ""), ("how", "index.html#how", "How it works", "opt"),
             ("pricing", "index.html#pricing", "Pricing", "opt"), ("library", "index.html#library", "Parts library", "opt"),
             ("prints", "prints.html", "Track record", "opt"), ("order", "request.html", "How to order", "")]
    nav = "".join(f'<a class="{cls}" href="{up}{href}"{" aria-current=page" if key == current else ""}>{label}</a>'
                  for key, href, label, cls in links)
    cta = f'<a class="btn primary small" href="{esc(data["portal"])}">Request a part</a>' if data["portal"] else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description or data['cfg'].get('tagline', ''))}">
<meta name="theme-color" content="{AUGUR['cream']}">
<link rel="icon" href="{up}brand/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{up}style.css">
</head><body>
<header class="top"><div class="wrap">
<a class="brand" href="{up}index.html">{LOGO_SVG}{esc(data['brand'])}</a>
<nav class="nav" aria-label="Main">{nav}{cta}</nav>
</div></header>
<main>
{body}
</main>
<footer><div class="wrap">
<div style="display:grid;gap:8px"><a class="brand" href="{up}index.html" style="text-decoration:none">{LOGO_SVG}{esc(data['brand'])}</a>
<span>Custom parts designed in <a href="https://github.com/gumyr/build123d">build123d</a> and printed on a {esc(PRINTER['name'])}.</span></div>
<div style="display:grid;gap:6px;align-content:start">
{f'<a href="{esc(data["portal"])}">Request portal</a>' if data['portal'] else ''}
<a href="{up}request.html">How to order</a><a href="{up}prints.html">Track record</a>
<a href="{REPO_URL}">Source on GitHub</a><span class="num" style="font-size:12px">Updated {date.today().isoformat()}</span></div>
</div></footer>
</body></html>
"""


def status_pill(d: dict) -> str:
    if d["status"] == "printed":
        mats = "/".join(d["ok_materials"])
        return f'<span class="pill ok">Printed{" in " + esc(mats) if mats else ""}</span>'
    if d["status"] == "failed":
        return '<span class="pill gold">In testing</span>'
    return '<span class="pill">Ready to print</span>'


# ---------------------------------------------------------------- images

def product_shot(d: dict) -> Path | None:
    """Cached clean render of all parts; falls back to the build's first render PNG."""
    ex = MODELS_DIR / d["project"] / "exports"
    cache = ex / "renders" / "_shot.png"
    rep = ex / "build_report.json"
    if not cache.exists() or cache.stat().st_mtime < rep.stat().st_mtime:
        try:
            from scripts.product_shot import shot
            stls = [p["stl"] for p in d["parts"] if p["stl"].exists()]
            if not shot(stls, cache):
                cache = None
        except Exception as e:  # noqa: BLE001 - a missing picture must not break the site
            print(f"  product shot for {d['project']} failed: {e}")
            cache = None
    return cache if cache and cache.exists() else next((p["render"] for p in d["parts"] if p["render"].exists()), None)


def frame(im, aspect: float = 4 / 3, pad: float = 0.12):
    """Crop a render to its subject plus a margin, at a fixed aspect, on the render's own ground colour."""
    from PIL import Image, ImageChops
    ground = im.getpixel((2, 2))
    box = ImageChops.difference(im, Image.new("RGB", im.size, ground)).convert("L").point(lambda v: 255 if v > 10 else 0).getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) * (1 + 2 * pad), (y1 - y0) * (1 + 2 * pad)
    w, h = max(w, h * aspect), max(h, w / aspect)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    canvas = Image.new("RGB", (int(w), int(h)), ground)
    canvas.paste(im, (int(w / 2 - cx), int(h / 2 - cy)))
    if canvas.width > 1200:
        canvas = canvas.resize((1200, int(1200 / aspect)), Image.LANCZOS)
    return canvas


def place_images(d: dict, out: Path) -> str:
    """Copy the product shot (full + card size) into the design's folder; returns the relative name or ''."""
    src = product_shot(d)
    if not src:
        return ""
    ddir = out / "designs" / d["project"]
    try:
        from PIL import Image
        with Image.open(src) as im:
            im = frame(im.convert("RGB"))
            im.save(ddir / "shot.jpg", quality=88, optimize=True, progressive=True)
            im.thumbnail((720, 540))
            im.save(ddir / "card.jpg", quality=84, optimize=True, progressive=True)
    except Exception:  # noqa: BLE001
        shutil.copyfile(src, ddir / "shot.jpg")
        shutil.copyfile(src, ddir / "card.jpg")
    return "shot.jpg"


def brand_assets(data: dict, out: Path) -> None:
    """Logo (SVG + 512 px PNG) and a 1600x400 portal banner in the Augur palette, for the Jira portal."""
    bdir = out / "brand"
    bdir.mkdir(exist_ok=True)
    (bdir / "logo.svg").write_text(LOGO_SVG.replace('width="30" height="30"', 'width="512" height="512" xmlns="http://www.w3.org/2000/svg"'), encoding="utf-8")
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return

    def rgb(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    s = 512 / 32
    logo = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    g = ImageDraw.Draw(logo)
    g.rounded_rectangle((0, 0, 511, 511), radius=int(8 * s), fill=rgb(AUGUR["sage"]))
    cream = rgb(AUGUR["cream"])
    g.polygon([(11 * s, 6 * s), (21 * s, 6 * s), (21 * s, 11 * s), (18 * s, 15 * s), (14 * s, 15 * s), (11 * s, 11 * s)], fill=cream)
    for x, y, w, h, a in ((7, 19, 18, 2.4, 255), (9, 23.2, 14, 2.4, 204), (11, 27.4, 10, 2, 153)):
        layer = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle((x * s, y * s, (x + w) * s, (y + h) * s), radius=int(h * s / 2), fill=cream + (a,))
        logo = Image.alpha_composite(logo, layer)
    logo.save(bdir / "logo.png")

    banner = Image.new("RGB", (1600, 400), rgb(AUGUR["cream"]))
    b = ImageDraw.Draw(banner)
    for x in range(0, 1600, 40):
        b.line([(x, 0), (x, 400)], fill=rgb(AUGUR["line"]))
    for y in range(0, 400, 40):
        b.line([(0, y), (1600, y)], fill=rgb(AUGUR["line"]))
    x = 1600
    for d in reversed(data["designs"][:3]):
        shot = out / "designs" / d["project"] / "card.jpg"
        if not shot.exists():
            continue
        with Image.open(shot) as im:
            im = im.convert("RGB")
            im.thumbnail((400, 300))
            x -= im.width + 24
            banner.paste(im, (x, 50))
            b.rectangle((x, 50, x + im.width - 1, 50 + im.height - 1), outline=rgb(AUGUR["line"]))
    b.rectangle((0, 392, 1600, 400), fill=rgb(AUGUR["sage"]))
    banner.save(bdir / "banner.png", optimize=True)


# ---------------------------------------------------------------- sections

def hero(data: dict) -> str:
    ds = data["designs"]
    pick = next((d for d in ds if d["project"] == data["cfg"].get("hero_model")), ds[0] if ds else None)
    cur = data["pricing"].get("currency", "USD")
    lo = min((d["estimate"]["print_price"] for d in ds), default=data["pricing"]["min_charge"])
    fee = design_fee(data["pricing"], "new")
    portal_btn = f'<a class="btn primary" href="{esc(data["portal"])}">Request a part <span class="arr">→</span></a>' if data["portal"] else ""
    visual = ""
    if pick:
        big = max(pick["parts"], key=lambda p: p["volume"]) if pick["parts"] else None
        visual = f"""<a class="plate" href="designs/{pick['project']}/index.html" aria-label="{esc(pick['title'])}">
<div class="grid-mark"></div><img src="designs/{pick['project']}/shot.jpg" alt="{esc(pick['title'])}, rendered from the print file" width="1200" height="900">
<div class="spec"><span class="tag">{esc(pick['title'])}</span>
<span style="display:flex;gap:8px;flex-wrap:wrap">{f'<span class="tag num">{dims(big["bbox"])} mm</span>' if big else ''}{'<span class="tag ok">Printed &amp; in use</span>' if pick['status'] == 'printed' else ''}</span></div></a>"""
    return f"""<section class="hero"><div class="wrap">
<div class="hero-copy">
<span class="eyebrow">Custom 3D printing · design included</span>
<h1>Parts made to fit <em>the thing you already have.</em></h1>
<p class="lede">Tell us what it has to hold, fix or fit. You get a 3D model you can turn in your browser, every measurement and a fixed price, and nothing is printed until you say so.</p>
<div class="actions">{portal_btn}<a class="btn" href="#work">See the work</a></div>
<div class="assure"><span>{ICONS['check']}Prints from <b class="num">&nbsp;{money(lo, cur, cents=False)}</b>, design <b class="num">&nbsp;{money(0, cur, cents=False)}–{money(fee, cur, cents=False)}</b></span><span>{ICONS['check']}Changes until it's right</span><span>{ICONS['check']}PLA, PETG, TPU, ASA</span></div>
</div>
{visual}
</div></section>"""


def proof(data: dict) -> str:
    ds = data["designs"]
    prints = [p for d in ds for p in d["prints"]]
    bed = PRINTER.get("bed") or (270, 270, 270)
    items = [(str(len(ds)), "designs in the portfolio"), (str(sum(len(d["parts"]) for d in ds)), "printable parts, each measured"),
             (str(sum(1 for p in prints if p.get("outcome") == "ok")), "prints reported working"),
             (f"{bed[0]:.0f}×{bed[1]:.0f}×{bed[2]:.0f}", "mm build volume, 4 colours")]
    return '<section class="proof"><div class="wrap">' + "".join(f"<div><b>{esc(v)}</b><span>{esc(k)}</span></div>" for v, k in items) + "</div></section>"


def how(data: dict) -> str:
    q = data["pricing"]["queue_days"]
    steps = [
        ("Describe it", "Say what it's for and how big the things around it are. A photo with a ruler in it helps more than anything."),
        ("Check the design", "You get a 3D model to turn and slice in your browser, a measurement sheet and a price."),
        ("Confirm or change", "Reply CONFIRM to go ahead, or say what to change. Revisions come back the same way."),
        ("Pick it up", f"It's printed, checked and handed over, usually {q}–{q + 3} days after you confirm."),
    ]
    items = "".join(f"<li><h3>{esc(t)}</h3><p>{esc(p)}</p></li>" for t, p in steps)
    return f"""<section class="band" id="how"><div class="wrap">
<div class="head"><span class="eyebrow">How it works</span><h2>From a measurement to a part in your hand.</h2>
<p>Every request is designed from scratch around your object, so the first thing you see is the design, not an invoice.</p></div>
<ol class="steps">{items}</ol>
</div></section>"""


def work(data: dict) -> str:
    cur = data["pricing"].get("currency", "USD")
    kinds = sorted({d["kind"] for d in data["designs"] if d["kind"]})
    cards = []
    for d in data["designs"]:
        ex = d["estimate"]
        img = (f'<img src="designs/{d["project"]}/card.jpg" alt="{esc(d["title"])}" loading="lazy" width="720" height="540">'
               if (OUT_CURRENT / "designs" / d["project"] / "card.jpg").exists() else "")
        cards.append(f"""<a class="card" href="designs/{d['project']}/index.html" data-kind="{esc(d['kind'])}">
<div class="img">{img}</div><div class="body"><span class="kind">{esc(d['kind'])}</span><h3>{esc(d['title'])}</h3>
<p>{esc(d['tagline'])}</p>
<div class="foot">{status_pill(d)}<span class="price">{money(ex['print_price'], cur)}</span></div></div></a>""")
    filters = ('<div class="filters" role="group" aria-label="Filter by kind"><button type="button" aria-pressed="true" data-kind="">All</button>'
               + "".join(f'<button type="button" aria-pressed="false" data-kind="{esc(k)}">{esc(k)}</button>' for k in kinds) + "</div>")
    script = """<script>
(function(){const g=document.getElementById('work-grid');const bs=document.querySelectorAll('.filters button');
bs.forEach(b=>b.addEventListener('click',()=>{bs.forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
g.querySelectorAll('.card').forEach(c=>{c.hidden=!!b.dataset.kind&&c.dataset.kind!==b.dataset.kind;});}));})();
</script>"""
    return f"""<section class="band well" id="work"><div class="wrap">
<div class="head"><span class="eyebrow">Selected work</span><h2>Designed here, printed here.</h2>
<p>Every piece below was modelled for a real object and checked for printability. The price is what one costs in PLA today, printed as designed. Want it sized to your own object instead? That is a {money(design_fee(data['pricing'], 'adapt'), cur, cents=False)} adjustment, not a new design.</p></div>
{filters}<div class="grid" id="work-grid">{''.join(cards)}</div>{script}
</div></section>"""


def quote_anatomy(data: dict) -> str:
    ds = data["designs"]
    d = next((x for x in ds if x["project"] == "esp32_devkit_case"), ds[0] if ds else None)
    if not d:
        return ""
    cur = data["pricing"].get("currency", "USD")
    e = estimate(d["report"], "PLA", 1, data["pricing"], design="new")     # the example is a request designed from scratch
    big = max(d["parts"], key=lambda p: p["volume"])
    wall = min((p["wall_min"] for p in d["parts"] if p["wall_min"] is not None), default=None)
    feats = [("cube", "A 3D model you can inspect", "Orbit it, cut through it and check every opening before anything is printed. It opens in any browser."),
             ("ruler", "Every measurement, written down", "Outer size, thinnest wall, hole sizes and each dimension that was assumed, so you can check it against the real thing."),
             ("tag", "A price in two lines, and a date", "The print price comes from the design itself: filament, printer time and handling. The design fee is flat and shown separately, with the ready date."),
             ("chat", "Changes until it's right", "Reply with what to change and a revised design comes back. Nothing is printed until you confirm.")]
    return f"""<section class="band"><div class="wrap quote-grid">
<div><div class="head"><span class="eyebrow">What every quote includes</span><h2>You see the part before you pay for it.</h2></div>
<div class="features">{''.join(f'<div class="feature"><span class="ico">{ICONS[i]}</span><div><h3>{esc(t)}</h3><p>{esc(p)}</p></div></div>' for i, t, p in feats)}</div></div>
<figure class="sheet" style="margin:0" aria-label="Example quote">
<div class="bar"><span>Quote <b>r1</b> · {esc(d['title'])}</span><span class="muted">Example</span></div>
<div class="pic"><img src="designs/{d['project']}/shot.jpg" alt="" loading="lazy"></div>
<dl class="rows">
<dt>Largest part</dt><dd>{dims(big['bbox'])} mm</dd>
<dt>Thinnest wall</dt><dd>{f"{wall:g} mm" if wall is not None else "—"}</dd>
<dt>Material</dt><dd>PLA · about {e['mass_g']:.0f} g</dd>
<dt>Print time</dt><dd>about {e['print_h']:.1f} h</dd>
<dt>Ready in</dt><dd>about {e['lead_days']} days</dd>
<dt>Print</dt><dd>{money(e['print_price'], cur)}</dd>
<dt>Design, from scratch</dt><dd>{money(e['design_fee'], cur)}</dd>
<dt class="total">Price</dt><dd class="total">{money(e['total'], cur)}</dd>
</dl>
<div class="reply">Reply <span class="kbd">CONFIRM</span> to print it, or say what to change.</div>
</figure>
</div></section>"""


MATERIALS = [
    ("PLA", AUGUR["sage"], "Stiff and crisp. The default for indoor parts, decor and enclosures.", "Softens above ~55 °C"),
    ("PETG", AUGUR["steel"], "Tougher, a little flexible, happy with warmth and water.", "Clips, brackets, kitchen"),
    ("TPU", AUGUR["gold"], "Rubbery and grippy: bumpers, feet, gaskets and sleeves.", "Shore 95A"),
    ("ASA", AUGUR["rust"], "Holds up to sun and heat for parts that live outside.", "UV-stable"),
]


def price_examples(data: dict) -> list[dict]:
    """Worked examples priced from real designs, so the numbers are the ones a quote would give:
    a catalogue piece as is, one adapted to the requester's object, one designed from scratch, and a batch."""
    ds, pr = data["designs"], data["pricing"]
    if not ds:
        return []
    by_price = sorted(ds, key=lambda d: d["estimate"]["print_price"])
    small, mid = by_price[0], by_price[len(by_price) // 2]
    multi = next((d for d in ds if len(d["parts"]) > 1 and d["status"] != "failed"), ds[0])
    big = next((d for d in reversed(by_price) if d is not small), by_price[-1])
    picks = [("As designed", small, 1, "none",
              f"One {small['title'].lower()} exactly as it appears above. It already exists, so there is no design fee."),
             ("Fitted to your object", mid, 1, "adapt",
              f"A {mid['title'].lower()} resized around your own board, object or gap. The proven parts stay; only the sizes change."),
             ("Designed from scratch", big, 1, "new",
              f"Something like the {big['title'].lower()}, drawn from your description and measurements. The fee covers every revision."),
             ("A batch", multi, 5, "adapt",
              f"Five of the {multi['title'].lower()}, fitted to your object. The design is paid once; the print price is per copy.")]
    out = []
    for label, d, qty, design, blurb in picks:
        e = estimate(d["report"], "PLA", qty, pr, design=design)
        out.append({"label": label, "design": d, "qty": qty, "kind": design, "blurb": blurb, "estimate": e})
    return out


def pricing(data: dict) -> str:
    pr, cur = data["pricing"], data["pricing"].get("currency", "USD")
    tiers = pr.get("design") or {}
    rows = "".join(f'<tr><td><a href="designs/{d["project"]}/index.html">{esc(d["title"])}</a><br><span class="muted">{len(d["parts"])} part{"s" if len(d["parts"]) != 1 else ""}</span></td>'
                   f'<td class="r num">{d["estimate"]["mass_g"]:.0f} g</td><td class="r num">{d["estimate"]["print_h"]:.1f} h</td>'
                   f'<td class="r num"><b>{money(d["estimate"]["print_price"], cur)}</b></td></tr>'
                   for d in sorted(data["designs"], key=lambda d: d["estimate"]["print_price"]))
    tier_copy = {"none": ("Existing design, or your own file",
                          "A piece from this page printed as it is, a reprint, or an STL you already have. You pay the print price only."),
                 "adapt": ("Fitted to your object",
                           "An existing design or the proven library parts, resized and rearranged around your measurements. Most requests land here."),
                 "new": ("Designed from scratch",
                         "Nothing on file fits, so it is drawn from your description. One flat fee, however many revisions it takes.")}
    tier_cards = "".join(f"""<div class="tier{' hi' if k == 'adapt' else ''}"><span class="fee">{money(t['fee'], cur, cents=False)}<small>{'no design fee' if not t['fee'] else 'flat'}</small></span>
<b>{esc(tier_copy.get(k, (t.get('label', k), ''))[0])}</b><p>{esc(tier_copy.get(k, ('', t.get('label', '')))[1])}</p></div>""" for k, t in tiers.items())
    ex_cards = []
    for x in price_examples(data):
        e, d = x["estimate"], x["design"]
        per = f'<span class="muted">of which each</span><span class="muted">{money(e["per_unit"], cur)}</span>' if x["qty"] > 1 else ""
        ex_cards.append(f"""<div class="ex"><span class="eyebrow">{esc(x['label'])}</span><h3><a href="designs/{d['project']}/index.html" style="color:inherit;text-decoration:none">{esc(d['title'])}</a>{f" × {x['qty']}" if x['qty'] > 1 else ""}</h3>
<p>{esc(x['blurb'])}</p>
<div class="sum"><span>Print<br><span class="muted">{e['mass_g']:.0f} g PLA · about {e['print_h']:.0f} h</span></span><span>{money(e['print_price'], cur)}</span>{per}
<span>Design</span><span>{money(e['design_fee'], cur)}</span>
<span class="t">Price</span><span class="t">{money(e['total'], cur)}</span>
<span class="muted">Ready in</span><span class="muted">about {e['lead_days']} days</span></div></div>""")
    mats = pr.get("materials", {})
    mat_cards = "".join(f"""<div class="mat"><div class="sw" style="background:{c}"></div><b>{m}</b><p>{esc(t)}</p>
<span class="num">{esc(note)} · {money(mats[m]['cost_per_kg'], cur, cents=False)}/kg</span></div>""" for m, c, t, note in MATERIALS if m in mats)
    return f"""<section class="band well" id="pricing"><div class="wrap">
<div class="head"><span class="eyebrow">Pricing</span><h2>Two numbers: the print, and the design.</h2>
<p>The print price is worked out from the part itself, so a small bracket costs a few dollars and a big rack costs what its filament and hours cost. The design fee is flat and depends on how much is new.</p></div>
<div class="price-grid">
<dl class="formula">
<div><dt>Filament</dt><dd>The part's volume printed with {pr['shell_mm']:g} mm walls and {pr['infill'] * 100:g}% infill, at the material's price.</dd></div>
<div><dt>Printer time</dt><dd>{money(pr['machine_per_h'], cur)} an hour on the printer, from setup to the last layer.</dd></div>
<div><dt>Handling</dt><dd>Setup, cleanup and checking against the measurements at {money(pr['labor_per_h'], cur, cents=False)} an hour: {pr['setup_min']} minutes a job plus about {pr['post_min_per_part']} minutes a part.</dd></div>
<div><dt>Print price</dt><dd>Those three plus a {pr['margin'] * 100:g}% margin, rounded up to {money(pr.get('round_to', 0.5), cur)}, never less than {money(pr['min_charge'], cur, cents=False)}. Quantity multiplies this line only.</dd></div>
<div><dt>Design fee</dt><dd>Added once per request, whatever the quantity. Zero for an existing design; see the three cases below.</dd></div>
</dl>
<div class="ledger tablewrap"><table><thead><tr><th>Print price, one in PLA</th><th class="r">Filament</th><th class="r">Print</th><th class="r">Price</th></tr></thead>
<tbody>{rows}</tbody></table></div>
</div>
<div class="head" style="margin-top:64px"><span class="eyebrow">The design fee</span><h3 style="font-size:28px">Pay for new design work, not for design that already exists.</h3>
<p>Every design is built from a library of proven parts, so most requests are a matter of fitting, not inventing.</p></div>
<div class="tiers">{tier_cards}</div>
<div class="head" style="margin-top:64px"><span class="eyebrow">Worked examples</span><h3 style="font-size:28px">What a quote looks like, on real designs.</h3>
<p>Each one is priced exactly as a request would be today.</p></div>
<div class="examples">{''.join(ex_cards)}</div>
<div class="head" style="margin-top:72px"><span class="eyebrow">Materials</span><h3 style="font-size:28px">Four materials, loaded side by side.</h3>
<p>The printer runs up to four filaments in one job, so a part can mix colours or put a rubbery TPU foot on a rigid body.</p></div>
<div class="mats">{mat_cards}</div>
</div></section>"""


def library_section(data: dict) -> str:
    lib = data["library"]
    if not lib["count"]:
        return ""
    titles = {d["project"]: d["title"] for d in data["designs"]}
    cats = "".join(f'<div class="cat"><b>{c["count"]}</b><h3>{esc(c["name"])}</h3><p>{esc(c["blurb"])}</p></div>' for c in lib["categories"])
    top = sorted((c for c in lib["components"] if c["used_in"]), key=lambda c: (-len(c["used_in"]), -len(c["printed_in"]), c["name"]))[:8]
    rows = []
    for c in top:
        where = ", ".join(titles.get(p, title_of(p)) for p in c["used_in"])
        proven = ", ".join(c["printed_in"]) if c["printed_in"] else "not yet"
        rows.append(f'<tr><td><b>{esc(c["name"])}</b><br><span class="muted">{esc(c["summary"].split(";")[0].split(" — ")[0])}</span></td>'
                    f'<td>{esc(where)}</td><td class="num">{esc(proven)}</td></tr>')
    return f"""<section class="band" id="library"><div class="wrap">
<div class="head"><span class="eyebrow">The parts library</span><h2>Every design starts from parts that have already printed.</h2>
<p>A case is not drawn from a blank screen. The insert pockets, the board's hole pattern, the vents, the lid and the snap fit are all parametric components that have been printed and measured before. Only the shape around your object is new.</p></div>
<div class="cats">{cats}</div>
<div class="lib-grid">
<div class="prose">
<h3>What it means for you</h3>
<p><b>Fewer surprises.</b> A component that has held a heat-set insert or snapped shut in a finished part does it the same way in yours. When a print report says a part failed, the component it used is marked, and the next design avoids the same mistake.</p>
<p><b>Faster, cheaper design.</b> Fitting proven parts around your measurements takes a fraction of the time of drawing them, which is why most requests carry the small design fee rather than the full one, and why a revision usually comes back within a day.</p>
<p><b>Written down.</b> Every design page above lists the components it used and the materials they have been printed in. The library itself is open: <a href="{REPO_URL}/blob/main/PARTS.md">{lib['count']} components on GitHub</a>, with every parameter documented.</p>
</div>
<div class="ledger tablewrap"><table><thead><tr><th>Most used</th><th>In</th><th>Printed in</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
</div>
</div></section>"""


def faq(data: dict) -> str:
    items = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in data["cfg"].get("faq") or [])
    return f"""<section class="band" id="faq"><div class="wrap">
<div class="head"><span class="eyebrow">Questions</span><h2>Before you ask.</h2></div>
<div class="faq">{items}</div>
</div></section>""" if items else ""


def cta(data: dict) -> str:
    btn = f'<a class="btn primary" href="{esc(data["portal"])}">Start a request <span class="arr">→</span></a>' if data["portal"] else ""
    return f"""<section class="band ink cta"><div class="wrap">
<div style="display:grid;gap:14px"><span class="eyebrow">Have something in mind?</span><h2>Measure it, describe it, and we'll draw it.</h2>
<p class="muted">Requests take a few minutes. You'll get the design and a price back before anything is printed.</p></div>
<div class="actions">{btn}<a class="btn" href="request.html">How ordering works</a></div>
</div></section>"""


# ---------------------------------------------------------------- pages

OUT_CURRENT = OUT   # the output directory of the build in progress (work() checks for the card images)


def index_page(data: dict) -> str:
    body = hero(data) + proof(data) + how(data) + work(data) + quote_anatomy(data) + pricing(data) + library_section(data) + faq(data) + cta(data)
    return page(f"{data['brand']} · Custom 3D-printed parts", body, data, depth=0, current="",
                description=data["cfg"].get("tagline", ""))


def design_page(d: dict, data: dict, out: Path) -> str:
    ddir = out / "designs" / d["project"]
    cur = data["pricing"].get("currency", "USD")
    e = d["estimate"]
    has_viewer = d["viewer"].exists()
    if has_viewer:
        (ddir / "viewer.html").write_text(VIEWER_HEAD + d["viewer"].read_text(encoding="utf-8"), encoding="utf-8")
    big = max(d["parts"], key=lambda p: p["volume"]) if d["parts"] else None
    plate = d["plate"]

    figs = []
    if (ddir / "shot.jpg").exists():
        figs.append(f'<figure><img src="shot.jpg" alt="{esc(d["title"])}, all parts" width="1200" height="900">'
                    f'<figcaption><span>All parts, as they come off the printer</span><span class="num">{len(d["parts"])} part{"s" if len(d["parts"]) != 1 else ""}</span></figcaption></figure>')

    facts = [("Size", f'<span class="num">{dims(big["bbox"])} mm</span>' if big else "—"),
             ("Parts", f'<span class="num">{len(d["parts"])}</span>'),
             ("Filament (PLA)", f'<span class="num">about {e["mass_g"]:.0f} g</span>'),
             ("Print time", f'<span class="num">about {e["print_h"]:.1f} h</span>'),
             ("Status", status_pill(d))]
    if plate.get("extent"):
        facts.insert(1, ("Print plate", f'<span class="num">{dims(plate["extent"])} mm</span>'))
    portal_btn = f'<a class="btn primary" href="{esc(data["portal"])}">Request one like this <span class="arr">→</span></a>' if data["portal"] else ""
    viewer_btn = '<a class="btn" href="viewer.html">Open in 3D</a>' if has_viewer else ""

    # technical details
    rows = []
    for p in d["parts"]:
        chk = ('<span class="pill bad">needs work</span>' if p["problems"] else
               '<span class="pill ok">passes</span>' if p["ok"] else '<span class="pill">unchecked</span>')
        mode = " · spiral vase" if p["mode"] == "vase" else ""
        wall = f"{p['wall_min']:g} mm" if p["wall_min"] is not None else "—"
        rows.append(f'<tr><td><b>{esc(p["name"])}</b>{mode}</td><td class="num">{" × ".join(f"{x:g}" for x in p["bbox"])}</td>'
                    f'<td class="num">{p["volume"] / 1000:.1f} cm³</td><td class="num">{wall}</td><td>{chk}</td></tr>')
    (ddir / "renders").mkdir(exist_ok=True)
    views = []
    for p in d["parts"]:
        if p["render"].exists():
            shutil.copyfile(p["render"], ddir / "renders" / f"{p['name']}.png")
            views.append(f'<figure style="margin:0;border:1px solid var(--line);border-radius:8px;overflow:hidden"><img src="renders/{esc(p["name"])}.png" alt="{esc(p["name"])}: isometric, top and front views" loading="lazy">'
                         f'<figcaption style="padding:6px 12px;font-size:13px;color:var(--ink-2)">{esc(p["name"])}</figcaption></figure>')
    files = []
    if d["files"]:
        (ddir / "files").mkdir(exist_ok=True)
        for f in d["files"]:
            size = f.stat().st_size
            if size > MAX_FILE_MB * 1e6:
                files.append(f'<li><span>{esc(f.name)}</span><span class="muted">{fmt_size(size)}, too large to host</span></li>')
                continue
            shutil.copyfile(f, ddir / "files" / f.name)
            label = "whole plate" if f.suffix == ".3mf" else f.suffix[1:].upper()
            files.append(f'<li><a href="files/{esc(f.name)}" download>{esc(f.name)}</a><span class="muted num">{label} · {fmt_size(size)}</span></li>')
    comps = "".join(f'<tr><td><b>{esc(lib_name(c["id"]))}</b><br><code>{esc(c["id"])}</code></td><td>{esc(c.get("summary", ""))}</td>'
                    f'<td class="num">{esc(", ".join(sorted(set(c.get("validated") or []) | set(c.get("field_validated") or []))) or "not yet")}</td></tr>' for c in d["components"])
    tech = f"""<details class="tech"><summary>Technical details</summary><div>
{f'<div class="prose">{paragraphs(d["details"])}</div>' if d["details"].strip() else ''}
<div><h3>Parts</h3><div class="tablewrap"><table><thead><tr><th>Part</th><th>Size (mm)</th><th>Volume</th><th>Thinnest wall</th><th>Printability</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></div>
{f'<div><h3>Engineering views</h3><div class="gallery">{"".join(views)}</div></div>' if views else ''}
{f'<div><h3>Downloads</h3><ul class="files">{"".join(files)}</ul></div>' if files else ''}
{f'<div><h3>Library parts used</h3><p class="muted" style="font-size:14px;margin-bottom:10px">Parametric components shared with the other designs; see <a href="../../index.html#library">the parts library</a>.</p><div class="tablewrap"><table><thead><tr><th>Component</th><th>What it does</th><th>Printed in</th></tr></thead><tbody>{comps}</tbody></table></div></div>' if comps else ''}
<p class="muted" style="font-size:14px">Source: <a href="{REPO_URL}/tree/main/models/{d['project']}">models/{d['project']}</a> · built <span class="num">{esc(d['built_at'])}</span></p>
</div></details>"""

    log = ""
    if d["prints"]:
        log = '<div style="display:grid;gap:14px"><h2 style="font-size:28px">Print reports</h2>' + timeline(
            [dict(p, _project=d["project"]) for p in d["prints"]], data, link=False) + "</div>"

    body = f"""<div class="wrap"><p class="crumbs"><a href="../../index.html#work">Work</a> / {esc(d['kind'] or 'Design')}</p>
<div class="detail">
<div style="display:grid;gap:28px"><div class="gallery">{''.join(figs)}</div>{log}{tech}</div>
<div class="copy">
<span class="eyebrow">{esc(d['kind'])}</span>
<h1 style="font-size:clamp(34px,4vw,48px)">{esc(d['title'])}</h1>
<p class="lede">{esc(d['tagline'])}</p>
{f'<p class="muted">{esc(d["story"])}</p>' if d['story'] else ''}
<div class="bigprice"><b>{money(e['print_price'], cur)}</b><span class="muted">for one in PLA, printed as designed</span></div>
<dl class="facts">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts)}</dl>
<div class="actions">{portal_btn}{viewer_btn}</div>
<p class="muted" style="font-size:14px">Want it in another size, colour or material? Say so in the request: fitting it to your object is a {money(design_fee(data['pricing'], 'adapt'), cur, cents=False)} adjustment, and you see the revised design before it's printed.</p>
</div>
</div></div>
{cta(data).replace('href="request.html"', 'href="../../request.html"')}"""
    return page(f"{d['title']} · {data['brand']}", body, data, depth=2, current="work", description=d["tagline"])


def outcome_pill(o: str) -> str:
    return ('<span class="pill ok">Worked</span>' if o == "ok" else
            '<span class="pill bad">Failed</span>' if o == "fail" else f'<span class="pill">{esc(o or "reported")}</span>')


def timeline(prints: list[dict], data: dict, link: bool) -> str:
    titles = {d["project"]: d["title"] for d in data["designs"]}
    items = []
    for p in sorted(prints, key=lambda x: x.get("date", ""), reverse=True):
        where = f'<a href="designs/{p["_project"]}/index.html"><b>{esc(titles.get(p["_project"], title_of(p["_project"])))}</b></a>' if link else ""
        mat = f'<span class="pill">{esc(p["material"])}</span>' if p.get("material") else ""
        items.append(f'<li><div class="top-line">{where}{outcome_pill(p.get("outcome", ""))}{mat}'
                     f'<span class="num muted">{esc(p.get("date", ""))}</span></div><p>{esc(report_text(p.get("text", "")))}</p></li>')
    return f'<ul class="log">{"".join(items)}</ul>'


def prints_page(data: dict) -> str:
    allp = [dict(p, _project=d["project"]) for d in data["designs"] for p in d["prints"]]
    ok = sum(1 for p in allp if p.get("outcome") == "ok")
    body = f"""<section class="band" style="padding-bottom:40px"><div class="wrap">
<div class="head"><span class="eyebrow">Track record</span><h1 style="font-size:clamp(34px,4.4vw,52px)">Every print, including the ones that failed.</h1>
<p>A failed print sends the design back to the drawing board; a good one marks the parts of the design it used as proven in that material. Both are written down here.</p></div>
</div></section>
<section class="proof"><div class="wrap"><div><b>{len(allp)}</b><span>print reports</span></div><div><b>{ok}</b><span>worked first time or after a fix</span></div>
<div><b>{len(allp) - ok}</b><span>failed and redesigned</span></div><div><b>{len({p['_project'] for p in allp})}</b><span>designs printed</span></div></div></section>
<section class="band"><div class="wrap" style="max-width:900px">
{timeline(allp, data, link=True) if allp else '<p class="muted">Nothing printed yet.</p>'}
</div></section>
{cta(data)}"""
    return page(f"Track record · {data['brand']}", body, data, depth=0, current="prints")


REQUEST_TYPES = {
    "3D print request": ("Describe a part you need and it's designed with you.",
                         "Something that doesn't exist yet: a case for a board, a bracket, a holder, a replacement part."),
    "Print my file": ("You already have an STL, 3MF or STEP file.",
                      "Attach the file under Photos. You still get the measurements and a price before it's printed."),
    "Reprint or fix an earlier part": ("A part printed here broke, didn't fit, or needs a change.",
                                       "Say what went wrong and give the earlier request's key (for example PRINT-12) if you have it."),
}

FORM_FIELDS = [
    ("What do you need?", "A short name for the part, like “wall mount for my router”.", True),
    ("What is it for?", "What it holds, attaches to or protects, and where it lives (indoors, outdoors, near heat).", False),
    ("Sizes it must fit", "The measurements that matter, in millimetres: the object it holds, hole spacing, the gap it fits into.", False),
    ("How many", "How many copies.", True),
    ("Material", "PLA, PETG, TPU or ASA, or “Not sure” and one will be recommended.", True),
    ("Color", "Any, or a preference. Multi-colour prints can use up to four colours.", False),
    ("When do you need it?", "A date, if there is one.", False),
    ("Photos", "Photos of the object with a ruler in shot. For “Print my file”, the model file goes here.", False),
    ("Additional information", "Anything else: how strong it must be, what it must not cover, a link to something similar.", False),
]


def request_page(data: dict) -> str:
    j, portal = data["jira"], data["portal"]
    types = [t for t in (j.get("request_type") or []) if t in REQUEST_TYPES] or list(REQUEST_TYPES)
    type_cards = "".join(f'<div class="mat"><b style="font-size:21px">{esc(t)}</b><p style="color:var(--ink)">{esc(REQUEST_TYPES[t][0])}</p><p>{esc(REQUEST_TYPES[t][1])}</p></div>' for t in types)
    fields = "".join(f'<div><b>{esc(n)}{" <span class=\"pill\" style=\"margin-left:6px\">required</span>" if req else ""}</b><p>{esc(h)}</p></div>'
                     for n, h, req in FORM_FIELDS)
    portal_btn = f'<a class="btn primary" href="{esc(portal)}">Open the request portal <span class="arr">→</span></a>' if portal else ""
    help_btn = f'<a class="btn" href="{esc(data["help"])}">Help articles</a>' if data["help"] else ""
    steps = [
        ("Raise a request", "Open the portal, sign in with your e-mail and pick a request type. No Jira licence is needed. Your request gets a key like <b class=num>PRINT-12</b>."),
        ("It's designed", "The request moves to <b>In Progress</b>. If a measurement is missing you get a question first."),
        ("You get a quote", "A comment arrives on the request and by e-mail with a 3D viewer file, renders, a measurement sheet and the price. The request is now <b>Pending</b>, waiting for you."),
        ("Confirm or change", "Reply <span class=kbd>CONFIRM</span> to go ahead. Anything else is read as a change: say what should be different and a revised quote comes back."),
        ("It's printed", "The request goes back to <b>In Progress</b> while it's printed and checked, then to <b>Done</b>. Pick-up or delivery is arranged on the request."),
    ]
    step_items = "".join(f"<li><h3>{t}</h3><p>{p}</p></li>" for t, p in steps)
    body = f"""<section class="band" style="padding-bottom:48px"><div class="wrap">
<div class="head"><span class="eyebrow">How to order</span><h1 style="font-size:clamp(34px,4.4vw,52px)">Ordering takes a few minutes. The design takes care of itself.</h1>
<p>Requests go through a service portal. You describe what you need; you get a design, the measurements and a price back, and nothing is printed until you confirm.</p>
<div class="actions">{portal_btn}{help_btn}</div>
{f'<p class="muted" style="font-size:14px">The portal lives at <span class="num">{esc(portal.removeprefix("https://"))}</span>.</p>' if portal else ''}</div>
<ol class="steps five">{step_items}</ol>
</div></section>
<section class="band well"><div class="wrap">
<div class="head"><span class="eyebrow">Your reply</span><h2>Replies are read by a person.</h2>
<p>“Looks good, but…” counts as a change, not a confirmation, and a CONFIRM that also asks a question gets an answer before anything is printed.</p></div>
<div class="status-flow"><span class="pill">To Do</span><span class="arrow">→</span><span class="pill gold">In Progress</span><span class="arrow">→</span><span class="pill gold">Pending</span><span class="arrow">→</span><span class="pill gold">In Progress</span><span class="arrow">→</span><span class="pill ok">Done</span></div>
<p class="muted" style="margin-top:14px;max-width:70ch"><b>To Do</b>: received. <b>In Progress</b>: being designed, or printed once you've confirmed. <b>Pending</b>: a quote is waiting for your reply. A cancelled request is closed as <b>Done</b>.</p>
</div></section>
<section class="band"><div class="wrap">
<div class="head"><span class="eyebrow">Request types</span><h2>Pick the one that fits.</h2></div>
<div class="mats" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">{type_cards}</div>
<div class="head" style="margin-top:72px"><span class="eyebrow">The form</span><h2>What to put where.</h2>
<p>The more of this you give, the fewer questions come back. Measure with calipers if you have them, and say which sizes are exact and which are rough.</p></div>
<div class="fields">{fields}</div>
</div></section>
{cta(data)}"""
    return page(f"How to order · {data['brand']}", body, data, depth=0, current="order")


# ---------------------------------------------------------------- build / deploy

def build(out: Path = OUT) -> Path:
    global OUT_CURRENT
    OUT_CURRENT = out
    data = collect()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / ".nojekyll").write_text("")
    (out / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    for d in data["designs"]:
        (out / "designs" / d["project"]).mkdir(parents=True)
        place_images(d, out)
    brand_assets(data, out)
    (out / "index.html").write_text(index_page(data), encoding="utf-8")
    for d in data["designs"]:
        (out / "designs" / d["project"] / "index.html").write_text(design_page(d, data, out), encoding="utf-8")
    (out / "prints.html").write_text(prints_page(data), encoding="utf-8")
    (out / "request.html").write_text(request_page(data), encoding="utf-8")
    return out


def deploy(out: Path, branch: str = "gh-pages") -> None:
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        git = ["git", f"--git-dir={tmp}/.git", f"--work-tree={out}"]
        subprocess.run(["git", "init", "-q", "-b", branch, tmp], check=True)
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", f"site: build from {head}"], check=True)
        subprocess.run(git + ["push", "-f", remote, f"{branch}:{branch}"], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--serve", action="store_true", help="serve the built site on http://localhost:8000")
    ap.add_argument("--deploy", action="store_true", help="force-push the built site to the gh-pages branch")
    args = ap.parse_args()
    out = build(args.out)
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"built {out} ({fmt_size(total)})")
    if args.deploy:
        deploy(out)
        print("pushed to gh-pages")
    if args.serve:
        subprocess.run([sys.executable, "-m", "http.server", "8000", "-d", str(out)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
