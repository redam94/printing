"""PARAMETERS — Diptyque discovery-set stand, "le jardin". Every dimension lives here; model.py has no literals.

A thin plate bent into an arc, a pond along its front, and every bottle on its own pedestal or column,
all stepping up toward the centre (STEP_RISE per pitch), themed on fragrances in the sets:
  * the POND (front, lowest): Lunamaris (a crescent moon on the water), Lilyphea (lily pads and a
    water lily), L'Ombre dans l'Eau (ripples round the pads), Philosykos (a fig leaf floating at the
    left end), with a wavy shoreline;
  * the FRONT ROW: the five 2 x 4 cm cuboid bottles on rounded rectangular pedestals;
  * the BACK ROW, staggered half a pitch against the front: the five 12 cm cylinder bottles on fluted
    columns (Bois Corse / Tam Dao wood, Diptyque's fluted glass), four of them in the gaps between
    the cuboids and the fifth, the crown, behind the centre cuboid; and the four 1.5 ml testers on
    plain towers behind the other cuboids, tall enough to show over them;
  * the back edge scalloped into rose petals (Rose Roche), one behind every column and tower.

Why this shape: the 12 cm cylinders stand ~70 mm above the 5 cm cuboids whatever they stand on, so
they need no raised terrace, which was ~2/3 of the old stand's volume. Each bottle gets a column
only as tall as its pocket needs. Staggering lets the cylinders show between the cuboids; it does
not save depth here, because the 40 mm cuboids leave too narrow a gap behind them for a cylinder.

Coordinates: the arc centre is the origin, the stand is symmetric about +Y and the viewer looks
from the -Y side (from the centre outward), +Z up, bed at z=0. Angles are from +Y, counter-clockwise
positive, so a positive angle is on the viewer's LEFT.
"""
from math import asin, atan, cos, degrees, hypot, pi, radians, sin

# --- the bottles (measured by the user, 2026-10-06) -------------------------------------
CUBE_W = 40.0           # mm, cuboid width along the row (the wide face, toward the viewer)
CUBE_D = 20.0           # mm, cuboid depth front to back
CUBE_H = 50.0           # mm, cuboid height including the cap
CUBE_CORNER_R = 2.0     # mm, the glass cuboid's vertical-edge radius (ASSUMED; a sharp corner still fits)
CYL_CIRC = 60.0         # mm, cylinder circumference
CYL_D = round(CYL_CIRC / pi, 2)    # mm, cylinder diameter: 19.1
CYL_H = 120.0           # mm, cylinder height including the cap
TEST_CIRC = 40.0        # mm, 1.5 ml tester vial circumference
TEST_D = round(TEST_CIRC / pi, 2)  # mm, tester diameter: 12.73
TEST_H = 60.0           # mm, tester height including the cap
BOTTLES_PER_ROW = 5     # count, cuboids and cylinders: each set is five bottles
TESTERS = BOTTLES_PER_ROW - 1      # count, one tester behind each cuboid but the centre one (the crown's place)

# --- pockets -----------------------------------------------------------------
CLEARANCE = 2.0         # mm, added to the cuboid's width and depth and to each round bottle's diameter
                        #     (1 mm a side): covers tape-measured sizes, glass drops in
POCKET_DEPTH_FRAC = 0.28    # pocket depth as a fraction of the bottle height (cuboids, testers)
CYL_DEPTH_FRAC = 0.22   # the 12 cm cylinders: 26 mm holds them upright (tilt < 5 deg in the 1 mm play)
LEAD_IN = 1.2           # mm, 45 deg chamfer at each rim so a bottle finds its pocket
WEB = 4.0               # mm, wall between neighbouring cuboid pockets (10 perimeters)
FLOOR_T = 2.4           # mm, solid floor under the lowest pockets

CUBE_POCKET = (CUBE_W, CUBE_D, round(CUBE_H * POCKET_DEPTH_FRAC, 1))   # mm, pocket_array (x, y, depth): 14
CYL_POCKET_DEPTH = round(CYL_H * CYL_DEPTH_FRAC, 1)                    # mm, socket depth: 26.4
TEST_POCKET_DEPTH = round(TEST_H * POCKET_DEPTH_FRAC, 1)               # mm, socket depth: 16.8
POCKET_R_FRAC = 0.9     # ratio, pocket_array's corner clamp (corner <= 0.9 x half the short side);
                        #     repeated here so the pedestals and fit-check envelopes match the pockets

