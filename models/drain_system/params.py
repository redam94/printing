"""PARAMETERS — countertop drain system: rail, tile field, pot rack. Every dimension lives here.

Assembly frame (the frame every fit check is written in):
    +X  along the counter edge
    +Y  toward the sink; the countertop cutout edge is y = 0
    +Z  up, countertop top surface z = 0

Water goes: pot rack -> tile row 2 -> tile row 1 -> rail pan -> basin. Each stage hands off by
overhanging the next, so nothing has to seal.

Measured by the user 2026-09-09: 30 mm counter, 420 x 420 mm of counter to play with. The one
number still unmeasured is UNDER_REACH — how much counter underside is exposed at the cutout
before the sink flange starts. It is the only thing standing between this and a printable rail.
"""
from math import radians, tan

# --- the counter -------------------------------------------------------------
COUNTER_T = 30.0        # mm, countertop thickness at the sink cutout (MEASURED: 3 cm stone slab)
COUNTER_RUN = 420.0     # mm, counter available along the sink edge (MEASURED)
COUNTER_DEPTH = 420.0   # mm, counter available back from the edge (MEASURED). The field does not
                        #     use all of it — see ROWS: depth costs leg height, not counter.
UNDER_REACH = 4.0       # mm, exposed counter underside at the cutout before the sink flange starts.
                        #     PLACEHOLDER — the last unmeasured number. 0 makes it a plain saddle
                        #     held by the pan; too much and the lip fouls the sink flange.
THROAT_CLEAR = 0.4      # mm, added to COUNTER_T so the clip slides onto a square edge
RAIL_LEN = 140.0        # mm, ONE rail segment. 420 mm of run will not fit a 270 mm bed, so the rail
                        #     is printed in RAIL_SEGMENTS pieces that butt end to end. The seam runs
                        #     across the pan, and the water runs along it toward the basin, not over
                        #     it, so a plain butt joint does not leak.

# --- material ----------------------------------------------------------------
# PLA throughout, at the user's request (2026-09-09). The write-ups specified PETG for the splash
# zone; PLA is defensible for the tiles (keyed, not sprung, nothing hot lands on them) and is the
# risk the user accepted on the rack, which may take a hot pan. Clearances below are PLA values.
SNAP_CLEAR = 0.15       # mm, added to the snap groove radius; PLA prefers <= 0.4 total interference

# --- rail: the clip and its pan ----------------------------------------------
JAW_T = 3.0             # mm, jaw hanging down the cut face
LIP_T = 2.4             # mm, return lip thickness
CORNER_RELIEF = 1.2     # mm, relief at both counter corners: a printed inside corner carries a
                        #     radius, a stone arris does not, and without relief the clip rocks
PAN_REACH = 55.0        # mm, how far inland the pan sits on the counter
FLOOR_T = 2.4           # mm, pan floor thickness at the outboard edge
PAN_PITCH_DEG = 3.0     # deg, floor pitch toward the sink
RIM_H = 4.0             # mm, rim height above the floor at the inland end. Low because the tiles
                        #     cantilever their deck over this rim; ~10 if the rail is used alone.
RAMP_RATIO = 1.15       # -, rim ramp run / rise; >= 1.0 keeps it self-supporting
RIM_TOP_W = 1.6         # mm, flat on the rim crest. Without it the ramp meets the outer face in a
                        #     knife edge, which was every sub-0.8 mm sample in the sketch.
END_WALL_T = 2.4        # mm, end walls closing the pan at both ends
DRIP_GROOVE_R = 1.0     # mm, drip break cut into the outboard face so water separates
DRIP_GROOVE_Z = 2.0     # mm, how far below the counter surface it sits
DRIP_GROOVE_OUT = 0.4   # mm, groove centre outboard of the face, so the arc meets it at 66 deg
                        #     instead of tangentially (a tangential groove leaves knife edges)

PAN_TP = tan(radians(PAN_PITCH_DEG))                     # -, floor rise per mm inland
Y_RAMP = -PAN_REACH + RIM_TOP_W + RIM_H * RAMP_RATIO     # mm, where the rim ramp meets the floor
PAN_ZTOP = FLOOR_T + (JAW_T - Y_RAMP) * PAN_TP + RIM_H   # mm, rim crest height above the counter
# The clip's saddle IS the pan floor at its outboard edge: flat at FLOOR_T, with the pan wedge
# sitting on it and rising inland, so water leaves the floor over the jaw's outboard face.

