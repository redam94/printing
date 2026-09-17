"""Blind rectangular pockets of individual sizes: remote / phone / card / tool caddies."""
from __future__ import annotations

from build123d import Part, Pos, RectangleRounded, extrude, loft

from lib.component import MaterialNotes, component

_OVERSHOOT = 1.0   # mm the cutter runs above the rim so the cut leaves no coincident faces


@component(
    id="primitives.pocket_array", version="1.0.0",
    summary="Negative (subtract me): row of blind rounded-rectangle pockets, each its own size and depth, with chamfered lead-ins; rims at z=0, pockets extend down.",
    tags=["pocket", "caddy", "holder", "remote", "phone", "organizer", "rectangular", "negative", "slot"],
    units={"sizes": "mm", "web": "mm", "clearance": "mm", "corner_r": "mm", "lead_in": "mm", "align_y": "enum"},
    descriptions={
        "sizes": "one (x, y, depth) per pocket, in order along +X: the held object's footprint before clearance, and the pocket depth from the rim",
        "web": "wall left between neighbouring pockets",
        "clearance": "added to each pocket's X and Y (total, not per side)",
        "corner_r": "vertical corner radius of each pocket (clamped below half the short side)",
        "lead_in": "45 degree chamfer at the rim so the object finds the pocket; 0 = sharp rim",
        "align_y": "min | center | max: which Y side the pockets line up on (the row is centred on y=0 for center, else that side sits on y=0)",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="rims up (floors are up-facing, lead-ins 45 deg) or rims on the bed (each floor becomes a bridge across the pocket's SHORT side: keep that <= 25 mm)",
        notes="UNVALIDATED: no test print yet. Clearance is added to the total X and Y, not per side.",
    ),
)
def pocket_array(sizes: tuple[tuple[float, float, float], ...] = ((45.0, 20.0, 60.0),), web: float = 2.4,
                 clearance: float = 2.0, corner_r: float = 3.0, lead_in: float = 1.2,
                 align_y: str = "center") -> Part:
    """Pockets in a row along X, the whole row centred on x=0, rims in the z=0 plane.

    ``row_length(sizes, web, clearance)`` gives the X extent, for sizing the body around it::

        block = block - Pos(0, 0, top_z) * pocket_array(((45, 20, 90), (40, 18, 75)), web=2.4)

    Example:
        caddy = box - Pos(0, 0, box_h) * pocket_array(((45, 20, 90), (40, 18, 75), (38, 15, 70)))
    """
    if align_y not in ("min", "center", "max"):
        raise ValueError(f"align_y must be min, center or max, not {align_y!r}")
    x = -row_length(sizes, web, clearance) / 2
    out = Part()
    for sx, sy, depth in sizes:
        px, py = sx + clearance, sy + clearance
        r = min(corner_r, min(px, py) / 2 * 0.9)
        cy = 0.0 if align_y == "center" else (py / 2 if align_y == "min" else -py / 2)
        at = Pos(x + px / 2, cy, 0)
        pocket = Pos(0, 0, -depth) * extrude(RectangleRounded(px, py, r), amount=depth + _OVERSHOOT)
        if lead_in > 0:
            rim = RectangleRounded(px + 2 * lead_in, py + 2 * lead_in, r + lead_in)
            pocket += loft([Pos(0, 0, -lead_in) * RectangleRounded(px, py, r), rim])
            pocket += extrude(rim, amount=_OVERSHOOT)
        out += at * pocket
        x += px + web
    return out


def row_length(sizes, web: float = 2.4, clearance: float = 2.0) -> float:
    """X extent of ``pocket_array(sizes, web, clearance)`` without the lead-in."""
    return sum(s[0] + clearance for s in sizes) + web * (len(sizes) - 1)

