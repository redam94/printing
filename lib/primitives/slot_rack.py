"""A comb of leaning blades with the slots between them."""
from __future__ import annotations

from math import radians, tan

from build123d import Part, Plane, Polygon, Pos, extrude

from lib.component import MaterialNotes, component


@component(
    id="primitives.slot_rack", version="1.0.0",
    summary="Row of leaning blades with the slots between them, standing on z=0 and centred on the origin in X.",
    tags=["rack", "slots", "fins", "blades", "comb", "drying", "holder", "kitchen"],
    units={"count": "count", "pitch": "mm", "fin_t": "mm", "fin_h": "mm", "depth": "mm",
           "tilt_deg": "deg", "top_slope_deg": "deg"},
    descriptions={
        "count": "number of blades; the slots are the count-1 gaps between them",
        "pitch": "blade centre-to-centre",
        "fin_t": "blade thickness (>= 2.4 mm before a wet pan leans on one)",
        "fin_h": "blade height at the back edge (-Y), measured from z=0",
        "depth": "blade depth along Y, centred on the origin",
        "tilt_deg": "blade lean off vertical; blades are SHEARED, so this is also the print overhang angle",
        "top_slope_deg": "blade tops slope down toward +Y so nothing resting across them sits level",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="blade roots on the bed, blades up. The blades are sheared rather than rotated, so every root stays flat and the lean is the only overhang in the part; keep tilt_deg well under 45",
        notes="UNVALIDATED — no test print yet. A blade is a cantilever loaded sideways by whatever leans on it: PLA is stiffer but brittle at the root, "
              "PETG survives a knock. Blades must run from z=0 through whatever carries them, not merely sit on its top face — a blade that only shares a "
              "face with a base fuses as a separate body.",
    ),
)
def slot_rack(count: int = 7, pitch: float = 12.0, fin_t: float = 2.6, fin_h: float = 55.0,
              depth: float = 60.0, tilt_deg: float = 12.0, top_slope_deg: float = 10.0) -> Part:
    """Blades stand on z=0, run along Y and are arrayed along X.

    Items go in on edge between the blades: plates, lids, chopping boards, pot rims.
    ``top_slope_deg`` is what stops a rim resting across two blade tops from sitting level
    and holding a ring of water, so it is not decoration.

    Example:
        rack = base + Pos(lid_x, 0, 0) * slot_rack(7, 12.0, 2.6, BASE_T + LID_FIN_H, DEPTH, 12.0, 10.0)
    """
    shear = fin_h * tan(radians(tilt_deg))
    fin = extrude(
        Plane.XZ * Polygon(
            (-fin_t / 2, 0.0),
            (fin_t / 2, 0.0),
            (fin_t / 2 + shear, fin_h),
            (-fin_t / 2 + shear, fin_h),
            align=None,
        ),
        amount=depth / 2,
        both=True,
    )
    t = tan(radians(top_slope_deg))
    top = lambda y: fin_h - (y + depth / 2) * t          # noqa: E731
    big = fin_h + depth + 100.0
    fin -= extrude(
        Plane.YZ * Polygon(
            (-depth, top(-depth)),
            (depth, top(depth)),
            (depth, fin_h + big),
            (-depth, fin_h + big),
            align=None,
        ),
        amount=big,
        both=True,
    )
    span = (count - 1) * pitch
    return Part() + [Pos(i * pitch - span / 2, 0, 0) * fin for i in range(count)]
