"""ESP32 development-board footprints.

Most ESP32 dev kits have NO mounting holes.  These components give the board
outline and header-row positions so an enclosure can hold the board by its
edges (see ``primitives.pcb_slot_cradle``) or by the header pins.
"""
from __future__ import annotations

from dataclasses import dataclass

from build123d import Pos, Rectangle, RectangleRounded, Sketch

from lib.component import MaterialNotes, component


@dataclass(frozen=True)
class Esp32Board:
    name: str
    length: float        # along the header rows (X)
    width: float         # across the header rows (Y)
    row_spacing: float   # centre-to-centre between the two header rows
    pins_per_row: int
    pin_pitch: float
    pcb_t: float
    usb: str             # connector type at the -X end
    module_h: float      # tallest component height above PCB (the shield can)
    corner_r: float = 1.0


ESP32_BOARDS: dict[str, Esp32Board] = {
    # length = overall including antenna overhang (DevKitC V4: 48.26 PCB + 6.04 antenna). See hardware_dimensions.md.
    "devkitc_v4":    Esp32Board("ESP32-DevKitC V4 (38 pin)",       54.3, 27.94, 25.40, 19, 2.54, 1.6, "micro-USB", 3.2),
    "s3_devkitc_1":  Esp32Board("ESP32-S3-DevKitC-1 v1.1 (44 pin)", 62.74, 25.40, 22.86, 22, 2.54, 1.6, "2x micro-USB", 3.2),
    "nodemcu_32s":   Esp32Board("NodeMCU-32S (38 pin)",            48.26, 25.40, 22.86, 19, 2.54, 1.6, "micro-USB", 3.2),
    "doit_v1_30":    Esp32Board("DOIT ESP32 DevKit V1 (30 pin) [UNVERIFIED dims]", 51.8, 28.2, 25.4, 15, 2.54, 1.6, "micro-USB", 3.2),
    "c3_supermini":  Esp32Board("ESP32-C3 SuperMini [secondary source]", 22.5, 18.0, 15.24, 8, 2.54, 1.0, "USB-C", 2.5),
}


@component(
    id="patterns.esp32_footprint", version="1.0.0",
    summary="ESP32 dev-board PCB outline (no mount holes exist on these boards) centred on the origin, USB end at -X.",
    tags=["esp32", "devkitc", "doit", "esp32-s3", "esp32-c3", "supermini", "footprint", "outline", "pcb", "microcontroller"],
    units={"board": "enum", "clearance": "mm"},
    descriptions={"board": "devkitc_v4, s3_devkitc_1, nodemcu_32s, doit_v1_30, c3_supermini", "clearance": "grown outward on all sides"},
    material_notes=MaterialNotes(validated=["PLA"], orientation="any (2D pattern)",
                                 notes="Boards have no holes: hold by edge slots (pcb_slot_cradle) or header sockets."),
)
def esp32_footprint(board: str = "devkitc_v4", clearance: float = 0.0) -> Sketch:
    """Example:
        pocket = extrude(esp32_footprint("devkitc_v4", clearance=0.5), amount=pcb_t)
    """
    b = ESP32_BOARDS[board]
    return Sketch() + RectangleRounded(b.length + 2 * clearance, b.width + 2 * clearance, b.corner_r + clearance)


@component(
    id="patterns.esp32_header_rows", version="1.0.0",
    summary="Two rectangular strips where the ESP32 dev-board header rows sit (for pin-clearance pockets or socket recesses).",
    tags=["esp32", "header", "pins", "2.54", "pocket", "keep-out"],
    units={"board": "enum", "strip_width": "mm", "extra_length": "mm"},
    descriptions={"board": "devkitc_v4, s3_devkitc_1, nodemcu_32s, doit_v1_30, c3_supermini", "strip_width": "width of each strip across the pins",
                  "extra_length": "added to the strip length beyond the pin run"},
    material_notes=MaterialNotes(validated=["PLA"], orientation="any (2D pattern)"),
)
def esp32_header_rows(board: str = "devkitc_v4", strip_width: float = 3.0, extra_length: float = 1.0) -> Sketch:
    """Example:
        floor = floor - extrude(esp32_header_rows(), amount=pin_len)
    """
    b = ESP32_BOARDS[board]
    run = b.pins_per_row * b.pin_pitch + extra_length
    return Sketch() + [Pos(0, y) * Rectangle(run, strip_width) for y in (b.row_spacing / 2, -b.row_spacing / 2)]
