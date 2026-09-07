"""Cantilever snap latch (hook on a flexing beam) and its mating window."""
from __future__ import annotations

from build123d import Align, Axis, Box, Part, Plane, Polygon, Pos, extrude, fillet

from lib.component import MaterialNotes, component

_LATCH_NOTES = MaterialNotes(
    validated=["PETG"],
    orientation="beam lying flat in the bed plane (beam length along X or Y, thickness along Z). "
                "Never print the beam standing up: bending then peels layers apart and the root cracks.",
    notes="PETG and ABS/ASA flex reliably; PLA snaps below ~1.2 mm thickness or after a few dozen cycles. "
          "Strain at the root ~ 1.5*t*hook_depth/length^2 — keep under ~2% for PETG. Defaults give ~1.0%.",
)


@component(
    id="mechanisms.cantilever_latch", version="1.0.1",
    summary="Cantilever snap-fit hook: flexing beam along +Z from z=0 with a ramped hook on the +X face at the tip.",
    tags=["latch", "snap", "snap-fit", "cantilever", "hook", "clip", "lid", "compliant"],
    units={"length": "mm", "width": "mm", "thickness": "mm", "hook_depth": "mm", "hook_height": "mm",
           "entry_angle": "deg", "retention_angle": "deg", "root_fillet": "mm"},
    descriptions={
        "length": "beam length from root (z=0) to the underside of the hook",
        "width": "beam width (Y)",
        "thickness": "beam thickness (X) — the flexing dimension",
        "hook_depth": "how far the hook protrudes in +X beyond the beam face = deflection required to release",
        "hook_height": "height of the hook block (Z)",
        "entry_angle": "ramp angle on the top of the hook (lower = easier to push closed)",
        "retention_angle": "angle of the underside of the hook (90 = permanent, 45 = easy release)",
        "root_fillet": "fillet at the beam root to spread stress",
    },
    material_notes=_LATCH_NOTES,
)
def cantilever_latch(length: float = 12.0, width: float = 6.0, thickness: float = 1.6, hook_depth: float = 1.2,
                     hook_height: float = 2.5, entry_angle: float = 30.0, retention_angle: float = 90.0,
                     root_fillet: float = 0.5) -> Part:
    """The beam's back face is at x=0 (attach it there), hook faces +X.
    Total height = length + hook_height.  As returned, the beam stands along
    Z — that is the *assembled* pose for a latch embedded in a vertical wall,
    and it must be rotated so the beam lies in the bed plane before printing
    (see material_notes).  The usual layer-safe layout is to make the beam a
    strip of the box wall: cut a U-slot in the wall, place the latch in it
    with its length along the wall and its thickness = wall thickness, hook
    pointing outward; the lid carries a skirt tab with a ``latch_window``.

    Example:
        # beam runs along X inside the +Y wall (wall thickness = latch thickness), hook points +Y
        latch = Rot(0, 90, 90) * cantilever_latch(length=12, thickness=wall_t)
        body = body - wall_slot + Pos(x_root, y_wall, z_hook) * latch
        lid_tab = lid_tab - Pos(x_hook, y_wall, z_hook) * Rot(0, 0, 90) * latch_window(width=6, hook_depth=1.2)
    """
    import math
    beam = Box(thickness, width, length, align=(Align.MIN, Align.CENTER, Align.MIN))
    # hook profile in XZ, extruded along Y
    ret_dx = hook_depth / math.tan(math.radians(retention_angle)) if retention_angle < 90 else 0.0
    ramp_dz = hook_depth * math.tan(math.radians(entry_angle))
    top_flat = max(hook_height - ramp_dz, 0.4)
    pts = [
        (0, length), (thickness, length), (thickness + hook_depth, length + ret_dx), (thickness + hook_depth, length + ret_dx + top_flat),
        (thickness, length + ret_dx + top_flat + ramp_dz), (0, length + ret_dx + top_flat + ramp_dz),
    ]
    hook = extrude(Plane.XZ * Polygon(*pts, align=None), amount=width / 2, both=True)
    latch = beam + hook
    if root_fillet > 0:
        root_edge = latch.edges().filter_by(Axis.Y).group_by(Axis.Z)[0].sort_by(Axis.X)[-1]
        latch = fillet(root_edge, root_fillet)
    return latch


@component(
    id="mechanisms.latch_window", version="1.0.0",
    summary="Negative (subtract me) rectangular window through a wall for a cantilever_latch hook to snap into.",
    tags=["latch", "snap", "window", "catch", "negative", "lid"],
    units={"width": "mm", "hook_depth": "mm", "hook_height": "mm", "clearance": "mm", "wall_t": "mm"},
    descriptions={
        "width": "latch beam width", "hook_depth": "latch hook_depth", "hook_height": "latch hook_height",
        "clearance": "added around the hook (0.3 slip fit)", "wall_t": "wall thickness to punch through (window depth in X, both ways)",
    },
    material_notes=_LATCH_NOTES,
)
def latch_window(width: float = 6.0, hook_depth: float = 1.2, hook_height: float = 2.5, clearance: float = 0.3, wall_t: float = 1.6) -> Part:
    """Window centred on the origin in Y and Z, cutting through X in both directions.

    Example:
        body = body - Pos(wall_x, y, z_hook) * latch_window(6, 1.2, 2.5)
    """
    return Box(2 * wall_t + 2, width + 2 * clearance, hook_height + 2 * clearance, align=(Align.CENTER, Align.CENTER, Align.CENTER))
