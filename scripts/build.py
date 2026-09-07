#!/usr/bin/env python
"""Build a model end to end: run it, report metrics, render, check printability,
export STL + STEP, and compare/update golden metrics.

    uv run python scripts/build.py <project> [--update-golden] [--no-render] [--no-export]

This is steps 4-8 of the new-part workflow in one command.  Exit code:
  0  built, checks passed, golden matches (or was created for a new model)
  2  built but golden differs (geometry changed) — review and pass --update-golden
  1  build error or printability problem
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR, ROOT, build_parts, diff_golden, export, format_changes, load_golden, metrics, run_fit_checks, write_golden, write_build_report, review_info, FIT_TOL_MM3  # noqa: E402
from scripts.check_printable import check_mesh, format_report  # noqa: E402
from scripts.render import render_project  # noqa: E402
from scripts._common import to_trimesh  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--update-golden", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--nozzle", type=float, default=0.4)
    a = ap.parse_args()

    t0 = time.time()
    parts = build_parts(a.project)
    print(f"built {a.project}: {len(parts)} part(s) in {time.time()-t0:.1f}s\n")

    current, checks, ok = {}, {}, True
    for name, shape in parts.items():
        m = metrics(shape)
        current[name] = m
        print(f"{name}: bbox {m.bbox_size[0]} x {m.bbox_size[1]} x {m.bbox_size[2]} mm  "
              f"(min {m.bbox_min}, max {m.bbox_max})  volume {m.volume:.1f} mm³ = {m.volume/1000:.2f} cm³  "
              f"solids={m.solids} valid={m.valid}")
        rep = check_mesh(to_trimesh(shape), a.nozzle)
        checks[name] = rep
        print(format_report(name, rep))
        ok &= rep["ok"] and m.valid
        if not a.no_export:
            stl, step = export(shape, a.project, name)
            print(f"      exported {stl.relative_to(ROOT)}  {step.relative_to(ROOT)}")
        print()

    fits = run_fit_checks(a.project, parts)
    if fits:
        for name, vol in fits.items():
            bad = vol > FIT_TOL_MM3
            ok &= not bad
            print(f"[{'FAIL' if bad else 'OK'}] fit check {name}: {vol} mm³ intersection" + ("  <- parts collide" if bad else ""))
        print()
    else:
        print("(no fit_checks() defined in the model — add one if the parts must mate or enclose hardware)\n")

    golden = load_golden(a.project)
    changes = diff_golden(golden, current)
    if golden is None:
        p = write_golden(a.project, current)
        print(f"no golden existed; wrote {p.relative_to(ROOT)}")
        rc = 0
    elif changes:
        print("golden diff:")
        print(format_changes(changes))
        if a.update_golden:
            p = write_golden(a.project, current)
            print(f"updated {p.relative_to(ROOT)}")
            rc = 0
        else:
            print("geometry differs from golden — if intended, rerun with --update-golden")
            rc = 2
    else:
        print("matches golden")
        rc = 0
    print()

    if not a.no_export:
        rep_path = write_build_report(a.project, parts, current, checks, fits, changes)
        print(f"build report {rep_path.relative_to(ROOT)}")
    if not a.no_render:
        for png in render_project(a.project, parts=parts):
            print(f"rendered {png.relative_to(ROOT)}   <- open this with Read to inspect")
        if not a.no_export:
            from scripts.export_viewer import project_run, write_viewer
            html_out = write_viewer([project_run(a.project)], MODELS_DIR / a.project / "exports" / "view.html", f"{a.project} review", a.project)
            print(f"review page {html_out.relative_to(ROOT)}   <- interactive 3D + report + notes")
            rv = review_info(a.project)
            if rv.get("artifact_url"):
                print(f"published review: {rv['artifact_url']}  (republish with the Artifact tool, url=<that>, same file path)")
            else:
                print("not yet published: publish exports/view.html with the Artifact tool (capabilities db) and record the URL in models/{}/review.json".format(a.project))
    print()
    return rc if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
