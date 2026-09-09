"""Countertop drain system for an undermount sink: an edge rail, a field of tiles, a pot rack.

Parts, all printed in the orientation returned:

* ``rail`` — ONE 140 mm segment of the C-clip that grips the countertop at the sink cutout, carrying
  a shallow pan whose floor pitches at the basin. The measured 420 mm run will not fit a 270 mm bed,
  so print ``RAIL_SEGMENTS`` (3) of these and butt them end to end: the seam runs across the pan and
  the water runs along it toward the basin rather than over it. Printed lying on the jaw's OUTBOARD face: that face and the pan
  floor's outboard end face are coplanar by construction, so the whole part stands off one flat bed
  face and the only downward surface left is the rim ramp, held at ~41 degrees by ``RAMP_RATIO``.
* ``tile_row1`` / ``tile_row2`` — the draining field. **One design, one number apart**: row 2 stands
  ``ROW_DROP`` taller than row 1. Printed deck face down; the walls, the end rib, the drip nose and
  the snap bead all stand up off a flat TILE_X x TILE_Y bed face, so no supports.
* ``rack`` — the comb of leaning blades that holds pots, pans and lids on edge. Printed as drawn,
  base underside on the bed, blades up; the blades are sheared rather than rotated so every root
  stays flat and the lean is the only overhang in the part.

**How the pieces interconnect.** Nothing seals and nothing screws:

* Tile to tile ACROSS the counter (X): ``mechanisms.snap_ridge`` on the +X wall into
  ``mechanisms.snap_groove`` on the -X wall. The field grows along the edge one tile at a time.
* Tile to tile BACK from the sink (Y): a lap, not a key. Each row's deck overhangs its own walls by
  ``LAP`` at the downhill edge and lies over the row in front, and each row stands ``ROW_DROP``
  taller so the whole field is ONE continuous pitched plane. This is why the four-edge symmetric
  key from the brief could not work: on a flat counter, identical tiles at identical leg height put
  row 2's downhill edge BELOW row 1's uphill edge by the tile's own drop, and every seam dams. The
  drop has to go somewhere, and the legs are where it goes. Row n's uphill ``END_RIB`` is what the
  row behind butts against, so the rows cannot creep apart.
* Tile field to rail: the front row's deck cantilevers ``DRIP_OVER`` past the rail's rim crest and
  drips into the pan. ``RIM_H`` is 4 mm rather than 10 for exactly this.
* Rack to tile: it stands on the deck and inherits its pitch, so its base only has to move water
  off its own front edge onto the tile downstream. That is why there is no sloped base and no spout
  here — the row already has one. Its blade tops slope ``TOP_SLOPE_DEG`` toward the sink on top of
  the deck's own pitch, because a rim resting across level blade tops sits horizontally and holds
  exactly the ring of water this rack exists to drain.

Water goes: rack -> row 2 -> row 1 -> pan -> basin, each stage handing off by overhanging the next.

Assumptions, all of them parameters (see ``params.py``):

* **PLA throughout, at the user's request.** The three write-ups specified PETG for the splash zone.
  PLA is defensible for the tiles (keyed, not sprung, nothing hot lands on them); on the rack it is
  the user's accepted risk, and a hot pan straight off the hob is what would find it.
* **The counter is measured**: 30 mm slab, 420 x 420 mm of counter. ``UNDER_REACH`` (4 mm) is the
  one number still guessed — the exposed underside at the cutout that the return lip tucks into.
  Measure it before printing the rail; nothing else in the system depends on it.
* Two rows of 70 mm tiles use 181 mm of the 420 mm depth. Depth is limited by leg height, not by
  counter: every row back costs ``ROW_DROP`` (11 mm) because the lap must clear the deck and drip
  nose of the row in front. 3 rows would put the back row on 35 mm legs; that is the practical end.
* A full field is ``RAIL_SEGMENTS`` x rail, ``TILES_PER_ROW`` x each row (6 + 6), and one rack.
* Rack sized for 2 pot bays at 48 mm and 6 lid slots at 12 mm; real pot and lid sizes would set
  these properly.

Open, and only a print answers them: whether a big pot rim-down sits stably across 48 mm bays or
wants a concave blade top, and whether the tiles need an anti-slip pad where they meet the stone.
"""
from build123d import Box, Plane, Polygon, Pos, Rot, extrude

from lib.component import on_bed
from lib.mechanisms.snap_fit import snap_groove, snap_ridge
from lib.primitives.edge_clip import edge_clip
from lib.primitives.groove_field import groove_field
from lib.primitives.slot_rack import slot_rack

from . import params as P
from .params import *  # noqa: F401,F403


# ---------------------------------------------------------------- rail

def _floor_top(y: float) -> float:
    """Pan floor height above the counter at inland coordinate y (y <= JAW_T)."""
    return FLOOR_T + (JAW_T - y) * PAN_TP


