"""PARAMETERS — 40 mm L-bracket, M3. Every dimension lives here; model.py has no literals."""

# --- bracket envelope ---
ARM_LEN = 40.0          # mm, each arm from the outer corner to its free end (both arms equal)
THICKNESS = 4.0         # mm, arm thickness (10 perimeters at 0.4 nozzle)
WIDTH = 20.0            # mm, bracket width = print height (ASSUMED: user did not specify)

# --- holes: one row of three per arm ---
SCREW = "M3"
HOLES_PER_ARM = 3
HOLE_PITCH = None       # mm; None = spread evenly over the arm span beyond the other arm (12 mm here)
HOLE_STYLE = "teardrop" # holes are horizontal in print orientation; teardrop bridges without support
HOLE_FIT = "medium"     # ISO 273 medium: 3.4 mm for M3
HOLE_OVERSIZE = 0.2     # mm, FDM compensation -> 3.6 mm printed hole

# --- edges ---
INNER_R = 1.0           # mm, inside-corner fillet (vertical edge in print orientation)
OUTER_R = 0.0           # mm, outside corner left sharp so the bracket seats flush in a corner
BED_CHAMFER = 0.4       # mm, elephant-foot chamfer on the bed edge loop
