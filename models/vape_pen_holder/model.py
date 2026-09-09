"""Caterpillar-and-mushrooms holder for a slim 510 vape pen and two spare cartridges.

Part: ``holder`` — one solid, garden ground and the caterpillar's underside flat on the bed.

The scene: a bulbous hookah whose neck is the pen socket, two toadstools with a cartridge hidden
down the stalk of each, a garden patch they all stand in — and an eighteen-segment caterpillar
wrapped right around the outside of the lot, rearing up the hookah at the front.  The body sweeps
up the left, across the back behind mushroom A and down the right, and the tail curls back in at
the front beside mushroom B, leaving the C open at the front so the garden is never fenced in.  Out
of its front segment a four-ball neck climbs the pot to the rim, where the head sits level with the
socket with its eyes turned up at the mouthpiece and two stubby arms closing on the pen either side
of it.  The pen IS the hookah's pipe — it drops into the rim and stands 102 mm proud — and the pose
is the whole joke: the caterpillar is not holding the thing, it is using it.  Cartridges go in
mouthpiece up: mushroom A swallows 40 mm of a 55 mm cartridge (15 mm shows), the shorter mushroom B
29 mm (26 mm shows, so one is easy to grab and one is properly hidden).

Everything that reaches up to the rim is sized by ONE constraint, and it is the reason the neck
tapers rather than hugging the pot: the pot's wall narrows from r 19.3 to r 11.0 as it rises but the
Ø16.6 bore does not, so a neck that follows the wall walks straight into the parked battery.  Neck
balls, head and arms all keep their nearest point at least 8.8 mm off the axis against an 8.0 mm
pen; ``fit_checks`` is what proves it, and it caught 45 mm3 of exactly that mistake at the smaller
pen diameter this started from.

The pen and the cartridges were re-measured at Ø16 after the first version was drawn around Ø13 and
Ø11.  That is not a one-line change: the bore went up 3 mm in radius while the stem and the stalks
still needed 2.7 mm of wall, so every profile radius grew, both toadstools moved out to stop their
Ø33.6 caps fouling each other and the Ø39 belly, the caterpillar's back arc moved out with them,
and the whole neck moved out again to clear the fatter pen.

Surface work, in the lib/form order — bores first, then the flutes, then the studs.  All B-rep:
there is no mesh step, so the part is one exact solid and exports STEP as well as STL and 3MF.

* **A diamond lattice** (``form.flutes``, twice) on all three turned bodies: the same flute band cut
  once each way, so the two helices cross and leave faceted diamonds standing between them.  Both
  passes measure against the same un-cut solid — reference the already-fluted body and the second
  pass sinks to twice the depth wherever it crosses the first.  Depth is 0.7 mm, set by the THINNEST
  wall the band crosses (the 2.7 mm stem and stalks, not the 9 mm belly), which leaves five
  extrusions under the deepest part of a groove.  The twist is given as a rate, 3.5 deg per mm, so
  that the 42, 23 and 12 mm bands all come out with the same helix angle.
* **Studs** (``form.surface_studs``): toadstool spots on both caps, tubercles down the caterpillar's
  back and up its neck, and the two eyes, each seated on whatever surface a ray finds and tilted
  with it.

Straight flutes on the stalks were tried first and read as scratches beside the hookah's diamonds;
one pattern over all three bodies is what makes it look designed rather than decorated.

All three bores are blind: a vent under a cartridge would drip a leaky cart onto the desk.

Print orientation: as returned, no supports.  An upper half-ellipsoid has no down-facing surface at
all, so every body segment, stud and eye is self-supporting; the mushroom caps and the hookah's
belly never flare faster than 37 degrees from vertical; every bore floor is an up-facing floor.  The
build reports ~1000 mm2 of >45 deg overhang and all of it is accepted: 580 mm2 is the foot recesses
and the bed chamfer, in the first 6 mm off the plate, and most of the rest is the down-facing side
of a 0.7 mm decorative groove, which needs no more support than a chamfer does.  The neck is the one
thing here that COULD print as unsupported nonsense — a rearing chain of balls is a 90-degree
overhang all down its underside — so every ball is half sunk into the pot and sits on the one below
it, and the head leans back out over the rim by only 25 degrees from vertical.  Material: PLA.

Stability is the governing constraint, not fit: with a cartridge screwed on, ~150 mm of pen stands
above a socket floor 6 mm off the desk.  ``stability()`` reports three cases; the governing one is
loaded, standing on its rubber feet, because fitted feet REPLACE the ground as the support polygon.
Five of the six feet sit under a body segment — wrapping the caterpillar around the outside makes
it the perimeter of the part, and standing on it is worth a couple of degrees of tip angle over the
old stance even after the reared neck put 5 cm3 up at rim height.

Three things this shape taught, all recorded where they belong: a surface of revolution that closes
to a POINT tessellates into a loose degenerate triangle and reads as a non-watertight part (see
``lib.form.blobs.dome``, which stops at a 0.4 mm flat instead); Z-SCALING a body scales its slopes,
so mushroom B has its own profile rather than being the tall one squashed (see params); and cutting
detail into a spline surface of revolution reliably leaves OCC a needle of uncut skin and a
collapsed shell or two in the tessellation (see ``lib.component.drop_debris`` and
``scripts/_common._without_debris``).

Assumptions: the pen and the cartridges are Ø16 as the user measured them, and the socket is sized
from that.  Still assumed, and still worth checking against the real thing: the battery is 90 mm
long, a cartridge is 55 mm, and the two weigh 30 g and 10 g for the stability sum.  All single
constants in params.py.
"""
from math import atan2, cos, degrees, radians, sin, tau

