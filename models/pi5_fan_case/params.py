"""PARAMETERS — Raspberry Pi 5 enclosure with a lid-mounted 30 mm fan and heat-set inserts.

Every dimension lives here; model.py has no numeric literals.  Coordinates: box centred on the
origin, floor on the bed (z=0).  The Pi hole-pattern origin (lib.patterns.pi convention: +X toward
USB/Ethernet, +Y toward the GPIO header) sits at (PI_X, PI_Y).
"""
from lib.fasteners.hardware import heat_set
from lib.patterns.pi import PI_BOARDS

BOARD = PI_BOARDS["pi5"]

# --- print / material (PLA or PETG, 0.4 mm nozzle) ---
WALL = 1.6                 # 4 perimeters
FLOOR_T = 1.6
LID_T = 2.0                # thicker than the walls: it carries the fan
CORNER_R = 3.0
BED_CHAMFER = 0.4

# --- cavity: board + room for the four M3 corner bosses beside the board corners ---
CLEARANCE_XY = 6.5         # board edge to inner wall, every side (corner bosses need >= 5.6, see model docstring)
INNER_L = BOARD.length + 2 * CLEARANCE_XY      # 98
INNER_W = BOARD.width + 2 * CLEARANCE_XY       # 69
OUTER_L = INNER_L + 2 * WALL                   # 101.2
OUTER_W = INNER_W + 2 * WALL                   # 72.2

# --- Pi position: board centred in the cavity; the hole pattern is offset from the board centre ---
PI_X = -BOARD.outline_offset_x                 # -10
PI_Y = 0.0

# --- Pi standoffs: M2.5 heat-set inserts, Pi screwed down from above with M2.5 x 6 ---
PI_INSERT = "M2.5"
STANDOFF_H = 6.0           # PCB underside above the floor (SD slot body + GPIO pin stubs clear)
STANDOFF_WALL = 1.2        # boss OD 6.4: stays inside the ~6 mm component keep-out around the Pi holes
PCB_BOTTOM_Z = FLOOR_T + STANDOFF_H
PCB_TOP_Z = PCB_BOTTOM_Z + BOARD.pcb_t         # 9.2
PCB_ENVELOPE_H = 16.0      # tallest component above the PCB top (USB-A double stack) for fit checks
HEADROOM = 20.0            # PCB top to lid underside: USB-A stacks 16 tall, 10 mm fan under the lid clears the SoC by ~7.5
OUTER_H = PCB_TOP_Z + HEADROOM                 # 29.2 body height (31.2 with lid)

# --- lid screws: M3 heat-set bosses fused into the four inner corners, floor to rim ---
LID_INSERT = "M3"
BOSS_OD = heat_set(LID_INSERT).min_boss_od     # 7.2
BOSS_R = BOSS_OD / 2
BOSS_INSET = BOSS_R - 0.2  # boss centre from each inner wall; overlaps the wall 0.2 so it fuses
BOSS_H = OUTER_H - FLOOR_T
LID_LIP_H = 3.0
LID_LIP_T = 1.2
LID_CLEARANCE = 0.25
LID_HOLE_OVERSIZE = 0.2
LIP_NOTCH_R = BOSS_R + LID_CLEARANCE           # lid lip is cut back around each corner boss

# --- fan in the lid: 30 mm axial, centred over the SoC (approx. the hole-pattern centre) ---
FAN_SIZE = 30
FAN_X = PI_X
FAN_Y = PI_Y
FAN_HOLE_OVERSIZE = 0.2

# --- connector windows (lib.patterns.pi.pi5_port_cutouts) ---
PORT_CLEARANCE = 0.75      # per side around the plug envelope

# --- exhaust vents on the +Y (GPIO) wall; slots vertical so they need no bridging ---
VENT_AREA_L = 9.0          # slot length (vertical); shortened so the slots stay below the latch slits
VENT_AREA_W = 60.0         # span along the wall
VENT_SLOT_W = 1.6
VENT_PITCH = 4.0
VENT_Z = 16.5              # slots span z 12..21; latch slit starts at 22.2

# --- snap-fit lid (mechanisms.cantilever_latch + latch_window), body-side beams -----------------
# The latch beam is a strip of the +/-Y wall at the rim, freed by a 1 mm slit below and at its tip,
# so it lies flat (length along X, flexing in Y) as the component's orientation note requires.
# Hooks point OUTWARD through windows in skirt tabs hanging from the lid; press a hook to release.
LATCH_L = 12.0             # beam length along the wall (component default; ~1 % root strain in PETG)
LATCH_W = 6.0              # beam height = component width (Z here)
LATCH_T = WALL             # beam thickness = the wall it is cut from
LATCH_HOOK_D = 1.2         # hook protrusion beyond the outer wall face
LATCH_HOOK_H = 2.5         # hook length along the beam (X here)
LATCH_SLIT = 1.0           # gap freeing the beam below and at its tip
LATCH_CLEAR = 0.3          # window clearance around the hook
LATCH_ROOT_X = 30.0        # beam roots at x = +/-30, beams point toward the box centre (two per long wall)
LATCH_Z = OUTER_H - LATCH_W / 2                # strip occupies the top 6 mm of the wall
HOOK_X = LATCH_ROOT_X - LATCH_L - LATCH_HOOK_H / 2   # hook centre |x| = 16.75
HOOK_Y = INNER_W / 2 + LATCH_T + LATCH_HOOK_D / 2   # hook centre y (beyond the outer face)
LATCH_POCKET_L = LATCH_L + LATCH_HOOK_H + LATCH_SLIT   # wall opening: beam incl. hook region + tip slit (15.5)
LATCH_POCKET_H = LATCH_W + LATCH_SLIT          # wall opening: beam + slit below, open to the rim
LATCH_POCKET_MARGIN = 0.5  # cutter overshoot beyond both wall faces and above the rim

# --- snap lid skirt tabs (rigid, hang outside the wall; the hook snaps into a window in each) ---
TAB_T = 1.6                # skirt thickness
TAB_CLEAR = 0.25           # skirt inner face to outer wall face
TAB_MARGIN = 2.5           # skirt material each side of the window (X)
TAB_W = LATCH_HOOK_H + 2 * LATCH_CLEAR + 2 * TAB_MARGIN   # 8.1
TAB_BELOW = 2.0            # skirt material under the window that carries the hook
TAB_H = LATCH_W + LATCH_CLEAR + TAB_BELOW      # 8.3 below the plate underside
TAB_CHAMFER = 1.0          # lead-in on the skirt's bottom inner edge; pushes the hook inward on closing
TAB_EAR = 2.0              # how far the tab's plate-level ear overlaps the lid plate (attachment)
TAB_Y0 = OUTER_W / 2 + TAB_CLEAR               # skirt inner face
TAB_Y1 = TAB_Y0 + TAB_T                        # skirt outer face
LIP_GAP_MARGIN = 1.0       # lip removed over the beam span (+ margin) so the deflected beam clears it
LIP_GAP_L = LATCH_POCKET_L + 2 * LIP_GAP_MARGIN
LIP_GAP_X = LATCH_ROOT_X - LATCH_POCKET_L / 2  # centre |x| of the lip gap
LIP_GAP_W = 2 * (LID_LIP_T + LID_CLEARANCE + LIP_GAP_MARGIN)

# --- stick-on rubber feet on the underside ---
FOOT_D = 10.0
FOOT_INSET = 12.0          # foot centre from the outer edges (clear of the corner bosses)
