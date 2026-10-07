"""Decorative motifs: arc bands (terraces, amphitheatre steps), palmate leaves, lily pads, petal
rosettes, crescents, ripple rings, and vertical flutes along an arc.

Everything except ``arc_flutes`` is a 2D sketch on the XY plane.  Raise a motif with
``extrude(Plane.XY.offset(top - embed) * sk, amount=h + embed)``, deboss it with
``part - extrude(Plane.XY.offset(top) * sk, amount=-depth)``, or put it on a wall with
``Plane(origin, x_dir, z_dir) * sk`` (local +Y is ``z_dir x x_dir``).  Arc angles are measured
from +Y, counter-clockwise positive, so an ``arc_band`` of any angle is symmetric about +Y.
"""
from __future__ import annotations

from math import cos, pi, radians, sin

from build123d import (Align, Circle, Cylinder, Ellipse, Line, Part, Polygon, Pos, Rectangle, Rot, Sketch, Spline,
                       ThreePointArc, make_face, offset)

from lib.component import MaterialNotes, component
from lib.form.outline import smooth_corners

_NOTES = MaterialNotes(
    validated=[], orientation="any (2D motif): raised or debossed on a top face it needs no support; on a wall keep the relief <= 1 mm",
    notes="UNVALIDATED. Keep raised/debossed features >= 0.8 mm wide (two lines at a 0.4 nozzle): crescent horns and rosette petal tips are rounded to min_width for that reason; leaf veins and ripple rings take their width as given.")


_PALM_RISE = 0.6   # palm circle centre height above the stem junction, as a fraction of its radius
_VEIN_HUB = 1.5    # radius of the disc joining the veins at the stem junction, in vein widths
_MIN_LAND = 0.8    # mm, narrowest land left between lily-pad veins (two lines at a 0.4 nozzle)
_VEIN_REACH = 0.85  # lily-pad veins stop this fraction of the radius out, inside the rim


def _blunt(sk: Sketch, min_width: float) -> Sketch:
    """Morphological opening: shrink by half of min_width and grow back, so every tip or horn
    narrower than min_width is rounded off (to radius min_width / 2) and nothing prints as a hairline."""
    if min_width <= 0:
        return sk
    return Sketch() + offset(offset(sk, -min_width / 2), min_width / 2).faces()


def _at(r: float, a: float) -> tuple[float, float]:
    """Point at radius ``r`` and angle ``a`` (rad) from +Y, counter-clockwise positive."""
    return (-r * sin(a), r * cos(a))


def _edge(r: float, half: float, amp: float, waves: int, samples: int, reverse: bool):
    """Arc (or sinusoidal wavy arc) at radius r from -half to +half (reversed if asked)."""
    if amp == 0 or waves == 0:
        pts = [_at(r, -half), _at(r, 0.0), _at(r, half)]
        return ThreePointArc(*(pts[::-1] if reverse else pts))
    n = max(8, waves * samples)
    pts = [_at(r + amp * cos(2 * pi * waves * (i / n - 0.5)), -half + 2 * half * i / n) for i in range(n + 1)]
    return Spline(*(pts[::-1] if reverse else pts))


@component(
    id="form.arc_band", version="1.0.0",
    summary="Annular-sector sketch symmetric about +Y (terrace, amphitheatre step, curved shelf), optional wavy inner/outer edge and rounded corners.",
    tags=["arc", "band", "sector", "annulus", "terrace", "step", "amphitheatre", "curved", "shelf", "wave", "sketch", "form"],
    units={"r_in": "mm", "r_out": "mm", "angle": "deg", "wave_in": "mm", "waves_in": "count", "wave_out": "mm",
           "waves_out": "count", "corner_r": "mm", "samples_per_wave": "count"},
    descriptions={
        "r_in": "inner radius", "r_out": "outer radius", "angle": "total sector angle, centred on +Y",
        "wave_in": "sinusoidal amplitude of the inner edge (0 = plain arc)",
        "waves_in": "full waves along the inner edge (the edge is symmetric about +Y)",
        "wave_out": "sinusoidal amplitude of the outer edge (0 = plain arc)",
        "waves_out": "full waves along the outer edge",
        "corner_r": "fillet on the four corners (0 = sharp); corners too tight for it get a smaller radius",
        "samples_per_wave": "spline points per wave (>= 6 keeps the curve faithful)",
    },
    material_notes=_NOTES,
)
def arc_band(r_in: float = 40.0, r_out: float = 60.0, angle: float = 90.0, wave_in: float = 0.0, waves_in: int = 0,
             wave_out: float = 0.0, waves_out: int = 0, corner_r: float = 0.0, samples_per_wave: int = 8) -> Sketch:
    """Centre of curvature at the origin; the band spans ``angle`` degrees centred on +Y.

    Example:
        terrace = extrude(arc_band(90, 120, 100, wave_in=1.5, waves_in=7, corner_r=4), amount=5)
    """
    if not 0 <= r_in < r_out:
        raise ValueError("need 0 <= r_in < r_out")
    if wave_in + wave_out >= r_out - r_in:
        raise ValueError("the waves would make the band cross itself")
    half = radians(angle) / 2
    outer = _edge(r_out, half, wave_out, waves_out, samples_per_wave, reverse=False)   # right -> left
    inner = _edge(r_in, half, wave_in, waves_in, samples_per_wave, reverse=True)       # left -> right
    edges = [outer, Line(outer @ 1, inner @ 0), inner, Line(inner @ 1, outer @ 0)]
    return smooth_corners(Sketch() + make_face(edges), corner_r)


