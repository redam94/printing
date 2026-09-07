#!/usr/bin/env python
"""Impact analysis for a library component change.

    uv run python scripts/impact.py <component-id>            # which models use it, and do they still match their goldens?
    uv run python scripts/impact.py <component-id> --accept   # write new goldens for the affected models
    uv run python scripts/impact.py --all                     # re-check every model against its golden

Reads the reverse dependency map from parts.json (run reindex.py first),
rebuilds every model that imports the component, and diffs bounding box,
volume, watertightness and mesh hash against tests/regression/<model>.json.

Run this BEFORE committing any major (default-geometry-changing) bump, and
never pass --accept without showing the user the diff first: the goldens are
the record of parts that were already printed and fit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import ROOT, build_parts, diff_golden, format_changes, list_projects, load_golden, metrics, write_golden  # noqa: E402


def affected_models(component_id: str) -> list[str]:
    pj = ROOT / "parts.json"
    if not pj.exists():
        raise SystemExit("parts.json missing — run scripts/reindex.py")
    idx = json.loads(pj.read_text())
    comp = idx["components"].get(component_id)
    if comp is None:
        raise SystemExit(f"unknown component {component_id!r}; known: {', '.join(sorted(idx['components']))}")
    projects = sorted({Path(f).parts[1] for f in comp["used_by"]})
    return projects


def check_models(projects: list[str], accept: bool = False) -> dict[str, list[dict]]:
    results = {}
    for proj in projects:
        parts = build_parts(proj)
        current = {n: metrics(s) for n, s in parts.items()}
        golden = load_golden(proj)
        changes = diff_golden(golden, current)
        results[proj] = changes
        print(f"\n{proj}:")
        print(format_changes(changes))
        if accept and changes:
            p = write_golden(proj, current)
            print(f"  accepted -> {p.relative_to(ROOT)}")
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("component_id", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--accept", action="store_true", help="write new goldens for changed models (ask the user first!)")
    a = ap.parse_args()
    if a.all:
        projects = list_projects()
        print(f"checking all {len(projects)} models against goldens")
    elif a.component_id:
        projects = affected_models(a.component_id)
        if not projects:
            print(f"{a.component_id}: no models import it — safe to change (still bump version + reindex)")
            return 0
        print(f"{a.component_id} is used by {len(projects)} model(s): {', '.join(projects)}")
    else:
        ap.error("give a component id or --all")
    results = check_models(projects, a.accept)
    changed = [p for p, c in results.items() if c]
    print()
    if changed:
        kinds = {c["kind"] for p in changed for c in results[p]}
        if kinds <= {"mesh"}:
            print(f"{len(changed)} model(s) changed at mesh level only (tessellation/hash) — volume and bbox unchanged.")
        else:
            print(f"{len(changed)} model(s) CHANGED: {', '.join(changed)}" + ("" if a.accept else "  — review, then rerun with --accept if intended"))
        return 0 if a.accept else 2
    print("all affected models match their goldens")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
