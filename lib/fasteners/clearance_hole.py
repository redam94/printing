"""Clearance holes with print compensation, optional counterbore/countersink."""
from __future__ import annotations

from build123d import Align, Cone, Cylinder, Part, Pos

from lib.component import MaterialNotes, component
from lib.fasteners.hardware import screw

_ALIGN_BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@component(
    id="fasteners.clearance_hole",
    version="1.0.0",
    summary="Negative (subtract me) clearance hole for a metric screw, with print oversize and optional counterbore or countersink.",
    tags=["hole", "clearance", "screw", "counterbore", "countersink", "negative", "M2", "M2.5", "M3", "M4"],
    units={"size": "enum", "depth": "mm", "fit": "enum", "print_oversize": "mm", "head": "enum",
           "head_clearance": "mm", "head_depth": "mm"},
    descriptions={
        "size": "screw size: M2, M2.5, M3, M4, M5",
        "depth": "hole length along -Z from the surface at z=0 (make it through the whole part)",
        "fit": "ISO 273 series: fine, medium, coarse",
        "print_oversize": "added to diameter because FDM holes print small (0.2-0.4 typical)",
        "head": "none, counterbore (socket head) or countersink (90 deg)",
        "head_clearance": "added to head diameter for counterbore/countersink",
        "head_depth": "counterbore depth; default = head height",
    },
    material_notes=MaterialNotes(validated=["PLA", "PETG"], orientation="any; for horizontal holes use primitives.teardrop instead"),
)
def clearance_hole(
    size: str = "M3",
    depth: float = 20.0,
    fit: str = "medium",
    print_oversize: float = 0.2,
    head: str = "none",
    head_clearance: float = 0.4,
    head_depth: float | None = None,
) -> Part:
    """Cutter whose top face sits at z=0 and extends downward ``depth``.

    Example:
        plate = plate - [Pos(x, y, plate_t) * clearance_hole("M3", depth=plate_t) for x, y in pts]
    """
    s = screw(size)
    d = {"fine": s.clearance_fine, "medium": s.clearance_medium, "coarse": s.clearance_coarse}[fit] + print_oversize
    cutter = Pos(0, 0, -depth) * Cylinder(d / 2, depth + 1, align=_ALIGN_BOTTOM)
    if head == "counterbore":
        hd = s.socket_head_d + head_clearance
        hh = s.socket_head_h if head_depth is None else head_depth
        cutter = cutter + Pos(0, 0, -hh) * Cylinder(hd / 2, hh + 1, align=_ALIGN_BOTTOM)
    elif head == "countersink":
        hd = s.csk_head_d + head_clearance
        hh = (hd - d) / 2  # 90 degree countersink
        cutter = cutter + Pos(0, 0, -hh) * Cone(d / 2, hd / 2, hh, align=_ALIGN_BOTTOM) + Cylinder(hd / 2, 1, align=_ALIGN_BOTTOM)
    elif head != "none":
        raise ValueError("head must be none, counterbore or countersink")
    return cutter
