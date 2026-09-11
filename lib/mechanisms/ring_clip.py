"""Snap-on split-ring clip: a C-ring on two living-hinge push arms, sprung by thin side strips off a mounting rail.

Numbers come from a reference mesh the user handed over (``Parametric_clip_VL_5.5.STL``, filed as
``ideas/ring_clip_5_5/references/file-5725bdb05c.md``): ring bore 5.05 for a 5.5 mm rod, wall 1.0,
necks 0.46, arms 1.54 wide at ~16 deg, springs 0.55, rail 3.0, depth 7.2, all MEASURED off the
mesh.  The reference's necks exist only as two 1.9 mm plates at the top and bottom faces, with a
3.4 mm gap between them; that is reproduced by ``neck_plate`` and can be switched off.
"""
from __future__ import annotations

import math

from build123d import Align, Box, Circle, Part, Pos, Rectangle, RectangleRounded, Rot, SlotOverall, extrude

from lib.component import MaterialNotes, component


def split_ring_clip_envelope(rod_d: float = 5.5, grip: float = 0.45, wall: float = 1.0, ring_clear: float = 1.2, rail_t: float = 3.0,
                             arm_len: float = 16.2, arm_w: float = 1.6, arm_angle: float = 16.0, jaw_attach: float = -1.75,
                             hinge_length: float = 2.0, post_d: float = 2.0, strip_t: float = 0.6) -> dict:
    """Where things are for a parameter set (same defaults as the component). Not a component.

    Ring centre is the origin; +Y is toward the rail; the rod enters from -Y.  Returns ``r_in``,
    ``r_out``, ``rail_bottom``, ``rail_top``, ``rail_len``, ``x_post``, ``y_post`` (post centres at
    ±x_post), ``width`` (overall X), ``y_min`` (lowest point: the post underside) and the arm end
    centres ``arm_in`` / ``arm_out`` for the +X arm.
    """
    r_in = (rod_d - grip) / 2
    r_out = r_in + wall
    rail_bottom = r_out + ring_clear
    rail_top = rail_bottom + rail_t
    # arm-to-ring neck runs along X at y = jaw_attach from the ring's outer wall to the arm tip
    x_ring = math.sqrt(max(r_out**2 - jaw_attach**2, 0.0))
    arm_in = (x_ring + hinge_length + arm_w / 2, jaw_attach)
    span = arm_len - arm_w  # centre to centre of the slot's end arcs
    a = math.radians(arm_angle)
    arm_out = (arm_in[0] + span * math.cos(a), arm_in[1] - span * math.sin(a))
    x_post = arm_out[0] + arm_w / 2 + hinge_length + post_d / 2
    y_post = arm_out[1]
    rail_len = 2 * (x_post + strip_t / 2)
    return {"r_in": r_in, "r_out": r_out, "rail_bottom": rail_bottom, "rail_top": rail_top, "rail_len": rail_len,
            "x_post": x_post, "y_post": y_post, "width": 2 * (x_post + post_d / 2), "y_min": y_post - post_d / 2,
            "x_ring": x_ring, "arm_in": arm_in, "arm_out": arm_out}


