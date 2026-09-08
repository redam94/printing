"""Solid blob forms: clusters of domes (the 3D sibling of lib.form.outline.blob_outline)."""
from __future__ import annotations

from math import acos, cos, pi, sin
from typing import Sequence

from build123d import Axis, Line, Part, Plane, Polyline, Pos, Rot, Spline, Vector, make_face, revolve

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


_DEFAULT_BALLS = ((0.0, 0.0, 10.0, 10.0), (0.0, -6.0, 20.0, 8.5), (0.0, -10.0, 29.0, 7.0))


_DEFAULT_PATH = ((0.0, 0.0), (18.0, -8.0), (34.0, -4.0), (44.0, 8.0))
_PATH_SAMPLES = 240     # points along the spline before it is re-sampled at equal arc length


_DEFAULT_RAYS = (((0.0, 0.0, 40.0), (0.0, 0.0, -1.0)),
                 ((14.0, 0.0, 40.0), (0.0, 0.0, -1.0)))


@component(
    id="form.surface_studs", version="1.0.0",
    summary="Domes seated where each ray first meets a body's surface, aligned with the local normal: toadstool spots, caterpillar tubercles, eyes, rivets, grip bumps.",
    tags=["blob", "bumps", "dots", "form", "organic", "rivets", "spots", "studs", "surface", "texture"],
    units={"shape": "-", "rays": "mm", "radius": "mm", "height": "mm", "embed": "mm"},
    descriptions={
        "shape": "body to seat the studs on (Part); None = dome_cluster() default",
        "rays": "sequence of (origin, direction); the origin must be OUTSIDE the body and the stud lands on the first surface the ray meets",
        "radius": "stud radius (or a sequence, one per ray)",
        "height": "stud height above the surface; None = radius, i.e. a hemisphere",
        "embed": "how far the stud's flat base is sunk below the surface; it must exceed the surface's sag across the stud (about radius^2 / 2 / local_radius) or the stud only touches at a point and fuses into a loose solid",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="a stud on a down-facing surface is an unsupported overhang; keep them on upward and sideways faces",
        notes="UNVALIDATED. A ray that misses the body is skipped silently, so check the stud count "
              "against the ray count when a spot goes missing.",
    ),
)
def surface_studs(shape: Part | None = None,
                  rays: Sequence[tuple[tuple[float, float, float], tuple[float, float, float]]] = _DEFAULT_RAYS,
                  radius: float | Sequence[float] = 2.0, height: float | None = None,
                  embed: float = 0.6) -> Part:
    """Studs on any surface, found by ray casting rather than by solving the surface analytically.

    The point of casting instead of computing is that the same call decorates a body of revolution,
    a dome cluster or a boxy part: aim a ray at the feature and the stud lands flat on whatever is
    there, tilted with the surface.  Sink each one (``embed``) — a flat-based dome resting on a
    convex surface touches it at exactly one point, and one point is not a union.

    Example:
        cap = revolved_body(profile)
        spots = surface_studs(cap, [((x, y, 60), (0, 0, -1)) for x, y in dots], radius=2.4)
    """
    body = dome_cluster() if shape is None else shape
    radii = [radius] * len(rays) if isinstance(radius, (int, float)) else list(radius)
    out = Part()
    for (origin, direction), r in zip(rays, radii):
        hits = body.find_intersection_points(Axis(origin, direction))
        if not hits:
            continue
        near = min(hits, key=lambda h: (h[0] - Vector(origin)).length)
        point, normal = near[0], near[1]
        if normal.dot(Vector(direction)) > 0:
            normal = -normal
        seat = point - normal * embed
        out += Plane(origin=seat, z_dir=normal) * dome(r, r if height is None else height)
    return out


