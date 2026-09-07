"""Shared helpers for the tooling scripts: model discovery, metrics, export.

Model convention
----------------
``models/<project>/model.py`` defines ``build() -> dict[str, Shape]`` mapping a
print-part name to a build123d solid (Part or Compound).  ``params.py`` beside
it holds every dimension.  Exports land in ``models/<project>/exports/``.
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
    return json.loads(p.read_text()) if p.exists() else None


def write_golden(project: str, part_metrics: dict[str, Metrics]) -> Path:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "project": project,
        "generated": time.strftime("%Y-%m-%d"),
        "tessellation": {"tolerance": STL_TOLERANCE, "angular_tolerance": STL_ANGULAR_TOLERANCE},
        "parts": {n: m.to_dict() for n, m in part_metrics.items()},
    }
    p = golden_path(project)
    p.write_text(json.dumps(data, indent=2) + "\n")
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
