"""Caterpillar-and-mushrooms holder for a slim 510 vape pen and two spare cartridges.

Part: ``holder`` — one solid, garden ground flat on the bed.

The scene, left to right: a five-segment caterpillar leaning its head on a bulbous hookah whose
neck is the pen socket, and two toadstools with a cartridge hidden down the stalk of each, all
standing in a smoothed garden patch.  The pen IS the hookah's pipe — it drops into the rim and
stands 102 mm proud — and the caterpillar's head plus two stubby arms wrap the water bowl so it
reads as holding the thing it is smoking.  Cartridges go in mouthpiece up: mushroom A swallows
40 mm of a 55 mm cartridge (15 mm shows), the shorter mushroom B 29 mm (26 mm shows, so one is
easy to grab and one is properly hidden).

Every bore floor sits at BASE_T, so the ground thickness is the floor under all three.  Bores are
blind on purpose — a vent under a cartridge would drain a leaky cart onto the desk.

Form pipeline (the lib/form order of operations): outline -> bodies -> booleans, all B-rep, no mesh
step, so the part exports STEP and every fit is exact.  ``form.blob_outline`` draws the ground,
``form.revolved_body`` turns the hookah and the mushrooms, ``form.dome_cluster`` is the caterpillar
and its eyes, and ``primitives.socket_array`` cuts all three sockets.

Print orientation: as returned, ground on the bed, nothing else touching it, no supports anywhere.
An upper half-ellipsoid has no down-facing surface at all, the mushroom caps and the hookah's belly
never flare faster than 37 degrees from vertical, and every bore floor is an up-facing floor — so
the only overhangs in the part are the bed chamfer and the five foot recesses, both of which start
at or 0.8 mm above the bed.  Material: PLA.

Stability is the governing constraint, not fit: with a cartridge screwed on, ~150 mm of pen stands
above a socket floor 6 mm off the desk.  ``stability()`` reports three cases; the governing one is
loaded, standing on its rubber feet, because fitted feet REPLACE the ground as the support polygon.
Empty — the case that matters while you are placing the pen, since until you let go the pen's mass
is in your hand — it is far steadier.

The feet are placed explicitly rather than with patterns.corner_holes: that component wants a
rectangle, and a rectangle inscribed in this outline either pokes out of a lobe or throws away most
of the stance.

Two things this shape taught, both recorded where they belong: a surface of revolution that closes
to a POINT tessellates into a loose degenerate triangle and reads as a non-watertight part (see
``lib.form.blobs.dome``, which stops at a 0.4 mm flat instead), and Z-SCALING a body scales its
slopes, so mushroom B has its own profile rather than being the tall one squashed (see params).

Assumptions (user not available for every number): pen battery 90 mm long and ~12 mm across, socket
sized 13.0 nominal at the user's request for room; cartridges 11 x 55 mm; pen 30 g and a cartridge
10 g for the stability sum.  All single constants in params.py.
"""
from math import atan2, cos, degrees, sin, tau

from build123d import Axis, CenterOf, Cylinder, Part, Plane, Pos, Rot, chamfer, extrude

from lib.component import on_bed
from lib.form.blobs import dome_cluster
from lib.form.outline import blob_outline
from lib.form.revolved import revolved_body
from lib.primitives.feet import rubber_foot_recess
from lib.primitives.socket_array import socket_array

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def _ground() -> Part:
    """The garden patch: one smoothed outline through a lobe per feature it carries."""
    return extrude(blob_outline(P.BASE_BLOB, smooth_r=P.BASE_SMOOTH_R), amount=P.BASE_T)


def _hookah() -> Part:
    return revolved_body(P.HOOKAH_PROFILE)


def _mushroom(profile) -> Part:
    return revolved_body(profile)


def _dome_base_z() -> float:
    return P.BASE_T - P.SEGMENT_SINK


def _caterpillar() -> Part:
    """Body segments and arms as one dome cluster, sunk into the ground so it is one solid."""
    return dome_cluster(tuple(P.CATERPILLAR) + tuple(P.ARMS), squash=P.SEGMENT_SQUASH, base_z=_dome_base_z())


