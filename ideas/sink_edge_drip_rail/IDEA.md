---
title: Countertop edge drip rail for an undermount sink
status: sketching
kind: part
created: 2026-09-07
updated: 2026-09-08
tags: [kitchen, drying, sink, drainage, clip, petg, parametric]
hardware: []
reuse: [primitives.foot, primitives.rubber_foot_recess]
gaps: [primitives.edge_clip]
model:
---

## Problem
Whatever drying rack sits beside the sink, the last 50 mm between the rack and the basin is where
the water actually ends up: it runs off the rack, spreads on the counter and sits there. With an
undermount sink there is no rim to hang anything from, but the countertop cutout is a free edge —
the counter surface stops at the basin opening and the sink is glued underneath. That edge is the
one place a part can grip.

## Concept
A short C-profile clip that grips the countertop at the cutout, carrying a shallow pan. The pan
sits on the counter under the drying rack's downhill edge, its floor pitched toward the sink, and
its floor ends flush with the outboard face of the jaw that hangs down the square cut face — so
runoff leaves the pan 3 mm out over the opening and falls into the basin, never touching the
counter again. The jaw ends in a return lip that tucks into the reveal under the counter.

The section is a Z (pan above the counter, jaw below it), which normally means supports. It does
not here: printed lying on the jaw's outboard face, that face and the pan floor's end face are
coplanar by construction, giving a flat bed face of `RAIL_LEN x (COUNTER_T + LIP_T + FLOOR_T)`
with the pan floor, end walls and return lip all standing up off it. The only downward-facing
surface left is the rim ramp at the inland end, held at ~41 degrees by `RAMP_RATIO`.

The clip's throat has to swallow a stone countertop, which is thick — that is the whole design
question. The inner leg reaches under the counter and bears on the sink's own flange; a soft pad
on both jaw faces keeps it from marking the stone and stops it sliding.

This is the smallest of the drying-rack candidates and also the enabler under the others: the same
`edge_clip` grips the counter for [[drain_tiles]]' spout tile, and [[pot_fin_rack]] can use it
instead of overhanging the edge itself if the counter run is too shallow.

## Constraints
- PETG. Splash zone, and PLA creeps when a hot pan drains into it.
- Pan floor pitched >= 2 degrees toward the basin (sketch uses 3), with a V drip break cut into the
  outboard face 2 mm below the counter surface so water separates instead of wicking back under.
- No enclosed volume anywhere: the pan is open along its whole length and washable.
- Printed lying on the jaw's outboard face (see Concept). Sketched at 180 x 47.5 x 58 mm.
- Must not rely on adhesive or on drilling the counter.
- Relief at both counter corners so the printed inside corners cannot hold the clip off the stone
  (a printed 90-degree inside corner always carries a small radius; a square stone arris does not).

## Reuse map
| need | component | notes |
|---|---|---|
| soft jaw pad | primitives.foot | in TPU on a second toolhead, as the pad on each jaw face |
| pad seat | primitives.rubber_foot_recess | if using stick-on pads instead of printed TPU |

## Gaps
`primitives.edge_clip` — a C-profile clip that grips a panel or counter edge. Parameters as the
sketch settled them: `thickness` (the edge it grips; 30 default = 3 cm stone slab),
`throat_clearance` (0.4, added to thickness so it slides onto a square edge), `jaw_t` (3.0),
`under_reach` (how far the return lip tucks under; 0 degenerates to a plain saddle), `lip_t` (2.4),
`corner_relief` (1.2 radius at both inside corners), `pad_recess` (optional seat for a stick-on or
printed pad). Returned in print orientation, jaw outboard face on z=0, so whatever is grown off
its top flange prints without supports.

Library-shaped: this idea, the [[drain_tiles]] spout tile, and any future shelf hook, desk-edge
mount or monitor-lip hanger are the same C-section with different `thickness` and payload. It is
also the parent of the rim saddle that a rim-mounted sink bridge would have needed — that variant
was set aside only because this sink is undermount, not because the geometry was wrong.

## Open questions
- Countertop thickness at the cutout. Sketch assumes the standard 30 mm (3 cm stone slab);
  `COUNTER_T` is the lead knob and 20 / 25 / 30 / 38 all build, clear the slab with zero
  interference and fit the bed. Confirm the real number before printing.
- The reveal: how much counter underside is exposed at the cutout before the sink flange starts.
  That is what `UNDER_REACH` (4 mm) may occupy. Zero reveal means setting it to 0.
- How far the rack sits back from the edge — sets `PAN_REACH` (55 mm) and `RAIL_LEN` (180 mm).
- Does anything (a garbage-disposal air switch, a soap dispenser, the faucet base) occupy the
  stretch of edge this would sit on?

## Log
- 2026-09-07 captured in a drying-rack ideation session; picked by the user alongside
  [[pot_fin_rack]] and [[drain_tiles]]. Ranked as the cheapest print and the enabler for the
  other two.
- 2026-09-08 sketch round 1 (`uv run python scripts/sketch.py sink_edge_drip_rail`). Square edge
  confirmed by the user; `COUNTER_T` parameterised, default 30. Decisions this round:
  - The Z-section prints support-free lying on the jaw's outboard face, once the pan floor ends
    flush with that face rather than projecting as a separate spout. That removed the spout
    entirely: water leaves the pan 3 mm out over the opening and there is nothing to cantilever.
  - Rim ramp instead of a vertical rim wall — a vertical rim becomes a horizontal ledge in the
    print orientation. `RAMP_RATIO` 1.15 holds it at ~41 degrees.
  - End plates must be the whole filled section outline, not just the pan cavity: a cavity that
    only shares the floor edge with the rail fuses into two loose bodies.
  - Checker: 180 x 47.5 x 58 mm, 69.9 cm3, watertight, one body, 6017 mm2 bed contact,
    overhang 2.0 %, no problems. 0.4 % of the surface reads under 0.8 mm (the relief arcs and the
    V-notch flanks) — worth a look when this becomes a model, harmless in the sketch.
  - Verified across COUNTER_T 20 / 25 / 30 / 38: zero interference with a mock slab, Y grows
    exactly with thickness, all fit the bed.
  Next: measure the real counter and the reveal, then promote the section to
  `primitives.edge_clip` and build the model against it.
- 2026-09-08 changed by the [[drain_tiles]] sketch round, which feeds this rail:
  - `RIM_H` 10 -> 4. The tiles cantilever their deck over this rim to drip into the pan; at 10 mm
    the tile fouled the rim by 1231 mm3, at 4 mm the assembly has zero interference. Raise it back
    to ~10 if the rail is ever used on its own.
  - Added `RIM_TOP_W` (1.6 mm flat on the rim crest). Without it the ramp met the outer face in a
    knife edge, which is where **every** sub-0.8 mm sample in this part was coming from — the
    0.4 % noted in round 1 was not spread over the relief arcs at all, it was all one feature.
    Located by re-running the checker's own sampler and printing where the thin samples land:
    108 of 108 sat at the crest. With the flat top the rail reads **min wall 1.2 mm, 0.0 % under
    0.8 and under 1.2**, so round 1's only outstanding defect is closed.
  - Drip break is now a round-bottomed groove whose centre sits 0.4 mm outboard of the face
    (`DRIP_GROOVE_OUT`) instead of a V-notch. The V's mouth met the bed face at a tangent and left
    knife edges there; the offset circle meets it at 66 degrees. Overhang 2.0 % -> 1.5 %.
  - Checker after the changes: 180 x 41.8 x 58 mm, 61.4 cm3, watertight, one body, no problems.
