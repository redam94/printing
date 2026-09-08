"""Component metadata decorator and registry.

Every function in ``lib/`` that produces geometry is wrapped with
``@component(...)``.  The decorator:

* records ``id``, ``version`` (semver, per component), ``summary``, ``tags``,
  ``material_notes`` and a ``params`` table derived from the function
  signature (name, type, default) plus the ``units`` you pass in;
* records the source file and line so ``parts.json`` can point straight at
  the definition;
* registers the component in ``REGISTRY`` so ``scripts/reindex.py`` can find
  it by importing the module.

Metadata is validated at import time so a component with missing units or a
malformed version fails loudly, not silently in the index.

Example::

    from build123d import Sketch, Circle, GridLocations
    from lib.component import component, MaterialNotes

    @component(
        id="patterns.example_mount",
        version="1.0.0",
        summary="Two holes 20 mm apart.",
        tags=["example"],
        units={"hole_d": "mm"},
        material_notes=MaterialNotes(validated=["PLA", "PETG"], orientation="any"),
    )
    def example_mount(hole_d: float = 3.4) -> Sketch:
        '''Two-hole pattern.

        Example:
            plate = Rectangle(30, 10) - example_mount()
        '''
        return Sketch() + [loc * Circle(hole_d / 2) for loc in GridLocations(20, 0, 2, 1)]
"""
from __future__ import annotations

import inspect
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

CATEGORIES = ("patterns", "mechanisms", "fasteners", "primitives", "form")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
KNOWN_UNITS = {"mm", "deg", "count", "ratio", "bool", "str", "enum", "mm/mm", "-"}


@dataclass
class Param:
    name: str
    type: str
    units: str
    default: Any
    description: str = ""


@dataclass
class MaterialNotes:
    """What a component has been printed in and how it must be oriented.

    ``validated``: materials this geometry has actually been printed and
    checked in (e.g. ``["PETG", "PLA"]``).  Empty list = untested.
    ``orientation``: required print orientation, written for a human
    ("beam lying flat in the bed plane, hook pointing up").  For compliant
    mechanisms this is not optional: flex behaviour depends on which way the
    layers run.
    ``notes``: anything else (material to avoid, tolerances observed, ...).
    """

    validated: list[str] = field(default_factory=list)
    orientation: str = "any"
    notes: str = ""


@dataclass
class ComponentMeta:
    id: str
    version: str
    summary: str
    params: list[Param]
    tags: list[str]
    material_notes: MaterialNotes
    category: str
    module: str
    qualname: str
    file: str
    line: int
    returns: str
    docstring: str
    example: str

    def to_dict(self) -> dict:
        return asdict(self)


REGISTRY: dict[str, ComponentMeta] = {}
FUNCTIONS: dict[str, Callable] = {}


