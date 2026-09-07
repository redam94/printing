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

from build123d import Circle, GridLocations, Pos, Rectangle, RectangleRounded, Sketch

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


# ---------------------------------------------------------------------------
# Pi 5 connector windows
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PiPort:
    """One edge connector, in hole-pattern coordinates (see module docstring).

    ``along`` is the connector centre measured along its board edge: lib X for
    the -Y (USB-C/HDMI) edge, lib Y for the +X (USB-A/Ethernet) and -X (SD)
    edges.  Heights are relative to the PCB TOP surface (z=0).  ``body_*`` is
    the connector shell on the board; ``plug_*`` is the envelope a mating
    plug/overmold needs to pass through a wall that stands a few mm off the
    board edge.
    """
    name: str
    edge: str
    along: float
    body_w: float
    body_z0: float
    body_z1: float
    plug_w: float
    plug_z0: float
    plug_z1: float
    status: str


# Positions from the official Pi 5 drawing (board coords -> lib coords: x-32.5, y-28).
# Connector body sizes are Pi 4 values / generic connector specs; plug envelopes are typical
# cable overmolds.  Both flagged UNVERIFIED in references/hardware_dimensions.md sec. 1.
PI5_PORTS: tuple[PiPort, ...] = (
    PiPort("usb_c",       "power", -21.3, 9.0,  0.0,  3.2, 13.0, -1.9,  5.1,  "position verified; body Pi 4; plug envelope UNVERIFIED (13 x 7 overmold)"),
    PiPort("hdmi0",       "power",  -6.7, 7.6,  0.0,  3.0, 10.0, -1.5,  4.5,  "position verified; body/plug UNVERIFIED"),
    PiPort("hdmi1",       "power",   6.7, 7.6,  0.0,  3.0, 10.0, -1.5,  4.5,  "position verified; body/plug UNVERIFIED"),
    PiPort("ethernet",    "usb",   -17.8, 16.0, 0.0, 13.5, 16.0,  0.0, 13.5,  "position verified; body Pi 4 (13.5 tall)"),
    PiPort("usb_a_lower", "usb",     1.1, 13.3, 0.0, 15.6, 13.3,  0.0, 15.6,  "position verified; body generic dual USB-A"),
    PiPort("usb_a_upper", "usb",    19.0, 13.3, 0.0, 15.6, 13.3,  0.0, 15.6,  "position verified; body generic dual USB-A"),
    PiPort("microsd",     "sd",      0.0, 12.0, -3.6, 0.0, 16.0, -3.6, 0.0,   "UNVERIFIED: slot assumed centred on the SD edge, card under the PCB"),
)
PI5_PORT_EDGES = {
    "power": "-Y edge (USB-C, micro-HDMI 0/1); map with Plane.XZ, sketch x = lib X",
    "usb": "+X edge (Ethernet, two USB-A stacks); map with Plane.YZ, sketch x = lib Y",
    "sd": "-X edge (microSD access window); map with Plane.YZ, sketch x = lib Y",
}


@component(
    id="patterns.pi5_port_cutouts", version="1.0.0",
    summary="Raspberry Pi 5 connector windows for one board edge as a wall-plane sketch (x along the edge, y = height above PCB top).",
    tags=["raspberry pi", "pi5", "pi 5", "ports", "cutout", "usb-c", "hdmi", "ethernet", "usb-a", "microsd", "connector", "window"],
    units={"edge": "enum", "clearance": "mm", "plug_envelope": "bool", "ports": "-"},
    descriptions={
        "edge": "power (-Y: USB-C + 2x micro-HDMI), usb (+X: Ethernet + 2x USB-A), sd (-X: microSD window)",
        "clearance": "added on every side of the connector/plug envelope",
        "plug_envelope": "size windows for the mating plug overmold (True) or just the connector body (False, flush panels)",
        "ports": "optional subset of port names to include, e.g. ['usb_c']; default = every port on that edge",
    },
    material_notes=MaterialNotes(
        validated=[], orientation="windows cut through a vertical wall; the wall above each window is a short bridge (<= 18 mm)",
        notes="UNVALIDATED: positions from the official drawing, connector/plug envelopes from Pi 4 data and typical cables — test-fit before printing many.",
    ),
)
def pi5_port_cutouts(edge: str = "power", clearance: float = 0.75, plug_envelope: bool = True,
                     ports: list[str] | None = None) -> Sketch:
    """Rectangles to subtract from an enclosure wall so the Pi 5 connectors are reachable.

    Sketch frame: x runs along the board edge in hole-pattern coordinates
    (lib X for ``power``, lib Y for ``usb``/``sd``), y is height above the PCB
    top surface.  Place it with ``Pos(x_of_pi_origin, z_of_pcb_top)`` on the
    wall plane and extrude through the wall with ``both=True``.

    Example:
        win = pi5_port_cutouts("power")
        body = body - extrude(Plane.XZ.offset(outer_w / 2) * Pos(pi_x, pcb_top_z) * win, amount=wall, both=True)
    """
    if edge not in PI5_PORT_EDGES:
        raise ValueError(f"unknown edge {edge!r}; known: {sorted(PI5_PORT_EDGES)}")
    sel = [p for p in PI5_PORTS if p.edge == edge and (ports is None or p.name in ports)]
    if not sel:
        raise ValueError(f"no ports selected on edge {edge!r} from {ports}")
    rects = []
    for p in sel:
        w, z0, z1 = (p.plug_w, p.plug_z0, p.plug_z1) if plug_envelope else (p.body_w, p.body_z0, p.body_z1)
        w, z0, z1 = w + 2 * clearance, z0 - clearance, z1 + clearance
        rects.append(Pos(p.along, (z0 + z1) / 2) * Rectangle(w, z1 - z0))
    return Sketch() + rects
