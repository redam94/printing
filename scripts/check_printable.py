#!/usr/bin/env python
"""Printability checks for a model (or a loose STL).

    uv run python scripts/check_printable.py <project> [--nozzle 0.4] [--json]
    uv run python scripts/check_printable.py --stl path/to/file.stl [--vase]

Checks per part:
  * watertight + consistent winding + positive volume (trimesh)
  * minimum wall thickness sampled over the surface (ray from the surface inward;
    a sample only counts when the ray exits through a roughly parallel face, so
    concave creases, rib roots and fillets do not read as thin walls); flags
    anything below 2 x nozzle and reports the fraction thinner than 3 x nozzle
  * overhang area: down-facing surfaces steeper than 45 deg that are not the
    bed face, plus flat horizontal ceilings (bridges) above the bed
  * footprint: which face is on the bed (z = min) and its area
  * openwork mode (``PRINT_MODES = {"part": "openwork"}``, or --openwork): the part
    is a lattice / perforated shell, and the inward-ray wall metric cannot measure
    one.  Sampling is by AREA, and in a perforated wall most of the surface is the
    inside of the holes, so a large fraction of samples sit within a nozzle width
    of a hole rim and read as thin walls that are not there.  Measured: a plain
    2.4 mm tube reads 0.00% under 0.8 mm; pierce it with a Voronoi lattice and the
    SAME 2.4 mm wall reads 21%, while a morphological opening — the honest measure,
    "material a 0.8 mm ball cannot reach" — puts it at 6% of volume against a 0.66%
    baseline for the unpierced tube.  So in this mode wall thickness is reported and
    warned on but does not gate; everything else (watertight, bodies, overhangs,
    ceilings) gates as normal, and ``--opening`` runs the slow honest measure.
  * vase mode (``PRINT_MODES = {"part": "vase"}`` in the model, or --vase): the
    slicer prints ONE continuous outer perimeter per layer, so the checks become
    "exactly one outer contour per layer above the floor" (islands / handles
    cannot print), overhangs measured at 60 deg (a single wall self-supports
    further) are problems not warnings, and flat ceilings above the floor are
    problems (nothing bridges them); wall thickness is informational only.

Exit code 1 if any part is not watertight or has walls thinner than 2 x nozzle
(openwork and vase parts excepted, see above).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import build_parts, print_modes, to_trimesh  # noqa: E402

OVERHANG_DEG = 45.0
OVERHANG_DEG_VASE = 60.0      # a single continuous wall self-supports further than a stacked perimeter
SAMPLES = 4000
VASE_LAYER_STEP = 1.0         # mm between checked layers
VASE_FLOOR = 2.0              # mm of solid bottom layers the slicer prints before spiralising
EXIT_PARALLEL_COS = -0.5      # exit face normal within 60 deg of anti-parallel to the entry normal
OPENING_PITCH = 0.25          # mm, voxel pitch for the --opening measure; 0.25 resolves a 0.4 mm ball


def wall_thickness_samples(mesh, samples: int = SAMPLES, seed: int = 0):
    """Wall thickness at random surface points, robust to creases.

    A ray is cast inward from each sample; the distance to the first exit counts only if the exit
    face is roughly anti-parallel to the entry face (a slab), so rays that clip a neighbouring face
    at a concave crease, rib root or fillet are discarded instead of reporting a phantom thin wall.
    """
    import numpy as np
    import trimesh

    pts, fid = trimesh.sample.sample_surface(mesh, samples, seed=seed)
    n = mesh.face_normals[fid]
    origins = pts - n * 1e-3
    loc, ray_idx, tri_idx = mesh.ray.intersects_location(origins, -n, multiple_hits=False)
    if len(ray_idx) == 0:
        return np.array([])
    th = np.linalg.norm(loc - origins[ray_idx], axis=1)
    n_exit = mesh.face_normals[tri_idx]
    parallel = (n[ray_idx] * n_exit).sum(axis=1) < EXIT_PARALLEL_COS
    th = th[parallel & np.isfinite(th) & (th > 1e-6)]
    return th


def opening_thin_fraction(mesh, nozzle: float = 0.4, pitch: float = OPENING_PITCH) -> float:
    """Fraction of VOLUME a ball of radius ``nozzle`` cannot reach: morphological opening.

    The honest thin-material measure, and the one to reach for when the inward-ray sampler and your
    eyes disagree on a perforated part.  It is slow (voxelising a 100 mm part takes ~30 s), which is
    why it is opt-in rather than part of every build.  Expect a per-cent or so on ANY part: the
    surface layer of voxels around every edge, chamfer and fillet is lost to the opening too, so
    read it against the same part without the feature you are suspicious of, not against zero.
    """
    import numpy as np
    from scipy import ndimage

    grid = mesh.voxelized(pitch=pitch).fill().matrix
    r = max(1, int(round(nozzle / pitch)))
    zz, yy, xx = np.ogrid[-r:r + 1, -r:r + 1, -r:r + 1]
    ball = (zz * zz + yy * yy + xx * xx) <= r * r
    opened = ndimage.binary_dilation(ndimage.binary_erosion(grid, structure=ball), structure=ball)
    total = int(grid.sum())
    return float(total - int((grid & opened).sum())) / total if total else 0.0


def vase_layers(mesh, step: float = VASE_LAYER_STEP, floor: float = VASE_FLOOR) -> dict:
    """Contour count per layer above the floor.  A spiral-mode part needs exactly one outer loop
    (inner loops = the shell's inner wall are fine; the slicer follows the outer)."""
    import numpy as np

    z0, z1 = float(mesh.bounds[0][2]), float(mesh.bounds[1][2])
    bad: list[float] = []
    checked = 0
    z = z0 + floor + step / 2
    while z < z1 - 0.05:
        sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        checked += 1
        if sec is None:
            bad.append(round(z, 1))
        else:
            try:
                planar, _ = sec.to_2D()
                outer = len(planar.polygons_full)
            except Exception:
                outer = len(sec.discrete)
            if outer != 1:
                bad.append(round(z, 1))
        z += step
    return {"layers_checked": checked, "multi_contour_layers": bad[:12], "multi_contour_count": len(bad)}


def check_mesh(mesh, nozzle: float = 0.4, samples: int = SAMPLES, mode: str = "normal") -> dict:
    import numpy as np

    vase, openwork = mode == "vase", mode == "openwork"
    rep: dict = {"print_mode": mode if mode in ("vase", "openwork") else "normal"}
    rep["watertight"] = bool(mesh.is_watertight)
    rep["winding_consistent"] = bool(mesh.is_winding_consistent)
    rep["volume_mm3"] = round(float(mesh.volume), 2)
    rep["bbox_mm"] = [round(float(x), 2) for x in mesh.extents]
    rep["bodies"] = int(len(mesh.split(only_watertight=False)))

    # --- wall thickness (crease-robust inward rays) ---
    try:
        th = wall_thickness_samples(mesh, samples)
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
    cos_lim = -np.sin(np.radians(OVERHANG_DEG_VASE if vase else OVERHANG_DEG))  # normal.z below this = surface tilted past the limit from vertical
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

    # --- vase mode: one outer contour per layer ---
    if vase:
        rep["vase"] = vase_layers(mesh)

    # --- verdicts ---
    problems, warnings = [], []
    if not rep["watertight"]:
        problems.append("mesh is not watertight (slicer may fail or fill gaps unpredictably)")
    if not rep["winding_consistent"]:
        problems.append("inconsistent face winding")
    if rep["bodies"] > 1:
        (problems if vase else warnings).append(f"{rep['bodies']} separate bodies in one part — intentional? (they will print as loose pieces)")
    if vase:
        v = rep["vase"]
        if v["multi_contour_count"]:
            problems.append(f"vase mode: {v['multi_contour_count']} of {v['layers_checked']} layers have != 1 outer contour "
                            f"(islands or splits at z {v['multi_contour_layers']}) — spiral mode prints one loop per layer")
        if rep["overhang_pct_of_surface"] > 1:
            problems.append(f"vase mode: {rep['overhang_area_mm2']} mm² steeper than {OVERHANG_DEG_VASE:.0f}° with no support possible "
                            f"(region {rep.get('overhang_regions_bbox')})")
        if rep["bridge_ceiling_area_mm2"] > 5:
            problems.append(f"vase mode: {rep['bridge_ceiling_area_mm2']} mm² of flat ceilings above the floor — nothing bridges in spiral mode")
        if rep.get("wall_min_mm") is not None and rep["wall_below_2x_nozzle_pct"] > 0.5:
            warnings.append(f"single wall: {rep['wall_below_2x_nozzle_pct']}% of surface < {2*nozzle:.1f} mm (fine in spiral mode, "
                            "the slicer extrudes one line regardless; not printable as a normal shell)")
    else:
        if openwork and rep.get("wall_min_mm") is not None and rep["wall_below_2x_nozzle_pct"] > 0.5:
            warnings.append(f"openwork: {rep['wall_below_2x_nozzle_pct']}% of surface < {2*nozzle:.1f} mm by the inward-ray metric, "
                            "which counts every hole rim — informational here, not a verdict. Size the webs at the "
                            "INNERMOST radius they reach and confirm with --opening if in doubt")
        elif rep.get("wall_min_mm") is not None and rep["wall_below_2x_nozzle_pct"] > 0.5:
            problems.append(f"{rep['wall_below_2x_nozzle_pct']}% of surface has walls < {2*nozzle:.1f} mm (min {rep['wall_min_mm']} mm)")
        elif not openwork and rep.get("wall_min_mm") is not None and rep["wall_below_3x_nozzle_pct"] > 5:
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
    tag = {"vase": "  [vase mode]", "openwork": "  [openwork]"}.get(rep.get("print_mode"), "")
    lines = [f"[{ 'OK' if rep['ok'] else 'FAIL'}] {name}: {rep['bbox_mm'][0]} x {rep['bbox_mm'][1]} x {rep['bbox_mm'][2]} mm, "
             f"{rep['volume_mm3']/1000:.1f} cm³, watertight={rep['watertight']}, bodies={rep['bodies']}{tag}"]
    if rep.get("wall_min_mm") is not None:
        lines.append(f"      walls: min {rep['wall_min_mm']} mm, 5th pct {rep['wall_p05_mm']} mm, "
                     f"<0.8: {rep['wall_below_2x_nozzle_pct']}%, <1.2: {rep['wall_below_3x_nozzle_pct']}%")
    if rep.get("opening_thin_pct") is not None:
        lines.append(f"      opening: {rep['opening_thin_pct']}% of volume a {rep['opening_ball_mm']} mm ball cannot reach")
    deg = OVERHANG_DEG_VASE if rep.get("print_mode") == "vase" else OVERHANG_DEG
    lines.append(f"      bed contact {rep['bed_contact_area_mm2']} mm², overhang>{deg:.0f}° {rep['overhang_area_mm2']} mm² "
                 f"({rep['overhang_pct_of_surface']}%), flat ceilings {rep['bridge_ceiling_area_mm2']} mm²")
    if rep.get("vase"):
        v = rep["vase"]
        lines.append(f"      vase layers: {v['layers_checked']} checked, {v['multi_contour_count']} with != 1 outer contour")
    for p in rep["problems"]:
        lines.append(f"      PROBLEM: {p}")
    for w in rep["warnings"]:
        lines.append(f"      warning: {w}")
    return "\n".join(lines)


def check_project(project: str, nozzle: float = 0.4, parts: dict | None = None,
                  opening: bool = False) -> dict[str, dict]:
    parts = parts or build_parts(project)
    modes = print_modes(project)
    out = {}
    for name, shape in parts.items():
        mesh = to_trimesh(shape)
        rep = check_mesh(mesh, nozzle, mode=modes.get(name, "normal"))
        if opening:
            rep["opening_thin_pct"] = round(100.0 * opening_thin_fraction(mesh, nozzle), 2)
            rep["opening_ball_mm"] = 2 * nozzle
        out[name] = rep
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?")
    ap.add_argument("--stl", type=Path)
    ap.add_argument("--nozzle", type=float, default=0.4)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--vase", action="store_true", help="check a --stl as a spiral / vase-mode print")
    ap.add_argument("--openwork", action="store_true", help="check a --stl as a lattice / perforated part")
    ap.add_argument("--opening", action="store_true",
                    help="also run the morphological opening measure (slow, ~30 s per part; the honest "
                         "thin-material number when the ray metric and your eyes disagree)")
    a = ap.parse_args()
    if a.stl:
        import trimesh
        mesh = trimesh.load(a.stl, force="mesh")
        rep = check_mesh(mesh, a.nozzle, mode="vase" if a.vase else "openwork" if a.openwork else "normal")
        if a.opening:
            rep["opening_thin_pct"] = round(100.0 * opening_thin_fraction(mesh, a.nozzle), 2)
            rep["opening_ball_mm"] = 2 * a.nozzle
        reports = {a.stl.stem: rep}
    elif a.project:
        reports = check_project(a.project, a.nozzle, opening=a.opening)
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
