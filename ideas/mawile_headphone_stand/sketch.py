"""Sketch for ideas/mawile_headphone_stand, round 5 (from the reference photo brief): Mawile's jaw is
a big black horn that leaves the back of the head, arches up and over, and comes down to rest on the
ground behind her, wide "mouth" end at the bottom with teeth along the inner edge.  The top of the
arch is the headband saddle; the mouth end on the base is a second foot.

Parts (print orientation):
  body      yellow: base plate + bell dress + head (+ the two black ear flaps, painted), upright
  jaw_left / jaw_right   black: the arch split on its mid-plane, each half printed flat face down
                          (teeth are half-pyramids on the inner edge; paint white)
  assembly  preview only
"""
import math

from build123d import *  # noqa: F401,F403

from lib.component import on_bed
from lib.fasteners.clearance_hole import clearance_hole
from lib.form.outline import blob_outline
from lib.form.revolved import revolved_body

# --- knobs (mm) ---------------------------------------------------------------
BASE_T = 8.0
BASE_CIRCLES = ((-30, 8, 34), (30, 8, 34), (0, -18, 34), (0, -72, 30), (0, -118, 40))   # feet lobes ... rear pad under the mouth
BODY_PROFILE = (            # (r, z) above the base: bell dress, waist, shoulders, neck, head (<= 45 deg everywhere)
    (46, 0), (44, 14), (34, 44), (22, 76), (15, 100), (20, 116), (14, 122), (18, 127), (23, 134), (28, 142), (31, 151), (32, 160),
    (29, 172), (20, 183), (8, 189), (3, 190),
)
HEAD_C = (0, 0, 156)        # head centre (above the base top), for placing flaps and the jaw root
HEAD_R = 32.0
FLAP = (14, 40, 10)         # ear flaps: x, z, y thickness; hang beside the head, overlapping it
FLAP_Z = 142                # flap centre height

# jaw arch path in the YZ plane (y, z) from the head back to the ground, and the ellipse section (x width, y thickness) at each point
JAW_PATH = (
    ((-30, 168), (24, 16)),      # root inside the head
    ((-46, 196), (30, 20)),
    ((-64, 228), (38, 26)),
    ((-86, 250), (46, 30)),      # apex: the saddle
    ((-112, 238), (52, 36)),
    ((-132, 200), (60, 42)),
    ((-140, 150), (68, 48)),     # mouth: widest
    ((-136, 95), (70, 50)),
    ((-124, 45), (66, 48)),
    ((-116, 8), (60, 44)),       # end on the base top
)
JAW_ROOT_STUB = 14.0        # straight stub from the first section into the head (tenon)
JAW_FOOT_STUB = 5.0         # stub from the last section into the base (tenon)
STUB_CLEAR = 0.3
TEETH_Z = (215, 185, 155, 125, 95)   # tooth heights; y is taken from the jaw's inner edge at that height
TOOTH_R, TOOTH_H, TOOTH_SINK = 5.0, 12.0, 3.0
PIN_PTS = (((-80, 240)), ((-130, 120)))   # M3 pin holes on the mid-plane (y, z)
PIN_DEPTH = 8.0


def _plane_at(i):
    (y, z), _ = JAW_PATH[i]
    (yp, zp), _ = JAW_PATH[max(i - 1, 0)]
    (yn, zn), _ = JAW_PATH[min(i + 1, len(JAW_PATH) - 1)]
    t = Vector(0, yn - yp, zn - zp).normalized()
    return Plane(origin=(0, y, z + BASE_T - 1), x_dir=(1, 0, 0), z_dir=t)


def inner_edge_y(z):
    """y of the jaw's +Y (inner) edge at height z on the descending part, by linear interpolation of the path."""
    pts = [(zz, yy + th / 2) for (yy, zz), (w, th) in JAW_PATH[3:]]   # from the apex down: (z, inner y)
    pts.sort()
    for (z0, y0), (z1, y1) in zip(pts, pts[1:]):
        if z0 <= z <= z1:
            return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
    return pts[0][1] if z < pts[0][0] else pts[-1][1]


