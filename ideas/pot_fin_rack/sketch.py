"""Sketch for ideas/pot_fin_rack: a comb of leaning blades that holds pots, pans
and lids on edge so their rims drain, standing on the drain_tiles field.

Use orientation:
    +X  along the counter edge, blades arrayed along it
    +Y  toward the sink; blades run along Y, base grooves drain this way
    +Z  up.

The comb does not carry its own drainage.  It stands on the [[drain_tiles]] deck
and inherits that deck's 4 degree pitch, so its base only has to move water
forward off its own front edge and onto the tile downstream; the tiles carry it
to [[sink_edge_drip_rail]] and the rail to the basin.  That is why there is no
sloped wedge base and no spout here.

Print orientation: as drawn.  Base underside flat on the bed, blades up.  The
blades LEAN (they are sheared, not rotated, so their roots stay flat on the
base), and the lean angle is the overhang angle, so TILT_DEG must stay well
under 45.  Nothing else faces down.

``slot_rack`` below is the proposed primitives.slot_rack, written here with the
signature it should ship with.  NOTE: it is a new component, not a
generalisation of primitives.pcb_slot_cradle — see IDEA.md.
"""
from math import radians, tan

from build123d import *  # noqa: F401,F403

# --- knobs (mm) ---------------------------------------------------------------
DEPTH = 60.0          # blade depth along Y = how far the comb reaches back
TILT_DEG = 12.0       # blade lean off vertical; this IS the print overhang angle
FIN_T = 2.6           # blade thickness (>= 2.4 so a wet pan does not splay one)
TOP_SLOPE_DEG = 10.0  # blade tops slope down toward the sink.  Level tops would sit a
                      #     pot rim horizontally, which is the trapped-water failure this
                      #     rack exists to fix; the tile under it adds its own 4 degrees.

POT_FINS = 4          # blades in the pot zone -> POT_FINS - 1 bays
POT_PITCH = 48.0      # pot bay width
POT_FIN_H = 85.0      # blade height in the pot zone

LID_FINS = 7          # blades in the lid zone
LID_PITCH = 12.0      # lid slot pitch
LID_FIN_H = 55.0      # shorter: a lid does not need 85 mm of blade

ZONE_GAP = 16.0       # between the last pot blade and the first lid blade
BASE_T = 3.2          # base plate thickness
BASE_MARGIN = 6.0     # base past the outermost blade roots

GROOVE_PITCH = 9.0    # base drain grooves, matching drain_tiles
GROOVE_W = 5.0        # grooves live INSIDE the bays: a groove running under a blade
                      #     severs it from the base (they are parallel)
BAY_MARGIN = 2.0      # groove field keeps this clear of each blade root
GROOVE_D = 1.2
GROOVE_WALL_DEG = 30.0

_GROOVE_RUN = GROOVE_D * tan(radians(GROOVE_WALL_DEG))


def slot_rack(
    count: int = 7,
    pitch: float = 12.0,
    fin_t: float = 2.6,
    fin_h: float = 55.0,
    depth: float = 60.0,
    tilt_deg: float = 12.0,
    top_slope_deg: float = 10.0,
) -> Part:
    """Proposed primitives.slot_rack: a row of leaning blades with the slots
    between them, standing on z=0 and centred on the origin in X.

    Blades are SHEARED by ``tilt_deg`` rather than rotated, so every root stays
    flat on whatever carries them and the print needs no support.  ``tilt_deg``
    is the overhang angle; keep it under ~40.  ``fin_h`` is the height at the
    back edge (-Y); ``top_slope_deg`` slopes the tops down toward +Y so whatever
    rests across them cannot sit level.
    """
    shear = fin_h * tan(radians(tilt_deg))
    fin = extrude(
        Plane.XZ
        * Polygon(
            (-fin_t / 2, 0.0),
            (fin_t / 2, 0.0),
            (fin_t / 2 + shear, fin_h),
            (-fin_t / 2 + shear, fin_h),
            align=None,
        ),
        amount=depth / 2,
        both=True,
    )
    # trim the tops with a plane through (y = -depth/2, z = fin_h) sloping down toward +Y
    t = tan(radians(top_slope_deg))
    top = lambda y: fin_h - (y + depth / 2) * t          # noqa: E731
    big = fin_h + depth + 100.0
    fin -= extrude(
        Plane.YZ
        * Polygon(
            (-depth, top(-depth)),
            (depth, top(depth)),
            (depth, fin_h + big),
            (-depth, fin_h + big),
            align=None,
        ),
        amount=big,
        both=True,
    )
    span = (count - 1) * pitch
    return Part() + [Pos(i * pitch - span / 2, 0, 0) * fin for i in range(count)]


