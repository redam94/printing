"""Voronoi lattices: the cell pattern as a flat sketch, and the same pattern wrapped around a
cylinder as a radial cutter for bodies of revolution.

Two things make a printed Voronoi different from a plotted one:

* **Webs, not lines.**  A Voronoi diagram is a set of edges; a printable lattice is the cells
  *shrunk* so the leftovers form a web of real width.  ``web`` is that width, and it is the number
  that decides whether the part survives being picked up.
* **Roofs.**  Every cell is a hole through a near-vertical wall, so the top of the cell is a
  ceiling.  A raw Voronoi cell has flat-ish top edges, which print as unsupported bridges over the
  full depth of the wall.  ``roof_angle`` clips a tent off the top of each cell so no ceiling ever
  exceeds the overhang limit, which is why the cells come out looking like faceted stones rather
  than soap bubbles.
* **Fanning.**  ``voronoi_shell`` converges each cell on the axis instead of cutting a
  parallel-sided prism.  Straight prisms look right from outside and are wrong inside: the arc
  between two cell centres shrinks with the radius while a flat cell keeps its width, so on a wall
  of any real thickness the webs taper to knife edges and vanish before they reach the bore.  A
  fanned cell keeps every web at a constant ANGULAR width, so ``web`` at the layout radius becomes
  ``web * inner / radius`` at the bore — size it there, not outside.
"""
from __future__ import annotations

from math import cos, radians, sin, tan, tau
from typing import Sequence

import numpy as np
import shapely.affinity as sa
import shapely.geometry as sg
from build123d import Part, Plane, Polygon, Pos, Sketch, loft, scale
from scipy.spatial import Voronoi

from lib.component import MaterialNotes, component

_QUAD_SEGS = 2          # segments per quarter circle in the corner-rounding buffer; 2 is plenty at
                        #     a ~1 mm radius and keeps the face vertex count (and the boolean) down
_MIN_CELL_AREA = 6.0    # mm2, cells smaller than this after webbing and roofing are dropped:
                        #     a 2 mm2 window is not a window, it is a defect in the web
_SIMPLIFY_TOL = 0.05    # mm, drops the near-duplicate vertices the buffer chain leaves behind. They
                        #     are invisible and they cost a sliver face in the loft, which is enough
                        #     to leave a needle of uncut skin standing in a window
_SEAM_OVERLAP = 0.6     # mm, how far the two halves of a seam-split cell reach past the seam. They
                        #     are placed on their own tangent planes and so meet at a slight kink;
                        #     overlapping them means the kink is inside the cut, not a flake of skin


def _tiled(pts: np.ndarray, width: float, height: float) -> tuple[np.ndarray, int]:
    """Seed points repeated in a 3x3 block; returns the block and the index the originals start at.

    Tiling is what makes the pattern periodic: a cell that runs off the right edge of the panel is
    the same cell that runs on at the left, so the lattice closes seamlessly when it is wrapped
    around a body.
    """
    offsets = [(dx, dy) for dx in (-width, 0.0, width) for dy in (-height, 0.0, height)]
    block = np.vstack([pts + o for o in offsets])
    return block, offsets.index((0.0, 0.0)) * len(pts)


def _cells(pts: np.ndarray, width: float, height: float) -> list:
    """Voronoi cell of each seed point, clipped to the panel's Y band (shapely polygons).

    Deliberately NOT clipped in X.  A cell that straddles the seam has to be webbed, rounded and
    roofed as ONE cell and only then split, or the two halves get a pointed roof each and meet at
    the seam as a pair of slivers.  ``voronoi_cells`` does the X clip last.
    """
    block, first = _tiled(pts, width, height)
    vor = Voronoi(block)
    band = sg.box(-width * 2, -height / 2, width * 2, height / 2)
    out = []
    for i in range(len(pts)):
        region = vor.regions[vor.point_region[first + i]]
        if not region or -1 in region:
            out.append(None)
            continue
        cell = sg.Polygon(vor.vertices[region]).buffer(0).intersection(band)
        out.append(cell if not cell.is_empty else None)
    return out


def _relaxed(pts: np.ndarray, width: float, height: float, rounds: int) -> np.ndarray:
    """Lloyd relaxation: move each seed to its cell's centroid so the cells even out.

    Purely random seeds give a lattice with a few slivers and a few caverns; two or three rounds of
    this gives cells of a believable, roughly constant size while keeping the irregularity that is
    the whole point of a Voronoi.
    """
    for _ in range(rounds):
        moved = []
        for pt, cell in zip(pts, _cells(pts, width, height)):
            moved.append((cell.centroid.x, cell.centroid.y) if cell is not None and cell.area > 0 else pt)
        pts = np.asarray(moved)
        pts[:, 0] = (pts[:, 0] + width / 2) % width - width / 2
    return pts


