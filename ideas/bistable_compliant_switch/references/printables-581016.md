---
id: printables-581016
target: "idea:bistable_compliant_switch"
created: 2026-09-10
source: printables
url: "https://www.printables.com/model/581016-bistable-compliant-switch"
title: Bistable Compliant Switch
author: BYU CMR
license: Creative Commons — Attribution  — Noncommercial
why: how thick and how angled are the beams of a printed bistable toggle, and which way it prints
files: [Bistable_Switch.STL]
images: [printables-581016-Bistable_Switch-render.png, printables-581016-img1.jpg, printables-581016-img2.jpg, printables-581016-img3.jpg]
reading_model: haiku subagent
tags: [bistable, compliant-mechanism, living-hinge, four-bar, snap-through, monolithic, toggle-switch, contact-stop, spring-action, switch]
---

## Page
This bistable switch is an example of a compliant mechanism with a four-bar mechanism pseudo-rigid-body model.
190 likes · 18 makes · 1870 downloads  ·  published 2023-09-29
tags: switch, spring, lightswitch, compliant, livinghinge, bending, bistable, byucmr, byu, compliantmechanim, Engineering
files on the page (download login):
- BistableSwitch.dxf (27 KB)
- Bistable_Switch.STL (86 KB)
images:
- https://media.printables.com/media/prints/581016/images/4638314_ec7afbf9-9c3b-4219-a5f1-060e13533d96/swi3.jpg
- https://media.printables.com/media/prints/581016/images/4638315_ea5898f6-5a05-4849-9510-0ed717baec58/swi2.jpg
- https://media.printables.com/media/prints/581016/images/4638316_82b40c97-8302-4823-8ba7-2be3cf806e3c/swi1.jpg

### Description
Summary

This bistable switch is an example of a compliant mechanism with a four-bar mechanism pseudo-rigid-body model. A contact force is created by causing the contacts to connect before the second stable equilibrium position is reached. Living hinges are used at the other joints. This mechanism could be used as a fully compliant electrical switch, or for other applications, such as on cabinet door hinges.

 

Print Settings

This can be 3D printed or milled. For ideal use, milling or cutting with polypropylene results in the best performance.

If 3D printing, the filament material you use and its fatigue/flex properties will determine the number of cycles the mechanism can handle.

 

Learn More

This design was developed by the Compliant Mechanisms Research Group (CMR) from Brigham Young University (BYU). Follow us at @byucmr on Instagram or visit the BYU Compliant Mechanisms Research (CMR) website to learn more about compliant mechanisms.

 

Lesson Plan and Activity

What is a Bistable Mechanism?

A Bistable Mechanism has two stable equilibrium positions in which it can rest. A common example of a bistable device is a light switch (Figure 2) which has two stable positions, resting in either the "on" or "off" position, but not in between. The mechanism remains in one of the stable positions until an external force is exerted on it. A simple way to illustrate the stability of a bistable system is by using the "ball-on-the-hill" analogy (Figure 3). The ball rests in either of the two low points on the potential energy graph.

 

Why use compliant mechanisms for bistable systems?

Just like any mechanism, a compliant mechanism also transfers or transforms motions, force, or energy. However, unlike rigid-linked mechanisms, it uses its own flexible members to gain mobility by storing strain energy internally, similar to potential energy stored in a deflected spring.

REDUCE PART COUNT AND COST Using compliant mechanisms can be extremely advantageous because it reduces the number of parts required. This can make it easier, faster, and more affordable to manufacture and assemble. In the case of this compliant switch, you only need a single part to perform the task while a traditional switch may require multiple pieces such as springs, hinges, pins, etc. The compliant switch uses its own members to store energy to simulate the springs found in other switches.

REDUCE WEAR Because of the reduced part count, there are also fewer movable joints which reduce wear and need for lubrication.

INCREASE PRECISION It can also increase precision because backlash is reduced or even eliminated since there is no "play" or "wobble" between separate parts.

REDUCE WEIGHT By minimizing how many separate parts are needed in the design, the overall weight can be decreased significantly. This is very beneficial for aerospace and many other applications where weight is an issue. It can also help companies save money on shipping costs on consumer products.

SIZE REDUCTION Compliant mechanisms can easily be scaled down to miniature versions. It is impractical to create microscopic rigid body mechanisms that include pins and multiple assembly parts, because it is difficult to manufacture and assemble on such a small scale. it is more feasible to use compliant mechanisms in micro mechanisms because of the reduction of parts and joints as it reduces the need for assembly and separate part manufacturing.

 

Activity #1 - Build your own compliant bistable mechanism
…(truncated)

## Measurements
`Bistable_Switch.STL` — 1776 faces, watertight, 1 body(ies)

| metric | value |
|---|---|
| bbox X x Y x Z (mm) | 109.45 x 50.02 x 8.89 |
| depth along Z (print height as filed) | 8.89 mm |
| volume | 20.0 cm³ |
| min wall (inward ray) | 0.49 mm (p05 5.7) |
| living hinge / neck width in plane (splits the section) | 0.51 mm |
| beam width in plane (first members holding ≥1 % of area after the hinge) | 8.0 mm |
| thinnest member in plane | 0.51 mm |
| thickest member in plane (largest inscribed disc: hub / block) | 15.5 mm |
| overhang > 45° | 0.6% of surface |
| bed contact | 2202.5 mm² |