@component(
    id="form.palmate_leaf", version="1.0.0",
    summary="Palmate leaf sketch (fig, vine, maple): lobes radiating from the stem junction at the origin, central lobe along +Y, optional vein lines left uncut.",
    tags=["leaf", "fig", "vine", "maple", "botanical", "palmate", "lobes", "veins", "relief", "deboss", "sketch", "form"],
    units={"length": "mm", "lobes": "count", "spread": "deg", "lobe_width": "ratio", "taper": "ratio", "palm": "ratio",
           "stem_len": "ratio", "stem_w": "ratio", "tip": "ratio", "veins": "mm", "smooth_r": "mm"},
    descriptions={
        "length": "stem junction to the tip of the central lobe",
        "lobes": "number of lobes (odd keeps a central lobe; the defaults draw a 5-lobed fig leaf)",
        "spread": "angle between the outermost lobe axes",
        "lobe_width": "lobe width as a fraction of its own length",
        "taper": "each lobe out from the centre is this fraction of the length of the one inside it",
        "palm": "radius of the solid centre that joins the lobes, as a fraction of length",
        "stem_len": "stem length below the origin, as a fraction of length (0 = no stem)",
        "stem_w": "stem width, as a fraction of length",
        "tip": "radius of a disc rounding off each lobe's end, as a fraction of that lobe's length: 0 = plain elliptical lobes (pointed, maple-like); ~0.22 = spoon-shaped lobes, broad and blunt at the end (fig); 0.3 and up turns into a club suit",
        "veins": "width of the vein lines removed from the sketch (0 = none); debossed, the veins stay standing",
        "smooth_r": "fillet in the sinuses between lobes",
    },
    material_notes=_NOTES,
)
def palmate_leaf(length: float = 30.0, lobes: int = 5, spread: float = 220.0, lobe_width: float = 0.55,
                 taper: float = 0.75, palm: float = 0.3, stem_len: float = 0.35, stem_w: float = 0.12,
                 tip: float = 0.22, veins: float = 0.0, smooth_r: float = 2.0) -> Sketch:
    """Each lobe is an ellipse from the origin out to its tip, optionally club-ended (``tip``); the
    union is smoothed in the sinuses. The defaults draw a fig leaf; tip=0 with lobe_width ~0.4 reads
    as maple, lobes=3 as a vine leaf.
    With ``veins`` > 0 a midrib runs up every lobe from the stem junction, removed from the sketch, so
    subtracting the extruded sketch from a wall leaves a recessed leaf with raised veins.

    Example:
        wall = wall - extrude(Plane.YZ * palmate_leaf(28, veins=1.0), amount=-0.8)
    """
    if lobes < 1:
        raise ValueError("need at least one lobe")
    mid = (lobes - 1) / 2
    angles = [0.0 if lobes == 1 else -spread / 2 + spread * i / (lobes - 1) for i in range(lobes)]
    lens = [length * taper ** abs(i - mid) for i in range(lobes)]
    sk = Sketch() + Pos(0, palm * length * _PALM_RISE) * Circle(palm * length)   # raised: the base narrows into the stem
    for a, ln in zip(angles, lens):
        sk += Rot(0, 0, a) * (Pos(0, ln / 2) * Ellipse(ln * lobe_width / 2, ln / 2))
        if tip > 0:
            sk += Rot(0, 0, a) * (Pos(0, ln * (1 - tip)) * Circle(ln * tip))
    if stem_len > 0:
        sk += Pos(0, -stem_len * length / 2) * Rectangle(stem_w * length, stem_len * length)
    sk = smooth_corners(sk, smooth_r)
    if veins > 0:
        rib = 0.85
        cut = Sketch() + [Rot(0, 0, a) * (Pos(0, rib * ln / 2) * Rectangle(veins, rib * ln)) for a, ln in zip(angles, lens)]
        cut += Circle(veins * _VEIN_HUB)   # where the veins meet: no hair-thin wedges between them
        sk -= cut
    return sk


