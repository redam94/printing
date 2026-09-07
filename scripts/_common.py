"""Shared helpers for the tooling scripts: model discovery, metrics, export.

Model convention
----------------
``models/<project>/model.py`` defines ``build() -> dict[str, Shape]`` mapping a
print-part name to a build123d solid (Part or Compound) in PRINT orientation.
``params.py`` beside it holds every dimension.  Exports land in
``models/<project>/exports/``.

Optionally ``fit_checks(parts) -> dict[str, tuple[Shape, Shape]]`` returns
pairs of shapes that must NOT intersect once assembled (lid placed on body,
PCB envelope vs bosses, ...).  ``build.py`` intersects each pair and fails on
any overlap: the printability check cannot see two parts colliding.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODELS_DIR = ROOT / "models"
GOLDEN_DIR = ROOT / "tests" / "regression"
LIB_DIR = ROOT / "lib"

# tessellation used for STL export and for the mesh hash (must stay fixed:
# changing it changes every golden hash)
STL_TOLERANCE = 0.01
STL_ANGULAR_TOLERANCE = 0.1


def list_projects() -> list[str]:
    return sorted(p.parent.name for p in MODELS_DIR.glob("*/model.py"))


def load_model(project: str):
    """Import ``models.<project>.model`` and return the module."""
    if not (MODELS_DIR / project / "model.py").exists():
        raise SystemExit(f"no such model: models/{project}/model.py  (known: {', '.join(list_projects())})")
    mod = importlib.import_module(f"models.{project}.model")
    if not hasattr(mod, "build"):
        raise SystemExit(f"models/{project}/model.py must define build() -> dict[str, Part]")
    return mod


def build_parts(project: str) -> dict:
    """Run the model's build() and normalise the result to {name: shape}."""
    mod = load_model(project)
    result = mod.build()
    if not isinstance(result, dict):
        result = {project: result}
    return result


@dataclass
class Metrics:
    bbox_min: list[float]
    bbox_max: list[float]
    bbox_size: list[float]
    volume: float
    surface_area: float
    solids: int
    valid: bool
    watertight: bool
    mesh_hash: str
    triangles: int

    def to_dict(self) -> dict:
        return asdict(self)


def tessellate(shape, tolerance: float = STL_TOLERANCE, angular_tolerance: float = STL_ANGULAR_TOLERANCE):
    """Return (vertices ndarray (n,3), faces ndarray (m,3))."""
    import numpy as np

    verts, tris = shape.tessellate(tolerance, angular_tolerance)
    v = np.array([[p.X, p.Y, p.Z] for p in verts], dtype=float)
    f = np.array(tris, dtype=int).reshape(-1, 3)
    return v, f


def to_trimesh(shape):
    import trimesh

    v, f = tessellate(shape)
    mesh = trimesh.Trimesh(vertices=v, faces=f, process=True)
    return mesh


def mesh_hash(shape) -> str:
    """Stable hash of the tessellated geometry, independent of vertex order."""
    import numpy as np

    v, f = tessellate(shape)
    tri = v[f]                                   # (m,3,3)
    tri = np.round(tri, 3)
    # canonical order within each triangle, then sort triangles
    tri = np.sort(tri.reshape(len(tri), -1), axis=1)
    order = np.lexsort(tri.T[::-1])
    return hashlib.sha256(tri[order].tobytes()).hexdigest()[:16]


