---
title: Pot, pan and lid fin rack
status: idea
kind: part
created: 2026-09-07
updated: 2026-09-07
tags: [kitchen, drying, rack, fins, sink, petg]
hardware: []
reuse: [primitives.pcb_slot_cradle, primitives.foot, primitives.rubber_foot_recess]
gaps: [primitives.slot_rack]
model:
---

## Problem
Pots, pans and their lids do not stack, and stood upside down on a flat drying rack they trap a
ring of water in the rim that is still there an hour later. A wire rack holds them at an angle but
takes the whole counter and rusts. Wanted: a compact printed rack that holds two or three pots
rim-down at a tilt so the rim drains, with narrow slots alongside for lids, sitting next to an
undermount sink so the runoff goes to the basin rather than the counter.

## Concept
A comb of vertical fins rising from a sloped base. Wide bays (fin pitch ~55 mm) take pots and pans
rim-down at about 15 degrees off vertical, so a rim resting on two fins drains along its low point;
a group of narrow bays (~12 mm pitch) at one end takes lids on edge. The base under the fins is
pitched a couple of degrees toward the sink-side edge and terminates in a lip that overhangs the
countertop cutout, so what runs off the fins runs off the base and into the basin (see
[[sink_edge_drip_rail]] for the case where the rack cannot reach the edge).

Printed base-down, fins standing: the fins are loaded in bending by a leaning pot, and standing
them up puts that load along the layer lines rather than across them. Nothing is enclosed — every
surface is reachable with a brush, and there are no closed cavities to grow mould.

## Constraints
- PETG, not PLA: this lives in splash range and may see hot pans; PLA creeps at dish temperatures.
- Fits the 270 x 270 x 270 bed as one part if the fin comb is kept under ~250 mm long; longer
  racks tile from two combs.
- Fin thickness >= 2.4 mm (6 perimeters at 0.4) so a wet 3 kg dutch oven leaning on one does not
  splay it.
- Base on the bed; fin tips are the top surface. No supports.
- Feet must lift the base ~4 mm so the underside dries and the counter stays dry.

## Reuse map
| need | component | notes |
|---|---|---|
| slotted fin geometry | primitives.pcb_slot_cradle | not usable as is — it is the 1.6 mm-pitch special case of the slot_rack this needs; generalise it (see Gaps) |
| feet | primitives.foot | print in TPU on a second toolhead so a wet rack does not slide |
| foot location | primitives.rubber_foot_recess | if using stick-on feet instead of printed TPU |

## Gaps
`primitives.slot_rack` — a parametric row of fins with the slots between them: `count`, `pitch`,
`slot_w`, `fin_t`, `fin_h`, `tilt` (fins leaning off vertical), `base_t`, `rounded tips`. Returns
the solid comb standing on z=0.

It is library-shaped several times over: `primitives.pcb_slot_cradle` becomes a two-rail instance
of it (same geometry, 1.6 mm slot, tilt 0), and the same component gives a plate rack, a lid rack,
a chisel/screwdriver holder and an SD-card holder. Writing it retires a private pattern rather
than adding a new one — the promotion test is that `esp32_devkit_case` rebuilds against the
generalised component with an unchanged golden.

## Open questions
- Pot diameters and lid diameters to size the bays for (largest pan, largest lid).
- Counter depth available beside the sink, and how far the base may overhang the cutout.
- Two or three pot bays? Three at 55 mm pitch plus six lid slots is roughly 240 mm, one print.
- Printed TPU feet (needs the second toolhead) or stick-on rubber feet?

## Log
- 2026-09-07 captured in a drying-rack ideation session; picked by the user alongside
  [[drain_tiles]] and [[sink_edge_drip_rail]]. The slot_rack generalisation was the reason this
  ranked highest on library payoff.
