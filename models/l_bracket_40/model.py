"""40 mm L-bracket with three M3 clearance holes per arm, 4 mm thick, 20 mm wide.

Part: ``bracket`` — ``primitives.l_bracket`` at the parameters in params.py. Fits M3 socket-head
or pan-head screws (3.6 mm printed hole = ISO 273 medium 3.4 + 0.2 oversize).

Print orientation: on its side, i.e. the L profile lies in the bed plane and the 20 mm width is
the print height, so bending load at the corner runs along the layers instead of across them.
Consequently every hole is horizontal and is cut as a teardrop (point up) so it bridges cleanly.

Assumptions (user not available): width 20 mm; holes evenly spread over the free span of each arm
(centres 10 / 22 / 34 mm from the outer corner, on the width centreline); sharp outer corner;
1 mm inside fillet; no counterbores.
"""
from build123d import Part

from lib.primitives.l_bracket import l_bracket

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def build() -> dict[str, Part]:
    bracket = l_bracket(
        P.ARM_LEN, P.ARM_LEN, thickness=P.THICKNESS, width=P.WIDTH,
        size=P.SCREW, holes_per_arm=P.HOLES_PER_ARM, hole_pitch=P.HOLE_PITCH, hole_style=P.HOLE_STYLE,
        fit=P.HOLE_FIT, print_oversize=P.HOLE_OVERSIZE,
        inner_r=P.INNER_R, outer_r=P.OUTER_R, bottom_chamfer=P.BED_CHAMFER,
    )
    return {"bracket": bracket}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