@component(
    id="mechanisms.split_ring_clip", version="0.1.0",
    summary="Snap-on split-ring clip: a C-ring (bore = rod - grip) on two living-hinge push arms, sprung by thin side strips off a mounting rail; the rod snaps in through the bottom slit.",
    tags=["clip", "ring clip", "snap-on", "rod", "cable", "compliant", "living hinge", "spring", "holder", "print in place"],
    units={"rod_d": "mm", "grip": "mm", "wall": "mm", "ring_gap": "mm", "hinge_width": "mm", "hinge_length": "mm", "neck_plate": "mm",
           "arm_len": "mm", "arm_w": "mm", "arm_angle": "deg", "jaw_attach": "mm", "post_d": "mm", "strip_t": "mm",
           "ring_clear": "mm", "rail_t": "mm", "depth": "mm"},
    descriptions={
        "rod_d": "diameter of the rod, tube or cable the clip holds",
        "grip": "bore undersize: ring bore = rod_d - grip, so the closed jaws preload the rod (reference: 5.5 rod, 5.05 bore)",
        "wall": "ring wall thickness (measured 1.0)",
        "ring_gap": "width of the slit that splits the ring top and bottom; the rod enters through the bottom one",
        "hinge_width": "in-plane width of every living-hinge neck: arm to post, arm to ring, and the bridge across the top slit (measured 0.46 = one 0.4 mm line)",
        "hinge_length": "length of the arm-to-post and arm-to-ring necks along X",
        "neck_plate": "Z thickness of the two neck plates at the top and bottom faces (measured 1.9); the necks are absent between them. 0 = necks run the full depth",
        "arm_len": "overall length of each push arm including its rounded ends",
        "arm_w": "width of the push arms (measured 1.54; 1.6 = four lines)",
        "arm_angle": "angle of the arms below the X axis, outer end lower (measured ~16 deg)",
        "jaw_attach": "Y of the arm-to-ring neck relative to the ring centre; negative = below centre, must stay below the top bridge so pulling the arms outward opens the jaws",
        "post_d": "diameter of the round posts that join the strips to the arm necks",
        "strip_t": "thickness of the side strips, the return springs (measured 0.55; 0.6 = one line plus gap fill)",
        "ring_clear": "clear gap between the ring top and the rail underside",
        "rail_t": "thickness (Y) of the mounting rail",
        "depth": "part height (Z) = print height (measured 7.2)",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="flat on the bed, ring axis along Z, so every neck and strip bends in the bed plane; never stand it up",
        notes="UNVALIDATED here. Reproduced from a downloaded mesh with no page or material notes; the necks are one 0.4 mm line and the strips one and a half, so print with thin-wall (Arachne) perimeters on. The strips and necks bend on every rod insertion; PETG expected to hold up, PLA expected to work for a few insertions and creep if the rod is oversize. A coupon print at the defaults (models/ring_clip_5_5) is the first test.",
    ),
)
def split_ring_clip(rod_d: float = 5.5, grip: float = 0.45, wall: float = 1.0, ring_gap: float = 0.5, hinge_width: float = 0.5,
                    hinge_length: float = 2.0, neck_plate: float = 1.9, arm_len: float = 16.2, arm_w: float = 1.6, arm_angle: float = 16.0,
                    jaw_attach: float = -1.75, post_d: float = 2.0, strip_t: float = 0.6, ring_clear: float = 1.2, rail_t: float = 3.0,
                    depth: float = 7.2) -> Part:
    """Ring centre at the origin, rail along +Y above it, rod enters from -Y; the part stands on z=0.

    One connected body: rail -> side strips -> posts -> necks -> arms -> necks -> ring halves, whose
    top slit is bridged by a ``hinge_width`` neck.  Pushing the ring onto the rod spreads the halves
    about that bridge, pulls the arms outward and bends the strips; the strips then hold the jaws
    shut on the rod.  Squeezing the posts together tightens the jaws.  With ``neck_plate`` > 0 the
    necks and the top bridge exist only in the top and bottom plates, as in the reference, so the
    middle layers of the arms and ring halves are free islands standing on the bottom plate.
    Mounting is by the rail's back face (y = rail_top); cut holes into it in the model.

    Example:
        env = split_ring_clip_envelope(rod_d=8)                   # rail_top, width, x_post ...
        clip = split_ring_clip(rod_d=8, grip=0.6)                 # holds an 8 mm tube
        wall = Pos(0, env["rail_top"] + wall_t / 2, 0) * Box(env["width"], wall_t, depth)   # fuse to a host
    """
    if not 0 <= neck_plate <= depth / 2:
        raise ValueError("neck_plate must be between 0 and half the depth")
    env = split_ring_clip_envelope(rod_d, grip, wall, ring_clear, rail_t, arm_len, arm_w, arm_angle, jaw_attach, hinge_length, post_d, strip_t)
    r_in, r_out, x_post, y_post = env["r_in"], env["r_out"], env["x_post"], env["y_post"]
    (x_in, y_in), (x_out, y_out) = env["arm_in"], env["arm_out"]
    overlap = 0.2  # necks run this far into the members they join so the boolean fuses them

    # rigid members: rail, strips, posts (full depth)
    rail_y = (env["rail_bottom"] + env["rail_top"]) / 2
    sk = Pos(0, rail_y) * RectangleRounded(env["rail_len"], rail_t, rail_t / 4)
    strip_len = rail_y - y_post  # the strips run up to the rail centreline so they fuse under its rounded corners
    for sx in (-1, 1):
        sk = sk + Pos(sx * x_post, (rail_y + y_post) / 2) * Rectangle(strip_t, strip_len)
        sk = sk + Pos(sx * x_post, y_post) * Circle(post_d / 2)
    # arms: slots from the outer end (at the post neck) to the inner end (at the ring neck)
    for sx in (-1, 1):
        cx, cy = sx * (x_in + x_out) / 2, (y_in + y_out) / 2
        sk = sk + Pos(cx, cy) * Rot(0, 0, -sx * arm_angle) * SlotOverall(arm_len, arm_w)
    # ring: annulus split top and bottom; the top slit keeps a bridge of hinge_width at the outer surface
    ring = Circle(r_out) - Circle(r_in)
    ring = ring - Pos(0, -r_out / 2 - 1) * Rectangle(ring_gap, r_out + 2)                       # bottom slit, through
    ring = ring - Pos(0, (r_out - hinge_width) / 2) * Rectangle(ring_gap, r_out - hinge_width)   # top slit up to the bridge
    sk = sk + ring
    body = extrude(sk, amount=depth)

    # necks: arm-to-post and arm-to-ring, along X at the arm end heights, in the plates only when neck_plate > 0
    neck_sk = None
    for sx in (-1, 1):
        post_neck_len = x_post - post_d / 2 - (x_out + arm_w / 2) + 2 * overlap
        pn = Pos(sx * (x_post - post_d / 2 + overlap - post_neck_len / 2), y_out) * Rectangle(post_neck_len, hinge_width)
        ring_neck_len = x_in - arm_w / 2 - env["x_ring"] + overlap + wall * 0.5
        rn = Pos(sx * (env["x_ring"] - wall * 0.5 + ring_neck_len / 2), y_in) * Rectangle(ring_neck_len, hinge_width)
        neck_sk = pn + rn if neck_sk is None else neck_sk + pn + rn
    if neck_plate > 0:
        necks = extrude(neck_sk, amount=neck_plate) + Pos(0, 0, depth - neck_plate) * extrude(neck_sk, amount=neck_plate)
        # the top bridge is also plates-only: cut it out of the middle band
        mid = Box(ring_gap, hinge_width + 2 * overlap, depth - 2 * neck_plate, align=(Align.CENTER, Align.CENTER, Align.MIN))
        body = body - Pos(0, r_out - hinge_width / 2 + overlap, neck_plate) * mid
    else:
        necks = extrude(neck_sk, amount=depth)
    return body + necks
