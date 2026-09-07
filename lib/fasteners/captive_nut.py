"""Captive hex-nut slots (nut slides in from the side, screw comes through)."""
from __future__ import annotations

from build123d import Align, Box, Cylinder, Part, Pos, RegularPolygon, extrude

from lib.component import MaterialNotes, component
from lib.fasteners.hardware import screw

_ALIGN_BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@component(
    id="fasteners.captive_nut_slot",
    version="1.0.0",
    summary="Negative (subtract me) side-entry slot for a captive hex nut plus the screw clearance hole.",
    tags=["nut", "captive", "hex", "slot", "trap", "negative", "M3", "M4"],
    units={"size": "enum", "slot_length": "mm", "nut_clearance": "mm", "thickness_clearance": "mm",
           "screw_depth_above": "mm", "screw_depth_below": "mm", "screw_oversize": "mm"},
    descriptions={
        "size": "nut size: M2, M2.5, M3, M4, M5",
        "slot_length": "how far the entry slot runs from the nut centre in +X (reach the part's edge)",
        "nut_clearance": "added across flats so the nut slides in",
        "thickness_clearance": "added to nut thickness",
        "screw_depth_above": "screw clearance hole length in +Z above the nut",
        "screw_depth_below": "screw clearance hole length in -Z below the nut",
        "screw_oversize": "FDM oversize on the screw hole",
    },
    material_notes=MaterialNotes(
        validated=["PETG", "PLA"],
        orientation="nut axis vertical; if the slot roof is a horizontal bridge keep slot_length short or add a sacrificial layer",
    ),
)
def captive_nut_slot(
    size: str = "M3",
    slot_length: float = 10.0,
    nut_clearance: float = 0.3,
    thickness_clearance: float = 0.3,
    screw_depth_above: float = 10.0,
    screw_depth_below: float = 10.0,
    screw_oversize: float = 0.3,
) -> Part:
    """Cutter centred on the nut, nut mid-plane at z=0, slot running in +X.

    Example:
        body = body - Pos(x, y, z_nut) * captive_nut_slot("M3", slot_length=wall_to_edge)
    """
    s = screw(size)
    af = s.nut_af + nut_clearance
    t = s.nut_h + thickness_clearance
    # hexagon with flats parallel to X so it slides along X
    hex_r = af / 2 / (3 ** 0.5 / 2)  # across-corners radius from across-flats
    nut = extrude(RegularPolygon(hex_r, 6, rotation=30), amount=t / 2, both=True)
    slot = Pos(slot_length / 2, 0, 0) * Box(slot_length, af, t)
    hole_d = s.clearance_medium + screw_oversize
    hole = Pos(0, 0, -screw_depth_below) * Cylinder(hole_d / 2, screw_depth_below + screw_depth_above, align=_ALIGN_BOTTOM)
    return nut + slot + hole
