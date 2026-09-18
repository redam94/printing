"""Printed springs: a bowed leaf spring and an in-plane serpentine (meander) spring."""
from __future__ import annotations

import math

from build123d import Align, Box, Circle, Part, Pos, extrude

from lib.component import MaterialNotes, component

_NOTES = MaterialNotes(
    validated=[],
    orientation="flat on the bed, the spring flexing in the bed plane (bending stress runs along the extrusion lines, never across layers)",
    notes="UNVALIDATED: no test print yet. PETG for anything cycled; PLA holds a small preload but creeps and fatigues. "
          "Keep the beam >= 3 lines (1.2 mm) at a 0.4 nozzle unless the part is declared hinged.",
)


@component(
    id="mechanisms.leaf_spring", version="1.0.0",
    summary="Bowed leaf spring (circular-arc beam) between two points on the X axis, bulging toward +Y; standing on z=0.",
    tags=["spring", "leaf", "leaf spring", "arc", "bow", "gate", "compliant", "cantilever", "carabiner", "clip"],
    units={"length": "mm", "thickness": "mm", "bow": "mm", "depth": "mm", "end_overlap": "mm"},
    descriptions={
        "length": "chord: X distance between the two ends (the ends sit on y=0 at +/- length/2)",
        "thickness": "beam thickness measured radially (the flexing dimension, in the bed plane)",
        "bow": "sagitta: how far the beam's outer face bulges in +Y at the middle; 0 gives a straight beam",
        "depth": "part depth = print height (Z)",
        "end_overlap": "extra straight length past each end along the arc tangent, so the ends bury into their blocks",
    },
    material_notes=_NOTES,
)
def leaf_spring(length: float = 30.0, thickness: float = 1.2, bow: float = 3.0, depth: float = 6.0, end_overlap: float = 1.0) -> Part:
    """The beam's mid-surface runs through (-length/2, 0) and (length/2, 0) with its middle at (0, bow).
    Union the ends into whatever holds them (a ring end, a jaw); as a cantilever, anchor one end
    and leave the other free.  Strain at the root of a cantilever of chord L deflected d at the tip
    is about 1.5 * thickness * d / L^2 (0.7% for the defaults deflected 3 mm at 28 mm).

    Example:
        gate = Pos(x_gap_centre, y_edge, 0) * leaf_spring(length=28, thickness=1.2, bow=2.5, depth=6)
        body = ring + gate          # one end overlaps the ring; the other stops short of the nose
    """
    half = length / 2
    if bow <= 1e-6:
        return Box(length + 2 * end_overlap, thickness, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    R = (half * half + bow * bow) / (2 * bow)                       # arc radius through the three points
    cy = bow - R                                                    # arc centre (below the chord)
    ring = Circle(R + thickness / 2) - Circle(R - thickness / 2)
    arc = extrude(Pos(0, cy) * ring, amount=depth)
    # keep the arc between the chord ends (vertical end cuts at +/- length/2), then add tangent stubs so the ends bury into their blocks
    keep = Box(length, bow + thickness + 1, depth + 2, align=(Align.CENTER, Align.MIN, Align.MIN))
    beam = arc & Pos(0, -thickness / 2, -1) * keep
    if end_overlap > 0:
        ang = math.atan2(half, -cy)                                  # angle of the end point from the arc centre
        for sx in (-1, 1):
            stub = Box(end_overlap + 0.02, thickness, depth, align=(Align.MAX, Align.CENTER, Align.MIN))
            rot = -math.degrees(ang) * sx
            from build123d import Rot
            beam = beam + Pos(sx * half, 0, 0) * Rot(0, 0, rot) * (stub if sx < 0 else Rot(0, 0, 180) * stub)
    return beam


@component(
    id="mechanisms.serpentine_spring", version="1.0.0",
    summary="In-plane serpentine (meander) spring along X between two end blocks, compliant along X; standing on z=0, centred on the origin.",
    tags=["spring", "serpentine", "meander", "zigzag", "compliant", "compression", "self-centring", "button", "holder"],
    units={"length": "mm", "amplitude": "mm", "legs": "count", "beam_t": "mm", "depth": "mm", "end_block": "mm"},
    descriptions={
        "length": "X span of the meander between the inner faces of the end blocks",
        "amplitude": "Y extent of the meander (leg length, centre to centre of the links)",
        "legs": "number of transverse legs (more legs = softer, longer travel)",
        "beam_t": "beam thickness everywhere (the flexing dimension)",
        "depth": "part depth = print height (Z)",
        "end_block": "X width of the two end blocks the spring pushes with; their Y size is amplitude + 2 * beam_t",
    },
    material_notes=_NOTES,
)
def serpentine_spring(length: float = 20.0, amplitude: float = 8.0, legs: int = 4, beam_t: float = 1.0, depth: float = 6.0,
                      end_block: float = 3.0) -> Part:
    """Fixed block at -X, pushing block at +X (or the other way round: it is symmetric).  Compressing
    along X bends every leg; stiffness scales with beam_t^3 / amplitude^3 and falls with more legs.
    Legs are joined by links alternating between +Y and -Y; the first and last legs join their
    blocks by a link on the X axis.

    Example:
        spring = serpentine_spring(length=24, amplitude=10, legs=5, beam_t=1.0, depth=8)
        pad = Pos(24 / 2 + 3 + pad_w / 2, 0, 0) * Box(pad_w, pad_h, 8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    """
    legs = max(int(legs), 1)
    half_a = amplitude / 2
    pitch = length / legs
    x0 = -length / 2 + pitch / 2
    xs = [x0 + i * pitch for i in range(legs)]
    part = Part()
    for x in xs:
        part = part + Pos(x, 0, 0) * Box(beam_t, amplitude + beam_t, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for i in range(legs - 1):
        y = half_a if i % 2 == 0 else -half_a
        xa, xb = xs[i], xs[i + 1]
        part = part + Pos((xa + xb) / 2, y, 0) * Box(xb - xa + beam_t, beam_t, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    block_h = amplitude + 2 * beam_t
    for sx in (-1, 1):
        x_face = sx * length / 2
        x_leg = xs[0] if sx < 0 else xs[-1]
        link = Box(abs(x_face - x_leg) + beam_t, beam_t, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
        part = part + Pos((x_face + x_leg) / 2, 0, 0) * link
        part = part + Pos(x_face + sx * end_block / 2, 0, 0) * Box(end_block + 0.02, block_h, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part