# --- pedestals and columns ---------------------------------------------------
# Each pocket is ringed by its pedestal: the pocket's lead-in outline grown by PLINTH_RIM. The
# cylinders' columns are fluted, so they are FLUTE_R wider to keep the rim whole between flutes.
PLINTH_RIM = 1.6        # mm, band of pedestal showing round each pocket's lead-in (4 lines)
PLINTH_GAP = 2.4        # mm, minimum gap between neighbouring pedestals / columns
PLINTH_CHAMFER = 0.4    # mm, chamfer on each pedestal's top edge
FLUTE_R = 1.2           # mm, column flute radius = depth
FLUTE_PITCH = 4.0       # mm, flute spacing round a column (lands of 1.6 mm between flutes)
FLUTE_OVERSHOOT = 1.0   # mm, flutes run past the column top so they open cleanly through it
EMBED = 0.2             # mm, raised features (pedestals, pads, moon) start this far below their surface so they fuse
OVERSHOOT = 0.5         # mm, cutters start this far outside the face they cut, so no faces coincide

_CUBE_PW, _CUBE_PD = CUBE_W + CLEARANCE, CUBE_D + CLEARANCE    # mm, cuboid pocket footprint (along, radial)
_GROW = LEAD_IN + PLINTH_RIM
CUBE_PLINTH = (_CUBE_PW + 2 * _GROW, _CUBE_PD + 2 * _GROW,
               min(CUBE_CORNER_R, _CUBE_PD / 2 * POCKET_R_FRAC) + _GROW)   # mm, (along, radial, corner r)
CYL_COLUMN_R = (CYL_D + CLEARANCE) / 2 + _GROW + FLUTE_R       # mm, fluted column radius: 14.55
TEST_TOWER_R = (TEST_D + CLEARANCE) / 2 + _GROW                # mm, tester tower radius: 10.17
_N_FLUTES = round(2 * pi * CYL_COLUMN_R / FLUTE_PITCH)        # count, flutes round a column
FLUTE_ARC_DEG = 360 * (_N_FLUTES - 0.5) / _N_FLUTES           # deg, arc_flutes span giving _N_FLUTES evenly round
COLUMN_FLUTE_PITCH = 2 * pi * CYL_COLUMN_R / _N_FLUTES        # mm, FLUTE_PITCH adjusted to close the circle

# --- heights -----------------------------------------------------------------
# Every pedestal / column top follows one ramp: STEP_RISE higher per FRONT pitch toward the centre,
# so the end cuboids are lowest, the centre cuboid 2 x STEP_RISE up, and the back row (on half
# pitches) rises STEP_RISE / 2 per bottle to the crown.
STEP_RISE = 6.0         # mm, per pitch toward the centre
PLATE_T = 7.0           # mm, the plate everything stands on (the shore)
POND_TOP = 4.0          # mm, the water surface: top of the pond along the front
CUBE_TOP = FLOOR_T + CUBE_POCKET[2]                    # mm, end cuboids' pedestal top: their floors sit FLOOR_T up
TESTER_REVEAL = 25.0    # mm, how much of each tester stands above the cuboid in front of it
BACK_TOP = CUBE_TOP - CUBE_POCKET[2] + CUBE_H + TESTER_REVEAL - (TEST_H - TEST_POCKET_DEPTH)  # mm, end testers' tower top
if BACK_TOP + STEP_RISE / 2 - CYL_POCKET_DEPTH < FLOOR_T:
    raise ValueError("the outer cylinders' sockets would break through the bed: raise TESTER_REVEAL")

# --- the arc -----------------------------------------------------------------
ARC_R = 110.0           # mm, radius of the cuboid row's pocket centres. Smaller = tighter arc
FRONT_LIP = 6.0         # mm, cuboid pocket to the plate's front edge (the shore)
END_WALL = 4.0          # mm, flat past the outermost pedestal, at each end and behind the wings
BACK_WALL = 3.0         # mm, column / tower to the start of the back edge's fillet (the petal's rim)
EDGE_R = 2.5            # mm, fillet on the plate's top edge
CORNER_R = 4.0          # mm, plan-view radius on the plate's end corners
BED_CHAMFER = 0.4       # mm, elephant-foot chamfer round the bed edge
TIER_OVERLAP = 1.0      # mm, how far one plan runs under the next, past its corner radius, so hidden corners stay buried

