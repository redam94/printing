"""Metric hardware dimension tables shared by fastener components.

All values in millimetres.  Sources and verification status are documented in
``.claude/skills/printable-parts/references/hardware_dimensions.md`` — update
both together.  These are *nominal* hardware dimensions; print compensation
(hole oversize, clearance) is applied by the components, not here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Screw:
    size: str
    d: float                 # nominal thread diameter
    pitch: float             # coarse thread pitch
    clearance_fine: float    # ISO 273 fine series
    clearance_medium: float  # ISO 273 medium series (default for printed parts)
    clearance_coarse: float  # ISO 273 coarse series
    tap_drill: float         # metal tap drill (d - pitch)
    plastic_pilot: float     # pilot for thread-forming directly into printed plastic
    socket_head_d: float     # ISO 4762 head diameter (dk max)
    socket_head_h: float     # ISO 4762 head height (k)
    button_head_d: float     # ISO 7380 head diameter
    button_head_h: float     # ISO 7380 head height
    pan_head_d: float        # ISO 7045 / DIN 7985 pan head dia
    csk_head_d: float        # ISO 10642 countersunk head dia (theoretical)
    nut_af: float            # ISO 4032 hex nut width across flats (s)
    nut_ac: float            # across corners (e, min)
    nut_h: float             # ISO 4032 nut thickness (m max)
    washer_od: float         # ISO 7089 washer outer dia
    washer_t: float          # ISO 7089 washer thickness


@dataclass(frozen=True)
class HeatSetInsert:
    size: str
    od: float          # knurl outer diameter
    length: float      # insert length
    hole_d: float      # recommended hole diameter in the printed part
    min_wall: float    # minimum plastic around the insert (radial)

    @property
    def min_boss_od(self) -> float:
        return self.hole_d + 2 * self.min_wall


# ISO 273 clearance, ISO 4762/7380/7045/10642 heads, ISO 4032 nuts, ISO 7089 washers.
SCREWS: dict[str, Screw] = {
    #                 d    pitch  fine  med  coarse tap   pilot sock_d sock_h btn_d btn_h  pan_d csk_d nut_af nut_ac nut_h wash_od wash_t
    "M2":   Screw("M2",   2.0, 0.40, 2.2, 2.4, 2.6,  1.6,  1.7,  3.8,  2.0,  3.8,  1.3,  3.7,  3.8,  4.0,  4.32, 1.6,  5.0, 0.35),
    "M2.5": Screw("M2.5", 2.5, 0.45, 2.7, 2.9, 3.1,  2.05, 2.2,  4.5,  2.5,  4.7,  1.5,  4.7,  4.7,  5.0,  5.45, 2.0,  6.0, 0.55),
    "M3":   Screw("M3",   3.0, 0.50, 3.2, 3.4, 3.6,  2.5,  2.7,  5.5,  3.0,  5.7,  1.65, 5.7,  6.0,  5.5,  6.01, 2.4,  7.0, 0.55),
    "M4":   Screw("M4",   4.0, 0.70, 4.3, 4.5, 4.8,  3.3,  3.7,  7.0,  4.0,  7.6,  2.2,  7.64, 8.0,  7.0,  7.66, 3.2,  9.0, 0.9),
    "M5":   Screw("M5",   5.0, 0.80, 5.3, 5.5, 5.8,  4.2,  4.7,  8.5,  5.0,  9.5,  2.75, 9.2,  10.0, 8.0,  8.79, 4.7, 10.0, 1.0),
}
# Button-head (ISO 7380-1) starts at M3; M2/M2.5 button values are vendor-typical, not ISO.

# Brass heat-set inserts for thermoplastics (CNC Kitchen TC-series / Ruthex RX-series).
HEAT_SET_INSERTS: dict[str, HeatSetInsert] = {
    #                          od   length hole  min_wall   (CNC Kitchen "standard" length; Ruthex RX-M3x5.7 identical)
    "M2":   HeatSetInsert("M2",   3.6, 3.0,  3.2, 1.6),
    "M2.5": HeatSetInsert("M2.5", 4.6, 4.0,  4.0, 1.6),
    "M3":   HeatSetInsert("M3",   4.6, 5.7,  4.0, 1.6),
    "M4":   HeatSetInsert("M4",   6.3, 8.1,  5.6, 2.0),
    "M5":   HeatSetInsert("M5",   7.1, 9.5,  6.4, 2.0),
}

NOZZLE_D = 0.4  # mm; wall thicknesses should be multiples of this


def screw(size: str) -> Screw:
    try:
        return SCREWS[size.upper()]
    except KeyError:
        raise KeyError(f"unknown screw size {size!r}; known: {sorted(SCREWS)}") from None


def heat_set(size: str) -> HeatSetInsert:
    try:
        return HEAT_SET_INSERTS[size.upper()]
    except KeyError:
        raise KeyError(f"unknown insert size {size!r}; known: {sorted(HEAT_SET_INSERTS)}") from None
