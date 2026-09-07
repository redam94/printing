"""PARAMETERS — ESP32-DevKitC V4 case. Every dimension lives here; model.py has no literals."""
from lib.patterns.esp32 import ESP32_BOARDS

BOARD = ESP32_BOARDS["devkitc_v4"]

# --- print / material ---
WALL = 1.6                 # 4 perimeters at 0.4 nozzle
FLOOR_T = 1.6
LID_T = 1.6
CORNER_R = 3.0
BED_CHAMFER = 0.4

# --- cavity ---
CLEARANCE_XY = 1.0         # board to inner wall, per side
BOARD_Z = 4.0              # underside of PCB above the floor (pins are ~3 mm)
HEADROOM = 10.0            # above PCB top for the module can and wires
CRADLE_H = BOARD_Z + BOARD.pcb_t + 2.0
CRADLE_SLOT_DEPTH = 1.5
CRADLE_RAIL_T = 1.6
CRADLE_CLEARANCE = 0.3

INNER_L = BOARD.length + 2 * CLEARANCE_XY
INNER_W = BOARD.width + 2 * (CRADLE_RAIL_T + CLEARANCE_XY)
OUTER_L = INNER_L + 2 * WALL
OUTER_W = INNER_W + 2 * WALL
OUTER_H = FLOOR_T + BOARD_Z + BOARD.pcb_t + HEADROOM

# --- USB opening (micro-USB overmold passes through the -X wall) ---
USB_CUT_W = 12.0
USB_CUT_H = 8.0
USB_CUT_Z = FLOOR_T + BOARD_Z - 1.0      # bottom of the opening

# --- vents on the +/-Y walls ---
VENT_AREA_L = 8.0          # along each slot (vertical on the wall)
VENT_AREA_W = 30.0         # span across the slots
VENT_SLOT_W = 1.6
VENT_PITCH = 4.0
VENT_Z = OUTER_H * 0.55

# --- cable grommet on the +X wall (antenna end; sensor leads) ---
CABLE_D = 4.0
CABLE_CLEARANCE = 0.6
CABLE_Z = FLOOR_T + BOARD_Z + 6.0

# --- lid: M3 heat-set bosses in the corners, screws through the lid ---
LID_SCREW = "M3"
BOSS_H = OUTER_H - FLOOR_T            # bosses run floor to rim
BOSS_INSET = 4.6                      # boss centre from inner wall
LID_LIP_H = 3.0
LID_LIP_T = 1.2
LID_CLEARANCE = 0.25
LID_HOLE_OVERSIZE = 0.2
