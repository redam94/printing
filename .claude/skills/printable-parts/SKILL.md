---
name: printable-parts
description: >-
  Design, modify, inspect, and export 3D-printable parts as parametric build123d scripts backed by
  this repo's shared, versioned component library (lib/, PARTS.md, parts.json). ALWAYS use this skill
  when the user mentions designing or printing an enclosure, case, box, bracket, mount, holder, adapter,
  spacer, standoff, jig, fixture, clip, latch, hinge, lid, cover, grommet, or stand; wants an STL, STEP,
  or "something I can print"; asks to change, tweak, resize, or re-export a part designed here; asks
  what components, patterns, mechanisms, or parts are already in the library; wants to add, promote,
  version-bump, or change a library component (and see what models it affects); or mentions build123d,
  CadQuery-style scripting, heat-set inserts, Raspberry Pi / ESP32 / fan / VESA / DIN-rail mounting.
  Trigger even for casual phrasing ("can you knock up a little box for this sensor") — the point of the
  skill is that Claude checks the library BEFORE freehanding geometry that already exists.
---

# Printable parts: parametric build123d + shared library

You are working in a monorepo of printable parts. `lib/` holds versioned, metadata-carrying
components; `models/<project>/` holds printable assemblies that import them; `scripts/` does the
building, checking, rendering, exporting, indexing and impact analysis. The generated `PARTS.md`
(human) and `parts.json` (machine: import path, file, line, `used_by`) are the catalogue.

**The one behaviour that matters most:** look for an existing component before writing geometry,
and promote anything reusable back into `lib/`. The library only stays useful if every design
passes through it. Freehanding a Pi hole pattern in a model file is a bug even if the numbers are right.

Run everything with `uv run python ...` from the repo root (a `.venv` exists; `uv run` uses it).

## Step 0, always: read the catalogue

Read `PARTS.md` before designing anything, even when you are confident nothing relevant exists.
For any component you plan to use, open `parts.json` for the `import` line and `file:line`, then
read the source so you know its coordinate convention (patterns are centred on the hole-pattern
origin; "negative" components are cutters whose surface sits at z=0; bosses stand on z=0).

If the user asks *what they already have* ("what compliant mechanisms do I have?"), answer from
`PARTS.md`: list id, version, summary, validated materials and orientation, grouped by category.
Do not guess or pad with things that are not there.

## Workflow for a new part

1. **Search and report reuse.** Say which existing components you will use, by id, and which parts
   of the request have nothing in the library yet. Do this before writing code.
2. **Ask about constraints that matter** (skip anything already given): overall envelope or the
   hardware it must fit, screw/insert sizes, connector cutouts, which face sits on the bed,
   material (PLA vs PETG changes compliant parts). If the user is not available, state your
   assumptions explicitly in the model docstring and in your report, and pick the defaults in
   `references/design_rules.md` and `references/hardware_dimensions.md`.
3. **Write the model.** Create `models/<project>/` with `__init__.py`, `params.py` and `model.py`:
   - `params.py` is the PARAMETERS block. Every dimension, count, size string and clearance lives
     there as an UPPER_CASE constant with a units comment. Derive values (`OUTER_L = INNER_L + 2*WALL`)
     rather than repeating numbers.
   - `model.py` starts with `from .params import *` / `from . import params as P`, imports
     components from `lib.*`, and defines `build() -> dict[str, Part]` mapping each print part to a
     solid **in print orientation with the bed at z=0** (use `lib.component.on_bed`, `Rot(180,0,0)`
     for lids). No numeric literals in `model.py` except 0/1/2/±1/0.5 and right angles;
     `scripts/lint_models.py` enforces this and flags inlined hole patterns and hardware-sized holes.
   - `fit_checks(parts) -> dict[str, tuple[Shape, Shape]]` (optional but expected for anything with
     two parts or enclosed hardware): pairs that must not intersect once assembled, e.g. the lid
     placed back on the body, or a PCB envelope (footprint extruded by board + component height)
     against the body. `build.py` intersects each pair and fails on overlap. The printability check
     looks at one part at a time and cannot see a boss colliding with a lid lip or a PCB corner;
     both of those happened in the seed model before this hook existed.
   - Module docstring: what the parts are, what hardware they fit, which face is on the bed, and
     any assumptions you made.
   - See `references/build123d_cheatsheet.md` for the 0.11 idioms that work here (algebra API,
     `is_valid` is a property, `Plane.XZ` mapping, selecting edges).
4. **Build it:** `uv run python scripts/build.py <project>`. This runs the model, prints bbox and
   volume per part, runs the printability check, exports STL + STEP to `models/<project>/exports/`,
   renders `exports/renders/<part>.png` (isometric + top + front) and writes or diffs the golden
   metrics in `tests/regression/<project>.json`. **Open each render PNG with Read and look at it.**
   Misplaced cutouts and features running out of a wall are obvious in the picture and invisible in
   the numbers.
5. **Report** bounding box and volume for each part, the printability result, fit-check results,
   and anything the check flagged (thin walls, overhangs, flat ceilings, multiple bodies). Fix real problems before
   moving on; explain the warnings you are accepting and why.
