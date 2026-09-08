"""PARAMETERS — caterpillar-and-mushrooms vape pen holder. Every dimension lives here.

Coordinates: +X right, +Y back, +Z up, origin on the hookah (pen) axis.  Read left to right the
scene is caterpillar -> hookah -> mushroom clump, all standing in a garden-patch ground.
"""

# --- what it holds -----------------------------------------------------------
PEN_D = 13.0            # mm, socket sizing for the pen battery (measures ~12; 13 + clearance = room)
PEN_LEN = 90.0          # mm, battery body length (ASSUMED: slim 510 pen)
CART_D = 11.0           # mm, cartridge body diameter at its widest
CART_LEN = 55.0         # mm, cartridge length including the mouthpiece
PEN_MASS_G = 30.0       # g, battery (ASSUMED) — only used by stability()
CART_MASS_G = 10.0      # g, one cartridge (ASSUMED) — only used by stability()

# --- sockets -----------------------------------------------------------------
BORE_CLEARANCE = 0.6    # mm, added to the DIAMETER (0.3 per side): drops in, does not rattle out
LEAD_IN = 1.2           # mm, 45 deg chamfer at each rim so the pen finds the hole without looking
VENT_D = 0.0            # mm, hole through a bore floor; 0 = blind. A vent under a cartridge would
VENT_LEN = 0.0          # mm,   drip leaked oil onto the desk, so both stay at 0

BASE_T = 6.0            # mm, ground thickness. EVERY bore floor sits on it, so it is the floor
                        #     thickness under the pen and both cartridges

# --- the hookah: pen tower at the origin -------------------------------------
# (r, z) from the base of the water bowl to the rim.  Bulbous at the bottom (mass down low, which
# is what keeps a 150 mm loaded pen upright), waisted, then flaring gently back out to the rim.
# A real belly, then a slim stem: the first version flared and waisted so gently that it read as a
# cooling tower. The stem cannot go below r = 9.5 (bore 6.8 + a 2.7 mm wall) so the bowl has to do
# the work — Ø36 belly against a Ø19 stem. Nothing flares faster than 35 deg from vertical.
HOOKAH_PROFILE = ((12.0, 0.0), (15.5, 5.0), (18.0, 12.0), (17.0, 18.0), (13.0, 25.0),
                  (10.0, 32.0), (9.5, 38.0), (10.5, 44.0), (12.5, 48.0))
HOOKAH_H = 48.0         # mm, = the last profile z; the socket rim
PEN_DEPTH = HOOKAH_H - BASE_T   # 42 mm, so the pen stands on the ground floor

# --- the caterpillar ---------------------------------------------------------
# (x, y, r) per body segment, head first.  The head is placed so it overlaps the hookah bowl:
# that contact is the whole gag — the caterpillar is holding the pipe it is smoking.
CATERPILLAR = (
    (-25.0, 6.0, 13.0),     # head, leaning its cheek on the hookah's belly
    (-39.0, 2.0, 10.5),
    (-46.0, -7.0, 8.5),
    (-49.0, -17.0, 6.5),
    (-47.0, -26.0, 5.0),    # tail, curling toward the front of the garden
)
# Pushed well into the bowl rather than grazing it: two curved surfaces that meet tangentially
# leave a feather edge the slicer cannot print, and the checker reads it as a 0.1 mm wall.
ARMS = (
    (-16.0, 9.0, 5.0),      # two stubby arms reaching around the hookah bowl from the head
    (-17.0, -4.0, 5.0),
)
SEGMENT_SQUASH = 1.7    # ratio, Z stretch per dome: 1.0 = hemisphere, >1 = a taller, rounder body.
                        #     At 1.45 the caterpillar read as a row of pebbles next to the hookah
SEGMENT_SINK = 3.0      # mm, how far the domes sit below the ground surface (half-buried, and it
                        #     guarantees a volumetric overlap rather than a shared face)
EYE_R = 3.2             # mm, eyeball
EYE_SQUASH = 1.0        # ratio, 1.0 = a round eye; the dome is seated on the head surface
EYE_EMBED = 0.95        # ratio of the head's semi-axis at which an eye centre sits (1.0 = on the
                        #     surface, so most of the ball would stick out)
