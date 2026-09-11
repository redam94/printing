"""Snap-on split-ring clip: half a bistable beam pair, scaled down, with a C-ring for a shuttle and sprung anchors.

Each arm is one ``hinged_beam`` from ``lib.mechanisms.bistable`` (thin neck, wide body, thin neck)
tilted like the bistable pair's beams; there is one per side instead of N, the shuttle is the split
ring, and the anchors are round posts on thin spring strips instead of fixed blocks.  Numbers come
from a reference mesh the user handed over (``Parametric_clip_VL_5.5.STL``, filed as
``ideas/ring_clip_5_5/references/file-5725bdb05c.md``): ring bore 5.05 for a 5.5 mm rod, wall 1.0,
necks 0.46, beam body 1.54 wide, post face to ring wall ~20.5 mm at ~14 deg, springs 0.55, rail 3.0,
depth 7.2, all MEASURED off the mesh.  The reference's necks exist only as two 1.9 mm plates at the
top and bottom faces with a 3.4 mm gap between them; ``neck_plate`` reproduces that (it is the same
option on ``hinged_beam`` and ``bistable_beam_pair``) and 0 switches it off.
"""
from __future__ import annotations

import math

from build123d import Align, Box, Circle, Part, Pos, Rectangle, RectangleRounded, Rot, extrude

from lib.component import MaterialNotes, component
from lib.mechanisms.bistable import hinged_beam


def split_ring_clip_envelope(rod_d: float = 5.5, grip: float = 0.45, wall: float = 1.0, ring_clear: float = 1.2, rail_t: float = 3.0,
                             arm_len: float = 20.5, arm_angle: float = 14.0, jaw_attach: float = -1.75, post_d: float = 2.0,
                             strip_t: float = 0.6) -> dict:
    """Where things are for a parameter set (same defaults as the component). Not a component.

    Ring centre is the origin; +Y is toward the rail; the rod enters from -Y.  Returns ``r_in``,
    ``r_out``, ``rail_bottom``, ``rail_top``, ``rail_len``, ``x_post``, ``y_post`` (post centres at
    ±x_post), ``width`` (overall X), ``y_min`` (lowest point: the post underside), and for the +X
    arm its ``ring_end`` (where the beam meets the ring wall) and ``post_end`` (where it meets the
    post face).  ``rise`` is what the ring would climb if the arms went flat, and ``ring_travel``
    how far it can actually climb before the rail stops it: the clip snaps through only if the
    second exceeds the first, which the defaults do not (it is a spring, not a toggle).
    """
    r_in = (rod_d - grip) / 2
    r_out = r_in + wall
    rail_bottom = r_out + ring_clear
    rail_top = rail_bottom + rail_t
    a = math.radians(arm_angle)
    ring_end = (math.sqrt(max(r_out**2 - jaw_attach**2, 0.0)), jaw_attach)   # beam tip on the ring's outer wall
    post_end = (ring_end[0] + arm_len * math.cos(a), ring_end[1] - arm_len * math.sin(a))   # beam root on the post face
    x_post = post_end[0] + post_d / 2 * math.cos(a)
    y_post = post_end[1] - post_d / 2 * math.sin(a)
    rail_len = 2 * (x_post + strip_t / 2)
    return {"r_in": r_in, "r_out": r_out, "rail_bottom": rail_bottom, "rail_top": rail_top, "rail_len": rail_len,
            "x_post": x_post, "y_post": y_post, "width": 2 * (x_post + post_d / 2), "y_min": y_post - post_d / 2,
            "ring_end": ring_end, "post_end": post_end, "rise": arm_len * math.sin(a), "ring_travel": ring_clear}


