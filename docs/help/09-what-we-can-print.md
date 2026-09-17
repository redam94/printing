---
title: What we can and cannot print
order: 9
summary: Sizes, detail, strength, what is possible in one piece, and what is refused.
---

## Size and detail

- **Largest single piece:** {printer.bed}. Bigger things are split into pieces that bolt, slot or glue together, and the joint is designed in.
- **Layers:** {printer.layer}, from a {printer.nozzle} nozzle.
- **Finest detail:** about {printer.nozzle}. Raised or engraved text should be at least 3 mm tall to stay readable.
- **Thinnest wall:** 1.2 mm for anything structural, 0.8 mm for decoration.
- **Accuracy:** roughly ±0.2 mm on any single dimension.
- **Smallest useful hole:** about 2 mm. Holes print slightly undersized, so they are enlarged on purpose in the design.

## What prints well

- Boxes, trays, brackets, mounts, holders, stands, organisers, spacers and adapters.
- Enclosures with cutouts for real connectors, and pockets for brass threaded inserts.
- Snap fits, living hinges and clips, in PETG or TPU where they must flex repeatedly.
- Print-in-place mechanisms: hinges, latches and switches that come off the printer already assembled.
- Replacement knobs, feet, clips and handles, copied from a broken original.
- Decorative pieces: vases, planters, ornaments, lamp shades.

## What does not print well

- **Very thin, tall and unsupported:** a 1 mm post 100 mm high will not survive use.
- **Perfectly flat and very wide:** big flat plates can warp slightly; ribs are added to keep them true.
- **Watertight containers:** printed walls are not reliably sealed for liquids without a coating.
- **Fine threads:** anything below M6 is better as a brass insert or a captive nut, which is designed in.
- **Sharp cutting edges**, gears under real load, or anything that has to stay accurate while hot.

## What we will not print

- Weapons, weapon parts, or anything designed to cause harm.
- Safety-critical parts: anything holding a person's weight, a child's harness, a climbing or diving component, a load-bearing vehicle or electrical part.
- Copies of a copyrighted or patented product for resale, or anything that infringes a third party's rights.
- Keys, locks, or anything meant to defeat a security device.
- Medical or dental appliances, and anything implanted or used inside the body.

::: warn Printed plastic has limits
FDM parts soften with heat, creep slowly under a constant load, and are weaker across the layers than along them. If a part is holding something heavy, valuable or fragile, say so in the request: it changes the material, the wall thickness and the way the part is oriented on the printer.
:::
