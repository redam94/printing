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
tapers rather than hugging the pot: the pot's wall narrows from r 17.8 to r 9.5 as it rises but the
Ø13.6 bore does not, so a neck that follows the wall walks straight into the parked battery.  Neck
balls, head and arms all keep their nearest point at least 7.2 mm off the axis against a 6.5 mm
pen; ``fit_checks`` is what proves it, and it caught 45 mm3 of exactly that mistake.

Surface work, in the lib/form order — bores, then flutes, then the lattice, then the studs, then
the mesh skin LAST:

* **Voronoi openwork** (``form.voronoi_shell``) through the hookah's bowl and both mushroom stalks,
  cut to the axis so it goes clean through into the bore: the battery shows through the bowl and a
  cartridge through each stalk.  Every cell is roofed at 48 degrees, so no window needs support.
  The cutters FAN from the axis rather than cutting straight in; a flat prism through a wall this
  thick pinches its own webs to nothing before it reaches the bore.
* **Flutes** (``form.flutes``) down the hookah's waist, 0.6 mm deep on a 2.7 mm wall.
* **Studs** (``form.surface_studs``): toadstool spots on both caps, tubercles down the caterpillar's
  back and up its neck, and the two eyes, each seated on whatever surface a ray finds and tilted
  with it.
* **Noise skin** (``form.textured``, 0.28 mm) over the whole exterior.  This is the mesh step, so
  the part exports STL and 3MF but NO STEP.  It displaces horizontally and exterior-only, so every
  bore, every cell and every z level stays exactly where the B-rep put it and the fit checks hold.

The bores are otherwise blind, and the lattice bands start above each bore floor, leaving a sealed
sump (2 mm under the bowl, 3.5 mm under each stalk) so a cartridge that leaks pools instead of
running out of a window onto the desk.  Opening the bores at all was the user's call, made with
that trade-off in front of them.

``PRINT_MODES`` declares this part **openwork**: the inward-ray wall metric samples by area, and in
a perforated part most of the surface is the inside of a hole, so it reports thin walls that are
not there.  See the note above ``PRINT_MODES`` for the measurements, and check_printable --opening
for the honest number.

Print orientation: as returned.  An upper half-ellipsoid has no down-facing surface at all, so every
body segment, stud and eye is self-supporting; the mushroom caps and the hookah's belly never flare
faster than 37 degrees from vertical; every bore floor is an up-facing floor; and every Voronoi cell
carries a 48-degree roof.  The neck is the one thing here that COULD print as unsupported nonsense —
a rearing chain of balls is a 90-degree overhang all down its underside — so every ball is half sunk
into the pot and sits on the one below it, and the head leans back out over the rim by only 25
degrees from vertical.  Material: PLA.

Stability is the governing constraint, not fit: with a cartridge screwed on, ~150 mm of pen stands
above a socket floor 6 mm off the desk.  ``stability()`` reports three cases; the governing one is
loaded, standing on its rubber feet, because fitted feet REPLACE the ground as the support polygon.
Five of the six feet sit under a body segment — wrapping the caterpillar around the outside makes
it the perimeter of the part, and standing on it is worth a couple of degrees of tip angle over the
old stance even after the lattice took 6 cm3 out of the bowl and the reared neck put 5 cm3 back up
at rim height.

Three things this shape taught, all recorded where they belong: a surface of revolution that closes
to a POINT tessellates into a loose degenerate triangle and reads as a non-watertight part (see
``lib.form.blobs.dome``, which stops at a 0.4 mm flat instead); Z-SCALING a body scales its slopes,
so mushroom B has its own profile rather than being the tall one squashed (see params); and cutting
openwork into a spline surface of revolution reliably leaves OCC a needle of uncut skin (see
``lib.component.drop_debris``).

