# From a brief to build123d geometry

A brief describes a look in a fixed vocabulary. This table is the translation into operations,
with the print rule that limits each. Ratios in a brief are scaled by one absolute dimension the
user or the hardware gives (height, the pot it must hold, the bulb it must clear).

## Form words → primary solid

| brief says | build with | print rule |
|---|---|---|
| cylindrical, tapered, bulbous shoulder, waisted, bell, urn | `revolve` of a 2D profile (polyline + `Spline`/`Bezier` for curves) about Z | shoulder overhang ≤ 45° from vertical prints without supports; steeper needs the bulge reduced or the part split at the widest point |
| faceted, polygonal, crystal, low-poly | `revolve` a profile with a `RegularPolygon` section, or `loft` between polygons rotated per station | flat facets show layer lines at low angles; keep facet tilt ≥ 30° or accept the texture |
| lofted, transitions from square to round, twisted | `loft([section_bottom, ..., section_top])`, rotate sections per station for a twist, `ruled=True` for crisp edges | a twist increases overhang at the corners; check with `check_printable.py` |
| stepped, tiered, ziggurat | stack of extrudes with decreasing outline, or one profile with steps in `revolve` | each step needs ≥ 1 perimeter of horizontal landing to print clean |
| organic, blobby, pebble | `revolve`/`loft` of spline profiles, generous `fillet` on every edge, or an `Ellipsoid`-like sweep | bottom must be flattened (cut below a plane) for a bed face |
| swept, ribbon, coiled | `sweep(profile, path)` along a `Spline`/`Helix` | check the lowest point of the path; a sweep that dips below the bed plane is a support problem |
| hollow / vessel | `offset(amount=-wall, openings=top_face)` after the outer form, or revolve the wall profile directly | wall ≥ 1.2 mm at the thinnest point of the taper; vase-mode prints want a single continuous perimeter |

## Surface words → secondary operation

| brief says | build with | print rule |
|---|---|---|
| ribbed, fluted, reeded, vertical ribs | polar pattern (`PolarLocations(r, n)`) of a small extruded profile, fused (ribs) or cut (flutes) into the body; taper the rib with the body by revolving the rib section too | rib width ≥ 2 nozzle widths (≥ 0.9 mm); rib count so that the gap ≥ 1 mm at the narrowest diameter |
| horizontal rings, grooves, coil marks | grooves in the revolve profile itself (small notches in the polyline) | groove depth ≤ wall/2; keep the undercut face ≤ 45° |
| spiral, twisted ribs | ribs built straight then the body `loft`ed with per-station rotation, or a `Helix` sweep cut | steeper spirals mean more overhang on the trailing face |
| faceted surface, hammered, dimpled | pattern of small cuts (`Sphere` / `Cone` at `HexLocations`) on a revolved body | dimple depth < wall - 0.8 mm; a dimple that breaks through is a hole |
| perforated, lattice, pierced | `HexLocations` / `GridLocations` of `Circle`/`RegularPolygon` cuts through the wall | bridge the top of every hole: round holes ≤ 8 mm print without support; larger want a teardrop or hex |
| chamfered edges, crisp | `chamfer(edges, length)` on the selected edges | chamfers on the bed edge (elephant-foot chamfer 0.4–0.6 mm) always help |
| soft, rounded, pillowed | `fillet(edges, radius)` | fillet on the top of a bed-down part fine; fillet at the bed edge creates a small overhang, ≤ 1 mm is safe |
| woven, basket | two families of sweeps along sinusoidal `Spline` paths | many small overhangs; treat as decorative only above 0.3 mm layer |
| textured, matte, grainy | not geometry: note it for the slicer (fuzzy skin) in the model docstring | — |

## Feature words → detail

| brief says | build with |
|---|---|
| lip, rolled rim, flared mouth | last segment of the revolve profile bends outward; a rolled rim is a small circle fused at the top of the profile |
| foot, plinth, pedestal | a shorter revolve or extrude fused under the body, slightly wider than the body's base for stability |
| handle, lug, ear | `sweep` of an ellipse along an arc, fused; orient so the handle prints as a bridge (both ends on the body) or add it as a separate part with a fastener from `lib/` |
| recessed panel, inset band | cut of an offset outline, depth ≤ wall/2 |
| a repeated motif around the body | `PolarLocations` of the motif sketch, projected/cut; count chosen so the motif width stays ≥ 2 mm at the smallest radius |

## What the print notes in a brief mean for orientation

- "base on the bed" → the widest flat face down; if the widest point is the shoulder, a vase still
  goes base-down and the shoulder is kept under 45°.
- "supports under the shoulder / handle" → redesign before accepting supports on a decorative
  surface: split the part at the widest point (lid + body), flatten the angle, or turn the
  overhang into a chamfer.
- "thin ribs" → widen to ≥ 0.9 mm or reduce the count; a rib is a wall and obeys the wall rule.
- "hollow" → decide vase mode (single wall, no top) vs. shelled solid (wall ≥ 1.2 mm, drain hole)
  in the idea's Constraints; it changes the profile.

## Library first

Decorative parts still reuse: `primitives.*` for the box or the lid the decoration sits on,
`mechanisms.*` for any latch or hinge, `fasteners.*` if a lamp base needs a cord grommet or a
screw. Check the overview (`scripts/studio.py`) and put every library component in the idea's
reuse map; the decoration itself is usually model-local geometry unless it appears twice, at
which point it is a `patterns.*` candidate (e.g. `patterns.ribbed_shell(profile, n, rib)`).