@component(
    id="form.lily_pad", version="1.0.0",
    summary="Lily-pad sketch: a disc with a V slit running to the centre, optional radial vein lines left uncut.",
    tags=["lily", "pad", "water", "pond", "botanical", "leaf", "relief", "sketch", "form"],
    units={"r": "mm", "notch": "deg", "rotation": "deg", "veins": "mm", "vein_count": "count"},
    descriptions={
        "r": "pad radius", "notch": "opening angle of the V slit", "rotation": "direction the slit opens toward, from +Y",
        "veins": "width of the radial vein lines removed from the sketch (0 = none)",
        "vein_count": "number of veins, spaced evenly with the slit's edges; each starts where the land beside it is 0.8 mm wide (small pads may get none)",
    },
    material_notes=_NOTES,
)
def lily_pad(r: float = 8.0, notch: float = 36.0, rotation: float = 0.0, veins: float = 0.0, vein_count: int = 7) -> Sketch:
    """Example:
        pond = pond + extrude(Plane.XY.offset(pond_top) * lily_pad(9, rotation=40), amount=1.2)
    """
    h = radians(notch) / 2
    reach = 2 * r
    wedge = Polygon((0, 0), _at(reach, h), _at(reach, -h), align=None)
    sk = Circle(r) - wedge
    if veins > 0 and vein_count > 0:
        # veins evenly spaced with the slit's two edges; each starts where the land beside it is
        # _MIN_LAND wide, so the wedges between veins near the centre never print as hairlines
        step = (360.0 - notch) / (vein_count + 1)
        start = (_MIN_LAND + veins) / (2 * sin(radians(step) / 2))
        stop = min(r * _VEIN_REACH, r - _MIN_LAND)     # and the rim outside them keeps _MIN_LAND too
        if stop - start >= veins:
            cut = Sketch() + [Rot(0, 0, notch / 2 + step * (i + 1)) * (Pos(0, (start + stop) / 2) * Rectangle(veins, stop - start))
                              for i in range(vein_count)]
            sk -= cut
    return Rot(0, 0, rotation) * sk


@component(
    id="form.petal_rosette", version="1.0.0",
    summary="Flower rosette sketch: pointed (lens-shaped) petals radiating from a centre disc; stack two, rotated, for a layered bloom.",
    tags=["flower", "petal", "rosette", "lily", "lotus", "daisy", "botanical", "star", "relief", "sketch", "form"],
    units={"r": "mm", "petals": "count", "petal_w": "ratio", "centre": "ratio", "rotation": "deg", "min_width": "mm"},
    descriptions={
        "r": "centre to petal tip", "petals": "number of petals",
        "petal_w": "petal width as a fraction of r", "centre": "centre disc radius as a fraction of r",
        "rotation": "rotates the rosette",
        "min_width": "petal tips are rounded so nothing is narrower than this (0 = needle-sharp tips)",
    },
    material_notes=_NOTES,
)
def petal_rosette(r: float = 6.0, petals: int = 8, petal_w: float = 0.42, centre: float = 0.25, rotation: float = 0.0,
                  min_width: float = 0.8) -> Sketch:
    """Each petal is a vesica (the overlap of two circles) from the centre to the tip.

    Example:
        bloom = extrude(petal_rosette(6), amount=1.2) + extrude(Plane.XY.offset(1.2) * petal_rosette(3.5, rotation=22.5), amount=1.2)
    """
    ln, w = r, petal_w * r
    big = ((ln / 2) ** 2 + (w / 2) ** 2) / w      # radius of the two circles whose overlap is the lens
    off = big - w / 2
    lens = (Pos(off, ln / 2) * Circle(big)) & (Pos(-off, ln / 2) * Circle(big))
    sk = Sketch() + Circle(centre * r) + [Rot(0, 0, rotation + 360.0 * i / petals) * lens for i in range(petals)]
    return _blunt(sk, min_width)


