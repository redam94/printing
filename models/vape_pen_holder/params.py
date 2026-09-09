"""PARAMETERS — caterpillar-and-mushrooms vape pen holder. Every dimension lives here.

Coordinates: +X right, +Y back, +Z up, origin on the hookah (pen) axis.  The hookah and the two
toadstools stand in a garden patch and the caterpillar wraps right around the outside of them.
"""
from math import cos, radians, sin

from lib.form.blobs import chain_centres    # the caterpillar's segments are derived from its path

# --- what it holds -----------------------------------------------------------
PEN_D = 16.0            # mm, socket sizing for the pen battery (measured by the user; 16 + clearance)
PEN_LEN = 90.0          # mm, battery body length (ASSUMED: slim 510 pen)
CART_D = 16.0           # mm, cartridge body diameter at its widest (measured by the user)
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
# cooling tower. The stem cannot go below r = 11.0 (bore 8.3 + a 2.7 mm wall) so the bowl has to do
# the work — Ø39 belly against a Ø22 stem. Nothing flares faster than 35 deg from vertical.
# Every radius here is 1.5 mm larger than the first version: the Ø16.6 bore left the old 9.5 stem
# with a 1.2 mm wall, which is three extrusions and nothing else.
HOOKAH_PROFILE = ((13.5, 0.0), (17.0, 5.0), (19.5, 12.0), (18.5, 18.0), (14.5, 25.0),
                  (11.5, 32.0), (11.0, 38.0), (12.0, 44.0), (14.0, 48.0))
HOOKAH_H = 48.0         # mm, = the last profile z; the socket rim
PEN_DEPTH = HOOKAH_H - BASE_T   # 42 mm, so the pen stands on the ground floor

# --- the caterpillar ---------------------------------------------------------
# It wraps the whole scene: head at the front-left with its face to the viewer, body sweeping up
# the left side, across the back behind mushroom A, down the right, tail curling back in at the
# front-right beside mushroom B.  The C opens at the FRONT, so the garden is never fenced in.
#
# The path is the parameter, not the segment coordinates: lib.form.dome_chain walks a spline
# through these control points at equal ARC length, which is what keeps the segments evenly spaced
# round the corners instead of bunching on the straights.
# The back of the arc is 4-5 mm further out than it was: mushroom A is fatter and sits further from
# the hookah now, and at the old radius a body segment reached 6.6 mm from A's axis — inside the
# Ø16 cartridge.  fit_checks is what says whether this arc is far enough out.
CATERPILLAR_PATH = ((-16.0, -16.0), (-25.0, 4.0), (-9.0, 30.0), (19.0, 41.0),
                    (47.0, 30.0), (58.0, 4.0), (48.0, -21.0), (30.0, -35.0))
CATERPILLAR_N = 18      # count, segments. Neighbours only fuse where they OVERLAP: at 17 the last
                        #     two segments met with 0.25 mm to spare, which is not a margin
CATERPILLAR_R_HEAD = 12.5   # mm
CATERPILLAR_R_TAIL = 6.0    # mm, and it sets the spacing budget — the tail is where a chain breaks
CATERPILLAR = chain_centres(CATERPILLAR_PATH, CATERPILLAR_N, CATERPILLAR_R_HEAD, CATERPILLAR_R_TAIL)

# --- the neck: the caterpillar rears up the hookah to the pen -----------------
# The body arrives at the hookah from the south-west, so the neck climbs at that azimuth, hugging
# the pot the whole way: each ball is half sunk into the hookah wall and sits on the one below, so
# a rearing neck that would otherwise be a 90 deg overhang all down its underside is supported the
# whole way up.  It leans IN as it rises (R 17 -> 12.5) because the pot narrows, and only the head
# leans back out to clear the rim.
#
# (R, z, r): R is the distance from the hookah axis, so the constraint that matters is legible —
# R - r is how close that ball gets to the axis, and the pen needs everything to stay outside
# PEN_D/2 = 6.5.  The head keeps 1.5 mm of that, the arms 0.7 mm.
NECK_SQUASH = 1.15      # ratio, Z stretch per ball. NOT SEGMENT_SQUASH: at 1.7 the bottom neck
                        #     ball is an egg 16 mm tall in the half-axis and its underside reaches
                        #     z = -2, through the bed, which is where the bed chamfer gives up
