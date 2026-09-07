"""Living hinges: thin-web and lattice styles."""
from __future__ import annotations

from build123d import Align, Axis, Box, GridLocations, Part, Pos, Rectangle, Sketch, extrude, fillet

from lib.component import MaterialNotes, component


@component(
    id="mechanisms.living_hinge_web", version="1.0.0",
    summary="Thin flexible web joining two thicker panels (single-strip living hinge), hinge axis along Y, printed flat.",
    tags=["hinge", "living hinge", "flexible", "web", "lid", "compliant", "fold"],
    units={"width": "mm", "web_thickness": "mm", "web_length": "mm", "panel_t": "mm", "panel_len": "mm", "fillet_r": "mm"},
    descriptions={
        "width": "hinge width along the axis (Y)", "web_thickness": "flexing web thickness (1-2 layers: 0.4-0.6)",
        "web_length": "web span between the panels (X)", "panel_t": "thickness of the joined panels",
        "panel_len": "length of each stub panel included (X) — union your real panels onto these",
        "fillet_r": "fillet where the web meets the panels (spreads strain)",
    },
    material_notes=MaterialNotes(
        validated=["PETG", "TPU"],
        orientation="flat on the bed, hinge axis in the bed plane; the web is then 1-2 continuous layers with extrusion lines along the axis",
        notes="PLA fatigue-cracks within tens of cycles; PP and TPU are best. Fold immediately after printing while warm for PETG.",
    ),
)
def living_hinge_web(width: float = 30.0, web_thickness: float = 0.5, web_length: float = 2.0, panel_t: float = 1.6,
                     panel_len: float = 5.0, fillet_r: float = 0.3) -> Part:
    """Web sits at the bottom (z=0 to web_thickness), centred at x=0; panels extend to +/-X.

    Example:
        hinge = living_hinge_web(width=40, web_thickness=0.5)
        part = left_panel + hinge + right_panel
    """
    web = Box(web_length, width, web_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
    left = Pos(-(web_length / 2 + panel_len / 2), 0, 0) * Box(panel_len, width, panel_t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    right = Pos(web_length / 2 + panel_len / 2, 0, 0) * Box(panel_len, width, panel_t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part = left + web + right
    if fillet_r > 0:
        # inner corners where the web top meets panel inner faces
        corners = part.edges().filter_by(Axis.Y).filter_by(lambda e: abs(e.center().Z - web_thickness) < 1e-6 and abs(abs(e.center().X) - web_length / 2) < 1e-6)
        if corners:
            part = fillet(corners, min(fillet_r, (panel_t - web_thickness) * 0.9, web_length / 2 * 0.9))
    return part


@component(
    id="mechanisms.living_hinge_lattice", version="1.0.0",
    summary="Lattice (kerf-style) living hinge: staggered slots cut through a panel so it can bend about the Y axis; returns the slot pattern to subtract.",
    tags=["hinge", "living hinge", "lattice", "kerf", "flexible", "bend", "compliant"],
    units={"length": "mm", "width": "mm", "slot_w": "mm", "slot_gap": "mm", "column_pitch": "mm", "link_w": "mm"},
    descriptions={
        "length": "bend region length along X (direction of bending)", "width": "panel width along the hinge axis (Y)",
        "slot_w": "slot width (X)", "slot_gap": "gap between consecutive slots along Y in the same column (the torsion links)",
        "column_pitch": "X pitch between slot columns", "link_w": "solid material between slots in Y = torsion link width",
    },
    material_notes=MaterialNotes(
        validated=["PLA", "PETG"],
        orientation="flat on the bed; slot walls vertical. Works even in PLA because links twist rather than bend across layers.",
        notes="Bend radius ~ length / total bend angle; more columns = gentler bend.",
    ),
)
def living_hinge_lattice(length: float = 20.0, width: float = 40.0, slot_w: float = 1.0, slot_gap: float = 3.0,
                         column_pitch: float = 3.0, link_w: float = 1.6) -> Sketch:
    """Slots alternate offset by half a period between columns. Subtract (extruded through the panel) from your plate.

    Example:
        plate = plate - extrude(living_hinge_lattice(20, 40), amount=plate_t)
    """
    n_cols = max(int(length // column_pitch), 1)
    period = slot_gap + link_w
    slot_len = slot_gap  # each slot's Y length
    sk = Sketch()
    x0 = -(n_cols - 1) * column_pitch / 2
    for i in range(n_cols):
        x = x0 + i * column_pitch
        offset = (period / 2) if i % 2 else 0.0
        # slots spanning the width, leaving link_w between them
        ys = []
        y = -width / 2 + offset - period
        while y < width / 2 + period:
            ys.append(y)
            y += period
        for yc in ys:
            lo, hi = max(yc - slot_len / 2, -width / 2), min(yc + slot_len / 2, width / 2)
            if hi - lo > 0.2:
                sk = sk + Pos(x, (lo + hi) / 2) * Rectangle(slot_w, hi - lo)
    return sk
