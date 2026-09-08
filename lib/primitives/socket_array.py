"""Blind cylindrical sockets: pen / brush / tool / cartridge holders."""
from __future__ import annotations

from build123d import Align, Cone, Cylinder, GridLocations, Part, Pos

from lib.component import MaterialNotes, component

_ALIGN_TOP = (Align.CENTER, Align.CENTER, Align.MAX)
_ALIGN_BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@component(
    id="primitives.socket_array", version="1.0.0",
    summary="Negative (subtract me): row or grid of blind cylindrical sockets with chamfered lead-ins; socket rims at z=0, bores extend down.",
    tags=["bore", "socket", "pocket", "holder", "rack", "tool", "pen", "negative", "cylindrical"],
    units={"bore_d": "mm", "depth": "mm", "count": "count", "pitch": "mm", "rows": "count",
           "row_pitch": "mm", "clearance": "mm", "lead_in": "mm", "vent_d": "mm", "vent_len": "mm"},
    descriptions={
        "bore_d": "nominal diameter of the object being held, before clearance",
        "depth": "socket depth from the rim (z=0) down to the bore floor",
        "count": "sockets along X",
        "pitch": "centre-to-centre along X",
        "rows": "socket rows along Y",
        "row_pitch": "centre-to-centre along Y; default = pitch",
        "clearance": "added to the DIAMETER (0.6 = 0.3 per side, drops in one-handed; 0.3 = snug)",
        "lead_in": "45 degree chamfer at the rim so the object finds the hole; 0 = sharp rim",
        "vent_d": "coaxial hole through the bore floor for dust / pushing a stuck item out; 0 = blind",
        "vent_len": "how far the vent runs below the bore floor (make it reach the underside)",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="bores vertical (axis along Z), rims up: the lead-in cone is a 45 deg overhang and each bore floor is an up-facing floor, so nothing needs support",
        notes="UNVALIDATED: no test print yet. Clearance is added to the DIAMETER, not per side. "
              "Leave vent_d at 0 for anything that can leak — a vent under the pocket drips onto the desk.",
    ),
)
def socket_array(bore_d: float = 12.0, depth: float = 30.0, count: int = 1, pitch: float = 18.0,
                 rows: int = 1, row_pitch: float | None = None, clearance: float = 0.6,
                 lead_in: float = 1.2, vent_d: float = 0.0, vent_len: float = 0.0) -> Part:
    """Sockets on a ``count`` x ``rows`` grid centred on the origin, rims in the z=0 plane.

    Subtract from a body whose top face is at ``top_z``::

        block = block - Pos(x, y, top_z) * socket_array(...)

    The wall left between two sockets is ``pitch - bore_d - clearance``; keep it at 2 mm or more
    (5 perimeters at a 0.4 nozzle) for anything that gets pushed sideways.

    Example:
        holder = block - Pos(0, 0, block_h) * socket_array(11.0, depth=22, count=2, pitch=26)
    """
    r = (bore_d + clearance) / 2
    socket = Cylinder(r, depth, align=_ALIGN_TOP)
    if lead_in > 0:
        socket += Pos(0, 0, -lead_in) * Cone(r, r + lead_in, lead_in, align=_ALIGN_BOTTOM)
    if vent_d > 0 and vent_len > 0:
        socket += Pos(0, 0, -depth) * Cylinder(vent_d / 2, vent_len, align=_ALIGN_TOP)
    return Part() + [loc * socket for loc in GridLocations(pitch, row_pitch or pitch, count, rows)]