def _rail():
    """The edge clip with its pan, in USE orientation (counter top z=0, cut face y=0)."""
    clip = edge_clip(
        length=RAIL_LEN, thickness=COUNTER_T, throat_clearance=THROAT_CLEAR, jaw_t=JAW_T,
        under_reach=UNDER_REACH, lip_t=LIP_T, saddle_t=FLOOR_T, saddle_reach=PAN_REACH,
        corner_relief=CORNER_RELIEF, drip_groove_r=DRIP_GROOVE_R, drip_groove_z=DRIP_GROOVE_Z,
        drip_groove_out=DRIP_GROOVE_OUT,
    )
    # The pan sits ON the saddle: floor rising inland to the rim, ramp back down onto the floor.
    pan = extrude(
        Plane.YZ * Polygon(
            (JAW_T, FLOOR_T),                       # outboard lip: water leaves here
            (-PAN_REACH, FLOOR_T),                  # along the saddle top
            (-PAN_REACH, PAN_ZTOP),                 # up the inland face to the rim crest
            (-PAN_REACH + RIM_TOP_W, PAN_ZTOP),     # flat on the crest (no knife edge)
            (Y_RAMP, _floor_top(Y_RAMP)),           # ramp down onto the pitched floor
            align=None,
        ),
        amount=RAIL_LEN / 2, both=True,
    )
    # End walls are the whole pan outline, not just the cavity: a wall that shares only the floor
    # edge with the rail fuses as a loose body.
    wall = extrude(
        Plane.YZ * Polygon(
            (JAW_T, FLOOR_T), (-PAN_REACH, FLOOR_T), (-PAN_REACH, PAN_ZTOP), (JAW_T, PAN_ZTOP),
            align=None,
        ),
        amount=END_WALL_T / 2, both=True,      # centred: a polygon's winding decides which way a
    )                                          # one-sided extrude goes, and that is not worth relying on
    x_end = RAIL_LEN / 2 - END_WALL_T / 2
    return clip + pan + Pos(x_end, 0, 0) * wall + Pos(-x_end, 0, 0) * wall


# ---------------------------------------------------------------- tiles

def _deck_underside(foot_h: float, y: float) -> float:
    return foot_h - y * DECK_TP


def _tile(foot_h: float):
    """One tile in USE orientation, downhill deck edge at y=0, deck spanning y in [-TILE_Y, 0].

    ``foot_h`` is the only thing that differs between rows.
    """
    slab = Pos(0, -TILE_Y / 2, DECK_T / 2) * Box(TILE_X, TILE_Y, DECK_T)
    slab -= Pos(0, 0, DECK_T) * groove_field(
        area_l=TILE_X, area_w=TILE_Y + 2, pitch=GROOVE_PITCH, width=GROOVE_W,
        depth=GROOVE_D, wall_deg=GROOVE_WALL_DEG,
    )
    nose = Pos(0, -NOSE_T / 2, -NOSE_D / 2) * Box(TILE_X, NOSE_T, NOSE_D)
    tile = Pos(0, 0, foot_h) * (Rot(-DECK_PITCH_DEG, 0, 0) * (slab + nose))

    # Side walls: flat on the counter, tops running 1 mm into the deck, stopping LAP short of the
    # downhill edge so the deck cantilevers over whatever is in front.
    wall = extrude(
        Plane.YZ * Polygon(
            (-LAP, 0.0),
            (-LAP, _deck_underside(foot_h, -LAP) + 1),
            (-TILE_Y, _deck_underside(foot_h, -TILE_Y) + 1),
            (-TILE_Y, 0.0),
            align=None,
        ),
        amount=WALL_T / 2, both=True,          # centred, see the note on the rail's end walls
    )
    x_wall = TILE_X / 2 - WALL_T / 2
    tile += Pos(x_wall, 0, 0) * wall
    tile += Pos(-x_wall, 0, 0) * wall

    # Uphill cross rib: stiffens the deck and gives the row behind something to butt against.
    tile += extrude(
        Plane.YZ * Polygon(
            (-TILE_Y, 0.0),
            (-TILE_Y, _deck_underside(foot_h, -TILE_Y) + 1),
            (-TILE_Y + END_RIB_T, _deck_underside(foot_h, -TILE_Y + END_RIB_T) + 1),
            (-TILE_Y + END_RIB_T, 0.0),
            align=None,
        ),
        amount=TILE_X / 2, both=True,
    )

    span = TILE_Y - LAP
    y_mid = -LAP - span / 2
    tile += Pos(TILE_X / 2, y_mid, SNAP_Z) * Rot(0, 0, -90) * snap_ridge(
        length=span - 2 * SNAP_INSET, r=SNAP_R)
    tile -= Pos(-TILE_X / 2, y_mid, SNAP_Z) * Rot(0, 0, 90) * snap_groove(
        length=span + 2, r=SNAP_R, clearance=SNAP_CLEAR)
    return tile


