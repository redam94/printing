"""Rounded open-top box shell and a matching lid."""
from __future__ import annotations

from build123d import Align, Axis, Box, Part, Pos, RectangleRounded, Sketch, chamfer, extrude, fillet

from lib.component import MaterialNotes, component

_ALIGN_BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@component(
    id="primitives.rounded_box", version="1.0.0",
    summary="Open-top rounded rectangular shell (enclosure body) with floor, standing on z=0; outer dimensions given.",
    tags=["box", "enclosure", "shell", "case", "rounded", "body"],
    units={"length": "mm", "width": "mm", "height": "mm", "wall": "mm", "floor_t": "mm", "corner_r": "mm",
           "bottom_chamfer": "mm", "inner_fillet": "mm"},
    descriptions={
        "length": "outer X", "width": "outer Y", "height": "outer Z including floor",
        "wall": "side wall thickness (multiple of 0.4)", "floor_t": "floor thickness; default = wall",
        "corner_r": "outer vertical corner radius", "bottom_chamfer": "chamfer on the bed-contact edge (elephant foot)",
        "inner_fillet": "fillet where floor meets the inner walls (0 = none)",
    },
    material_notes=MaterialNotes(validated=["PLA", "PETG"], orientation="floor on the bed, open top up"),
)
def rounded_box(
    length: float = 100.0, width: float = 70.0, height: float = 30.0, wall: float = 1.6, floor_t: float | None = None,
    corner_r: float = 3.0, bottom_chamfer: float = 0.4, inner_fillet: float = 0.0,
) -> Part:
    """Example:
        body = rounded_box(110, 80, 35, wall=2.0)
        body = body + Pos(0, 0, floor_t) * bosses
    """
    floor_t = wall if floor_t is None else floor_t
    outer = extrude(RectangleRounded(length, width, corner_r), amount=height)
    inner_r = max(corner_r - wall, 0.01)
    inner = Pos(0, 0, floor_t) * extrude(RectangleRounded(length - 2 * wall, width - 2 * wall, inner_r), amount=height)
    shell = outer - inner
    if inner_fillet > 0:
        floor_edges = shell.edges().group_by(Axis.Z)[1]  # inner floor loop
        shell = fillet(floor_edges, inner_fillet)
    if bottom_chamfer > 0:
        bottom_outer = shell.faces().sort_by(Axis.Z)[0].outer_wire().edges()
        shell = chamfer(bottom_outer, bottom_chamfer)
    return shell


@component(
    id="primitives.box_lid", version="1.1.0",
    summary="Flat lid for rounded_box with an inner lip that drops inside the walls; printed upside down (top face on the bed).",
    tags=["lid", "cover", "enclosure", "box", "lip"],
    units={"length": "mm", "width": "mm", "wall": "mm", "corner_r": "mm", "thickness": "mm", "lip_height": "mm",
           "lip_thickness": "mm", "clearance": "mm", "top_chamfer": "mm", "lip_cutouts": "-"},
    descriptions={
        "length": "outer X of the box it fits", "width": "outer Y of the box it fits", "wall": "box wall thickness",
        "corner_r": "box outer corner radius", "thickness": "lid plate thickness", "lip_height": "how far the lip drops into the box",
        "lip_thickness": "lip wall thickness", "clearance": "gap per side between lip and box inner wall (slip fit 0.2-0.3)",
        "top_chamfer": "chamfer on the outer top edge (bed-contact edge when printed inverted)",
        "lip_cutouts": "optional sketch in the lid XY frame subtracted from the lip only (e.g. circles clearing corner bosses); None = full lip",
    },
    material_notes=MaterialNotes(validated=["PLA", "PETG"], orientation="top face down on the bed, lip pointing up"),
)
def box_lid(
    length: float = 100.0, width: float = 70.0, wall: float = 1.6, corner_r: float = 3.0, thickness: float = 1.6,
    lip_height: float = 3.0, lip_thickness: float = 1.2, clearance: float = 0.25, top_chamfer: float = 0.4,
    lip_cutouts: Sketch | None = None,
) -> Part:
    """Lid plate spans z in [0, thickness] with the lip hanging below z=0 (as
    assembled on the box); flip for printing.  ``lip_cutouts`` (v1.1.0) is
    subtracted from the lip ring before extruding so the lip can step around
    corner bosses that run up to the box rim; the plate is untouched.

    Example:
        lid = box_lid(110, 80, wall=2.0)
        lid = box_lid(110, 80, lip_cutouts=Sketch() + [loc * Circle(boss_r + 0.3) for loc in boss_locs])
    """
    plate = extrude(RectangleRounded(length, width, corner_r), amount=thickness)
    if top_chamfer > 0:
        plate = chamfer(plate.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), top_chamfer)
    lo = length - 2 * (wall + clearance)
    wo = width - 2 * (wall + clearance)
    r_out = max(corner_r - wall - clearance, 0.01)
    r_in = max(r_out - lip_thickness, 0.01)
    ring = RectangleRounded(lo, wo, r_out) - RectangleRounded(lo - 2 * lip_thickness, wo - 2 * lip_thickness, r_in)
    if lip_cutouts is not None:
        ring = ring - lip_cutouts
    lip = extrude(ring, amount=-lip_height)
    return plate + lip