from build123d import Axis, CenterOf, Cylinder, Part, Plane, Pos, Rot, chamfer, extrude

from lib.component import drop_debris, on_bed
from lib.form.blobs import ball, ball_chain, dome_chain, surface_studs
from lib.form.outline import blob_outline
from lib.form.revolved import revolved_body
from lib.form.surface import flutes
from lib.primitives.feet import rubber_foot_recess
from lib.primitives.socket_array import socket_array

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def _ground() -> Part:
    """The garden patch: one smoothed outline through a lobe per feature it carries."""
    return extrude(blob_outline(P.BASE_BLOB, smooth_r=P.BASE_SMOOTH_R), amount=P.BASE_T)


def _hookah() -> Part:
    """Bowl and stem, bored for the pen, then cut with the diamond lattice.

    The bore is cut FIRST and in this body's own frame, and the UN-bored solid is what the flutes
    are measured against: ``form.flutes`` trims its bars to the outer ``depth`` of the reference, so
    handing it a hollow body would let a groove reach through into the bore.
    """
    solid = revolved_body(P.HOOKAH_PROFILE)
    body = solid - Pos(0, 0, P.HOOKAH_H) * _socket(P.PEN_D, P.PEN_DEPTH)
    return _diamonds(body, solid, P.HOOKAH_FLUTE_N, P.HOOKAH_FLUTE_Z)


def _diamonds(body: Part, solid: Part, count: int, band: tuple[float, float]) -> Part:
    """The diamond lattice: one flute band cut twice, once each way, so the helices cross.

    Both cuts measure against the same UN-cut ``solid``: ``form.flutes`` trims its bars to the outer
    ``depth`` of the reference, so handing it the already-fluted body would let the second pass sink
    to twice the depth wherever it crossed the first.
    """
    z0, z1 = band
    for hand in (1, -1):
        body = flutes(body, count=count, width=P.FLUTE_W, depth=P.FLUTE_D, z_from=z0, z_to=z1,
                      twist_angle=hand * P.FLUTE_TWIST_RATE * (z1 - z0), reference=solid)
    return body


