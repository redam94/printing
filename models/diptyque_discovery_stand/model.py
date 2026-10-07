"""Diptyque discovery-set stand, "le jardin": a pond, a front row of cuboids, a staggered colonnade behind.

Part: ``stand`` — one piece, seen in plan as an arc concave towards the viewer like an amphitheatre:
a thin plate with a pond along its front, and every bottle on its own pedestal or column, all
stepping up toward the centre (see params.py for the themes):

* the pond (POND_TOP high): a wavy water's edge, lily pads and a water lily (Lilyphea), a crescent
  moon (Lunamaris), ripple rings round the pads (L'Ombre dans l'Eau), a fig leaf afloat (Philosykos);
* the front row: the five 2 x 4 cm cuboid bottles, wide face to the viewer, on rounded rectangular
  pedestals;
* the back row, half a pitch off the front: the five 12 cm cylinder bottles on fluted columns (Bois
  Corse, Tam Dao), four in the gaps between the cuboids and the crown behind the centre one, and
  the four 1.5 ml testers on plain towers behind the other cuboids, each TESTER_REVEAL taller than
  the cuboid in front of it;
* the back edge: one rose petal round every column and tower (Rose Roche).

Every pocket faces the arc centre. Pedestal and column tops follow one ramp, STEP_RISE per front
pitch toward the centre, so the crown cylinder stands highest.

Print orientation: as it stands, plate on the bed, pockets open upward. Faces are vertical or
horizontal, lead-ins and the pedestal chamfers are 45 deg, the flutes are vertical grooves, and every
relief stands on the surface below it: no supports.

Assumptions: bottle sizes are the user's tape measurements (cuboids 20 x 40 x 50, cylinders 60 mm
round x 120, testers 40 mm round x 60); the cuboids' corner radius is a guess (a sharp corner still
fits). Six optional stick-on pads (PAD_D) go under the plate.
"""
from math import cos, degrees, radians, sin

from build123d import Axis, Circle, Part, Plane, Pos, RectangleRounded, Rot, Sketch, chamfer, extrude, fillet, offset

from lib.component import on_bed
from lib.form.motifs import arc_band, arc_flutes, crescent, lily_pad, palmate_leaf, petal_rosette, ripple_rings
from lib.form.outline import smooth_corners
from lib.primitives.feet import rubber_foot_recess
from lib.primitives.pocket_array import pocket_array
from lib.primitives.socket_array import socket_array

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def on_arc(radius: float, angle: float, shape):
    """Place ``shape`` (its X along the arc, Y pointing away from the centre) at ``angle`` deg from +Y."""
    a = radians(angle)
    return Pos(-radius * sin(a), radius * cos(a), 0) * Rot(0, 0, angle) * shape


def lift(angle: float) -> float:
    """Height of a pedestal / column top above its row's end ones: STEP_RISE per front pitch toward the centre."""
    return P.STEP_RISE * (P.FRONT_HALF_DEG - abs(angle)) / P.FRONT_PITCH_DEG


# --- the bottles' places --------------------------------------------------------

class Kind:
    """A bottle type: pedestal outline, pocket cutter (rim at z=0), row radius, end top height,
    fluted or not, and the bottle's envelope standing on its pocket floor (rim at z=0)."""

    def __init__(self, outline: Sketch, cutter: Part, radius: float, base: float, fluted: bool, bottle: Part):
        self.outline, self.cutter, self.radius, self.base, self.fluted, self.bottle = (
            outline, cutter, radius, base, fluted, bottle)


class Slot:
    """One bottle's place: its kind, its angle from +Y, and its pedestal top height."""

    def __init__(self, kind: Kind, angle: float):
        self.kind, self.angle = kind, angle
        self.radius = kind.radius
        self.top = kind.base + lift(angle)


def kinds() -> tuple[Kind, Kind, Kind]:
    """(cuboid, cylinder, tester)."""
    clear = dict(clearance=P.CLEARANCE, lead_in=P.LEAD_IN)
    cube_r = min(P.CUBE_CORNER_R, P.CUBE_D / 2 * P.POCKET_R_FRAC)
    cube = Kind(RectangleRounded(*P.CUBE_PLINTH), pocket_array((P.CUBE_POCKET,), corner_r=P.CUBE_CORNER_R, **clear),
                P.ARC_R, P.CUBE_TOP, False,
                Pos(0, 0, -P.CUBE_POCKET[2]) * extrude(RectangleRounded(P.CUBE_W, P.CUBE_D, cube_r), amount=P.CUBE_H))
    cyl = Kind(Circle(P.CYL_COLUMN_R), socket_array(P.CYL_D, depth=P.CYL_POCKET_DEPTH, **clear), P.R_CYL,
               P.BACK_TOP, True, Pos(0, 0, -P.CYL_POCKET_DEPTH) * extrude(Circle(P.CYL_D / 2), amount=P.CYL_H))
    test = Kind(Circle(P.TEST_TOWER_R), socket_array(P.TEST_D, depth=P.TEST_POCKET_DEPTH, **clear), P.R_TEST,
                P.BACK_TOP, False, Pos(0, 0, -P.TEST_POCKET_DEPTH) * extrude(Circle(P.TEST_D / 2), amount=P.TEST_H))
    return cube, cyl, test


