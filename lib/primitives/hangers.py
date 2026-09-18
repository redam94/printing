"""Mounting cutouts: keyhole hangers and zip-tie slots."""
from __future__ import annotations

from build123d import Align, Box, Circle, Part, Pos, Rectangle, Sketch, extrude

from lib.component import MaterialNotes, component

_OVERSHOOT = 1.0


@component(
    id="primitives.keyhole_hanger", version="1.0.0",
    summary="Negative (subtract me) keyhole pocket for hanging on a screw head: round head pocket narrowing to a slot in +Y; mouth at z=0, pocket extends down.",
    tags=["keyhole", "hanger", "wall mount", "screw", "hang", "negative", "mount", "pocket"],
    units={"head_d": "mm", "shank_d": "mm", "slot_len": "mm", "depth": "mm", "clearance": "mm"},
    descriptions={
        "head_d": "screw head diameter (8 fits a #8 / M4 pan head)", "shank_d": "screw shank diameter the slot rides on",
        "slot_len": "slot length from the head-pocket centre in +Y (up, when hung)", "depth": "pocket depth below the mouth (head height + 1)",
        "clearance": "added to head_d and shank_d",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="pocket cut into the face that meets the wall; on a vertical face the round pocket roof is a short bridge (<= 10 mm) and prints clean",
        notes="UNVALIDATED: no test print yet. Slot must point up in use; screw the head out ~depth from the wall.",
    ),
)
def keyhole_hanger(head_d: float = 8.0, shank_d: float = 4.5, slot_len: float = 8.0, depth: float = 3.0, clearance: float = 0.6) -> Part:
    """Drawn in XY with the slot in +Y; rotate it so +Y is up on the mounting face.

    Example:
        # keyholes on a vertical back face at y = -spine_w, slot pointing +Z
        comb = comb - [Pos(x, -spine_w, z) * Rot(90, 0, 0) * keyhole_hanger() for x in (-25, 25)]
    """
    sk = Sketch() + Circle((head_d + clearance) / 2) + Pos(0, slot_len / 2) * Rectangle(shank_d + clearance, slot_len)
    sk = sk + Pos(0, slot_len) * Circle((shank_d + clearance) / 2)
    return Pos(0, 0, -depth) * extrude(sk, amount=depth + _OVERSHOOT)


@component(
    id="primitives.zip_tie_slot", version="1.0.0",
    summary="Negative (subtract me) pair of parallel slots through a wall for a cable tie loop; slots along Y, spaced along X, cutting through Z.",
    tags=["zip tie", "cable tie", "strap", "slot", "negative", "mount", "strain relief"],
    units={"tie_w": "mm", "tie_t": "mm", "spacing": "mm", "through": "mm", "clearance": "mm"},
    descriptions={
        "tie_w": "cable tie width (4.8 = common 4.8 mm tie)", "tie_t": "cable tie thickness",
        "spacing": "X distance between the two slot centres (the loop wraps whatever lies between)",
        "through": "cut length along Z, both ways from z=0 (exceed the wall thickness)", "clearance": "added to width and thickness",
    },
    material_notes=MaterialNotes(validated=[], orientation="any; slots are rectangular", notes="UNVALIDATED: no test print yet."),
)
def zip_tie_slot(tie_w: float = 4.8, tie_t: float = 1.6, spacing: float = 8.0, through: float = 20.0, clearance: float = 0.6) -> Part:
    """Example:
        spine = spine - Pos(x, y, 0) * zip_tie_slot(spacing=10, through=spine_w * 2)
    """
    slot = Box(tie_t + clearance, tie_w + clearance, 2 * through, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return Pos(-spacing / 2, 0, 0) * slot + Pos(spacing / 2, 0, 0) * slot
