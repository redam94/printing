"""Ventilation slot pattern."""
from __future__ import annotations

from build123d import GridLocations, Sketch, SlotOverall

from lib.component import MaterialNotes, component


@component(
    id="primitives.vent_slots", version="1.0.0",
    summary="Grid of rounded ventilation slots filling a rectangular area, centred on the origin (subtract from a wall).",
    tags=["vent", "slots", "cooling", "airflow", "grille", "panel"],
    units={"area_l": "mm", "area_w": "mm", "slot_w": "mm", "pitch": "mm", "slot_l": "mm", "rows": "count", "rotation": "deg"},
    descriptions={
        "area_l": "length of the vented area along the slots", "area_w": "width across the slots",
        "slot_w": "slot width (>= 1.5 for reliable bridging / cleaning)", "pitch": "centre-to-centre across slots (web = pitch - slot_w, keep >= 1.2)",
        "slot_l": "slot length; default fills area_l", "rows": "number of slot columns along the length; default 1",
        "rotation": "rotate the whole pattern in-plane",
    },
    material_notes=MaterialNotes(validated=["PLA", "PETG"], orientation="on a vertical wall run slots vertically so they need no bridging"),
)
def vent_slots(area_l: float = 40.0, area_w: float = 20.0, slot_w: float = 1.6, pitch: float = 4.0,
               slot_l: float | None = None, rows: int = 1, rotation: float = 0.0) -> Sketch:
    """Example:
        side = side - extrude(Plane.XZ * vent_slots(40, 16), amount=wall, both=True)
    """
    n_across = max(int(area_w // pitch), 1)
    gap = 2.0
    slot_l = (area_l - (rows - 1) * gap) / rows if slot_l is None else slot_l
    x_pitch = slot_l + gap
    sk = Sketch() + [loc * SlotOverall(slot_l, slot_w) for loc in GridLocations(x_pitch, pitch, rows, n_across)]
    return sk.rotate(__import__("build123d").Axis.Z, rotation) if rotation else sk
