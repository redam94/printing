"""Thread-forming screw bosses (screw drives straight into plastic)."""
from __future__ import annotations

from build123d import Align, Axis, Cylinder, Part, Pos, chamfer, fillet

from lib.component import MaterialNotes, component
from lib.fasteners.hardware import screw

_ALIGN_BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@component(
    id="fasteners.screw_boss",
    version="1.0.0",
    summary="Boss with a pilot hole for a machine screw to self-thread into printed plastic.",
    tags=["boss", "screw", "pilot", "self-tapping", "thread-forming", "M2", "M2.5", "M3", "M4"],
    units={"size": "enum", "height": "mm", "wall": "mm", "pilot_d": "mm", "pilot_depth": "mm",
           "top_chamfer": "mm", "base_fillet": "mm"},
    descriptions={
        "size": "screw size: M2, M2.5, M3, M4, M5",
        "height": "boss height from z=0",
        "wall": "wall around the pilot (>= 2 perimeters, 1.6 mm recommended for M3)",
        "pilot_d": "pilot hole diameter; default from hardware table (thread-forming size)",
        "pilot_depth": "pilot depth; default = full height minus one wall thickness of floor",
        "top_chamfer": "entry chamfer",
        "base_fillet": "fillet at the base (0 = none)",
    },
    material_notes=MaterialNotes(
        validated=["PETG"],
        orientation="boss axis vertical so the screw threads cut across layers, not between them",
        notes="Good for ~5 insert/remove cycles. Use heat_set_boss for anything serviced often. PLA cracks under over-torque.",
    ),
)
def screw_boss(
    size: str = "M3",
    height: float = 8.0,
    wall: float = 1.6,
    pilot_d: float | None = None,
    pilot_depth: float | None = None,
    top_chamfer: float = 0.3,
    base_fillet: float = 0.0,
) -> Part:
    """Boss standing on z=0, pilot hole opening at the top.

    Example:
        boss = screw_boss("M3", height=10)
        body = body + Pos(20, 10, floor_t) * boss
    """
    s = screw(size)
    pilot_d = s.plastic_pilot if pilot_d is None else pilot_d
    pilot_depth = height - wall if pilot_depth is None else min(pilot_depth, height)
    od = pilot_d + 2 * wall
    boss = Cylinder(od / 2, height, align=_ALIGN_BOTTOM)
    if base_fillet > 0:
        boss = fillet(boss.edges().group_by(Axis.Z)[0], base_fillet)
    boss = boss - Pos(0, 0, height - pilot_depth) * Cylinder(pilot_d / 2, pilot_depth + 1, align=_ALIGN_BOTTOM)
    if top_chamfer > 0:
        top_inner = boss.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[-1].sort_by_distance((0, 0, height))[0]
        boss = chamfer(top_inner, top_chamfer)
    return boss
