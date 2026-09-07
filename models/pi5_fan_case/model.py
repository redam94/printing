"""Raspberry Pi 5 enclosure: body (floor on the bed) + two alternative lids with a 30 mm fan (printed upside down).

Parts
  ``body`` — open-top rounded shell, four M2.5 heat-set standoffs at the Pi 5 hole pattern (Pi
  screwed down from above), four M3 heat-set bosses fused into the inner corners for the screw lid,
  connector windows for USB-C + 2x micro-HDMI (-Y wall), Ethernet + 2x USB-A (+X wall) and a
  microSD access window (-X wall), vertical exhaust vent slots on the +Y (GPIO) wall, four
  rubber-foot recesses underneath, and four cantilever snap latches cut into the top of the +/-Y
  walls (for ``lid_snap``; harmless under ``lid``).
  ``lid`` — screw lid: flat plate with a drop-in lip (square-notched around the corner bosses),
  four M3 clearance holes, 30 mm fan cutout + 4 x M3 fan screw holes centred over the SoC.
  ``lid_snap`` — snap-fit lid: same plate, lip and fan cutout, no screw holes; four skirt tabs
  hang outside the long walls, each with a window that the body's latch hook snaps into.

Snap latch design (mechanisms.cantilever_latch + mechanisms.latch_window)
  The latch component's orientation rule is "beam lying flat in the bed plane — never print the
  beam standing up".  A finger hanging from a face-down lid would stand up, so the beams live on
  the BODY instead: each is a 12 x 6 mm strip of the wall at the rim, freed by a 1 mm slit below
  and at its tip, beam length along X, flexing in Y (bending stress runs along the layers).  The
  hook points outward through a window in the lid's skirt tab.  Closing: the tab's chamfered
  bottom edge pushes the hook inward ~1 mm until the window lines up and the hook springs out;
  the hook's underside then bears on the tab material under the window.  Release: press the four
  hooks inward while lifting.  The lid lip is removed over each beam so the deflected beam has room.

Hardware: Raspberry Pi 5 (bare or with a low-profile heatsink <= 7 mm), 4x M2.5 + 4x M3 brass
heat-set inserts (CNC Kitchen / Ruthex standard length), 4x M2.5 x 6 screws (Pi), 4x M3 x 8
screws (screw lid only), one 30 x 30 x 10 mm fan with 4x M3 x 16 screws + nuts (or self-tappers).
The fan is meant to hang under the lid blowing down onto the SoC; exhaust leaves through the +Y
vents.  It can equally be bolted on top of the lid — the cutout is the same either way.

Print orientation: body floor on the bed; lids top face on the bed (returned already flipped).
Material: PETG for the body if you use the snap lid (the latch component is validated in PETG
only; PLA fatigues); either PLA or PETG with the screw lid.  All parts sit with z_min = 0.

Assumptions (user unavailable):
  * Corner bosses need ~5.6 mm between the board edge and the wall, so the cavity is 6.5 mm bigger
    than the PCB on every side — connectors are recessed ~8 mm from the outer face and the
    windows are sized for cable overmolds (USB-C 14.5 x 8.5, micro-HDMI 11.5 x 7.5).
  * Pi standoffs use a 1.2 mm insert wall (OD 6.4) instead of the 1.6 default to respect the
    component keep-out around the Pi's mounting holes; use STANDOFF_WALL = 1.6 if you prefer.
  * Pi 5 power button and PCIe/CSI/DSI connectors are not dimensioned on the official drawing
    and get no cutouts; the microSD window position is inferred (slot centred on the SD edge).
  * No Active Cooler: with the official cooler (13.7 mm tall) the lid fan would collide; raise
    HEADROOM to >= 28 or move FAN_X/FAN_Y.
  * Snap lid: latch defaults (12 x 6 x 1.6 beam, 1.2 hook, 30 deg entry, 90 deg retention) and
    root_fillet=0 because the beam root merges into the continuous wall.  The latch is cut with
    the wall it belongs to, so the vents were shortened to stay 1.2 mm below the latch slits.
"""
from build123d import Align, Box, Part, Plane, Polygon, Pos, Rectangle, Rot, Sketch, extrude

from lib.component import flip_to_assembly, locations_of, on_bed
from lib.fasteners.clearance_hole import clearance_hole
from lib.fasteners.heat_set_boss import heat_set_boss
from lib.mechanisms.cantilever_latch import cantilever_latch, latch_window
from lib.patterns.corners import corner_holes
from lib.patterns.fan import fan_mount
from lib.patterns.pi import pi5_mount, pi5_port_cutouts, pi_board_outline
from lib.primitives.feet import rubber_foot_recess
from lib.primitives.rounded_box import box_lid, rounded_box
from lib.primitives.vented_panel import vent_slots

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P

