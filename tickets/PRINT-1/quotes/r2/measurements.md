# couch_remote_caddy — measurements

Built 2026-09-17 11:28 (build 20260917-112801). Every number in millimetres unless marked.

Couch-arm remote caddy for three TV / streaming remotes (design request PRINT-1).

Part: ``caddy`` — one piece that sits over a padded couch arm with no screws or adhesive:
a saddle plate across the arm top, a short leg down the seat side, and a pocket block hanging down
the outboard side. The block holds three open-top pockets sized for the requested remotes
(45 x 20, 40 x 18 and 38 x 15 mm, plus 2 mm clearance) and as deep as 40% of each remote, so most of
every remote stays in reach. The remotes' weight pulls the block against the arm; the
seat-side leg stops the caddy sliding off.

Fabric protection: every edge that runs along the arm is rounded (EDGE_R) and the underside of the
saddle has four recesses for stick-on felt or rubber dots (PAD_D).

Print orientation: upside down, the saddle's top face and the pocket rims on the bed. The pocket
floors then bridge across each pocket's short side (at most 22 mm); everything else is vertical.
No supports.

Assumptions: the arm is 140 mm wide at the top (re-measured by the requester for quote r2) and
square-edged enough for a flat saddle; "25 thick" is read as the padding, so the saddle leaves 4 mm
of play across the arm.
The caddy follows the arm along 140 mm.

## Parts

| part | X x Y x Z (mm) | volume (cm³) | est. mass (g) | thinnest wall (mm) | print mode |
|---|---|---|---|---|---|
| caddy | 174.8 x 140.2 x 74.4 | 207.32 | 178.7 | 1.61 | normal |

Plate extent 174.8 x 140.2 x 74.4 mm on the Snapmaker U1 (fits the bed)

## Dimensions and choices

| parameter | value | meaning |
|---|---|---|
| ARM_W | 140.0 | mm, arm width across the top (PRINT-1 r2: requester re-measured, was 150) |
| ARM_CLEARANCE | 4.0 | mm, added to ARM_W so the saddle slides over padded fabric without dragging |
| ARM_SPAN | 144.0 | mm, inside width of the saddle |
| ARM_ENVELOPE_H | 200.0 | mm, how far down the arm is modelled for the fit check (the sides of any couch arm) |
| REMOTES | ((45.0, 20.0, 180.0), (40.0, 18.0, 150.0), (38.0, 15.0, 140.0)) |  |
| POCKET_DEPTH_FRAC | 0.4 | pocket depth as a fraction of each remote's length (PRINT-1 r2: was 0.5) |
| POCKET_CLEARANCE | 2.0 | mm, added to each remote's width and thickness (1 mm per side, drops in one-handed) |
| POCKET_CORNER_R | 3.0 | mm, vertical corner radius inside each pocket |
| POCKET_LEAD_IN | 1.2 | mm, 45 deg chamfer at each pocket rim |
| POCKET_WEB | 2.4 | mm, wall between pockets (6 perimeters) |
| POCKETS | ((45.0, 20.0, 72.0), (40.0, 18.0, 60.0), (38.0, 15.0, 56.0)) | (x, y, depth) for pocket_array |
| PLATE_T | 3.2 | mm, saddle plate lying on the arm (8 perimeters' worth of stiffness across the span) |
| INNER_LEG_T | 3.2 | mm, leg down the seat side |
| INNER_LEG_H | 35.0 | mm, leg length below the arm top (stops the caddy sliding off outboard) |
| BLOCK_ARM_WALL | 3.2 | mm, block wall against the outboard side of the arm (it is the outer leg) |
| BLOCK_OUTER_WALL | 2.4 | mm, block wall facing the room |
| BLOCK_END_WALL | 3.2 | mm, block walls at both ends of the pocket row |
| BLOCK_FLOOR_T | 2.4 | mm, pocket floors (bridges in print orientation) |
| EDGE_R | 1.5 | mm, radius on every edge running along the arm except the saddle top: nothing sharp touches the fabric |
| BED_CHAMFER | 0.4 | mm, elephant-foot chamfer round the saddle top (the bed face) |
| PAD_D | 12.0 | mm, stick-on felt / rubber dot diameter |
| PAD_DEPTH | 0.8 | mm, locating recess depth |
| PAD_INSET | 15.0 | mm, pad centre distance from the saddle's inner edges and ends |

## Fit checks

- arm_vs_caddy: clear

## Proven pieces it is built from

- primitives.pocket_array v1.0.0: Negative (subtract me): row of blind rounded-rectangle pockets, each its own size and depth, with chamfered lead-ins; rims at z=0, pockets extend down. (printed in: not yet test-printed)
- primitives.rubber_foot_recess v1.0.0: Negative (subtract me) shallow recess to locate a stick-on rubber foot; top face at z=0, extends down. (printed in: PLA)
