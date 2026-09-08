"""Solid blob forms: clusters of domes (the 3D sibling of lib.form.outline.blob_outline)."""
from __future__ import annotations

from math import acos, cos, pi, sin
from typing import Sequence

from build123d import Axis, Line, Part, Plane, Pos, Spline, make_face, revolve

from lib.component import MaterialNotes, component

_QUARTER_SAMPLES = 9    # points along the quarter-ellipse profile; 9 is visually exact at this scale
APEX_FLAT = 0.4         # mm, radius of the tiny flat the profile stops at instead of closing to a
                        #     point: a revolved apex tessellates into one loose degenerate triangle,
                        #     which reads downstream as a non-watertight part with two bodies

_DEFAULT_DOMES = ((0.0, 0.0, 12.0), (13.0, 0.0, 10.0), (24.0, -2.0, 8.0), (32.0, -6.0, 6.0))


def dome(r: float = 10.0, height: float | None = None, apex_flat: float = APEX_FLAT) -> Part:
    """One dome (upper half-ellipsoid) of radius ``r`` standing on z=0, apex at ``height``.

    Revolved from a quarter-ellipse rather than trimmed off a ``Sphere``: an OCC sphere tessellates
    into a non-watertight mesh at its poles and seam, and so does any surface of revolution that
    closes to a point, so the profile stops at ``apex_flat`` and takes a tiny flat top instead.  At
    0.4 mm that is invisible on a 10 mm dome and it also gives the slicer a real top layer rather
    than a knife edge.  The profile leaves the base vertical, so there is no overhang at the rim
    however the dome is squashed.
    """
    h = r if height is None else height
    t_max = acos(min(apex_flat / r, 1.0)) if apex_flat > 0 else pi / 2
    pts = [(r * cos(t_max * i / (_QUARTER_SAMPLES - 1)), h * sin(t_max * i / (_QUARTER_SAMPLES - 1)))
           for i in range(_QUARTER_SAMPLES)]
    outer = Spline(*pts, tangents=[(0, 1), (-1, 0)])
    top = Line(pts[-1], (0.0, pts[-1][1]))
    face = Plane.XZ * make_face(outer + top + Line((0.0, pts[-1][1]), (0.0, 0.0)) + Line((0.0, 0.0), pts[0]))
    return revolve(face, Axis.Z)


@component(
    id="form.dome_cluster", version="1.0.0",
    summary="Union of dome blobs (upper half-ellipsoids) at given (x, y, r), flat faces on a common plane: caterpillar and creature bodies, pebbles, cloud lobes, bumpy grips.",
    tags=["blob", "bumps", "caterpillar", "creature", "dome", "form", "organic", "pebble", "segments", "toy"],
    units={"domes": "mm", "squash": "ratio", "base_z": "mm"},
    descriptions={
        "domes": "sequence of (x, y, r); neighbours must overlap to make one solid",
        "squash": "Z scale per dome: 1.0 = hemisphere, >1 = taller egg, <1 = flat pebble",
        "base_z": "plane the flat faces sit on; pass a value below a ground surface to half-bury them",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="flat faces down on the bed (or on the body that carries them): an upper half-ellipsoid has no down-facing surface at all, so any squash >= 1 needs no support",
        notes="UNVALIDATED. squash < 1 flattens the dome and starts to add a shallow overhang near the rim; "
              "keep it above ~0.7 unless the cluster is supported. Domes that only touch become separate solids — overlap them.",
    ),
)
def dome_cluster(domes: Sequence[tuple[float, float, float]] = _DEFAULT_DOMES,
                 squash: float = 1.0, base_z: float = 0.0) -> Part:
    """Overlapping domes as one solid, the way ``blob_outline`` overlaps circles in 2D.

    A dome of radius ``r`` rises ``r * squash`` above ``base_z``.  Sink the cluster into whatever
    carries it (``base_z`` a few mm below the ground surface) rather than resting it on top: a blob
    that merely shares a face with the plate under it fuses into a separate loose solid.

    Example:
        body = ground + dome_cluster(((0, 0, 12), (13, 1, 10), (23, -4, 8)), squash=1.4, base_z=-3)
    """
    out = Part()
    for x, y, r in domes:
        out += Pos(x, y, base_z) * dome(r, r * squash)
    return out