| slice z | islands | area mm² | hinge | beam | thickest | extent |
|---|---|---|---|---|---|---|
| 1.33 | 1 | 2257.8 | 0.51 | 8.0 | 15.5 | 109.5 x 50 |
| 3.11 | 1 | 2257.8 | 0.51 | 8.0 | 15.5 | 109.5 x 50 |
| 4.45 | 1 | 2257.8 | 0.51 | 8.0 | 15.5 | 109.5 x 50 |
| 5.78 | 1 | 2257.8 | 0.51 | 8.0 | 15.5 | 109.5 x 50 |
| 7.56 | 1 | 2257.8 | 0.51 | 8.0 | 15.5 | 109.5 x 50 |

member width histogram (mid slice; % of area first appearing at each width): 8 mm +12.22%, 10 mm +35.47%

All member widths are measured IN THE SLICE PLANE (XY); the Z depth is the row above. hinge = thinnest neck joining two pieces of the section (a living hinge); beam = first width after it where members holding ≥1 % of the area appear.
Members are read per Z slice as the mesh sits: re-orient (or re-run `measure` on a rotated copy) if the flexing members do not lie in XY.

## Reading
**Subject:** Monolithic bistable compliant switch with four-bar pseudo-rigid-body mechanism

**Mechanism:** bistable snap-through beam pair with living hinges and contact stops

**Principle:** Two curved support beams anchored to a rectangular base store elastic strain energy while a thin living hinge (0.51 mm) at their junction provides primary compliance. A movable top lever arm bridges the beams and contacts fixed stops built into the base geometry, forcing the mechanism into two distinct stable positions. External force on the top arm triggers snap-through to the alternate position, with the contact geometry determining where the unstable equilibrium sits.

**Key dimensions:**
- living hinge width 0.51 mm (measured)
- beam width in plane 8.0 mm (measured)
- thickest member (base platform) 15.5 mm (measured)
- overall bbox 109.45 x 50.02 x 8.89 mm (measured)
- depth along Z (print height) 8.89 mm (measured)
- support beam angle ~20–30 deg from horizontal (estimated from render side profile)
- top lever arm span ~55 mm (estimated from XY render view)
- contact stops: small rounded protrusions on top arm and base (<1 mm estimated)

**Features to borrow:**
- 0.51 mm thin-section living hinge joining curved support beams at center
- rectangular base platform 109 x 50 x 8.9 mm with integral hollow core for mechanism motion
- bilaterally symmetric curved support beams anchored at both ends to base
- thin wall beam construction (8 mm wide) contrasting with thick base hub (15.5 mm)
- movable top lever arm creating four-bar pseudo-rigid-body linkage
- contact geometry (stops) built into base and lever to define bistable snap-through positions
- monolithic single-part design, no assembly required
- minimal overhang (0.6% of surface) for FDM printing

**Print notes:** Prints base-down (largest face on bed), the natural orientation in all photos. Designed for polypropylene by milling but 3D-printable in FDM-capable thermoplastics. The 0.51 mm living hinge is the critical stress point and fatigue limiter. Cycle life depends heavily on material: rigid PLA/ABS roughly 100–1000 cycles; flexible materials (TPU, modern flex resin) handle significantly more. Minimal supports needed due to low overhang. Avoid sharp corners at hinge junction to reduce stress concentration.

**build123d hints:**
- create rectangular base platform 109 x 50 x 8.9 mm, extrude solid
- sketch symmetrical angled beam pair (one per side) at ~20–25 deg from horizontal, 8 mm wide, ~55 mm length; extrude to full 8.9 mm height and merge into base
- at beam junction (center), create living hinge by reducing cross-section to 0.51 mm at the connection point; use offset inward on sketch and separate thin extrusion or chamfer edges down to ~0.5 mm in transitional zones
- mirror the curved support beam structure across the XZ symmetry plane
- model contact geometry as small rounded stops (<1 mm radius) on interior surfaces of top lever arm and base
- apply subtle fillet (0.1–0.2 mm) at living hinge root to reduce stress concentration
- verify motion in simulated assembly: top arm should rock between two stable positions when external force is removed

**Library map:**
- mechanisms.living_hinge: the 0.51 mm thin-section connector at beam junction
- mechanisms.parallel_flexure: paired curved support beams storing and releasing elastic energy
- mechanisms.latch_window: contact-driven bistable snap-through behavior
- gap: mechanisms.bistable_beam_pair: four-bar compliant toggle with dual-contact stop geometry

## Log
- 2026-09-10 filed from printables: how thick and how angled are the beams of a printed bistable toggle, and which way it prints
- 2026-09-10 reading by haiku subagent
- 2026-09-10 attached Bistable_Switch.STL: thinnest member 5.82 mm, min wall 0.49 mm
- 2026-09-10 attached Bistable_Switch.STL: thinnest member 5.82 mm, min wall 0.49 mm
- 2026-09-10 attached Bistable_Switch.STL: thinnest member 0.51 mm, min wall 0.49 mm
- 2026-09-10 attached Bistable_Switch.STL: thinnest member 0.51 mm, min wall 0.49 mm
- 2026-09-10 reading by haiku subagent
- 2026-09-10 attached Bistable_Switch.STL: thinnest member 0.51 mm, min wall 0.49 mm
- 2026-09-10 attached Bistable_Switch.STL: thinnest member 0.51 mm, min wall 0.49 mm
- 2026-09-10 reading by haiku subagent
- 2026-09-10 read alongside 581013; its four-bar lever with contact stops is not in the library yet (gap: a lever variant)
