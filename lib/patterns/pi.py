"""Raspberry Pi mounting-hole patterns and board outlines.

Coordinate convention for every Pi component here: the origin is the CENTRE
OF THE HOLE PATTERN, +X points toward the USB/Ethernet end of the board
(Pi 4/5) or the USB end (Zero), +Y toward the GPIO header edge.  Because the
holes are 3.5 mm from the SD-card end but 23.5 mm from the USB end on a
Pi 4/5, the board outline is offset in +X relative to the pattern — use
``pi_board_outline`` and the mounts together and they line up.
"""
from __future__ import annotations

from dataclasses import dataclass

from build123d import Circle, GridLocations, Pos, RectangleRounded, Sketch

from lib.component import MaterialNotes, component


@dataclass(frozen=True)
class PiBoard:
    name: str
    length: float        # board X
    width: float         # board Y
    corner_r: float
    hole_dx: float       # hole spacing X
    hole_dy: float       # hole spacing Y
    hole_edge: float     # hole centre distance from the SD end and from both long edges
    hole_d: float        # PCB hole diameter (M2.5 clearance)
    pcb_t: float

    @property
    def outline_offset_x(self) -> float:
        """X offset of board centre relative to hole-pattern centre."""
        return self.length / 2 - (self.hole_edge + self.hole_dx / 2)


PI_BOARDS: dict[str, PiBoard] = {
    "pi5":     PiBoard("Raspberry Pi 5",        85.0, 56.0, 3.0, 58.0, 49.0, 3.5, 2.7, 1.6),
    "pi4":     PiBoard("Raspberry Pi 4 B",      85.0, 56.0, 3.0, 58.0, 49.0, 3.5, 2.7, 1.6),
    "pi3":     PiBoard("Raspberry Pi 3 B/B+",   85.0, 56.0, 3.0, 58.0, 49.0, 3.5, 2.7, 1.6),
    "pi_zero": PiBoard("Raspberry Pi Zero/2 W", 65.0, 30.0, 3.0, 58.0, 23.0, 3.5, 2.75, 1.6),
}

# Pi 5 Active Cooler push-pin holes, relative to the hole-pattern centre
PI5_COOLER_HOLE_D = 3.0
PI5_COOLER_HOLE_X = 29.0     # 61.5 - 32.5 from the board drawing
PI5_COOLER_HOLE_Y = 18.5     # (46.5 - 9.5) / 2

_MOUNT_UNITS = {"hole_d": "mm", "print_oversize": "mm"}
_MOUNT_DESC = {
    "hole_d": "hole diameter before print compensation; default = M2.5 clearance (2.7)",
    "print_oversize": "added to diameter because FDM holes print small",
}
_MOUNT_NOTES = MaterialNotes(validated=["PLA", "PETG"], orientation="any (2D pattern)")


def _pattern(board: PiBoard, hole_d: float, print_oversize: float) -> Sketch:
    d = (board.hole_d if hole_d is None else hole_d) + print_oversize
    return Sketch() + [loc * Circle(d / 2) for loc in GridLocations(board.hole_dx, board.hole_dy, 2, 2)]


@component(
    id="patterns.pi5_mount", version="1.0.0",
    summary="Raspberry Pi 5 four-hole mount pattern (58 x 49 mm, M2.5) centred on the origin.",
    tags=["raspberry pi", "pi5", "pi 5", "mount", "holes", "M2.5", "sbc", "active cooler"],
    units={**_MOUNT_UNITS, "active_cooler_holes": "bool"},
    descriptions={**_MOUNT_DESC, "active_cooler_holes": "also cut the two 3 mm Active Cooler push-pin holes"},
    material_notes=_MOUNT_NOTES,
)
def pi5_mount(hole_d: float | None = None, print_oversize: float = 0.2, active_cooler_holes: bool = False) -> Sketch:
    """Four circles at the Pi 5 hole positions; subtract from a floor, or use
    ``locations_of()`` to place bosses.  ``active_cooler_holes`` adds the two
    3 mm push-pin holes of the official Active Cooler (x=+29, y=+/-18.5).

    Example:
        floor = Rectangle(95, 66) - pi5_mount()
        bosses = [loc * heat_set_boss("M2.5") for loc in locations_of(pi5_mount())]
    """
    sk = _pattern(PI_BOARDS["pi5"], hole_d, print_oversize)
    if active_cooler_holes:
        d = PI5_COOLER_HOLE_D + print_oversize
        sk = sk + [Pos(PI5_COOLER_HOLE_X, y) * Circle(d / 2) for y in (PI5_COOLER_HOLE_Y, -PI5_COOLER_HOLE_Y)]
    return sk


@component(
    id="patterns.pi4_mount", version="1.0.0",
    summary="Raspberry Pi 4 B (and 3 B/B+) four-hole mount pattern (58 x 49 mm, M2.5).",
    tags=["raspberry pi", "pi4", "pi 4", "pi3", "mount", "holes", "M2.5", "sbc"],
    units=_MOUNT_UNITS, descriptions=_MOUNT_DESC, material_notes=_MOUNT_NOTES,
)
def pi4_mount(hole_d: float | None = None, print_oversize: float = 0.2) -> Sketch:
    """Identical spacing to the Pi 5; kept as its own id so models document which board they target.

    Example:
        floor = Rectangle(95, 66) - pi4_mount()
    """
    return _pattern(PI_BOARDS["pi4"], hole_d, print_oversize)


@component(
    id="patterns.pi_zero_mount", version="1.0.0",
    summary="Raspberry Pi Zero / Zero 2 W four-hole mount pattern (58 x 23 mm, M2.5).",
    tags=["raspberry pi", "pi zero", "zero 2 w", "mount", "holes", "M2.5", "sbc"],
    units=_MOUNT_UNITS, descriptions=_MOUNT_DESC, material_notes=_MOUNT_NOTES,
)
def pi_zero_mount(hole_d: float | None = None, print_oversize: float = 0.2) -> Sketch:
    """Example:
        floor = Rectangle(75, 40) - pi_zero_mount()
    """
    return _pattern(PI_BOARDS["pi_zero"], hole_d, print_oversize)


@component(
    id="patterns.pi_board_outline", version="1.0.0",
    summary="Raspberry Pi PCB outline (rounded rectangle) positioned to line up with the matching mount pattern.",
    tags=["raspberry pi", "pi5", "pi4", "pi zero", "outline", "footprint", "pcb", "keep-out"],
    units={"board": "enum", "clearance": "mm"},
    descriptions={"board": "pi5, pi4, pi3 or pi_zero", "clearance": "grown outward on every side (use for pocket/keep-out)"},
    material_notes=_MOUNT_NOTES,
)
def pi_board_outline(board: str = "pi5", clearance: float = 0.0) -> Sketch:
    """Board outline sketch sharing the mount pattern's origin, so
    ``pi_board_outline() - pi5_mount()`` is the drilled PCB footprint.

    Example:
        pocket = extrude(pi_board_outline("pi5", clearance=1.0), amount=pcb_t)
    """
    b = PI_BOARDS[board]
    return Pos(b.outline_offset_x, 0) * RectangleRounded(b.length + 2 * clearance, b.width + 2 * clearance, b.corner_r + clearance)
