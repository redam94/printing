---
title: Lid skirt tab and wall-embedded latch as library components
status: idea
kind: library
created: 2026-09-07
updated: 2026-09-07
tags: [lid, snap, latch, enclosure, promotion]
hardware: []
reuse: [mechanisms.cantilever_latch, mechanisms.latch_window, primitives.box_lid]
gaps: [mechanisms.skirt_tab, mechanisms.wall_latch]
model:
---

## Problem
`models/pi5_fan_case` builds its snap lid from two private helpers, `_skirt_tab()` and `_latch()`
(plus `_latch_pocket()`), that are not in the library. Both Pi 5 eval runs independently wrote the
same two helpers, which is the signal that they are library-shaped. The next snap-lid enclosure
would copy them, and the "never inline a mechanism in a model" rule would be broken twice.

## Concept
Two components in `lib/mechanisms/`:

- `mechanisms.skirt_tab` — a tab hanging from the lid rim outside the wall, with a
  `latch_window` cut through it and a lead-in chamfer on its bottom edge so the hook is pushed in
  as the lid closes. Positive solid, tab hanging in -Z from z=0 (the lid underside), centred on
  the wall it clears. Parameters: `width`, `drop`, `thickness`, `wall_clearance`,
  `window_*` forwarded to `latch_window`, `lead_in`.
- `mechanisms.wall_latch` — the body-side variant of `cantilever_latch`: a strip of an existing
  wall freed by slits so the beam lies flat in the bed plane, hook pointing outward. Returns the
  pocket (negative, cut first) and the beam (positive, fused after) so the caller does
  `body = body - pocket + beam`. Same beam/hook parameters as `cantilever_latch`.

## Constraints
- Orientation rule from `cantilever_latch` holds: beam flat in the bed plane, never standing up.
- Validated only in PETG (pi5_fan_case docstring); PLA is UNVALIDATED for the beam.
- Wall thickness is the beam thickness; walls under 1.6 mm cannot host a latch.

## Reuse map
| need | component | notes |
|---|---|---|
| hook + beam geometry | mechanisms.cantilever_latch | as is; `wall_latch` wraps it with the pocket |
| window through the tab | mechanisms.latch_window | needs a `lead_in` chamfer parameter (minor bump) or the tab adds it |
| lid plate and lip | primitives.box_lid | the skirt tab fuses to its underside |

## Gaps
`mechanisms.skirt_tab` and `mechanisms.wall_latch` (ids above). Source geometry already exists in
`models/pi5_fan_case/model.py` (`_skirt_tab`, `_latch`, `_latch_pocket`, `_TO_WALL`); promotion is
lifting them out with the model's numbers turned into parameters, then rebuilding the model
against the library versions with an unchanged golden.

## Open questions
- Should `latch_window` grow the lead-in chamfer (minor bump) or should the tab own it?
- Does the beam need the `root_fillet` parameter exposed when it merges into a continuous wall?

## Log
- 2026-09-07 captured from the two pi5_fan_case eval runs (both wrote the same helpers)
