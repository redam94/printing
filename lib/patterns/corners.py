"""Generic rectangular corner hole pattern (lid screws, corner bosses)."""
from __future__ import annotations

from build123d import Circle, GridLocations, Sketch

from lib.component import MaterialNotes, component


@component(
    id="patterns.corner_holes", version="1.0.0",
    summary="Four holes inset from the corners of a length x width rectangle (lid screws / corner bosses), centred on the origin.",
    tags=["corners", "holes", "lid", "screws", "bosses", "enclosure", "pattern", "M3"],
    units={"length": "mm", "width": "mm", "inset": "mm", "hole_d": "mm", "print_oversize": "mm"},
    descriptions={
        "length": "rectangle X (usually the box INNER length)",
        "width": "rectangle Y (usually the box INNER width)",
        "inset": "hole centre distance from each of the two adjacent rectangle edges",
        "hole_d": "hole diameter before print compensation (default M3 medium clearance 3.4)",
        "print_oversize": "added to diameter because FDM holes print small",
    },
    material_notes=MaterialNotes(validated=["PLA", "PETG"], orientation="any (2D pattern)"),
)
def corner_holes(length: float = 100.0, width: float = 70.0, inset: float = 4.6,
                 hole_d: float = 3.4, print_oversize: float = 0.2) -> Sketch:
    """Four circles at ``(+/-(length/2 - inset), +/-(width/2 - inset))``.

    Pass the box *inner* cavity size and the boss inset to get the corner-boss
    centres of a ``rounded_box``; ``locations_of()`` turns them into boss
    placements, and the same call with the lid gives the matching screw holes.

    Example:
        holes = corner_holes(inner_l, inner_w, inset=3.4)
        bosses = [loc * heat_set_boss("M3", height=h) for loc in locations_of(holes)]
    """
    d = hole_d + print_oversize
    return Sketch() + [loc * Circle(d / 2) for loc in GridLocations(length - 2 * inset, width - 2 * inset, 2, 2)]
