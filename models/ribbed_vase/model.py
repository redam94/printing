"""Ribbed desk vase: one part, printed in spiral / vase mode, axis vertical, base on the bed.

Borrowed from the reference photo brief (ideas/ribbed_desk_vase/inspiration): tall ~2:1 cylinder,
pronounced bulging shoulder, wide mouth, evenly spaced sharp-edged vertical flutes running from
just above the base through the shoulder to the rim, no fillets on the ribs.

Print: spiral / vase mode (Snapmaker Orca "Spiral vase"), 2-3 bottom layers, 0.4 nozzle, any
rigid filament; the slicer follows the fluted outer contour with a single perimeter.  Printed as a
normal shell instead, the wall is 2.0 mm between flutes and 0.8 mm under them.  The shoulder
leans out 28 deg and the mouth leans in 14 deg from vertical: both self-supporting.  Not
watertight for water without a sealant (single wall); fine for dried stems or a glass insert.

Assumptions (user unavailable): sizes from the brief's proportions, 150 mm tall; 28 flutes so the
ribs and grooves are about equal width at the body; flutes straight (FLUTE_TWIST = 0).
"""
from build123d import Part

from lib.form.revolved import revolved_body, shell_open_top
from lib.form.surface import flutes

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P

PRINT_MODES = {"vase": "vase"}   # scripts/check_printable.py applies the single-wall rules


def build() -> dict[str, Part]:
    solid = revolved_body(P.PROFILE, smooth=True, tangents=P.PROFILE_TANGENTS)
    shell = shell_open_top(solid, wall=P.WALL)
    vase = flutes(shell, count=P.FLUTE_COUNT, width=P.FLUTE_WIDTH, depth=P.FLUTE_DEPTH, z_from=P.FLUTE_Z0,
                  twist_angle=P.FLUTE_TWIST, reference=solid)
    return {"vase": vase}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