@component(
    id="form.dome_chain", version="1.0.0",
    summary="Chain of overlapping domes stepped along a spline path at equal spacing, tapering head to tail: caterpillars, snakes, larvae, vines, bunting.",
    tags=["blob", "caterpillar", "chain", "creature", "dome", "form", "organic", "path", "segments", "snake", "taper", "toy"],
    units={"path": "mm", "count": "count", "r_head": "mm", "r_tail": "mm", "squash": "ratio",
           "base_z": "mm", "smooth": "bool"},
    descriptions={
        "path": "sequence of (x, y) control points the body follows, head first; the chain starts on the first and ends on the last",
        "count": "number of segments",
        "r_head": "radius of the first segment",
        "r_tail": "radius of the last segment",
        "squash": "Z scale per dome: 1.0 = hemisphere, >1 = a taller, rounder body",
        "base_z": "plane the flat faces sit on",
        "smooth": "True: a spline through the control points; False: straight runs between them",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="flat faces down: an upper half-ellipsoid has no down-facing surface, so any squash >= 1 needs no support",
        notes="UNVALIDATED. Neighbours only fuse where they OVERLAP, and the spacing is the path "
              "length over count-1: a long path with few segments gives a row of separate beads. "
              "Rule of thumb, keep count above path_length / r_tail.",
    ),
)
def dome_chain(path: Sequence[tuple[float, float]] = _DEFAULT_PATH, count: int = 8,
               r_head: float = 12.0, r_tail: float = 5.0, squash: float = 1.0,
               base_z: float = 0.0, smooth: bool = True) -> Part:
    """A body that follows a line instead of a list of coordinates.

    Stepping at equal ARC length is the point: sampling a spline by its own parameter bunches the
    segments up on the straight runs and stretches them thin round the corners, which on a creature
    reads immediately as a mistake.  Radii interpolate head to tail over the same steps.

    Example:
        body = dome_chain(((0, 0), (20, -12), (44, -6)), count=9, r_head=11, r_tail=4, squash=1.5)
    """
    return dome_cluster(chain_centres(path, count, r_head, r_tail, smooth), squash=squash, base_z=base_z)


def chain_centres(path: Sequence[tuple[float, float]], count: int, r_head: float, r_tail: float,
                  smooth: bool = True) -> tuple[tuple[float, float, float], ...]:
    """The (x, y, r) the chain's domes land on: equal arc-length steps along the path."""
    pts = [(float(x), float(y), 0.0) for x, y in path]
    curve = Spline(*pts) if smooth and len(pts) > 2 else Polyline(*pts)
    samples = [curve @ (i / (_PATH_SAMPLES - 1)) for i in range(_PATH_SAMPLES)]
    run = [0.0]
    for a, b in zip(samples, samples[1:]):
        run.append(run[-1] + (b - a).length)
    out = []
    for i in range(count):
        target = run[-1] * (i / (count - 1) if count > 1 else 0.0)
        j = min(range(len(run)), key=lambda k: abs(run[k] - target))
        t = i / (count - 1) if count > 1 else 0.0
        out.append((samples[j].X, samples[j].Y, r_head + (r_tail - r_head) * t))
    return tuple(out)


def ball(r: float = 10.0, height: float | None = None, apex_flat: float = APEX_FLAT) -> Part:
    """A full ellipsoid, built as two ``dome``s back to back rather than as a ``Sphere``.

    Same reason ``dome`` exists: an OCC sphere tessellates into a non-watertight mesh at its poles
    and its seam, and a body made of thirty of them is thirty chances to lose watertightness.
    """
    h = r if height is None else height
    half = dome(r, h, apex_flat)
    return half + Rot(180, 0, 0) * half


@component(
    id="form.ball_chain", version="1.0.0",
    summary="Chain of overlapping ellipsoids at given (x, y, z, r): the part of a creature that leaves the ground — a reared neck, a tentacle, a raised tail — which a dome_chain cannot do.",
    tags=["blob", "chain", "creature", "ellipsoid", "form", "neck", "organic", "reared", "segments", "tentacle", "toy"],
    units={"balls": "mm", "squash": "ratio"},
    descriptions={
        "balls": "sequence of (x, y, z, r); neighbours must overlap to make one solid",
        "squash": "Z scale per ball: 1.0 = a sphere, >1 = a taller egg",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="a ball floating free is a 90 deg overhang all round its underside: every ball "
                    "must sit ON something — the one below it, or a body it is half sunk into — and "
                    "a rearing chain must lean IN as it rises, never out",
        notes="UNVALIDATED. This is the one blob primitive that can print unsupported nonsense, so "
              "check the overhang number after using it, not just the fit.",
    ),
)
def ball_chain(balls: Sequence[tuple[float, float, float, float]] = _DEFAULT_BALLS,
               squash: float = 1.0) -> Part:
    """Overlapping ellipsoids in 3D, the way ``dome_cluster`` overlaps half-ellipsoids in a plane.

    Example:
        neck = ball_chain(((0, 0, 10, 10), (0, -6, 20, 8.5), (0, -10, 29, 7)), squash=1.1)
    """
    out = Part()
    for x, y, z, r in balls:
        out += Pos(x, y, z) * ball(r, r * squash)
    return out