def _blade_x() -> list[float]:
    """Every blade centre in X, both zones, sorted."""
    pot_x, lid_x, _ = _zones()
    pot = [pot_x + (i - (POT_FINS - 1) / 2) * POT_PITCH for i in range(POT_FINS)]
    lid = [lid_x + (i - (LID_FINS - 1) / 2) * LID_PITCH for i in range(LID_FINS)]
    return sorted(pot + lid)


def _groove_x(base_l: float) -> list[float]:
    """Groove lane centres: the bays between blades, plus the two base margins.

    Keyed to the blades rather than laid on a uniform pitch, because a groove is
    parallel to the blades — one that lands under a blade cuts it off the base.
    """
    blades = _blade_x()
    edges = [(-base_l / 2 + FIN_T / 2, blades[0])]
    edges += list(zip(blades, blades[1:]))
    edges += [(blades[-1], base_l / 2 - FIN_T / 2)]
    lanes: list[float] = []
    for x0, x1 in edges:
        usable = (x1 - x0) - FIN_T - 2 * BAY_MARGIN
        k = int(usable // GROOVE_PITCH)
        if k < 1:
            continue
        mid = (x0 + x1) / 2
        lanes += [mid + (i - (k - 1) / 2) * GROOVE_PITCH for i in range(k)]
    return lanes


def _zones() -> tuple[float, float, float]:
    """(pot centre x, lid centre x, total blade span in X)."""
    pot_span = (POT_FINS - 1) * POT_PITCH
    lid_span = (LID_FINS - 1) * LID_PITCH
    total = pot_span + ZONE_GAP + lid_span
    return -total / 2 + pot_span / 2, total / 2 - lid_span / 2, total


def build():
    pot_x, lid_x, total = _zones()

    base_l = total + FIN_T + 2 * BASE_MARGIN
    base = Pos(0, 0, BASE_T / 2) * Box(base_l, DEPTH, BASE_T)

    groove = Pos(0, 0, BASE_T) * extrude(
        Plane.XZ
        * Polygon(
            (-GROOVE_W / 2, 0.0),
            (GROOVE_W / 2, 0.0),
            (GROOVE_W / 2 - _GROOVE_RUN, -GROOVE_D),
            (-GROOVE_W / 2 + _GROOVE_RUN, -GROOVE_D),
            align=None,
        ),
        amount=DEPTH + 2,
        both=True,
    )
    # Blades run from z=0, not from the base top: a blade that merely sits on the
    # base shares a face with it and fuses into a loose body.  The grooves are then
    # cut through base and blades together, which is also what lets water past each
    # blade root instead of damming behind it.
    rack = base + Pos(pot_x, 0, 0) * slot_rack(
        POT_FINS, POT_PITCH, FIN_T, BASE_T + POT_FIN_H, DEPTH, TILT_DEG, TOP_SLOPE_DEG
    )
    rack += Pos(lid_x, 0, 0) * slot_rack(
        LID_FINS, LID_PITCH, FIN_T, BASE_T + LID_FIN_H, DEPTH, TILT_DEG, TOP_SLOPE_DEG
    )
    rack -= [Pos(x, 0, 0) * groove for x in _groove_x(base_l)]
    return {"rack": rack}