def _cap_spots(mushroom: Part, top_z: float) -> Part:
    """Toadstool spots: a dome dropped straight down onto the cap lands tilted with the surface."""
    rays = [((x, y, top_z + P.CAP_SPOT_CAST), (0, 0, -1)) for x, y in P.CAP_SPOT_XY]
    return surface_studs(mushroom, rays, radius=P.CAP_SPOT_R, height=P.CAP_SPOT_H,
                         embed=P.CAP_SPOT_EMBED)


def _mushroom(profile, top_z: float, depth: float, band: tuple[float, float]) -> Part:
    """One toadstool: a diamond-cut column under a spotted cap.

    Bored before it is decorated, and fluted against the un-bored solid, both for the reason given
    in ``_hookah``.  The spots are seated against that solid too, so a ray still finds a surface
    where the bore has since opened.
    """
    solid = revolved_body(profile)
    body = solid - Pos(0, 0, top_z) * _socket(P.CART_D, depth)
    body = _diamonds(body, solid, P.STALK_FLUTE_N, band)
    return body + _cap_spots(solid, top_z)


def _dome_base_z() -> float:
    return P.SEGMENT_BASE_Z


def _tubercle_rays(targets) -> list:
    """One ray per bump, aimed at each (x, y, z) from outside the whole scene.

    Azimuth 0 points straight OUT from ``TUBERCLE_ABOUT``, so on a body that curls all the way round
    the scene — and then climbs the pot — the bumps stay on the side you can see instead of drifting
    underneath it half way along.  The head gets none: it has eyes, and the two would fight.
    """
    el = radians(P.TUBERCLE_EL)
    rays = []
    for x, y, z in targets:
        out = atan2(y - P.TUBERCLE_ABOUT[1], x - P.TUBERCLE_ABOUT[0])
        for az in P.TUBERCLE_AZ:
            a = out + radians(az)
            d = (cos(a) * cos(el), sin(a) * cos(el), sin(el))
            origin = (x + d[0] * P.TUBERCLE_CAST, y + d[1] * P.TUBERCLE_CAST, z + d[2] * P.TUBERCLE_CAST)
            rays.append((origin, (-d[0], -d[1], -d[2])))
    return rays


def _caterpillar() -> Part:
    """Body on the ground, neck up the pot, head and arms at the rim.

    The body stands on the bed rather than in the ground: most of it is outside the garden now.
    Where it does cross the garden it is half buried, which is where a caterpillar belongs.  The
    neck then climbs out of its front segment and up the side of the hookah — see ``NECK_RZR`` for
    why it hugs the pot rather than rearing free.
    """
    body = dome_chain(P.CATERPILLAR_PATH, count=P.CATERPILLAR_N, r_head=P.CATERPILLAR_R_HEAD,
                      r_tail=P.CATERPILLAR_R_TAIL, squash=P.SEGMENT_SQUASH, base_z=_dome_base_z())
    neck = ball_chain(P.NECK, squash=P.NECK_SQUASH) + _head()
    targets = [(x, y, _dome_base_z()) for x, y, _ in P.CATERPILLAR[P.TUBERCLE_FROM:]]
    targets += [(x, y, z) for x, y, z, _ in P.NECK]
    skin = body + neck
    return skin + surface_studs(skin, _tubercle_rays(targets), radius=P.TUBERCLE_R,
                                height=P.TUBERCLE_H, embed=P.TUBERCLE_EMBED) \
                + ball_chain(P.ARMS, squash=P.NECK_SQUASH)


def _head() -> Part:
    """The head itself: one ball at the top of the neck, level with the hookah's rim."""
    hx, hy, hz, hr = P.HEAD
    return Pos(hx, hy, hz) * ball(hr, hr * P.NECK_SQUASH)


def _eyes() -> Part:
    """Two eyeballs seated wherever a ray from outside meets the head, tilted with its surface."""
    hx, hy, hz, _ = P.HEAD
    rays = [((hx + u * P.EYE_CAST, hy + v * P.EYE_CAST, hz + w * P.EYE_CAST), (-u, -v, -w))
            for u, v, w in P.EYE_DIRS]
    return surface_studs(_head(), rays, radius=P.EYE_R, height=P.EYE_R * P.EYE_SQUASH,
                         embed=P.EYE_EMBED)


