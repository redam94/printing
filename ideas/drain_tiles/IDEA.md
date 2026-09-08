---
title: Snap-together draining tiles with a spout tile
status: idea
kind: part
created: 2026-09-07
updated: 2026-09-07
tags: [kitchen, drying, tiles, modular, drainage, snap, petg]
hardware: []
reuse: [primitives.vent_slots, mechanisms.snap_ridge, mechanisms.snap_groove, primitives.rounded_box, primitives.foot, primitives.rubber_foot_recess]
gaps: [primitives.sloped_floor, primitives.drip_spout]
model:
---

## Problem
A drying mat beside the sink holds the water it collects: the tray fills, and someone has to
carry it to the sink and tip it out. The counter run beside a sink is also never the size of any
rack you can buy — it wants to be a different width in every kitchen, and a rack sized for the
worst case wastes counter the rest of the time.

## Concept
A field of 90 x 90 mm tiles, roughly 12 mm tall, that snap edge to edge into whatever footprint
the counter allows. Each tile is a shallow tray whose floor is pitched a few degrees toward one
edge, with a coarse slot grid over it so dishes stand on slots and water falls through to the
sloped floor beneath and runs to the low edge. Tiles pass water to their downhill neighbour
through a notch in the shared wall; the last tile in the run is a spout variant whose floor
narrows into a lip that overhangs the countertop cutout and pours into the basin.

Bed side is the tile's underside; the slot grid is the top surface. The tray under the slots is
**open at the bottom** — it is a pitched shelf standing on feet, not a sealed void. A closed
cavity in a permanently wet part cannot be scrubbed and will grow mould, which is the failure mode
that kills most printed dish racks.

If the counter run cannot reach the basin, the spout tile hands off to [[sink_edge_drip_rail]]
instead of overhanging by itself.

## Constraints
- PETG. Splash zone; PLA creeps and the snap joints relax.
- One tile is well under the 270 mm bed; a six-tile field is six identical prints plus one spout.
- Floor pitch >= 3 degrees so water actually moves at low volume; slot webs >= 1.2 mm.
- Slots sized for dish feet, not for ventilation: `slot_w` 5-6 mm at ~9 mm pitch, so a mug rim
  bridges but water leaves immediately.
- Feet lift the field ~4 mm; the counter under the rack must dry.
- Snap joints must survive being pulled apart for washing repeatedly — not a one-time assembly.

## Reuse map
| need | component | notes |
|---|---|---|
| drain grid | primitives.vent_slots | as is, run coarse (slot_w ~5.5, pitch ~9, several rows) |
| tile tray body | primitives.rounded_box | as the shell; its flat floor is then replaced (see Gaps) |
| tile-to-tile joint | mechanisms.snap_ridge | bead on two edges of every tile |
| matching joint | mechanisms.snap_groove | groove on the opposite two edges; check clearance survives repeated cycles |
| feet | primitives.foot | TPU on a second toolhead so the field does not slide when loaded |
| foot seat | primitives.rubber_foot_recess | if using stick-on feet instead |

## Gaps
`primitives.sloped_floor` — replace a shell's flat floor with one pitched by `angle` toward a named
edge, keeping the wall heights and the floor thickness constant. Parameters: `length`, `width`,
`angle`, `floor_t`, `toward` (+X/-X/+Y/-Y), optional `channel` (a shallow gutter along the low
edge). Library-shaped: every tray, planter saucer, soap dish, drip channel and battery tray wants
it, and it composes with `primitives.rounded_box` rather than replacing it.

`primitives.drip_spout` — a channel that narrows into a pour lip with a drip-break undercut so the
stream separates instead of wicking back along the underside. Parameters: `width_in`, `width_out`,
`length`, `drop`, `wall`, `break_depth`. Used by this tile and by [[sink_edge_drip_rail]]'s
outfall, which is the second use that makes it library rather than model geometry.

## Open questions
- Counter run available beside the sink: length and depth, which fixes the tile count and whether
  90 mm is the right module.
- Does the field need to reach the basin at all, or does it hand off to the drip rail?
- Countertop thickness at the cutout, for the spout tile's overhang (same measurement
  [[sink_edge_drip_rail]] needs).
- Does anything need to sit flat on the field (a cutting board, a pan), which would argue for a
  solid-topped tile variant in the same snap module?

## Log
- 2026-09-07 captured in a drying-rack ideation session; picked by the user alongside
  [[pot_fin_rack]] and [[sink_edge_drip_rail]]. Ranked last of the three on cost (two gaps) but
  it is the one that fits an undermount sink with no rim to hang from.
