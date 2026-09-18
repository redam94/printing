"""PARAMETERS — compliant key carabiner. Every dimension lives here; model.py has no literals."""

# --- ring ---
OUTER_L = 60.0          # mm, overall length (X)
OUTER_W = 34.0          # mm, overall width (Y)
BAND = 5.0              # mm, ring band width (radial)
DEPTH = 6.0             # mm, part depth = print height
OUTER_R = 8.0           # mm, outer corner radius (keeps the +Y side straight over |x| < 22)
INNER_R = OUTER_R - BAND   # mm, inner corner radius (concentric corners)
BAND_Y = OUTER_W / 2 - BAND / 2      # mm, centreline of the +Y band (the gated side)
BED_CHAMFER = 0.4       # mm, elephant-foot chamfer on the bed edge loop of the ring

# --- gate: a leaf spring rooted at the -X end of the gap, tip resting under a lip at the +X end ---
GAP_LEN = 28.0          # mm, opening in the +Y band (what a key ring or strap passes through)
GAP_X = 6.0             # mm, gap centre offset in X (root at GAP_X - GAP_LEN/2 = -8, nose at +20, both inside the straight run)
GATE_T = 1.2            # mm, gate thickness = 3 lines; flexes in the bed plane
GATE_BOW = 1.5          # mm, outward bow of the gate at mid-span (finger pad, and a little preload against the lip)
GATE_DEPTH = DEPTH      # mm, gate height = ring height
ROOT_OVERLAP = 2.5      # mm, gate buried into the ring past the gap's -X end
TIP_CLEAR = 0.4         # mm, gap between the gate tip and the back of the mouth (prints free)
MOUTH_CLEAR = 0.35      # mm, gap between the gate's outer face and the lip above it
LIP_LEN = 1.5           # mm, how far the lip reaches over the gate tip in +X (tip sits LIP_LEN - TIP_CLEAR under it)
GAP_X0 = GAP_X - GAP_LEN / 2                       # mm, gap start (root side)
GAP_X1 = GAP_X + GAP_LEN / 2                       # mm, gap end (nose side)
GATE_X_START = GAP_X0 - ROOT_OVERLAP               # mm, buried end of the gate
GATE_X_END = GAP_X1 + LIP_LEN - TIP_CLEAR          # mm, free tip of the gate
GATE_LEN = GATE_X_END - GATE_X_START               # mm, gate chord
GATE_XC = (GATE_X_START + GATE_X_END) / 2          # mm, gate chord centre
MOUTH_TOP = BAND_Y + GATE_T / 2 + MOUTH_CLEAR      # mm, Y of the underside of the lip
LIP_T = OUTER_W / 2 - MOUTH_TOP                    # mm, lip thickness left above the mouth (1.55 = 4 lines)
assert LIP_T >= 1.2, "lip over the gate tip is too thin; reduce GATE_T or MOUTH_CLEAR"
assert GATE_BOW + GATE_T / 2 < BAND / 2, "the bowed gate would stand proud of the ring outline"