R_IN = ARC_R - _CUBE_PD / 2 - FRONT_LIP                # mm, the shore: the plate's front edge
_CUBE_BACK = ARC_R + CUBE_PLINTH[1] / 2                # mm, pedestals' back face
R_FRONT_OUT = _CUBE_BACK + END_WALL + EDGE_R           # mm, the plate's back edge past the back row (the wings)
R_CYL = _CUBE_BACK + PLINTH_GAP + CYL_COLUMN_R         # mm, cylinder columns' centres
R_TEST = _CUBE_BACK + PLINTH_GAP + TEST_TOWER_R        # mm, tester towers' centres
if ARC_R - CUBE_PLINTH[1] / 2 < R_IN + EDGE_R:
    raise ValueError("a pedestal overhangs the shore: raise FRONT_LIP or shrink PLINTH_RIM")


def _pitch_for(width: float, radius: float) -> float:
    """deg between centres for a chord of ``width`` at ``radius``."""
    return degrees(2 * asin(width / 2 / radius))


def _half_deg(half_w: float, r_inner: float) -> float:
    """deg from a rectangle's centre line to its inner corner, the rectangle facing the arc centre."""
    return degrees(atan(half_w / r_inner))


# Cuboid pitch: WEB between pockets at their crowded inner edge, and PLINTH_GAP between pedestals at
# their inner corners (rectangles on an arc converge toward the centre).
_CUBE_IN = ARC_R - CUBE_PLINTH[1] / 2                  # mm, pedestals' inner face
FRONT_PITCH_DEG = round(max(
    _pitch_for(_CUBE_PW + WEB, ARC_R - _CUBE_PD / 2 - LEAD_IN),
    2 * _half_deg(CUBE_PLINTH[0] / 2, _CUBE_IN) + degrees(PLINTH_GAP / _CUBE_IN)), 2)
FRONT_HALF_DEG = (BOTTLES_PER_ROW - 1) / 2 * FRONT_PITCH_DEG   # deg, outermost cuboid centre (and tester)
FRONT_SECTOR_DEG = round(2 * (FRONT_HALF_DEG + _half_deg(CUBE_PLINTH[0] / 2, _CUBE_IN)
                              + degrees(END_WALL / R_IN)), 2)       # deg, the plate and the pond


def _gap_to_pedestal(r: float, a: float, radius: float) -> float:
    """mm from a disc of ``radius`` at (r, a deg) to the cuboid pedestal at angle 0 (rounded corners ignored)."""
    x, y = abs(r * sin(radians(a))), r * cos(radians(a)) - ARC_R
    dx, dy = max(x - CUBE_PLINTH[0] / 2, 0.0), max(abs(y) - CUBE_PLINTH[1] / 2, 0.0)
    return hypot(dx, dy) - radius


# The staggered columns, half a pitch off the cuboids, must clear the pedestals either side, and
# neighbouring back-row discs must clear each other.
if min(_gap_to_pedestal(R_CYL, FRONT_PITCH_DEG / 2, CYL_COLUMN_R),
       _gap_to_pedestal(R_TEST, 0.0, TEST_TOWER_R)) < PLINTH_GAP - 1e-6:
    raise ValueError("a back-row column crowds a cuboid pedestal: raise PLINTH_GAP or ARC_R")
_HALF_STEP = radians(FRONT_PITCH_DEG / 2)
if hypot(R_CYL - R_TEST, 2 * R_TEST * sin(_HALF_STEP / 2)) < CYL_COLUMN_R + TEST_TOWER_R + PLINTH_GAP:
    raise ValueError("a cylinder column crowds a tester tower")

# --- the back edge: rose petals ----------------------------------------------
# A disc round every column and tower, at least BACK_WALL + EDGE_R wider than it, on a band out to
# R_BACK_EDGE. Neighbouring petals must overlap: where two only touch, the band's edge shows between
# them as a sub-millimetre flat and the top fillet fails on it. So the cylinder petals grow until
# they overlap their tester neighbours by PETAL_OVERLAP, and the band ends through the middle of
# that overlap, where it never shows. (The tester petals stay tight: the end ones set the width.)
PETAL_OVERLAP = 3.0     # mm, cylinder petal into tester petal, along the line between their centres
PETAL_SMOOTH = 4.0      # mm, radius in the notch between petals
TEST_PETAL_R = TEST_TOWER_R + BACK_WALL + EDGE_R       # mm
_CX, _CY = R_CYL * sin(_HALF_STEP), R_CYL * cos(_HALF_STEP)            # a gap cylinder (at half a pitch) ...
_TX, _TY = R_TEST * sin(2 * _HALF_STEP), R_TEST * cos(2 * _HALF_STEP)  # ... and the tester beside it
_D_CT = hypot(_TX - _CX, _TY - _CY)                    # mm, between their centres
CYL_PETAL_R = max(CYL_COLUMN_R + BACK_WALL + EDGE_R, _D_CT - TEST_PETAL_R + PETAL_OVERLAP)   # mm
_A = (_D_CT ** 2 + CYL_PETAL_R ** 2 - TEST_PETAL_R ** 2) / (2 * _D_CT)   # mm, cylinder centre to the overlap's chord
R_BACK_EDGE = hypot(_CX + (_TX - _CX) * _A / _D_CT, _CY + (_TY - _CY) * _A / _D_CT)   # mm, through that chord's middle

