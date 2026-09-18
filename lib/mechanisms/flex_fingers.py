"""Rows of compliant fingers that grip round things of varying diameter (cable combs, tool rails)."""
from __future__ import annotations

from build123d import Align, Box, Circle, Part, Pos, Rectangle, Sketch, extrude

from lib.component import MaterialNotes, component


@component(
    id="mechanisms.flex_fingers", version="1.0.0",
    summary="Comb of bulb-tipped compliant fingers along X forming self-adjusting slots that grip cables or tool shanks pushed in from +Y; standing on z=0.",
    tags=["fingers", "comb", "cable", "cable comb", "clip", "grip", "tool rail", "holder", "organizer", "compliant", "snap"],
    units={"slots": "count", "pitch": "mm", "finger_t": "mm", "finger_len": "mm", "entry_w": "mm", "depth": "mm", "spine_w": "mm", "end_t": "mm"},
    descriptions={
        "slots": "number of slots (fingers = slots + 1)",
        "pitch": "X pitch between fingers; slot width at the bottom = pitch - finger_t",
        "finger_t": "finger thickness along X (the flexing dimension); 1.2 = 3 lines",
        "finger_len": "finger length from the spine face (y=0) to the tip in +Y",
        "entry_w": "opening between the tip bulbs of neighbouring fingers = smallest diameter that is held; bigger things spread the fingers",
        "depth": "part depth = print height (Z)",
        "spine_w": "spine bar width in -Y behind the fingers (mount screws / keyholes go here)",
        "end_t": "thickness of the two outermost fingers (stiffer, they only flex one way)",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="flat on the bed, fingers in the bed plane; the bulbs and slot bottoms are then vertical walls with no overhang",
        notes="UNVALIDATED: no test print yet. Each finger deflects (object_d - entry_w) / 2 at the tip; root strain ~ 1.5 * finger_t * "
              "deflection / finger_len^2 — keep under ~1.5% (PETG) by lengthening the fingers rather than thinning them below 3 lines.",
    ),
)
def flex_fingers(slots: int = 6, pitch: float = 9.0, finger_t: float = 1.2, finger_len: float = 14.0, entry_w: float = 3.2,
                 depth: float = 10.0, spine_w: float = 8.0, end_t: float = 2.4) -> Part:
    """Spine bar occupies y in [-spine_w, 0] over the full length; fingers rise from y=0 to y=finger_len,
    the row centred on x=0.  Slot bottoms are rounded (radius = half the slot width), and each finger
    tip carries a round bulb sized so the gap between neighbouring bulbs equals entry_w.

    Example:
        comb = flex_fingers(slots=6, pitch=9, finger_t=1.2, finger_len=14, entry_w=3.2, depth=10)
        comb = comb - [Pos(x, -spine_w, depth / 2) * Rot(90, 0, 0) * keyhole_hanger() for x in (-25, 25)]
    """
    slots = max(int(slots), 1)
    gap = pitch - finger_t
    if gap <= 0:
        raise ValueError("pitch must exceed finger_t")
    entry_w = min(max(entry_w, 0.6), gap)
    bulb_r = finger_t / 2 + (gap - entry_w) / 2          # bulb protrudes (gap - entry_w) / 2 into each neighbouring slot
    xs = [-slots * pitch / 2 + i * pitch for i in range(slots + 1)]
    total = slots * pitch + end_t                          # outer fingers are end_t thick, centred on the same pitch line
    sk = Sketch() + Pos(0, -spine_w / 2) * Rectangle(total, spine_w)
    for i, x in enumerate(xs):
        t = end_t if i in (0, slots) else finger_t
        sk = sk + Pos(x, finger_len / 2) * Rectangle(t, finger_len)
        sk = sk + Pos(x, finger_len - bulb_r) * Circle(bulb_r)
    # round slot bottoms: a circle of the slot width sitting on the spine face
    for i in range(slots):
        xc = (xs[i] + xs[i + 1]) / 2
        sk = sk - Pos(xc, gap / 2) * Circle(gap / 2)
        sk = sk - Pos(xc, gap / 2 + 0.5) * Rectangle(gap, 1.0)     # blend the circle into the straight slot walls
    # bulbs must not close the slot bottom: trim anything below the spine face
    sk = sk - Pos(0, -spine_w - 5) * Rectangle(total + 2 * bulb_r + 4, 10)
    return extrude(sk, amount=depth)
