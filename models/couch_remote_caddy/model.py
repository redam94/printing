"""Couch-arm remote caddy for three TV / streaming remotes (design request PRINT-1).

Part: ``caddy`` — one piece that sits over a padded couch arm with no screws or adhesive:
a saddle plate across the arm top, a short leg down the seat side, and a pocket block hanging down
the outboard side. The block holds three open-top pockets sized for the requested remotes
(45 x 20, 40 x 18 and 38 x 15 mm, plus 2 mm clearance) and as deep as 40% of each remote, so most of
every remote stays in reach. The remotes' weight pulls the block against the arm; the
seat-side leg stops the caddy sliding off.

Fabric protection: every edge that runs along the arm is rounded (EDGE_R) and the underside of the
saddle has four recesses for stick-on felt or rubber dots (PAD_D).

Print orientation: upside down, the saddle's top face and the pocket rims on the bed. The pocket
floors then bridge across each pocket's short side (at most 22 mm); everything else is vertical.
No supports.

Assumptions: the arm is 140 mm wide at the top (re-measured by the requester for quote r2) and
square-edged enough for a flat saddle; "25 thick" is read as the padding, so the saddle leaves 4 mm
of play across the arm.
The caddy follows the arm along 140 mm.
"""
from build123d import Align, Axis, Box, Part, Pos, Rot, chamfer, fillet

from lib.component import on_bed
from lib.primitives.feet import rubber_foot_recess
from lib.primitives.pocket_array import pocket_array, row_length

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P

_TOP = (Align.CENTER, Align.CENTER, Align.MAX)
_MIN_X_TOP = (Align.MIN, Align.CENTER, Align.MAX)
_MAX_X_TOP = (Align.MAX, Align.CENTER, Align.MAX)


def block_size() -> tuple[float, float, float]:
    """(X, Y, Z) of the pocket block: X away from the arm, Y along it."""
    x = P.BLOCK_ARM_WALL + max(t for _, t, _ in P.POCKETS) + P.POCKET_CLEARANCE + P.BLOCK_OUTER_WALL
    y = row_length(P.POCKETS, P.POCKET_WEB, P.POCKET_CLEARANCE) + 2 * P.BLOCK_END_WALL
    z = max(d for _, _, d in P.POCKETS) + P.BLOCK_FLOOR_T
    return x, y, z


def in_use() -> Part:
    """The caddy as it sits on the arm: arm top at z=0, arm centred on x=0 and running along Y."""
    bx, length, bz = block_size()
    half = P.ARM_SPAN / 2
    top = P.PLATE_T
    plate = Pos(-half - P.INNER_LEG_T, 0, top) * Box(P.ARM_SPAN + P.INNER_LEG_T, length, P.PLATE_T, align=_MIN_X_TOP)
    leg = Pos(-half, 0, top) * Box(P.INNER_LEG_T, length, P.INNER_LEG_H + P.PLATE_T, align=_MAX_X_TOP)
    block = Pos(half, 0, top) * Box(bx, length, bz, align=_MIN_X_TOP)
    body = plate + leg + block
    along = body.edges().filter_by(Axis.Y)
    on_top = along.group_by(Axis.Z)[-1]          # the saddle's top face: the bed face once flipped
    body = fillet([e for e in along if e not in on_top], P.EDGE_R)
    body = chamfer(body.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), P.BED_CHAMFER)

    pockets = Pos(half + P.BLOCK_ARM_WALL, 0, top) * Rot(0, 0, 90) * pocket_array(
        P.POCKETS, web=P.POCKET_WEB, clearance=P.POCKET_CLEARANCE, corner_r=P.POCKET_CORNER_R,
        lead_in=P.POCKET_LEAD_IN, align_y="max")
    pad = Rot(180, 0, 0) * rubber_foot_recess(P.PAD_D, depth=P.PAD_DEPTH)
    pad_x = (-half + P.PAD_INSET, half - P.PAD_INSET)
    pad_y = (-length / 2 + P.PAD_INSET, length / 2 - P.PAD_INSET)
    pads = [Pos(x, y, 0) * pad for x in pad_x for y in pad_y]
    return body - pockets - pads


def _to_print(shape, ref: Part):
    """Apply the print transform (upside down, dropped onto the bed) that turns ``ref`` into the printed part."""
    flipped = Rot(180, 0, 0) * ref
    return Pos(0, 0, -flipped.bounding_box().min.Z) * (Rot(180, 0, 0) * shape)


def build() -> dict[str, Part]:
    return {"caddy": on_bed(Rot(180, 0, 0) * in_use())}


def fit_checks(parts: dict[str, Part]) -> dict[str, tuple[Part, Part]]:
    """The arm (a block ARM_W wide below z=0) must not intersect the caddy."""
    _, length, _ = block_size()
    arm = Box(P.ARM_W, 2 * length, P.ARM_ENVELOPE_H, align=_TOP)
    return {"arm_vs_caddy": (parts["caddy"], _to_print(arm, in_use()))}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