def _roofed(cell, roof_angle: float):
    """Clip a tent off the top of a cell so its ceiling never exceeds the overhang limit.

    The apex sits above the cell's centroid at its highest point, and both roof edges fall away at
    ``roof_angle`` from horizontal.  Once the cell is swept radially through a wall, those edges
    become the ceiling of the hole, so their slope IS the overhang angle the slicer sees.
    """
    if roof_angle <= 0:
        return cell
    cell = cell.buffer(0)   # the erode/dilate chain can leave a self-touching ring GEOS refuses to clip
    if cell.is_empty:
        return cell
    minx, miny, maxx, maxy = cell.bounds
    reach = (maxx - minx) + (maxy - miny)
    apex_x, drop = cell.centroid.x, reach * tan(radians(roof_angle))
    tent = sg.Polygon([(apex_x - reach, maxy - drop), (apex_x, maxy), (apex_x + reach, maxy - drop),
                       (apex_x + reach, miny - reach), (apex_x - reach, miny - reach)])
    try:
        return cell.intersection(tent)
    except Exception:       # GEOS gives up on a degenerate cell rather than returning an empty one
        return sg.Polygon()


def _largest(shape):
    """The biggest polygon in a shapely result, which may be empty or a MultiPolygon."""
    if shape.is_empty:
        return None
    if shape.geom_type == "Polygon":
        return shape
    parts = [g for g in getattr(shape, "geoms", []) if g.geom_type == "Polygon"]
    return max(parts, key=lambda g: g.area) if parts else None


@component(
    id="form.voronoi_cells", version="1.0.0",
    summary="Voronoi cell openings as a sketch on a width x height panel, webbed, corner-rounded and roofed so each cell prints without support; periodic in X so it wraps seamlessly.",
    tags=["cells", "form", "lattice", "organic", "panel", "perforation", "sketch", "vent", "voronoi"],
    units={"width": "mm", "height": "mm", "count": "count", "seed": "count", "web": "mm",
           "corner_r": "mm", "roof_angle": "deg", "relax": "count"},
    descriptions={
        "width": "panel X extent, centred on the origin; wrap this around a cylinder of width/tau radius for a seamless join",
        "height": "panel Y extent, centred on the origin",
        "count": "number of cells",
        "seed": "random seed; change it for a different arrangement at the same statistics",
        "web": "material left between neighbouring cells (each cell is inset by half of it)",
        "corner_r": "fillet radius on every cell corner",
        "roof_angle": "slope of the two roof edges clipped off the top of each cell, from horizontal; 0 = leave cells unroofed (flat ceilings)",
        "relax": "Lloyd relaxation rounds; 0 = raw random cells (slivers and caverns), 2-3 = even cells",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="panel Y is the print Z direction — the roof clip only self-supports if the cells are used that way up",
        notes="UNVALIDATED. Keep web >= 4 nozzle widths (1.6 mm at 0.4) or the webs print as single "
              "unbonded strands. roof_angle must stay at or above the slicer's overhang limit "
              "(45 deg is the usual limit; 50-55 leaves margin).",
    ),
)
def voronoi_cells(width: float = 100.0, height: float = 40.0, count: int = 24, seed: int = 0,
                  web: float = 2.5, corner_r: float = 1.0, roof_angle: float = 45.0,
                  relax: int = 2) -> Sketch:
    """The cell openings (the holes, not the webs) as one sketch of disjoint faces.

    Subtract it from a flat panel, or hand it to ``voronoi_shell`` to wrap it around a body.

    Example:
        vents = voronoi_cells(80, 30, count=18, web=2.0)
        panel = extrude(Rectangle(80, 30) - vents, amount=2)
    """
    rng = np.random.default_rng(seed)
    pts = np.column_stack([rng.uniform(-width / 2, width / 2, count),
                           rng.uniform(-height / 2, height / 2, count)])
    pts = _relaxed(pts, width, height, relax)

    rect = sg.box(-width / 2 - _SEAM_OVERLAP, -height / 2, width / 2 + _SEAM_OVERLAP, height / 2)
    sketch = Sketch()
    for cell in _cells(pts, width, height):
        if cell is None:
            continue
        shrunk = _largest(cell.buffer(-web / 2 - corner_r, quad_segs=_QUAD_SEGS)
                              .buffer(corner_r, quad_segs=_QUAD_SEGS).buffer(0))
        if shrunk is None:
            continue
        roofed = _roofed(shrunk, roof_angle)
        if roofed.is_empty:
            continue
        for shift in (-width, 0.0, width):
            # the panel is periodic, so the part of a cell that runs off one edge belongs to the
            # other: clip against the panel shifted a turn either way and slide the piece back
            clipped = sa.translate(roofed, xoff=shift).intersection(rect)
            for piece in getattr(clipped, "geoms", None) or [clipped]:
                if piece.geom_type != "Polygon" or piece.is_empty or piece.area < _MIN_CELL_AREA:
                    continue
                piece = piece.simplify(_SIMPLIFY_TOL)
                sketch += Polygon(*list(piece.exterior.coords)[:-1], align=None)
    return sketch


