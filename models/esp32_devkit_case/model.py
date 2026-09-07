"""ESP32-DevKitC V4 enclosure: body (bed side down) + screw-on lid (printed upside down).

Parts: ``body`` — open-top shell with edge-slot cradle for the hole-less dev board,
micro-USB opening, side vents, cable grommet, four M3 heat-set bosses beyond the PCB ends.
The cradle is an open ledge (no top lip): the DevKitC header bodies run to the board edge, so the board
is retained by the lid, not by a slot.
``lid`` — flat plate with drop-in lip and four M3 clearance holes.
Both parts are returned in print orientation (bed at z=0): body floor down, lid top face down.
"""
from build123d import Align, Box, Part, Plane, Pos, Rot, extrude

from lib.component import flip_to_assembly, on_bed
from lib.fasteners.clearance_hole import clearance_hole
from lib.fasteners.heat_set_boss import heat_set_boss
from lib.primitives.cable_grommet import cable_grommet
from lib.patterns.esp32 import esp32_footprint
from lib.primitives.pcb_cradle import pcb_slot_cradle
from lib.primitives.rounded_box import box_lid, rounded_box
from lib.primitives.vented_panel import vent_slots

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def _boss_locations():
    from build123d import GridLocations
    dx = P.INNER_L - 2 * P.BOSS_INSET
    dy = P.INNER_W - 2 * P.BOSS_INSET
    return list(GridLocations(dx, dy, 2, 2))


def build() -> dict[str, Part]:
    body = rounded_box(P.OUTER_L, P.OUTER_W, P.OUTER_H, wall=P.WALL, floor_t=P.FLOOR_T,
                       corner_r=P.CORNER_R, bottom_chamfer=P.BED_CHAMFER)

    cradle = pcb_slot_cradle(P.BOARD.length, P.BOARD.width, P.BOARD.pcb_t, rail_h=P.CRADLE_H, rail_t=P.CRADLE_RAIL_T,
                             slot_depth=P.CRADLE_SLOT_DEPTH, clearance=P.CRADLE_CLEARANCE, slot_z=P.BOARD_Z, top_lip=P.CRADLE_TOP_LIP)
    body = body + Pos(0, 0, P.FLOOR_T) * cradle

    bosses = [loc * heat_set_boss(P.LID_SCREW, height=P.BOSS_H) for loc in _boss_locations()]
    body = body + [Pos(0, 0, P.FLOOR_T) * b for b in bosses]

    # micro-USB opening through the -X wall
    usb = Pos(-P.OUTER_L / 2, 0, P.USB_CUT_Z) * Box(2 * P.WALL, P.USB_CUT_W, P.USB_CUT_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = body - usb

    # vents through both long (Y) walls; slots vertical so no bridging
    vents = extrude(Plane.XZ.offset(-P.OUTER_W / 2) * Pos(0, P.VENT_Z) * vent_slots(P.VENT_AREA_L, P.VENT_AREA_W, P.VENT_SLOT_W, P.VENT_PITCH, rotation=90),
                    amount=P.WALL, both=True)
    body = body - vents - vents.mirror(Plane.XZ)

    # cable grommet through the +X wall
    grommet = extrude(Plane.YZ.offset(P.OUTER_L / 2) * Pos(0, P.CABLE_Z) * cable_grommet(P.CABLE_D, P.CABLE_CLEARANCE), amount=P.WALL, both=True)
    body = body - grommet

    lid = box_lid(P.OUTER_L, P.OUTER_W, wall=P.WALL, corner_r=P.CORNER_R, thickness=P.LID_T,
                  lip_height=P.LID_LIP_H, lip_thickness=P.LID_LIP_T, clearance=P.LID_CLEARANCE, top_chamfer=P.BED_CHAMFER)
    lid = lid - [loc * Pos(0, 0, P.LID_T) * clearance_hole(P.LID_SCREW, depth=P.LID_T + P.LID_LIP_H, print_oversize=P.LID_HOLE_OVERSIZE)
                 for loc in _boss_locations()]
    lid = on_bed(Rot(180, 0, 0) * lid)   # print orientation: top face on the bed
    return {"body": body, "lid": lid}


def fit_checks(parts: dict[str, Part]) -> dict[str, tuple[Part, Part]]:
    """Assembled-state interference checks run by scripts/build.py."""
    body, lid = parts["body"], parts["lid"]
    # lid back in assembled orientation: plate on the rim, lip hanging inside
    lid_assembled = flip_to_assembly(lid, P.OUTER_H + P.LID_T)
    # PCB envelope (board + components) sitting in the cradle
    pcb = Pos(0, 0, P.FLOOR_T + P.BOARD_Z) * extrude(esp32_footprint("devkitc_v4"), amount=P.BOARD.pcb_t + P.BOARD.module_h)
    return {"lid_vs_body": (lid_assembled, body), "pcb_vs_body": (pcb, body)}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