def _bed_edges(solid: Part) -> list:
    """The bed-contact outline, inner gaps included, minus anything too short to chamfer.

    Two of the caterpillar's segments meet the garden almost tangentially, and where they do the
    footprint outline picks up a 0.3 mm edge.  OCC will not put a 0.5 mm chamfer on a 0.3 mm edge —
    it fails the whole operation rather than skipping it — and an unchamfered third of a millimetre
    is not an elephant foot worth having.  The bed face also has inner wires now: the caterpillar
    wraps round the garden and touches it in two places, so the footprint has two gaps in it, and
    those edges want the same chamfer as the outside.
    """
    face = solid.faces().sort_by(Axis.Z)[0]
    wires = [face.outer_wire()] + list(face.inner_wires())
    return [e for w in wires for e in w.edges() if e.length > 2 * P.BED_CHAMFER]


def _scene() -> Part:
    """Everything unioned, before a single bore is cut."""
    solid = _ground() + _hookah()
    solid += Pos(*P.MUSH_A_XY) * _mushroom(P.MUSHROOM_PROFILE, P.MUSH_A_H, P.CART_A_DEPTH,
                                           P.STALK_A_FLUTE_Z)
    solid += Pos(*P.MUSH_B_XY) * _mushroom(P.MUSHROOM_B_PROFILE, P.MUSH_B_H, P.CART_B_DEPTH,
                                           P.STALK_B_FLUTE_Z)
    solid += _caterpillar()
    solid += _eyes()
    return chamfer(_bed_edges(solid), P.BED_CHAMFER)


def _socket(bore_d: float, depth: float):
    return socket_array(bore_d, depth=depth, clearance=P.BORE_CLEARANCE, lead_in=P.LEAD_IN,
                        vent_d=P.VENT_D, vent_len=P.VENT_LEN)


def holder() -> Part:
    """The whole scene; every socket is already bored in the body that carries it (see ``_hookah``).

    ``drop_debris`` is here because cutting the Voronoi into the bowl's spline surface leaves OCC
    one needle of uncut skin, ~0.05 mm3, in the same place whatever the cell size, corner radius or
    roof angle.  It is boolean debris, not geometry; anything a printer could lay down is far above
    the 0.1 mm3 threshold and would still be reported as a second body.
    """
    body = _scene()
    body -= [Pos(x, y, 0) * Rot(180, 0, 0) * rubber_foot_recess(P.FOOT_D) for x, y in P.FOOT_POS]
    return drop_debris(body)


# ~130 small revolved bodies go into this part (18 body segments, 68 tubercles, 14 spots, the neck,
# the eyes) and OCC tessellates every one of them to the default 0.01 mm, which is five times finer
# than a 0.4 mm nozzle can print and exported a 72 MB STL for a 100 mm ornament. 0.02 mm and 0.25
# rad is still an eighth of a layer and takes it to about a fifth of that.
EXPORT_TOLERANCE = 0.02             # mm
EXPORT_ANGULAR_TOLERANCE = 0.25     # rad


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
        print(name, part.bounding_box().size, round(part.volume, 1),
              "valid" if part.is_valid else "INVALID", len(part.solids()), "solid(s)")
    for tag, r in stability().items():
        ok = "" if tag != "loaded_on_feet" else (
            "  <- governing, target {} -> {}".format(
                P.MIN_TIP_ANGLE, "OK" if r["tip_angle_deg"] >= P.MIN_TIP_ANGLE else "TOO TIPPY"))
        print(f"{tag:16s} {r['mass_g']:6.1f} g  com {r['com']}  margin {r['margin_mm']:5.1f} mm  "
              f"tip {r['tip_angle_deg']:5.1f} deg{ok}")
