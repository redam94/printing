"""Cable comb and tool rail: rows of compliant fingers that grip whatever is pushed into them.

Parts
  ``comb`` — six slots for desk leads (USB, power, audio, 3 to 8 mm): 1.2 mm fingers, 14 mm long,
  3.2 mm entry between the tip bulbs. Push a lead in, the two fingers beside it spread and close
  round it; pull it out the same way. Two keyholes in the back face hang it on screws (slot up),
  or it sticks under a desk edge on tape, or a cable tie through the two slots in the spine straps
  it to a table leg or a monitor arm.
  ``tool_rail`` — the same component sized for screwdrivers, markers and hex keys (7 to 14 mm):
  1.6 mm fingers, 22 mm long, 7 mm entry. Keyholes for two wall screws.

Both print flat on the bed, fingers in the bed plane, no support: the bulbs and slot bottoms are
vertical walls. PETG is the material for anything flexed daily; PLA holds cables fine but will
eventually crack a finger that is spread every day. Root strain at the widest object is ~1.4%
(comb) and ~1.7% (rail).

Assumptions (user unavailable): the keyhole screws are pan heads (7 / 8 mm) driven out 3 mm; the
slots are sized for the objects listed and no bigger.
"""
from build123d import Part, Pos, Rot

from lib.mechanisms.flex_fingers import flex_fingers
from lib.primitives.hangers import keyhole_hanger, zip_tie_slot

from .params import *  # noqa: F401,F403 — the PARAMETERS block
from . import params as P


def _comb() -> Part:
    comb = flex_fingers(slots=P.COMB_SLOTS, pitch=P.COMB_PITCH, finger_t=P.COMB_FINGER_T, finger_len=P.COMB_FINGER_LEN,
                        entry_w=P.COMB_ENTRY, depth=P.COMB_DEPTH, spine_w=P.COMB_SPINE, end_t=P.COMB_END_T)
    keys = [Pos(sx * P.COMB_KEY_X, -P.COMB_SPINE, P.COMB_KEY_Z) * Rot(90, 0, 0)
            * keyhole_hanger(head_d=P.KEY_HEAD_D, shank_d=P.KEY_SHANK_D, slot_len=P.KEY_SLOT, depth=P.KEY_DEPTH) for sx in (-1, 1)]
    ties = Pos(0, -P.COMB_SPINE / 2, P.COMB_DEPTH / 2) * Rot(90, 0, 0) * zip_tie_slot(tie_w=P.TIE_W, tie_t=P.TIE_T, spacing=P.TIE_SPACING, through=P.COMB_SPINE)
    return comb - keys - ties


def _rail() -> Part:
    rail = flex_fingers(slots=P.RAIL_SLOTS, pitch=P.RAIL_PITCH, finger_t=P.RAIL_FINGER_T, finger_len=P.RAIL_FINGER_LEN,
                        entry_w=P.RAIL_ENTRY, depth=P.RAIL_DEPTH, spine_w=P.RAIL_SPINE, end_t=P.RAIL_END_T)
    keys = [Pos(sx * P.RAIL_KEY_X, -P.RAIL_SPINE, P.RAIL_KEY_Z) * Rot(90, 0, 0)
            * keyhole_hanger(head_d=P.RAIL_KEY_HEAD_D, shank_d=P.RAIL_KEY_SHANK_D, slot_len=P.RAIL_KEY_SLOT, depth=P.KEY_DEPTH) for sx in (-1, 1)]
    return rail - keys


def build() -> dict[str, Part]:
    return {"comb": _comb(), "tool_rail": _rail()}


if __name__ == "__main__":
    for name, part in build().items():
        print(name, part.bounding_box().size, round(part.volume, 1))
