"""Feet and rubber-foot recesses."""
from __future__ import annotations

from build123d import Align, Axis, Cylinder, Part, chamfer

from lib.component import MaterialNotes, component

_ALIGN_BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@component(
    id="primitives.foot", version="1.0.0",
    summary="Cylindrical foot / bumper standing on z=0 with a chamfered bed edge.",
    tags=["foot", "feet", "bumper", "standoff", "base"],
    units={"d": "mm", "height": "mm", "bed_chamfer": "mm"},
    descriptions={"d": "foot diameter", "height": "foot height", "bed_chamfer": "chamfer on the bed-contact edge"},
    material_notes=MaterialNotes(validated=["PLA", "PETG", "TPU"], orientation="printed as part of the body, bed side down"),
)
def foot(d: float = 8.0, height: float = 2.0, bed_chamfer: float = 0.4) -> Part:
    """Example:
        body = body + [loc * foot() for loc in GridLocations(80, 50, 2, 2)]
    """
    f = Cylinder(d / 2, height, align=_ALIGN_BOTTOM)
    if bed_chamfer > 0:
        f = chamfer(f.edges().group_by(Axis.Z)[0], bed_chamfer)
    return f


@component(
    id="primitives.rubber_foot_recess", version="1.0.0",
    summary="Negative (subtract me) shallow recess to locate a stick-on rubber foot; top face at z=0, extends down.",
    tags=["foot", "rubber", "recess", "pocket", "negative"],
    units={"d": "mm", "depth": "mm", "clearance": "mm"},
    descriptions={"d": "rubber foot diameter", "depth": "recess depth", "clearance": "added to diameter"},
    material_notes=MaterialNotes(validated=["PLA"], orientation="any"),
)
def rubber_foot_recess(d: float = 10.0, depth: float = 0.8, clearance: float = 0.4) -> Part:
    """Example:
        body = body - [loc * rubber_foot_recess(10) for loc in GridLocations(80, 50, 2, 2)]
    """
    from build123d import Pos
    return Pos(0, 0, -depth) * Cylinder((d + clearance) / 2, depth + 1, align=_ALIGN_BOTTOM)
