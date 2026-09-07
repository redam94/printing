"""Flexures: compliant linear guides."""
from __future__ import annotations

from build123d import Align, Box, Part, Pos

from lib.component import MaterialNotes, component


@component(
    id="mechanisms.parallel_flexure", version="1.0.0",
    summary="Parallel-beam flexure stage: fixed block and moving block joined by N thin beams; moving block translates in Y.",
    tags=["flexure", "compliant", "spring", "stage", "parallel", "linear guide", "button"],
    units={"beam_length": "mm", "beam_thickness": "mm", "beam_count": "count", "beam_spacing": "mm", "depth": "mm",
           "block_w": "mm"},
    descriptions={
        "beam_length": "beam span along X between the blocks", "beam_thickness": "beam thickness (Y) — flexing dimension, 0.8-1.2",
        "beam_count": "number of parallel beams (2 = classic parallelogram)", "beam_spacing": "Y pitch between beams",
        "depth": "part depth (Z), i.e. beam height", "block_w": "X width of the two end blocks",
    },
    material_notes=MaterialNotes(
        validated=["PETG"],
        orientation="flat on the bed with beams in the XY plane so bending stress runs along the extrusion lines, not across layers",
        notes="Stiffness ~ N*E*depth*t^3/L^3. Halve thickness for 8x softer. PLA works for tiny strokes only.",
    ),
)
def parallel_flexure(beam_length: float = 20.0, beam_thickness: float = 1.0, beam_count: int = 2, beam_spacing: float = 8.0,
                     depth: float = 6.0, block_w: float = 6.0) -> Part:
    """Fixed block at -X, moving block at +X; whole thing stands on z=0 and is centred in Y.

    Example:
        stage = parallel_flexure(beam_length=25, beam_thickness=0.8)
        button = stage + Pos(x_moving_block, 0, 0) * button_cap
    """
    span_y = (beam_count - 1) * beam_spacing + beam_thickness
    blocks = Part()
    for x in (-(beam_length / 2 + block_w / 2), beam_length / 2 + block_w / 2):
        blocks = blocks + Pos(x, 0, 0) * Box(block_w, span_y + 2 * beam_thickness, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    beams = Part()
    y0 = -(beam_count - 1) * beam_spacing / 2
    for i in range(beam_count):
        beams = beams + Pos(0, y0 + i * beam_spacing, 0) * Box(beam_length + 0.02, beam_thickness, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return blocks + beams
