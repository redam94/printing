"""Fridge-magnet bag clip: two jaws on a living hinge, a sealing rib, a snap catch and two magnets, printed flat.

Part: ``clip`` — printed open, 180 mm long: the lower jaw (90 x 20 x 3.2) and the upper jaw
(84 x 20 x 2.4) end to end with a 0.5 mm ``mechanisms.living_hinge_web`` between them. Fold the
upper jaw over: a half-round rib along the lower jaw (``mechanisms.snap_ridge``) presses the bag
into a matching channel in the upper jaw (``mechanisms.snap_groove``, 0.3 mm wider for the film),
and the upper jaw's tip snaps under a lip on the catch block at the lower jaw's end. The upper jaw
is the spring: pushing its tip down the lip's 45 deg ramp bows it, and it springs into the 0.8 mm
undercut. To open, push a thumb into the scoop at the tip toward the hinge and lift. Two 10 x 2 mm
disc magnets glued into pockets in the underside hold it on the fridge door.

Print flat as built, PETG (the living hinge is validated in PETG and TPU; PLA fatigue-cracks
within tens of folds). Fold once while the print is still warm. Declared ``hinged``: the 0.5 mm web
is the design, not a thin-wall defect. The catch block's undercut is a 0.8 mm deep, 2.8 mm tall
horizontal slot in a vertical face: it bridges without support.

Assumptions (user unavailable): sized for a 20 mm jaw and a ~2.4 mm bow-to-snap; magnets 10 x 2
(use MAGNET_H = 3 and JAW_T_LOW = 4.4 for 10 x 3); no text on the jaws.
"""
from build123d import Align, Box, Part, Plane, Polygon, Pos, RectangleRounded, Rot, extrude

from lib.fasteners.magnet_pocket import magnet_pocket
from lib.mechanisms.living_hinge import living_hinge_web
from lib.mechanisms.snap_fit import snap_groove, snap_ridge
from lib.primitives.notches import finger_notch

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P

# the 0.5 mm living-hinge web is the point of the part: sub-2x-nozzle walls are expected, not a defect
PRINT_MODES = {"clip": "hinged"}


def _plate(length: float, thickness: float, xc: float) -> Part:
    return Pos(xc, 0, 0) * extrude(RectangleRounded(length, P.JAW_W, P.CORNER_R), amount=thickness)


def _catch() -> Part:
    block = Box(P.CATCH_LEN, P.JAW_W, P.CATCH_H, align=(Align.MIN, Align.CENTER, Align.MIN))
    block = Pos(P.CATCH_X_OUT, 0, 0) * block
    undercut = Pos(P.CATCH_X_IN - P.LIP_OVER, 0, P.NOTCH_Z0) * Box(P.LIP_OVER + 1, P.JAW_W + 2, P.NOTCH_Z1 - P.NOTCH_Z0, align=(Align.MIN, Align.CENTER, Align.MIN))
    # 45 deg ramp on the lip's inner top edge: the descending tip rides it and bows the jaw
    ramp = extrude(Plane.XZ * Polygon((P.CATCH_X_IN + 1, P.CATCH_H + 1), (P.CATCH_X_IN + 1, P.CATCH_H - P.LIP_CHAMFER - 1),
                                      (P.CATCH_X_IN - P.LIP_CHAMFER, P.CATCH_H + 1), align=None), amount=P.JAW_W / 2 + 1, both=True)
    return block - undercut - ramp


def lower_jaw() -> Part:
    jaw = _plate(P.JAW_LEN_LOW, P.JAW_T_LOW, P.LOW_XC) + _catch()
    jaw = jaw + Pos(P.RIDGE_XC, 0, P.JAW_T_LOW) * Rot(90, 0, 0) * snap_ridge(length=P.RIDGE_LEN, r=P.RIDGE_R)
    magnets = [Pos(P.LOW_XC + sx * P.MAGNET_X, 0, 0) * Rot(180, 0, 0) * magnet_pocket(P.MAGNET_D, P.MAGNET_H, clearance=P.MAGNET_CLEAR) for sx in (-1, 1)]
    return jaw - magnets


def upper_jaw() -> Part:
    jaw = _plate(P.JAW_LEN_UP, P.JAW_T_UP, P.UP_XC)
    jaw = jaw - Pos(P.UP_XC, 0, P.JAW_T_UP) * Rot(90, 0, 0) * snap_groove(length=P.RIDGE_LEN + 2, r=P.RIDGE_R, clearance=P.GROOVE_CLEAR)
    tip_x = P.WEB_LEN / 2 + P.JAW_LEN_UP
    return jaw - Pos(tip_x, 0, P.JAW_T_UP / 2) * Rot(0, 0, 90) * finger_notch(width=P.SCOOP_W, depth=P.SCOOP_D)


def _hinge() -> Part:
    return living_hinge_web(width=P.JAW_W, web_thickness=P.WEB_T, web_length=P.WEB_LEN, panel_t=P.PANEL_T, panel_len=P.PANEL_LEN)


def build() -> dict[str, Part]:
    return {"clip": lower_jaw() + _hinge() + upper_jaw()}


def folded_upper() -> Part:
    """The upper jaw closed onto the lower one: mirrored through the hinge, its printed top face down on the bag gap."""
    return Pos(0, 0, P.JAW_T_LOW + P.BAG_GAP + P.JAW_T_UP) * Rot(0, 180, 0) * upper_jaw()


def fit_checks(parts: dict[str, Part]) -> dict[str, tuple[Part, Part]]:
    """Closed: the ridge must sit inside the groove and the tip must land in front of the catch, not in it."""
    return {"closed_upper_vs_lower": (folded_upper(), lower_jaw())}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