# --- the pond: water, moon, lilies and a fig leaf ----------------------------------
POND_W = 22.0           # mm, mean radial width of the pond in front of the shore
POND_WAVE = 1.6         # mm, amplitude of the wavy water's edge
POND_WAVES = 6          # count, waves along the water's edge
POND_CORNER_R = 8.0     # mm, plan radius on the pond's end corners
POND_EDGE_R = 1.5       # mm, fillet on the pond's top edge
R_POND = R_IN - POND_W                                 # mm, mean radius of the water's edge
R_POND_MID = (R_POND + R_IN) / 2                       # mm, where pond features are laid out

# Lily pads: (angle deg, radial offset from R_POND_MID mm, radius mm, slit direction deg).
# Pad 0 carries the water lily; it sits in front of the second cuboid on the viewer's left.
# A ripple ring must CROSS the shore's clip circle (R_IN - RIPPLE_MARGIN) or stay clear of it: at
# dr 0.5 pad 0's first ring touched it at one point, which left a non-manifold edge in the mesh.
# Both rippled pads sit so their first ring tops out ~0.7 mm inside it and the second ~0.9 outside.
LILY_PADS = ((FRONT_PITCH_DEG, -1.0, 7.5, 200.0),
             (FRONT_PITCH_DEG * 1.55, -3.0, 4.5, 120.0),
             (-FRONT_PITCH_DEG * 1.5, 0.5, 6.0, 330.0),
             (-FRONT_PITCH_DEG * 2.05, -2.5, 4.0, 60.0))
LILY_H = 1.2            # mm, pad height above the water
                        #     Plain pads, no vein grooves: at these sizes the veins read as clock ticks
LILY_FLOWER_PAD = 0     # index into LILY_PADS
LILY_FLOWER_R = (4.4, 2.7)     # mm, outer and inner petal ring radius (two stacked rosettes)
LILY_FLOWER_PETALS = 8  # count, per ring; the inner ring turns half a petal
LILY_FLOWER_LAYER = 1.2  # mm, each ring stands this much above the one below (the first above the pad)

# The moon on the water, centre front: (angle deg, radial offset mm, radius mm, rotation deg)
MOON = (0.0, 0.0, 6.5, 120.0)
MOON_H = 0.8            # mm, relief height above the water

# The fig leaf floating at the pond's left end (Philosykos; it was on the old back terrace's end
# faces, which the plate no longer has): (angle deg, radial offset mm, length mm, rotation deg).
# A plain silhouette, no veins: five veins meeting at a hub read as a maple leaf.
FIG = (FRONT_PITCH_DEG * 2.15, 0.0, 12.0, 75.0)
FIG_H = 0.8             # mm, relief height above the water

# Ripples spreading from the pads (L'Ombre dans l'Eau): rings around these pads, clipped to the water.
RIPPLE_PADS = (0, 2)    # indices into LILY_PADS
RIPPLE_FIRST = 2.2      # mm, first ring's distance outside the pad edge
RIPPLE_PITCH = 2.4      # mm, ring spacing
RIPPLE_COUNT = 3        # count
RIPPLE_W = 0.8          # mm, ring groove width
RIPPLE_D = 0.6          # mm, ring groove depth
RIPPLE_MARGIN = 1.2     # mm, rings stop this far inside the pond's edge, off the fillet and the shore
RIPPLE_MIN_AREA = 8.0   # mm2, ring fragments smaller than this (stubs left where a ring is clipped by a
                        #     pad or the shore) are dropped: they print as specks, and two side by side
                        #     left the tessellation open

# --- feet --------------------------------------------------------------------
PAD_D = 10.0            # mm, stick-on rubber / felt dots (optional; recesses locate them)
PAD_DEPTH = 0.8         # mm, recess depth
PAD_INSET = 14.0        # mm, pad centre distance from the plate's inner/outer edge and its ends
