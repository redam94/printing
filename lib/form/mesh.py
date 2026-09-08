"""The mesh branch: things the B-rep kernel cannot do, done on triangle meshes with manifold3d.

* ``to_mesh(shape)`` tessellates any build123d shape into a watertight ``trimesh.Trimesh``.
* ``textured(shape, ...)`` displaces the surface with Perlin noise or ripples (masked so bed faces,
  cavities and bosses stay exact) and returns a mesh.
* ``sdf_solid(f, bounds, edge)`` meshes a signed-distance function (gyroids, metaballs, ...).
* ``mesh_boolean(a, b, op)`` unions / subtracts / intersects meshes or shapes with manifold3d.

A model whose ``build()`` returns a mesh for a part gets STL / 3MF / renders / printability / golden
metrics like any other part; STEP is not written for mesh parts and golden volume tolerance is
looser (tessellation seeds the texture).  Do the mesh step LAST: build123d cannot take a mesh back.
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np

from lib.component import MaterialNotes, component

MESH_TOLERANCE = 0.01
MESH_ANGULAR_TOLERANCE = 0.1

_NOTES = MaterialNotes(validated=[], orientation="as the source shape; bed face is never displaced",
                       notes="UNVALIDATED: texture amplitude <= 0.4 mm prints cleanly with 0.4 mm nozzle; larger needs slower outer walls")


def is_mesh(obj) -> bool:
    return type(obj).__name__ == "Trimesh"


def to_mesh(shape, tolerance: float = MESH_TOLERANCE, angular_tolerance: float = MESH_ANGULAR_TOLERANCE):
    """Tessellate a build123d shape (or pass a mesh through) as a processed, watertight trimesh."""
    import trimesh

    if is_mesh(shape):
        return shape
    verts, tris = shape.tessellate(tolerance, angular_tolerance)
    v = np.array([[p.X, p.Y, p.Z] for p in verts], dtype=float)
    f = np.array(tris, dtype=np.int64).reshape(-1, 3)
    m = trimesh.Trimesh(vertices=v, faces=f, process=True)
    if not m.is_watertight:
        trimesh.repair.fill_holes(m)
        m.merge_vertices()
    if not m.is_winding_consistent:
        trimesh.repair.fix_normals(m)
    return m


def _manifold(mesh):
    from manifold3d import Manifold, Mesh

    mm = Mesh(vert_properties=np.ascontiguousarray(mesh.vertices, dtype=np.float32),
              tri_verts=np.ascontiguousarray(mesh.faces, dtype=np.uint32))
    mm.merge()   # OCC tessellations leave a few near-duplicate vertices along face seams
    m = Manifold(mm)
    if m.is_empty():
        raise ValueError(f"mesh is not manifold ({m.status()}): repair the tessellation before mesh operations")
    return m


def _from_manifold(m):
    import trimesh

    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts), process=False)


def mesh_boolean(a, b, op: str = "difference"):
    """Robust mesh boolean via manifold3d.  ``a``/``b`` may be shapes or meshes.  op: union, difference, intersection."""
    ma, mb = _manifold(to_mesh(a)), _manifold(to_mesh(b))
    if op == "union":
        r = ma + mb
    elif op == "difference":
        r = ma - mb
    elif op == "intersection":
        r = ma ^ mb
    else:
        raise ValueError("op must be union, difference or intersection")
    return _from_manifold(r)


# ---------------------------------------------------------------------------
# Perlin noise (numpy, deterministic per seed)
# ---------------------------------------------------------------------------

def _perlin3(p: np.ndarray, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(256)
    perm = np.concatenate([perm, perm])
    grads = np.array([[1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0], [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
                      [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1]], dtype=float)
    pi = np.floor(p).astype(int)
    pf = p - pi
    pi &= 255

    def fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    u, v, w = fade(pf[:, 0]), fade(pf[:, 1]), fade(pf[:, 2])
    total = np.zeros(len(p))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = perm[perm[perm[pi[:, 0] + dx] + pi[:, 1] + dy] + pi[:, 2] + dz] % 12
                g = grads[h]
                d = pf - np.array([dx, dy, dz])
                dot = (g * d).sum(axis=1)
                wx = u if dx else 1 - u
                wy = v if dy else 1 - v
                wz = w if dz else 1 - w
                total += dot * wx * wy * wz
    return total


def noise(p: np.ndarray, scale: float = 8.0, octaves: int = 2, seed: int = 0) -> np.ndarray:
    """Fractal Perlin noise in roughly [-1, 1] at points ``p`` (n, 3); ``scale`` = feature size in mm."""
    out = np.zeros(len(p))
    amp, freq, norm = 1.0, 1.0 / scale, 0.0
    for o in range(octaves):
        out += amp * _perlin3(p * freq + 17.3 * o, seed + o)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return out / norm * 1.6


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def _default_shape():
    from lib.form.revolved import revolved_body, shell_open_top

    return shell_open_top(revolved_body(), wall=1.6)


def exterior_mask(mesh, normals: np.ndarray, probe: float = 0.05) -> np.ndarray:
    """True for vertices whose outward normal ray escapes the part (outer skin), False inside cavities."""
    origins = mesh.vertices + normals * probe
    hits = mesh.ray.intersects_any(origins, normals)
    return ~hits


@component(
    id="form.textured", version="1.0.0",
    summary="Displace a shape's outer surface with Perlin noise or horizontal ripples and return a mesh (organic skin, hammered / wavy look).",
    tags=["texture", "noise", "perlin", "ripple", "displacement", "mesh", "organic", "skin", "form"],
    units={"shape": "-", "amplitude": "mm", "scale": "mm", "kind": "enum", "mask": "enum", "seed": "count",
           "edge_length": "mm", "bed_margin": "mm", "octaves": "count"},
    descriptions={
        "shape": "Part or mesh to texture; None = default hollow revolved_body", "amplitude": "peak displacement along the normal",
        "scale": "feature size (noise wavelength / ripple pitch)", "kind": "noise | ripple",
        "mask": "exterior (outer skin only, cavities and bosses untouched) | sides (|normal z| < 0.5) | all",
        "seed": "noise seed", "edge_length": "mesh refinement before displacing (smaller = finer texture, more triangles)",
        "bed_margin": "height above the bed left undisplaced (elephant-foot chamfer zone)", "octaves": "noise detail levels",
    },
    material_notes=_NOTES,
)
def textured(shape=None, amplitude: float = 0.4, scale: float = 8.0, kind: str = "noise", mask: str = "exterior",
             seed: int = 0, edge_length: float = 1.0, bed_margin: float = 0.6, octaves: int = 2) -> "Trimesh":
    """Refines the mesh to ``edge_length`` with manifold3d, then warps vertices along their normals
    (horizontally only, unless ``mask="all"``, so no height changes).  The bed face and everything
    below ``bed_margin`` stay put; ``exterior`` mask also keeps inner walls, bosses and holes exact so
    fits are unchanged.  Returns a ``trimesh.Trimesh``; put it last in build().

    Example:
        tray = textured(tray_part, amplitude=0.35, scale=6, mask="exterior")
    """
    src = _default_shape() if shape is None else shape
    base = to_mesh(src)
    m = _manifold(base).refine_to_length(edge_length)
    mesh = _from_manifold(m)
    mesh.merge_vertices()
    n = mesh.vertex_normals
    v = mesh.vertices
    z_min = float(v[:, 2].min())
    if kind == "noise":
        d = noise(v, scale=scale, octaves=octaves, seed=seed)
    elif kind == "ripple":
        d = np.sin(2 * np.pi * (v[:, 2] - z_min) / scale)
    else:
        raise ValueError("kind must be 'noise' or 'ripple'")
    keep = np.ones(len(v), dtype=bool)
    if mask == "exterior":
        keep &= exterior_mask(mesh, n)
        keep &= np.abs(n[:, 2]) < 0.85   # top rims / floors of the outer skin stay flat
    elif mask == "sides":
        keep &= np.abs(n[:, 2]) < 0.5
    elif mask != "all":
        raise ValueError("mask must be 'exterior', 'sides' or 'all'")
    ramp = np.clip((v[:, 2] - z_min - bed_margin) / max(bed_margin, 1e-6), 0.0, 1.0)
    disp = amplitude * d * keep * ramp
    if mask == "all":
        direction = n
    else:
        # displace horizontally only: every z level (rim tops, boss tops, floor) stays exactly where the
        # B-rep put it, so fit checks and assembly heights are unchanged; skip near-horizontal normals
        direction = n * np.array([1.0, 1.0, 0.0])
        horiz = np.linalg.norm(direction, axis=1)
        ok = horiz > 0.3
        direction[ok] /= horiz[ok][:, None]
        disp[~ok] = 0.0
    new_v = v + direction * disp[:, None]
    new_v[:, 2] = np.maximum(new_v[:, 2], z_min)
    out = mesh.copy()
    out.vertices = new_v
    out.fix_normals()
    return out


def gyroid_sdf(cell: float = 10.0, thickness: float = 1.2) -> Callable[[float, float, float], float]:
    """Positive-inside SDF of a gyroid sheet: |sin x cos y + sin y cos z + sin z cos x| < t."""
    from math import cos, pi, sin

    k = 2 * pi / cell
    t = thickness * k / 2 * 1.3   # approx conversion of half-thickness to gyroid level units

    def f(x, y, z):
        g = sin(k * x) * cos(k * y) + sin(k * y) * cos(k * z) + sin(k * z) * cos(k * x)
        return t - abs(g)
    return f


@component(
    id="form.sdf_solid", version="1.0.0",
    summary="Mesh a signed-distance function (positive inside) over a box with manifold3d level_set; default is a gyroid block.",
    tags=["sdf", "implicit", "gyroid", "lattice", "metaball", "marching", "mesh", "form"],
    units={"sdf": "-", "bounds": "mm", "edge_length": "mm"},
    descriptions={"sdf": "callable f(x, y, z) -> float, positive inside; None = gyroid_sdf()",
                  "bounds": "(xmin, ymin, zmin, xmax, ymax, zmax) of the evaluation box; the solid is clipped to it",
                  "edge_length": "target triangle edge (resolution); 0.5-1.0 mm is plenty for FDM"},
    material_notes=MaterialNotes(validated=[], orientation="any; check overhangs, gyroids self-support up to ~cell 15 mm",
                                 notes="UNVALIDATED"),
)
def sdf_solid(sdf: Callable[[float, float, float], float] | None = None,
              bounds: tuple[float, float, float, float, float, float] = (-15.0, -15.0, 0.0, 15.0, 15.0, 30.0),
              edge_length: float = 0.8) -> "Trimesh":
    """Example:
        block = sdf_solid(gyroid_sdf(cell=12, thickness=1.2), bounds=(-20, -20, 0, 20, 20, 40))
        lamp = mesh_boolean(block, cylinder_shape, "intersection")
    """
    from manifold3d import Manifold

    f = gyroid_sdf() if sdf is None else sdf
    m = Manifold.level_set(f, list(bounds), edge_length)
    if m.is_empty():
        raise ValueError("level set is empty: check the sign convention (positive inside) and bounds")
    return _from_manifold(m)
