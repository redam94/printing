# build123d 0.11 cheatsheet (algebra API, verified in this repo)

Use the **algebra** style (operators), not Builder contexts, so components compose as values.

```python
from build123d import *
```

## Objects and placement
```python
Box(l, w, h, align=(Align.CENTER, Align.CENTER, Align.MIN))   # stand on z=0
Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
Cone(r_bottom, r_top, h)
Rectangle(w, h)  RectangleRounded(w, h, r)  Circle(r)  SlotOverall(len, w)
RegularPolygon(radius, n, major_radius=True, rotation=30)   # hex, flats parallel to X
Polygon((x1,y1), (x2,y2), ...)            # pass points as separate args
Pos(x, y, z) * shape        Rot(rx, ry, rz) * shape      Location((x,y,z)) * shape
Plane.XZ * sketch           # map an XY sketch onto the XZ wall; sketch +Y becomes world +Z
Plane.XY.offset(z) * sketch
extrude(sketch, amount=h)           extrude(sketch, amount=h/2, both=True)
extrude(sketch, amount=-h)          # extrude downward
```
Sketch/Part results can be combined with `+`, `-`, `&`. A list works too:
`part - [Pos(x,y,0) * hole for x, y in pts]`.

## Selecting edges/faces
```python
part.edges().filter_by(Axis.Z)             # vertical edges
part.edges().filter_by(Axis.Z, reverse=True)
part.edges().group_by(Axis.Z)[0]           # lowest loop(s)   [-1] = highest
part.faces().sort_by(Axis.Z)[-1]           # top face
part.faces().sort_by(Axis.Z)[0].outer_wire().edges()   # bed edge loop
edges.sort_by_distance((x, y, z))[0]
fillet(edges, r)      chamfer(edges, length)
```

## Properties (0.11 specifics)
- `shape.is_valid` is a **property**, not a method.
- `shape.volume`, `shape.area`, `shape.bounding_box().min/.max/.size` (Vectors with `.X .Y .Z`).
- `len(shape.solids())` — disjoint solids give a `Compound`, not a `Part`; that is fine for export
  but means the pieces are not connected (check_printable reports `bodies`).
- Sketch face centres: `[Location(f.center()) for f in sketch.faces()]` (`lib.component.locations_of`).
- `export_stl(shape, path, tolerance=0.01, angular_tolerance=0.1)`, `export_step(shape, path)`.

## Gotchas seen in this repo
- A hook/rib that only touches its parent along an edge or point becomes a second solid.
  Overlap by ≥ 0.01 mm or share a full face.
- `Plane.XZ` has its normal along −Y; `extrude(Plane.XZ * sk, amount=t)` grows toward −Y.
  Use `both=True` or `Pos` to place cutters through a wall unambiguously.
- `fillet` fails silently-as-exception on edges that are too short for the radius; clamp radii
  to `< min(adjacent thickness) * 0.9`.
- `Polygon(..., align=None)` keeps your coordinates; the default centres the polygon.
- `RectangleRounded` radius must be < half the shorter side.
- Booleans on many small features are slow (seconds each). Build a `Sketch` of all holes and
  extrude/subtract once rather than subtracting cylinders in a loop.
- Inner fillets on a shell: `shell.edges().group_by(Axis.Z)[1]` is the inner floor loop when the
  floor is thinner than the walls; verify with `len()` before filleting.
