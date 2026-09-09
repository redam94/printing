---
title: Snap-together draining tiles feeding the drip rail
status: sketching
kind: part
created: 2026-09-07
updated: 2026-09-09
tags: [kitchen, drying, tiles, modular, drainage, snap, shingle, petg]
hardware: []
reuse: [mechanisms.snap_ridge, mechanisms.snap_groove]
gaps: [primitives.groove_field, primitives.tenon_socket]
model:
---

## Problem
A drying mat beside the sink holds the water it collects: the tray fills, and someone has to
carry it to the sink and tip it out. The counter run beside a sink is also never the size of any
rack you can buy — it wants to be a different width in every kitchen, and a rack sized for the
worst case wastes counter the rest of the time.

## Concept
A row of tiles, `TILE_X` = 90 mm each, that snap edge to edge along the counter so the field is
whatever width the counter allows. Each tile is a deck pitched 4 degrees toward the sink with
trapezoidal grooves running down it: dishes stand on the ribs between grooves, water runs in the
grooves to the outboard edge and off a drip nose. Two side walls carry the deck, sit flat on the
counter and hold the snap joint — one wall has a bead, the other a matching groove, so a run of
tiles is one continuous deck with the joint hidden under the seam.

The tile does not reach the sink itself. Its deck cantilevers past its walls (`WALL_SETBACK`) and
overhangs the rim of [[sink_edge_drip_rail]], dripping into the rail's pan, which carries the
water across the counter edge into the basin. That is what removes the spout tile from this idea
entirely: the rail is the spout, for the whole row at once.

Nothing is enclosed. The whole underside is open front to back, and a brush reaches every face.

### Second axis: the field grows in depth too (brief `fqpeiyno0oxdncx6rxe2`, 2026-09-09)

Sketch round 1 concluded the field could only be one row deep, because identical tiles cannot
stack in the flow direction without each row sitting a tile-drop lower than the one behind it.
The brief answers that objection rather than accepting it: **tiles overlap like roofing tiles or
fish scales.** The drop between rows is taken up by the overlap itself, so the uphill tile's
deck sheds onto the downhill tile's deck and the joint never has to be watertight — water cannot
leak *between* the links because the upper link is always over the lower one.

That changes the module: **70 x 70 mm** instead of 90 x 140, so a field is built to the counter
in both directions, and the edge joint becomes the same key on all four edges — one self-mating
wedge profile (see Gaps), rotationally symmetric so any edge mates with any other. The X joint
is then no longer `mechanisms.snap_ridge` / `snap_groove`; those stay in the reuse map until a
sketch round has actually shown the wedge key works in both axes.

The field still ends at [[sink_edge_drip_rail]], and the same edge language is what would let
[[pot_fin_rack]] sit in the field rather than beside it.

## Constraints
- PETG. Splash zone; PLA creeps and the snap joints relax. **The brief says PLA** — unresolved,
  see Open questions. A shingle field is less exposed to creep than a snap joint under load, so
  PLA may be defensible here in a way it was not for [[sink_edge_drip_rail]] (hot pans).
- Module 70 x 70 mm (brief), was 90.6 x 140.4 in sketch round 1. One tile is far under the 270 mm
  bed either way; the smaller module is what makes a 2D field practical.
- Tiles overlap in the flow direction (shingle), so no joint has to seal.
- The same edge key on all four edges, no drilling and no adhesive anywhere in the field.
- Deck pitch >= 3 degrees so water moves at low volume (sketch uses 4).
- Grooves 5 mm wide at 9 mm pitch, 1.2 deep, walls 30 degrees off vertical so they self-support
  when the deck is printed face down. Ribs between them are 4 mm — a mug rim bridges, water leaves.
- No enclosed volume: no second level, no tray under the deck.
- `FOOT_H` must clear the drip rail's pan rim where the deck overhangs it (see Log).
- Snap joints must survive being pulled apart for washing repeatedly — not a one-time assembly.

## Reuse map
| need | component | notes |
|---|---|---|
| tile-to-tile joint | mechanisms.snap_ridge | bead on the +X wall face, 0.6 r |
| matching joint | mechanisms.snap_groove | groove in the -X wall face, 0.1 clearance; verified to mate with zero interference |
| groove field | — | see Gaps; the sketch freehands it |
| four-edge tile key | — | see Gaps, `primitives.tenon_socket`; supersedes the two rows above if it works |

## Gaps
`primitives.groove_field` — a field of blind, self-supporting drain grooves in a surface:
`area_l`, `area_w`, `pitch`, `width`, `depth`, `wall_deg` (groove wall angle off vertical),
`rotation`. Library-shaped because the rule it encodes is not obvious and is easy to get wrong:
a groove cut into a face that will be printed *face down* has its wall angle as the overhang
angle, so square-walled grooves become flat ceilings and 45-degree walls sit exactly on the
limit. Any drying tray, soap dish, drainer or draining shelf wants the same thing.
`primitives.vent_slots` is the near neighbour but not the same component: it cuts *through* a wall
for airflow, this one cuts *into* a surface for liquid.

