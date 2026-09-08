"""PARAMETERS — ribbed desk vase (ideas/ribbed_desk_vase): tall fluted cylinder with a fat shoulder.

Every dimension lives here; model.py has no numeric literals.  Axis = Z, base on the bed.  The
profile is (radius, z) from the base rim to the mouth; lib.form.revolved_body splines through it.
"""

# --- overall form (from the inspiration brief: ~2:1 height to width, bulging shoulder, wide mouth) ---
HEIGHT = 150.0
BASE_R = 30.0              # base rim radius
BODY_R = 31.0              # straight body radius below the shoulder
SHOULDER_R = 46.0          # the fat shoulder
MOUTH_R = 38.0             # rim radius at the opening
BODY_TOP_Z = 88.0          # where the body starts swelling into the shoulder
SHOULDER_Z = 118.0         # height of the widest point
PROFILE = (                # (r, z) walking up the outside; the extra collinear body points stop the spline waisting
    (BASE_R, 0.0),
    (BODY_R, 25.0),
    (BODY_R, 55.0),
    (BODY_R, BODY_TOP_Z),
    (BODY_R + 1.5, 94.0),    # dense points through the bend keep the spline from waisting the body
    (BODY_R + 5.0, 100.0),
    (BODY_R + 10.0, 107.0),
    (SHOULDER_R, SHOULDER_Z),
    (MOUTH_R + 4.0, 138.0),
    (MOUTH_R, HEIGHT),
)
PROFILE_TANGENTS = ((0.0, 1.0), (-0.35, 1.0))   # vertical at the base; leaning in at the mouth

# --- wall: printed in spiral (vase) mode the slicer lays ONE perimeter along the outer contour, so
#     the geometric wall only matters if someone prints it as a normal shell (then 2.0 - 1.2 = 0.8 under a flute)
WALL = 2.0

# --- vertical flutes: sharp-edged grooves, negative space as wide as the ribs ---
FLUTE_COUNT = 28
FLUTE_WIDTH = 3.2          # groove width; rib between grooves ~ (2*pi*BODY_R / 28) - 3.2 = 3.8 at the body
FLUTE_DEPTH = 1.2
FLUTE_Z0 = 4.0             # grooves start above the elephant-foot zone
FLUTE_TWIST = 0.0          # deg over the height; 0 = straight ribs like the reference photo
