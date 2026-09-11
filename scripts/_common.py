"""Shared helpers for the tooling scripts: model discovery, metrics, export.

Model convention
----------------
``models/<project>/model.py`` defines ``build() -> dict[str, Shape]`` mapping a
print-part name to a build123d solid (Part or Compound) in PRINT orientation,
or to a ``trimesh.Trimesh`` for parts that went through the mesh branch
(``lib.form.mesh``: textures, SDF solids).  Mesh parts get STL / 3MF / render /
printability / golden metrics like any other; no STEP is written for them and
their golden volume tolerance is looser.  ``params.py`` beside it holds every
dimension.  Exports land in ``models/<project>/exports/``.

Optionally ``PRINT_MODES = {"<part>": "vase"}`` declares parts that print in
spiral / vase mode (or ``"openwork"`` for a lattice, where the inward-ray wall
metric measures hole rims rather than walls and so stops gating);
the printability check then enforces the single-wall rules
(one contour per layer, no unsupportable overhangs) instead of wall thickness.

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
TESSELLATION_ATTR = "_export_tolerance"   # (tolerance, angular_tolerance) stamped on each part


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
    """Run the model's build() and normalise the result to {name: shape}.

    A model may set ``EXPORT_TOLERANCE`` (and ``EXPORT_ANGULAR_TOLERANCE``) to say how finely its
    B-rep should be tessellated for STL, 3MF, the printability check and the golden.  The default
    0.01 mm is right for a box; it is wrong for a part assembled from a hundred small revolved
    bodies, which arrives an order of magnitude finer than a 0.4 mm nozzle can use and exports a
    70 MB STL.  Everything else keeps the default, so no other model moves.

    The setting is stamped on each part rather than kept in a module global: the test suite builds
    every project up front and tessellates later, so a global belongs to whichever project happened
    to build last and one model's tolerance silently becomes another's.
    """
    mod = load_model(project)
    tess = (getattr(mod, "EXPORT_TOLERANCE", STL_TOLERANCE),
            getattr(mod, "EXPORT_ANGULAR_TOLERANCE", STL_ANGULAR_TOLERANCE))
    result = mod.build()
    if not isinstance(result, dict):
        result = {project: result}
    for shape in result.values():
        try:
            setattr(shape, TESSELLATION_ATTR, tess)
        except AttributeError:      # pragma: no cover - a shape that will not take an attribute
            pass
    return result


def print_modes(project: str) -> dict[str, str]:
    """``PRINT_MODES`` from the model: {part: "vase" | "openwork" | "hinged" | "normal"}; missing = normal."""
    mod = load_model(project)
    modes = getattr(mod, "PRINT_MODES", {}) or {}
    return {k: str(v) for k, v in modes.items()}


def is_mesh(obj) -> bool:
    """True for trimesh.Trimesh parts (the mesh branch), False for build123d shapes."""
    return type(obj).__name__ == "Trimesh"


def bbox_of(shape) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """((xmin, ymin, zmin), (xmax, ymax, zmax)) for a shape or a mesh."""
    if is_mesh(shape):
        lo, hi = shape.bounds
        return (float(lo[0]), float(lo[1]), float(lo[2])), (float(hi[0]), float(hi[1]), float(hi[2]))
    bb = shape.bounding_box()
    return (bb.min.X, bb.min.Y, bb.min.Z), (bb.max.X, bb.max.Y, bb.max.Z)


def translate(shape, dx: float, dy: float, dz: float):
    if is_mesh(shape):
        out = shape.copy()
        out.apply_translation([dx, dy, dz])
        return out
    from build123d import Pos

    return Pos(dx, dy, dz) * shape


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
    kind: str = "brep"   # "brep" (build123d) or "mesh" (trimesh part from lib.form.mesh)

    def to_dict(self) -> dict:
        return asdict(self)


def tessellate(shape, tolerance: float | None = None, angular_tolerance: float | None = None):
    """Return (vertices ndarray (n,3), faces ndarray (m,3)); a mesh part returns its own arrays."""
    import numpy as np

    if is_mesh(shape):
        return np.asarray(shape.vertices, dtype=float), np.asarray(shape.faces, dtype=int)
    stamped = getattr(shape, TESSELLATION_ATTR, (STL_TOLERANCE, STL_ANGULAR_TOLERANCE))
    tol = stamped[0] if tolerance is None else tolerance
    ang = stamped[1] if angular_tolerance is None else angular_tolerance
    verts, tris = shape.tessellate(tol, ang)
    v = np.array([[p.X, p.Y, p.Z] for p in verts], dtype=float)
    f = np.array(tris, dtype=int).reshape(-1, 3)
    return v, f


def to_trimesh(shape):
    import trimesh

    if is_mesh(shape):
        return shape
    v, f = tessellate(shape)
    mesh = trimesh.Trimesh(vertices=v, faces=f, process=True)
    return _without_debris(mesh)


def _without_debris(mesh, max_volume: float = 0.1):
    """Drop closed shells with no volume in them (same threshold as ``lib.component.drop_debris``).

    Tessellating a spot where two curved surfaces meet almost tangentially — a ball set into the
    side of a bored, fluted body of revolution — leaves a handful of triangles collapsed onto a
    point.  It has no volume and cannot print; the only thing it does is report the part as two
    bodies.  Anything a printer could lay down is orders of magnitude above the threshold, so a
    genuinely loose piece still shows up in the build report.
    """
    import numpy as np
    import trimesh

    # label first and only build submeshes if there is more than one: split() materialises every
    # component, and on a 1.5 M triangle part that alone doubled the build time.
    labels = trimesh.graph.connected_component_labels(mesh.face_adjacency, node_count=len(mesh.faces))
    if labels.max() == 0:
        return mesh
    keep = []
    for i in range(labels.max() + 1):
        sub = mesh.submesh([np.where(labels == i)[0]], append=True)
        if abs(sub.volume) >= max_volume:
            keep.append(sub)
    if not keep or len(keep) == labels.max() + 1:
        return mesh
    return trimesh.util.concatenate(keep) if len(keep) > 1 else keep[0]


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
    mesh = to_trimesh(shape)
    if is_mesh(shape):
        lo, hi = bbox_of(shape)
        return Metrics(
            bbox_min=[round(x, 3) for x in lo], bbox_max=[round(x, 3) for x in hi],
            bbox_size=[round(h - l, 3) for l, h in zip(lo, hi)],
            volume=round(float(mesh.volume), 3), surface_area=round(float(mesh.area), 3),
            solids=int(len(mesh.split(only_watertight=False))), valid=bool(mesh.is_watertight and mesh.is_winding_consistent),
            watertight=bool(mesh.is_watertight), mesh_hash=mesh_hash(shape), triangles=int(len(mesh.faces)), kind="mesh",
        )
    bb = shape.bounding_box()
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


def write_stl(shape, path: Path) -> Path:
    """STL for a shape (fixed tessellation) or a mesh part."""
    if is_mesh(shape):
        shape.export(str(path))
    else:
        from build123d import export_stl

        tol, ang = getattr(shape, TESSELLATION_ATTR, (STL_TOLERANCE, STL_ANGULAR_TOLERANCE))
        export_stl(shape, str(path), tolerance=tol, angular_tolerance=ang)
    return path


def export(shape, project: str, name: str) -> tuple[Path, Path | None]:
    """Write <name>.stl and, for B-rep parts, <name>.step (None for mesh parts)."""
    out = MODELS_DIR / project / "exports"
    out.mkdir(parents=True, exist_ok=True)
    stl = write_stl(shape, out / f"{name}.stl")
    if is_mesh(shape):
        return stl, None
    from build123d import export_step

    step = out / f"{name}.step"
    export_step(shape, str(step))
    return stl, step


def golden_path(project: str) -> Path:
    return GOLDEN_DIR / f"{project}.json"


def load_golden(project: str) -> dict | None:
    p = golden_path(project)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def write_golden(project: str, part_metrics: dict[str, Metrics]) -> Path:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    mod = load_model(project)
    data = {
        "project": project,
        "generated": time.strftime("%Y-%m-%d"),
        "tessellation": {"tolerance": getattr(mod, "EXPORT_TOLERANCE", STL_TOLERANCE),
                         "angular_tolerance": getattr(mod, "EXPORT_ANGULAR_TOLERANCE", STL_ANGULAR_TOLERANCE)},
        "parts": {n: m.to_dict() for n, m in part_metrics.items()},
    }
    p = golden_path(project)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p


VOLUME_RTOL = 1e-4
BBOX_ATOL = 1e-3
# mesh parts: the texture is sampled on a platform-dependent tessellation, so volume and bbox wobble slightly
VOLUME_RTOL_MESH = 5e-3
BBOX_ATOL_MESH = 0.05


def diff_golden(golden: dict | None, current: dict[str, Metrics]) -> list[dict]:
    """Compare current metrics to a golden file. Returns a list of change records.

    ``mesh_hash`` is recorded in the golden but deliberately NOT compared. It is exact
    and reproducible on one machine, but OCCT tessellates slightly differently between
    platforms and OCP builds, so a hash mismatch is what you get every time a model is
    rebuilt anywhere other than where its golden was written — noise, not a signal.
    The fields compared here are all platform-independent to their tolerance: volume,
    surface area, bbox size AND position, and watertightness.
    """
    changes: list[dict] = []
    if golden is None:
        return [{"part": n, "field": "golden", "old": None, "new": "missing", "kind": "new"} for n in current]
    gparts = golden.get("parts", {})
    for name, m in current.items():
        g = gparts.get(name)
        if g is None:
            changes.append({"part": name, "field": "part", "old": None, "new": "added", "kind": "added"})
            continue
        meshy = m.kind == "mesh" or g.get("kind") == "mesh"
        v_rtol, b_atol = (VOLUME_RTOL_MESH, BBOX_ATOL_MESH) if meshy else (VOLUME_RTOL, BBOX_ATOL)
        if abs(m.volume - g["volume"]) > v_rtol * max(abs(g["volume"]), 1e-9):
            pct = 100.0 * (m.volume - g["volume"]) / g["volume"] if g["volume"] else float("inf")
            changes.append({"part": name, "field": "volume", "old": g["volume"], "new": m.volume, "kind": "geometry", "delta": f"{pct:+.3f}%"})
        if abs(m.surface_area - g["surface_area"]) > v_rtol * max(abs(g["surface_area"]), 1e-9):
            pct = 100.0 * (m.surface_area - g["surface_area"]) / g["surface_area"] if g["surface_area"] else float("inf")
            changes.append({"part": name, "field": "surface_area", "old": g["surface_area"], "new": m.surface_area, "kind": "geometry", "delta": f"{pct:+.3f}%"})
        for i, ax in enumerate("xyz"):
            if abs(m.bbox_size[i] - g["bbox_size"][i]) > b_atol:
                changes.append({"part": name, "field": f"bbox_{ax}", "old": g["bbox_size"][i], "new": m.bbox_size[i], "kind": "geometry",
                                "delta": f"{m.bbox_size[i] - g['bbox_size'][i]:+.3f} mm"})
        # position, not just size: a part that moved keeps its bbox_size and its volume
        for field, cur, ref in (("bbox_min", m.bbox_min, g["bbox_min"]), ("bbox_max", m.bbox_max, g["bbox_max"])):
            for i, ax in enumerate("xyz"):
                if abs(cur[i] - ref[i]) > b_atol:
                    changes.append({"part": name, "field": f"{field}_{ax}", "old": ref[i], "new": cur[i], "kind": "geometry",
                                    "delta": f"{cur[i] - ref[i]:+.3f} mm"})
        if m.watertight != g["watertight"]:
            changes.append({"part": name, "field": "watertight", "old": g["watertight"], "new": m.watertight, "kind": "integrity"})
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
            if is_mesh(a) or is_mesh(b):
                from lib.form.mesh import mesh_boolean

                inter = mesh_boolean(a, b, "intersection")
                vol = float(inter.volume) if len(inter.faces) else 0.0
            else:
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


def notes_info(project: str) -> dict:
    """models/<project>/notes.json: repo mirror of the review page's notes from the last sync."""
    p = MODELS_DIR / project / "notes.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def prints_info(project: str) -> dict:
    """models/<project>/prints.json: print log written by scripts/sync_notes.py from review-page print reports."""
    p = MODELS_DIR / project / "prints.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def write_build_report(project: str, parts: dict, part_metrics: dict, checks: dict, fits: dict, golden_changes: list, threemf: dict | None = None) -> Path:
    import inspect

    mod = load_model(project)
    doc = inspect.getdoc(mod) or ""
    modes = print_modes(project)
    build_id = time.strftime("%Y%m%d-%H%M%S")
    report = {
        "project": project,
        "build_id": build_id,
        "built_at": time.strftime("%Y-%m-%d %H:%M"),
        "docstring": doc,
        "components": components_used(project),
        "params": params_snapshot(project),
        "parts": {name: {"metrics": part_metrics[name].to_dict(), "printability": checks.get(name, {}),
                         "stl": f"models/{project}/exports/{name}.stl",
                         "step": None if is_mesh(parts[name]) else f"models/{project}/exports/{name}.step",
                         "threemf": f"models/{project}/exports/{name}.3mf", "print_mode": modes.get(name, "normal")}
                  for name in parts},
        "plate": ({"threemf": f"models/{project}/exports/{project}.3mf", "extent": list(threemf["plate_extent"]),
                   "fits_bed": threemf["fits_bed"], "printer": threemf["printer"], "bed": list(threemf["bed"])} if threemf else {}),
        "fit_checks": fits,
        "golden_changes": golden_changes,
        "review": review_info(project),
        "prints": prints_info(project).get("prints", []),
        "notes_synced": notes_info(project).get("synced", ""),
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
    boxes = sorted(((n, bbox_of(s)) for n, s in parts.items()), key=lambda nb: -(nb[1][1][1] - nb[1][0][1]))
    rows: list[list] = [[]]
    row_w = 0.0
    for n, (lo, hi) in boxes:
        w = hi[0] - lo[0]
        if rows[-1] and row_w + PLATE_GAP + w > bed_x:
            rows.append([]); row_w = 0.0
        rows[-1].append((n, (lo, hi))); row_w += (PLATE_GAP if len(rows[-1]) > 1 else 0) + w
    row_h = [max(hi[1] - lo[1] for _, (lo, hi) in r) for r in rows]
    total_h = sum(row_h) + PLATE_GAP * (len(rows) - 1)
    out = {}
    y = -total_h / 2
    for r, h in zip(rows, row_h):
        total_w = sum(hi[0] - lo[0] for _, (lo, hi) in r) + PLATE_GAP * (len(r) - 1)
        x = -total_w / 2
        for n, (lo, hi) in r:
            out[n] = (x - lo[0], y + h / 2 - (lo[1] + hi[1]) / 2, -lo[2])
            x += hi[0] - lo[0] + PLATE_GAP
        y += h + PLATE_GAP
    return out


def export_3mf(project: str, parts: dict, build_id: str = "") -> dict:
    """Write <part>.3mf for each part and <project>.3mf with all parts arranged on the plate.
    Returns {"files": [...], "plate_extent": (x, y, z), "fits_bed": bool}."""
    from build123d import Mesher

    out_dir = MODELS_DIR / project / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    if any(is_mesh(s) for s in parts.values()):
        return _export_3mf_meshes(project, parts, out_dir)

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
    placed = {n: translate(s, *layout[n]) for n, s in parts.items()}
    m = Mesher()
    for name, shape in placed.items():
        m.add_shape(shape, linear_deflection=STL_TOLERANCE, angular_deflection=STL_ANGULAR_TOLERANCE, part_number=name)
    meta(m, f"{project} plate ({len(parts)} parts)")
    plate = out_dir / f"{project}.3mf"
    m.write(str(plate))
    files.append(plate)

    return {"files": files, **_plate_extent(placed)}


def _plate_extent(placed: dict) -> dict:
    boxes = [bbox_of(s) for s in placed.values()]
    xs = [b for lo, hi in boxes for b in (lo[0], hi[0])]
    ys = [b for lo, hi in boxes for b in (lo[1], hi[1])]
    zmax = max(hi[2] for _, hi in boxes)
    extent = (round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1), round(zmax, 1))
    fits = all(e <= b for e, b in zip(extent, PRINTER["bed"]))
    return {"plate_extent": extent, "fits_bed": fits, "printer": PRINTER["name"], "bed": PRINTER["bed"]}


def _export_3mf_meshes(project: str, parts: dict, out_dir: Path) -> dict:
    """3MF via trimesh when any part is a mesh (build123d's Mesher only takes shapes)."""
    import trimesh

    files = []
    meshes = {n: to_trimesh(s) for n, s in parts.items()}
    for name, m in meshes.items():
        p = out_dir / f"{name}.3mf"
        scene = trimesh.Scene()
        scene.add_geometry(m, node_name=name, geom_name=name)
        scene.export(str(p))
        files.append(p)
    layout = plate_layout(parts)
    placed = {n: translate(m, *layout[n]) for n, m in meshes.items()}
    scene = trimesh.Scene()
    for name, m in placed.items():
        scene.add_geometry(m, node_name=name, geom_name=name)
    plate = out_dir / f"{project}.3mf"
    scene.export(str(plate))
    files.append(plate)
    return {"files": files, **_plate_extent(placed)}
