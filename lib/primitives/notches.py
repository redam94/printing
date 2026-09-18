"""Notches: finger scoops for lifting a lid, and racks of rectangular notches a plate edge drops into."""
from __future__ import annotations

from build123d import Align, Box, Part, Pos, SlotOverall, extrude

from lib.component import MaterialNotes, component


@component(
    id="primitives.finger_notch", version="1.0.0",
    summary="Negative (subtract me) rounded finger scoop cut into an edge so a lid or jaw can be lifted; centred on the edge at the origin, cutting through Z.",
    tags=["notch", "finger", "scoop", "lift", "lid", "grip", "negative", "edge"],
    units={"width": "mm", "depth": "mm", "through": "mm"},
    descriptions={"width": "scoop width along the edge (X)", "depth": "how far the scoop reaches into the part from the edge (-Y)",
                  "through": "cut length along Z, both ways from z=0"},
    material_notes=MaterialNotes(validated=[], orientation="any", notes="UNVALIDATED: no test print yet."),
)
def finger_notch(width: float = 20.0, depth: float = 6.0, through: float = 20.0) -> Part:
    """An ellipse of the given width centred on the edge (y=0) whose inner end reaches ``depth`` into -Y;
    the half outside the part cuts nothing.

    Example:
        jaw = jaw - Pos(0, jaw_end_y, jaw_t / 2) * finger_notch(width=18, depth=5)
    """
    from build123d import Ellipse
    return extrude(Ellipse(width / 2, depth), amount=through, both=True)


@component(
    id="primitives.notch_rack", version="1.0.0",
    summary="Negative (subtract me) row of rectangular notches across a face (running along X, stepped along Y) that a plate edge drops into; face at z=0, notches extend down.",
    tags=["notch", "rack", "detent", "stand", "angle", "adjustable", "kickstand", "negative", "groove"],
    units={"count": "count", "pitch": "mm", "width": "mm", "depth": "mm", "length": "mm", "lead_in": "mm"},
    descriptions={
        "count": "number of notches", "pitch": "Y distance between notch centres", "width": "notch width (Y) = plate thickness + clearance",
        "depth": "notch depth below the face", "length": "notch length along X (through the face if longer than the part)",
        "lead_in": "45 deg chamfer on the notch mouth so the edge finds it (0 = sharp)",
    },
    material_notes=MaterialNotes(validated=[], orientation="face up (notch floors are flat) or on the bed (notch mouths bridge across width)",
                                 notes="UNVALIDATED: no test print yet."),
)
def notch_rack(count: int = 3, pitch: float = 8.0, width: float = 4.6, depth: float = 2.0, length: float = 40.0, lead_in: float = 0.8) -> Part:
    """Notches centred on y = 0, +/-pitch, ... (the row is centred on the origin).

    Example:
        prop = prop - Pos(0, y_first + pitch, prop_t) * notch_rack(count=3, pitch=8, width=4.6, depth=2, length=80)
    """
    count = max(int(count), 1)
    out = Part()
    y0 = -(count - 1) * pitch / 2
    for i in range(count):
        y = y0 + i * pitch
        cut = Pos(0, y, -depth) * Box(length, width, depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
        if lead_in > 0:
            from build123d import Plane, Polygon
            w2 = width / 2
            mouth = extrude(Plane.YZ * Polygon((-w2 - lead_in, 0.01), (w2 + lead_in, 0.01), (w2, -lead_in), (-w2, -lead_in), align=None),
                            amount=length / 2, both=True)
            cut = cut + Pos(0, y, 0) * mouth + Pos(0, y, 0) * Box(length, width + 2 * lead_in, 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
        out = out + cut
    return out
