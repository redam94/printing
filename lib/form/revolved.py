"""Bodies of revolution: spline profiles, open-top shells, planter drainage.

Coordinate convention: the axis of revolution is Z, the base sits on z=0, profiles are given as
``(radius, z)`` pairs walking from the base rim up to the top rim.  The profile is closed along the
axis automatically, so every body here is a solid; ``shell_open_top`` hollows it.
"""
from __future__ import annotations

from collections.abc import Sequence

from build123d import Axis, Circle, Line, Part, Plane, Polyline, Pos, Sketch, Spline, make_face, offset, revolve

from lib.component import MaterialNotes, component

VASE_PROFILE: tuple[tuple[float, float], ...] = ((25.0, 0.0), (26.0, 40.0), (28.0, 70.0), (40.0, 95.0), (38.0, 112.0), (30.0, 120.0))

_FORM_NOTES = MaterialNotes(validated=[], orientation="axis vertical, base on the bed",
                            notes="UNVALIDATED: no test print yet; designed for spiral (vase) mode or 2-4 perimeters")


def profile_face(profile: Sequence[tuple[float, float]], smooth: bool = True, tangents: Sequence[tuple[float, float]] | None = None):
    """Closed XZ face bounded by the (r, z) profile and the Z axis, ready to revolve."""
    pts = [(float(r), float(z)) for r, z in profile]
    if len(pts) < 2:
        raise ValueError("profile needs at least two (r, z) points")
    if pts[0][1] != 0.0:
        raise ValueError("profile must start on the base (z = 0)")
    if smooth and len(pts) >= 3:
        outer = Spline(*pts, tangents=list(tangents) if tangents else None)
    else:
        outer = Polyline(*pts)
    top = Line(pts[-1], (0.0, pts[-1][1]))
    axis = Line((0.0, pts[-1][1]), (0.0, 0.0))
    base = Line((0.0, 0.0), pts[0])
    return Plane.XZ * make_face(outer + top + axis + base)


@component(
    id="form.revolved_body", version="1.0.0",
    summary="Solid of revolution about Z from an (r, z) profile, spline-smoothed by default, base on z=0 (vases, planters, lamps, knobs).",
    tags=["vase", "revolve", "spline", "organic", "profile", "lathe", "planter", "lamp", "bowl", "form"],
    units={"profile": "mm", "smooth": "bool", "tangents": "-"},
    descriptions={
        "profile": "sequence of (radius, z) points from the base rim (z=0) to the top rim; closed along the axis",
        "smooth": "True: one spline through the points; False: straight segments (facetted / stepped profiles)",
        "tangents": "optional start and end tangent directions for the spline, e.g. ((0, 1), (-1, 1)); None = natural",
    },
    material_notes=_FORM_NOTES,
)
def revolved_body(profile: Sequence[tuple[float, float]] = VASE_PROFILE, smooth: bool = True,
                  tangents: Sequence[tuple[float, float]] | None = None) -> Part:
    """The profile's last point is the top rim radius; the top is closed flat.  ``shell_open_top``
    hollows it; ``flutes`` (with this solid as ``reference``) ribs the shell.

    Example:
        solid = revolved_body(((30, 0), (34, 30), (26, 80), (30, 100)))
        vase = flutes(shell_open_top(solid, wall=2.0), count=20, reference=solid)
    """
    return revolve(profile_face(profile, smooth, tangents), Axis.Z)


@component(
    id="form.shell_open_top", version="1.0.0",
    summary="Hollow a solid into an open-top shell of uniform wall (floor included); default hollows the default revolved_body.",
    tags=["shell", "hollow", "vase", "wall", "open top", "cup", "planter", "form"],
    units={"shape": "-", "wall": "mm"},
    descriptions={"shape": "solid to hollow (Part); None = revolved_body() default", "wall": "wall and floor thickness (multiple of 0.4)"},
    material_notes=_FORM_NOTES,
)
def shell_open_top(shape: Part | None = None, wall: float = 1.6) -> Part:
    """The highest planar face becomes the opening; uniform inward offset (wall = floor).  Shell the
    smooth solid, then add flutes / textures: offsetting an already-fluted body is slow and fragile.

    Example:
        vase = shell_open_top(revolved_body(profile), wall=1.2)
    """
    shape = revolved_body() if shape is None else shape
    top = shape.faces().sort_by(Axis.Z)[-1]
    return offset(shape, amount=-wall, openings=top)


@component(
    id="form.drain_holes", version="1.0.0",
    summary="Planter drainage: one centre hole plus a ring of holes, as a sketch to subtract from a floor.",
    tags=["planter", "drain", "drainage", "holes", "pot", "floor", "pattern", "form"],
    units={"ring_r": "mm", "hole_d": "mm", "count": "count", "centre": "bool"},
    descriptions={"ring_r": "radius of the hole ring", "hole_d": "hole diameter", "count": "holes on the ring",
                  "centre": "also cut a centre hole"},
    material_notes=MaterialNotes(validated=[], orientation="any (2D pattern)", notes="UNVALIDATED"),
)
def drain_holes(ring_r: float = 15.0, hole_d: float = 6.0, count: int = 6, centre: bool = True) -> Sketch:
    """Example:
        planter = planter - extrude(drain_holes(ring_r=inner_r * 0.55), amount=floor_t)
    """
    from math import cos, radians, sin

    holes = [Pos(ring_r * cos(radians(360 * i / count)), ring_r * sin(radians(360 * i / count))) * Circle(hole_d / 2)
             for i in range(max(count, 0))]
    if centre:
        holes.append(Circle(hole_d / 2))
    return Sketch() + holes