def _type_name(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "Any"
    if isinstance(annotation, str):
        return annotation.strip("'\"")   # forward references under `from __future__ import annotations`
    return getattr(annotation, "__name__", repr(annotation).replace("typing.", ""))


def _extract_example(doc: str) -> str:
    """Return the text following an ``Example:`` heading in a docstring."""
    if not doc:
        return ""
    m = re.search(r"Example[s]?:\s*\n(.*)", doc, flags=re.S)
    if not m:
        return ""
    lines = m.group(1).splitlines()
    # take the indented block that follows
    block: list[str] = []
    for ln in lines:
        if ln.strip() == "" and block:
            break
        block.append(ln)
    return inspect.cleandoc("\n".join(block))


def component(
    *,
    id: str,
    version: str,
    summary: str,
    tags: list[str],
    units: dict[str, str],
    material_notes: MaterialNotes,
    descriptions: dict[str, str] | None = None,
) -> Callable[[Callable], Callable]:
    """Register a geometry function as a library component.

    ``units`` must name every parameter of the function; use ``"mm"``,
    ``"deg"``, ``"count"``, ``"ratio"``, ``"bool"``, ``"str"``, ``"enum"`` or
    ``"-"``.  ``descriptions`` is an optional per-parameter one-liner.
    """
    category = id.split(".", 1)[0]
    if category not in CATEGORIES or id.count(".") != 1:
        raise ValueError(f"{id}: component id must be '<category>.<name>' with category in {CATEGORIES}")
    if not SEMVER_RE.match(version):
        raise ValueError(f"{id}: version {version!r} is not semver (MAJOR.MINOR.PATCH)")
    if not summary or "\n" in summary.strip():
        raise ValueError(f"{id}: summary must be a single non-empty line")
    bad_units = set(units.values()) - KNOWN_UNITS
    if bad_units:
        raise ValueError(f"{id}: unknown units {bad_units}; use one of {sorted(KNOWN_UNITS)}")

    def deco(fn: Callable) -> Callable:
        sig = inspect.signature(fn)
        missing = [p for p in sig.parameters if p not in units]
        extra = [u for u in units if u not in sig.parameters]
        if missing or extra:
            raise ValueError(f"{id}: units missing for {missing}, extra for {extra}")
        descs = descriptions or {}
        params = [
            Param(
                name=p.name,
                type=_type_name(p.annotation),
                units=units[p.name],
                default=None if p.default is inspect.Parameter.empty else p.default,
                description=descs.get(p.name, ""),
            )
            for p in sig.parameters.values()
        ]
        if id in REGISTRY and REGISTRY[id].qualname != fn.__qualname__:
            raise ValueError(f"{id}: duplicate component id (also {REGISTRY[id].module}.{REGISTRY[id].qualname})")
        src_file = inspect.getsourcefile(fn) or "?"
        try:
            line = inspect.getsourcelines(fn)[1]
        except OSError:
            line = 0
        doc = inspect.getdoc(fn) or ""
        meta = ComponentMeta(
            id=id,
            version=version,
            summary=summary.strip(),
            params=params,
            tags=sorted(set(tags)),
            material_notes=material_notes,
            category=category,
            module=fn.__module__,
            qualname=fn.__qualname__,
            file=src_file,
            line=line,
            returns=_type_name(sig.return_annotation),
            docstring=doc,
            example=_extract_example(doc),
        )
        fn.__component__ = meta  # type: ignore[attr-defined]
        REGISTRY[id] = meta
        FUNCTIONS[id] = fn
        return fn

    return deco


def get(component_id: str) -> Callable:
    """Look up a registered component function by id."""
    return FUNCTIONS[component_id]


def locations_of(sketch) -> list:
    """Return one ``Location`` at the centre of each face of a sketch.

    Hole-pattern components return a ``Sketch`` of circles so they can be
    subtracted directly; use this to place bosses/standoffs at the same spots::

        holes = pi5_mount()
        bosses = [loc * heat_set_boss() for loc in locations_of(holes)]
    """
    from build123d import Location

    return [Location(f.center()) for f in sketch.faces()]


def on_bed(shape):
    """Translate a shape so its lowest point sits on z=0 (the print bed).

    Models return every part in PRINT orientation; use ``Rot(180, 0, 0) * lid``
    to flip a lid and then ``on_bed(...)`` to drop it onto the bed::

        lid = on_bed(Rot(180, 0, 0) * box_lid(...))

    Works on build123d shapes and on ``trimesh.Trimesh`` meshes (the mesh branch
    of the pipeline, see ``lib.form.mesh``).
    """
    if type(shape).__name__ == "Trimesh":
        out = shape.copy()
        out.apply_translation([0.0, 0.0, -float(shape.bounds[0][2])])
        return out
    from build123d import Pos

    return Pos(0, 0, -shape.bounding_box().min.Z) * shape


def flip_to_assembly(shape, top_z: float):
    """Undo a print flip: rotate a face-down part (lid, cover) 180 deg about X and translate it
    so its highest point sits at ``top_z``.  For a lid printed top-face-down, pass
    ``top_z = body_height + lid_thickness`` and the plate lands on the rim with the lip inside::

        lid_assembled = flip_to_assembly(parts["lid"], OUTER_H + LID_T)
        return {"lid_vs_body": (lid_assembled, parts["body"])}
    """
    from build123d import Pos, Rot

    flipped = Rot(180, 0, 0) * shape
    return Pos(0, 0, top_z - flipped.bounding_box().max.Z) * flipped
