"""PARAMETERS — caterpillar-and-mushrooms vape pen holder. Every dimension lives here.

Coordinates: +X right, +Y back, +Z up, origin on the hookah (pen) axis.  The hookah and the two
toadstools stand in a garden patch and the caterpillar wraps right around the outside of them.
"""
from math import cos, radians, sin

from lib.form.blobs import chain_centres    # the caterpillar's segments are derived from its path

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
# It wraps the whole scene: head at the front-left with its face to the viewer, body sweeping up
# the left side, across the back behind mushroom A, down the right, tail curling back in at the
# front-right beside mushroom B.  The C opens at the FRONT, so the garden is never fenced in.
#
# The path is the parameter, not the segment coordinates: lib.form.dome_chain walks a spline
# through these control points at equal ARC length, which is what keeps the segments evenly spaced
# round the corners instead of bunching on the straights.
CATERPILLAR_PATH = ((-16.0, -16.0), (-24.0, 4.0), (-8.0, 27.0), (18.0, 36.0),
                    (42.0, 27.0), (53.0, 4.0), (45.0, -20.0), (28.0, -33.0))
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
NECK_RZR = ((17.0, 14.0, 9.5),      # anchored in body segment 0 AND in the pot's belly
            (15.0, 23.0, 7.5),
            (13.8, 31.0, 6.2),
            (12.8, 38.0, 5.4))      # the waist: this is the narrowest the pot gets
                        # Every R - r above is >= 7.3, and that is the whole design of this column.
                        # The pot's wall shrinks from 17.8 to 9.5 over the climb but the BORE does
                        # not, so a neck that keeps hugging the wall walks straight into the pen:
                        # at (13.0, 31, 7.8) and (12.5, 38, 7.0) it reached 5.2 and 5.5 from the
                        # axis and the fit check caught 45 mm3 of it inside the parked battery.
                        # So the neck tapers instead of leaning in, and stands ~9 mm proud of the
                        # pot the whole way up — which is what a neck should look like anyway.
HEAD_RZR = (16.0, 45.0, 8.0)        # beside the rim, top at z 53 — head and shoulders over the pot,
                                    #     face at the mouthpiece. R - r = 8.0, clear of the pen

# Two stubby arms up at the rim, one either side of the head, reaching in to the pen: the gag is
# that the caterpillar is using the thing, and at the old ground level it could only cuddle the pot.
# R - r = 7.5 against a 6.5 pen, so they close on it without touching.
ARM_AZ = (-95.0, -175.0)    # deg, +-40 from the neck
ARM_RZR = (11.8, 45.0, 4.3)

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
# The garden is now only what the three towers and the head stand on — the caterpillar wraps around
# OUTSIDE it and rests on the bed, so the old lobes that used to chase its tail are gone.
BASE_BLOB = (
    (0.0, -2.0, 25.0),      # under the hookah
    (24.0, 17.0, 20.0),     # under mushroom A
    (31.0, -11.0, 20.0),    # under mushroom B
    (-13.0, -10.0, 15.0),   # under the head, where it leans in
)
BASE_SMOOTH_R = 9.0     # mm, fillet where the lobes meet — the difference between a garden and a blob
BED_CHAMFER = 0.5       # mm, elephant-foot chamfer on the bed-contact edge

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

# --- surface work: fluting, openwork, spots, skin -----------------------------
# Order these are applied in (lib/form's order of operations): flutes on the stem, then the Voronoi
# cut, then the studs, then the noise skin LAST.  Every cut below is made in the body's OWN frame
# before the scene is unioned — that is what stops the bowl's cells appearing in the caterpillar's
# arms where they wrap the bowl, and stops mushroom A's cutter reaching across into mushroom B.

# Shallow flutes down the hookah's stem. The stem wall is only 2.7 mm and the parked pen leans on
# it, so these stay decorative: 0.6 mm leaves 2.1 mm of wall, still five perimeters at 0.4.
STEM_FLUTE_N = 16       # count, flutes around the stem
STEM_FLUTE_W = 2.2      # mm, tangential width
STEM_FLUTE_D = 0.6      # mm, cut depth
STEM_FLUTE_Z = (26.0, 45.0)     # mm, (from, to) — the waisted section only, stopping short of the rim

