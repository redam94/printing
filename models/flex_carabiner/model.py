"""Compliant key carabiner: a rounded D-ring whose gate is a printed leaf spring, printed in place.

Part: ``carabiner`` — a 60 x 34 x 6 mm ring, 5 mm band. A 28 mm opening in one long side is
closed by ``mechanisms.leaf_spring``: a 1.2 mm gate rooted in the ring at one end of the opening,
bowed 1.5 mm outward, its free tip resting in a mouth at the other end under a 1.5 mm lip. Push the
gate inward with a thumb and the tip swings out from under the lip, opening the ring for a key
ring, a strap or a bottle loop; let go and it springs back. Anything pulling outward on the gate
presses the tip harder into the lip, so it cannot open by accident.

Printed flat on the bed. The gate and the ring are one solid (the root is buried 2.5 mm into the
ring); the tip clears the mouth by 0.4 mm along the gate and 0.35 mm under the lip, so it prints
free without support. Gate root strain at 3 mm tip deflection is about 0.6%: fine in PETG, and PLA
survives it for casual use (keys), not for hundreds of cycles a day.

Not load-bearing: keys, a water bottle, a lanyard. Never for climbing or anything holding a person.

Assumptions (user unavailable): ring proportions chosen for a thumb on the gate and two fingers
through the ring; 6 mm depth so the gate is a 1.2 x 6 beam; no keyring hole (the ring is the loop).
"""
from build123d import Align, Axis, Box, Part, Pos, RectangleRounded, chamfer, extrude

from lib.mechanisms.springs import leaf_spring

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def _ring() -> Part:
    outline = RectangleRounded(P.OUTER_L, P.OUTER_W, P.OUTER_R) - RectangleRounded(P.OUTER_L - 2 * P.BAND, P.OUTER_W - 2 * P.BAND, P.INNER_R)
    ring = extrude(outline, amount=P.DEPTH)
    if P.BED_CHAMFER > 0:
        ring = chamfer(ring.edges().group_by(Axis.Z)[0], P.BED_CHAMFER)
    # the opening: the whole band over the gap
    gap = Pos(P.GAP_X, P.BAND_Y, P.DEPTH / 2) * Box(P.GAP_LEN, P.BAND + 2, P.DEPTH + 2)
    # the mouth: the inner part of the band beyond the gap, up to MOUTH_TOP, leaving the lip above the gate tip
    mouth_h = P.MOUTH_TOP - (P.OUTER_W / 2 - P.BAND) + 1
    mouth = Pos(P.GAP_X1 + P.LIP_LEN / 2, P.MOUTH_TOP, P.DEPTH / 2) * Box(P.LIP_LEN, mouth_h, P.DEPTH + 2, align=(Align.CENTER, Align.MAX, Align.CENTER))
    return ring - gap - mouth


def _gate() -> Part:
    return Pos(P.GATE_XC, P.BAND_Y, 0) * leaf_spring(length=P.GATE_LEN, thickness=P.GATE_T, bow=P.GATE_BOW, depth=P.GATE_DEPTH, end_overlap=0)


def build() -> dict[str, Part]:
    return {"carabiner": _ring() + _gate()}


def fit_checks(parts: dict[str, Part]) -> dict[str, tuple[Part, Part]]:
    """The gate must be free of the ring everywhere except its buried root, or it prints fused."""
    free = _gate() & Pos(P.GAP_X0 + 1, P.BAND_Y, P.DEPTH / 2) * Box(P.OUTER_L, P.BAND * 2, P.DEPTH + 2, align=(Align.MIN, Align.CENTER, Align.CENTER))
    return {"gate_free_of_ring": (free, _ring())}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
