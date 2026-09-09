#!/usr/bin/env python
"""The design brief: a standard form for handing a part idea to Claude, and its page.

    uv run python scripts/brief.py            # the form spec + published-page status, as text
    uv run python scripts/brief.py --html     # write exports/brief.html (the Briefs page)
    uv run python scripts/brief.py --json     # the page data as JSON

A brief is one of two framings:

  problem     a part that solves something (what goes wrong today, what it touches, it works if...)
  aesthetic   a part that has to look like something (the feeling, the form language, it's right if...)

FIELDS below is the single definition of both forms.  The page renders it (each field's ``section``
decides where its answer lands in the write-up), and ``idea_text_from_brief`` turns a submitted
brief into ``ideas/<slug>/IDEA.md`` in exactly the format ``ideas/README.md`` documents, so a brief
written in the browser arrives in the repo as a normal idea.  ``scripts/sync_notes.py`` calls it.

The page keeps three collections in its artifact database (URL recorded in brief.json):

  briefs        one document per brief: title, framing, kind, target, tags, fields{}, status
  brief_notes   the thread: {brief, author "me"|"claude", text, status "open"|"resolved"}
  brief_chat    one document per brief: {turns: [{role, content}]} from the page's Claude helper
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import ROOT, list_projects  # noqa: E402
from scripts.ideas import list_ideas, slugify  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent / "brief_template.html"
BRIEF_JSON = ROOT / "brief.json"
OUT_HTML = ROOT / "exports" / "brief.html"

FRAMINGS = ("problem", "aesthetic")
KINDS = ("part", "library", "modification")

# The printer everything here is designed for; quoted to the page and to the page's Claude helper.
PRINTER = {"machine": "Snapmaker U1", "bed": "270 mm cube", "nozzle": "0.4 mm", "layer": "0.2 mm",
           "toolheads": 4, "materials": ["PLA", "PETG", "TPU", "ASA"]}

# key, label, hint, placeholder, section (where the answer lands in IDEA.md), weight (completeness)
FIELDS: dict[str, list[dict]] = {
    "problem": [
        {"key": "problem", "label": "What goes wrong today", "weight": 3, "section": "Problem", "rows": 4,
         "hint": "The failure, not the fix. What you do instead now and where it lets you down.",
         "placeholder": "Water runs off the drying rack and sits on the counter; with an undermount sink there is no rim to hang anything from."},
        {"key": "job", "label": "What the part has to do", "weight": 3, "section": "Concept", "rows": 2,
         "hint": "One sentence, no shape yet: it holds / spaces / mounts / guards X so that Y.",
         "placeholder": "Catch the runoff between the rack and the basin and send it into the sink."},
        {"key": "interfaces", "label": "What it touches", "weight": 2, "section": "Constraints", "rows": 3,
         "hint": "Every object it meets, with measured mm. Mark a number you guessed with ~ so Claude knows to ask.",
         "placeholder": "Countertop at the cutout, ~30 mm stone. Sink flange underneath. Rack foot 12 mm tall."},
        {"key": "envelope", "label": "Space it lives in (mm)", "weight": 2, "section": "Constraints", "rows": 2,
         "hint": "Room it may occupy and what it must not foul. The bed is a 270 mm cube.",
         "placeholder": "180 long along the edge, 60 onto the counter, nothing below 40 mm under the counter."},
        {"key": "constraints", "label": "Must / must not", "weight": 1, "section": "Constraints", "rows": 3,
         "hint": "Load, clearance, removal, orientation, no adhesive, no drilling, has to be washable.",
         "placeholder": "No adhesive, no drilling. Comes off to wash. Nothing enclosed that can hold water."},
        {"key": "material", "label": "Material and environment", "weight": 1, "section": "Constraints", "rows": 2,
         "hint": "PLA / PETG / TPU / ASA, and what it is up against: heat, water, UV, food, springiness, load.",
         "placeholder": "PETG — splash zone, and PLA creeps when a hot pan drains into it."},
        {"key": "success", "label": "It works if...", "weight": 2, "section": "Concept", "rows": 2,
         "hint": "The test you will actually run on the print. Something that can fail.",
         "placeholder": "A cup of water poured on the rack ends in the basin and the counter stays dry."},
        {"key": "unknowns", "label": "What you are not sure about", "weight": 1, "section": "Open questions", "rows": 3,
         "hint": "Numbers you have not measured, choices you want pushed back on. One per line.",
         "placeholder": "Real counter thickness at the cutout\nHow much underside is exposed before the sink flange"},
    ],
    "aesthetic": [
        {"key": "object", "label": "What it is, and what goes in or on it", "weight": 3, "section": "Problem", "rows": 3,
         "hint": "The object and its job, however slight: a vase for dried stems, a stand that holds 350 g of headphones.",
         "placeholder": "A desk vase for dried stems, 200 mm tall, nothing wet in it."},
        {"key": "feeling", "label": "The feeling, in one line", "weight": 3, "section": "Concept", "rows": 2,
         "hint": "Ominous, ceremonial, cheap-and-cheerful, quiet, geological. One honest word beats a paragraph.",
         "placeholder": "Quiet and geological — something that looks eroded rather than designed."},
        {"key": "form", "label": "Form language", "weight": 2, "section": "Concept", "rows": 3,
         "hint": "Silhouette, surface, rhythm: what the eye follows, what repeats, where it is heavy and where it is thin.",
         "placeholder": "Narrow foot swelling to a wide shoulder, then a short straight neck. Vertical ribs, dense at the foot, opening out at the shoulder."},
        {"key": "refs", "label": "References", "weight": 2, "section": "Concept", "rows": 2,
         "hint": "Photos belong on the Inspiration page (they get read into a brief there); name them here, plus anything else it should recall.",
         "placeholder": "The two basalt column photos on the Inspiration page; ribbed_desk_vase but taller and less regular."},
        {"key": "avoid", "label": "What it must not look like", "weight": 1, "section": "Constraints", "rows": 2,
         "hint": "The near miss you would hate. This does more work than any other line here.",
         "placeholder": "Not a spiral twist. Nothing that reads as a CAD revolve with a fillet on it."},
        {"key": "setting", "label": "Where it lives, seen from how far, how big (mm)", "weight": 2, "section": "Constraints", "rows": 2,
         "hint": "Viewing distance decides how fine the surface can be. The bed is a 270 mm cube.",
         "placeholder": "Desk, seen from 600 mm and from above. About 200 tall, 90 across."},
        {"key": "palette", "label": "Colour, material, finish", "weight": 1, "section": "Constraints", "rows": 2,
         "hint": "Filaments you own, how many toolheads it may use, vase mode, texture, post-processing.",
         "placeholder": "Matte grey PLA, single colour. Vase mode if the walls allow it."},
        {"key": "success", "label": "It's right if...", "weight": 2, "section": "Concept", "rows": 2,
         "hint": "How you will judge the render before it is ever printed.",
         "placeholder": "From across the room it reads as one eroded mass, not as a stack of rings."},
        {"key": "unknowns", "label": "Open questions", "weight": 1, "section": "Open questions", "rows": 3,
         "hint": "What you want Claude to decide, and what you want to be asked about first. One per line.",
         "placeholder": "Whether the ribs should die out at the neck or run over the lip"},
    ],
}

SECTION_ORDER = ("Problem", "Concept", "Constraints", "Open questions")


def field_specs(framing: str) -> list[dict]:
    return FIELDS.get(framing, FIELDS["problem"])


def completeness(doc: dict) -> tuple[int, int, list[str]]:
    """(filled weight, total weight, labels of the empty fields) for one brief document."""
    fields = doc.get("fields") or {}
    have = total = 0
    missing = []
    for f in field_specs(str(doc.get("framing") or "problem")):
        total += f["weight"]
        if str(fields.get(f["key"]) or "").strip():
            have += f["weight"]
        else:
            missing.append(f["label"])
    return have, total, missing


def brief_markdown(doc: dict) -> str:
    """The brief as the markdown the page stores in `text` and the chat helper reads."""
    fields = doc.get("fields") or {}
    out = [f"# {doc.get('title') or 'untitled'}",
           f"_{doc.get('framing') or 'problem'} brief · kind {doc.get('kind') or 'part'}"
           + (f" · relates to {doc['target']}" if doc.get("target") else "") + "_"]
    for f in field_specs(str(doc.get("framing") or "problem")):
        v = str(fields.get(f["key"]) or "").strip()
        out.append(f"**{f['label']}**\n{v if v else '_(blank)_'}")
    if doc.get("tags"):
        out.append("**Tags** " + ", ".join(doc["tags"]))
    if doc.get("hardware"):
        out.append("**Hardware** " + ", ".join(doc["hardware"]))
    return "\n\n".join(out)


def idea_text_from_brief(doc: dict, notes: list[dict] | None = None, today: str | None = None) -> str:
    """One submitted brief as an ideas/<slug>/IDEA.md file, in the format ideas/README.md documents."""
    today = today or time.strftime("%Y-%m-%d")
    fields = doc.get("fields") or {}
    framing = str(doc.get("framing") or "problem")
    tags = [str(t) for t in (doc.get("tags") or [])]
    if framing == "aesthetic" and "form" not in tags:
        tags = tags + ["form"]
    hardware = [str(h) for h in (doc.get("hardware") or [])]

    sections: dict[str, list[str]] = {s: [] for s in SECTION_ORDER}
    for f in field_specs(framing):
        v = str(fields.get(f["key"]) or "").strip()
        if not v:
            continue
        if f["section"] == "Open questions":
            sections["Open questions"] += [f"- {ln.strip()}" for ln in v.splitlines() if ln.strip()]
        else:
            sections[f["section"]].append(f"**{f['label']}**  \n{v}")
    for n in notes or []:
        t = str(n.get("text") or "").strip()
        if t and str(n.get("status")) != "resolved":
            who = "you" if str(n.get("author")) != "claude" else "Claude"
            sections["Open questions"].append(f"- ({who}, thread) {t.splitlines()[0][:200]}")

    body = []
    for s in SECTION_ORDER:
        joiner = "\n" if s == "Open questions" else "\n\n"
        body.append(f"## {s}\n" + (joiner.join(sections[s]) if sections[s] else "_(not written yet)_"))
        if s == "Constraints":
            body.append("## Reuse map\n| need | component | notes |\n|---|---|---|\n|  |  |  |")
            body.append("## Gaps\n_(not written yet)_")
    article = "an" if framing[0] in "aeiou" else "a"
    log = [f"- {today} captured from the Briefs page as {article} {framing} brief"]
    if doc.get("id"):
        log.append(f"  (brief `{doc['id']}`; the thread and the page chat stay on the page)")
    body.append("## Log\n" + "\n".join(log))

    fmt = lambda xs: "[" + ", ".join(xs) + "]"  # noqa: E731
    return (
        "---\n"
        f"title: {doc.get('title') or 'untitled'}\n"
        "status: inbox\n"
        f"kind: {doc.get('kind') or 'part'}\n"
        f"created: {today}\n"
        f"updated: {today}\n"
        f"tags: {fmt(tags)}\n"
        f"hardware: {fmt(hardware)}\n"
        "reuse: []\n"
        "gaps: []\n"
        + (f"model: {doc['target']}\n" if str(doc.get("target") or "").strip() and doc.get("target") in set(list_projects()) else "model:\n")
        + "---\n\n" + "\n\n".join(body) + "\n"
    )


# ---------------------------------------------------------------- page

def page_data() -> dict:
    from scripts.studio import git_head, model_docstring

    idx = json.loads((ROOT / "parts.json").read_text(encoding="utf-8")) if (ROOT / "parts.json").exists() else {"components": {}}
    comps = []
    for cid, c in sorted(idx.get("components", {}).items()):
        mn = c.get("material_notes") or {}
        comps.append({"id": cid, "category": cid.split(".", 1)[0], "version": c.get("version", ""),
                      "summary": (c.get("summary") or "").strip(),
                      "unvalidated": not (mn.get("validated") or mn.get("field_validated"))})
    models = [{"project": p, "summary": (model_docstring(p).strip().split("\n\n")[0].replace("\n", " ") or "")[:150]}
              for p in list_projects()]
    ideas = [{"slug": i.slug, "title": i.title, "status": i.status, "kind": i.kind,
              "gaps": i.lst("gaps"), "reuse": i.lst("reuse")} for i in list_ideas()]
    gaps = sorted({g for i in ideas for g in i["gaps"]})
    return {
        "generated": time.strftime("%Y-%m-%d %H:%M"), "git": git_head(), "repo": ROOT.name,
        "components": comps, "models": models, "ideas": ideas, "gaps": gaps, "printer": PRINTER,
        "fields": FIELDS, "framings": list(FRAMINGS), "kinds": list(KINDS),
        "studio": json.loads((ROOT / "studio.json").read_text(encoding="utf-8")) if (ROOT / "studio.json").exists() else {},
        "inspiration_page": json.loads((ROOT / "inspiration.json").read_text(encoding="utf-8")) if (ROOT / "inspiration.json").exists() else {},
        "page": json.loads(BRIEF_JSON.read_text(encoding="utf-8")) if BRIEF_JSON.exists() else {},
    }


def write_html(d: dict, out: Path = OUT_HTML) -> Path:
    data = json.dumps(d).replace("</", "<\\/")
    page = (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", html.escape(f"{d['repo']} Briefs"))
            .replace("__DATA__", data))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def format_text(d: dict) -> str:
    lines = [f"{d['repo']} briefs — the form Claude reads, {len(d['components'])} components / "
             f"{len(d['models'])} models / {len(d['ideas'])} ideas quoted to the page"]
    for framing in FRAMINGS:
        lines.append(f"\n{framing} brief")
        for f in FIELDS[framing]:
            lines.append(f"  {f['key']:<12s} w{f['weight']}  -> {f['section']:<15s} {f['label']}")
            lines.append(f"               {f['hint']}")
    page = d.get("page") or {}
    lines.append("\npublished: " + (page.get("artifact_url") or "not yet — publish exports/brief.html and record brief.json"))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html", action="store_true", help="write exports/brief.html")
    ap.add_argument("--json", action="store_true", help="print the page data as JSON")
    ap.add_argument("--out", type=Path, default=OUT_HTML)
    a = ap.parse_args()
    d = page_data()
    print(json.dumps(d, indent=1) if a.json else format_text(d))
    if a.html:
        out = write_html(d, a.out)
        print(f"\nbriefs page {out.relative_to(ROOT)}   ({out.stat().st_size // 1024} kB)")
        if d["page"].get("artifact_url"):
            print(f"published at {d['page']['artifact_url']}  — republish with the Artifact tool, url=<that>, same file path")
        else:
            print('not yet published: publish it with the Artifact tool (capabilities {"db": {}, "sample": {}}) and record the URL in brief.json')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
