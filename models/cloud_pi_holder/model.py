"""Cloud-shaped Raspberry Pi 5 enclosure: ``body`` (floor on the bed) + ``lid`` (printed upside down).

The plan view is a cloud (lib.form.cloud_outline): flat edge on the -Y power side, straight sides
at +X (Ethernet) and -X (SD end), round lobes along the +Y GPIO edge.  Walls are vertical; the
body's outer skin carries a soft noise texture (lib.form.textured) and the lid's top edge is
chamfered so the silhouette reads soft from every side.

Body: four M2.5 heat-set standoffs at the Pi 5 hole pattern (Pi screwed down from above), vent
slots in the floor under the board, four rubber-foot recesses, and three windows cut with
lib.patterns.pi.pi5_port_cutouts: USB-C (power, -Y flat wall), Ethernet (+X wall) and the 40-way
GPIO ribbon (+Y lobed wall).  The ribbon opening is a NOTCH from the ribbon slot height up through
the rim, closed by the lid: the IDC socket sits inside the lobes and the assembled cable drops into
the notch before the lid goes on (a closed window that high would leave < 1 mm of wall above it).
micro-HDMI, USB-A and the microSD slot are CLOSED (add "hdmi0"/"hdmi1" to POWER_PORTS,
"usb_a_lower"/"usb_a_upper" to USB_PORTS, or an "sd" cut, in params.py).
Lid: cloud plate with a 3 mm lip dropping inside the walls (0.25 mm slip fit per side), lip
interrupted over the ribbon notch, vent slots over the SoC, 1.5 mm top chamfer; no screws.

Hardware: Raspberry Pi 5 (bare or with a heatsink <= 20 mm; the Active Cooler at 13.7 fits),
4x M2.5 brass heat-set inserts, 4x M2.5 x 6 screws, 4x 10 mm stick-on rubber feet (optional),
a 40-way IDC ribbon cable on the GPIO header exiting through the +Y window.

Pipeline: the body is built exactly in B-rep (outline, walls, bosses, windows, vents, feet) and
handed to lib.form.textured LAST; the exterior-only, horizontal displacement leaves the bed face,
the rim height, the cavity, bosses, holes and windows untouched, so the lid fit and the Pi fit are
the B-rep ones.  The body exports STL / 3MF (no STEP); the lid is B-rep.

Print orientation: body floor on the bed, lid top face on the bed (returned already flipped).
Windows are bridged by the wall above them (<= 18 mm spans).  Material: PLA or PETG.

Assumptions (user unavailable): headless use, so only power, Ethernet and GPIO are open; a
+Y clearance of 14 mm so the IDC socket and its strain relief sit inside the lobes; standoffs use
a 1.2 mm insert wall (OD 6.4) to respect the component keep-out around the Pi holes.
"""
from build123d import Align, Axis, Box, Part, Plane, Pos, Rot, chamfer, extrude, offset

from lib.component import flip_to_assembly, locations_of, on_bed
from lib.fasteners.heat_set_boss import heat_set_boss
from lib.form.mesh import textured
from lib.form.outline import cloud_outline
from lib.patterns.corners import corner_holes
from lib.patterns.pi import pi5_mount, pi5_port_cutouts, pi_board_outline
from lib.primitives.feet import rubber_foot_recess
from lib.primitives.vented_panel import vent_slots

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def _outline():
    """Cloud silhouette in world XY (flat edge at -Y on the power wall, lobes toward +Y)."""
    return Pos(P.CLOUD_CX, P.CLOUD_CY) * cloud_outline(P.CLOUD_LEN, P.CLOUD_W, lobes=P.CLOUD_LOBES, lobe_r=P.CLOUD_LOBE_R,
                                                       overlap=P.CLOUD_OVERLAP, smooth_r=P.CLOUD_SMOOTH_R)


def _pi_locations():
    return [Pos(P.PI_X, P.PI_Y) * loc for loc in locations_of(pi5_mount())]


def _through_wall(sketch_on_plane):
    return extrude(sketch_on_plane, amount=P.WALL, both=True)


def _vents():
    return vent_slots(P.VENT_AREA_L, P.VENT_AREA_W, P.VENT_SLOT_W, P.VENT_PITCH)


def _ribbon_slot():
    """Bare-ribbon slot from the library (sketch frame: x = lib X, y = height above PCB top)."""
    return pi5_port_cutouts("gpio", clearance=P.PORT_CLEARANCE, plug_envelope=False, ports=P.GPIO_PORTS)


def _gpio_notch(y0: float, y1: float, z_top: float) -> Part:
    """Box from the ribbon slot's bottom edge up through ``z_top``, spanning y0..y1 (world frame)."""
    bb = _ribbon_slot().bounding_box()
    z0 = P.PCB_TOP_Z + bb.min.Y
    return Pos(P.PI_X + (bb.min.X + bb.max.X) / 2, y0, z0) * Box(bb.size.X, y1 - y0, z_top - z0, align=(Align.CENTER, Align.MIN, Align.MIN))


