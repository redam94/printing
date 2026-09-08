"""Surface treatments and sections: flutes / ribs on any body, twisted extrusions, wavy circles."""
from __future__ import annotations

from math import cos, pi, radians, sin

from build123d import Align, Axis, Box, GeomType, Part, Pos, Rectangle, Rot, Sketch, Solid, Spline, make_face, offset

from lib.component import MaterialNotes, component

_NOTES = MaterialNotes(validated=[], orientation="axis vertical, base on the bed",
                       notes="UNVALIDATED: no test print yet; keep flute depth <= wall - 0.8 unless shelled afterwards")


@component(
    id="form.wavy_circle", version="1.0.0",
    summary="Circle with a sinusoidal radius (lobed / scalloped section) as a sketch, for twisted vases and lamp shades.",
    tags=["wave", "lobes", "scallop", "section", "spiral vase", "sketch", "petal", "form"],
    units={"radius": "mm", "amplitude": "mm", "lobes": "count", "phase": "deg", "samples_per_lobe": "count"},
    descriptions={"radius": "mean radius", "amplitude": "radial wave amplitude (peak = radius + amplitude)",
                  "lobes": "number of waves around the circumference", "phase": "rotates the pattern",
                  "samples_per_lobe": "spline control points per wave (>= 6 keeps the curve faithful)"},
    material_notes=MaterialNotes(validated=[], orientation="any (2D section)", notes="UNVALIDATED"),
)
def wavy_circle(radius: float = 30.0, amplitude: float = 3.0, lobes: int = 8, phase: float = 0.0,
                samples_per_lobe: int = 8) -> Sketch:
    """Periodic spline through ``lobes * samples_per_lobe`` points of r(t) = radius + amplitude sin(lobes t).

    Example:
        vase = twist(wavy_circle(35, 4, 10), height=150, angle=120)
    """
    n = max(3, lobes * samples_per_lobe)
    ph = radians(phase)
    pts = []
    for i in range(n):
        t = 2 * pi * i / n
        r = radius + amplitude * sin(lobes * t + ph)
        pts.append((r * cos(t), r * sin(t)))
    return Sketch() + make_face(Spline(*pts, periodic=True))


@component(
    id="form.twist", version="1.0.0",
    summary="Extrude a section along Z while rotating it (spiral / twisted vase body), base on z=0.",
    tags=["twist", "spiral", "helix", "extrude", "vase", "column", "form"],
    units={"section": "-", "height": "mm", "angle": "deg", "taper": "ratio"},
    descriptions={"section": "sketch to extrude (one or more faces); None = wavy_circle()", "height": "extrusion height",
                  "angle": "total rotation over the height (sign = handedness)",
                  "taper": "top scale relative to the base (1.0 = straight; 0.8 = narrows to 80 %)"},
    material_notes=MaterialNotes(validated=[], orientation="axis vertical, base on the bed",
                                 notes="UNVALIDATED; keep the surface slope (angle * radius / height) under ~50 deg from vertical"),
)
def twist(section: Sketch | None = None, height: float = 100.0, angle: float = 90.0, taper: float = 1.0) -> Part:
    """Twist about the Z axis through the sketch origin.  ``taper`` != 1 is done by lofting rotated,
    scaled copies of the section (slower, still exact enough at 2 deg per step).

    Example:
        body = twist(wavy_circle(30, 3, 8), height=120, angle=90)
        vase = shell_open_top(body, wall=1.2)
    """
    from build123d import Plane, loft

    section = wavy_circle() if section is None else section
    faces = section.faces()
    if taper == 1.0:
        solids = [Solid.extrude_linear_with_rotation(f, (0, 0, 0), (0, 0, height), angle) for f in faces]
        return Part() + solids
    steps = max(4, int(abs(angle) / 2))
    parts = []
    for f in faces:
        sections = []
        for i in range(steps + 1):
            u = i / steps
            s = 1 + (taper - 1) * u
            sk = Plane.XY.offset(height * u) * Rot(0, 0, angle * u) * (Sketch() + f).scale(s)
            sections.append(sk)
        parts.append(loft(sections, ruled=False))
    return Part() + parts


