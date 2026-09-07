"""DIN rail (TS35 / EN 60715 top-hat) cross-section for clip design."""
from __future__ import annotations

from build123d import Polygon, Sketch

from lib.component import MaterialNotes, component

TS35_WIDTH = 35.0     # overall width across the lips
TS35_DEPTH_7_5 = 7.5  # standard shallow rail
TS35_DEPTH_15 = 15.0  # deep rail
TS35_SHEET_T = 1.0    # typical sheet thickness
TS35_BASE_W = 27.0    # width of the base (flat part that screws to the panel)


@component(
    id="patterns.din_rail_ts35_profile", version="1.0.0",
    summary="TS35 top-hat DIN rail cross-section (35 mm wide) as a sketch in XY, for subtracting a rail pocket from a clip.",
    tags=["din rail", "ts35", "en 60715", "clip", "profile", "electrical", "enclosure"],
    units={"depth": "mm", "clearance": "mm", "sheet_t": "mm"},
    descriptions={"depth": "rail depth: 7.5 (standard) or 15", "clearance": "grown outward so the clip slides on",
                  "sheet_t": "rail sheet-metal thickness"},
    material_notes=MaterialNotes(validated=[], orientation="clip printed with rail axis vertical (Z) so the lips are solid perimeters",
                                 notes="UNVALIDATED: geometry from standard, no test print yet"),
)
def din_rail_ts35_profile(depth: float = 7.5, clearance: float = 0.3, sheet_t: float = 1.0) -> Sketch:
    """Profile drawn in XY: rail lips at y=0 (top, where a clip hooks), base at y=-depth.
    Extrude along Z for the rail length.

    Example:
        clip = clip - extrude(din_rail_ts35_profile(clearance=0.3), amount=clip_len)
    """
    w, b, c, t = TS35_WIDTH / 2, TS35_BASE_W / 2, clearance, sheet_t
    # Outer silhouette of the hat: lips of width (w-b) at top, body down to the base.
    pts = [
        (-w - c, 0 + c), (w + c, 0 + c),                   # top lip edge
        (w + c, -t - c), (b + c, -t - c),                  # under the lip
        (b + c, -depth - c), (-b - c, -depth - c),         # down to base
        (-b - c, -t - c), (-w - c, -t - c),
    ]
    return Sketch() + Polygon(*pts)
