---
id: file-5725bdb05c
target: "idea:ring_clip_5_5"
created: 2026-09-11
source: file
url: ""
title: clip
author: ""
license: ""
why: "how a printed squeeze/snap ring clip is dimensioned: ring bore and wall, living-hinge neck widths and their Z extent, push-arm width and angle, side spring thickness, rail thickness; and how it prints (flat, 7.2 mm tall)"
files: [clip.stl]
images: [file-5725bdb05c-clip-render.png, file-5725bdb05c-sections.png, file-5725bdb05c-top.png]
reading_model: haiku subagent
tags: [ring clip, squeeze snap, living hinge, compliant mechanism, cantilever, return spring, gripper, fdm printable]
---

## Page
local mesh clip.stl

## Measurements
`clip.stl` — 3752 faces, watertight, 1 body(ies)

| metric | value |
|---|---|
| bbox X x Y x Z (mm) | 49.8 x 15.21 x 7.2 |
| depth along Z (print height as filed) | 7.2 mm |
| volume | 1.7 cm³ |
| min wall (inward ray) | 0.21 mm (p05 0.55) |
| living hinge / neck width in plane (splits the section) | 0.46 mm |
| beam width in plane (first members holding ≥1 % of area after the hinge) | 0.6 mm |
| thinnest member in plane | 0.46 mm |
| thickest member in plane (largest inscribed disc: hub / block) | 3.0 mm |
| overhang > 45° | 0.2% of surface |
| bed contact | 232.6 mm² |

| slice z | islands | area mm² | hinge | beam | thickest | extent |
|---|---|---|---|---|---|---|
| -2.52 | 1 | 231.9 | 0.46 | 0.6 | 3.0 | 49.8 x 15.2 |
| -1.08 | 5 | 227.5 | 0.55 | 1.2 | 3.0 | 49.8 x 15.2 |
| 0.0 | 5 | 227.5 | 0.55 | 1.2 | 3.0 | 49.8 x 15.2 |
| 1.08 | 5 | 227.5 | 0.55 | 1.2 | 3.0 | 49.8 x 15.2 |
| 2.52 | 1 | 231.9 | 0.46 | 0.6 | 3.0 | 49.8 x 15.2 |

member width histogram (mid slice; % of area first appearing at each width): 0.6 mm +4.85%, 1.2 mm +7.91%, 1.5 mm +20.71%, 2 mm +2.85%

All member widths are measured IN THE SLICE PLANE (XY); the Z depth is the row above. hinge = thinnest neck joining two pieces of the section (a living hinge); beam = first width after it where members holding ≥1 % of the area appear.
Members are read per Z slice as the mesh sits: re-orient (or re-run `measure` on a rotated copy) if the flexing members do not lie in XY.

### Section probes (trimesh, 2026-09-11; mesh centred on z=0, z in [-3.6, 3.6])
Topology by Z: one island for |z| > 1.7 (top and bottom 1.9 mm), five islands for |z| < 1.7
(frame, left arm, right arm, left ring half, right ring half). Every living-hinge neck therefore
exists only as two 1.9 mm plates at the faces with a 3.4 mm gap between them.

| member | measured |
|---|---|
| top rail (mounting bar) | 48.35 x 3.0 mm (y 7.35..10.35), full 7.2 depth, rounded ends |
| side strips (return springs) | 0.55 mm thick, from the rail down ~10.7 mm to the posts, at x = ±23.9 |
| posts (arm anchors) | round, Ø ~1.9, centred ~(±23.9, -3.9) |
| push arms | 1.54 mm wide, ~15.9 mm long, from (±20.9, -3.5) to (±5.4, +0.9): ~15 deg to X, rounded ends |
| arm-to-post neck | 0.47 mm wide, ~2.1 mm long, at y ≈ -3.2 |
| arm-to-ring neck | 0.47 mm wide, ~1.8 mm long, at y ≈ +0.6 (lower outboard of the ring) |
| ring | C-ring centred (0, 2.65): bore Ø5.05, wall 1.0, outer Ø7.2 |
| ring top hinge | 0.46 mm wide neck at y 5.69..6.15 joining the two halves (faces only) |
| ring bottom gap | 0.48 mm slit at x = ±0.24, open toward -Y (the rod enters here) |
| ring to rail | not connected: 1.2 mm clear between ring top (6.25) and rail (7.35) |

## Reading
**Subject:** Parametric C-ring clip for grasping cylindrical rods via push-arm release

**Mechanism:** cantilever snap with living-hinge compliant ring and return springs

