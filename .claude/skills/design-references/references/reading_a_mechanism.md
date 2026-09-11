# Reading a reference into numbers, and numbers into a part

A reference's reading has five parts worth acting on: the mechanism family, the principle, the
key dimensions (measured / page / estimated), the features to borrow, and the library map. This
file says which numbers govern each family, how to check them against the measurements table,
and how they become build123d parameters and a sketch. FDM rules that constrain everything are in
the printable-parts skill's `references/design_rules.md`; the library's existing mechanisms are
`mechanisms.living_hinge`, `mechanisms.parallel_flexure`, `mechanisms.cantilever_latch`,
`mechanisms.latch_window` and `mechanisms.snap_fit` (check `parts.json` for current versions).

## What governs each family

| family | the numbers that decide behaviour | where to read them |
|---|---|---|
| bistable toggle (pseudo-rigid-body four-bar, two angled beams or a curved beam pair) | beam thickness t, beam length L, beam angle to the line of travel (the pre-tilt that makes it bistable; small angle = weak snap, large = stiff), hub/shuttle width, stop positions | thinnest member per slice = t; slice extent and the render give L and the angle; stops are the thickest members near the ends |
| snap-through clip / buckle (a precompressed arch) | arch thickness t, chord length, rise (arch height above the chord: rise/t sets whether it snaps or just bends), end fixity (clamped vs pinned) | thinnest member = t; slice bbox = chord and rise |
| living hinge | hinge thickness (2–3 layers at 0.2 mm is the printed norm: 0.4–0.6 mm), hinge length along the fold, hinge width (short = stiff, long = floppy), radius or relief at the root, count of hinges in series | min wall (inward ray) = hinge thickness when printed flat; the page usually states layers and material |
| parallel flexure / linear stage | beam thickness t, beam length L, beam count, beam spacing, depth (Z height); stiffness ∝ N·depth·t³/L³ so t is the whole story | thinnest member = t; slice extent along the beam = L; thickest = blocks |
| cantilever snap / latch | beam thickness, beam length, hook height (the deflection), lead-in angle, retention angle, root fillet | thinnest member = beam; hook height from the render or the slice at the hook |
| cross-axis / LET rotary joint | leaf thickness, leaf length, number of leaves, the crossing angle | thinnest member = leaf |
| compliant gripper (fin-ray, four-bar) | rib thickness and spacing, side-wall thickness, the taper | thinnest members; slice count of islands shows the rib count |

For every family, thickness is the number to get right first and it is a multiple of the nozzle
line width: a 1.2 mm beam is three 0.4 mm lines, a 1.0 mm beam is two and a half (the slicer
will make it two or gap-fill it). Round to line multiples in the sketch and say so.

## Checking the reading against the measurements

- `thinnest member across slices` is the flexing member's thickness only if the member lies in
  the XY plane of the mesh as filed. A hinge printed standing up shows as `min wall` instead.
- If the reading says "estimated" for a dimension the table measures, the table wins; note it in
  the log.
- `bed contact` is the face the author put down if the mesh is in print orientation; a mesh
  exported in modelling orientation can put it anywhere, so read the page's print notes too.
- Islands per slice count separate members at that height: a bistable switch reads 3 to 5
  islands at mid-height (two beams, shuttle, stops).

## From reading to parameters

1. Write the mechanism as the library would: one function, print orientation baked in, every
   governing number a parameter with units and a description, `material_notes` naming what the
   reference validated (the page's material, not yours until you print it).
2. Default the parameters to the reference's measured numbers, rounded to line multiples; the
   reference's proportions (L/t, angle, rise/t) are the ratios to keep when the user scales it.
3. Sketch at those defaults (`scripts/sketch.py --new <slug>`), export the STL and run
   `references.py measure` on it: the thinnest / thickest members should match the reference's
   table before you change anything.
4. Print a coupon before the part: for a bistable or snap-through mechanism the test is "does it
   snap and does it come back after 50 cycles"; for a living hinge "how many folds before
   whitening"; for a flexure "stroke before yield". Record the print through the review page so
   `lib/validation.json` gains the evidence.
5. Promote to `lib/mechanisms/` once the coupon printed and the model builds against it (the
   printable-parts skill's library rules); put the reference URL in the component docstring.

## Compliant mechanism cautions the pages tend to omit

- PLA creeps and fatigues: a bistable toggle that lives in one state for a month may not snap
  back. PETG, PP and nylon are what the reference designs are validated in; say UNVALIDATED for
  PLA unless the page or a print report says otherwise.
- Layer adhesion is the weak direction. Flexing members must lie in the bed plane so bending
  stress runs along the extrusion lines; a member standing up bends across layers and cracks.
- Overhang rules still apply at the hub: an angled beam meeting a block at 20° from vertical is
  fine; a beam meeting it horizontally is a bridge.
- Root fillets (0.3–0.5 mm) at every member root are cheap and remove the stress riser; readings
  often list them under features to borrow.
