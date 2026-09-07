"""Axial fan mounting patterns (holes + optional airflow cutout)."""
from __future__ import annotations

from build123d import Circle, GridLocations, Sketch

from lib.component import MaterialNotes, component

# fan frame size -> screw hole spacing (square), mm
FAN_HOLE_SPACING: dict[int, float] = {
    25: 20.0, 30: 24.0, 40: 32.0, 50: 40.0, 60: 50.0, 70: 61.5, 80: 71.5, 92: 82.5, 120: 105.0, 140: 124.5,
}
# screw hole diameter in the fan frame -> what to put in the mating panel (M3 self-tap for small, M4/#6-32 for 60+)
FAN_HOLE_D: dict[int, float] = {25: 2.9, 30: 3.2, 40: 3.4, 50: 4.3, 60: 4.3, 70: 4.5, 80: 4.5, 92: 4.5, 120: 4.3, 140: 4.3}


@component(
    id="patterns.fan_mount", version="1.0.0",
    summary="Axial fan four-hole pattern plus optional circular airflow cutout, centred on the origin.",
    tags=["fan", "cooling", "vent", "cutout", "30mm", "40mm", "80mm", "120mm", "holes"],
    units={"size": "mm", "hole_d": "mm", "cutout": "bool", "cutout_d": "mm", "print_oversize": "mm"},
    descriptions={
        "size": "fan frame size: 25, 30, 40, 50, 60, 70, 80, 92, 120, 140",
        "hole_d": "screw hole diameter; default per fan size (3.2 for 30 mm M3, 4.3-4.5 for 60 mm+)",
        "cutout": "include the circular airflow opening",
        "cutout_d": "airflow opening diameter; default = size - 2",
        "print_oversize": "FDM oversize added to the screw holes",
    },
    material_notes=MaterialNotes(validated=["PLA", "PETG"], orientation="any (2D pattern)"),
)
def fan_mount(size: int = 30, hole_d: float | None = None, cutout: bool = True, cutout_d: float | None = None, print_oversize: float = 0.2) -> Sketch:
    """Subtract from a wall to mount a fan.

    Example:
        side = Plane.XZ * (Rectangle(w, h) - fan_mount(30))
    """
    if size not in FAN_HOLE_SPACING:
        raise ValueError(f"unknown fan size {size}; known: {sorted(FAN_HOLE_SPACING)}")
    sp = FAN_HOLE_SPACING[size]
    hole_d = FAN_HOLE_D[size] if hole_d is None else hole_d
    sk = Sketch() + [loc * Circle((hole_d + print_oversize) / 2) for loc in GridLocations(sp, sp, 2, 2)]
    if cutout:
        sk = sk + Circle((size - 2 if cutout_d is None else cutout_d) / 2)
    return sk
