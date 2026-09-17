"""PARAMETERS — couch-arm remote caddy (ticket PRINT-1). Every dimension lives here; model.py has no literals."""

# --- the couch arm (request: "couch arm 150 wide, 25 thick fabric-covered"; re-measured as 140 wide in r2) ---
ARM_W = 140.0            # mm, arm width across the top (PRINT-1 r2: requester re-measured, was 150)
ARM_CLEARANCE = 4.0      # mm, added to ARM_W so the saddle slides over padded fabric without dragging
ARM_SPAN = ARM_W + ARM_CLEARANCE   # mm, inside width of the saddle
ARM_ENVELOPE_H = 200.0   # mm, how far down the arm is modelled for the fit check (the sides of any couch arm)
# ASSUMED: "25 thick" is the padding, so the arm is treated as a square-edged block ARM_W wide.

# --- the remotes, as (width, thickness, length) from the request ---
REMOTES = (
    (45.0, 20.0, 180.0),
    (40.0, 18.0, 150.0),
    (38.0, 15.0, 140.0),
)
POCKET_DEPTH_FRAC = 0.4  # pocket depth as a fraction of each remote's length (PRINT-1 r2: was 0.5)
POCKET_CLEARANCE = 2.0   # mm, added to each remote's width and thickness (1 mm per side, drops in one-handed)
POCKET_CORNER_R = 3.0    # mm, vertical corner radius inside each pocket
POCKET_LEAD_IN = 1.2     # mm, 45 deg chamfer at each pocket rim
POCKET_WEB = 2.4         # mm, wall between pockets (6 perimeters)
POCKETS = tuple((w, t, round(length * POCKET_DEPTH_FRAC, 1)) for w, t, length in REMOTES)  # (x, y, depth) for pocket_array

# --- saddle and pocket block ---
PLATE_T = 3.2            # mm, saddle plate lying on the arm (8 perimeters' worth of stiffness across the span)
INNER_LEG_T = 3.2        # mm, leg down the seat side
INNER_LEG_H = 35.0       # mm, leg length below the arm top (stops the caddy sliding off outboard)
BLOCK_ARM_WALL = 3.2     # mm, block wall against the outboard side of the arm (it is the outer leg)
BLOCK_OUTER_WALL = 2.4   # mm, block wall facing the room
BLOCK_END_WALL = 3.2     # mm, block walls at both ends of the pocket row
BLOCK_FLOOR_T = 2.4      # mm, pocket floors (bridges in print orientation)
EDGE_R = 1.5             # mm, radius on every edge running along the arm except the saddle top: nothing sharp touches the fabric
BED_CHAMFER = 0.4        # mm, elephant-foot chamfer round the saddle top (the bed face)

# --- felt pads under the saddle ---
PAD_D = 12.0             # mm, stick-on felt / rubber dot diameter
PAD_DEPTH = 0.8          # mm, locating recess depth
PAD_INSET = 15.0         # mm, pad centre distance from the saddle's inner edges and ends
