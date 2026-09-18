"""PARAMETERS — print-in-place folding phone stand. Every dimension lives here; model.py has no literals."""

# --- plates ---
PLATE_T = 4.0           # mm, every plate (base, rest, prop) and the hinge leaves
BASE_W = 90.0           # mm, base width (X) including the two front ears
BASE_D = 60.0           # mm, base depth (Y) between the two hinge axes
HINGE_LEN = 60.0        # mm, both hinges, = rest and prop width
REST_L = 50.0           # mm, rest plate beyond its hinge stub
PROP_L = 71.0           # mm, prop plate beyond its hinge stub (long enough for the last notch)
CORNER_R = 4.0          # mm, plan-view radius on the free corners of rest and prop

# --- hinges (mechanisms.pip_hinge), both axes along X at z = HUB_D / 2 ---
KNUCKLES = 7
PIN_D = 3.0
HUB_D = 7.0
CLEAR = 0.35            # mm, pin bore and knuckle gaps
LEAF_LEN = 6.0          # mm, hinge stubs (buried in the plates)
HINGE_INNER = HUB_D / 2 + CLEAR      # mm, where a leaf stops short of the other side's knuckles (3.85)
FRONT_Y = -BASE_D / 2   # mm, front hinge axis: rest (-Y, leaf A) | base (+Y, leaf B)
REAR_Y = BASE_D / 2     # mm, rear hinge axis: base (-Y, leaf A) | prop (+Y, leaf B)
AXIS_Z = HUB_D / 2

# --- base: the plate between the hinges plus two ears in front of the front hinge that carry the phone lip ---
BASE_Y0 = FRONT_Y + HINGE_INNER      # mm, base plate spans BASE_Y0 .. BASE_Y1 between the hinges
BASE_Y1 = REAR_Y - HINGE_INNER
EAR_CLEAR = 0.5         # mm, between an ear's inner face and the rest / hinge ends
EAR_X0 = HINGE_LEN / 2 + EAR_CLEAR   # mm, ears occupy |x| in EAR_X0 .. BASE_W / 2
EAR_W = BASE_W / 2 - EAR_X0          # mm, each ear's width (14.5)
EAR_FRONT_Y = FRONT_Y - 15.0         # mm, ears reach this far forward of the front axis
LIP_D = 5.0             # mm, phone lip depth (Y) at the front of each ear
LIP_H = 8.0             # mm, lip height above the ear's top face
FOOT_D = 8.0            # mm, stick-on rubber feet under the base
FOOT_X = 38.0
FOOT_Y = 18.0

# --- rest: the plate the phone leans on (its printed underside faces the phone) ---
REST_Y1 = FRONT_Y - HINGE_INNER      # mm, rest plate spans REST_Y1 - REST_L .. REST_Y1
# --- prop: the plate with the notch rack the rest's tip drops into (rack on its printed top face) ---
PROP_Y0 = REAR_Y + HINGE_INNER       # mm, prop plate spans PROP_Y0 .. PROP_Y0 + PROP_L
NOTCHES = 3
NOTCH_PITCH = 8.0       # mm; with REST_L + HINGE_INNER = 53.85 from the front axis, notches at 53 / 61 / 69 from the rear axis give ~55 / 65 / 75 deg
NOTCH_S_MID = 61.0      # mm, middle notch distance from the rear axis
NOTCH_W = PLATE_T + 0.6 # mm, the rest's 4 mm tip plus play
NOTCH_DEPTH = 2.0
NOTCH_LEAD = 0.8
NOTCH_LEN = HINGE_LEN + 2
assert PROP_Y0 + PROP_L >= REAR_Y + NOTCH_S_MID + NOTCH_PITCH + NOTCH_W / 2 + NOTCH_LEAD + 2, "prop too short for the last notch"

# --- the open pose used by the fit check: rest leaning back at this angle from the base ---
CHECK_ANGLE = 65.0      # deg
EPS = 0.01              # mm, overlap so unions share volume rather than a face