def _eyes() -> list[Part]:
    """Two eyeballs set into the head along EYE_DIRS, based just under the surface so a cap shows.

    Each is a dome standing on a plane normal to its own direction, not a sphere: see
    ``lib.form.blobs.dome`` for why nothing here closes to a point.
    """
    hx, hy, hr = P.CATERPILLAR[0]
    out = []
    for u, v, w in P.EYE_DIRS:
        seat = (hx + hr * u * P.EYE_EMBED,
                hy + hr * v * P.EYE_EMBED,
                _dome_base_z() + hr * P.SEGMENT_SQUASH * w * P.EYE_EMBED)
        out.append(Plane(origin=seat, z_dir=(u, v, w)) * dome_cluster(((0, 0, P.EYE_R),), squash=P.EYE_SQUASH))
    return out


def _scene() -> Part:
    """Everything unioned, before a single bore is cut."""
    solid = _ground() + _hookah()
    solid += Pos(*P.MUSH_A_XY) * _mushroom(P.MUSHROOM_PROFILE)
    solid += Pos(*P.MUSH_B_XY) * _mushroom(P.MUSHROOM_B_PROFILE)
    solid += _caterpillar()
    solid += _eyes()
    return chamfer(solid.faces().sort_by(Axis.Z)[0].outer_wire().edges(), P.BED_CHAMFER)


def _socket(bore_d: float, depth: float):
    return socket_array(bore_d, depth=depth, clearance=P.BORE_CLEARANCE, lead_in=P.LEAD_IN,
                        vent_d=P.VENT_D, vent_len=P.VENT_LEN)


def holder() -> Part:
    body = _scene()
    body -= Pos(0, 0, P.HOOKAH_H) * _socket(P.PEN_D, P.PEN_DEPTH)
    body -= Pos(*P.MUSH_A_XY, P.MUSH_A_H) * _socket(P.CART_D, P.CART_A_DEPTH)
    body -= Pos(*P.MUSH_B_XY, P.MUSH_B_H) * _socket(P.CART_D, P.CART_B_DEPTH)
    return body - [Pos(x, y, 0) * Rot(180, 0, 0) * rubber_foot_recess(P.FOOT_D) for x, y in P.FOOT_POS]


def build() -> dict[str, Part]:
    return {"holder": on_bed(holder())}


# --- envelopes of the hardware, in the assembled position --------------------

def _cart_envelope(x: float, y: float) -> Part:
    return Pos(x, y, P.BASE_T + P.CART_LEN / 2) * Cylinder(P.CART_D / 2, P.CART_LEN)


def _parked_pen() -> Part:
    """Battery standing on the hookah's socket floor with a cartridge screwed on top."""
    pen = Pos(0, 0, P.BASE_T + P.PEN_LEN / 2) * Cylinder(P.PEN_D / 2, P.PEN_LEN)
    return pen + Pos(0, 0, P.BASE_T + P.PEN_LEN + P.CART_LEN / 2) * Cylinder(P.CART_D / 2, P.CART_LEN)


def fit_checks(parts: dict) -> dict:
    """Every bore must clear what it holds, and the parked pen must clear both mushrooms."""
    body = parts["holder"]
    a, b = _cart_envelope(*P.MUSH_A_XY), _cart_envelope(*P.MUSH_B_XY)
    pen = _parked_pen()
    return {
        "pen_vs_body": (pen, body),
        "cart_a_vs_body": (a, body),
        "cart_b_vs_body": (b, body),
        "pen_vs_carts": (pen, a + b),
    }


# --- stability ---------------------------------------------------------------

def _base_points(body) -> list[tuple[float, float]]:
    """XY samples along the bed-contact face's outer wire."""
    return [(v.X, v.Y) for e in body.faces().sort_by(Axis.Z)[0].outer_wire().edges()
            for v in (e @ (i / P.EDGE_SAMPLES) for i in range(P.EDGE_SAMPLES))]


