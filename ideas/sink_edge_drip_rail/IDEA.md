---
title: Countertop edge drip rail for an undermount sink
status: idea
kind: part
created: 2026-09-07
updated: 2026-09-07
tags: [kitchen, drying, sink, drainage, clip, petg]
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
A short C-profile clip that grips the countertop at the cutout, carrying a shallow channel. The
channel runs from under the drying rack's downhill edge, crosses the counter edge, and turns down
past the opening so drips fall into the basin instead of tracking back under the counter. 150-200
mm long, printed channel-up (open channel on top, no supports, nothing enclosed).

The clip's throat has to swallow a stone countertop, which is thick — that is the whole design
question. The inner leg reaches under the counter and bears on the sink's own flange; a soft pad
on both jaw faces keeps it from marking the stone and stops it sliding.

This is the smallest of the drying-rack candidates and also the enabler under the others: the same
`edge_clip` grips the counter for [[drain_tiles]]' spout tile, and [[pot_fin_rack]] can use it
instead of overhanging the edge itself if the counter run is too shallow.

## Constraints
- PETG. Splash zone, and PLA creeps when a hot pan drains into it.
- Channel floor pitched >= 2 degrees toward the basin, with a drip break (a sharp downward lip) at
  the outfall so water separates instead of wicking back along the underside.
- No enclosed volume anywhere: the channel is open along its whole length and washable.
- Printed channel-up, bed contact on the outside of the channel floor. Under 200 x 60 x 60 mm.
- Must not rely on adhesive or on drilling the counter.

## Reuse map
| need | component | notes |
|---|---|---|
| soft jaw pad | primitives.foot | in TPU on a second toolhead, as the pad on each jaw face |
| pad seat | primitives.rubber_foot_recess | if using stick-on pads instead of printed TPU |

## Gaps
`primitives.edge_clip` — a C-profile clip that grips a panel or counter edge: `thickness` (the
edge it grips), `depth` (how far the jaws reach in), `jaw_t`, `throat_clearance`, `spring` (the
inner jaw as a compliant beam so it preloads onto the edge), `pad_recess` (optional seat for a
stick-on or printed pad). Returned standing on z=0 in its print orientation.

Library-shaped: this idea, the [[drain_tiles]] spout tile, and any future shelf hook, desk-edge
mount or monitor-lip hanger are the same C-section with different `thickness` and payload. It is
also the parent of the rim saddle that a rim-mounted sink bridge would have needed — that variant
was set aside only because this sink is undermount, not because the geometry was wrong.

## Open questions
- Countertop thickness at the cutout (stone is typically 20-32 mm, sometimes 38 with a built-up
  edge) and whether the sink flange leaves room underneath for the inner jaw.
- Is the cutout edge square, bullnosed or eased? A radius changes the jaw's inner profile.
- How far the rack sits back from the edge — sets the channel length.
- Does anything (a garbage-disposal air switch, a soap dispenser, the faucet base) occupy the
  stretch of edge this would sit on?

## Log
- 2026-09-07 captured in a drying-rack ideation session; picked by the user alongside
  [[pot_fin_rack]] and [[drain_tiles]]. Ranked as the cheapest print and the enabler for the
  other two.
