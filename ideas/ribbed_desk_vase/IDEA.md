---
title: Ribbed desk vase
status: prototyping
kind: part
created: 2026-09-07
updated: 2026-09-07
tags: [vase, form, spiral-vase, flutes]
hardware: []
reuse: [form.revolved_body, form.shell_open_top, form.flutes]
gaps: []
model: ribbed_vase
---

## Problem
like the vertical ribs and the fat shoulder

## Concept
Tall ~2:1 cylinder with a bulging shoulder and a wide mouth, 28 sharp-edged vertical flutes from
just above the base through the shoulder to the rim (from the inspiration brief).  Printed in
spiral / vase mode: one perimeter follows the fluted contour.

## Constraints
- 150 mm tall, 92 mm across the shoulder; fits the U1 bed with room to spare.
- Shoulder leans out 28 deg, mouth leans in 14 deg: both under the 60 deg single-wall limit.
- Single wall is not watertight; dried stems or a glass insert.

## Reuse map
| need | component | notes |
|---|---|---|
| spline body of revolution | form.revolved_body | (r, z) profile in params.py, end tangents |
| hollow with open top | form.shell_open_top | 2.0 mm wall (only matters outside vase mode) |
| vertical flutes following the profile | form.flutes | 28 x 3.2 wide x 1.2 deep, reference = the solid |

## Gaps
none: the form category (added 2026-09-07) covers this.

## Open questions
- Twisted flutes (FLUTE_TWIST) as a variant?
- Print and check whether the 0.8 mm rib floors matter when not in vase mode.

## Log
- 2026-09-07 captured from local vase.png
- 2026-09-07 promoted to models/ribbed_vase (vase mode); first build passes the single-wall checks
