#!/usr/bin/env python
"""Repo-level view: library, models, ideas and what needs attention, as text and as a page.

    uv run python scripts/studio.py            # text overview on stdout (for reading / for Claude)
    uv run python scripts/studio.py --html     # also write exports/studio.html (the Studio page)
    uv run python scripts/studio.py --json     # machine-readable overview on stdout

Reads only what already exists: parts.json, tests/regression goldens, each model's
exports/build_report.json + renders + review.json, and ideas/*/IDEA.md.  It never
builds a model, so it is fast; a model that was never built shows as "not built".

The Studio page has four tabs (Overview, Library, Models, Ideas) and an idea inbox
that persists in the artifact database when published with the Artifact tool
(capabilities {"db": {}}, URL recorded in studio.json at the repo root).
"""
from __future__ import annotations

import argparse
import ast
import base64
import html
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import GOLDEN_DIR, MODELS_DIR, ROOT, Metrics, diff_golden, list_projects, load_golden, prints_info, review_info  # noqa: E402
from scripts.ideas import STATUSES, list_ideas, validate  # noqa: E402
from scripts.inspiration import INSPIRATION_JSON, list_records as list_inspiration, thumb_data_uri  # noqa: E402
from scripts.references import list_records as list_references  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent / "studio_template.html"
STUDIO_JSON = ROOT / "studio.json"
OUT_HTML = ROOT / "exports" / "studio.html"


def git_head() -> dict:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%h%x09%cs%x09%s"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        h, d, s = out.split("\t", 2)
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        return {"hash": h, "date": d, "subject": s, "dirty": dirty}
    except Exception:
        return {}


def model_docstring(project: str) -> str:
    try:
        return ast.get_docstring(ast.parse((MODELS_DIR / project / "model.py").read_text(encoding="utf-8"))) or ""
    except Exception:
        return ""