6. **Goldens.** A new model gets its golden written automatically on first build. When you change
   a model on purpose, rebuild with `--update-golden`. Never update a golden to make a failure go
   away without saying what changed.
7. **Promote.** If anything you wrote is generalizable (a hole pattern, a fastener detail, a cutout
   used twice, a bracket shape with obvious parameters), propose moving it into `lib/` with the
   metadata below, do it if the user agrees (or if it is clearly library-shaped and you are working
   autonomously), then `uv run python scripts/reindex.py` and rebuild the model against the library
   version. A component you write today and forget tomorrow is why the index exists.
8. **Tests:** `uv run python -m pytest -q` before you call the work done.

## Modifying an existing part

Change `params.py` (or the model) and rebuild. Read the golden diff: it tells you exactly which
parts changed and by how much. Update the golden only when the change is the intended one.
If the modification is really a library gap ("the boss needs a fillet"), fix the library (next
section) instead of working around it in the model.

## Library rules

- **Never write new geometry for something that already exists.** Search `PARTS.md` by tag and
  summary first. Same hardware, same feature → same component.
- **Close but not exact? Add an optional parameter that defaults to the current behaviour.** Do
  not fork a component or copy its body into a model. Adding a parameter is a *minor* bump.
- **Never inline a hole pattern or fastener detail in a model file.** If it will plausibly be used
  twice, it belongs in `lib/`. The lint flags `GridLocations` with literal spacing and hardware-sized
  `Cylinder`/`Circle` calls in models.
- **Every component** is a function decorated with `@component(...)` from `lib.component` and has a
  docstring with an `Example:` block. The decorator records:
  `id` (`<category>.<name>`, category in patterns / mechanisms / fasteners / primitives), `version`
  (semver, per component), `summary` (one line), `params` (derived from the signature; you pass
  `units={...}` for every parameter and optional `descriptions`), `tags`, and `material_notes`
  (`MaterialNotes(validated=[...], orientation="...", notes="...")`). Import-time validation fails
  on missing units or bad ids, so run the module after writing it.
- **Compliant mechanisms** (latches, hinges, flexures, snaps) must state validated materials and
  the required print orientation; a cantilever that works in PETG snaps in PLA, and flex depends on
  layer direction. Untested geometry says `UNVALIDATED` in `notes`.
- **Negative components** (things you subtract) say so in their summary and put the cut surface at
  z=0 so `Pos(x, y, surface_z) * cutter` reads naturally.
- **Hardware numbers** come from `lib/fasteners/hardware.py`, which mirrors
  `references/hardware_dimensions.md`. Update both together and cite a source.
- **Reindex in the same commit as any `lib/` change:** `uv run python scripts/reindex.py`.
  `tests/test_index_fresh.py` and the pre-commit hook fail on a stale index; treat that as a bug.

## Versioning and impact

Semver per component, independent of the repo:

| bump | when | example |
|---|---|---|
| patch | tolerance, comment, docstring; geometry unchanged at default parameters | tighten a clearance note |
| minor | new optional parameter, defaults preserve existing geometry | `active_cooler_holes=False` |
| major | default geometry changes | boss wall 1.6 → 2.4 |

Before any **major** bump (and any hardware-table change), run

```
uv run python scripts/impact.py <component-id>
```

It reads `used_by` from `parts.json`, rebuilds every affected model, and diffs bbox, volume,
watertightness and mesh hash against the goldens. Report to the user which models changed and by
how much (the script prints deltas). **Ask before accepting new goldens** — those goldens describe
parts that have already been printed and fit. Only after the user agrees run
`scripts/impact.py <id> --accept` (or `scripts/build.py <project> --update-golden` per model).
If the user wants the new default only for one project, the answer is a parameter on the model
side, not a golden update.

`scripts/impact.py --all` re-checks every model; run it after touching shared code.

## Commands

| task | command |
|---|---|
| build, check, export, render, golden | `uv run python scripts/build.py <project> [--update-golden]` |
| render only | `uv run python scripts/render.py <project>` |
| printability only | `uv run python scripts/check_printable.py <project>` or `--stl file.stl` |
| regenerate catalogue | `uv run python scripts/reindex.py` (`--check` to verify) |
| impact of a component change | `uv run python scripts/impact.py <component-id> [--accept]` |
| lint models for magic numbers / inlined patterns | `uv run python scripts/lint_models.py` |
| full test suite | `uv run python -m pytest -q` |

## References (read when relevant)

- `references/design_rules.md` — FDM rules: hole oversize, fits, wall multiples, overhangs,
  orientation, enclosure defaults. Read before writing geometry the library does not cover.
- `references/hardware_dimensions.md` — verified Pi 4/5, Pi Zero, ESP32, metric fastener,
  heat-set insert, VESA, DIN rail, fan and connector dimensions with sources and UNVERIFIED flags.
- `references/build123d_cheatsheet.md` — the build123d 0.11 API idioms and gotchas that are
  known to work in this repo.

## Reporting

Lead with what was reused and what was new. Then per part: bbox, volume, printability verdict,
export paths, render path. Then any assumptions, warnings accepted, and promotion proposals with
the proposed id, parameters and version. Keep numbers in a small table.