# Component frame -> wall frame: beam length (+Z) -> +X along the wall, thickness/hook (+X) -> +Y
# (outward on the +Y wall), width (Y) -> Z.  Applied to both the latch and its window.
_TO_WALL = Rot(0, 0, 90) * Rot(90, 0, 0)


def _corner_locations():
    """Lid-screw / corner-boss centres, inset from the inner cavity corners."""
    return locations_of(corner_holes(P.INNER_L, P.INNER_W, inset=P.BOSS_INSET))


def _pi_locations():
    """Pi 5 mounting-hole centres, translated to the board's place in the box."""
    return [Pos(P.PI_X, P.PI_Y) * loc for loc in locations_of(pi5_mount())]


def _through_wall(sketch_on_plane):
    """Cut a wall-plane sketch through one wall (cutter spans exactly the wall thickness)."""
    return extrude(sketch_on_plane, amount=P.WALL, both=True)


def _four_fold(shape):
    """Replicate a +X/+Y-quadrant feature to all four latch positions (mirror in X, then in Y)."""
    pair = shape + shape.mirror(Plane.YZ)
    return pair + pair.mirror(Plane.XZ)


def _latch_pocket():
    """Wall opening for one beam: beam volume + slit below + slit at the tip, open to the rim (+Y wall, root at -X)."""
    depth = P.LATCH_T + 2 * P.LATCH_POCKET_MARGIN
    height = P.LATCH_POCKET_H + P.LATCH_POCKET_MARGIN
    return Pos(-P.LATCH_ROOT_X, P.INNER_W / 2 - P.LATCH_POCKET_MARGIN, P.OUTER_H - P.LATCH_POCKET_H) * Box(
        P.LATCH_POCKET_L, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))


def _latch():
    """One body-side latch: beam re-filling the wall strip, hook protruding outward (+Y wall, root at -X)."""
    latch = cantilever_latch(length=P.LATCH_L, width=P.LATCH_W, thickness=P.LATCH_T, hook_depth=P.LATCH_HOOK_D,
                             hook_height=P.LATCH_HOOK_H, root_fillet=0)
    return Pos(-P.LATCH_ROOT_X, P.INNER_W / 2, P.LATCH_Z) * _TO_WALL * latch


def _skirt_tab():
    """Rigid tab hanging outside the +Y wall at the +X hook (lid frame: plate underside at z=0)."""
    profile = Polygon((P.TAB_Y0, 0), (P.TAB_Y1, 0), (P.TAB_Y1, -P.TAB_H),
                      (P.TAB_Y0 + P.TAB_CHAMFER, -P.TAB_H), (P.TAB_Y0, -P.TAB_H + P.TAB_CHAMFER), align=None)
    skirt = extrude(Plane.YZ * profile, amount=P.TAB_W / 2, both=True)
    ear = Pos(0, P.OUTER_W / 2 - P.TAB_EAR, 0) * Box(P.TAB_W, P.TAB_EAR + P.TAB_CLEAR + P.TAB_T, P.LID_T,
                                                    align=(Align.CENTER, Align.MIN, Align.MIN))
    return Pos(P.HOOK_X, 0, 0) * (skirt + ear)


def _tab_window():
    """Window through the skirt tab for the hook (lid frame), same rotation as the latch."""
    win = latch_window(P.LATCH_W, P.LATCH_HOOK_D, P.LATCH_HOOK_H, clearance=P.LATCH_CLEAR, wall_t=P.TAB_T)
    return Pos(P.HOOK_X, P.TAB_Y0 + P.TAB_T / 2, -P.LATCH_W / 2) * _TO_WALL * win


def _lid_base(lip_cutouts):
    lid = box_lid(P.OUTER_L, P.OUTER_W, wall=P.WALL, corner_r=P.CORNER_R, thickness=P.LID_T,
                  lip_height=P.LID_LIP_H, lip_thickness=P.LID_LIP_T, clearance=P.LID_CLEARANCE,
                  top_chamfer=P.BED_CHAMFER, lip_cutouts=lip_cutouts)
    return lid - extrude(Pos(P.FAN_X, P.FAN_Y) * fan_mount(P.FAN_SIZE, print_oversize=P.FAN_HOLE_OVERSIZE),
                         amount=P.LID_T, both=True)