@component(
    id="form.flutes", version="1.0.0",
    summary="Cut vertical flutes into (or raise ribs on) the outer surface of any body, following its profile; polar array about Z.",
    tags=["flutes", "ribs", "fluting", "ridges", "grooves", "vase", "texture", "polar", "form"],
    units={"shape": "-", "count": "count", "width": "mm", "depth": "mm", "z_from": "mm", "z_to": "mm",
           "twist_angle": "deg", "raised": "bool", "reference": "-"},
    descriptions={
        "shape": "body to flute (Part); None = revolved_body() default",
        "count": "number of flutes around Z", "width": "flute width (tangential)", "depth": "cut depth into the surface (or rib height when raised)",
        "z_from": "flutes start height", "z_to": "flutes end height; None = full height",
        "twist_angle": "rotation of the flutes over their height (0 = straight)",
        "raised": "True: add ribs standing proud of the surface instead of cutting grooves",
        "reference": "optional solid used to derive the surface band (pass the un-shelled solid when fluting a shell)",
    },
    material_notes=_NOTES,
)
def flutes(shape: Part | None = None, count: int = 24, width: float = 3.0, depth: float = 1.2, z_from: float = 0.0,
           z_to: float | None = None, twist_angle: float = 0.0, raised: bool = False, reference: Part | None = None) -> Part:
    """``count`` radial bars, trimmed to the outer ``depth`` of ``reference`` (or ``shape``), are cut
    from the shape, so the flute floor follows the body profile at constant depth.  Sharp-edged: no fillets.  Shell FIRST, then flute the shell with the solid as
    ``reference`` (offsetting a fluted solid is slow and often invalid); the wall under a flute is
    then ``wall - depth``, so keep that >= 0.8 unless the part prints in spiral (vase) mode.

    Example:
        solid = revolved_body(profile)
        vase = flutes(shell_open_top(solid, wall=2.0), count=20, width=3, depth=1.2, z_from=5, reference=solid)
    """
    shape = revolved_body_default() if shape is None else shape
    ref = shape if reference is None else reference
    bb = ref.bounding_box()
    z_top = bb.max.Z + depth + 1.0 if z_to is None else z_to   # full height: overshoot the rim, no coincident faces
    reach = max(abs(bb.min.X), abs(bb.max.X), abs(bb.min.Y), abs(bb.max.Y)) + depth + 1.0
    h = z_top - z_from
    if h <= 0:
        raise ValueError("z_to must be above z_from")
    if twist_angle == 0.0:
        bar = Box(reach, width, h, align=(Align.MIN, Align.CENTER, Align.MIN))
        bars = Part() + [Rot(0, 0, 360.0 * i / count) * bar for i in range(count)]
    else:
        face = (Pos(reach / 2, 0) * Rectangle(reach, width)).face()
        bars = Part() + [Rot(0, 0, 360.0 * i / count) * Solid.extrude_linear_with_rotation(face, (0, 0, 0), (0, 0, h), twist_angle)
                         for i in range(count)]
    bars = Pos(0, 0, z_from) * bars
    z_slab = Pos(0, 0, bb.min.Z) * Box(4 * reach, 4 * reach, bb.max.Z - bb.min.Z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if raised:
        outer = offset(ref, amount=depth) & z_slab          # ribs never stand above the rim or below the bed
        return shape + ((bars & outer) - ref)
    # cut: the bars minus the inward offset of the reference = exactly the flute volumes.  The offset
    # keeps the top and bottom faces open so it does not shrink the height (else the top ``depth``
    # of the rim is cut clean through).
    inner = offset(_extended(ref, depth + 1.0), amount=-depth)
    return shape - (bars - inner)


def _extended(ref: Part, by: float) -> Part:
    """``ref`` with its planar top and bottom faces extruded outward by ``by`` (so an inward offset
    keeps its full height instead of shrinking at the ends)."""
    from build123d import extrude

    faces = ref.faces().sort_by(Axis.Z)
    ext = ref
    for f in (faces[0], faces[-1]):
        if f.geom_type == GeomType.PLANE:
            ext = ext + extrude(f, amount=by, both=True)
    return ext


def revolved_body_default() -> Part:
    from lib.form.revolved import revolved_body

    return revolved_body()
