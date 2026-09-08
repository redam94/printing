"""PARAMETERS — cloud-shaped Raspberry Pi 5 enclosure (body + lid) with USB-C, Ethernet and GPIO ribbon windows.

Coordinates: the Pi hole-pattern origin (lib.patterns.pi convention: +X toward USB/Ethernet, +Y
toward the GPIO header) is the world origin; floor on the bed (z=0).  The cloud outline
(lib.form.cloud_outline) is used in its native frame: flat edge at -Y (the USB-C / power wall),
lobes bulging toward +Y (the GPIO edge), straight sides at +X (Ethernet) and -X (SD end).
"""
from lib.fasteners.hardware import heat_set
from lib.patterns.pi import PI_BOARDS

BOARD = PI_BOARDS["pi5"]

# --- print / material (PLA or PETG, 0.4 mm nozzle) ---
WALL = 2.0                 # 5 perimeters: the outer skin carries a +/-0.35 mm texture
FLOOR_T = 2.0
LID_T = 2.0
BED_CHAMFER = 0.4          # elephant-foot chamfer on the body's bed edge

# --- cavity: board + room for plugs; the walls sit close so the windows are short recesses ---
CLEAR_SD = 6.0             # board SD end (-X) to inner wall
CLEAR_USB = 3.0            # board USB/Ethernet end (+X) to inner wall (connectors protrude ~2.5)
CLEAR_POWER = 3.5          # board -Y edge to the flat wall's inner face (USB-C body protrudes ~1.5)
CLEAR_GPIO = 14.0          # board +Y edge to the lobe valleys' inner face (IDC socket overhangs the edge ~3)
BOARD_X0 = BOARD.outline_offset_x - BOARD.length / 2         # -32.5 (board centre is +10 from the hole pattern)
BOARD_X1 = BOARD_X0 + BOARD.length                           # 52.5
INNER_X0 = BOARD_X0 - CLEAR_SD                                # -38.5
INNER_X1 = BOARD_X1 + CLEAR_USB                               # 55.5
INNER_Y0 = -BOARD.width / 2 - CLEAR_POWER                     # -31.5 (flat wall inner face)

# --- cloud silhouette: native frame, then shifted so the flat edge and sides land on the walls above ---
CLOUD_LEN = INNER_X1 - INNER_X0 + 2 * WALL                    # 98: X extent
CLOUD_LOBE_R = 18.0        # largest lobe radius
CLOUD_LOBES = (0.72, 0.9, 1.0, 0.85, 0.68)
CLOUD_OVERLAP = 0.35       # lobe centres sink this fraction of their radius below the base top
CLOUD_SMOOTH_R = 3.0       # fillet where lobes meet
CLOUD_VALLEY_DROP = (1.0 - CLOUD_OVERLAP) * CLOUD_LOBE_R      # lobe top to base top (11.7): valleys sit ~ at the base top
CLOUD_W = (BOARD.width / 2 + CLEAR_GPIO + WALL) + CLOUD_VALLEY_DROP - INNER_Y0 + WALL   # ~89: flat edge to tallest lobe
CLOUD_CX = (INNER_X0 + INNER_X1) / 2                          # 8.5
CLOUD_CY = INNER_Y0 - WALL + CLOUD_W / 2                      # centre so the flat edge outer face is at INNER_Y0 - WALL
FLAT_WALL_Y = INNER_Y0 - WALL / 2                             # centre plane of the -Y wall (for the port cutter)
GPIO_WALL_Y = BOARD.width / 2 + CLEAR_GPIO + WALL / 2         # centre plane of the lobed +Y wall at the valleys
USB_WALL_X = INNER_X1 + WALL / 2                              # centre plane of the +X wall

# --- Pi: hole pattern at the origin; M2.5 heat-set standoffs, Pi screwed down from above ---
PI_X = 0.0
PI_Y = 0.0
PI_INSERT = "M2.5"
STANDOFF_H = 6.0           # PCB underside above the floor
STANDOFF_WALL = 1.2        # boss OD 6.4 respects the component keep-out around the Pi holes
PCB_BOTTOM_Z = FLOOR_T + STANDOFF_H                           # 8.0
PCB_TOP_Z = PCB_BOTTOM_Z + BOARD.pcb_t                        # 9.6
PCB_ENVELOPE_H = 16.0      # tallest component above the PCB (USB-A stack) for the fit check
HEADROOM = 20.0            # PCB top to lid underside: USB-A stack 16, IDC socket + strain relief 19
OUTER_H = PCB_TOP_Z + HEADROOM                                # 29.6 body height (31.6 with lid)
BOSS_OD = heat_set(PI_INSERT).hole_d + 2 * STANDOFF_WALL

# --- windows (lib.patterns.pi.pi5_port_cutouts): only these three; HDMI, USB-A and SD stay closed ---
PORT_CLEARANCE = 0.75      # per side around the plug envelope
POWER_PORTS = ["usb_c"]    # -Y flat wall
USB_PORTS = ["ethernet"]   # +X wall
GPIO_PORTS = ["gpio_ribbon"]   # +Y lobed wall: the ribbon slot (plug_envelope=False) opened up to the rim as a notch
GPIO_NOTCH_Y0 = BOARD.width / 2 + CLEAR_GPIO - 1.0   # notch cutter starts just inside the lobed wall's inner face (valleys)
GPIO_NOTCH_Y1 = GPIO_NOTCH_Y0 + 2 * CLOUD_LOBE_R + WALL + 4.0   # and runs out past the lobe peaks
NOTCH_OVERSHOOT = 1.0      # cutter extends above the rim
LIP_NOTCH_MARGIN = 1.0     # lid lip removed over the notch width, from this far inboard of the lip out to the wall
IDC_W = 58.0               # IDC socket envelope for the fit check (x), centred on the header
IDC_D = 9.0                # socket depth (y), overhanging the board edge by ~3
IDC_OVERHANG = 3.0
IDC_H = 19.0               # socket + strain relief above PCB top

# --- lid: drops inside the walls (lib.primitives.box_lid style lip), printed upside down ---
LID_LIP_H = 3.0
LID_LIP_T = 1.2
LID_CLEARANCE = 0.25       # per side between lip and inner wall (slip fit)
LID_TOP_CHAMFER = 1.0      # softens the top edge (leaves a 1.0 mm edge on the 2.0 plate); 45 deg prints fine inverted

# --- vents: slots through the lid over the SoC and through the floor under the board (convection) ---
VENT_AREA_L = 36.0         # slot length direction (X)
VENT_AREA_W = 28.0         # span across (Y)
VENT_SLOT_W = 1.6
VENT_PITCH = 4.0
VENT_X = 10.0              # centred under / over the board, between the standoffs
VENT_Y = 0.0

# --- rubber feet under the floor ---
FOOT_D = 10.0
FOOT_SPAN_L = 70.0
FOOT_SPAN_W = 50.0
FOOT_INSET = 6.0
FOOT_CENTER_X = 10.0

# --- surface texture (lib.form.textured, mesh branch): soft cloud skin on the body's outer walls ---
TEXTURE_AMP = 0.35         # mm, horizontal only; <= 0.4 prints clean at 0.4 mm nozzle
TEXTURE_SCALE = 7.0        # mm feature size
TEXTURE_SEED = 3
TEXTURE_EDGE = 2.0         # mesh refinement before displacing (7 mm features need ~3 samples; 1.0 makes a 20 MB STL)
