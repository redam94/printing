---
name: design-references
description: >-
  Find 3D models online and file them as design guides for new parts, especially mechanisms whose
  behaviour is hard to predict from first principles (bistable switches, snap-through buckles,
  living hinges, flexure stages, print-in-place latches, compliant grippers): search Printables,
  GitHub, Sketchfab and Thingiverse from scripts/references.py, the rest of the web with the
  web-search tool; file a reference next to a model or an idea as references/<id>.md with the page
  read, the numbers measured off its mesh (beam thickness, hinge thickness, min wall, per-slice
  members) and a SMALL-model reading (mechanism, principle, key dimensions, features to borrow,
  build123d hints, library map). ALWAYS use this skill when the user asks to find, look up, search
  for, or "see how others did" a part or mechanism; says "there must be one on Printables /
  Thingiverse"; pastes a model URL or an STL they downloaded; asks what references are attached to
  a model or idea; asks how a bistable / snap / compliant / flexure part is usually dimensioned; or
  when the Studio overview lists a reference with "READING PENDING". Use it before design-studio
  sketching of a mechanism and before printable-parts adds a new mechanism to the library.
---

# Design references: models found online, read into numbers, filed next to the part

A photo says what a part should look like; a reference model says how a part that already prints
was built. For a compliant mechanism that is the difference between guessing a beam thickness and
reading one off a mesh that a thousand people have printed. This skill finds such models, files
each one next to the model or idea it guides, measures its mesh when one can be had, and has a
small model write a fixed-shape reading so later sessions read text, not pages. Run everything
from the repo root with `uv run python ...`.

Where things live:

| what | where |
|---|---|
| reference attached to a model | `models/<project>/references/<id>.md` |
| reference attached to an idea | `ideas/<slug>/references/<id>.md` |
| downloaded meshes, page images, renders | `.../references/files/` (gitignored: licences and size; the sidecar records the URL to refetch) |
| the reading prompt (single source) | `READING_PROMPT` in `scripts/references.py`; `references.py prompt` prints it |
| where to look | `references.py sources` and `references/sources.md` |

