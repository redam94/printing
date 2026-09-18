"""Print-in-place pin hinge: two leaves with alternating knuckles around a captive pin, printed assembled."""
from __future__ import annotations

from build123d import Align, Axis, Box, Circle, Part, Plane, Pos, Rot, extrude

from lib.component import MaterialNotes, component
from lib.primitives.cable_grommet import teardrop


@component(
    id="mechanisms.pip_hinge", version="1.0.0",
    summary="Print-in-place pin hinge: leaf A (-Y) and leaf B (+Y) joined by alternating knuckles on a captive pin along X, printed flat and assembled.",
    tags=["hinge", "print-in-place", "pin", "knuckle", "fold", "stand", "lid", "articulated", "pip"],
    units={"length": "mm", "knuckles": "count", "pin_d": "mm", "hub_d": "mm", "clearance": "mm", "leaf_len": "mm", "leaf_t": "mm"},
    descriptions={
        "length": "hinge length along X (the knuckles fill it)",
        "knuckles": "number of knuckle segments, alternating A, B, A...; odd gives leaf A both ends",
        "pin_d": "pin diameter (part of leaf A; B's knuckles turn on it)",
        "hub_d": "knuckle outer diameter; the axis sits at z = hub_d / 2 so the hub rests on the bed",
        "clearance": "gap between the pin and B's bore (radial) and between neighbouring knuckles (axial); 0.3-0.4 at a 0.4 nozzle",
        "leaf_len": "Y length of each stub leaf beyond the hub; union your real plates onto them",
        "leaf_t": "leaf thickness (Z), from the bed up; must not exceed hub_d",
    },
    material_notes=MaterialNotes(
        validated=[],
        orientation="flat on the bed with the axis in the bed plane; B's bore is a teardrop (point up) so it bridges over the pin without support",
        notes="UNVALIDATED: no test print yet. Leaves sit on the bed, so the axis is above them: the hinge opens toward +Z to about 160 deg "
              "before B's plate meets A's knuckle blocks; it cannot fold flat face-to-face. Break it free with a firm twist after printing. Fine in PLA "
              "(nothing flexes); with 0.35 mm clearance the fit is snug rather than loose.",
    ),
)
def pip_hinge(length: float = 60.0, knuckles: int = 5, pin_d: float = 3.0, hub_d: float = 7.0, clearance: float = 0.35,
              leaf_len: float = 8.0, leaf_t: float = 4.0) -> Part:
    """Returns one Part holding two separate solids (A and B) that do not touch; ``pip_hinge_halves``
    gives them separately for fit checks.  Axis: X, at (y=0, z=hub_d/2).  Leaf A spans y in
    [-(leaf_len + hub_d/2), -(hub_d/2 + clearance)] and leaf B the mirror, both z in [0, leaf_t].

    Example:
        h = pip_hinge(length=70, knuckles=7, leaf_t=4)
        base = Pos(0, -(35 + 3.5), 0) * Box(70, 70, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))   # overlaps leaf A
        stand = h + base + backrest
    """
    a, b = pip_hinge_halves(length, knuckles, pin_d, hub_d, clearance, leaf_len, leaf_t)
    return a + b


def pip_hinge_halves(length: float = 60.0, knuckles: int = 5, pin_d: float = 3.0, hub_d: float = 7.0, clearance: float = 0.35,
                     leaf_len: float = 8.0, leaf_t: float = 4.0) -> tuple[Part, Part]:
    """The two solids of ``pip_hinge``: (leaf A with the pin, leaf B with the bored knuckles)."""
    if leaf_t > hub_d:
        raise ValueError("leaf_t must not exceed hub_d")
    knuckles = max(int(knuckles), 2)
    seg = (length - (knuckles - 1) * clearance) / knuckles
    zc = hub_d / 2
    r_hub = hub_d / 2
    inner = r_hub + clearance                        # where each leaf stops short of the other side's knuckles

    def knuckle(x0: float, side: int) -> Part:
        """Cylinder segment plus a block joining it to its own leaf (side = -1 for A, +1 for B)."""
        cyl = Pos(x0, 0, zc) * Rot(0, 90, 0) * extrude(Circle(r_hub), amount=seg)
        bridge = Pos(x0, side * (inner + 0.01) / 2, 0) * Box(seg, inner + 0.01, leaf_t, align=(Align.MIN, Align.CENTER, Align.MIN))
        return cyl + bridge

    a, b = Part(), Part()
    for i in range(knuckles):
        x0 = -length / 2 + i * (seg + clearance)
        if i % 2 == 0:
            a = a + knuckle(x0, -1)
        else:
            b = b + knuckle(x0, +1)
    pin = Pos(-length / 2 - 0.01, 0, zc) * Rot(0, 90, 0) * extrude(Circle(pin_d / 2), amount=length + 0.02)
    a = a + pin
    # B turns on the pin through a teardrop bore (point up bridges without support)
    bore = extrude(Plane.YZ * teardrop(pin_d, print_oversize=2 * clearance), amount=length / 2 + 1, both=True)
    b = b - Pos(0, 0, zc) * bore
    leaf_a = Pos(0, -(inner + leaf_len / 2), 0) * Box(length, leaf_len + 0.02, leaf_t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    leaf_b = Pos(0, inner + leaf_len / 2, 0) * Box(length, leaf_len + 0.02, leaf_t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return a + leaf_a, b + leaf_b