@component(
    id="form.voronoi_shell", version="1.0.0",
    summary="NEGATIVE component: Voronoi cells wrapped around a cylinder as radial prisms, to pierce the wall of a body of revolution (or dimple it) with self-supporting cells.",
    tags=["cells", "cutter", "form", "lattice", "negative", "openwork", "pierce", "revolve", "voronoi", "wrap"],
    units={"radius": "mm", "height": "mm", "count": "count", "seed": "count", "web": "mm",
           "corner_r": "mm", "roof_angle": "deg", "relax": "count", "inner": "mm", "over": "mm"},
    descriptions={
        "radius": "radius the pattern is laid out on; use the body's mean radius over the band so the cells come out the size you asked for",
        "height": "Z extent of the band, centred on z=0 (translate the cutter to place it)",
        "count": "number of cells around the whole body",
        "seed": "random seed",
        "web": "material left between neighbouring cells",
        "corner_r": "fillet radius on every cell corner",
        "roof_angle": "slope of each cell's roof from horizontal; the ceiling of every hole, so keep it at or above the overhang limit",
        "relax": "Lloyd relaxation rounds",
        "inner": "radius the cutters stop at; put it inside the bore (or inside the far wall) so every cell breaks clean through, and remember the web there is only web * inner / radius",
        "over": "how far the cutters start outside the layout radius; must exceed how far the body bulges past it",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="body axis vertical, base on the bed",
        notes="UNVALIDATED. Each cell sits on the tangent plane at its own centre and fans in "
              "tangentially toward the axis, so the wrap is faceted: keep cells under about a third "
              "of the radius or the cut edges visibly skew. Check the web at the INNER radius, not "
              "at the layout radius — that is where it is narrowest and where a lattice fails.",
    ),
)
def voronoi_shell(radius: float = 15.0, height: float = 30.0, count: int = 24, seed: int = 0,
                  web: float = 2.5, corner_r: float = 1.0, roof_angle: float = 45.0,
                  relax: int = 2, inner: float = 3.0, over: float = 3.0) -> Part:
    """The lattice as a solid to subtract, band centred on z=0 and the body's axis on Z.

    Each cell is lofted between a copy of itself at ``radius + over`` and a tangentially narrowed
    copy at ``inner``, both at the same heights: the cell fans in like a wedge of an orange, which
    keeps the webs, and only the height stays true so the roof keeps the angle it was cut at.

    Example:
        stalk = revolved_body(profile) - Cylinder(5.8, 40)
        stalk -= Pos(0, 0, 16) * voronoi_shell(radius=9.4, height=14, count=18, web=2.2, inner=3.5)
    """
    cells = voronoi_cells(width=tau * radius, height=height, count=count, seed=seed, web=web,
                          corner_r=corner_r, roof_angle=roof_angle, relax=relax)
    cutter = Part()
    for face in cells.faces():
        c = face.center()
        angle = c.X / radius
        seat = Plane(origin=(radius * cos(angle), radius * sin(angle), c.Y),
                     z_dir=(cos(angle), sin(angle), 0), x_dir=(-sin(angle), cos(angle), 0))
        flat = Pos(-c.X, -c.Y) * face
        wedge = loft([Pos(0, 0, inner - radius) * scale(flat, by=(inner / radius, 1, 1)),
                      Pos(0, 0, over) * scale(flat, by=((radius + over) / radius, 1, 1))])
        cutter += seat * wedge
    return cutter