The sidecar is front matter (`id`, `target`, `created`, `source`, `url`, `title`, `author`,
`license`, `why`, `files`, `images`, `reading_model`, `tags`) plus `## Page` (what the site says),
`## Measurements` (numbers off the mesh), `## Reading` (the small model's structured reading) and
`## Log`. `reading_model: pending` means nobody has read it yet; the Studio overview lists those
under ATTENTION.

## The two rules

**Say why before you search.** A reference is filed with a `--why` line: the question it should
answer ("how thick are the beams of a printed bistable toggle and which way does it print").
Searching without a question fills the repo with bookmarks; the reading is written to answer the
why, and the log records whether it did.

**Do not read pages and pictures yourself when a small model can.** The page text is cheap and
`references.py show <url>` prints it; read that to decide whether a hit is worth filing. The
pictures and renders are not cheap: a Haiku subagent reads them with the prompt from
`references.py prompt` and the reading is what gets committed. Look at an image yourself only when
the user asks you to, and say what it costs in one line.

## Step 0: what is filed, what is waiting

```
uv run python scripts/references.py            # every reference by target, READING PENDING flagged
uv run python scripts/references.py pending    # just the ones without a reading
```

Clear pending readings first (the reading section below); they are cheap and the user expects a
filed reference to have been read.

## Finding references

Start with the question, then pick the sources for it (`references/sources.md` has the per-kind
list and the search phrases that work):

```
uv run python scripts/references.py search "bistable compliant switch" [-n 8] [--source printables|github|sketchfab|thingiverse]
uv run python scripts/references.py show <url>            # title, author, licence, files, images, description; nothing filed
uv run python scripts/references.py sources               # where else to look, and how
```

`search` asks the sites that answer without a key: Printables (functional prints with print
settings in the description, and the makes count that says it actually prints), GitHub (source
models: OpenSCAD, build123d, CadQuery, FreeCAD, where the parameters are visible), Sketchfab
(look at a mechanism from every side), and Thingiverse when `THINGIVERSE_TOKEN` is set. For
everything else use the web-search tool with `site:` filters: `site:thingiverse.com`,
`site:thangs.com`, `site:cults3d.com`, `site:myminifactory.com`,
`site:compliantmechanisms.byu.edu` (the BYU Compliant Mechanisms Research maker library; its
bistable, LET-joint and ortho-planar demos are the canonical printable examples), and YouTube for
build videos. For the equations behind a mechanism (snap force vs beam geometry, fatigue vs
material) use the alphaXiv tools.

Judge hits by: does the description state material, orientation and a dimension; how many makes
or print photos; is the source file (not just the STL) available; what the licence allows.
Present two to four candidates with the URL, the licence, whether the mesh can be downloaded, and
one line on what each would answer. Do not file ten.

## Filing

```
uv run python scripts/references.py add <url> --model <p> | --idea <slug> | --new "<title>" --why "..." [--download <direct file url>] [--file <mesh>]
uv run python scripts/references.py attach <references/<id>.md> <mesh.stl> [--scale 25.4]
uv run python scripts/references.py add <mesh.stl> --idea <slug> --why "..."      # a file the user handed you
```

`add` reads the page, writes the sidecar, downloads the page images (downscaled) into `files/`
for the reader, fetches any `--download` link (GitHub blob links are converted to raw), attaches
and measures any mesh, and prints the next step. `--new` creates `ideas/<slug>/IDEA.md` with
`status: inbox` so a reference never floats free. Re-adding the same URL refreshes the page read
and keeps files, measurements, reading and log.

Downloads: Printables and Thingiverse require a login. Tell the user which file to save and where
the `attach` command goes; do not try to log in. GitHub files and any direct link fetch by
themselves. Respect the licence recorded in the sidecar: a reference is a guide for a part of
the user's own design, not a mesh to copy into `models/`; NoDerivatives and NonCommercial terms
are noted so the user can decide.

## Measuring

`attach` (and `add --file`) runs the repo's printability check plus a per-slice member analysis on
the mesh and writes `## Measurements`:

- bbox, volume, watertightness, bodies, min wall by the inward-ray metric, overhang fraction, bed
  contact (the printed orientation, if the file is in print orientation);
- five Z slices, each with island count, area, **thinnest member** (the smallest inset whose
  morphological opening loses material: the flexure beam) and **thickest member** (the largest
  inscribed disc: the hub or block);
- a units warning when the extents look like inches or metres (`--scale 25.4`).

Members are read per Z slice as the mesh sits. If the flexing members lie in XZ (a hinge printed
standing up) rotate a copy first, or read the min wall figure instead. `references.py measure
<mesh>` gives the same table for any mesh without filing it; use it on the user's own downloads
and on a sketch export to compare against the reference.

## The reading (small model)

For each pending sidecar, launch one Haiku subagent (several in one message when there are
several) that: runs `references.py prompt` and treats it as its instructions; reads the sidecar
(the `why` line and the Page and Measurements sections); Reads every image in `files/` named in
the sidecar's `images:` list (page photos and the render); writes only the JSON object to a file.
Then:

```
uv run python scripts/references.py set-reading <references/<id>.md> --json <reading.json> --model "haiku subagent"
```

`set-reading` refuses a reading with no subject, mechanism, features or key dimensions, so a
failed read stays pending instead of committing an empty one. Readings distinguish `(measured)`,
`(page)` and `(estimated)` dimensions; when the reading has only estimates and the mesh is
downloadable, say so and offer the attach step, because a measured beam thickness is the number
the user came for.

## Using references in design

Read the sidecars of the target (`cat ideas/<slug>/references/*.md`) and
`references/reading_a_mechanism.md`, which says which numbers govern each mechanism family and
how to turn a reading into library parameters and a sketch. Then:

1. **Quote the reading's key dimensions and features to borrow before touching geometry**, and
   say which are measured and which estimated. The `why` line is the question; answer it first.
2. **Map to the library.** The reading's `Library map` names the component the reference
   resembles (`mechanisms.living_hinge`) or a gap (`gap: mechanisms.bistable_beam`). Put those in
   the idea's `reuse:` / `gaps:` (design-studio skill); a mechanism that two references share and
   the library lacks is the next component to write.
3. **Sketch it at the reference's numbers first** (`scripts/sketch.py`), then vary. A compliant
   mechanism sketched at a known-good thickness and angle is a test print away from a decision;
   one sketched from theory is three. Compare `references.py measure` on the sketch's STL with
   the reference's table.
4. **Respect what the page says failed.** Print notes carry the author's material and
   orientation; a mechanism validated in PP or PETG is not validated in PLA, and the component's
   `material_notes` must say so when it lands in the library.
5. **Log what was taken.** When a number or feature from a reference lands in a sketch, model or
   component, add a line to the sidecar's log (`references.py log <md> "beam 1.2 mm and 8° used in
   bistable_toggle sketch round 1"`) so the next session knows which references have been mined.

## Report

Say what was searched and where, which candidates were shown and why, what was filed (path,
target, licence, whether the mesh was attached and measured or needs a manual download), which
readings were written and which are still pending, and what the reading answered about the why.
When designing from references, list the borrowed numbers and features first, marked measured or
estimated, then the geometry. If nothing is pending and nothing was asked, one line.
