"""Bistable compliant mechanisms: a shuttle that snaps between two rest positions and stays there.

Numbers come from two BYU Compliant Mechanisms Research references filed under
``ideas/bistable_compliant_switch/references/`` (Printables 581013 "Bistable Compliant Mechanism",
both STL variants measured; 581016 "Bistable Compliant Switch").  Hinge width 0.5, beam width 5.0
and depth 6.35 mm are MEASURED off the meshes; the beam span and pre-tilt are estimated from the
renders and are the two parameters a coupon print must confirm.
"""
from __future__ import annotations

import math

from build123d import Align, Box, Part, Pos, Rot

from lib.component import MaterialNotes, component


def bistable_travel(span: float = 37.0, pretilt: float = 8.0) -> float:
    """Shuttle travel between the two stable positions: 2 * span * sin(pretilt).

    Not a component; import it into a model to place whatever the shuttle carries (a hook, a
    button face, a jaw) in each state.  At the defaults: ~10.3 mm.
    """
    return 2.0 * span * math.sin(math.radians(pretilt))


def bistable_envelope(span: float = 37.0, beam_width: float = 5.0, beam_count: int = 2, beam_spacing: float = 12.0, pretilt: float = 8.0,
                      shuttle_w: float = 8.0, anchor_w: float = 8.0, margin: float = 3.0) -> dict:
    """Where things are for a given parameter set (same defaults as the component). Not a component.

    ``rise``: shuttle Y offset in the rest state (mirror state is at -rise); ``travel`` = 2*rise;
    ``run``: X projection of a beam; ``block_h``: Y height of shuttle and anchors;
    ``x_anchor_face``: X of the anchor inner faces; ``x_outer``: X of the anchor outer faces.
    A host frame must clear the shuttle over y in [-rise - block_h/2, rise + block_h/2].
    """
    rise = span * math.sin(math.radians(pretilt))
    run = span * math.cos(math.radians(pretilt))
    span_y = (beam_count - 1) * beam_spacing + beam_width
    block_h = span_y + 2 * margin + rise
    x_anchor_face = shuttle_w / 2 + run
    return {"rise": rise, "travel": 2 * rise, "run": run, "block_h": block_h, "x_anchor_face": x_anchor_face,
            "x_outer": x_anchor_face + anchor_w, "span_y": span_y}


def hinged_beam(span: float, beam_width: float, hinge_width: float, hinge_length: float, depth: float, overlap: float,
                neck_plate: float = 0.0) -> Part:
    """One neck-body-neck beam along +X from x=0 (anchor face) to x=span (shuttle face), centred on y=0, standing on z=0.

    The building block of every pre-tilted beam mechanism here: ``bistable_beam_pair`` uses N of
    them per side, ``mechanisms.split_ring_clip`` one per side (half the mechanism, scaled down).
    Hinges are short necks at both ends; the beam body is the wide middle.  Both necks run
    ``overlap`` past the faces they meet so the boolean fuses them into the blocks.  With
    ``neck_plate`` > 0 each neck is two plates of that Z thickness at the bottom and top faces with
    nothing between (the ring-clip reference does this: half the hinge stiffness for the same
    neck width, and the same footprint); 0 runs the necks the full depth.  Not a component.
    """
    body_len = span - 2 * hinge_length
    if body_len <= 0:
        raise ValueError("span must exceed twice the hinge length")
    if not 0 <= neck_plate <= depth / 2:
        raise ValueError("neck_plate must be between 0 and half the depth")
    neck = hinge_length + overlap
    body = Pos(hinge_length, 0, 0) * Box(body_len, beam_width, depth, align=(Align.MIN, Align.CENTER, Align.MIN))
    plate = neck_plate if neck_plate > 0 else depth
    necks = Part()
    for x0 in (-overlap, span - hinge_length):  # root neck buried in the anchor, tip neck running past x=span into the shuttle
        for z0 in ((0.0,) if neck_plate == 0 else (0.0, depth - plate)):
            necks = necks + Pos(x0, 0, z0) * Box(neck, hinge_width, plate, align=(Align.MIN, Align.CENTER, Align.MIN))
    return necks + body


_beam = hinged_beam  # old private name