def _feet_points() -> list[tuple[float, float]]:
    """XY samples around each rubber foot's contact disc."""
    return [(x + P.FOOT_D / 2 * cos(a), y + P.FOOT_D / 2 * sin(a))
            for x, y in P.FOOT_POS
            for a in (tau * i / P.EDGE_SAMPLES for i in range(P.EDGE_SAMPLES))]


def _margin(pts, cx: float, cy: float) -> float:
    """Distance from (cx, cy) to the convex hull of ``pts``.

    The part tips about a hull edge — it cannot rotate into one of the concave waists between the
    ground's lobes — so this is the support function of the sampled contact patch minus the centre
    of mass, minimised over direction.  No hull algorithm needed.
    """
    return min(max(x * cos(a) + y * sin(a) for x, y in pts) - (cx * cos(a) + cy * sin(a))
               for a in (tau * i / P.SUPPORT_DIRS for i in range(P.SUPPORT_DIRS)))


def _com(body, loaded: bool) -> tuple[float, float, float, float]:
    """(mass g, x, y, z) of the holder, optionally with the pen and both cartridges in it."""
    c = body.center(CenterOf.MASS)
    masses = [(body.volume / P.MM3_PER_CM3 * P.PLA_DENSITY * P.PRINT_FILL, c.X, c.Y, c.Z)]
    if loaded:
        masses += [(P.PEN_MASS_G, 0, 0, P.BASE_T + P.PEN_LEN / 2),
                   (P.CART_MASS_G, 0, 0, P.BASE_T + P.PEN_LEN + P.CART_LEN / 2),
                   (P.CART_MASS_G, P.MUSH_A_XY[0], P.MUSH_A_XY[1], P.BASE_T + P.CART_LEN / 2),
                   (P.CART_MASS_G, P.MUSH_B_XY[0], P.MUSH_B_XY[1], P.BASE_T + P.CART_LEN / 2)]
    total = sum(m for m, *_ in masses)
    return (total,
            sum(m * x for m, x, _, _ in masses) / total,
            sum(m * y for m, _, y, _ in masses) / total,
            sum(m * z for m, _, _, z in masses) / total)


def stability() -> dict:
    """Tip angles: how far the holder must be tilted before it goes over.

    Not a build gate — build.py checks geometry, and nothing in the pipeline knows how heavy a vape
    pen is.  This is the number the garden's width exists to satisfy, and it is reported three ways
    because they are genuinely different situations:

    * ``loaded_on_feet`` — the governing case.  Pen (with a cartridge on it) parked, both spares in
      their mushrooms, standing on the rubber feet.  Fitted feet REPLACE the ground as the support
      polygon, which is why FOOT_POS sits out on the lobes rather than in a tidy rectangle.
    * ``loaded_on_base`` — the same, with no feet fitted, so the whole garden touches the desk.
    * ``empty_on_feet`` — nothing in it.  This is the case that matters while you are PLACING the
      pen, because until you let go the pen's mass is in your hand, not on the holder.
    """
    body = build()["holder"]
    base, feet = _base_points(body), _feet_points()
    out = {}
    for tag, loaded, pts in (("loaded_on_feet", True, feet), ("loaded_on_base", True, base),
                             ("empty_on_feet", False, feet)):
        m, cx, cy, cz = _com(body, loaded)
        out[tag] = {"mass_g": round(m, 1), "com": (round(cx, 1), round(cy, 1), round(cz, 1)),
                    "margin_mm": round(_margin(pts, cx, cy), 1),
                    "tip_angle_deg": round(degrees(atan2(_margin(pts, cx, cy), cz)), 1)}
    return out


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1), "valid" if part.is_valid else "INVALID",
              len(part.solids()), "solid(s)")
    for tag, r in stability().items():
        ok = "" if tag != "loaded_on_feet" else (
            "  <- governing, target {} -> {}".format(
                P.MIN_TIP_ANGLE, "OK" if r["tip_angle_deg"] >= P.MIN_TIP_ANGLE else "TOO TIPPY"))
        print(f"{tag:16s} {r['mass_g']:6.1f} g  com {r['com']}  margin {r['margin_mm']:5.1f} mm  "
              f"tip {r['tip_angle_deg']:5.1f} deg{ok}")