def body_brep() -> Part:
    """The exact B-rep body before texturing."""
    outline = _outline()
    inner = offset(outline, amount=-P.WALL)
    shell = extrude(outline, amount=P.OUTER_H) - Pos(0, 0, P.FLOOR_T) * extrude(inner, amount=P.OUTER_H)
    if P.BED_CHAMFER > 0:
        shell = chamfer(shell.faces().sort_by(Axis.Z)[0].outer_wire().edges(), P.BED_CHAMFER)

    standoffs = [loc * heat_set_boss(P.PI_INSERT, height=P.STANDOFF_H, wall=P.STANDOFF_WALL) for loc in _pi_locations()]
    body = shell + [Pos(0, 0, P.FLOOR_T) * b for b in standoffs]

    # windows: USB-C through the flat -Y wall, Ethernet through the +X wall; GPIO ribbon = notch open to the rim
    power = Plane.XZ.offset(-P.FLAT_WALL_Y) * Pos(P.PI_X, P.PCB_TOP_Z) * pi5_port_cutouts("power", clearance=P.PORT_CLEARANCE, ports=P.POWER_PORTS)
    usb = Plane.YZ.offset(P.USB_WALL_X) * Pos(P.PI_Y, P.PCB_TOP_Z) * pi5_port_cutouts("usb", clearance=P.PORT_CLEARANCE, ports=P.USB_PORTS)
    body = body - [_through_wall(power), _through_wall(usb), _gpio_notch(P.GPIO_NOTCH_Y0, P.GPIO_NOTCH_Y1, P.OUTER_H + P.NOTCH_OVERSHOOT)]

    # floor vents under the board, rubber-foot recesses in the underside
    body = body - extrude(Pos(P.VENT_X, P.VENT_Y) * _vents(), amount=P.FLOOR_T)
    feet = locations_of(Pos(P.FOOT_CENTER_X, 0) * corner_holes(P.FOOT_SPAN_L, P.FOOT_SPAN_W, inset=P.FOOT_INSET))
    body = body - [loc * Rot(180, 0, 0) * rubber_foot_recess(P.FOOT_D) for loc in feet]
    return body


def lid_brep() -> Part:
    """Lid as assembled (plate z in [0, LID_T], lip hanging below z=0)."""
    outline = _outline()
    plate = extrude(outline, amount=P.LID_T)
    if P.LID_TOP_CHAMFER > 0:
        plate = chamfer(plate.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), P.LID_TOP_CHAMFER)
    lip_outer = offset(outline, amount=-(P.WALL + P.LID_CLEARANCE))
    lip_inner = offset(outline, amount=-(P.WALL + P.LID_CLEARANCE + P.LID_LIP_T))
    lip = extrude(lip_outer - lip_inner, amount=-P.LID_LIP_H)
    # lip interrupted over the ribbon notch (lid frame: lip spans z -LID_LIP_H..0), so the cable passes under the plate
    bb = _ribbon_slot().bounding_box()
    lip_gap = Pos(P.PI_X + (bb.min.X + bb.max.X) / 2, P.GPIO_NOTCH_Y0 - P.LID_LIP_T - P.LID_CLEARANCE - P.LIP_NOTCH_MARGIN, -P.LID_LIP_H - P.NOTCH_OVERSHOOT) * Box(
        bb.size.X, P.GPIO_NOTCH_Y1 - P.GPIO_NOTCH_Y0, P.LID_LIP_H + P.NOTCH_OVERSHOOT, align=(Align.CENTER, Align.MIN, Align.MIN))
    lid = plate + (lip - lip_gap)
    return lid - extrude(Pos(P.VENT_X, P.VENT_Y) * _vents(), amount=P.LID_T)


def build() -> dict:
    body = textured(body_brep(), amplitude=P.TEXTURE_AMP, scale=P.TEXTURE_SCALE, kind="noise", mask="exterior",
                    seed=P.TEXTURE_SEED, edge_length=P.TEXTURE_EDGE)
    lid = on_bed(Rot(180, 0, 0) * lid_brep())   # print orientation: top face on the bed
    return {"body": on_bed(body), "lid": lid}


def fit_checks(parts: dict) -> dict:
    """Lid back on the rim; Pi envelope and the IDC socket must clear body and lid."""
    lid = flip_to_assembly(parts["lid"], P.OUTER_H + P.LID_T)
    pcb = Pos(P.PI_X, P.PI_Y, P.PCB_BOTTOM_Z) * extrude(pi_board_outline("pi5"), amount=P.BOARD.pcb_t + P.PCB_ENVELOPE_H)
    idc = Pos(P.PI_X, P.PI_Y + P.BOARD.width / 2 + P.IDC_OVERHANG, P.PCB_TOP_Z) * Box(
        P.IDC_W, P.IDC_D, P.IDC_H, align=(Align.CENTER, Align.MAX, Align.MIN))
    return {
        "lid_vs_body": (lid, parts["body"]),
        "pcb_vs_body": (pcb, parts["body"]),
        "pcb_vs_lid": (pcb, lid),
        "idc_vs_body": (idc, parts["body"]),
        "idc_vs_lid": (idc, lid),
    }


if __name__ == "__main__":
    for name, part in build().items():
        print(name, getattr(part, "bounds", None) or part.bounding_box().size)