def collect(with_images: bool = False) -> dict:
    idx = json.loads((ROOT / "parts.json").read_text(encoding="utf-8")) if (ROOT / "parts.json").exists() else {"components": {}, "models": {}}
    comps = idx.get("components", {})
    projects = list_projects()

    insp: dict[tuple[str, str], list[dict]] = {}
    for r in list_inspiration():
        d = {k: r[k] for k in ("id", "caption", "subject", "tags", "pending", "brief_model", "path", "created", "image")}
        if with_images and r["image"]:
            try:
                d["thumb"] = thumb_data_uri(ROOT / r["image"])
            except Exception:  # noqa: BLE001
                d["thumb"] = ""
        insp.setdefault((r["kind"], r["target"]), []).append(d)

    refs: dict[tuple[str, str], list[dict]] = {}
    for r in list_references():
        refs.setdefault((r["kind"], r["target"]), []).append(
            {k: r[k] for k in ("id", "title", "url", "source", "license", "why", "subject", "mechanism", "tags", "pending", "measured", "files", "path", "created")})

    models = []
    for p in projects:
        exports = MODELS_DIR / p / "exports"
        rep_path = exports / "build_report.json"
        report = json.loads(rep_path.read_text(encoding="utf-8")) if rep_path.exists() else {}
        golden = load_golden(p) or {}
        doc = report.get("docstring") or model_docstring(p)
        src_mtime = max((f.stat().st_mtime for f in (MODELS_DIR / p).glob("*.py")), default=0)
        stale = bool(report) and rep_path.stat().st_mtime < src_mtime
        parts = []
        names = list(report.get("parts", {})) or list(golden.get("parts", {}))
        for n in names:
            rp = report.get("parts", {}).get(n, {})
            m = rp.get("metrics") or golden.get("parts", {}).get(n, {})
            pr = rp.get("printability", {})
            entry = {"name": n, "bbox": m.get("bbox_size"), "volume": m.get("volume"), "watertight": m.get("watertight"),
                     "ok": pr.get("ok"), "wall_min_mm": pr.get("wall_min_mm"), "warnings": len(pr.get("warnings", []) or []),
                     "problems": len(pr.get("problems", []) or [])}
            png = exports / "renders" / f"{n}.png"
            if with_images and png.exists():
                entry["render"] = "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode("ascii")
            entry["has_render"] = png.exists()
            parts.append(entry)
        # compare the last build's metrics with the golden that is committed NOW (the report's own
        # golden_changes list is what the build saw before a possible --update-golden)
        golden_diff: list = []
        if report and golden:
            try:
                cur = {n: Metrics(**rp["metrics"]) for n, rp in report.get("parts", {}).items() if rp.get("metrics")}
                golden_diff = diff_golden(golden, cur)
            except TypeError:
                golden_diff = []
        rv = review_info(p)
        notes_path = MODELS_DIR / p / "notes.json"
        mirrored = json.loads(notes_path.read_text(encoding="utf-8")) if notes_path.exists() else {}
        open_critiques = [n for n in mirrored.get("notes", []) if n.get("status") != "resolved" and n.get("kind") != "print"]
        prints = prints_info(p).get("prints", [])
        models.append({
            "open_critiques": [{"part": n.get("part", ""), "text": n.get("text", ""), "created": str(n.get("created", ""))[:10]} for n in open_critiques],
            "notes_synced": mirrored.get("synced", ""),
            "prints": [{k: pr.get(k) for k in ("date", "parts", "material", "outcome", "text", "inferred")} for pr in prints],
            "project": p, "summary": doc.strip().split("\n\n")[0].replace("\n", " ") if doc else "", "docstring": doc,
            "components": idx.get("models", {}).get(p, {}).get("components", []),
            "components_versions": {c["id"]: c["version"] for c in report.get("components", [])},
            "parts": parts, "built_at": report.get("built_at", ""), "build_id": report.get("build_id", ""), "built": bool(report),
            "stale": stale, "golden": (GOLDEN_DIR / f"{p}.json").exists(), "golden_changes": golden_diff,
            "fit_checks": report.get("fit_checks", {}), "plate": report.get("plate", {}),
            "review_url": rv.get("artifact_url", ""), "params": len(report.get("params", [])),
            "inspiration": insp.get(("model", p), []),
            "references": refs.get(("model", p), []),
        })

    ideas = list_ideas()
    comp_ids = set(comps)
    idea_dicts = []
    for i in ideas:
        d = i.to_dict()
        d["problems"] = validate(i, comp_ids, set(projects))
        if with_images and i.renders:
            d["render"] = "data:image/png;base64," + base64.b64encode(i.renders[0].read_bytes()).decode("ascii")
        d["has_render"] = bool(i.renders)
        d["inspiration"] = insp.get(("idea", i.slug), [])
        d["references"] = refs.get(("idea", i.slug), [])
        idea_dicts.append(d)

    comp_rows = []
    for cid, c in sorted(comps.items()):
        mn = c.get("material_notes") or {}
        validated = mn.get("validated") or []
        if isinstance(validated, str):
            validated = [validated]
        comp_rows.append({
            "id": cid, "category": cid.split(".", 1)[0], "name": cid.split(".", 1)[1], "version": c.get("version", ""),
            "summary": c.get("summary", ""), "tags": c.get("tags", []), "returns": c.get("returns", ""),
            "validated": validated, "orientation": mn.get("orientation", ""), "notes": mn.get("notes", ""),
            "field_validated": mn.get("field_validated", []), "field_failed": mn.get("field_failed", []),
            "evidence": [{k: e.get(k) for k in ("material", "outcome", "model", "date", "parts")} for e in mn.get("evidence", [])],
            "unvalidated": not validated and not mn.get("field_validated"),
            "used_by": sorted({u.split("/")[1] for u in c.get("used_by", []) if u.startswith("models/")}),
            "params": c.get("params", []), "example": c.get("example", ""), "import": c.get("import", ""),
            "file": c.get("file", ""), "line": c.get("line"),
            "wanted_by": [i.slug for i in ideas if cid in i.lst("reuse")],
        })
    gap_ids = sorted({g for i in ideas for g in i.lst("gaps")})
    gaps = [{"id": g, "wanted_by": [i.slug for i in ideas if g in i.lst("gaps")]} for g in gap_ids]

    attention = []
    for m in models:
        if not m["built"]:
            attention.append({"kind": "model", "ref": m["project"], "text": "never built — no exports/build_report.json", "fix": f"uv run python scripts/build.py {m['project']}"})
        elif m["stale"]:
            attention.append({"kind": "model", "ref": m["project"], "text": "source changed since last build", "fix": f"uv run python scripts/build.py {m['project']}"})
        if m["built"] and not m["review_url"]:
            attention.append({"kind": "model", "ref": m["project"], "text": "review page not published", "fix": "publish exports/view.html with the Artifact tool, record models/<p>/review.json"})
        if m["golden_changes"]:
            attention.append({"kind": "model", "ref": m["project"], "text": "last build differed from its golden", "fix": "review the diff; --update-golden only if intended"})
        if m["open_critiques"]:
            n = len(m["open_critiques"])
            attention.append({"kind": "model", "ref": m["project"], "text": f"{n} open critique{'s' if n > 1 else ''} on the review page (as of {m['notes_synced']})", "fix": "read them with Artifact read_db before modifying; resolve after the rebuild"})
        for pr in m["prints"]:
            if pr.get("outcome") == "fail":
                attention.append({"kind": "model", "ref": m["project"], "text": f"print FAILED {pr.get('date')} in {pr.get('material') or '?'}: {(pr.get('text') or '')[:80]}", "fix": ""})
        for c in comp_rows:
            if c["field_failed"]:
                attention.append({"kind": "component", "ref": c["id"], "text": f"print failures recorded in {', '.join(c['field_failed'])}", "fix": "check lib/validation.json; fix the geometry or note the material to avoid"})
        for p in m["parts"]:
            if p.get("ok") is False:
                attention.append({"kind": "part", "ref": f"{m['project']}/{p['name']}", "text": "printability check failed at last build", "fix": ""})
        for name, vol in (m["fit_checks"] or {}).items():
            if vol and vol > 0.05:
                attention.append({"kind": "part", "ref": f"{m['project']}", "text": f"fit check {name} intersects ({vol} mm³)", "fix": ""})
    for c in comp_rows:
        if c["unvalidated"]:
            attention.append({"kind": "component", "ref": c["id"], "text": "UNVALIDATED — no test print recorded", "fix": "print it, then update material_notes"})
    unused = [c["id"] for c in comp_rows if not c["used_by"]]
    for i in idea_dicts:
        for pr in i["problems"]:
            attention.append({"kind": "idea", "ref": i["slug"], "text": pr, "fix": f"edit {i['path']}"})
    for recs in insp.values():
        for r in recs:
            if r["pending"]:
                attention.append({"kind": "photo", "ref": r["path"], "text": "inspiration photo has no brief yet", "fix": "design-inspiration skill: Haiku subagent reads it, then inspiration.py set-brief"})
    for recs in refs.values():
        for r in recs:
            if r["pending"]:
                attention.append({"kind": "reference", "ref": r["path"], "text": "reference model has no reading yet", "fix": "design-references skill: Haiku subagent reads page + images, then references.py set-reading"})

    # design request tickets (scripts/tickets.py): the ones that need a person, not the requester
    tickets = []
    try:
        from scripts.tickets import NEXT as TICKET_NEXT, list_tickets, ticket_summary
        tickets = [ticket_summary(t) for t in list_tickets()]
    except Exception:
        TICKET_NEXT = {}
    for t in tickets:
        if t["status"] in ("new", "changes", "approved", "printing"):
            what = {"new": "new request", "changes": "requester sent notes on quote r%s" % ((t["quote"] or {}).get("rev", "?")),
                    "approved": "approved — print it", "printing": "on the bed"}[t["status"]]
            attention.append({"kind": "ticket", "ref": t["id"], "text": f"{what}: {t['title'][:60]} ({t['requester'].get('name') or t['requester'].get('email')})",
                              "fix": TICKET_NEXT.get(t["status"], "")})

    cats: dict[str, int] = {}
    for c in comp_rows:
        cats[c["category"]] = cats.get(c["category"], 0) + 1
    by_status = {s: sum(1 for i in idea_dicts if i["status"] == s) for s in STATUSES}

    return {
        "generated": time.strftime("%Y-%m-%d %H:%M"), "git": git_head(), "repo": ROOT.name,
        "studio": json.loads(STUDIO_JSON.read_text(encoding="utf-8")) if STUDIO_JSON.exists() else {},
        "inspiration_page": json.loads(INSPIRATION_JSON.read_text(encoding="utf-8")) if INSPIRATION_JSON.exists() else {},
        "stats": {"components": len(comp_rows), "categories": cats, "models": len(models), "parts": sum(len(m["parts"]) for m in models),
                  "ideas": len(idea_dicts), "ideas_by_status": by_status, "unused_components": len(unused), "unvalidated": sum(c["unvalidated"] for c in comp_rows),
                  "gaps": len(gaps), "inspiration": sum(len(v) for v in insp.values()),
                  "inspiration_pending": sum(1 for v in insp.values() for r in v if r["pending"]),
                  "references": sum(len(v) for v in refs.values()), "references_pending": sum(1 for v in refs.values() for r in v if r["pending"]),
                  "tickets": len(tickets), "tickets_open": sum(1 for t in tickets if t["status"] not in ("done", "declined")),
                  "tickets_by_status": {k: sum(1 for t in tickets if t["status"] == k) for k in sorted({t["status"] for t in tickets})}},
        "components": comp_rows, "unused": unused, "gaps": gaps, "models": models, "ideas": idea_dicts, "attention": attention,
        "statuses": list(STATUSES),
    }


