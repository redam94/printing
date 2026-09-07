"""Heat-set insert bosses and pockets."""
from __future__ import annotations

from build123d import Align, Axis, Cylinder, Part, Pos, chamfer, fillet

from lib.component import MaterialNotes, component
from lib.fasteners.hardware import heat_set

_ALIGN_BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@component(
    id="fasteners.heat_set_boss",
    version="1.0.0",
    summary="Cylindrical boss with a correctly sized pocket for a brass heat-set insert.",
    tags=["boss", "heat-set", "insert", "standoff", "M2", "M2.5", "M3", "M4", "screw"],
    units={"size": "enum", "height": "mm", "wall": "mm", "pocket_depth": "mm",
           "top_chamfer": "mm", "base_fillet": "mm", "through": "bool"},
    descriptions={
        "size": "insert size: M2, M2.5, M3, M4, M5",
        "height": "total boss height from its base (z=0) to the insert face",
        "wall": "plastic wall around the insert hole; defaults to the insert's minimum",
        "pocket_depth": "insert pocket depth; default = insert length + 1 mm for melt relief",
        "top_chamfer": "lead-in chamfer at the mouth of the pocket (helps the insert seat square)",
        "base_fillet": "fillet where the boss meets its parent surface (0 = none)",
        "through": "make the pocket a through hole (for bosses on thin floors)",
    },
    material_notes=MaterialNotes(
        validated=["PETG", "PLA"],
        orientation="boss axis vertical (insert pressed in along Z); pocket walls are then continuous perimeters",
        notes="Insert pocket is sized per the insert spec, never per the screw. In PLA keep iron at ~200 C.",
    ),
)
def heat_set_boss(
    size: str = "M3",
    height: float = 8.0,
    wall: float | None = None,
    pocket_depth: float | None = None,
    top_chamfer: float = 0.4,
    base_fillet: float = 0.0,
    through: bool = False,
) -> Part:
    """Boss standing on z=0 with an insert pocket opening at the top.

    The boss is centred on the origin so it can be placed with a Location::

    Example:
        from lib.component import locations_of
        from lib.patterns.pi import pi5_mount
        bosses = Part() + [loc * heat_set_boss("M2.5", height=6) for loc in locations_of(pi5_mount())]
        floor = floor + bosses
    """
    ins = heat_set(size)
    wall = ins.min_wall if wall is None else wall
    od = ins.hole_d + 2 * wall
    depth = height if through else (ins.length + 1.0 if pocket_depth is None else pocket_depth)
    depth = min(depth, height)
    boss = Cylinder(od / 2, height, align=_ALIGN_BOTTOM)
    if base_fillet > 0:
        boss = fillet(boss.edges().group_by(Axis.Z)[0], base_fillet)
    pocket = Pos(0, 0, height - depth) * Cylinder(ins.hole_d / 2, depth + (1 if not through else 0), align=_ALIGN_BOTTOM)
    boss = boss - pocket
    if top_chamfer > 0:
        top_inner = boss.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[-1].sort_by_distance((0, 0, height))[0]
        boss = chamfer(top_inner, top_chamfer)
    return boss


@component(
    id="fasteners.heat_set_pocket",
    version="1.0.0",
    summary="Negative (subtract me) pocket for a heat-set insert in a solid wall or floor.",
    tags=["heat-set", "insert", "pocket", "hole", "negative"],
    units={"size": "enum", "depth": "mm", "extra": "mm"},
    descriptions={
        "size": "insert size: M2, M2.5, M3, M4, M5",
        "depth": "pocket depth; default = insert length + 1 mm",
        "extra": "extra height above z=0 so the cutter clears the surface cleanly",
    },
    material_notes=MaterialNotes(validated=["PETG", "PLA"], orientation="pocket axis vertical preferred"),
)
def heat_set_pocket(size: str = "M3", depth: float | None = None, extra: float = 1.0) -> Part:
    """Cylinder to subtract; its top face sits at z=0 (the wall surface) and it
    extends downward by ``depth``.

    Example:
        lid = lid - [loc * heat_set_pocket("M3") for loc in locations_of(holes)]
    """
    ins = heat_set(size)
    depth = ins.length + 1.0 if depth is None else depth
    return Pos(0, 0, -depth) * Cylinder(ins.hole_d / 2, depth + extra, align=_ALIGN_BOTTOM)
