"""PARAMETERS — test coupons for mechanisms.bistable_beam_pair. Every dimension lives here; model.py has no literals.

The mechanism numbers are the component defaults, which came from the BYU CMR references filed
under ideas/bistable_compliant_switch/references/ (hinge, beam, depth measured; span and pre-tilt
estimated). The coupon exists to confirm the estimated two and to find out which materials snap
and hold, so the two parts differ only in hinge width.
"""
from lib.mechanisms.bistable import bistable_envelope

# --- the mechanism (component defaults; see lib/mechanisms/bistable.py for provenance) ---
SPAN = 37.0             # mm, beam hinge to hinge (ESTIMATED from the reference renders — the coupon tests this)
BEAM_W = 5.0            # mm, beam body width in plane (measured on both reference variants)
BEAM_COUNT = 2          # per side, as the reference
BEAM_SPACING = 12.0     # mm, Y pitch of the two beams of a side
PRETILT = 8.0           # deg, rest-state beam angle (ESTIMATED — the coupon tests this)
HINGE_W_THIN = 0.5      # mm, one 0.4 mm line at the neck (measured on the references)
HINGE_W_THICK = 0.8     # mm, two lines: the fallback if the 0.5 neck does not slice or tears
HINGE_LEN = 2.0         # mm, neck length along the beam
DEPTH = 6.35            # mm, print height (measured on the references)
SHUTTLE_W = 8.0         # mm, moving block width (X)
ANCHOR_W = 8.0          # mm, fixed block width (X) = frame side member thickness
MARGIN = 3.0            # mm, block Y overhang past the outer beams

ENV = bistable_envelope(SPAN, BEAM_W, BEAM_COUNT, BEAM_SPACING, PRETILT, SHUTTLE_W, ANCHOR_W, MARGIN)
RISE = ENV["rise"]              # mm, shuttle Y offset at rest (~5.15); mirror state at -RISE
TRAVEL = ENV["travel"]          # mm, between the two rest positions (~10.3)
BLOCK_H = ENV["block_h"]        # mm, Y height of shuttle and anchors
X_OUTER = ENV["x_outer"]        # mm, half the frame's outer X = anchor outer face

# --- frame: side members are the anchors, top and bottom rails close the loop ---
# The rails must stay continuous: the first print (2026-09-10) cut a slot clean through each rail for the
# plunger bar, which left two separate U-brackets joined only by the living hinges. The bar now runs under a
# tunnel through each rail instead: open to the bed, bridged on top, so the loop is one part.
RAIL_W = 6.0            # mm, rail thickness (Y); 6 so the bridge over the tunnel is a stiff 6 x CEILING_T section
CLEARANCE = 0.6         # mm, gap between the moving shuttle/plunger and anything fixed, both states, and above the bar
RAIL_Y = BLOCK_H / 2 + RISE + CLEARANCE + RAIL_W / 2   # rail centreline: clears the shuttle in either state
FRAME_H = 2 * RAIL_Y + RAIL_W                          # outer Y of the frame = side member height

# --- plunger: a bar under a tunnel through both rails so either end can be pressed to snap the shuttle ---
PLUNGER_W = 4.0         # mm, bar width (X)
BAR_H = 3.0             # mm, bar height (Z): shorter than the frame so the rail bridges over it (bar sits on the bed)
TUNNEL_W = PLUNGER_W + 2 * CLEARANCE                   # tunnel width through each rail (= bridge span, 5.2)
TUNNEL_H = BAR_H + CLEARANCE                           # tunnel height above the bed; the rail bridges from here to DEPTH
CEILING_T = DEPTH - TUNNEL_H                           # mm, rail material bridging over the bar (2.75): keeps the loop closed
KNOB_W = 12.0           # mm, finger pad width (X)
KNOB_H = 5.0            # mm, finger pad length (Y) beyond the rail face in the far state
PLUNGER_HALF = RAIL_Y + RAIL_W / 2 + RISE + KNOB_H + CLEARANCE   # the near pad clears the rail by CLEARANCE at rest (else it prints fused); the far pad clears by 2*RISE more
assert CEILING_T >= 2.0, "rail bridge over the plunger tunnel is too thin; lower BAR_H or raise DEPTH"