def slots() -> list[Slot]:
    """Five cuboids on the front row; on the back row, on half pitches, a cylinder in every gap and
    behind the centre cuboid (the crown), a tester behind every other cuboid."""
    cube, cyl, test = kinds()
    last = P.BOTTLES_PER_ROW - 1
    out = [Slot(cube, (i - last / 2) * P.FRONT_PITCH_DEG) for i in range(P.BOTTLES_PER_ROW)]
    for j in range(-last, last + 1):              # back row, in half pitches from the centre
        out.append(Slot(cyl if j % 2 or j == 0 else test, j * P.FRONT_PITCH_DEG / 2))
    return out


def back_row() -> list[Slot]:
    return [s for s in slots() if s.radius != P.ARC_R]


# --- plans ---------------------------------------------------------------------

def pond_plan() -> Sketch:
    """The water; it runs back under the plate past its own corner radius."""
    return arc_band(P.R_POND, P.R_IN + P.POND_CORNER_R + P.TIER_OVERLAP, P.FRONT_SECTOR_DEG,
                    wave_in=P.POND_WAVE, waves_in=P.POND_WAVES, corner_r=P.POND_CORNER_R)


def petal_r(s: Slot) -> float:
    return P.CYL_PETAL_R if s.kind.fluted else P.TEST_PETAL_R


def plate_plan() -> Sketch:
    """The shore: a band behind the pond out past the cuboids, and over the back row a band to
    R_BACK_EDGE scalloped by a rose petal round every column and tower."""
    front = arc_band(P.R_IN, P.R_FRONT_OUT, P.FRONT_SECTOR_DEG, corner_r=P.CORNER_R)
    back = arc_band(P.R_FRONT_OUT - P.CORNER_R - P.TIER_OVERLAP, P.R_BACK_EDGE, 2 * P.FRONT_HALF_DEG)
    petals = Sketch() + [on_arc(s.radius, s.angle, Circle(petal_r(s))) for s in back_row()]
    return smooth_corners(front + back + petals, P.PETAL_SMOOTH)


def slab(plan: Sketch, top: float, edge_r: float) -> Part:
    solid = extrude(plan, amount=top)
    solid = fillet(solid.edges().group_by(Axis.Z)[-1], edge_r)
    return chamfer(solid.edges().group_by(Axis.Z)[0], P.BED_CHAMFER)


def body() -> Part:
    return slab(pond_plan(), P.POND_TOP, P.POND_EDGE_R) + slab(plate_plan(), P.PLATE_T, P.EDGE_R)


# --- pedestals, columns and pockets ----------------------------------------------

def pedestals() -> list[Part]:
    out = []
    for s in slots():
        solid = Pos(0, 0, P.PLATE_T - P.EMBED) * extrude(s.kind.outline, amount=s.top - P.PLATE_T + P.EMBED)
        out.append(on_arc(s.radius, s.angle, chamfer(solid.edges().group_by(Axis.Z)[-1], P.PLINTH_CHAMFER)))
    return out


def flutes() -> list[Part]:
    """Vertical flutes round every cylinder column, from the plate up through the column top."""
    out = []
    for s in slots():
        if s.kind.fluted:
            rods = arc_flutes(P.CYL_COLUMN_R, P.FLUTE_ARC_DEG, pitch=P.COLUMN_FLUTE_PITCH, flute_r=P.FLUTE_R,
                              height=s.top - P.PLATE_T + P.FLUTE_OVERSHOOT)
            out.append(on_arc(s.radius, s.angle, Pos(0, 0, P.PLATE_T) * rods))
    return out


def pockets() -> list[Part]:
    return [on_arc(s.radius, s.angle, Pos(0, 0, s.top) * s.kind.cutter) for s in slots()]


# --- the pond -------------------------------------------------------------------

def _on_pond(angle: float, dr: float, sk: Sketch) -> Sketch:
    return on_arc(P.R_POND_MID + dr, angle, sk)


