"""PARAMETERS — cable comb and tool rail on mechanisms.flex_fingers. Every dimension lives here; model.py has no literals."""

# --- desk cable comb: USB / power / audio leads 3-8 mm ---
COMB_SLOTS = 6
COMB_PITCH = 9.0        # mm, finger pitch
COMB_FINGER_T = 1.2     # mm, 3 lines
COMB_FINGER_LEN = 14.0  # mm
COMB_ENTRY = 3.2        # mm, smallest cable held (thin USB lead); an 8 mm lead spreads a finger 2.4 mm (~1.4% root strain)
COMB_DEPTH = 12.0       # mm, print height; leaves room for the keyholes in the spine
COMB_SPINE = 8.0        # mm, spine width behind the fingers
COMB_END_T = 2.4        # mm, outer fingers
COMB_LEN = COMB_SLOTS * COMB_PITCH + COMB_END_T    # mm, overall X

# --- tool rail: screwdrivers, markers, hex keys 7-14 mm ---
RAIL_SLOTS = 5
RAIL_PITCH = 16.0
RAIL_FINGER_T = 1.6     # mm, 4 lines
RAIL_FINGER_LEN = 22.0
RAIL_ENTRY = 7.0        # mm; a 14 mm shank spreads a finger 3.5 mm (~1.7% root strain: PETG)
RAIL_DEPTH = 16.0
RAIL_SPINE = 10.0
RAIL_END_T = 3.2
RAIL_LEN = RAIL_SLOTS * RAIL_PITCH + RAIL_END_T

# --- mounting: keyholes in the back face (slot up), zip-tie slots through the spine ---
KEY_HEAD_D = 7.0        # mm, pan-head screw head (No. 6 / M3.5)
KEY_SHANK_D = 4.0       # mm
KEY_SLOT = 4.0          # mm, slot rise above the head pocket
KEY_DEPTH = 3.0         # mm, pocket depth into the spine
COMB_KEY_X = 20.0       # mm, keyholes at +/- this on the comb
COMB_KEY_Z = 4.5        # mm, head-pocket centre height (pocket spans 0.7 .. 10.8 of the 12 mm spine)
RAIL_KEY_HEAD_D = 8.0
RAIL_KEY_SHANK_D = 4.5
RAIL_KEY_SLOT = 6.0
RAIL_KEY_X = 30.0
RAIL_KEY_Z = 5.5        # mm (pocket spans 1.2 .. 14.3 of the 16 mm spine)
TIE_W = 4.8             # mm, common cable tie
TIE_T = 1.6
TIE_SPACING = 12.0      # mm, between the two slots (the loop goes round a table leg or a monitor arm)
