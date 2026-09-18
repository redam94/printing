"""Pockets for disc magnets."""
from __future__ import annotations

from build123d import Align, Cylinder, Part, Pos

from lib.component import MaterialNotes, component

_OVERSHOOT = 1.0


@component(
    id="fasteners.magnet_pocket", version="1.0.0",
    summary="Negative (subtract me) blind pocket for a disc magnet, press- or glue-fit; mouth at z=0, pocket extends down.",
    tags=["magnet", "neodymium", "disc", "pocket", "fridge", "negative", "closure", "lid"],
    units={"d": "mm", "h": "mm", "clearance": "mm", "floor": "mm"},
    descriptions={
        "d": "magnet diameter (10 x 3 and 6 x 3 discs are the common ones)", "h": "magnet height",
        "clearance": "added to the diameter; 0.2 press-fits in PLA/PETG, 0.4 leaves room for glue",
        "floor": "extra depth so the magnet sits this far below the mouth (0 = flush)",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="mouth up (flat floor) or mouth on the bed (the magnet is inserted after printing; the pocket is then a recess in the first layers)",
        notes="UNVALIDATED: no test print yet. Magnets pressed in warm PETG hold without glue; in PLA use a drop of CA.",
    ),
)
def magnet_pocket(d: float = 10.0, h: float = 3.0, clearance: float = 0.2, floor: float = 0.0) -> Part:
    """Example:
        jaw = jaw - Pos(x, y, 0) * magnet_pocket(10, 3)            # from the bed face up
        lid = lid - Pos(x, y, lid_t) * magnet_pocket(6, 3, floor=0.4)   # from the top face down
    """
    depth = h + floor
    return Pos(0, 0, -depth) * Cylinder((d + clearance) / 2, depth + _OVERSHOOT, align=(Align.CENTER, Align.CENTER, Align.MIN))
