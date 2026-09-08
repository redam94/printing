"""Organic 2D outlines: blobs (smoothed unions of circles) and clouds (lobes on a flat base).

These are sketches: extrude them for plates and trays, offset them inward for a cavity, subtract
hole patterns from the other categories for the functional part of a "form + function" model.
"""
from __future__ import annotations

from collections.abc import Sequence
from math import degrees, acos

from build123d import Circle, Pos, Rectangle, RectangleRounded, Sketch, fillet

from lib.component import MaterialNotes, component

_NOTES = MaterialNotes(validated=[], orientation="any (2D outline)", notes="UNVALIDATED")

BLOB_CIRCLES: tuple[tuple[float, float, float], ...] = ((0.0, 0.0, 20.0), (18.0, 6.0, 15.0), (-16.0, 4.0, 14.0), (4.0, -14.0, 12.0))
CLOUD_LOBES: tuple[float, ...] = (0.72, 0.9, 1.0, 0.85, 0.68)


def corner_vertices(sketch: Sketch, min_angle_deg: float = 5.0) -> list:
    """Vertices where two edges meet at an angle (not tangent joins), the ones a fillet can act on."""
    edges = sketch.edges()
    out = []
    for v in sketch.vertices():
        p = v.to_tuple()
        tangents = []
        for e in edges:
            for u, sign in ((0.0, 1.0), (1.0, -1.0)):
                q = e.position_at(u)
                if (q - p).length < 1e-6:
                    t = e.tangent_at(u) * sign
                    tangents.append(t)
        if len(tangents) < 2:
            continue
        c = max(-1.0, min(1.0, tangents[0].dot(tangents[1])))
        ang = degrees(acos(c))
        if ang < 180.0 - min_angle_deg:
            out.append(v)
    return out


def smooth_corners(sketch: Sketch, radius: float) -> Sketch:
    """Fillet every real corner of a sketch by ``radius`` (tangent joins are skipped).

    Corners whose adjacent edges are too short for the radius are filleted with a smaller radius
    (halving down to 0.5 mm) or left sharp, instead of failing the whole sketch: a sliver where
    three circles meet must not break a blob."""
    if radius <= 0:
        return sketch
    vs = corner_vertices(sketch)
    if not vs:
        return sketch
    edges = sketch.edges()

    def shortest_edge_at(v) -> float:
        p = v.to_tuple()
        return min((e.length for e in edges if (e.position_at(0) - p).length < 1e-6 or (e.position_at(1) - p).length < 1e-6),
                   default=0.0)

    out = sketch
    pending = list(vs)
    r = radius
    while pending and r >= 0.5:
        ok = [v for v in pending if shortest_edge_at(v) > 1.2 * r]
        if ok:
            try:
                out = fillet(ok, r)
                done = {tuple(round(c, 4) for c in v.to_tuple()) for v in ok}
                pending = [v for v in pending if tuple(round(c, 4) for c in v.to_tuple()) not in done]
                # vertices moved by the fillet are re-found on the new sketch
                pending = [nv for nv in corner_vertices(out)
                           if any((nv.to_tuple() - v.to_tuple()).length < 1e-6 for v in pending)]
            except Exception:
                pass
        r /= 2
    return out


@component(
    id="form.blob_outline", version="1.0.0",
    summary="Smoothed union of circles as a sketch (blob / pebble / organic plate outline).",
    tags=["blob", "pebble", "organic", "outline", "sketch", "union", "plate", "tray", "form"],
    units={"circles": "mm", "smooth_r": "mm"},
    descriptions={"circles": "sequence of (x, y, r); neighbours must overlap", "smooth_r": "fillet radius at every junction (0 = none)"},
    material_notes=_NOTES,
)
def blob_outline(circles: Sequence[tuple[float, float, float]] = BLOB_CIRCLES, smooth_r: float = 4.0) -> Sketch:
    """Example:
        plate = extrude(blob_outline(((0, 0, 30), (25, 10, 20), (-20, 15, 18)), smooth_r=6), amount=3)
    """
    sk = Sketch() + [Pos(x, y) * Circle(r) for x, y, r in circles]
    if len(sk.faces()) != 1:
        raise ValueError("blob circles must overlap into one region")
    return smooth_corners(sk, smooth_r)


@component(
    id="form.cloud_outline", version="1.0.0",
    summary="Cloud silhouette sketch: flat edge at -Y, round lobes bulging toward +Y; centred on the origin.",
    tags=["cloud", "organic", "outline", "lobes", "silhouette", "sketch", "tray", "holder", "kids", "form"],
    units={"length": "mm", "width": "mm", "lobes": "-", "lobe_r": "mm", "overlap": "ratio", "smooth_r": "mm"},
    descriptions={
        "length": "X extent", "width": "Y extent, flat edge (y = -width/2) to the tallest lobe (y = +width/2)",
        "lobes": "relative lobe radii left to right, e.g. (0.7, 0.9, 1.0, 0.85, 0.7); 1.0 = lobe_r",
        "lobe_r": "largest lobe radius; None = 0.22 * length", "overlap": "how far lobe centres sink below the base top, as a fraction of their radius",
        "smooth_r": "fillet radius where lobes meet each other and the base",
    },
    material_notes=_NOTES,
)
def cloud_outline(length: float = 120.0, width: float = 80.0, lobes: Sequence[float] = CLOUD_LOBES, lobe_r: float | None = None,
                  overlap: float = 0.35, smooth_r: float = 3.0) -> Sketch:
    """Base = rounded rectangle from the flat edge up; lobes = circles along the base top, spread so the
    outer lobes are flush with the base sides.  Rotate the sketch to put the flat edge where you need it.

    Example:
        tray = extrude(cloud_outline(130, 95), amount=2) + extrude(cloud_outline(130, 95) - offset(cloud_outline(130, 95), -1.6), amount=8)
    """
    rel = [float(v) for v in lobes]
    if not rel or max(rel) <= 0:
        raise ValueError("lobes must be a non-empty sequence of positive relative radii")
    r_max = 0.22 * length if lobe_r is None else lobe_r
    radii = [r_max * v / max(rel) for v in rel]
    y_flat = -width / 2
    y_top = width / 2
    base_top = y_top - (1.0 - overlap) * r_max
    base_h = base_top - y_flat
    if base_h <= 0:
        raise ValueError("width too small for the lobe radius")
    base_r = min(r_max * 0.6, base_h * 0.45, length * 0.2)
    # base: flat bottom at y_flat, rounded top corners at base_top
    base = (Pos(0, y_flat) * RectangleRounded(length, 2 * base_h, base_r)) & (Pos(0, y_flat + base_h / 2) * Rectangle(length, base_h))
    # lobe centres: first flush with the left side, last with the right, spacing proportional to radii sums
    if len(radii) == 1:
        xs = [0.0]
    else:
        span = length - radii[0] - radii[-1]
        gaps = [radii[i] + radii[i + 1] for i in range(len(radii) - 1)]
        total = sum(gaps)
        xs, x = [], -length / 2 + radii[0]
        for g in [0.0] + gaps:
            x += g / total * span if total else 0.0
            xs.append(x)
    circles = [Pos(x, base_top - overlap * r) * Circle(r) for x, r in zip(xs, radii)]
    cloud = base + circles
    cloud = cloud & Pos(0, y_flat + width) * Rectangle(length * 2, 2 * width)   # keep everything above the flat edge
    if len(cloud.faces()) != 1:
        raise ValueError("cloud lobes must overlap into one region; increase lobe_r or overlap")
    return smooth_corners(cloud, smooth_r)
