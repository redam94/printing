"""C-profile clip that grips a panel or countertop edge."""
from __future__ import annotations

from build123d import Box, Circle, Part, Plane, Polygon, Pos, Rot, extrude

from lib.component import MaterialNotes, component


@component(
    id="primitives.edge_clip", version="1.0.0",
    summary="C-profile clip that grips a square panel or countertop edge: saddle over the top, jaw down the cut face, return lip under.",
    tags=["clip", "edge", "counter", "hook", "saddle", "no-fastener", "kitchen", "shelf"],
    units={"length": "mm", "thickness": "mm", "throat_clearance": "mm", "jaw_t": "mm", "under_reach": "mm",
           "lip_t": "mm", "saddle_t": "mm", "saddle_reach": "mm", "corner_relief": "mm",
           "drip_groove_r": "mm", "drip_groove_z": "mm", "drip_groove_out": "mm", "pad_recess": "mm"},
    descriptions={
        "length": "clip length along the edge (X)",
        "thickness": "thickness of the panel it grips (30 = a 3 cm stone slab; measure it)",
        "throat_clearance": "added to thickness so the clip slides onto a square edge",
        "jaw_t": "thickness of the jaw hanging down the cut face",
        "under_reach": "how far the return lip tucks under the panel; 0 degenerates to a plain saddle",
        "lip_t": "return lip thickness",
        "saddle_t": "thickness of the flange lying on top of the panel (the floor of whatever is grown on it)",
        "saddle_reach": "how far inland the top flange runs",
        "corner_relief": "relief radius at both panel corners so printed inside corners cannot hold the clip off the panel",
        "drip_groove_r": "radius of the drip break cut into the outboard face; 0 = none",
        "drip_groove_z": "how far below the panel top surface the drip break sits",
        "drip_groove_out": "how far outboard of the face the groove centre sits, so the arc meets the face at an angle instead of tangentially",
        "pad_recess": "depth of a seat for a stick-on or printed pad on both gripping faces; 0 = none",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="print lying on the jaw's OUTBOARD face (Rot(0, 90, 0) then on_bed): that face and anything grown flush with it become the bed face, and the only downward surfaces left are whatever the caller adds",
        notes="UNVALIDATED — no test print yet. Relies on friction and the return lip, not on a spring, so PLA is acceptable here; "
              "the throat does not flex, so measure the panel and set thickness rather than counting on give. "
              "A printed inside corner always carries a small radius and a stone arris does not: keep corner_relief > 0 or the clip rocks.",
    ),
)
def edge_clip(length: float = 180.0, thickness: float = 30.0, throat_clearance: float = 0.4, jaw_t: float = 3.0,
              under_reach: float = 4.0, lip_t: float = 2.4, saddle_t: float = 2.4, saddle_reach: float = 55.0,
              corner_relief: float = 1.2, drip_groove_r: float = 0.0, drip_groove_z: float = 2.0,
              drip_groove_out: float = 0.4, pad_recess: float = 0.0) -> Part:
    """A C-section that hangs on a square edge, in USE orientation:

        +X along the edge, +Y outboard past the cut face, +Z up.
        The panel's top surface is z=0 and its cut face is y=0, so the panel
        occupies y < 0, z in [-thickness, 0] and the clip wraps around it.

    Grow the payload (a pan, a hook, a shelf) off the top of the saddle at z=saddle_t;
    the caller's geometry and the jaw's outboard face at y=jaw_t are what decide the
    print orientation.

    Example:
        rail = edge_clip(180, thickness=COUNTER_T, saddle_reach=PAN_REACH) + pan
        rail = on_bed(Rot(0, 90, 0) * rail)          # jaw's outboard face onto the bed
    """
    throat = thickness + throat_clearance
    section = Polygon(
        (jaw_t, -throat - lip_t),        # bottom of the return lip, outboard face
        (jaw_t, saddle_t),               # up the outboard face of jaw and saddle
        (-saddle_reach, saddle_t),       # top of the saddle, inland
        (-saddle_reach, 0.0),            # inland face down to the panel
        (0.0, 0.0),                      # panel contact face, out to the edge
        (0.0, -throat),                  # down the cut face
        (-under_reach, -throat),         # in under the panel
        (-under_reach, -throat - lip_t),  # lip end face
        align=None,
    )
    if corner_relief > 0:
        section -= Pos(0, 0) * Circle(corner_relief)              # top panel corner
        section -= Pos(0, -throat) * Circle(corner_relief)        # bottom panel corner
    if drip_groove_r > 0:
        section -= Pos(jaw_t + drip_groove_out, -drip_groove_z) * Circle(drip_groove_r)

    clip = extrude(Plane.YZ * section, amount=length / 2, both=True)
    if pad_recess > 0:
        inset = 2.0
        pad_l = max(length - 2 * inset, 1.0)
        top = Pos(0, -saddle_reach / 2, 0) * Box(pad_l, max(saddle_reach - 2 * inset, 1.0), 2 * pad_recess)
        lip = Pos(0, -under_reach / 2, -throat) * Box(pad_l, max(under_reach - inset, 1.0), 2 * pad_recess)
        clip -= top
        clip -= lip
    return clip