@component(
    id="mechanisms.bistable_beam_pair", version="0.2.0",
    summary="Fully compliant bistable slider: a central shuttle held between two fixed anchors by N pre-tilted beams per side with living-hinge necks; snaps between +Y and -Y rest positions.",
    tags=["bistable", "compliant", "snap-through", "toggle", "switch", "shuttle", "living hinge", "flexure", "print in place"],
    units={"span": "mm", "beam_width": "mm", "beam_count": "count", "beam_spacing": "mm", "pretilt": "deg", "hinge_width": "mm",
           "hinge_length": "mm", "depth": "mm", "shuttle_w": "mm", "anchor_w": "mm", "margin": "mm", "neck_plate": "mm"},
    descriptions={
        "span": "straight length of each beam from anchor face to shuttle face, hinge to hinge (estimated from the reference renders)",
        "beam_width": "in-plane width of the beam body between the hinges (measured 5.0 on both reference variants)",
        "beam_count": "beams per side; 2 parallel beams per side is the reference (4 beams, 8 hinges)",
        "beam_spacing": "Y pitch between the parallel beams of one side",
        "pretilt": "angle of the beams above the X axis in the rest state; the shuttle sits 2*span*sin(pretilt) higher than after a snap",
        "hinge_width": "in-plane width of the living-hinge necks at both ends of every beam (measured 0.5 = one 0.4 mm line)",
        "hinge_length": "length of each neck along the beam",
        "depth": "part height (Z) = hinge and beam height (measured 6.35)",
        "shuttle_w": "X width of the central moving block",
        "anchor_w": "X width of each fixed end block (fuse these to the host part)",
        "margin": "extra Y on the blocks beyond the outermost beam",
        "neck_plate": "0 = necks run the full depth (the reference and the validated coupon); > 0 = each neck is two plates of this Z thickness at the faces with nothing between, half the hinge stiffness (the split_ring_clip reference uses 1.9 of 7.2)",
    },
    material_notes=MaterialNotes(
        validated=["PLA"],
        orientation="flat on the bed, beams and hinges in the XY plane (Z = depth) so bending runs along the extrusion lines; never stand it up",
        notes="Validated in PLA by the bistable_coupon print of 2026-09-11 (closed frame, plunger tunnels): snaps both ways and holds, at the defaults below. Reference (BYU CMR, Printables 581013) measured: hinge 0.5 mm, beam 5.0 mm, depth 6.35 mm; span 37 mm and pre-tilt 8 deg were estimated from renders and the coupon confirmed they snap. The authors recommend polypropylene; PETG expected to work and is still unprinted here. PLA may creep when parked in one state for long and fatigue at the necks; not yet observed, cycle it and watch the necks for whitening. A 0.5 mm neck is one 0.4 mm line: enable thin-wall / Arachne perimeters in the slicer or widen hinge_width to 0.8 (two lines) and re-tune.",
    ),
)
def bistable_beam_pair(span: float = 37.0, beam_width: float = 5.0, beam_count: int = 2, beam_spacing: float = 12.0, pretilt: float = 8.0,
                       hinge_width: float = 0.5, hinge_length: float = 2.0, depth: float = 6.35, shuttle_w: float = 8.0,
                       anchor_w: float = 8.0, margin: float = 3.0, neck_plate: float = 0.0) -> Part:
    """Shuttle at x=0 raised by span*sin(pretilt) in +Y; anchors at -X and +X centred on y=0; everything stands on z=0.

    Each side has ``beam_count`` parallel beams tilted ``pretilt`` degrees upward toward the shuttle,
    each with a living-hinge neck at both ends (a pseudo-rigid-body four-bar per side).  Pushing the
    shuttle down past the flat position snaps it to the mirror state at -span*sin(pretilt); the travel is
    ``bistable_travel(span, pretilt)``.  Anchors are meant to be fused into the host part (a frame, a
    wall, a lid rim); the shuttle carries the working feature.

    Example:
        stage = bistable_beam_pair()                      # 37 mm beams, 8 deg, 0.5 mm necks
        env = bistable_envelope()                         # rise, travel (~10.3), block_h, x_outer ...
        frame = frame_around(env)                         # host geometry, any library primitive
        toggle = frame + stage + Pos(0, env["rise"], 0) * button_cap
    """
    overlap = hinge_width + 0.1  # the tilted neck end must bury fully in the block face, not just touch one corner
    env = bistable_envelope(span, beam_width, beam_count, beam_spacing, pretilt, shuttle_w, anchor_w, margin)
    rise, block_h, x_anchor_face = env["rise"], env["block_h"], env["x_anchor_face"]  # block_h: beams meet both blocks in either state

    anchors = Part()
    for sx in (-1, 1):
        anchors = anchors + Pos(sx * (x_anchor_face + anchor_w / 2), 0, 0) * Box(anchor_w, block_h, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shuttle = Pos(0, rise, 0) * Box(shuttle_w, block_h, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))

    beam = hinged_beam(span, beam_width, hinge_width, hinge_length, depth, overlap, neck_plate)
    beams = Part()
    y0 = -(beam_count - 1) * beam_spacing / 2
    for i in range(beam_count):
        y = y0 + i * beam_spacing
        # left side: from the left anchor face rising toward the shuttle
        beams = beams + Pos(-x_anchor_face, y, 0) * Rot(0, 0, pretilt) * beam
        # right side: mirror, from the right anchor face rising toward the shuttle
        beams = beams + Pos(x_anchor_face, y, 0) * Rot(0, 0, 180 - pretilt) * beam
    return anchors + shuttle + beams