NECK_AZ = -135.0        # deg, the compass bearing the neck climbs at, measured from +X
NECK_RZR = ((18.5, 14.0, 9.5),      # anchored in body segment 0 AND in the pot's belly
            (16.0, 23.0, 7.0),
            (15.0, 31.0, 6.0),
            (14.0, 38.0, 5.2))      # the waist: this is the narrowest the pot gets
                        # Every R - r above is >= 8.8, and that is the whole design of this column.
                        # The pot's wall shrinks from 17.8 to 9.5 over the climb but the BORE does
                        # not, so a neck that keeps hugging the wall walks straight into the pen:
                        # against the first Ø13.6 bore it reached 5.2 mm from the axis and the fit
                        # check caught 45 mm3 of neck inside the parked battery.  The pen is Ø16
                        # now, so the whole column moved out again — the clearance is 0.8 mm.
                        # So the neck tapers instead of leaning in, and stands ~9 mm proud of the
                        # pot the whole way up — which is what a neck should look like anyway.
HEAD_RZR = (17.0, 45.0, 8.0)        # beside the rim, top at z 54 — head and shoulders over the pot,
                                    #     face at the mouthpiece. R - r = 9.0, clear of the pen

# Two stubby arms up at the rim, one either side of the head, reaching in to the pen: the gag is
# that the caterpillar is using the thing, and at the old ground level it could only cuddle the pot.
# R - r = 9.2 against an 8.0 pen, so they close on it without touching.
ARM_AZ = (-95.0, -175.0)    # deg, +-40 from the neck
ARM_RZR = (13.5, 45.0, 4.3)

NECK = tuple((R * cos(radians(NECK_AZ)), R * sin(radians(NECK_AZ)), z, r) for R, z, r in NECK_RZR)
HEAD = (HEAD_RZR[0] * cos(radians(NECK_AZ)), HEAD_RZR[0] * sin(radians(NECK_AZ)),
        HEAD_RZR[1], HEAD_RZR[2])
ARMS = tuple((ARM_RZR[0] * cos(radians(a)), ARM_RZR[0] * sin(radians(a)), ARM_RZR[1], ARM_RZR[2])
             for a in ARM_AZ)

SEGMENT_SQUASH = 1.7    # ratio, Z stretch per dome: 1.0 = hemisphere, >1 = a taller, rounder body.
                        #     At 1.45 the caterpillar read as a row of pebbles next to the hookah
SEGMENT_BASE_Z = 0.0    # mm, the plane the domes stand on. On the BED, not sunk into the ground:
                        #     most of the body is now outside the garden, and a dome floating 3 mm
                        #     up on nothing is a dome printed on nothing. Where the body does cross
                        #     the garden it is simply half-buried in it, which is where a
                        #     caterpillar belongs
EYE_R = 3.2             # mm, eyeball
EYE_SQUASH = 1.0        # ratio, 1.0 = a round eye; the dome is seated on the head surface
EYE_EMBED = 0.95        # mm the eye's flat base sits below the head's surface. It has to beat the
                        #     head's sag across an eye (3.2^2 / 2 / 8 = 0.64 mm) or the eye touches
                        #     at a point and prints loose
EYE_CAST = 40.0         # mm, how far outside the head each eye's ray starts
EYE_DIRS = (            # unit directions on the head. Both look in at the pen and UP at the
    (0.30, 0.62, 0.72),         #     mouthpiece — the head is level with the rim and the pen goes
    (0.62, 0.30, 0.72),         #     on up past it, which is the whole joke. The elevation is not
)                       #     styling: at 0.45 the eyes sat on the head's inner face and the last
                        #     2 mm of eyeball stuck into the Ø13 pen bore, which the fit check
                        #     caught as a 45 mm3 collision with the pen

# --- the mushrooms: one cartridge hidden in each ------------------------------
# (r, z) toadstool: stalk fat enough to swallow a cartridge, cap flaring at <= 25 deg from vertical
# so it needs no support, rounding over to a near-flat top the bore opens through.
# Straight slim stalk, then an ABRUPT flare and a domed cap. A gentle flare just makes a vase; the
# flare here runs at 35-37 deg, which is as close to a real cap's overhang as no-support allows.
# Stalk r 11.0 is the floor: 8.3 bore + 2.7 wall.
MUSHROOM_PROFILE = ((11.6, 0.0), (11.2, 8.0), (11.0, 20.0), (11.0, 27.0), (13.6, 31.0),
                    (16.4, 35.0), (16.8, 38.0), (15.4, 42.0), (12.8, 46.0))