Assumptions (user not available for every number): pen battery 90 mm long and ~12 mm across, socket
sized 13.0 nominal at the user's request for room; cartridges 11 x 55 mm; pen 30 g and a cartridge
10 g for the stability sum.  All single constants in params.py.
"""
from math import atan2, cos, degrees, radians, sin, tau

from build123d import Axis, CenterOf, Cylinder, Part, Plane, Pos, Rot, chamfer, extrude

from lib.component import drop_debris, on_bed
from lib.form.blobs import ball, ball_chain, dome_chain, surface_studs
from lib.form.lattice import voronoi_shell
from lib.form.mesh import textured
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


def _cells(radius: float, band: tuple[float, float], count: int, seed: int, web: float,
           inner: float) -> Part:
    """The Voronoi cutter for one band, in the body's OWN frame (its axis on Z).

    Cut per body, before the scene is unioned.  Cut afterwards, the bowl's cutters — which start
    outside the bowl and run to the axis — would also punch cells through the caterpillar's arms
    where they wrap it, and mushroom A's would reach across into mushroom B.
    """
    z0, z1 = band
    return Pos(0, 0, (z0 + z1) / 2) * voronoi_shell(
        radius=radius, height=z1 - z0, count=count, seed=seed, web=web, inner=inner,
        corner_r=P.VORONOI_CORNER_R, roof_angle=P.VORONOI_ROOF, relax=P.VORONOI_RELAX,
        over=P.VORONOI_OVER)


def _hookah() -> Part:
    """Bowl and stem, bored for the pen, fluted down the waist, then opened up with Voronoi cells.

    The bore is cut FIRST and in this body's own frame.  Cut afterwards, every cell cutter runs on
    through solid material to the axis, twenty of them pile up in the core, and the union of that
    pile leaves slivers of leftover wall just outside the bore.  Against an already-hollow body the
    same cutters simply run out into the void.
    """
    solid = revolved_body(P.HOOKAH_PROFILE)
    body = solid - Pos(0, 0, P.HOOKAH_H) * _socket(P.PEN_D, P.PEN_DEPTH)
    body = flutes(body, count=P.STEM_FLUTE_N, width=P.STEM_FLUTE_W, depth=P.STEM_FLUTE_D,
                  z_from=P.STEM_FLUTE_Z[0], z_to=P.STEM_FLUTE_Z[1], reference=solid)
    return body - _cells(P.BOWL_CELL_R, P.BOWL_CELL_Z, P.BOWL_CELL_N, P.BOWL_CELL_SEED,
                         P.BOWL_WEB, P.BOWL_CELL_IN)


def _cap_spots(mushroom: Part, top_z: float) -> Part:
    """Toadstool spots: a dome dropped straight down onto the cap lands tilted with the surface."""
    rays = [((x, y, top_z + P.CAP_SPOT_CAST), (0, 0, -1)) for x, y in P.CAP_SPOT_XY]
    return surface_studs(mushroom, rays, radius=P.CAP_SPOT_R, height=P.CAP_SPOT_H,
                         embed=P.CAP_SPOT_EMBED)


def _mushroom(profile, top_z: float, depth: float, radius: float, band: tuple[float, float],
              count: int, seed: int) -> Part:
    """One toadstool: spotted cap, openwork stalk, the cartridge showing through the cells.

    Bored before it is decorated, for the reason given in ``_hookah``.  The spots are seated against
    the un-bored solid so a ray still finds a surface where the bore has since opened.
    """
    solid = revolved_body(profile)
    body = solid - Pos(0, 0, top_z) * _socket(P.CART_D, depth)
    body += _cap_spots(solid, top_z)
    return body - _cells(radius, band, count, seed, P.STALK_WEB, P.STALK_CELL_IN)


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


def _scene() -> Part:
    """Everything unioned, before a single bore is cut."""
    solid = _ground() + _hookah()
    solid += Pos(*P.MUSH_A_XY) * _mushroom(P.MUSHROOM_PROFILE, P.MUSH_A_H, P.CART_A_DEPTH,
                                           P.STALK_CELL_R, P.STALK_A_CELL_Z, P.STALK_A_CELL_N,
                                           P.STALK_A_CELL_SEED)
    solid += Pos(*P.MUSH_B_XY) * _mushroom(P.MUSHROOM_B_PROFILE, P.MUSH_B_H, P.CART_B_DEPTH,
                                           P.STALK_B_CELL_R, P.STALK_B_CELL_Z, P.STALK_B_CELL_N,
                                           P.STALK_B_CELL_SEED)
    solid += _caterpillar()
    solid += _eyes()
    return chamfer(solid.faces().sort_by(Axis.Z)[0].outer_wire().edges(), P.BED_CHAMFER)


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


# The lattice makes this a perforated part, and the inward-ray wall metric cannot measure one: it
# samples by area, and most of an openwork surface is the inside of a hole, so a fifth of the samples
# land within a nozzle width of a rim and report walls that are not there.  Measured on this part
# with the honest measure (check_printable --opening, a morphological opening): 0.42% of volume is
# out of reach of a 0.8 mm ball, against 0.66% for a PLAIN tube with no holes in it at all.  So the
# webs are sound and the metric is not; "openwork" keeps it reported and stops it gating.
PRINT_MODES = {"holder": "openwork"}


def build() -> dict:
    """The printed part: the B-rep solid with a noise skin displaced onto it, so this returns a mesh."""
    return {"holder": on_bed(textured(holder(), amplitude=P.TEXTURE_AMP, scale=P.TEXTURE_SCALE,
                                      kind="noise", mask="exterior", seed=P.TEXTURE_SEED,
                                      edge_length=P.TEXTURE_EDGE, tolerance=P.TEXTURE_TOL,
                                      angular_tolerance=P.TEXTURE_ANG))}


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
    body = on_bed(holder())     # the B-rep solid: the skin is a mesh and has no faces() or centre
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
        print(name, part.bounds, round(part.volume, 1),
              "watertight" if part.is_watertight else "NOT WATERTIGHT", part.body_count, "body(s)")
    for tag, r in stability().items():
        ok = "" if tag != "loaded_on_feet" else (
            "  <- governing, target {} -> {}".format(
                P.MIN_TIP_ANGLE, "OK" if r["tip_angle_deg"] >= P.MIN_TIP_ANGLE else "TOO TIPPY"))
        print(f"{tag:16s} {r['mass_g']:6.1f} g  com {r['com']}  margin {r['margin_mm']:5.1f} mm  "
              f"tip {r['tip_angle_deg']:5.1f} deg{ok}")
