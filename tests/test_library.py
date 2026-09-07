"""Every component in lib/ must carry complete metadata and build at its defaults."""
import importlib
import pkgutil

import pytest

import lib
from lib.component import CATEGORIES, FUNCTIONS, REGISTRY, SEMVER_RE


def _import_all():
    for m in pkgutil.walk_packages(lib.__path__, prefix="lib."):
        importlib.import_module(m.name)


_import_all()
IDS = sorted(REGISTRY)


def test_registry_not_empty():
    assert len(IDS) >= 20


@pytest.mark.parametrize("cid", IDS)
def test_metadata_complete(cid):
    m = REGISTRY[cid]
    assert m.category in CATEGORIES
    assert SEMVER_RE.match(m.version)
    assert m.summary and len(m.summary) < 200
    assert m.tags, "needs searchable tags"
    assert m.material_notes.orientation.strip(), "orientation is required"
    for p in m.params:
        assert p.units, f"{cid}.{p.name} has no units"
    assert m.line > 0 and m.file.endswith(".py")


@pytest.mark.parametrize("cid", IDS)
def test_docstring_has_example(cid):
    m = REGISTRY[cid]
    assert m.docstring, "component needs a docstring"
    assert m.example, "docstring needs an 'Example:' block with a minimal usage"


@pytest.mark.parametrize("cid", [c for c in IDS if c.startswith("mechanisms.")])
def test_compliant_mechanisms_declare_material(cid):
    """A latch that works in PETG snaps in PLA; mechanisms must say what they were validated in
    (or explicitly say UNVALIDATED) and how to orient them."""
    mn = REGISTRY[cid].material_notes
    assert mn.validated or "UNVALIDATED" in mn.notes.upper()
    assert mn.orientation.lower() != "any", "compliant parts always have a required orientation"


@pytest.mark.parametrize("cid", IDS)
def test_builds_valid_at_defaults(cid):
    shape = FUNCTIONS[cid]()
    assert shape.is_valid
    bb = shape.bounding_box().size
    assert bb.X > 0 and bb.Y > 0
    if REGISTRY[cid].returns in ("Part",):
        assert shape.volume > 0.05, "3D component with ~zero volume"
        assert len(shape.solids()) >= 1
    else:
        assert shape.area > 0.01