# Voronoi openwork.  Every cell is cut to the axis, so it goes clean through the near wall into the
# bore: the battery shows through the hookah's bowl and a cartridge through each mushroom stalk.
# The user asked for this knowing it opens the bores — so the bands START ABOVE the bore floor,
# leaving a sealed sump (2 mm under the bowl, 3.5 mm under each stalk) that catches a leaking
# cartridge instead of letting it run out of a cell onto the desk.
# The webs FAN IN with the cells (see form.voronoi_shell), so a web is widest at the outer surface
# and narrowest where it reaches the bore — web * bore_r / layout_r.  Both numbers below are sized
# at the bore, which is the only place a lattice ever actually fails: 3.4 on a 16.5 layout radius
# leaves 1.40 mm at the bowl's Ø13.6 bore, 2.4 on 9.5 leaves 1.47 mm at a stalk's Ø11.6 bore. Both
# are 3.5 nozzle widths, so every web prints as a solid strip and not as two touching perimeters.
BOWL_WEB = 3.4          # mm at the layout radius -> 1.40 mm at the bore
STALK_WEB = 2.4         # mm at the layout radius -> 1.47 mm at the bore
VORONOI_CORNER_R = 1.2  # mm, fillet on every cell corner — no stress risers in a web this thin
VORONOI_ROOF = 48.0     # deg from horizontal, slope of the roof clipped off each cell. Each cell is
                        #     a hole through a wall, so its top edges ARE the ceiling of that hole;
                        #     48 clears the 45 deg overhang limit, so nothing here needs support.
                        #     It is also why every cell reads as a pointed arch: a 12 mm wide window
                        #     cannot have a self-supporting roof AND square shoulders
VORONOI_RELAX = 4       # count, Lloyd rounds. At 3 the bowl still had a cavern and two slivers in
                        #     it; 4 evens the ring out without making it look like a drilled pattern
VORONOI_OVER = 3.5      # mm, how far outside the layout radius the cutters start (the bowl bulges
                        #     1.5 mm past its layout radius at the belly)
BOWL_CELL_IN = 4.0      # mm, radius the bowl's cells converge to — inside its 6.8 bore, so every
STALK_CELL_IN = 3.5     # mm,   cell breaks clean through instead of leaving a membrane at its edges

# Counts are low on purpose. The web is subtracted from every cell, so it is the CELL SIZE that
# decides how open the lattice looks: at 20 cells the bowl was 24% open and read as scattered
# shards, at 9 it is 41% open and reads as an openwork bowl with the pen visible behind it.
BOWL_CELL_R = 16.5      # mm, layout radius: the bowl's mean radius over its band
BOWL_CELL_Z = (8.0, 24.5)       # mm, (from, to); from = bore floor + 2 mm of sealed sump
BOWL_CELL_N = 9         # count, cells around the bowl -> ~12 mm windows
BOWL_CELL_SEED = 3

STALK_CELL_R = 9.5      # mm, layout radius: mushroom A's stalk is straight at 9.4-9.6
STALK_A_CELL_Z = (9.5, 25.0)    # mm, bore floor + 3.5 mm sump, up to where the cap starts to flare
STALK_A_CELL_N = 8      # count
STALK_A_CELL_SEED = 4
STALK_B_CELL_R = 9.8    # mm, B's band runs up into the start of the cap flare, so it sits slightly
                        #     proud of the 9.4 stalk; the cutters still start outside the body
STALK_B_CELL_Z = (8.0, 18.0)    # mm, B's stalk is 11 mm shorter than A's, so the band borrows the
                        #     first 2 mm of the flare — at (9.5, 15) it was 5.5 mm tall and the
                        #     cells came out as three triangles
STALK_B_CELL_N = 5      # count
STALK_B_CELL_SEED = 9

# Toadstool spots: domes seated on the cap wherever a vertical ray lands, so they tilt with it.
# (x, y) offsets from the mushroom's own axis, all between r 10.8 and 12.8. That inner limit is not
# taste: the bore plus its lead-in opens at r 7.0, so a spot centre must clear 7.0 + CAP_SPOT_R
# before the bore starts eating crescents out of it.
CAP_SPOT_XY = ((10.34, 3.76), (3.11, 11.59), (-6.94, 8.27), (-12.45, -1.09),
               (-7.20, -8.58), (3.31, -12.36), (9.44, -5.45))
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

# Noise skin, applied LAST over everything (this is the mesh step: the part exports STL and 3MF but
# no STEP from here on). Horizontal displacement only and exterior-only, so every bore, every cell
# and every z level stays exactly where the B-rep put it and the fit checks still hold.
TEXTURE_AMP = 0.28      # mm, peak displacement; <= 0.4 prints clean at a 0.4 mm nozzle
TEXTURE_SCALE = 5.0     # mm, feature size — finer than the cloud tray's 7, this is skin not weather
TEXTURE_SEED = 7
TEXTURE_EDGE = 1.6      # mm, refinement before displacing; 5 mm features need ~3 samples across
TEXTURE_TOL = 0.02      # mm, chord tolerance the B-rep is tessellated at before the texture. This
TEXTURE_ANG = 0.25      # rad,  part is ~130 small revolved bodies (18 segments, 68 tubercles, 14
                        #     spots, the eyes) and lib.form.mesh tessellates every one of them to
                        #     0.01 mm by default, which made a 1.44 M triangle, 69 MB STL for a
                        #     96 mm ornament. Refinement can only SPLIT edges, so the only lever is
                        #     the tolerance going in: 0.02 mm is well under a 0.28 mm texture and
                        #     an eighth of a layer, and it takes the mesh to ~340 k.
                        #     (Simplifying afterwards was tried and abandoned: manifold3d.simplify
                        #     pinches the thin webs into touching sheets and the part stops being
                        #     watertight at every tolerance that saves anything.)
