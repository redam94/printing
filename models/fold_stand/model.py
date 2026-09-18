"""Print-in-place folding phone stand: three plates on two pin hinges, angle set by a notch rack.

Part: ``stand`` — one print, three pieces that come off the bed already hinged together:
  * the base (90 x 60 x 4) with four rubber-foot recesses underneath and two ears in front that
    carry an 8 mm lip for the phone's bottom edge;
  * the rest (60 x 50 x 4), hinged along the base's front edge, that the phone leans on;
  * the prop (60 x 71 x 4), hinged along the base's rear edge, with three notches across its face.
Lift the rest, swing the prop forward over it and drop the rest's top edge into a notch: the two
plates brace each other as an A-frame, and the notch picks the angle (about 55, 65 or 75 degrees
from the desk). Fold both flat to carry it. Both hinges are ``mechanisms.pip_hinge`` (7 mm
knuckles on a 3 mm pin, 0.35 mm clearance, teardrop bores) and the rack is ``primitives.notch_rack``.

Printed flat, everything on the bed: the rest lies between the ears, the prop beyond the base.
Nothing flexes, so PLA is fine; PETG is also fine. Free both hinges with a firm twist as soon as
the print is off the bed. The part reports as three bodies: that is the two hinges.

Assumptions (user unavailable): phones 65 to 85 mm wide (the bottom corners sit on the ears'
lips); no cable slot; hinge length 60 leaves 14.5 mm ears either side.
"""
from build123d import Align, Box, Part, Pos, RectangleRounded, Rot, extrude

from lib.mechanisms.pip_hinge import pip_hinge_halves
from lib.primitives.feet import rubber_foot_recess
from lib.primitives.notches import notch_rack

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def _hinge(y_axis: float) -> tuple[Part, Part]:
    a, b = pip_hinge_halves(length=P.HINGE_LEN, knuckles=P.KNUCKLES, pin_d=P.PIN_D, hub_d=P.HUB_D, clearance=P.CLEAR,
                            leaf_len=P.LEAF_LEN, leaf_t=P.PLATE_T)
    return Pos(0, y_axis, 0) * a, Pos(0, y_axis, 0) * b


def _rounded_plate(width: float, y0: float, y1: float) -> Part:
    """A plate spanning y0..y1 with the far corners (at y1 if y1 is the free end) rounded; hinge-end corners are square."""
    length = y1 - y0
    plate = extrude(RectangleRounded(width, length + 2 * P.CORNER_R, P.CORNER_R), amount=P.PLATE_T)
    return Pos(0, (y0 + y1) / 2, 0) * plate


def pieces() -> tuple[Part, Part, Part]:
    """(rest, base, prop) as three separate solids."""
    front_a, front_b = _hinge(P.FRONT_Y)
    rear_a, rear_b = _hinge(P.REAR_Y)
    # rest: free end at REST_Y1 - REST_L, square end buried in the front hinge's leaf A
    rest_plate = _rounded_plate(P.HINGE_LEN, P.REST_Y1 - P.REST_L, P.REST_Y1) & Box(P.HINGE_LEN, P.REST_L + P.EPS, P.PLATE_T, align=(Align.CENTER, Align.MAX, Align.MIN)).moved(Pos(0, P.REST_Y1, 0))
    rest = front_a + rest_plate
    # base: full-width plate between the hinges; in front of the front hinge only the two ears continue, beside the rest
    base_plate = Box(P.BASE_W, P.BASE_Y1 - P.BASE_Y0 + P.EPS, P.PLATE_T, align=(Align.CENTER, Align.MIN, Align.MIN)).moved(Pos(0, P.BASE_Y0, 0))
    ears = Part()
    for sx in (-1, 1):
        x_in = sx * P.EAR_X0
        ax = Align.MIN if sx > 0 else Align.MAX
        ear = Box(P.EAR_W, P.BASE_Y0 - P.EAR_FRONT_Y + P.EPS, P.PLATE_T, align=(ax, Align.MIN, Align.MIN)).moved(Pos(x_in, P.EAR_FRONT_Y, 0))
        lip = Box(P.EAR_W, P.LIP_D, P.PLATE_T + P.LIP_H, align=(ax, Align.MIN, Align.MIN)).moved(Pos(x_in, P.EAR_FRONT_Y, 0))
        ears = ears + ear + lip
    base = front_b + base_plate + rear_a + ears
    feet = [Pos(sx * P.FOOT_X, sy * P.FOOT_Y, 0) * Rot(180, 0, 0) * rubber_foot_recess(P.FOOT_D) for sx in (-1, 1) for sy in (-1, 1)]
    base = base - feet
    # prop: square end buried in the rear hinge's leaf B, rounded free end, notch rack on the top face
    prop_plate = _rounded_plate(P.HINGE_LEN, P.PROP_Y0, P.PROP_Y0 + P.PROP_L) & Box(P.HINGE_LEN, P.PROP_L + P.EPS, P.PLATE_T, align=(Align.CENTER, Align.MIN, Align.MIN)).moved(Pos(0, P.PROP_Y0, 0))
    prop = rear_b + prop_plate
    prop = prop - Pos(0, P.REAR_Y + P.NOTCH_S_MID, P.PLATE_T) * notch_rack(count=P.NOTCHES, pitch=P.NOTCH_PITCH, width=P.NOTCH_W, depth=P.NOTCH_DEPTH,
                                                                             length=P.NOTCH_LEN, lead_in=P.NOTCH_LEAD)
    return rest, base, prop


def build() -> dict[str, Part]:
    rest, base, prop = pieces()
    return {"stand": rest + base + prop}


def fit_checks(parts: dict[str, Part]) -> dict[str, tuple[Part, Part]]:
    """Both hinges must be free as printed, and the raised rest must clear the ears and lips."""
    rest, base, prop = pieces()
    # rest leaning back at CHECK_ANGLE: rotate about the front axis (x-axis at y=FRONT_Y, z=AXIS_Z)
    raised = Pos(0, P.FRONT_Y, P.AXIS_Z) * Rot(-(180 - P.CHECK_ANGLE), 0, 0) * Pos(0, -P.FRONT_Y, -P.AXIS_Z) * rest
    return {"front_hinge_free": (rest, base), "rear_hinge_free": (base, prop), "rest_raised_clears_ears": (raised, base)}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
