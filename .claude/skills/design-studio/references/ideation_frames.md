# Ideation frames

Use two or three of these per session, chosen by what the user said. Every frame ends in the same
shape of output: a candidate with a problem, a one-sentence concept, a reuse map of component ids
from the overview, and the gaps. Read the overview first; the frames are ways of reading it.

## 1. Hardware on the bench
Start from the physical things the user has named (boards, fans, sensors, tools, cables, a
specific shelf). For each: what does it need to be held, protected, mounted, routed, or kept from
moving? The library already knows Pi 4/5/Zero, ESP32, 30–40 mm fans, VESA, DIN rail, heat-set
inserts and M2–M5 screws (see `hardware_dimensions.md`); a part for hardware that is already in
the table is mostly assembly. Hardware that is not in the table is itself a candidate: a
`patterns.<board>_mount` or `<connector>_cutout` component, measured once, used forever.

## 2. Unused components are one model away
The overview lists components no model uses. Each is a small bet the library made that has not
paid off. Ask what the *first* model to use it would be, and whether that model is useful on its
own: a DIN-rail clip for the sensor box makes `patterns.din_rail_ts35_profile` earn its place and
validates it in the same print. Prefer models that use two or three unused components at once.

## 3. Gap-first (library roadmap)
Collect `gaps:` across every idea. A gap wanted by three ideas is the next library component to
write, independent of which idea goes first. Propose it with parameters and a version, and note
which ideas it unblocks. This is the frame for "what should I build next" when the user means
the library rather than a printed thing.

## 4. Variation of an existing model
Every model is a family: the same enclosure for a different board, the same bracket at 60 mm,
the same lid with a snap instead of screws. Read the model's `params.py` (the overview shows how
many parameters it has) and ask which single parameter change produces a part someone would
actually want. Variations are cheap (reuse map is the whole existing model) but only worth
filing when there is a real reason for the variant.

## 5. Pain points in what exists
Read the models' review pages' open notes (via each `review.json` URL and `read_db` on `notes`)
and the ATTENTION list. A recurring critique ("lid lip binds", "boss too close to the wall") is a
library idea: a clearance parameter, a fit-check helper, a better default. Promotion candidates
(two models writing the same private helper) live here too.

## 6. Remix
Take two components from different categories that have never appeared together and ask what
part they make: living hinge + snap ridge = a clamshell case; parallel flexure + captive nut = an
adjustable stop; teardrop + cable grommet = a horizontal cable pass-through. Remixes are where
new *kinds* of parts come from; most will be silly, one in five will not.

## 7. Print-process ideas
The target printer has four toolheads. Which existing models would be better as two materials
(TPU feet, a PETG body with a PLA-coloured badge, soluble support for a bridge)? Which parts
are limited by orientation (a hinge that would be stronger printed a different way) and would
benefit from being split into two parts? These are `modification` kind ideas.

## What makes a candidate worth filing

- The problem is concrete (a thing, a place, a failure), not "an enclosure for something".
- The concept names which face is on the bed and how it comes apart.
- The reuse map uses real ids from the overview; each gap has a proposed id and a sentence on why
  it is library-shaped (would be used twice).
- Its cost is legible: mostly reuse = small; one gap = medium; new mechanism = large.
- It is not already in `ideas/` under another name, and not `parked` with a reason that still holds.

## Questions worth asking before filing (skip what is already known)

- What does it hold or attach to, exactly (model number, or a photo's worth of dimensions)?
- Where does it live: desk, wall, rail, inside something else? Which way is up in use?
- Does it need to open, flex, slide, or come apart? How often?
- Material on hand (PLA / PETG / TPU) — compliant mechanisms depend on it.
- Is this one print or a family (several sizes, several boards)?

If the user is not available, file with `status: inbox` and the questions listed under
`## Open questions`; the answers are what turns it into `status: idea`.