def build() -> dict[str, Part]:
    body = rounded_box(P.OUTER_L, P.OUTER_W, P.OUTER_H, wall=P.WALL, floor_t=P.FLOOR_T,
                       corner_r=P.CORNER_R, bottom_chamfer=P.BED_CHAMFER)

    # Pi standoffs (M2.5 inserts) and lid bosses (M3 inserts), both standing on the floor
    standoffs = [loc * heat_set_boss(P.PI_INSERT, height=P.STANDOFF_H, wall=P.STANDOFF_WALL) for loc in _pi_locations()]
    corner_bosses = [loc * heat_set_boss(P.LID_INSERT, height=P.BOSS_H) for loc in _corner_locations()]
    body = body + [Pos(0, 0, P.FLOOR_T) * b for b in standoffs + corner_bosses]

    # connector windows: -Y wall (USB-C, HDMI), +X wall (Ethernet, USB-A), -X wall (microSD)
    power = Plane.XZ.offset(P.OUTER_W / 2) * Pos(P.PI_X, P.PCB_TOP_Z) * pi5_port_cutouts("power", clearance=P.PORT_CLEARANCE)
    usb = Plane.YZ.offset(P.OUTER_L / 2) * Pos(P.PI_Y, P.PCB_TOP_Z) * pi5_port_cutouts("usb", clearance=P.PORT_CLEARANCE)
    sd = Plane.YZ.offset(-P.OUTER_L / 2) * Pos(P.PI_Y, P.PCB_TOP_Z) * pi5_port_cutouts("sd", clearance=P.PORT_CLEARANCE)
    body = body - [_through_wall(s) for s in (power, usb, sd)]

    # exhaust vents through the +Y wall, slots vertical
    vents = Plane.XZ.offset(-P.OUTER_W / 2) * Pos(0, P.VENT_Z) * vent_slots(
        P.VENT_AREA_L, P.VENT_AREA_W, P.VENT_SLOT_W, P.VENT_PITCH, rotation=90)
    body = body - _through_wall(vents)

    # rubber-foot recesses in the underside (cutter flipped so it bites upward from z=0)
    feet = locations_of(corner_holes(P.OUTER_L, P.OUTER_W, inset=P.FOOT_INSET))
    body = body - [loc * Rot(180, 0, 0) * rubber_foot_recess(P.FOOT_D) for loc in feet]

    # snap latches: open the wall strips, then put the flexing beams (with hooks) back in
    body = body - _four_fold(_latch_pocket())
    body = body + _four_fold(_latch())

    # lids: lip notched around the corner bosses (square notches so the lip ends are full-width)
    corners = _corner_locations()
    notches = Sketch() + [loc * Rectangle(2 * P.LIP_NOTCH_R, 2 * P.LIP_NOTCH_R) for loc in corners]

    lid = _lid_base(notches)
    lid = lid - [loc * Pos(0, 0, P.LID_T) * clearance_hole(P.LID_INSERT, depth=P.LID_T, print_oversize=P.LID_HOLE_OVERSIZE)
                 for loc in corners]

    # snap lid: lip also removed over each beam; skirt tabs with hook windows outside the long walls
    lip_gaps = Sketch() + [Pos(sx * P.LIP_GAP_X, sy * P.INNER_W / 2) * Rectangle(P.LIP_GAP_L, P.LIP_GAP_W)
                           for sx in (1, -1) for sy in (1, -1)]
    lid_snap = _lid_base(notches + lip_gaps)
    lid_snap = lid_snap + _four_fold(_skirt_tab()) - _four_fold(_tab_window())

    lid = on_bed(Rot(180, 0, 0) * lid)             # print orientation: top face on the bed
    lid_snap = on_bed(Rot(180, 0, 0) * lid_snap)
    return {"body": body, "lid": lid, "lid_snap": lid_snap}


def fit_checks(parts: dict[str, Part]) -> dict[str, tuple[Part, Part]]:
    """Assembled-state interference checks run by scripts/build.py.

    Both lids are put back on the rim (plate underside at OUTER_H); the Pi is a box envelope:
    PCB outline at its standoff height, PCB_ENVELOPE_H tall (USB-A stacks are the tallest part).
    """
    body = parts["body"]
    lid = flip_to_assembly(parts["lid"], P.OUTER_H + P.LID_T)
    lid_snap = flip_to_assembly(parts["lid_snap"], P.OUTER_H + P.LID_T)
    pcb = Pos(P.PI_X, P.PI_Y, P.PCB_BOTTOM_Z) * extrude(pi_board_outline("pi5"), amount=P.BOARD.pcb_t + P.PCB_ENVELOPE_H)
    return {
        "lid_vs_body": (lid, body),
        "lid_snap_vs_body": (lid_snap, body),
        "pcb_vs_body": (pcb, body),
        "pcb_vs_lid": (pcb, lid),
        "pcb_vs_lid_snap": (pcb, lid_snap),
    }


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