def jaw_full():
    sections = []
    for i, (_, (w, th)) in enumerate(JAW_PATH):
        sections.append(_plane_at(i) * Ellipse(w / 2, th / 2))
    jaw = loft(sections, ruled=False)
    # root stub into the head and foot stub into the base
    _, (w0, t0) = JAW_PATH[0]
    root = extrude(_plane_at(0) * Ellipse(w0 / 2, t0 / 2), amount=-JAW_ROOT_STUB)
    _, (w1, t1) = JAW_PATH[-1]
    foot = extrude(_plane_at(len(JAW_PATH) - 1) * Ellipse(w1 / 2, t1 / 2), amount=JAW_FOOT_STUB)
    jaw = jaw + root + foot
    # teeth on the inner (concave, +Y facing) edge of the descending part, pointing toward Mawile
    teeth = []
    for z in TEETH_Z:
        y = inner_edge_y(z)
        tooth = Cone(TOOTH_R, 0.6, TOOTH_H + TOOTH_SINK, align=(Align.CENTER, Align.CENTER, Align.MIN))
        teeth.append(Pos(0, y - TOOTH_SINK, z + BASE_T - 1) * Rot(-90, 0, 0) * tooth)
    jaw = jaw + teeth
    return jaw


def jaw_halves(jaw):
    big = 600
    right = jaw & Box(big, big, big, align=(Align.MIN, Align.CENTER, Align.CENTER))
    left = jaw & Box(big, big, big, align=(Align.MAX, Align.CENTER, Align.CENTER))
    # pin holes through the mid-plane faces (M3 clearance, filament or screw shank as the pin)
    for (y, z) in PIN_PTS:
        hole_r = Pos(0, y, z + BASE_T - 1) * Rot(0, -90, 0) * clearance_hole("M3", depth=PIN_DEPTH)   # into +X
        hole_l = Pos(0, y, z + BASE_T - 1) * Rot(0, 90, 0) * clearance_hole("M3", depth=PIN_DEPTH)    # into -X
        right = right - hole_r
        left = left - hole_l
    return left, right


def base_and_body(jaw):
    base = extrude(blob_outline(BASE_CIRCLES, smooth_r=10), amount=BASE_T)
    base = chamfer(base.faces().sort_by(Axis.Z)[0].outer_wire().edges(), 0.6)
    z0 = BASE_T - 1
    body = Pos(0, 0, z0) * revolved_body(BODY_PROFILE, smooth=True, tangents=((-0.15, 1), (-1, 0.4)))
    flaps = [Pos(sx * (HEAD_R - 7), -6, FLAP_Z + z0) * Box(FLAP[0], FLAP[2], FLAP[1]) for sx in (1, -1)]
    for i in range(2):
        flaps[i] = fillet(flaps[i].edges().filter_by(Axis.Y), 4)
    body = base + body + flaps
    # sockets: jaw root into the back of the head, jaw foot into the base (offset the stubs by the clearance)
    _, (w0, t0) = JAW_PATH[0]
    root_pocket = extrude(_plane_at(0) * Ellipse(w0 / 2 + STUB_CLEAR, t0 / 2 + STUB_CLEAR), amount=-(JAW_ROOT_STUB + 1))
    _, (w1, t1) = JAW_PATH[-1]
    foot_pocket = extrude(_plane_at(len(JAW_PATH) - 1) * Ellipse(w1 / 2 + STUB_CLEAR, t1 / 2 + STUB_CLEAR), amount=JAW_FOOT_STUB + 0.5)
    return body - root_pocket - foot_pocket


def build():
    jaw = jaw_full()
    body = base_and_body(jaw)
    left, right = jaw_halves(jaw)
    return {
        "body": on_bed(body),
        "jaw_right": on_bed(Rot(0, -90, 0) * right),   # mid-plane face (x=0) down, dome up
        "jaw_left": on_bed(Rot(0, 90, 0) * left),
        "assembly": on_bed(body + jaw),
    }