def _raise(sk: Sketch, base: float, top: float) -> Part:
    """Relief standing on the surface at ``base``, up to ``top``."""
    return extrude(Plane.XY.offset(base - P.EMBED) * sk, amount=top - base + P.EMBED)


def pad_sketches() -> list[Sketch]:
    return [_on_pond(a, dr, lily_pad(r, rotation=slit)) for a, dr, r, slit in P.LILY_PADS]


def moon_sketch() -> Sketch:
    a, dr, r, rot = P.MOON
    return _on_pond(a, dr, crescent(r, rotation=rot))


def fig_sketch() -> Sketch:
    a, dr, length, rot = P.FIG
    return _on_pond(a, dr, Rot(0, 0, rot) * palmate_leaf(length))


def pond_reliefs() -> list[Part]:
    """Lily pads, the water lily on pad LILY_FLOWER_PAD, the moon and the fig leaf, all on the water."""
    water = P.POND_TOP
    out = [_raise(sk, water, water + P.LILY_H) for sk in pad_sketches()]
    a, dr, _, _ = P.LILY_PADS[P.LILY_FLOWER_PAD]
    outer_r, inner_r = P.LILY_FLOWER_R
    half_petal = 180.0 / P.LILY_FLOWER_PETALS
    out.append(_raise(_on_pond(a, dr, petal_rosette(outer_r, P.LILY_FLOWER_PETALS)),
                      water, water + P.LILY_H + P.LILY_FLOWER_LAYER))
    out.append(_raise(_on_pond(a, dr, petal_rosette(inner_r, P.LILY_FLOWER_PETALS, rotation=half_petal)),
                      water, water + P.LILY_H + 2 * P.LILY_FLOWER_LAYER))
    out.append(_raise(moon_sketch(), water, water + P.MOON_H))
    out.append(_raise(fig_sketch(), water, water + P.FIG_H))
    return out


def ripples() -> Part:
    """Ring grooves round the RIPPLE_PADS, clipped to open water."""
    rings = Sketch()
    for i in P.RIPPLE_PADS:
        a, dr, r, _ = P.LILY_PADS[i]
        rings += _on_pond(a, dr, ripple_rings(r + P.RIPPLE_FIRST, P.RIPPLE_PITCH, P.RIPPLE_COUNT, P.RIPPLE_W))
    water = offset(pond_plan(), -(P.POND_EDGE_R + P.RIPPLE_MARGIN)) & Circle(P.R_IN - P.RIPPLE_MARGIN)
    keep_off = Sketch() + [_on_pond(a, dr, Circle(r + P.RIPPLE_MARGIN)) for a, dr, r, _ in P.LILY_PADS]
    keep_off += offset(moon_sketch(), P.RIPPLE_MARGIN) + offset(fig_sketch(), P.RIPPLE_MARGIN)
    rings = (rings & water) - keep_off
    rings = Sketch() + [f for f in rings.faces() if f.area >= P.RIPPLE_MIN_AREA]   # no stubs where a ring is clipped
    return extrude(Plane.XY.offset(P.POND_TOP + P.OVERSHOOT) * rings, amount=-(P.RIPPLE_D + P.OVERSHOOT))


# --- feet -----------------------------------------------------------------------

def pads() -> list[Part]:
    """A pair at the pond's ends, at the plate's back corners, and under the outer cylinder columns."""
    pad = Rot(180, 0, 0) * rubber_foot_recess(P.PAD_D, depth=P.PAD_DEPTH)
    out = []
    for r in (P.R_POND + P.PAD_INSET, P.R_FRONT_OUT - P.PAD_INSET):
        end = P.FRONT_SECTOR_DEG / 2 - degrees(P.PAD_INSET / r)
        out += [on_arc(r, a, pad) for a in (-end, end)]
    outer = max(s.angle for s in back_row() if s.kind.fluted)
    return out + [on_arc(P.R_CYL, a, pad) for a in (-outer, outer)]


def bottles() -> Part:
    """Envelopes of every bottle standing on its pocket floor (for the fit check and the picture)."""
    return Part() + [on_arc(s.radius, s.angle, Pos(0, 0, s.top) * s.kind.bottle) for s in slots()]


def build() -> dict[str, Part]:
    stand = body() + pedestals()
    stand = stand - ripples()
    stand = stand + pond_reliefs()
    stand = stand - pockets() - flutes() - pads()
    return {"stand": on_bed(stand)}


def fit_checks(parts: dict[str, Part]) -> dict[str, tuple[Part, Part]]:
    """Every bottle, standing on its pocket floor, must clear the stand."""
    return {"bottles_vs_stand": (parts["stand"], bottles())}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
