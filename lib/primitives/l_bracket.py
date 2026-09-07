"""Angle (L) brackets with rows of screw holes, in print orientation."""
from __future__ import annotations

from build123d import Axis, Circle, Part, Plane, Polygon, Pos, Sketch, chamfer, extrude, fillet

from lib.component import MaterialNotes, component
from lib.fasteners.hardware import screw
from lib.primitives.cable_grommet import teardrop


@component(
    id="primitives.l_bracket", version="1.0.0",
    summary="90-degree L (angle) bracket with a row of screw clearance holes along each arm, standing on its side on z=0 (strongest print orientation).",
    tags=["bracket", "angle", "L", "corner", "mount", "holes", "M3", "M4", "structural"],
    units={"arm_a": "mm", "arm_b": "mm", "thickness": "mm", "width": "mm", "size": "enum", "holes_per_arm": "count",
           "hole_pitch": "mm", "hole_style": "enum", "fit": "enum", "print_oversize": "mm", "inner_r": "mm",
           "outer_r": "mm", "bottom_chamfer": "mm"},
    descriptions={
        "arm_a": "arm along +X, measured from the outer corner to the free end",
        "arm_b": "arm along +Y, measured from the outer corner to the free end",
        "thickness": "arm thickness (multiple of 0.4; >= 3 for M3 hardware)",
        "width": "bracket width = print height along Z",
        "size": "screw size for the holes: M2, M2.5, M3, M4, M5",
        "holes_per_arm": "holes in the single row on each arm (0 = plain bracket)",
        "hole_pitch": "centre-to-centre along the arm; default spreads the holes evenly over the arm span beyond the other arm",
        "hole_style": "teardrop (horizontal hole bridges without support) or round",
        "fit": "ISO 273 clearance series: fine, medium, coarse",
        "print_oversize": "added to hole diameter because FDM holes print small",
        "inner_r": "fillet radius on the inside corner (vertical edge; stress relief, 0 = sharp)",
        "outer_r": "fillet radius on the outside corner (0 = sharp)",
        "bottom_chamfer": "chamfer on the bed-contact edge loop (elephant foot, 0 = none)",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="on its side: L profile in the bed plane, width along Z, so the corner is loaded along the layers; "
                    "holes are horizontal (teardrop point up)",
        notes="UNVALIDATED: no test print yet. Printing one arm flat on the bed puts the corner's bending load across layers.",
    ),
)
def l_bracket(
    arm_a: float = 40.0, arm_b: float = 40.0, thickness: float = 4.0, width: float = 20.0,
    size: str = "M3", holes_per_arm: int = 3, hole_pitch: float | None = None, hole_style: str = "teardrop",
    fit: str = "medium", print_oversize: float = 0.2,
    inner_r: float = 1.0, outer_r: float = 0.0, bottom_chamfer: float = 0.4,
) -> Part:
    """Outer corner at the origin; arm A runs along +X (its outer face on y=0), arm B along +Y
    (outer face on x=0); z spans [0, width] so the part sits on the bed as returned.  Holes run
    horizontally through each arm, centred on the width, in one row.

    Example:
        bracket = l_bracket(40, 40, thickness=4, width=20, size="M3", holes_per_arm=3)
        plate = plate + Pos(x, y, 0) * l_bracket(30, 20, holes_per_arm=2)
    """
    t = thickness
    if thickness <= 0 or width <= 0 or min(arm_a, arm_b) <= t:
        raise ValueError("l_bracket: arms must be longer than the thickness and all sizes positive")
    profile = Polygon((0, 0), (arm_a, 0), (arm_a, t), (t, t), (t, arm_b), (0, arm_b), align=None)
    body = extrude(profile, amount=width)

    vertical = body.edges().filter_by(Axis.Z)
    if inner_r > 0:
        body = fillet(vertical.sort_by_distance((t, t, width / 2))[0], min(inner_r, 0.9 * min(arm_a - t, arm_b - t)))
        vertical = body.edges().filter_by(Axis.Z)
    if outer_r > 0:
        body = fillet(vertical.sort_by_distance((0, 0, width / 2))[0], min(outer_r, 0.9 * t))
    if bottom_chamfer > 0:
        body = chamfer(body.faces().sort_by(Axis.Z)[0].outer_wire().edges(), min(bottom_chamfer, 0.45 * t))

    if holes_per_arm > 0:
        s = screw(size)
        d = {"fine": s.clearance_fine, "medium": s.clearance_medium, "coarse": s.clearance_coarse}[fit]
        if hole_style == "teardrop":
            hole = teardrop(d, print_oversize=print_oversize)
        elif hole_style == "round":
            hole = Sketch() + Circle((d + print_oversize) / 2)
        else:
            raise ValueError("hole_style must be teardrop or round")

        def centres(arm_len: float) -> list[float]:
            span = arm_len - t
            pitch = span / holes_per_arm if hole_pitch is None else hole_pitch
            mid = t + span / 2
            return [mid + (i - (holes_per_arm - 1) / 2) * pitch for i in range(holes_per_arm)]

        z = width / 2
        # arm A: wall in the XZ plane, hole axis along Y; arm B: wall in the YZ plane, axis along X
        cut_a = [extrude(Plane.XZ * Pos(x, z) * hole, amount=t, both=True) for x in centres(arm_a)]
        cut_b = [extrude(Plane.YZ * Pos(y, z) * hole, amount=t, both=True) for y in centres(arm_b)]
        body = body - cut_a - cut_b
    return body
