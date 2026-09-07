#!/usr/bin/env python
"""Printability checks for a model (or a loose STL).

    uv run python scripts/check_printable.py <project> [--nozzle 0.4] [--json]
    uv run python scripts/check_printable.py --stl path/to/file.stl

Checks per part:
  * watertight + consistent winding + positive volume (trimesh)
  * minimum wall thickness sampled over the surface; flags anything below
    2 x nozzle (not printable as a solid wall) and reports the fraction of
    surface thinner than 3 x nozzle
  * overhang area: down-facing surfaces steeper than 45 deg that are not the
    bed face, plus flat horizontal ceilings (bridges) above the bed
  * footprint: which face is on the bed (z = min) and its area

Exit code 1 if any part is not watertight or has walls thinner than 2 x nozzle.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import build_parts, to_trimesh  # noqa: E402

OVERHANG_DEG = 45.0
SAMPLES = 4000


def check_mesh(mesh, nozzle: float = 0.4, samples: int = SAMPLES) -> dict:
    import numpy as np
    import trimesh

    rep: dict = {}
    rep["watertight"] = bool(mesh.is_watertight)
    rep["winding_consistent"] = bool(mesh.is_winding_consistent)
    rep["volume_mm3"] = round(float(mesh.volume), 2)
    rep["bbox_mm"] = [round(float(x), 2) for x in mesh.extents]
    rep["bodies"] = int(len(mesh.split(only_watertight=False)))

    # --- wall thickness (ray from surface point inward along -normal) ---
    pts, fid = trimesh.sample.sample_surface(mesh, samples)
    normals = mesh.face_normals[fid]
    try:
        th = trimesh.proximity.thickness(mesh, pts, exterior=False, normals=normals, method="ray")
        th = th[np.isfinite(th) & (th > 1e-6)]
    except Exception:  # pragma: no cover
        th = np.array([])
    if len(th):
        rep["wall_min_mm"] = round(float(th.min()), 2)
        rep["wall_p05_mm"] = round(float(np.percentile(th, 5)), 2)
        rep["wall_below_2x_nozzle_pct"] = round(100.0 * float((th < 2 * nozzle - 0.05).mean()), 1)
        rep["wall_below_3x_nozzle_pct"] = round(100.0 * float((th < 3 * nozzle - 0.05).mean()), 1)
    else:
        rep["wall_min_mm"] = None

    # --- overhangs ---
    z_min = float(mesh.bounds[0][2])
    fn = mesh.face_normals
    fc = mesh.triangles_center
    fa = mesh.area_faces
    cos_lim = -np.cos(np.radians(OVERHANG_DEG))  # normal.z below this = steeper than 45 deg downward
    down = fn[:, 2] < cos_lim
    on_bed = np.abs(fc[:, 2] - z_min) < 0.05
    overhang = down & ~on_bed
    flat_ceiling = (fn[:, 2] < -0.98) & ~on_bed
    rep["bed_contact_area_mm2"] = round(float(fa[on_bed].sum()), 1)
    rep["overhang_area_mm2"] = round(float(fa[overhang].sum()), 1)
    rep["overhang_pct_of_surface"] = round(100.0 * float(fa[overhang].sum() / fa.sum()), 1)
    rep["bridge_ceiling_area_mm2"] = round(float(fa[flat_ceiling].sum()), 1)
    if overhang.any():
        oc = fc[overhang]
        rep["overhang_regions_bbox"] = [[round(float(x), 1) for x in oc.min(axis=0)], [round(float(x), 1) for x in oc.max(axis=0)]]
        heights = np.unique(np.round(fc[flat_ceiling][:, 2], 1)) if flat_ceiling.any() else []
        rep["ceiling_heights_mm"] = [float(h) for h in heights[:8]]

    # --- verdicts ---
    problems, warnings = [], []
    if not rep["watertight"]:
        problems.append("mesh is not watertight (slicer may fail or fill gaps unpredictably)")
    if not rep["winding_consistent"]:
        problems.append("inconsistent face winding")
    if rep["bodies"] > 1:
        warnings.append(f"{rep['bodies']} separate bodies in one part — intentional? (they will print as loose pieces)")
    if rep.get("wall_min_mm") is not None and rep["wall_below_2x_nozzle_pct"] > 0.5:
        problems.append(f"{rep['wall_below_2x_nozzle_pct']}% of surface has walls < {2*nozzle:.1f} mm (min {rep['wall_min_mm']} mm)")
    elif rep.get("wall_min_mm") is not None and rep["wall_below_3x_nozzle_pct"] > 5:
        warnings.append(f"{rep['wall_below_3x_nozzle_pct']}% of surface has walls < {3*nozzle:.1f} mm — fine for lids/webs, weak for load paths")
    if rep["overhang_pct_of_surface"] > 2:
        warnings.append(f"{rep['overhang_area_mm2']} mm² of >45° overhang not on the bed — needs support or reorientation "
                        f"(region {rep.get('overhang_regions_bbox')})")
    if rep["bridge_ceiling_area_mm2"] > 50:
        warnings.append(f"{rep['bridge_ceiling_area_mm2']} mm² of flat ceilings above the bed (bridges/hole tops) — ok if spans are short; teardrop horizontal holes")
    rep["problems"] = problems
    rep["warnings"] = warnings
    rep["ok"] = not problems
    return rep


def format_report(name: str, rep: dict) -> str:
    lines = [f"[{ 'OK' if rep['ok'] else 'FAIL'}] {name}: {rep['bbox_mm'][0]} x {rep['bbox_mm'][1]} x {rep['bbox_mm'][2]} mm, "
             f"{rep['volume_mm3']/1000:.1f} cm³, watertight={rep['watertight']}, bodies={rep['bodies']}"]
    if rep.get("wall_min_mm") is not None:
        lines.append(f"      walls: min {rep['wall_min_mm']} mm, 5th pct {rep['wall_p05_mm']} mm, "
                     f"<0.8: {rep['wall_below_2x_nozzle_pct']}%, <1.2: {rep['wall_below_3x_nozzle_pct']}%")
    lines.append(f"      bed contact {rep['bed_contact_area_mm2']} mm², overhang>45° {rep['overhang_area_mm2']} mm² "
                 f"({rep['overhang_pct_of_surface']}%), flat ceilings {rep['bridge_ceiling_area_mm2']} mm²")
    for p in rep["problems"]:
        lines.append(f"      PROBLEM: {p}")
    for w in rep["warnings"]:
        lines.append(f"      warning: {w}")
    return "\n".join(lines)


def check_project(project: str, nozzle: float = 0.4, parts: dict | None = None) -> dict[str, dict]:
    parts = parts or build_parts(project)
    return {name: check_mesh(to_trimesh(shape), nozzle) for name, shape in parts.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?")
    ap.add_argument("--stl", type=Path)
    ap.add_argument("--nozzle", type=float, default=0.4)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.stl:
        import trimesh
        reports = {a.stl.stem: check_mesh(trimesh.load(a.stl, force="mesh"), a.nozzle)}
    elif a.project:
        reports = check_project(a.project, a.nozzle)
    else:
        ap.error("give a project or --stl")
    if a.json:
        print(json.dumps(reports, indent=2))
    else:
        for n, r in reports.items():
            print(format_report(n, r))
    return 0 if all(r["ok"] for r in reports.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
