# FDM design rules baked into the library

Numbers assume a 0.4 mm nozzle, 0.2 mm layers, PLA/PETG. Components already apply these; use
this when writing geometry the library does not cover.

## Holes and fits
- **Holes print undersized.** Add 0.2–0.4 mm to a clearance hole's diameter (`print_oversize`).
  Vertical holes < 3 mm shrink the most; horizontal holes sag into ovals.
- **Slip fit:** 0.2–0.3 mm gap per side (lids, lips, sliding covers). **Press fit:** 0.05–0.1 mm
  interference per side. **Free rotation (pin in hole):** 0.3–0.5 mm.
- **Clearance holes:** ISO 273 medium + oversize (M3 → 3.4 + 0.2). Use `fasteners.clearance_hole`.
- **Heat-set inserts:** hole per the *insert* spec (M3 → Ø4.0, depth 5.7 + 1), not per the screw.
  Boss OD ≥ hole + 2 x 1.6. Use `fasteners.heat_set_boss` / `heat_set_pocket`.
- **Screwing into plastic:** pilot = d − 0.3 (M3 → 2.7), depth ≥ 2d, wall ≥ d. `fasteners.screw_boss`.
- **Nut traps:** across-flats + 0.2–0.3, thickness + 0.2. `fasteners.captive_nut_slot`.

## Walls and features
- **Wall thickness in nozzle multiples:** 0.8 (2 perimeters, lids/vents), 1.2 (3, light enclosures),
  1.6 (4, default enclosures), 2.0–2.4 (structural, bosses under load). A 1.0 mm wall prints as
  2 perimeters with a gap — avoid odd multiples.
- **Minimum feature:** 0.8 mm for pins/ribs to be solid; text/emboss ≥ 0.6 wide, ≥ 0.4 deep.
- **Elephant foot:** chamfer the bed-contact edge 0.4–0.6 mm (`bottom_chamfer` params). Never
  fillet it — a fillet on the bed edge creates an overhang.
- **Fillet vertical corners** (R ≥ 1) to reduce warping and stress; chamfer horizontal ones.

## Overhangs and bridges
- Past **45°** from vertical needs support. Chamfers ≤ 45° are free; fillets on undersides are not.
- **Horizontal holes:** teardrop (45° point) or hexagon the top so it bridges (`primitives.teardrop`).
  Round horizontal holes > 8 mm sag noticeably.
- **Bridges:** flat ceilings bridge cleanly up to ~15–20 mm; beyond that add a rib or sacrificial layer.
  Counterbores on the bed side need a 0.2 mm sacrificial layer or a printed-in-place bridge.
- **check_printable.py** reports overhang area and flat-ceiling area; anything > 2% of surface is a flag.

## Orientation and strength
- **Layer adhesion is the weak axis.** Orient so tensile/bending load runs along the layers
  (in the bed plane), not across them. A snap hook printed vertically breaks at the root.
- **Compliant parts** (latches, hinges, flexures): beam lying flat, flex direction in the bed plane.
  PETG/ABS flex reliably; PLA snaps below 1.2 mm or after tens of cycles. Living-hinge webs
  0.4–0.6 mm print as 2–3 continuous layers.
- **Bosses and pins** should be vertical so screws thread across layers.
- **Largest flat face down.** State which face is on the bed in the model docstring, and match
  `MaterialNotes.orientation` when promoting to the library.
- **Threads:** don't model them below M6; use inserts or nuts.

## Enclosure defaults
- Cavity = hardware envelope + 1.0 per side (PCB) or + 2.0 (cables, connectors).
- Standoff height ≥ 3 mm so solder joints clear the floor; ≥ 6 with through-hole leads.
- Lid lip 3 mm tall, 1.2 thick, 0.25 clearance per side. Snap ridges 0.6 R.
- Vents: 1.6 mm slots at 4 mm pitch; on vertical walls run them vertically (no bridging).
- Connector cutouts: connector + 1.0 per side, chamfer the outside edge 0.5.

## Metrics sanity
- Report bbox and volume every build. Volume x 1.24 g/cm³ (PLA) ≈ solid mass; with 20% infill and
  4 perimeters expect roughly half that for boxy parts.
- A part smaller than 0.5 cm³ or thinner than 0.8 mm anywhere is a flag, not an error.
