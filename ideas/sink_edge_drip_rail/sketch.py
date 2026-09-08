"""Sketch for ideas/sink_edge_drip_rail: a drip rail that clips over the square
countertop edge at an undermount sink cutout and pours runoff into the basin.

Use orientation (the coordinates the profile is written in):
    +X  along the counter edge (rail length)
    +Y  outboard, over the basin;  -Y inland, onto the countertop
    +Z  up.  Counter top surface = z 0, cut face = y 0, counter material y < 0.

Section, inland to outboard: a shallow pan sitting on the counter (floor pitched
toward the sink), a rim ramp at the inland end, then the pan floor ends flush
with the outboard face of a jaw that hangs down the square cut face, ending in a
return lip that tucks under the counter into the reveal.

Print orientation: rotated so the jaw's outboard face is on the bed.  That face
and the pan floor's end face are coplanar by construction, giving a flat bed
face of RAIL_LEN x (COUNTER_T + LIP_T + FLOOR_T); the pan floor, the end walls
and the return lip all stand up off it, so the only downward-facing surface in
the whole part is the rim ramp, held at ~41 deg by RAMP_RATIO.

Freehand geometry.  The reuse map in IDEA.md is what turns this into a model;
the section here is the proposed primitives.edge_clip (jaw + throat + lip) with
a pan grown off its top flange.
"""
from math import radians, tan

from build123d import *  # noqa: F401,F403

from lib.component import on_bed

# --- knobs (mm) ---------------------------------------------------------------
COUNTER_T = 30.0        # <-- countertop thickness at the cutout. 3 cm stone is the
                        #     standard undermount slab; 2 cm slab = 20, laminate
                        #     with a built-up edge = 38.  Everything else follows.
THROAT_CLEAR = 0.4      # added to COUNTER_T so the clip slides onto a square edge
JAW_T = 3.0             # thickness of the jaw hanging down the cut face
UNDER_REACH = 4.0       # how far the return lip tucks under the counter (= the
                        #     reveal; 0 makes it a plain saddle held by the pan)
LIP_T = 2.4             # return lip thickness

RAIL_LEN = 180.0        # along the counter edge
PAN_REACH = 55.0        # how far inland the pan sits on the counter
FLOOR_T = 2.4           # pan floor thickness at the outboard edge
PITCH_DEG = 3.0         # floor pitch toward the sink
RIM_H = 10.0            # rim height above the floor at the inland end
RAMP_RATIO = 1.15       # rim ramp run / rise; >= 1.0 keeps it self-supporting
END_WALL_T = 2.4        # end walls closing the pan at both ends

DRIP_GROOVE_R = 1.0     # drip break cut into the outboard face below the pan
DRIP_GROOVE_Z = 2.0     # how far below the counter top surface it sits
CORNER_RELIEF = 1.2     # relief radius at both counter corners so the printed
                        # inside corners cannot hold the clip off the stone

THROAT = COUNTER_T + THROAT_CLEAR
_TP = tan(radians(PITCH_DEG))
_RAMP = RIM_H * RAMP_RATIO
_Y_RAMP = -PAN_REACH + _RAMP


def floor_top(y: float) -> float:
    """Interior floor height above the counter surface, pitched toward +Y."""
    return FLOOR_T - y * _TP


ZTOP = floor_top(_Y_RAMP) + RIM_H


def section() -> Sketch:
    """Closed C-section in (y, z), drawn as a sketch in XY (x = y_use, y = z_use)."""
    pts = [
        (JAW_T, -THROAT - LIP_T),          # bed plane, bottom of the return lip
        (JAW_T, floor_top(JAW_T)),         # up the outboard face (jaw + pan end)
        (_Y_RAMP, floor_top(_Y_RAMP)),     # pitched interior floor, inland
        (-PAN_REACH, ZTOP),                # rim ramp
        (-PAN_REACH, 0.0),                 # inland face down to the counter
        (0.0, 0.0),                        # counter contact face out to the edge
        (0.0, -THROAT),                    # down the cut face
        (-UNDER_REACH, -THROAT),           # in under the counter (the reveal)
        (-UNDER_REACH, -THROAT - LIP_T),   # lip end face
    ]
    sk = Polygon(*pts, align=None)
    sk -= Pos(0, 0) * Circle(CORNER_RELIEF)            # top counter corner
    sk -= Pos(0, -THROAT) * Circle(CORNER_RELIEF)      # bottom counter corner
    sk -= Polygon(                                     # drip break, V-notch
        (JAW_T, -DRIP_GROOVE_Z + DRIP_GROOVE_R),
        (JAW_T - DRIP_GROOVE_R, -DRIP_GROOVE_Z),
        (JAW_T, -DRIP_GROOVE_Z - DRIP_GROOVE_R),
        align=None,
    )
    return sk


def end_wall() -> Sketch:
    """The whole section outline filled solid (C plus pan cavity), as one polygon
    so it fuses with the rail instead of only touching its floor."""
    return Polygon(
        (JAW_T, -THROAT - LIP_T),
        (JAW_T, ZTOP),
        (-PAN_REACH, ZTOP),
        (-PAN_REACH, 0.0),
        (0.0, 0.0),
        (0.0, -THROAT),
        (-UNDER_REACH, -THROAT),
        (-UNDER_REACH, -THROAT - LIP_T),
        align=None,
    )


def build():
    rail = extrude(section(), amount=RAIL_LEN / 2, both=True)
    wall = extrude(end_wall(), amount=END_WALL_T)
    rail += Pos(0, 0, RAIL_LEN / 2 - END_WALL_T) * wall
    rail += Pos(0, 0, -RAIL_LEN / 2) * wall
    # jaw outboard face (x = JAW_T here) onto the bed: x -> -z, z -> x
    return {"rail": on_bed(Rot(0, 90, 0) * rail)}
