"""PARAMETERS — snap-on split-ring clip for a 5.5 mm rod, the coupon print for mechanisms.split_ring_clip.

Every number is the component default, which was measured off the reference mesh filed under
ideas/ring_clip_5_5/references/ (bore, wall, necks, arm, strip and rail widths rounded to 0.4 mm
line multiples where the design rules ask for it). The two parts differ only in whether the necks
are plates at the faces (as the reference) or run the full depth.
"""
from lib.mechanisms.ring_clip import split_ring_clip_envelope

# --- what it holds ---
ROD_D = 5.5             # mm, the rod / tube / cable diameter (the reference file name says 5.5)
GRIP = 0.45             # mm, bore undersize so the closed jaws preload the rod (reference bore 5.05)

# --- ring ---
WALL = 1.0              # mm, ring wall (measured)
RING_GAP = 0.5          # mm, the slits that split the ring top and bottom (measured 0.48)
RING_CLEAR = 1.2        # mm, clear between ring top and rail underside (measured)

# --- living hinges ---
HINGE_W = 0.5           # mm, every neck: one 0.4 mm line (measured 0.46)
HINGE_LEN = 2.0         # mm, arm-to-post and arm-to-ring neck length (measured 1.8 to 2.1)
NECK_PLATE = 1.9        # mm, neck plate thickness at each face (measured); the necks are absent between the plates
NECK_FULL = 0.0         # the second part: necks over the full depth

# --- push arms: one bistable hinged beam per side (neck, body, neck) ---
ARM_LEN = 20.5          # mm, span from post face to ring wall, hinge to hinge (measured; = bistable_beam_pair span)
ARM_W = 1.6             # mm, beam body width, four lines (measured 1.54)
ARM_ANGLE = 14.0        # deg, pre-tilt: arms drop toward the posts (measured ~14 hinge to hinge)
JAW_ATTACH = -1.75      # mm, arm-to-ring neck height below the ring centre (measured)

# --- springs and rail ---
POST_D = 2.0            # mm, round posts joining strips to arm necks (measured 1.9)
STRIP_T = 0.6           # mm, side strip = return spring (measured 0.55)
RAIL_T = 3.0            # mm, mounting rail thickness (measured)
DEPTH = 7.2             # mm, print height (measured)

ENV = split_ring_clip_envelope(ROD_D, GRIP, WALL, RING_CLEAR, RAIL_T, ARM_LEN, ARM_ANGLE, JAW_ATTACH, POST_D, STRIP_T)
WIDTH = ENV["width"]            # mm, overall X (~49)
RAIL_TOP = ENV["rail_top"]      # mm, the mounting face, above the ring centre
Y_MIN = ENV["y_min"]            # mm, lowest point (post undersides)
RISE = ENV["rise"]              # mm, ring climb that would flatten the arms (~5); the rail stops it at RING_CLEAR, so no snap-through
