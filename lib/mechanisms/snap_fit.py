"""Ridge-and-groove snap features for lids and covers (annular / linear snap)."""
from __future__ import annotations

from build123d import Align, Box, Circle, Part, Plane, Pos, Rot, extrude

from lib.component import MaterialNotes, component

_NOTES = MaterialNotes(
    validated=["PETG", "PLA"],
    orientation="ridge running horizontally along a vertical wall prints fine (the half-round is a shallow overhang)",
    notes="Interference 0.4-0.6 mm total for PETG walls 1.2-1.6 thick; PLA prefers <=0.4.",
)


@component(
    id="mechanisms.snap_ridge", version="1.0.0",
    summary="Half-round snap ridge (bead) running along X, protruding in +Y from a wall face at y=0; sits on a lid lip.",
    tags=["snap", "ridge", "bead", "lid", "friction", "detent", "compliant"],
    units={"length": "mm", "r": "mm", "end_taper": "mm"},
    descriptions={"length": "ridge length along X", "r": "bead radius (protrusion)", "end_taper": "reserved (0)"},
    material_notes=_NOTES,
)
def snap_ridge(length: float = 20.0, r: float = 0.6, end_taper: float = 0.0) -> Part:
    """Example:
        lip = lip + Pos(0, lip_face_y, z) * snap_ridge(length=lip_len - 4, r=0.6)
    """
    bead = extrude(Plane.YZ * Circle(r), amount=length / 2, both=True)
    # keep only the half protruding in +Y
    return bead & Box(length + 2, 2 * r + 1, 2 * r + 1, align=(Align.CENTER, Align.MIN, Align.CENTER))


@component(
    id="mechanisms.snap_groove", version="1.0.0",
    summary="Negative (subtract me) half-round groove matching snap_ridge, cut into a wall face at y=0 going into -Y.",
    tags=["snap", "groove", "detent", "lid", "negative", "compliant"],
    units={"length": "mm", "r": "mm", "clearance": "mm"},
    descriptions={"length": "groove length along X", "r": "matching ridge radius", "clearance": "added to radius so the bead seats without binding"},
    material_notes=_NOTES,
)
def snap_groove(length: float = 20.0, r: float = 0.6, clearance: float = 0.1) -> Part:
    """Example:
        body = body - Pos(0, inner_wall_y, z) * snap_groove(length=lip_len, r=0.6)
    """
    bead = extrude(Plane.YZ * Circle(r + clearance), amount=length / 2, both=True)
    return bead & Box(length + 2, 2 * r + 2, 2 * r + 2, align=(Align.CENTER, Align.MAX, Align.CENTER))
