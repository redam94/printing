"""Cable pass-throughs."""
from __future__ import annotations

from build123d import Circle, Polygon, Sketch

from lib.component import MaterialNotes, component


@component(
    id="primitives.teardrop", version="1.0.0",
    summary="Teardrop hole profile (circle with a pointed top) so a horizontal-axis hole bridges without support; subtract from a vertical wall.",
    tags=["hole", "teardrop", "horizontal", "bridge", "overhang", "cable"],
    units={"d": "mm", "angle": "deg", "print_oversize": "mm"},
    descriptions={"d": "nominal hole diameter", "angle": "half-angle of the point (45 = printable without support)",
                  "print_oversize": "FDM oversize"},
    material_notes=MaterialNotes(validated=["PLA", "PETG"], orientation="hole axis horizontal, point up (+Y in the sketch)"),
)
def teardrop(d: float = 6.0, angle: float = 45.0, print_oversize: float = 0.3) -> Sketch:
    """Drawn in XY with the point in +Y; map onto the wall plane (e.g. Plane.XZ) so +Y becomes up.

    Example:
        wall = wall - extrude(Plane.XZ * Pos(x, z) * teardrop(cable_d), amount=wall_t, both=True)
    """
    import math
    r = (d + print_oversize) / 2
    a = math.radians(angle)
    # tangent points at +/-(90-angle) from +Y; apex height = r / sin(angle)
    tx, ty = r * math.cos(a), r * math.sin(a)
    apex = r / math.sin(a)
    return Sketch() + Circle(r) + Polygon((-tx, ty), (0, apex), (tx, ty))


@component(
    id="primitives.cable_grommet", version="1.0.0",
    summary="Cable pass-through cutout: teardrop hole for the cable plus a keyhole slit to the panel edge so a pre-terminated cable can be slipped in.",
    tags=["cable", "grommet", "pass-through", "strain relief", "keyhole", "slot"],
    units={"cable_d": "mm", "clearance": "mm", "slit_w": "mm", "slit_len": "mm"},
    descriptions={"cable_d": "cable outer diameter", "clearance": "added to diameter", "slit_w": "slit width (0 = no slit, plain teardrop)",
                  "slit_len": "slit length from hole centre in +Y (reach the panel edge)"},
    material_notes=MaterialNotes(validated=["PETG"], orientation="hole axis horizontal, slit pointing up"),
)
def cable_grommet(cable_d: float = 5.0, clearance: float = 0.6, slit_w: float = 0.0, slit_len: float = 10.0) -> Sketch:
    """Example:
        back = back - extrude(Plane.XZ * Pos(0, 10) * cable_grommet(4.0, slit_w=2.0, slit_len=12), amount=wall, both=True)
    """
    sk = teardrop(cable_d, print_oversize=clearance)
    if slit_w > 0:
        from build123d import Pos, Rectangle
        sk = sk + Pos(0, slit_len / 2) * Rectangle(slit_w, slit_len)
    return sk
