---
title: Snap-on ring clip for a 5.5 mm rod
status: prototyping
kind: part
created: 2026-09-11
updated: 2026-09-11
tags: [clip, ring clip, snap-on, living hinge, compliant]
hardware: [5.5 mm rod]
reuse: [mechanisms.split_ring_clip]
gaps: []
model: ring_clip_5_5
---

## Problem
A downloaded mesh (`Parametric_clip_VL_5.5.STL`) is a good snap-on clip for a 5.5 mm rod, but a
mesh cannot be resized. Read how it is dimensioned (ring bore and wall, living-hinge neck widths and
their Z extent, push-arm width and angle, side spring thickness, rail thickness) and make it a
parametric library component so the same clip can be built for any rod and fused to any host part.

## Concept
A C-ring (bore = rod - grip) hangs on two angled push arms through living-hinge necks; the arms'
outer ends sit on round posts at the foot of thin side strips that drop from a stiff mounting
rail. The rod snaps in through the bottom slit: the halves spread about a thin bridge across the
top slit, the arms are pulled outward, the strips bend, and then hold the jaws shut on the rod.
Squeezing the posts together tightens the jaws. The reference keeps every neck as two 1.9 mm
plates at the faces with a gap between them (half the hinge stiffness); the component reproduces
that with `neck_plate` and can also run the necks full depth.

## Constraints
- Prints flat, 7.2 mm tall, necks one 0.4 mm line: thin-wall perimeters on.
- No mounting holes on the reference rail; the host model cuts its own.
- Material unvalidated: the reference came with no page. PETG expected; PLA to be tested.

## Reuse map
| need | component | notes |
|---|---|---|
| the whole clip | mechanisms.split_ring_clip v0.1.0 | new; defaults are the measured reference numbers rounded to line multiples |

## Gaps
none: the clip is the component. If a mounted version is wanted, add a rail hole option or fuse to a host.

## Open questions
- Which material and how many insertions before the necks whiten (coupon: models/ring_clip_5_5).
- Do the plated necks (as the reference) or the full-depth necks feel right on a 5.5 mm pen barrel.

## Log
- 2026-09-11 captured from reference model
- 2026-09-11 reference measured and read (file-5725bdb05c); mechanisms.split_ring_clip written from its numbers; coupon model ring_clip_5_5 built (clip, clip_full_necks) and its review page published