@component(
    id="form.crescent", version="1.0.0",
    summary="Crescent-moon sketch: a disc with an offset disc bitten out of it, horns pointing +X before rotation.",
    tags=["moon", "crescent", "lunar", "night", "celestial", "relief", "sketch", "form"],
    units={"r": "mm", "bite_r": "ratio", "bite_offset": "ratio", "rotation": "deg", "min_width": "mm"},
    descriptions={
        "r": "moon radius", "bite_r": "radius of the disc removed, as a fraction of r",
        "bite_offset": "how far the removed disc sits off centre (toward +X), as a fraction of r; bite_r + bite_offset must exceed 1",
        "rotation": "rotates the crescent",
        "min_width": "the horns are rounded off so nothing is narrower than this (0 = cusps)",
    },
    material_notes=_NOTES,
)
def crescent(r: float = 8.0, bite_r: float = 0.82, bite_offset: float = 0.42, rotation: float = 0.0,
             min_width: float = 0.8) -> Sketch:
    """Example:
        sky = sky - extrude(Plane.XY.offset(top) * crescent(7, rotation=30), amount=-0.6)
    """
    if bite_r + bite_offset <= 1:
        raise ValueError("the bite must break out of the disc (bite_r + bite_offset > 1)")
    return Rot(0, 0, rotation) * _blunt(Circle(r) - Pos(bite_offset * r, 0) * Circle(bite_r * r), min_width)


@component(
    id="form.ripple_rings", version="1.0.0",
    summary="Concentric ring sketch (water ripples, target, rings in a pond) to deboss or raise; centred on the origin.",
    tags=["ripple", "rings", "water", "pond", "concentric", "groove", "relief", "sketch", "form"],
    units={"r0": "mm", "pitch": "mm", "count": "count", "width": "mm"},
    descriptions={"r0": "centre-line radius of the innermost ring", "pitch": "radial spacing between rings",
                  "count": "number of rings", "width": "ring width"},
    material_notes=_NOTES,
)
def ripple_rings(r0: float = 5.0, pitch: float = 3.0, count: int = 3, width: float = 0.8) -> Sketch:
    """Clip the result to the surface it sits on (``rings & surface_sketch``) before cutting.

    Example:
        pond = pond - extrude(Plane.XY.offset(top) * (ripple_rings(10, 3, 4) & pond_outline), amount=-0.6)
    """
    if width >= pitch:
        raise ValueError("width must be below pitch or the rings merge")
    return Sketch() + [Circle(r0 + i * pitch + width / 2) - Circle(r0 + i * pitch - width / 2) for i in range(count)]


@component(
    id="form.arc_flutes", version="1.0.0",
    summary="Negative (subtract me): vertical half-round flutes with their axes on an arc about Z, for a curved wall face (concave or convex); z=0 up.",
    tags=["flutes", "fluting", "reeding", "grooves", "arc", "curved", "riser", "wood", "texture", "negative", "form"],
    units={"radius": "mm", "angle": "deg", "pitch": "mm", "flute_r": "mm", "height": "mm"},
    descriptions={
        "radius": "radius of the face being fluted (the flute axes sit on it, so the depth is flute_r)",
        "angle": "sector the flutes fill, centred on +Y; the row is centred in it",
        "pitch": "spacing between flute axes, measured along the arc",
        "flute_r": "flute radius = depth into the face; width is twice this",
        "height": "flute length from z=0 up (overshoot the face's top by ~1 mm to open the flute out)",
    },
    material_notes=MaterialNotes(validated=[], orientation="axis vertical (flutes run up the wall); a horizontal flute is a 90 deg overhang",
                                 notes="UNVALIDATED. Keep pitch - 2 * flute_r >= 0.8 so the lands between flutes survive."),
)
def arc_flutes(radius: float = 60.0, angle: float = 60.0, pitch: float = 4.0, flute_r: float = 1.2, height: float = 20.0) -> Part:
    """Example:
        body = body - Pos(0, 0, tread_z) * arc_flutes(riser_r, sector, pitch=4, flute_r=1.2, height=riser_h + 1)
    """
    if pitch - 2 * flute_r <= 0:
        raise ValueError("flutes overlap: pitch must exceed 2 * flute_r")
    span = radius * radians(angle)
    n = int(span // pitch) + 1
    step = pitch / radius
    rod = Cylinder(flute_r, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Part() + [Pos(*_at(radius, (i - (n - 1) / 2) * step), 0) * rod for i in range(n)]
