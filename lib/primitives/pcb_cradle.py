"""Edge-slot cradle for PCBs without mounting holes (ESP32 dev kits, etc.)."""
from __future__ import annotations

from build123d import Align, Box, Part, Pos

from lib.component import MaterialNotes, component

_ALIGN_BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@component(
    id="primitives.pcb_slot_cradle", version="1.0.0",
    summary="Pair of rails with slots that grip a PCB by its two long edges (for boards with no mount holes), centred on the origin.",
    tags=["pcb", "cradle", "rails", "slot", "esp32", "holder", "card guide"],
    units={"board_l": "mm", "board_w": "mm", "pcb_t": "mm", "rail_h": "mm", "rail_t": "mm", "slot_depth": "mm",
           "clearance": "mm", "slot_z": "mm"},
    descriptions={
        "board_l": "PCB length along the rails (X)", "board_w": "PCB width across the rails (Y)", "pcb_t": "PCB thickness",
        "rail_h": "total rail height", "rail_t": "rail wall thickness outside the slot", "slot_depth": "how far the slot bites in over each edge",
        "clearance": "added to pcb_t (slot height) and to board_w (slot span)", "slot_z": "height of the slot floor above z=0",
    },
    material_notes=MaterialNotes(validated=["PLA"], orientation="rails vertical; slot faces are then vertical walls, no bridging",
                                 notes="Board slides in from the +X end; leave that end open in the enclosure or make one rail cantilevered."),
)
def pcb_slot_cradle(board_l: float = 54.4, board_w: float = 27.9, pcb_t: float = 1.6, rail_h: float = 6.0, rail_t: float = 1.6,
                    slot_depth: float = 1.5, clearance: float = 0.3, slot_z: float = 3.0) -> Part:
    """Example:
        cradle = pcb_slot_cradle(*esp32_dims)
        body = body + Pos(0, 0, floor_t) * cradle
    """
    span = board_w + clearance
    rail_w = rail_t + slot_depth
    slot_h = pcb_t + clearance
    rails = Part()
    for sign in (1, -1):
        y_outer = sign * (span / 2 - slot_depth + rail_w / 2)
        rail = Pos(0, y_outer, 0) * Box(board_l, rail_w, rail_h, align=_ALIGN_BOTTOM)
        slot = Pos(0, sign * (span / 2 - slot_depth / 2), slot_z) * Box(board_l + 2, slot_depth + 0.01, slot_h, align=_ALIGN_BOTTOM)
        rails = rails + (rail - slot)
    return rails