def metrics(shape) -> Metrics:
    bb = shape.bounding_box()
    mesh = to_trimesh(shape)
    return Metrics(
        bbox_min=[round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
        bbox_max=[round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
        bbox_size=[round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
        volume=round(float(shape.volume), 3),
        surface_area=round(float(shape.area), 3),
        solids=len(shape.solids()),
        valid=bool(shape.is_valid),
        watertight=bool(mesh.is_watertight),
        mesh_hash=mesh_hash(shape),
        triangles=int(len(mesh.faces)),
    )


def export(shape, project: str, name: str) -> tuple[Path, Path]:
    from build123d import export_step, export_stl

    out = MODELS_DIR / project / "exports"
    out.mkdir(parents=True, exist_ok=True)
    stl = out / f"{name}.stl"
    step = out / f"{name}.step"
    export_stl(shape, str(stl), tolerance=STL_TOLERANCE, angular_tolerance=STL_ANGULAR_TOLERANCE)
    export_step(shape, str(step))
    return stl, step


def golden_path(project: str) -> Path:
    return GOLDEN_DIR / f"{project}.json"


def load_golden(project: str) -> dict | None:
    p = golden_path(project)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def write_golden(project: str, part_metrics: dict[str, Metrics]) -> Path:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "project": project,
        "generated": time.strftime("%Y-%m-%d"),
        "tessellation": {"tolerance": STL_TOLERANCE, "angular_tolerance": STL_ANGULAR_TOLERANCE},
        "parts": {n: m.to_dict() for n, m in part_metrics.items()},
    }
    p = golden_path(project)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p


VOLUME_RTOL = 1e-4
BBOX_ATOL = 1e-3


def diff_golden(golden: dict | None, current: dict[str, Metrics]) -> list[dict]:
    """Compare current metrics to a golden file. Returns a list of change records."""
    changes: list[dict] = []
    if golden is None:
        return [{"part": n, "field": "golden", "old": None, "new": "missing", "kind": "new"} for n in current]
    gparts = golden.get("parts", {})
    for name, m in current.items():
        g = gparts.get(name)
        if g is None:
            changes.append({"part": name, "field": "part", "old": None, "new": "added", "kind": "added"})
            continue
        if abs(m.volume - g["volume"]) > VOLUME_RTOL * max(abs(g["volume"]), 1e-9):
            pct = 100.0 * (m.volume - g["volume"]) / g["volume"] if g["volume"] else float("inf")
            changes.append({"part": name, "field": "volume", "old": g["volume"], "new": m.volume, "kind": "geometry", "delta": f"{pct:+.3f}%"})
        for i, ax in enumerate("xyz"):
            if abs(m.bbox_size[i] - g["bbox_size"][i]) > BBOX_ATOL:
                changes.append({"part": name, "field": f"bbox_{ax}", "old": g["bbox_size"][i], "new": m.bbox_size[i], "kind": "geometry",
                                "delta": f"{m.bbox_size[i] - g['bbox_size'][i]:+.3f} mm"})
        if m.watertight != g["watertight"]:
            changes.append({"part": name, "field": "watertight", "old": g["watertight"], "new": m.watertight, "kind": "integrity"})
        if m.mesh_hash != g["mesh_hash"]:
            changes.append({"part": name, "field": "mesh_hash", "old": g["mesh_hash"], "new": m.mesh_hash, "kind": "mesh"})
    for name in gparts:
        if name not in current:
            changes.append({"part": name, "field": "part", "old": "present", "new": None, "kind": "removed"})
    return changes


def format_changes(changes: list[dict]) -> str:
    if not changes:
        return "  no changes vs golden"
    lines = []
    for c in changes:
        d = f"  ({c['delta']})" if c.get("delta") else ""
        lines.append(f"  {c['part']:<20s} {c['field']:<12s} {str(c['old']):>18s} -> {str(c['new']):<18s}{d}")
    return "\n".join(lines)


FIT_TOL_MM3 = 0.05


def run_fit_checks(project: str, parts: dict) -> dict[str, float]:
    """Return {check_name: intersection volume mm^3} for the model's fit_checks(), or {}."""
    mod = load_model(project)
    fn = getattr(mod, "fit_checks", None)
    if fn is None:
        return {}
    out = {}
    for name, (a, b) in fn(parts).items():
        try:
            inter = a & b
            vol = float(inter.volume) if inter is not None and inter.wrapped is not None else 0.0
        except Exception:
            vol = 0.0
        out[name] = round(vol, 3)
    return out


# ---------------------------------------------------------------------------
# Build report (feeds exports/build_report.json and the interactive viewer)
# ---------------------------------------------------------------------------

def params_snapshot(project: str) -> list[dict]:
    """UPPER_CASE constants from models/<project>/params.py with their values and trailing comments."""
    import ast
    import importlib

    src_path = MODELS_DIR / project / "params.py"
    if not src_path.exists():
        return []
    src = src_path.read_text(encoding="utf-8")
    lines = src.splitlines()
    mod = importlib.import_module(f"models.{project}.params")
    out = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if not name.isupper():
                continue
            line = lines[node.lineno - 1]
            comment = line.split("#", 1)[1].strip() if "#" in line else ""
            val = getattr(mod, name, None)
            if hasattr(val, "__dataclass_fields__"):
                val = f"{type(val).__name__}({getattr(val, 'name', '')})"
            elif not isinstance(val, (int, float, str, bool, type(None))):
                val = repr(val)
            out.append({"name": name, "value": val, "comment": comment,
                        "derived": not isinstance(node.value, ast.Constant)})
    return out


def components_used(project: str) -> list[dict]:
    pj = ROOT / "parts.json"
    if not pj.exists():
        return []
    idx = json.loads(pj.read_text(encoding="utf-8"))
    prefix = f"models/{project}/"
    out = []
    for cid, c in idx["components"].items():
        if not any(f.startswith(prefix) for f in c["used_by"]):
            continue
        mn = c.get("material_notes") or {}
        out.append({"id": cid, "version": c["version"], "summary": c["summary"], "validated": mn.get("validated", []),
                    "field_validated": mn.get("field_validated", []), "field_failed": mn.get("field_failed", []),
                    "evidence": [{k: e.get(k) for k in ("material", "outcome", "model", "date")} for e in mn.get("evidence", [])]})
    return out


def review_info(project: str) -> dict:
    p = MODELS_DIR / project / "review.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def prints_info(project: str) -> dict:
    """models/<project>/prints.json: print log written by scripts/sync_notes.py from review-page print reports."""
    p = MODELS_DIR / project / "prints.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def write_build_report(project: str, parts: dict, part_metrics: dict, checks: dict, fits: dict, golden_changes: list, threemf: dict | None = None) -> Path:
    import inspect

    mod = load_model(project)
    doc = inspect.getdoc(mod) or ""
    build_id = time.strftime("%Y%m%d-%H%M%S")
    report = {
        "project": project,
        "build_id": build_id,
        "built_at": time.strftime("%Y-%m-%d %H:%M"),
        "docstring": doc,
        "components": components_used(project),
        "params": params_snapshot(project),
        "parts": {name: {"metrics": part_metrics[name].to_dict(), "printability": checks.get(name, {}),
                         "stl": f"models/{project}/exports/{name}.stl", "step": f"models/{project}/exports/{name}.step",
                         "threemf": f"models/{project}/exports/{name}.3mf"}
                  for name in parts},
        "plate": ({"threemf": f"models/{project}/exports/{project}.3mf", "extent": list(threemf["plate_extent"]),
                   "fits_bed": threemf["fits_bed"], "printer": threemf["printer"], "bed": list(threemf["bed"])} if threemf else {}),
        "fit_checks": fits,
        "golden_changes": golden_changes,
        "review": review_info(project),
        "prints": prints_info(project).get("prints", []),
    }
    out = MODELS_DIR / project / "exports" / "build_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Printer profile and 3MF export
# ---------------------------------------------------------------------------

PRINTER = {
    "name": "Snapmaker U1",
    "bed": (270.0, 270.0, 270.0),   # X, Y, Z build volume in mm (Snapmaker U1 spec sheet, ver. 2025.09)
    "nozzle": 0.4,                   # stock hotends; 0.2/0.6/0.8 available
    "toolheads": 4,
    "slicer": "Snapmaker Orca",
}
PLATE_GAP = 10.0  # mm between parts on the plate


def plate_layout(parts: dict, bed_x: float | None = None) -> dict[str, tuple[float, float, float]]:
    """Shelf-pack parts onto the bed: rows along X (wrapping at the bed width minus a margin),
    rows stacked along Y, PLATE_GAP between parts, the whole arrangement centred on the origin,
    every part on z=0.  Returns {name: (dx, dy, dz)} translations."""
    bed_x = (PRINTER["bed"][0] if bed_x is None else bed_x) - 2 * PLATE_GAP
    boxes = sorted(((n, s.bounding_box()) for n, s in parts.items()), key=lambda nb: -nb[1].size.Y)
    rows: list[list] = [[]]
    row_w = 0.0
    for n, b in boxes:
        w = b.size.X
        if rows[-1] and row_w + PLATE_GAP + w > bed_x:
            rows.append([]); row_w = 0.0
        rows[-1].append((n, b)); row_w += (PLATE_GAP if len(rows[-1]) > 1 else 0) + w
    row_h = [max(b.size.Y for _, b in r) for r in rows]
    total_h = sum(row_h) + PLATE_GAP * (len(rows) - 1)
    out = {}
    y = -total_h / 2
    for r, h in zip(rows, row_h):
        total_w = sum(b.size.X for _, b in r) + PLATE_GAP * (len(r) - 1)
        x = -total_w / 2
        for n, b in r:
            out[n] = (x - b.min.X, y + h / 2 - (b.min.Y + b.max.Y) / 2, -b.min.Z)
            x += b.size.X + PLATE_GAP
        y += h + PLATE_GAP
    return out


def export_3mf(project: str, parts: dict, build_id: str = "") -> dict:
    """Write <part>.3mf for each part and <project>.3mf with all parts arranged on the plate.
    Returns {"files": [...], "plate_extent": (x, y, z), "fits_bed": bool}."""
    from build123d import Mesher, Pos

    out_dir = MODELS_DIR / project / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []

    def meta(m: Mesher, title: str):
        m.add_meta_data("", "Title", title, "xs:string", True)
        m.add_meta_data("", "Designer", f"printing/{project} (build123d)", "xs:string", False)
        m.add_meta_data("", "Description", f"build {build_id}; target {PRINTER['name']}", "xs:string", False)

    for name, shape in parts.items():
        m = Mesher()
        m.add_shape(shape, linear_deflection=STL_TOLERANCE, angular_deflection=STL_ANGULAR_TOLERANCE, part_number=name)
        meta(m, f"{project} / {name}")
        p = out_dir / f"{name}.3mf"
        m.write(str(p))
        files.append(p)

    layout = plate_layout(parts)
    placed = {n: Pos(*layout[n]) * s for n, s in parts.items()}
    m = Mesher()
    for name, shape in placed.items():
        m.add_shape(shape, linear_deflection=STL_TOLERANCE, angular_deflection=STL_ANGULAR_TOLERANCE, part_number=name)
    meta(m, f"{project} plate ({len(parts)} parts)")
    plate = out_dir / f"{project}.3mf"
    m.write(str(plate))
    files.append(plate)

    xs = [b for s in placed.values() for b in (s.bounding_box().min.X, s.bounding_box().max.X)]
    ys = [b for s in placed.values() for b in (s.bounding_box().min.Y, s.bounding_box().max.Y)]
    zmax = max(s.bounding_box().max.Z for s in placed.values())
    extent = (round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1), round(zmax, 1))
    fits = all(e <= b for e, b in zip(extent, PRINTER["bed"]))
    return {"files": files, "plate_extent": extent, "fits_bed": fits, "printer": PRINTER["name"], "bed": PRINTER["bed"]}