# ---------------------------------------------------------------- rack

def _zones():
    """(pot centre x, lid centre x, total blade span in X)."""
    pot_span = (POT_FINS - 1) * POT_PITCH
    lid_span = (LID_FINS - 1) * LID_PITCH
    total = pot_span + ZONE_GAP + lid_span
    return -total / 2 + pot_span / 2, total / 2 - lid_span / 2, total


def _blade_x():
    pot_x, lid_x, _ = _zones()
    pot = [pot_x + (i - (POT_FINS - 1) / 2) * POT_PITCH for i in range(POT_FINS)]
    lid = [lid_x + (i - (LID_FINS - 1) / 2) * LID_PITCH for i in range(LID_FINS)]
    return sorted(pot + lid)


def _groove_lanes(base_l: float):
    """Groove centres keyed to the bays between blades, never under a blade: the grooves run
    parallel to the blades, and one that lands under a blade severs it from the base."""
    blades = _blade_x()
    edges = [(-base_l / 2 + FIN_T / 2, blades[0])]
    edges += list(zip(blades, blades[1:]))
    edges += [(blades[-1], base_l / 2 - FIN_T / 2)]
    lanes = []
    for x0, x1 in edges:
        usable = (x1 - x0) - FIN_T - 2 * BAY_MARGIN
        k = int(usable // GROOVE_PITCH)
        if k < 1:
            continue
        mid = (x0 + x1) / 2
        lanes += [mid + (i - (k - 1) / 2) * GROOVE_PITCH for i in range(k)]
    return lanes


def _rack():
    """The comb, base underside on z=0 (already print orientation)."""
    pot_x, lid_x, total = _zones()
    base_l = total + FIN_T + 2 * BASE_MARGIN
    rack = Pos(0, 0, BASE_T / 2) * Box(base_l, RACK_DEPTH, BASE_T)
    # Blades run from z=0 through the base, not off its top face: a blade that merely shares a face
    # with the base fuses as a loose body. Cutting the grooves through base and blades together is
    # also what lets water past each root instead of damming behind it.
    rack += Pos(pot_x, 0, 0) * slot_rack(
        POT_FINS, POT_PITCH, FIN_T, BASE_T + POT_FIN_H, RACK_DEPTH, TILT_DEG, TOP_SLOPE_DEG)
    rack += Pos(lid_x, 0, 0) * slot_rack(
        LID_FINS, LID_PITCH, FIN_T, BASE_T + LID_FIN_H, RACK_DEPTH, TILT_DEG, TOP_SLOPE_DEG)
    rack -= Pos(0, 0, BASE_T) * groove_field(
        area_l=base_l, area_w=RACK_DEPTH + 2, pitch=GROOVE_PITCH, width=GROOVE_W,
        depth=GROOVE_D, wall_deg=GROOVE_WALL_DEG, lanes=_groove_lanes(base_l),
    )
    return rack


# ---------------------------------------------------------------- build

def build():
    parts = {"rail": on_bed(Rot(-90, 0, 0) * _rail())}
    for row in range(ROWS):
        parts[f"tile_row{row + 1}"] = on_bed(
            Rot(180 + DECK_PITCH_DEG, 0, 0) * _tile(FOOT_H + row * ROW_DROP))
    parts["rack"] = _rack()
    return parts


def _placed_tile(row: int):
    """Tile of the given row (0 = nearest the sink) in the assembly frame."""
    return Pos(0, TILE_Y0 - row * (TILE_Y - LAP), 0) * _tile(FOOT_H + row * ROW_DROP)


def _placed_rack(row: int):
    """The rack standing on the deck of the given row, with RACK_GAP of air under it."""
    foot_h = FOOT_H + row * ROW_DROP
    y_local = -TILE_Y / 2
    z = _deck_underside(foot_h, y_local) + DECK_T + RACK_GAP
    return Pos(0, TILE_Y0 - row * (TILE_Y - LAP) + y_local, z) * Rot(-DECK_PITCH_DEG, 0, 0) * _rack()


def fit_checks(parts):
    """Every hand-off in the system, as pairs that must not intersect once assembled."""
    front, back = _placed_tile(0), _placed_tile(ROWS - 1)
    return {
        # the front row's deck cantilevers over the rail's rim; the drip nose is the tight one
        "rail_vs_front_row": (_rail(), front),
        # the lap: the back row rides over the front row's uphill end and butts its end rib
        "front_row_vs_back_row": (front, back),
        # the snap joint along the counter: bead into groove with SNAP_CLEAR to spare
        "tile_to_tile_snap": (front, Pos(TILE_X, 0, 0) * _placed_tile(0)),
        # the rack stands on the back row's deck and must clear it
        "rack_on_back_row": (back, _placed_rack(ROWS - 1)),
        # and must not foul the row in front of the one it stands on
        "rack_vs_front_row": (front, _placed_rack(ROWS - 1)),
    }
