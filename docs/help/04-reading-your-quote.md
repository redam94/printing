---
title: Reading your quote
order: 4
summary: What arrives with a quote: the 3D viewer, the measurement sheet and the estimate.
---

A quote is not a number in an e-mail. It is the design itself, with the numbers attached, so you can check it before committing.

## What arrives

| Attachment | What it is |
|---|---|
| `…-3d-viewer.html` | The model, in a file that opens in any browser |
| Renders (`.png`) | The part from three sides, with its overall size |
| `measurements.md` | Every part's size, thinnest wall, and each dimension that was assumed |
| The comment itself | A plain-language description, the price, the print time and the ready-by date |

## Using the 3D viewer

Download the viewer file and double-click it; it opens like a web page and needs no software or account.

- **Drag** to turn the part, **scroll** to zoom, **shift-drag** to slide it around.
- **Section plane** cuts the part open at any height, so you can look inside a pocket or check a wall.
- **Isometric, top, front, right, bottom** are fixed views for checking a face straight on.
- **Parts on the plate** lists each piece with its size in millimetres, and lets you hide one to see behind it.
- **Report** shows the full build report: every part, every wall thickness, every parameter used.

## Checking the numbers

Hold the measurement sheet next to the real object and check, in this order:

1. **The overall size.** Will it physically go where it has to go?
2. **The openings.** Is every hole, slot and window in the right place, and big enough for the plug or screw you actually own?
3. **The assumptions.** Anything the quote says was assumed is a number nobody measured. If one is wrong, say so now.
4. **The material and colour.** They are on the quote; change them at no cost before printing.

## The estimate

The price is two numbers. The **print price** comes from the design's geometry: the weight of plastic, the hours on the printer and the handling. The **design fee** is flat and says how much was new: nothing for an existing design or your own file, {price.design_adapt} when an existing design or the library parts were fitted to your object, {price.design_fee} when it was drawn from scratch. Rates and worked examples are on *Prices and turnaround*; what the library is and why it makes design cheap is on *Designed from proven parts*.

::: warn Estimates versus the slicer
Print time and weight are calculated from the model. When the part is prepared for the printer the real numbers can differ a little. If they differ by more than a little, you are told before it is printed — the price on your quote does not go up afterwards.
:::
