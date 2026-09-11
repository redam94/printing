"""Test coupons for ``mechanisms.bistable_beam_pair``: the mechanism in a frame, with a plunger to snap it.

Parts: ``coupon_h05`` (0.5 mm living-hinge necks, one 0.4 mm line: the reference geometry) and
``coupon_h08`` (0.8 mm necks, two lines: the fallback). Everything else is identical: a rectangular
frame whose side members are the component's anchors, a bar that runs under a tunnel through each
rail so the shuttle can be pressed from either side, and finger pads on both ends of the bar.

The frame is one closed loop. The first print (2026-09-10) failed because the plunger slots cut
each rail clean through, leaving two separate side brackets held together only by the living
hinges. Now the bar is 3 mm tall on the bed and each rail keeps a 2.75 mm bridge over it: the
tunnel is open to the bed (so the bar prints in place without support) and closed on top, 5.2 mm
of bridging per rail. The pads and the shuttle stay full height.

Print flat as built (bed at z=0, 6.35 mm tall), beams and necks in the bed plane. Enable thin-wall
/ Arachne perimeters for the 0.5 mm part. Print one of each in PETG first; the reference authors
recommend polypropylene and PLA is expected to creep. The test: press a pad, does it snap and stay;
press the other, does it come back; after 50 cycles, are the necks whitening. Record the result on
the review page as a print report so ``lib/validation.json`` gains the evidence and the component's
``material_notes`` can be set.

Assumptions: span 37 mm and pre-tilt 8 deg are estimated from the reference renders (the coupon
tests them); plunger and pads are sized for a finger, not for any hardware. Idea:
``ideas/bistable_compliant_switch``.
"""
from build123d import Align, Box, Part, Pos

from lib.mechanisms.bistable import bistable_beam_pair

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P

# the 0.5 / 0.8 mm necks are the point of the part: sub-2x-nozzle walls are expected, not a defect
PRINT_MODES = {"coupon_h05": "hinged", "coupon_h08": "hinged"}


def _frame() -> Part:
    """Side members over the anchors plus two continuous rails, each with a tunnel the plunger bar runs under.

    The tunnel is cut from below the bed up to TUNNEL_H, so the rail keeps CEILING_T of material bridging
    over the bar and the frame stays one closed loop (a through-slot here is what broke the first print).
    """
    side = Box(P.ANCHOR_W, P.FRAME_H, P.DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    rail = Box(2 * P.X_OUTER, P.RAIL_W, P.DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    tunnel = Box(P.TUNNEL_W, P.RAIL_W + 2, P.TUNNEL_H + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    frame = Pos(-(P.X_OUTER - P.ANCHOR_W / 2), 0, 0) * side + Pos(P.X_OUTER - P.ANCHOR_W / 2, 0, 0) * side
    for sy in (-1, 1):
        frame = frame + Pos(0, sy * P.RAIL_Y, 0) * rail
    for sy in (-1, 1):
        frame = frame - Pos(0, sy * P.RAIL_Y, -1) * tunnel
    return frame


def _plunger() -> Part:
    """Low bar under both rail tunnels with a full-height finger pad at each end, attached to the shuttle at rest."""
    bar = Box(P.PLUNGER_W, 2 * P.PLUNGER_HALF, P.BAR_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pad = Box(P.KNOB_W, P.KNOB_H, P.DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    mover = bar + Pos(0, P.PLUNGER_HALF - P.KNOB_H / 2, 0) * pad + Pos(0, -(P.PLUNGER_HALF - P.KNOB_H / 2), 0) * pad
    return Pos(0, P.RISE, 0) * mover


def _coupon(hinge_w: float) -> Part:
    stage = bistable_beam_pair(
        span=P.SPAN, beam_width=P.BEAM_W, beam_count=P.BEAM_COUNT, beam_spacing=P.BEAM_SPACING, pretilt=P.PRETILT,
        hinge_width=hinge_w, hinge_length=P.HINGE_LEN, depth=P.DEPTH, shuttle_w=P.SHUTTLE_W, anchor_w=P.ANCHOR_W, margin=P.MARGIN,
    )
    return _frame() + stage + _plunger()


def build() -> dict[str, Part]:
    return {"coupon_h05": _coupon(P.HINGE_W_THIN), "coupon_h08": _coupon(P.HINGE_W_THICK)}


def fit_checks(parts: dict[str, Part]) -> dict[str, tuple[Part, Part]]:
    """The frame must clear the moving parts in the snapped state too, not just as built."""
    shuttle = Pos(0, P.RISE, 0) * Box(P.SHUTTLE_W, P.BLOCK_H, P.DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    mover_rest = _plunger() + shuttle
    mover_snapped = Pos(0, -P.TRAVEL, 0) * mover_rest
    # grow the frame by the clearance (in Y, and downward in Z for the tunnel ceiling over the bar) so a
    # mover that merely touches (and would print fused) also fails
    frame = _frame()
    fat_frame = frame + Pos(0, P.CLEARANCE / 2, 0) * frame + Pos(0, -P.CLEARANCE / 2, 0) * frame + Pos(0, 0, -P.CLEARANCE / 2) * frame
    return {"frame_vs_mover_rest": (fat_frame, mover_rest), "frame_vs_mover_snapped": (fat_frame, mover_snapped)}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