# --- tiles: one design, one leg height per row --------------------------------
TILE_X = 70.0           # mm, tile pitch along the counter edge; the field grows in X for free
TILE_Y = 70.0           # mm, tile depth. Two rows = 140 mm of counter depth.
ROWS = 2                # count, rows of tiles back from the sink. NOT set by the counter (there is
                        #     420 mm of it): every row back costs ROW_DROP of leg height, because the
                        #     lap has to clear the deck and drip nose of the row in front. 2 rows =
                        #     140 mm deep on 24 mm back legs; 3 rows = 210 mm on 35 mm legs, which is
                        #     the practical limit before the field is a ramp you reach over.
DECK_T = 3.2            # mm, deck thickness (the grooves take GROOVE_D of it)
DECK_PITCH_DEG = 4.0    # deg, deck pitch toward the sink
FOOT_H = 13.0           # mm, deck underside height at the outboard edge, front row. Must clear the
                        #     rail's rim crest (PAN_ZTOP) by more than NOSE_D — see fit_checks.
WALL_T = 2.4            # mm, side walls; they are also the feet and carry the snap joint
LAP = 14.0              # mm, how far the deck overhangs its own walls at the downhill edge. The
                        #     front row laps the rail's rim, every other row laps the row in front.
LAP_CLEAR = 1.0         # mm, air gap under the lap, on top of the nose depth
END_RIB_T = 2.4         # mm, cross rib under the uphill edge: stiffens the deck AND is what the
                        #     next row back butts against, so the rows cannot creep apart
GROOVE_PITCH = 9.0      # mm, drain groove centres (shared with the rack)
GROOVE_W = 5.0          # mm, groove width at the deck surface
GROOVE_D = 1.2          # mm, groove depth
GROOVE_WALL_DEG = 30.0  # deg, groove wall angle off vertical. The deck prints face down, so this
                        #     IS the overhang angle: 45 is the limit, 30 is comfortable.
NOSE_D = 3.0            # mm, drip nose hanging below the downhill deck edge
NOSE_T = 2.4            # mm, nose thickness
SNAP_R = 0.6            # mm, snap bead radius (mechanisms.snap_ridge default)
SNAP_Z = 5.0            # mm, bead height above the counter
SNAP_INSET = 8.0        # mm, bead stops this far short of each end (lead-in)

DECK_TP = tan(radians(DECK_PITCH_DEG))                   # -, deck rise per mm inland
# How much taller each row back stands. Derived, not chosen: the row behind has to clear the deck
# top of the row in front where it laps it, plus that row's drip nose, plus air.
ROW_DROP = (TILE_Y - LAP) * DECK_TP + DECK_T + NOSE_D + LAP_CLEAR

# --- rack: the comb of leaning blades ----------------------------------------
RACK_DEPTH = 60.0       # mm, blade depth along Y (the row it stands on is TILE_Y deep)
TILT_DEG = 12.0         # deg, blade lean off vertical; this IS the print overhang angle
FIN_T = 2.6             # mm, blade thickness (>= 2.4 so a wet 3 kg pan does not splay one)
TOP_SLOPE_DEG = 10.0    # deg, blade tops slope toward the sink. Level tops sit a pot rim
                        #     horizontally, which is the trapped-water failure this rack exists to
                        #     fix; the tile deck under it adds its own DECK_PITCH_DEG.
POT_FINS = 3            # count, blades in the pot zone -> POT_FINS - 1 = 2 bays
POT_PITCH = 48.0        # mm, pot bay width
POT_FIN_H = 85.0        # mm, blade height in the pot zone
LID_FINS = 7            # count, blades in the lid zone
LID_PITCH = 12.0        # mm, lid slot pitch
LID_FIN_H = 55.0        # mm, shorter: a lid does not need 85 mm of blade
ZONE_GAP = 16.0         # mm, between the last pot blade and the first lid blade
BASE_T = 3.2            # mm, base plate thickness
BASE_MARGIN = 6.0       # mm, base past the outermost blade roots
BAY_MARGIN = 2.0        # mm, groove field keeps this clear of each blade root: a groove is
                        #     parallel to the blades and one under a blade severs it from the base
RACK_GAP = 0.2          # mm, air gap between the rack base and the tile deck in the fit check

# --- how many of each to print -----------------------------------------------
TILES_PER_ROW = int(COUNTER_RUN // TILE_X)          # 6 at 70 mm across a 420 mm run
RAIL_SEGMENTS = int(COUNTER_RUN // RAIL_LEN)        # 3 at 140 mm; they butt end to end
FIELD_DEPTH = ROWS * TILE_Y - (ROWS - 1) * LAP + PAN_REACH   # mm, counter depth the system uses

# --- assembly: where each piece sits in the frame above -----------------------
DRIP_OVER = 2.0         # mm, how far the front row's deck edge reaches past the rail's rim crest
TILE_Y0 = -PAN_REACH + RIM_TOP_W + DRIP_OVER   # mm, front row's downhill deck edge
