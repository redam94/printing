---
title: Sending your own file to print
order: 10
summary: Formats, units, and the checks a file goes through before it is printed.
---

Already have a model? Choose **Print my file** on the portal and attach it under *Photos*.

## Accepted files

| Format | Notes |
|---|---|
| STL | The usual export from any 3D program. Send it in millimetres |
| 3MF | Preferred where you have it: it carries units and colours reliably |
| STEP | A CAD file; good, and it can be adjusted if something needs changing |
| OBJ | Accepted, but check the scale — OBJ carries no units |

Zip several files together if the model has more than one piece, and say which pieces go together.

## Tell us

- **How many** of each piece.
- **Material and colour**, or what the part is up against so one can be recommended.
- **Which way up**, if it matters for strength or looks. Otherwise it is oriented for the best result.
- **Whether it has been printed before**, and what went wrong if it did.
- **Where it must be accurate**: the dimension that has to be right for it to fit.

## What happens to your file

It is measured and checked before printing:

1. **Size:** it has to fit in {printer.bed}, or be split.
2. **Scale and units:** a model exported in inches or centimetres arrives 25.4 or 10 times the wrong size. Anything suspicious is queried rather than guessed.
3. **Watertight geometry:** meshes with holes, flipped faces or loose fragments are repaired where possible; you are told what was changed.
4. **Printability:** thin walls, steep overhangs and tiny features are flagged. Nothing is silently altered — if the model needs a change to print, you get a message.

You still get a quote with the measurements and the price before anything is printed.

::: tip Files from Printables, Thingiverse and friends
Downloaded models are fine, as long as their licence allows printing and you are not reselling the result. Send the link along with the file so the licence and any printing notes come with it.
:::