def _insp_lines(lines: list[str], recs: list[dict], indent: str = "    ") -> None:
    for r in recs:
        what = r["subject"] or r["caption"] or "-"
        flag = "BRIEF PENDING  " if r["pending"] else ""
        lines.append(f"{indent}inspiration {r['path']}  {flag}{what[:90]}" + (f"  [{', '.join(r['tags'][:6])}]" if r["tags"] else ""))


def _ref_lines(lines: list[str], recs: list[dict], indent: str = "    ") -> None:
    for r in recs:
        what = r["mechanism"] or r["subject"] or r["why"] or "-"
        flag = "READING PENDING  " if r["pending"] else ""
        extra = ("  measured" if r["measured"] else "") + (f"  files: {', '.join(r['files'])}" if r["files"] else "")
        lines.append(f"{indent}reference {r['path']}  {flag}{r['title'][:50]} [{r['source']}]  {what[:80]}{extra}")


def format_text(d: dict) -> str:
    s = d["stats"]
    g = d["git"]
    lines = [f"{d['repo']} studio — {s['components']} components · {s['models']} models ({s['parts']} parts) · {s['ideas']} ideas"
             f"   HEAD {g.get('hash', '?')} {g.get('date', '')}{' (dirty)' if g.get('dirty') else ''}   generated {d['generated']}"]
    if d["studio"].get("artifact_url"):
        lines.append(f"studio page: {d['studio']['artifact_url']}   (read the inbox: Artifact read_db collection 'ideas' where status == inbox)")
    if d.get("inspiration_page", {}).get("artifact_url"):
        lines.append(f"inspiration page: {d['inspiration_page']['artifact_url']}   (photos: Artifact read_db collection 'inspiration' where status == inbox; {s.get('inspiration', 0)} filed, {s.get('inspiration_pending', 0)} brief(s) pending)")
    if s.get("tickets"):
        lines.append(f"tickets: {s['tickets_open']} open of {s['tickets']} ({', '.join(f'{v} {k}' for k, v in s['tickets_by_status'].items())})   uv run python scripts/tickets.py")
    lines += ["", "LIBRARY"]
    cur = None
    for c in d["components"]:
        if c["category"] != cur:
            cur = c["category"]
            lines.append(f"  [{cur}]")
        used = f"used by {', '.join(c['used_by'])}" if c["used_by"] else "unused"
        val = "UNVALIDATED" if c["unvalidated"] else ", ".join(c["validated"]) or "-"
        if c["field_validated"]:
            val += f" +printed:{','.join(c['field_validated'])}"
        if c["field_failed"]:
            val += f" FAILED:{','.join(c['field_failed'])}"
        want = f"  wanted by ideas: {', '.join(c['wanted_by'])}" if c["wanted_by"] else ""
        lines.append(f"    {c['id']:<36s} v{c['version']:<7s} {val:<14s} {used}{want}")
        lines.append(f"      {c['summary']}")
    if d["gaps"]:
        lines += ["", "LIBRARY GAPS (components ideas need that do not exist)"]
        for gp in d["gaps"]:
            lines.append(f"    {gp['id']:<36s} wanted by {', '.join(gp['wanted_by'])}")
    lines += ["", "MODELS"]
    for m in d["models"]:
        built = f"built {m['built_at']}" + (" STALE" if m["stale"] else "") if m["built"] else "NOT BUILT"
        review = m["review_url"] or "unpublished"
        plate = "" if not m["plate"] else ("  plate fits" if m["plate"].get("fits_bed") else "  PLATE DOES NOT FIT")
        lines.append(f"  {m['project']:<24s} {len(m['parts'])} part(s)  {built}  golden {'yes' if m['golden'] else 'no'}{plate}  review {review}")
        if m["summary"]:
            lines.append(f"    {m['summary'][:160]}")
        for p in m["parts"]:
            bb = " x ".join(f"{v:.1f}" for v in p["bbox"]) if p.get("bbox") else "?"
            vol = f"{p['volume'] / 1000:.1f} cm³" if p.get("volume") else "?"
            verdict = "ok" if p.get("ok") else ("FAIL" if p.get("ok") is False else "?")
            lines.append(f"      {p['name']:<20s} {bb:<24s} {vol:>10s}  print {verdict}  wall_min {p.get('wall_min_mm')}")
        lines.append(f"    uses: {', '.join(m['components']) or '-'}")
        for pr in m["prints"]:
            lines.append(f"    printed {pr.get('date')} {', '.join(pr.get('parts') or []) or 'whole model'} in {pr.get('material') or '?'}: {pr.get('outcome')}{' (inferred)' if pr.get('inferred') else ''}  {(pr.get('text') or '')[:100]}")
        for n in m["open_critiques"]:
            lines.append(f"    open critique [{n['part'] or 'whole model'}] {n['created']}: {n['text'][:120]}")
        _insp_lines(lines, m.get("inspiration", []))
        _ref_lines(lines, m.get("references", []))
    lines += ["", "IDEAS"]
    if not d["ideas"]:
        lines.append("  (none yet — ideas/README.md explains the format; the Studio page inbox captures new ones)")
    for i in d["ideas"]:
        lines.append(f"  [{i['status']:<11s}] {i['slug']:<28s} {i['kind']:<12s} {i['title']}")
        if i["reuse"]:
            lines.append(f"      reuse: {', '.join(i['reuse'])}")
        if i["gaps"]:
            lines.append(f"      gaps:  {', '.join(i['gaps'])}")
        if i["hardware"]:
            lines.append(f"      hardware: {', '.join(i['hardware'])}")
        if i["has_sketch"]:
            lines.append(f"      sketch: uv run python scripts/sketch.py {i['slug']}")
        if i["model"]:
            lines.append(f"      model: models/{i['model']}")
        for pr in i["problems"]:
            lines.append(f"      ! {pr}")
        _insp_lines(lines, i.get("inspiration", []), indent="      ")
        _ref_lines(lines, i.get("references", []), indent="      ")
    lines += ["", f"ATTENTION ({len(d['attention'])})"]
    for a in d["attention"]:
        fix = f"   -> {a['fix']}" if a["fix"] else ""
        lines.append(f"  {a['kind']:<10s} {a['ref']:<34s} {a['text']}{fix}")
    if d["unused"]:
        lines.append(f"  unused components ({len(d['unused'])}): {', '.join(d['unused'])}")
    return "\n".join(lines)


def write_html(d: dict, out: Path = OUT_HTML) -> Path:
    data = json.dumps(d).replace("</", "<\\/")
    page = (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", html.escape(f"{d['repo']} Studio"))
            .replace("__DATA__", data))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html", action="store_true", help="write exports/studio.html")
    ap.add_argument("--json", action="store_true", help="print the overview as JSON instead of text")
    ap.add_argument("--out", type=Path, default=OUT_HTML)
    a = ap.parse_args()
    d = collect(with_images=a.html)
    if a.json:
        slim = {k: v for k, v in d.items()}
        for m in slim["models"]:
            for p in m["parts"]:
                p.pop("render", None)
        for i in slim["ideas"]:
            i.pop("render", None)
        print(json.dumps(slim, indent=1))
    else:
        print(format_text(d))
    if a.html:
        out = write_html(d, a.out)
        print(f"\nstudio page {out.relative_to(ROOT)}   ({out.stat().st_size // 1024} kB)")
        if d["studio"].get("artifact_url"):
            print(f"published at {d['studio']['artifact_url']}  — republish with the Artifact tool, url=<that>, same file path")
        else:
            print("not yet published: publish it with the Artifact tool (capabilities {\"db\": {}}) and record the URL in studio.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