EYE_DIRS = (            # unit directions on the head, looking forward (-Y) and slightly up
    (0.35, -0.72, 0.60),
    (-0.35, -0.72, 0.60),
)

# --- the mushrooms: one cartridge hidden in each ------------------------------
# (r, z) toadstool: stalk fat enough to swallow a cartridge, cap flaring at <= 25 deg from vertical
# so it needs no support, rounding over to a near-flat top the bore opens through.
# Straight slim stalk, then an ABRUPT flare and a domed cap. A gentle flare just makes a vase; the
# flare here runs at 35-37 deg, which is as close to a real cap's overhang as no-support allows.
# Stalk r 9.4 is the floor: 5.8 bore + 2.6 wall.
MUSHROOM_PROFILE = ((10.0, 0.0), (9.6, 8.0), (9.4, 20.0), (9.4, 27.0), (12.0, 31.0),
                    (14.8, 35.0), (15.2, 38.0), (13.8, 42.0), (11.2, 46.0))
MUSH_H = 46.0           # mm, = the last profile z
# Mushroom B is NOT the A profile scaled in Z: scaling a body scales its slopes, and a 0.76 z-scale
# turned the 37 deg cap flare into 45 and put 321 mm2 of unsupported overhang under it. B gets its
# own profile instead — 11 mm shorter in the STALK, cap section identical point for point.
MUSHROOM_B_PROFILE = ((10.0, 0.0), (9.6, 6.0), (9.4, 14.0), (9.4, 16.0), (12.0, 20.0),
                      (14.8, 24.0), (15.2, 27.0), (13.8, 31.0), (11.2, 35.0))
MUSH_A_XY = (24.0, 17.0)
MUSH_B_XY = (31.0, -11.0)
MUSH_A_H = MUSH_H
MUSH_B_H = MUSHROOM_B_PROFILE[-1][1]
CART_A_DEPTH = MUSH_A_H - BASE_T    # 40 mm: only 15 mm of cartridge shows above the cap
CART_B_DEPTH = MUSH_B_H - BASE_T    # 29.9 mm: the shorter mushroom is the easy one to grab from

# --- the ground --------------------------------------------------------------
# (x, y, r) circles smoothed into one garden-patch outline, one lobe per feature it has to carry.
BASE_BLOB = (
    (0.0, -2.0, 25.0),      # under the hookah, pushed forward so the front feet can go wide
    (-31.0, 4.0, 21.0),     # under the caterpillar's head and shoulders
    (-48.0, -13.0, 15.0),
    (-48.0, -25.0, 11.0),   # under the tail
    (24.0, 17.0, 20.0),     # under mushroom A
    (31.0, -11.0, 20.0),    # under mushroom B
)
BASE_SMOOTH_R = 9.0     # mm, fillet where the lobes meet — the difference between a garden and a blob
BED_CHAMFER = 0.5       # mm, elephant-foot chamfer on the bed-contact edge

# --- feet --------------------------------------------------------------------
# Explicit, not patterns.corner_holes: the ground is a blob, so a rectangle of holes either pokes
# out of a lobe or throws away the stance. Fitted feet REPLACE the base as the support polygon, so
# each one sits as far out on its lobe as it fits — that is worth ~8 deg of tip angle. Five, because
# four leave the front of the garden unsupported near x = 0.
FOOT_D = 10.0           # mm, stick-on rubber feet (optional; the recesses locate them)
FOOT_POS = ((-49.0, -22.0), (-31.0, 18.0), (25.0, 30.0), (36.0, -24.0), (0.0, -21.0))

# --- stability sums (not geometry) -------------------------------------------
PLA_DENSITY = 1.24      # g/cm3
PRINT_FILL = 0.5        # solid-volume fraction actually printed at 20% infill + 4 perimeters
MM3_PER_CM3 = 1000.0
MIN_TIP_ANGLE = 35.0    # deg, the design target stability() checks against
EDGE_SAMPLES = 24       # count, points sampled per footprint edge for the support polygon
SUPPORT_DIRS = 360      # count, directions the tipping margin is minimised over
