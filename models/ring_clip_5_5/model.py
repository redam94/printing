"""Snap-on split-ring clip for a 5.5 mm rod: the coupon print for ``mechanisms.split_ring_clip``.

Parts: ``clip`` (necks as two 1.9 mm plates at the faces, exactly as the reference mesh) and
``clip_full_necks`` (the same clip with the necks running the full 7.2 mm; stiffer, no bridging over
the neck footprints). Both are the component at its defaults: a C-ring with a 5.05 mm bore hung on
two living-hinge push arms, sprung by 0.6 mm side strips off a 3 mm rail.

Print flat as built (bed at z=0, 7.2 mm tall), one of each, with thin-wall / Arachne perimeters on:
the necks are a single 0.4 mm line. PETG first; PLA is expected to work for a few insertions. The
test: push the ring onto a 5.5 mm rod (a pen barrel, a cable) from the open side, does it snap on and
hold; pull it off ten times, do the necks whiten; squeeze the posts, do the jaws tighten. Record it on
the review page as a print report so ``lib/validation.json`` gains the evidence.

Assumptions: the rod is 5.5 mm because the reference file name says so; the rail has no mounting
holes (the reference has none) and is meant to be glued or fused to a host part by its back face at
y = RAIL_TOP. Reference: ``ideas/ring_clip_5_5/references/file-5725bdb05c.md``.
"""
from build123d import Part

from lib.mechanisms.ring_clip import split_ring_clip

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P

# 0.5 mm necks and 0.6 mm strips are the mechanism, not a defect
PRINT_MODES = {"clip": "hinged", "clip_full_necks": "hinged"}


def _clip(neck_plate: float) -> Part:
    return split_ring_clip(
        rod_d=P.ROD_D, grip=P.GRIP, wall=P.WALL, ring_gap=P.RING_GAP, hinge_width=P.HINGE_W, hinge_length=P.HINGE_LEN,
        neck_plate=neck_plate, arm_len=P.ARM_LEN, arm_w=P.ARM_W, arm_angle=P.ARM_ANGLE, jaw_attach=P.JAW_ATTACH,
        post_d=P.POST_D, strip_t=P.STRIP_T, ring_clear=P.RING_CLEAR, rail_t=P.RAIL_T, depth=P.DEPTH,
    )


def build() -> dict[str, Part]:
    return {"clip": _clip(P.NECK_PLATE), "clip_full_necks": _clip(P.NECK_FULL)}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