MUSH_H = 46.0           # mm, = the last profile z
# Mushroom B is NOT the A profile scaled in Z: scaling a body scales its slopes, and a 0.76 z-scale
# turned the 37 deg cap flare into 45 and put 321 mm2 of unsupported overhang under it. B gets its
# own profile instead — 11 mm shorter in the STALK, cap section identical point for point.
MUSHROOM_B_PROFILE = ((11.6, 0.0), (11.2, 6.0), (11.0, 14.0), (11.0, 16.0), (13.6, 20.0),
                      (16.4, 24.0), (16.8, 27.0), (15.4, 31.0), (12.8, 35.0))
# Both moved out with the profiles. At the old spacing the Ø33.6 caps and the Ø39 belly fouled each
# other: A grazed the hookah by 1.1 mm at z 12 and the two caps met at z 32, and two curved surfaces
# that touch tangentially leave the feather edge this model was built to avoid.
MUSH_A_XY = (26.0, 19.0)
MUSH_B_XY = (34.0, -13.0)
MUSH_A_H = MUSH_H
MUSH_B_H = MUSHROOM_B_PROFILE[-1][1]
CART_A_DEPTH = MUSH_A_H - BASE_T    # 40 mm: only 15 mm of cartridge shows above the cap
CART_B_DEPTH = MUSH_B_H - BASE_T    # 29.9 mm: the shorter mushroom is the easy one to grab from

# --- the ground --------------------------------------------------------------
# (x, y, r) circles smoothed into one garden-patch outline, one lobe per feature it has to carry.
# The garden is now only what the three towers and the head stand on — the caterpillar wraps around
# OUTSIDE it and rests on the bed, so the old lobes that used to chase its tail are gone.
BASE_BLOB = (
    (0.0, -2.0, 25.0),      # under the hookah
    (26.0, 19.0, 20.0),     # under mushroom A
    (34.0, -13.0, 20.0),    # under mushroom B
    (-13.0, -10.0, 15.0),   # under the head, where it leans in
)
BASE_SMOOTH_R = 9.0     # mm, fillet where the lobes meet — the difference between a garden and a blob
BED_CHAMFER = 0.3       # mm, elephant-foot chamfer on the bed-contact edge. Not 0.5 any more:
                        #     the caterpillar wraps round the garden and meets it almost
                        #     tangentially in five places, and OCC will not put a 0.5 mm chamfer
                        #     across a crease that sharp — it fails the whole operation rather than
                        #     skipping the edge. 0.3 goes on all 40 edges, gaps included

# --- feet --------------------------------------------------------------------
# Fitted feet REPLACE everything else as the support polygon, so they go as far out as the part
# allows — and now the part allows a lot, because the caterpillar IS the perimeter. Five of the six
# sit under a body segment; the sixth closes the gap at the front where the C opens, standing on
# mushroom B's lobe. That is worth ~15 deg of tip angle over the old rectangle-ish stance.
FOOT_D = 10.0           # mm, stick-on rubber feet (optional; the recesses locate them)
FOOT_SEGMENTS = (0, 3, 6, 9, 12)    # body segments that carry a foot; all have r >= 7, so a Ø10
                                    #     recess still leaves a rim on the dome's flat underside
FOOT_EXTRA = ((30.0, -28.0),)       # mm, feet on the garden itself
FOOT_POS = tuple((round(CATERPILLAR[i][0], 2), round(CATERPILLAR[i][1], 2)) for i in FOOT_SEGMENTS) + FOOT_EXTRA

# --- stability sums (not geometry) -------------------------------------------
PLA_DENSITY = 1.24      # g/cm3
PRINT_FILL = 0.5        # solid-volume fraction actually printed at 20% infill + 4 perimeters
MM3_PER_CM3 = 1000.0
MIN_TIP_ANGLE = 35.0    # deg, the design target stability() checks against
EDGE_SAMPLES = 24       # count, points sampled per footprint edge for the support polygon
SUPPORT_DIRS = 360      # count, directions the tipping margin is minimised over