**Principle:** Two symmetric push arms flex downward to mechanically separate the C-ring halves via 0.46–0.47 mm living hinges, allowing a rod to enter the 5.05 mm bore. Side strips (0.55 mm thick spring beams) anchored at the top rail act as return springs, snapping the ring closed when the arms are released. The ring halves remain in contact at the top rail and open downward around a central gap, storing elastic energy in the arm deflection and spring compression.

**Key dimensions:**
- C-ring bore diameter 5.05 mm (measured)
- C-ring wall thickness 1.0 mm (measured)
- C-ring outer diameter 7.2 mm (measured)
- living hinge width (arm-to-ring and arm-to-post) 0.46–0.47 mm (measured)
- living hinge Z extent 1.9 mm at top and bottom faces (measured)
- push arm width 1.54 mm (measured)
- push arm length ~15.9 mm (measured)
- push arm angle to X axis ~15 degrees (measured)
- side spring thickness 0.55 mm (measured)
- side spring span ~10.7 mm from rail to post (measured)
- top rail 48.35 x 3.0 mm (measured)
- full Z depth (print height) 7.2 mm (measured)
- minimum wall (inward ray) 0.21 mm p05 (measured)

**Features to borrow:**
- split C-ring with central gap for rod entry
- thin living-hinge necks (0.46 mm) joining ring halves only at faces, leaving 3.4 mm hollow gap through the middle
- symmetric push arms with ~15° angle to reduce horizontal footprint
- spring return strips anchored at rail, providing soft closing without external springs
- nearly flat profile (7.2 mm total depth) optimized for FDM printing
- round post anchors at arm-to-post hinges reducing stress concentration

**Print notes:** Prints flat on bed, 7.2 mm tall (Z depth). No page text or material specifications provided; mesh sits centred on z=0 with its 7.2 mm depth along Z axis. Minimal overhang (0.2% of surface > 45°). Bed contact area 232.6 mm². No supports required for standard orientations.

**build123d hints:**
- top rail: sketch 48.35 x 3.0 mm rectangle with rounded ends, extrude full 7.2 mm depth
- side springs: sketch thin (0.55 mm) vertical strips from rail down ~10.7 mm to post anchors at x ≈ ±23.9, extrude full depth
- post anchors: sketch circles Ø ~1.9 mm centred ~(±23.9, -3.9), extrude full depth or use polar pattern
- push arms: sketch from (±20.9, -3.5) to (±5.4, +0.9), 1.54 mm wide, ~15° angle to X, extrude full 7.2 mm, fillet ends to ~1 mm radius
- arm-to-post hinge: sketch neck 0.47 mm wide at y ≈ -3.2, reduce Z extent to ±1.9 mm (faces only) via local cut or layer-dependent taper
- C-ring halves: sketch bore Ø 5.05 mm with 1.0 mm wall, split along y=0, position left/right of centre
- arm-to-ring hinge: sketch 0.47 mm neck at y ≈ +0.6 joining arms to ring at Z faces only
- ring top hinge: sketch 0.46 mm wide neck at y 5.69–6.15 joining ring halves; constrain to top and bottom 1.9 mm layers only
- ring bottom gap: model 0.48 mm slit at x = ±0.24, open toward -Y for rod entry
- consider mirror() for arms and springs after defining one side to maintain symmetry

**Library map:**
- mechanisms.parallel_flexure: the side spring strips (0.55 mm thick, 2 parallel beams acting as return springs) resemble a 2-beam flexure stage, but constrained to linear motion in Z (arm deflection) rather than Y translation
- mechanisms.cantilever_latch: the push arms function as cantilevers, but with a snap-open rather than hook-latch geometry, and the flexure direction is vertical (Z bending) not horizontal
- gap: mechanisms.squeeze_ring_clip (proposed) — a parametric ring clip combining living-hinge ring halves, cantilever push arms, and spring return, for grasping cylindrical objects via compliant release

## Log
- 2026-09-11 filed from file: how a printed squeeze/snap ring clip is dimensioned: ring bore and wall, living-hinge neck widths and their Z extent, push-arm width and angle, side spring thickness, rail thickness; and how it prints (flat, 7.2 mm tall)
- 2026-09-11 attached clip.stl: thinnest member 0.46 mm, min wall 0.21 mm
- 2026-09-11 reading by haiku subagent
- 2026-09-11 bore 5.05 (5.5-0.45), wall 1.0, necks 0.5 x 2.0 as 1.9 mm plates, arms 1.6 wide at 16 deg, strips 0.6, rail 3.0, depth 7.2 became the defaults of mechanisms.split_ring_clip and models/ring_clip_5_5
