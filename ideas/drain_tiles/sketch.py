"""Sketch for ideas/drain_tiles: one tile of a snap-together draining field that
sits on the counter beside an undermount sink and feeds the drip rail.

Use orientation (the coordinates everything is written in):
    +X  along the counter edge (tiles snap to each other along X)
    +Y  toward the sink;  the tile spans y in [-TILE_Y, 0], outboard edge at y 0
    +Z  up, counter surface at z 0.

The IDEA as written asked for a slot grid over a sloped floor *and* an open
bottom.  Those contradict: with nothing under the slots the water lands on the
counter.  Resolved here as ONE surface — a deck pitched toward the sink with
trapezoidal grooves running down it.  Dishes stand on the ribs between grooves,
water runs in the grooves to the outboard edge and off a drip nose.  Nothing is
enclosed, the whole underside is open front to back, and a brush reaches every
face.

Print orientation: deck face down on the bed (rotate 180 + PITCH_DEG about X).
The side walls, the drip nose and the snap bead all point up off a flat
TILE_X x TILE_Y bed face, so the tile prints with no support.  The grooves are
trapezoidal rather than square so their inverted ceilings self-support.

Freehand geometry.  See IDEA.md for what the reuse map looks like after this
round — it is much shorter than it was before the sketch.
"""
from math import radians, tan

from build123d import *  # noqa: F401,F403

from lib.component import on_bed

# --- knobs (mm) ---------------------------------------------------------------
TILE_X = 90.0         # tile pitch along the counter edge; the field grows in X
TILE_Y = 140.0        # counter depth the field uses (the field is ONE row deep,
                      #     see IDEA.md log: rows in Y would each need to sit lower)
DECK_T = 3.2          # deck thickness (grooves take 1.2 of it)
PITCH_DEG = 4.0       # deck pitch toward the sink
FOOT_H = 12.0         # deck underside height above the counter at the outboard edge.
                      #     Must clear the drip rail's pan rim (ZTOP), which the deck
                      #     cantilevers over — see WALL_SETBACK and the IDEA.md log.

WALL_T = 2.4          # side walls; they are also the feet and the snap faces
WALL_SETBACK = 14.0   # walls stop this far short of the outboard deck edge, so the
                      #     deck overhangs the drip rail's rim and drips into its pan
GROOVE_PITCH = 9.0    # centre to centre across the grooves
GROOVE_W = 5.0        # groove width at the deck surface
GROOVE_D = 1.2        # groove depth
GROOVE_WALL_DEG = 30.0  # groove wall angle off vertical. Inverted on the bed the
                      #     groove narrows going up, so this IS the overhang angle;
                      #     45 is the limit and reads as a flag, 30 is comfortable.
NOSE_D = 3.0          # drip nose hanging below the outboard edge
NOSE_T = 2.4

SNAP_R = 0.6          # snap bead radius (mechanisms.snap_ridge default)
SNAP_CLEAR = 0.1      # added to the groove so the bead seats without binding
SNAP_Z = 5.0          # bead height above the counter
SNAP_INSET = 8.0      # bead stops this far short of each end (lead-in)

_TP = tan(radians(PITCH_DEG))
_GROOVE_RUN = GROOVE_D * tan(radians(GROOVE_WALL_DEG))


def deck_underside(y: float) -> float:
    """Height of the deck underside above the counter, pitched toward +Y."""
    return FOOT_H - y * _TP


def _deck() -> Part:
    """Deck built flat in its own frame (outboard-bottom edge at the origin),
    grooved, nosed, then tilted by the pitch and lifted onto its walls."""
    slab = Pos(0, -TILE_Y / 2, DECK_T / 2) * Box(TILE_X, TILE_Y, DECK_T)

    n = int(TILE_X // GROOVE_PITCH)
    groove = Pos(0, 0, DECK_T) * extrude(
        Plane.XZ
        * Polygon(
            (-GROOVE_W / 2, 0.0),
            (GROOVE_W / 2, 0.0),
            (GROOVE_W / 2 - _GROOVE_RUN, -GROOVE_D),
            (-GROOVE_W / 2 + _GROOVE_RUN, -GROOVE_D),
            align=None,
        ),
        amount=TILE_Y + 2,
        both=True,
    )
    slab -= [loc * groove for loc in GridLocations(GROOVE_PITCH, 1, n, 1)]

    nose = Pos(0, -NOSE_T / 2, -NOSE_D / 2) * Box(TILE_X, NOSE_T, NOSE_D)
    return Pos(0, 0, FOOT_H) * (Rot(-PITCH_DEG, 0, 0) * (slab + nose))


def _wall() -> Part:
    """One side wall: flat on the counter, top running 1 mm into the deck."""
    return extrude(
        Plane.YZ
        * Polygon(
            (-WALL_SETBACK, 0.0),
            (-WALL_SETBACK, deck_underside(-WALL_SETBACK) + 1.0),
            (-TILE_Y, deck_underside(-TILE_Y) + 1.0),
            (-TILE_Y, 0.0),
            align=None,
        ),
        amount=WALL_T,
    )


def build():
    tile = _deck()
    tile += Pos(TILE_X / 2 - WALL_T, 0, 0) * _wall()
    tile += Pos(-TILE_X / 2, 0, 0) * _wall()

    span = TILE_Y - WALL_SETBACK
    bead = Pos(0, -WALL_SETBACK - span / 2, SNAP_Z) * Rot(90, 0, 0) * Cylinder(
        SNAP_R, span - 2 * SNAP_INSET
    )
    tile += Pos(TILE_X / 2, 0, 0) * bead                       # ridge on the +X face
    tile -= Pos(-TILE_X / 2, 0, 0) * Pos(0, -WALL_SETBACK - span / 2, SNAP_Z) * Rot(
        90, 0, 0
    ) * Cylinder(SNAP_R + SNAP_CLEAR, span + 2)                                                          # groove in the -X face

    return {"tile": on_bed(Rot(180 + PITCH_DEG, 0, 0) * tile)}