@component(
    id="mechanisms.split_ring_clip", version="0.2.0",
    summary="Snap-on split-ring clip: half a bistable beam pair, one hinged beam per side at a pre-tilt, a split C-ring (bore = rod - grip) for a shuttle and thin spring strips off a mounting rail for anchors.",
    tags=["clip", "ring clip", "snap-on", "rod", "cable", "compliant", "living hinge", "hinged beam", "spring", "holder", "print in place"],
    units={"rod_d": "mm", "grip": "mm", "wall": "mm", "ring_gap": "mm", "hinge_width": "mm", "hinge_length": "mm", "neck_plate": "mm",
           "arm_len": "mm", "arm_w": "mm", "arm_angle": "deg", "jaw_attach": "mm", "post_d": "mm", "strip_t": "mm",
           "ring_clear": "mm", "rail_t": "mm", "depth": "mm"},
    descriptions={
        "rod_d": "diameter of the rod, tube or cable the clip holds",
        "grip": "bore undersize: ring bore = rod_d - grip, so the closed jaws preload the rod (reference: 5.5 rod, 5.05 bore)",
        "wall": "ring wall thickness (measured 1.0)",
        "ring_gap": "width of the slit that splits the ring top and bottom; the rod enters through the bottom one",
        "hinge_width": "in-plane width of every living-hinge neck: both ends of each arm, and the bridge across the top slit (measured 0.46 = one 0.4 mm line); bistable_beam_pair's hinge_width",
        "hinge_length": "length of each neck along the arm; bistable_beam_pair's hinge_length",
        "neck_plate": "Z thickness of the two neck plates at the top and bottom faces (measured 1.9), the necks absent between them; 0 = necks run the full depth. Same option as bistable_beam_pair",
        "arm_len": "arm span from the post face to the ring wall, hinge to hinge (measured ~20.5); bistable_beam_pair's span",
        "arm_w": "width of the arm body between the necks (measured 1.54; 1.6 = four lines); bistable_beam_pair's beam_width",
        "arm_angle": "pre-tilt of the arms: angle below the X axis toward the posts (measured ~14 deg hinge to hinge); bistable_beam_pair's pretilt",
        "jaw_attach": "Y of the arm-to-ring neck relative to the ring centre; negative = below centre, must stay below the top bridge so pulling the arms outward opens the jaws",
        "post_d": "diameter of the round posts that anchor the arms to the strips",
        "strip_t": "thickness of the side strips, the return springs (measured 0.55; 0.6 = one line plus gap fill)",
        "ring_clear": "clear gap between the ring top and the rail underside; also how far the ring can climb, which keeps it short of the snap-through position",
        "rail_t": "thickness (Y) of the mounting rail",
        "depth": "part height (Z) = print height (measured 7.2)",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="flat on the bed, ring axis along Z, so every neck and strip bends in the bed plane; never stand it up",
        notes="UNVALIDATED here. The arms are bistable_beam_pair's hinged beams (validated in PLA at 0.5 mm necks, 6.35 deep) scaled down to a 1.6 mm body; reproduced from a downloaded mesh with no page or material notes. Necks are one 0.4 mm line and the strips one and a half, so print with thin-wall (Arachne) perimeters on. The strips and necks bend on every rod insertion; PETG expected to hold up, PLA expected to work for a few insertions and creep if the rod is oversize. A coupon print at the defaults (models/ring_clip_5_5) is the first test.",
    ),
)
def split_ring_clip(rod_d: float = 5.5, grip: float = 0.45, wall: float = 1.0, ring_gap: float = 0.5, hinge_width: float = 0.5,
                    hinge_length: float = 2.0, neck_plate: float = 1.9, arm_len: float = 20.5, arm_w: float = 1.6, arm_angle: float = 14.0,
                    jaw_attach: float = -1.75, post_d: float = 2.0, strip_t: float = 0.6, ring_clear: float = 1.2, rail_t: float = 3.0,
                    depth: float = 7.2) -> Part:
    """Ring centre at the origin, rail along +Y above it, rod enters from -Y; the part stands on z=0.

    The same construction as ``bistable_beam_pair`` with one beam per side: each arm is a
    ``hinged_beam`` (neck, body, neck) running from the post face to the ring wall, tilted
    ``arm_angle`` so the ring sits above the posts.  Pushing the ring onto the rod spreads the halves
    about the bridge across the top slit, pulls the arms outward and bends the strips; the strips
    then hold the jaws shut.  Squeezing the posts together tightens the jaws.  Unlike the pair, it
    does not snap through: the ring would have to climb ``arm_len * sin(arm_angle)`` (~5 mm) to
    flatten the arms and the rail stops it after ``ring_clear``, so the beams act as a spring.  Set
    ``ring_clear`` above the rise and add travel for the rod, and you have a toggling clip.  With
    ``neck_plate`` > 0 the necks and the top bridge exist only in the top and bottom plates, as in
    the reference, so the middle layers of the arms and ring halves are islands standing on the
    bottom plate.  Mounting is by the rail's back face (y = rail_top); cut holes into it in the model.

    Example:
        env = split_ring_clip_envelope(rod_d=8)                   # rail_top, width, x_post, rise ...
        clip = split_ring_clip(rod_d=8, grip=0.6)                 # holds an 8 mm tube
        wall = Pos(0, env["rail_top"] + wall_t / 2, 0) * Box(env["width"], wall_t, depth)   # fuse to a host
    """
    if not 0 <= neck_plate <= depth / 2:
        raise ValueError("neck_plate must be between 0 and half the depth")
    env = split_ring_clip_envelope(rod_d, grip, wall, ring_clear, rail_t, arm_len, arm_angle, jaw_attach, post_d, strip_t)
    r_out, x_post, y_post = env["r_out"], env["x_post"], env["y_post"]
    px, py = env["post_end"]
    overlap = min(hinge_width + 0.1, 0.8 * wall)  # neck ends bury in the post and the ring wall without reaching the bore

    # rigid members: rail, strips, posts (full depth)
    rail_y = (env["rail_bottom"] + env["rail_top"]) / 2
    sk = Pos(0, rail_y) * RectangleRounded(env["rail_len"], rail_t, rail_t / 4)
    strip_len = rail_y - y_post  # the strips run up to the rail centreline so they fuse under its rounded corners
    for sx in (-1, 1):
        sk = sk + Pos(sx * x_post, (rail_y + y_post) / 2) * Rectangle(strip_t, strip_len)
        sk = sk + Pos(sx * x_post, y_post) * Circle(post_d / 2)
    # ring: annulus split top and bottom; the top slit keeps a bridge of hinge_width at the outer surface
    ring = Circle(r_out) - Circle(env["r_in"])
    ring = ring - Pos(0, -r_out / 2 - 1) * Rectangle(ring_gap, r_out + 2)                       # bottom slit, through
    ring = ring - Pos(0, (r_out - hinge_width) / 2) * Rectangle(ring_gap, r_out - hinge_width)   # top slit up to the bridge
    body = extrude(sk + ring, amount=depth)
    if neck_plate > 0:  # the top bridge is plates-only too: cut it out of the middle band
        mid = Box(ring_gap, hinge_width + 2 * overlap, depth - 2 * neck_plate, align=(Align.CENTER, Align.CENTER, Align.MIN))
        body = body - Pos(0, r_out - hinge_width / 2 + overlap, neck_plate) * mid

    # arms: one hinged beam per side from the post face (anchor) to the ring wall (shuttle), placed as bistable_beam_pair places its beams
    beam = hinged_beam(arm_len, arm_w, hinge_width, hinge_length, depth, overlap, neck_plate)
    arms = Pos(px, py, 0) * Rot(0, 0, 180 - arm_angle) * beam + Pos(-px, py, 0) * Rot(0, 0, arm_angle) * beam
    return body + arms
