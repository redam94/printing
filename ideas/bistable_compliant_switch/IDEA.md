---
title: Bistable compliant switch
status: prototyping
kind: library
created: 2026-09-10
updated: 2026-09-10
tags: [bistable, compliant, toggle, switch, living-hinge]
hardware: []
reuse: [mechanisms.bistable_beam_pair, mechanisms.living_hinge_web]
gaps: [mechanisms.bistable_lever]
model: bistable_coupon
---

## Problem
A bistable toggle (two rest positions, snaps between them, holds either without power) is the missing
mechanism for lid catches, cable clips, mode switches and detent slides. Its behaviour is hard to
predict from first principles, so the question was: how thick and how angled are the beams of a
printed bistable toggle, and which way does it print. Two BYU CMR references in `references/`
answer it with measured numbers.

## Concept
`mechanisms.bistable_beam_pair`: a central shuttle between two fixed anchors, two pre-tilted beams per
side, each beam a 5 mm body with 0.5 mm living-hinge necks at both ends, 6.35 mm deep, printed flat.
Pushing the shuttle past flat snaps it to the mirror state; travel = 2·span·sin(pretilt) ≈ 10.3 mm at
the defaults. Anchors fuse into the host part; the shuttle carries the working feature (hook, jaw,
button face).

## Constraints
- Flat on the bed, beams in XY; never standing. 0.5 mm neck = one 0.4 mm line (thin-wall / Arachne on),
  or widen to 0.8 and re-tune.
- Material: reference authors recommend PP; PETG expected to work; PLA expected to creep and fatigue.
- span (37) and pretilt (8°) are ESTIMATED from renders; hinge 0.5, beam 5.0, depth 6.35 are measured.

## Reuse map
| need | component | notes |
|---|---|---|
| the bistable slider itself | mechanisms.bistable_beam_pair | v0.1.0, UNVALIDATED, defaults from references/printables-581013.md |
| hinge dimensioning sanity | mechanisms.living_hinge_web | same 0.5 mm web, validated PETG/TPU |

## Gaps
`mechanisms.bistable_lever`: the 581016 switch variant (four-bar lever with contact stops, 8 mm links),
for wall-plate style toggles that press a microswitch.

## Open questions
- Do span 37 / pretilt 8° actually snap in PETG at hinge 0.5? Coupon print needed; then set `validated`.
- Snap force and cycle life in PETG vs PLA.
- Does a 0.8 mm (two-line) hinge still snap, or does the beam need to lengthen?

## Log
- 2026-09-10 captured from reference model
- 2026-09-10 two BYU CMR references filed and measured; mechanisms.bistable_beam_pair v0.1.0 written from them (unprinted)
- 2026-09-10 models/bistable_coupon built: coupon_h05 (0.5 mm necks) and coupon_h08 (0.8 mm) in a slotted frame with a through-plunger; review page published; awaiting PETG test print
