"""Drain grooves cut into a surface."""
from __future__ import annotations

from math import radians, tan

from build123d import Part, Plane, Polygon, Pos, extrude

from lib.component import MaterialNotes, component


@component(
    id="primitives.groove_field", version="1.0.0",
    summary="Negative (subtract me) field of self-supporting drain grooves running along Y; groove mouths at z=0, cutting down.",
    tags=["drain", "grooves", "water", "drying", "deck", "negative", "kitchen"],
    units={"area_l": "mm", "area_w": "mm", "pitch": "mm", "width": "mm", "depth": "mm",
           "wall_deg": "deg", "lanes": "mm", "rotation": "deg"},
    descriptions={
        "area_l": "width of the grooved area across the grooves (X); ignored when lanes are given",
        "area_w": "length of each groove along Y; oversize it to cut clean through both ends",
        "pitch": "centre-to-centre across the grooves",
        "width": "groove width at the mouth (the surface)",
        "depth": "groove depth below the surface",
        "wall_deg": "groove wall angle off vertical; on a surface printed FACE DOWN this is the overhang angle",
        "lanes": "explicit groove centres in X; overrides the uniform pitch (keeps a groove off a feature it would sever)",
        "rotation": "rotate the whole field about Z",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="the grooved face goes on the bed; the grooves then narrow going up, so wall_deg IS the overhang angle (45 is the limit, 30 is comfortable)",
        notes="UNVALIDATED — no test print yet. Square-walled grooves in a face-down surface print as flat ceilings; keep wall_deg >= 25. "
              "Groove ceilings read as overhang area in the printability check even when they are short, self-supporting bridges.",
    ),
)
def groove_field(area_l: float = 90.0, area_w: float = 140.0, pitch: float = 9.0, width: float = 5.0,
                 depth: float = 1.2, wall_deg: float = 30.0, lanes: list[float] | None = None,
                 rotation: float = 0.0) -> Part:
    """A field of trapezoidal grooves to subtract from a deck, tray or base plate.

    The grooves run along Y with their mouths in the z=0 plane, cutting downward, so
    ``Pos(0, 0, deck_top) * groove_field(...)`` reads naturally.  Water runs in the grooves
    and whatever is being dried stands on the ribs between them.

    Pass ``lanes`` when something on the surface must not be cut: a groove parallel to a
    standing blade or wall that lands under it severs it from its base.

    Example:
        deck = deck - Pos(0, 0, DECK_T) * groove_field(TILE_X, TILE_Y + 2, 9.0, 5.0, 1.2, 30.0)
    """
    run = depth * tan(radians(wall_deg))
    if width - 2 * run <= 0:
        raise ValueError(f"groove_field: wall_deg {wall_deg} closes a {width} mm groove {depth} mm deep")
    groove = extrude(
        Plane.XZ * Polygon(
            (-width / 2, 0.0),
            (width / 2, 0.0),
            (width / 2 - run, -depth),
            (-width / 2 + run, -depth),
            align=None,
        ),
        amount=area_w / 2,
        both=True,
    )
    if lanes is None:
        n = max(int(area_l // pitch), 1)
        span = (n - 1) * pitch
        lanes = [i * pitch - span / 2 for i in range(n)]
    field = Part() + [Pos(x, 0, 0) * groove for x in lanes]
    return field.rotate(__import__("build123d").Axis.Z, rotation) if rotation else field
