# ideas/ — the space between "what if" and `models/`

One directory per idea: `ideas/<slug>/IDEA.md` (the write-up), optionally `ideas/<slug>/sketch.py`
(a throwaway build123d sketch run with `scripts/sketch.py <slug>`) and `ideas/<slug>/exports/`
(gitignored renders and meshes from the sketch). The Studio page (`scripts/studio.py`) shows every
idea on a board next to the library and the models, and its inbox lets you jot new ideas from the
browser; Claude files those into directories here.

Nothing under `ideas/` is indexed, linted or golden-checked. Sketches may freehand geometry; the
`reuse:` list in the write-up is what turns a sketch into a model.

## IDEA.md format

```markdown
---
title: Lid skirt tab with latch window
status: sketching            # inbox | idea | sketching | prototyping | promoted | parked
kind: library                # part | library | modification
created: 2026-09-07
updated: 2026-09-07
tags: [lid, snap, latch]
hardware: []                 # boards, fans, fasteners it must fit (free text list)
reuse: [mechanisms.latch_window, primitives.box_lid]   # existing component ids (checked by tests)
gaps: [mechanisms.skirt_tab]                            # components that would need to exist
model:                       # models/<project> once promoted (checked by tests)
---

## Problem
One paragraph: what is this for, who / what does it hold, why the current thing is not enough.

## Concept
The shape in words. Which face is on the bed. What flexes, what screws, what slides.

## Constraints
Envelope, hardware, material, orientation, must-fit / must-not-touch.

## Reuse map
| need | component | notes |
|---|---|---|
| lid body | primitives.box_lid | as is |
| latch window | mechanisms.latch_window | needs a lead-in chamfer parameter (minor bump) |

## Gaps
What has to be written. Proposed id, parameters, and why it is library-shaped (used twice?).

## Open questions
- things only a test print or the user can answer

## Log
- 2026-09-07 captured from pi5_fan_case eval runs
```

Statuses mean:

| status | meaning | where the work lives |
|---|---|---|
| inbox | captured, not yet thought through | Studio page db, or a bare IDEA.md |
| idea | written up: problem, concept, reuse map | IDEA.md |
| sketching | form exploration | sketch.py + `scripts/sketch.py <slug>` |
| prototyping | real model in `models/<project>` being iterated / test printed | models/ (`model:` set) |
| promoted | shipped as a model or library component | models/ or lib/ |
| parked | not now; keep the reasoning | IDEA.md |