# --- geometric surface texture ------------------------------------------------
# Cut order (the lib/form order of operations): bores first, then flutes, then the studs. No mesh
# step at all now, so the part is one exact B-rep solid and exports STEP again.
#
# Everything turned on the lathe carries the same DIAMOND lattice: the flute band cut twice, once
# each way, so the two helices cross and leave faceted diamonds standing between them. Straight
# flutes were tried on the stalks first and read as scratches next to the hookah's diamonds — one
# pattern over all three bodies is what makes it look designed rather than decorated.
#
# Depth is set by the thinnest wall the band crosses, not by the fattest. The hookah band runs from
# the Ø39 belly to the Ø22 stem and the stem wall is 2.7, so 0.7 is the budget: it leaves 2.0 mm,
# five extrusions, under the deepest part of a groove. Crossing two cuts of the same depth does not
# make a deeper one — where they intersect the floor is still 0.7 down.
FLUTE_W = 2.4           # mm, groove width (tangential)
FLUTE_D = 0.7           # mm, cut depth -> 2.0 mm of wall left where the wall is thinnest
FLUTE_TWIST_RATE = 3.5  # deg of twist per mm of band. A rate rather than an angle, so the three
                        #     bands (42, 23 and 12 mm tall) all get the same helix: the angle a
                        #     helix makes with vertical is atan(rate * pi/180 * r) and the band
                        #     height cancels out of it. 34 deg at the stalks, 49 at the belly

HOOKAH_FLUTE_N = 18     # count, helices each way
HOOKAH_FLUTE_Z = (4.0, 46.0)    # mm, (from, to). Starts 2 mm below the garden surface so the step
                                #     where the groove begins is buried, and stops 2 mm short of
                                #     the rim so the socket's lead-in chamfer stays clean

STALK_FLUTE_N = 12      # count, helices each way. Fewer than the hookah because the stalk is a
                        #     third of the circumference: 12 gives the same ~3.5 mm diamond
STALK_A_FLUTE_Z = (4.0, 27.0)   # mm, stalk only: the flutes stop where the cap starts to flare
STALK_B_FLUTE_Z = (4.0, 16.0)   # mm, B's stalk is 11 mm shorter

# Toadstool spots: domes seated on the cap wherever a vertical ray lands, so they tilt with it.
# (x, y) offsets from the mushroom's own axis, all between r 13.2 and 14.8. That inner limit is not
# taste: the bore plus its lead-in opens at r 9.5, so a spot centre must clear 9.5 + CAP_SPOT_R
# before the bore starts eating crescents out of it. The outer limit is the cap's Ø33.6 rim.
CAP_SPOT_XY = ((13.16, 4.79), (3.78, 14.10), (-8.61, 10.26), (-14.74, -1.29),
               (-8.74, -10.42), (3.75, -14.01), (11.43, -6.60))
CAP_SPOT_R = 2.3        # mm, spot radius
CAP_SPOT_H = 1.1        # mm, height above the cap: a flattened dome, not a hemisphere — a proud
                        #     ball on a 37 deg cap flare would overhang, a 1.1 mm bump does not
CAP_SPOT_EMBED = 0.7    # mm, sunk below the cap surface. Must beat the cap's sag across a spot
                        #     (r^2 / 2R ~= 0.2 mm here) or the spot touches at a point and prints loose
CAP_SPOT_CAST = 20.0    # mm, how far above the cap top each ray starts

# Caterpillar tubercles: the little bumps down a real caterpillar's back. One ring per body segment
# (not the arms), all on the +Y side and 42 deg up, which is the surface you see and is well away
# from the eyes on -Y.
TUBERCLE_AZ = (-72.0, -24.0, 24.0, 72.0)    # deg about each segment, 0 = straight out from
                        #     TUBERCLE_ABOUT. The body curls right around the scene, so "the back"
                        #     is a different compass direction on every segment: it is the OUTWARD
                        #     side, the one you can see
TUBERCLE_ABOUT = (14.0, 2.0)    # mm, the point the bumps face away from — roughly the middle of
                                #     the hookah-and-mushrooms cluster the body is wrapped around
TUBERCLE_FROM = 1       # count, first body segment to get bumps; segment 0 carries the neck
TUBERCLE_EL = 42.0      # deg above horizontal
TUBERCLE_R = 2.1        # mm, bump radius, the same on every segment: they read as skin, and scaling
                        #     them with the segment left the tail with 1 mm nubs that just blob
TUBERCLE_H = 1.4        # mm, height above the surface
TUBERCLE_EMBED = 0.7    # mm, sunk below the surface (segment sag at r=5 is 0.44 mm)
TUBERCLE_CAST = 60.0    # mm, ray start distance from the segment centre — outside the whole scene

