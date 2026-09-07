"""VESA FDMI mount patterns."""
from __future__ import annotations

from build123d import Circle, GridLocations, Sketch

from lib.component import MaterialNotes, component

VESA_PATTERNS: dict[str, tuple[float, float, str]] = {
    "75":     (75.0, 75.0, "M4"),
    "100":    (100.0, 100.0, "M4"),
    "200x100": (200.0, 100.0, "M4"),
    "200":    (200.0, 200.0, "M6"),
}


@component(
    id="patterns.vesa_mount", version="1.0.0",
    summary="VESA MIS-D/E four-hole pattern (75, 100, 200x100, 200) centred on the origin.",
    tags=["vesa", "monitor", "tv", "mount", "holes", "M4", "M6"],
    units={"pattern": "enum", "hole_d": "mm", "print_oversize": "mm"},
    descriptions={"pattern": "75, 100, 200x100 or 200", "hole_d": "hole diameter; default = M4 medium clearance (4.5) or M6 (6.6)",
                  "print_oversize": "FDM oversize"},
    material_notes=MaterialNotes(validated=["PETG"], orientation="any (2D pattern); print the bracket so screw load is in-plane"),
)
def vesa_mount(pattern: str = "100", hole_d: float | None = None, print_oversize: float = 0.2) -> Sketch:
    """Example:
        plate = RectangleRounded(120, 120, 5) - vesa_mount("100")
    """
    dx, dy, screw_size = VESA_PATTERNS[pattern]
    d = (hole_d if hole_d is not None else {"M4": 4.5, "M6": 6.6}[screw_size]) + print_oversize
    return Sketch() + [loc * Circle(d / 2) for loc in GridLocations(dx, dy, 2, 2)]
