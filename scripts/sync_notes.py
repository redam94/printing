#!/usr/bin/env python
"""Pull review-page notes and Studio inbox ideas into the repo and turn print reports into state.

The artifact databases are only reachable through Claude's Artifact tool, so the flow is:

  1. Claude reads each collection with the Artifact tool (read_db, db_op list) and writes the
     documents it got back as a JSON list to .sync/<p>/notes.json (models/<p>/review.json pages)
     and .sync/studio/ideas.json (studio.json inbox). Each list item is {"id": <doc id>, ...fields}
     (an {"id", "data": {...}} envelope is also accepted). read_db's out_dir option, which writes
     .sync/<p>/notes/<doc_id>.json per document, works too but needs a file-write approval that a
     headless routine cannot give.
  2. uv run python scripts/sync_notes.py ingest [.sync]      (this script; --dry-run to preview)
       - mirrors every note into models/<p>/notes.json (committed; the repo copy of the critique log)
       - extracts print reports (kind == "print", or free text that reads like one -> inferred)
         into models/<p>/prints.json
       - records field evidence per component in lib/validation.json: a print that worked in a
         material validates every component the model uses (prune with --components if only
         some parts were printed); a failed print is recorded as a failure, never as validation
       - files inbox ideas into ideas/<slug>/IDEA.md
       - writes .sync/actions.json: the write_db updates Claude should apply (mark ideas filed,
         stamp notes as synced) — this script never talks to the artifact db itself
  3. uv run python scripts/reindex.py   (PARTS.md / parts.json pick up the evidence)
  4. Claude applies .sync/actions.json, rebuilds + republishes affected review pages and the Studio page.

Outcome vocabulary on a print note: "ok" (also worked/good/fits), "partial", "fail" (also failed/broke).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR, ROOT, list_projects, load_golden, review_info  # noqa: E402
from scripts.ideas import IDEAS_DIR, new_idea_text, slugify  # noqa: E402

SYNC_DIR = ROOT / ".sync"
VALIDATION_JSON = ROOT / "lib" / "validation.json"
STUDIO_JSON = ROOT / "studio.json"
OUTCOMES = {"ok": "ok", "worked": "ok", "works": "ok", "good": "ok", "fits": "ok", "fit": "ok", "pass": "ok", "success": "ok",
            "partial": "partial", "partly": "partial", "mostly": "partial", "meh": "partial",
            "fail": "fail", "failed": "fail", "broke": "fail", "broken": "fail", "bad": "fail", "snapped": "fail", "no": "fail"}
MATERIALS = ("PLA", "PETG", "TPU", "ASA", "ABS", "PC", "NYLON", "PA", "PLA+", "PLA-CF", "PETG-CF")
PRINT_WORDS = re.compile(r"\b(printed|print came out|test print|came off the (bed|printer)|off the printer|slic(ed|er))\b", re.I)
GOOD_WORDS = re.compile(r"\b(worked|works|fits?|good|great|perfect|snug|solid|no (issues|problems))\b", re.I)
BAD_WORDS = re.compile(r"\b(fail(ed|s)?|broke|snapped|crack(ed)?|warp(ed)?|too (tight|loose)|didn'?t fit|stringy|delaminat)\b", re.I)


def _unwrap(doc, fallback_id: str) -> dict:
    if isinstance(doc, dict) and "data" in doc and "id" in doc and isinstance(doc["data"], dict):  # {id, data} envelope
        doc = dict(doc["data"]) | {"id": doc["id"]}
    doc.setdefault("id", fallback_id)
    return doc


def load_docs(d: Path) -> list[dict]:
    """Documents of one collection, from either layout:
    <d>/<doc_id>.json per document (read_db out_dir), or a single <d>.json / <d>/all.json holding
    a JSON list of documents (or {"documents": [...]}) that Claude wrote from a read_db result."""
    docs: list[dict] = []
    for bundle in (d.with_suffix(".json"), d / "all.json"):
        if bundle.exists():
            try:
                data = json.loads(bundle.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            items = data.get("documents", data.get("docs", [])) if isinstance(data, dict) else data
            for i, doc in enumerate(items or []):
                if isinstance(doc, dict):
                    docs.append(_unwrap(doc, f"{bundle.stem}-{i}"))
    seen = {x["id"] for x in docs}
    for f in sorted(d.glob("*.json")) if d.exists() else []:
        if f.name == "all.json":
            continue
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(doc, dict):
            continue
        doc = _unwrap(doc, f.stem)
        if doc["id"] not in seen:
            docs.append(doc); seen.add(doc["id"])
    return docs


def classify_print(note: dict) -> dict | None:
    """Return {material, outcome, inferred} if the note is a print report, else None."""
    text = str(note.get("text") or "")
    kind = str(note.get("kind") or "")
    if kind == "print":
        outcome = OUTCOMES.get(str(note.get("outcome") or "").lower(), None)
        if outcome is None:
            outcome = "ok" if GOOD_WORDS.search(text) and not BAD_WORDS.search(text) else ("fail" if BAD_WORDS.search(text) else "ok")
        material = str(note.get("material") or _material_in(text) or "").upper()
        return {"material": material, "outcome": outcome, "inferred": False}
    if kind and kind != "critique":
        return None
    if PRINT_WORDS.search(text) and (GOOD_WORDS.search(text) or BAD_WORDS.search(text)):
        outcome = "fail" if BAD_WORDS.search(text) else "ok"
        return {"material": _material_in(text) or "", "outcome": outcome, "inferred": True}
    return None


def _material_in(text: str) -> str:
    for m in sorted(MATERIALS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(m)}\b", text, re.I):
            return m
    return ""


def _read_json(p: Path, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def _write_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ingest(sync_dir: Path = SYNC_DIR, *, components_override: dict[str, list[str]] | None = None, dry_run: bool = False,
           today: str | None = None) -> dict:
    """Do the whole deterministic half. Returns a summary dict (also printed by main)."""
    today = today or time.strftime("%Y-%m-%d")
    idx = _read_json(ROOT / "parts.json", {"components": {}, "models": {}})
    validation = _read_json(VALIDATION_JSON, {})
    actions: list[dict] = []
    summary = {"models": {}, "evidence_added": [], "ideas_filed": [], "inferred": [], "skipped_no_material": []}

    for project in list_projects():
        rv = review_info(project)
        docs = load_docs(sync_dir / project / "notes")
        if not docs:
            continue
        notes_path = MODELS_DIR / project / "notes.json"
        prints_path = MODELS_DIR / project / "prints.json"
        mirror = {"project": project, "artifact_url": rv.get("artifact_url", ""), "synced": today,
                  "notes": sorted(docs, key=lambda n: str(n.get("created", "")))}
        prints = _read_json(prints_path, {"project": project, "prints": []})
        known = {p.get("note_id") for p in prints["prints"]}
        open_critiques = sum(1 for n in docs if n.get("status") != "resolved" and classify_print(n) is None)
        added = 0
        for n in docs:
            cls = classify_print(n)
            if cls is None or n["id"] in known:
                continue
            parts = [n["part"]] if n.get("part") else sorted((load_golden(project) or {}).get("parts", {}))
            rec = {"note_id": n["id"], "date": str(n.get("created", ""))[:10] or today, "parts": parts, "material": cls["material"],
                   "outcome": cls["outcome"], "text": n.get("text", ""), "build_id": n.get("build_id", ""), "inferred": cls["inferred"]}
            prints["prints"].append(rec)
            added += 1
            if cls["inferred"]:
                summary["inferred"].append({"project": project, "note_id": n["id"], "text": n.get("text", "")[:120], "guess": cls})
            if not cls["material"]:
                summary["skipped_no_material"].append({"project": project, "note_id": n["id"]})
                continue
            comps = (components_override or {}).get(n["id"]) or idx["models"].get(project, {}).get("components", [])
            for cid in comps:
                ev_list = validation.setdefault(cid, [])
                if any(e.get("note_id") == n["id"] for e in ev_list):
                    continue
                ev_list.append({"material": cls["material"], "outcome": cls["outcome"], "model": project, "parts": parts,
                                "date": rec["date"], "note_id": n["id"], "inferred": cls["inferred"],
                                "text": (n.get("text") or "")[:200]})
                summary["evidence_added"].append({"component": cid, "material": cls["material"], "outcome": cls["outcome"], "model": project})
        for n in docs:
            if rv.get("artifact_url") and not n.get("synced"):
                actions.append({"artifact_url": rv["artifact_url"], "collection": rv.get("notes_collection", "notes"), "doc_id": n["id"],
                                "data": {"synced": today}})
        summary["models"][project] = {"notes": len(docs), "open_critiques": open_critiques, "prints_added": added}
        if not dry_run:
            _write_json(notes_path, mirror)
            _write_json(prints_path, prints)

    # Studio inbox -> ideas/
    studio = _read_json(STUDIO_JSON, {})
    for doc in load_docs(sync_dir / "studio" / "ideas"):
        if doc.get("status") != "inbox" or not doc.get("title"):
            continue
        slug = slugify(str(doc["title"]))
        path = IDEAS_DIR / slug / "IDEA.md"
        if not path.exists() and not dry_run:
            hw = [h.strip() for h in str(doc.get("hardware") or "").split(",") if h.strip()]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_idea_text(str(doc["title"]), kind=str(doc.get("kind") or "part"), status="inbox",
                                          text=str(doc.get("text") or ""), hardware=hw, source="the Studio inbox"), encoding="utf-8")
        summary["ideas_filed"].append({"slug": slug, "title": doc["title"], "existed": path.exists() and dry_run})
        if studio.get("artifact_url"):
            actions.append({"artifact_url": studio["artifact_url"], "collection": studio.get("inbox_collection", "ideas"), "doc_id": doc["id"],
                            "data": {"status": "filed", "path": str(path.relative_to(ROOT)), "slug": slug, "synced": today}})

    if not dry_run:
        for cid in list(validation):
            validation[cid].sort(key=lambda e: (e["date"], e["note_id"]))
        _write_json(VALIDATION_JSON, dict(sorted(validation.items())))
        _write_json(sync_dir / "actions.json", {"generated": today, "actions": actions})
    summary["actions"] = actions
    summary["validation"] = validation
    return summary


def format_summary(s: dict) -> str:
    out = []
    for p, m in s["models"].items():
        out.append(f"{p:<22s} {m['notes']} note(s) mirrored, {m['open_critiques']} open critique(s), {m['prints_added']} new print report(s)")
    if not s["models"]:
        out.append("no note dumps found (expected .sync/<project>/notes/*.json)")
    if s["evidence_added"]:
        out.append("\nfield evidence added:")
        for e in s["evidence_added"]:
            out.append(f"  {e['component']:<36s} {e['material']:<6s} {e['outcome']:<8s} from {e['model']}")
    if s["inferred"]:
        out.append("\nprint reports INFERRED from free text (check these; re-run with --components NOTE_ID=a,b to prune):")
        for i in s["inferred"]:
            out.append(f"  {i['project']} {i['note_id']}: {i['guess']}  \"{i['text']}\"")
    if s["skipped_no_material"]:
        out.append("\nprint reports without a material (recorded in prints.json, no component evidence):")
        for i in s["skipped_no_material"]:
            out.append(f"  {i['project']} {i['note_id']}")
    if s["ideas_filed"]:
        out.append("\ninbox ideas filed:")
        for i in s["ideas_filed"]:
            out.append(f"  ideas/{i['slug']}/IDEA.md  {i['title']}")
    out.append(f"\n{len(s['actions'])} db update(s) queued in .sync/actions.json (apply with Artifact write_db)")
    out.append("next: uv run python scripts/reindex.py && uv run python -m pytest -q; then rebuild + republish affected review pages and the Studio page")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ing = sub.add_parser("ingest", help="merge .sync dumps into the repo")
    ing.add_argument("sync_dir", nargs="?", type=Path, default=SYNC_DIR)
    ing.add_argument("--dry-run", action="store_true")
    ing.add_argument("--components", action="append", default=[], metavar="NOTE_ID=id1,id2",
                     help="limit the components a print note validates (repeatable)")
    a = ap.parse_args()
    override = {}
    for spec in a.components:
        k, _, v = spec.partition("=")
        override[k] = [x.strip() for x in v.split(",") if x.strip()]
    s = ingest(a.sync_dir, components_override=override, dry_run=a.dry_run)
    print(format_summary(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
