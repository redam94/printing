---
title: Pot, pan and lid fin rack
status: sketching
kind: part
created: 2026-09-07
updated: 2026-09-08
tags: [kitchen, drying, rack, fins, sink, petg]
hardware: []
reuse: []
gaps: [primitives.slot_rack, primitives.groove_field]
model:
---

## Problem
Pots, pans and their lids do not stack, and stood upside down on a flat drying rack they trap a
ring of water in the rim that is still there an hour later. A wire rack holds them at an angle but
takes the whole counter and rusts. Wanted: a compact printed rack that holds two or three pots
rim-down at a tilt so the rim drains, with narrow slots alongside for lids, sitting next to an
undermount sink so the runoff goes to the basin rather than the counter.

## Concept
A comb of leaning blades on a base plate. Three wide bays (48 mm pitch, 85 mm blades) take pots
and pans; six narrow slots (12 mm pitch, 55 mm blades) take lids on edge. Blades lean 12 degrees
so items rest against a blade face rather than balancing on an edge, and their **tops slope 10
degrees toward the sink** — that is the whole point of the rack, because a rim resting across
level blade tops sits horizontally and holds exactly the ring of water this is supposed to drain.
The tile under it adds its own 4 degrees, so a rim sits at ~13.7 degrees.

The comb does not carry its own drainage. It stands on the [[drain_tiles]] field and inherits its
pitch; its base only has to move water forward off its own front edge onto the tile downstream.
The tiles carry it to [[sink_edge_drip_rail]] and the rail to the basin. That is why there is no
sloped wedge base and no spout here — the row already has one.

Printed as drawn: base underside flat on the bed, blades up. The blades are **sheared, not
rotated**, so every root stays flat on the base and the lean is the only overhang angle in the
part.

## Constraints
- PETG. Splash zone, and it may take a hot pan.
- Blades >= 2.4 mm thick (sketch uses 2.6) so a wet 3 kg dutch oven leaning on one does not splay
  it; min wall in the sketch is 2.0 mm.
- Lean angle is the print overhang angle. 12 degrees is comfortable; keep it well under 40.
- Fits the bed, but only just: 253 x 60 x 88 mm against a 270 mm bed. The lean adds ~19 mm to the
  X envelope on top of the blade span, which is easy to forget when adding a bay.
- Base grooves must sit in the bays, never under a blade (see Log).
- Nothing enclosed; the whole base is reachable with a brush.

## Reuse map
Nothing. This idea uses no existing library component — see Gaps for why that is a correction
rather than an oversight.

## Gaps
`primitives.slot_rack` — a row of leaning blades with the slots between them, standing on z=0 and
centred in X. Signature as the sketch settled it: `count`, `pitch`, `fin_t`, `fin_h` (height at
the back edge), `depth`, `tilt_deg` (shear off vertical, and the print overhang angle),
`top_slope_deg` (tops sloping down toward +Y so nothing resting across them sits level).
Library-shaped: this rack uses it twice with different parameters in one part, and a plate rack,
a chopping-board rack, a tool holder and an SD-card holder are all the same component.

`primitives.groove_field` — shared with [[drain_tiles]], which specifies it. This idea adds one
requirement to that spec: the lanes must be placeable explicitly, not only on a uniform pitch,
because a groove parallel to a blade will cut that blade off its base.

**Correction to this idea's original justification.** It claimed `primitives.pcb_slot_cradle` was
"the 1.6 mm-pitch special case of the slot_rack this needs", making the gap a generalisation that
would earn back an existing component. Reading the source, that is wrong. `pcb_slot_cradle` is a
*pair of facing rails with one horizontal slot each*, gripping a board by two edges and loaded
from the side; a slot_rack is a comb of blades with open gaps, loaded from above. Forcing one
component to do both would make both worse. `slot_rack` is worth writing, but as a new component,
and this idea's cost is a whole afternoon more than the original write-up implied.

## Open questions
- Which pots and pans, and which lids: largest diameter and rim thickness. That fixes bay count,
  pitch and blade height, and it is the only thing standing between this and a model.
- Does a big pot rim-down actually sit stably across 48 mm bays, or does it want a concave blade
  top to cradle it? A test print answers this and nothing else will.
- It is the largest part in the system: 147 cm3, ~250 mm long, and the longest print of the three.
  Dropping `DEPTH` from 60 to 45, or one pot bay, takes a large bite out of that.
- Anti-slip where it sits on the tile deck: a TPU pad strip on a second toolhead, or blade-root
  ribs keyed into the tile grooves (needs the two pitches to relate).

## Log
- 2026-09-07 captured in a drying-rack ideation session; picked by the user alongside
  [[drain_tiles]] and [[sink_edge_drip_rail]]. The slot_rack generalisation was the reason this
  ranked highest on library payoff.
- 2026-09-08 sketch round 1 (`uv run python scripts/sketch.py pot_fin_rack`).
  - **The generalisation claim does not survive reading the source.** See Gaps. The reuse map went
    from three components to none: `pcb_slot_cradle` is a different mechanism, and
    `primitives.foot` / `primitives.rubber_foot_recess` do not apply because the rack stands on the
    tile field on its own base rather than on the counter on feet.
  - **Level blade tops defeat the whole idea.** Added `top_slope_deg` to the proposed component;
    measured 9.7 degrees on the built part, ~13.7 with the tile's pitch under it.
  - **Blades must run from z=0, not sit on the base.** A blade whose root merely shares a face with
    the base fuses into a loose body — the first build came out as 6 separate solids. Running them
    from z=0 and cutting the grooves through base and blades together fixes it, and the notches
    that leaves at each root are what lets water past a blade instead of damming behind it.
  - **A groove parallel to a blade severs it.** With the grooves on a uniform 9 mm pitch and the lid
    blades on 12 mm, every third lid blade landed inside a groove and came off the base entirely
    (three 8.54 cm3 solids floating at z=3.2). Grooves are now generated per bay, keyed to the
    blade positions with a 2 mm margin.
  - Checker: 253.0 x 60.0 x 88.2 mm, 147.3 cm3, watertight, one body, 14796 mm2 bed contact,
    min wall 2.0 mm, **0.0 % overhang and zero flat ceilings** — no supports anywhere.
  - Placed on a three-tile field with the rail: rests on the deck, contact only (51 mm3 of boolean
    sliver between coincident faces).
  Next: pot and lid dimensions, then write `primitives.slot_rack` and build the model against it.