`primitives.tenon_socket` — a self-mating wedge key run along an edge, worked out on the brief
thread: one extruded profile split through its thickness, the top half a wedge tenon (45 degree
flanks, proud of the wall's outer face), the bottom half the matching socket recessed at the true
edge line, so a tile keeps its exact 70 mm pitch and any edge mates with any edge rotated 180
degrees. Parameters as specced: `length`, `thickness`, `key_height` (1.5), `key_width` (6),
`draft_angle` (45), `play` (0.15 for PLA). Returns the positive tenon and the negative socket
cutter keyed to the same edge line. 45 degree flanks print without support; 1.5 mm key height
keeps the local wall above the 1.2 mm floor.

**Wanted by two ideas**, which is the library-shaped test: this field, and the body/jaw and
body/base joints in [[mawile_headphone_stand]] (already listed there as a gap). Whichever is
built first should write the component.

Dropped by the sketch, recorded so they are not re-proposed:
- `primitives.drip_spout` — not needed. [[sink_edge_drip_rail]] is the spout for the whole row.
- `primitives.sloped_floor` — not needed *here*. The tile is a tilted slab on two walls, not a
  shell with a pitched floor. Still a reasonable component for trays and saucers, but nothing in
  the current ideas wants it, so it should not sit on the roadmap as if something does.

## Open questions
- Counter run available beside the sink: length and depth. Length fixes the tile count, depth
  fixes `TILE_Y` (sketch uses 140 mm).
- Does anything need to sit flat on the field (a cutting board, a pan)? That would argue for a
  solid-topped tile variant sharing the same snap module.
- **PLA or PETG?** The brief says PLA, sketch round 1 says PETG. The failure PETG was chosen for
  (a snap joint relaxing under constant load in a splash zone) may not apply to a shingle field
  that is only keyed, not sprung. Decide before the next sketch: it changes `play` in the key.
- The brief left "it works if..." blank. The obvious test — a jug of water poured on the back row
  ends in the basin with nothing under the field — needs confirming; without it there is no way
  to fail a print.
- Does each tile carry its own molded channel (1-2 mm fall toward its downhill edge), or do tiles
  stay flat and rely on the overlap plus the counter? Assumed the former on the thread.
- Load: are these light-duty drip trays, or does a hand or a full pan press on them? Assumed
  light duty (ribs 1.2 mm, floor 1.5 mm) on the thread.
- Does the tenon stay inside the 70 mm footprint? Settled on the thread: yes, inset, so the field
  keeps true 70 mm centres.
- Anti-slip: the side walls are the feet, so `primitives.foot` no longer applies. A TPU bottom
  strip on a second toolhead is the natural answer on this printer — worth trying on the first
  print.

## Log
- 2026-09-07 captured in a drying-rack ideation session; picked by the user alongside
  [[pot_fin_rack]] and [[sink_edge_drip_rail]]. Ranked last of the three on cost (two gaps) but
  it is the one that fits an undermount sink with no rim to hang from.
- 2026-09-08 sketch round 1 (`uv run python scripts/sketch.py drain_tiles`). The design changed
  substantially, and so did the reuse map — it is now two components, not six.
  - **The idea contradicted itself.** It asked for a slot grid over a sloped floor *and* an open
    bottom. With nothing under the slots the water lands on the counter; with a floor under them
    there is a cavity that cannot be scrubbed. Resolved as ONE surface: a pitched deck with
    grooves down it. Dishes on the ribs, water in the grooves. That drops
    `primitives.vent_slots` (nothing is cut through) and `primitives.rounded_box` (there is no box).
  - **The field is one row deep, not a 2D grid.** Tiles stacked in Y would each have to sit lower
    than the one behind by the tile's own drop, so identical tiles cannot tile in the flow
    direction. The field grows along the counter edge only; `TILE_Y` is the counter depth used.
  - **The tiles feed the rail rather than reaching the sink.** Verified as a placed assembly, not
    by eye: with the rail's `RIM_H` at its old 10 mm the tile fouls the rim by 1231 mm3. Lowering
    the rail's rim to 4 mm and setting `WALL_SETBACK` 14 mm (so the deck cantilevers over the rim
    while the walls stop short of it) gives **zero interference** at tile `FOOT_H` 10 / 14 / 16.
    The rail's default `RIM_H` was changed to 4 for this reason; see that idea's log.
  - Two tiles side by side: **zero interference**, bead reaches x=45.60 into a neighbour groove
    that starts at x=45.00, decks butt at the tile boundary with no gap.
  - Groove walls at 45 degrees read as a 14 % overhang flag; at 30 degrees they are comfortable.
    The checker still reports ~13.8 % "overhang" either way, because it counts the groove
    *ceilings* — 3.6 mm bridges sitting 1.2 mm off the bed. Those are routine, and this is worth
    remembering: on a face-down grooved deck the headline overhang number is not the useful one.
  - Checker: 90.6 x 140.4 x 24.9 mm, 44.2 cm3, watertight, one body, 5600 mm2 bed contact,
    min wall 1.7 mm, no problems.
  Next: measure the counter run, then write `primitives.groove_field` and build the model against
  it together with `primitives.edge_clip` from [[sink_edge_drip_rail]].
- 2026-09-09 revisited from the Briefs page (brief `fqpeiyno0oxdncx6rxe2`, 87 % answered). The
  brief asks for depth as well as length and answers round 1's "one row deep" conclusion with a
  shingle overlap; module drops to 70 x 70 and the joint becomes one self-mating wedge on all
  four edges (`primitives.tenon_socket`, specced on the brief thread and also wanted by
  [[mawile_headphone_stand]]). Filed here rather than as a separate idea because it is the same
  object: the brief calls the existing tiles "the current part". Open: PLA vs PETG, and a
  success test. Next sketch round should try the shingle field before anything is promoted.
