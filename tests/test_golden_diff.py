"""diff_golden compares what is reproducible across machines, and only that.

``mesh_hash`` is exact and stable on one machine but OCCT tessellates slightly
differently between platforms and OCP builds, so comparing it made every cloud
rebuild report a change.  These tests pin both halves of the contract: a hash
difference is not a change, and the platform-independent fields still catch a
part that moved, which the hash used to be the only witness for.
"""
import dataclasses
import json
from pathlib import Path

import pytest

from scripts._common import GOLDEN_DIR, Metrics, diff_golden, list_projects

PROJECTS = list_projects()


def _golden(project: str) -> tuple[dict, dict[str, Metrics]]:
    g = json.loads((GOLDEN_DIR / f"{project}.json").read_text(encoding="utf-8"))
    return g, {n: Metrics(**m) for n, m in g["parts"].items()}


@pytest.mark.parametrize("project", PROJECTS)
def test_golden_matches_itself(project):
    g, cur = _golden(project)
    assert diff_golden(g, cur) == []


@pytest.mark.parametrize("project", PROJECTS)
def test_mesh_hash_difference_is_not_a_change(project):
    """A rebuild on another platform differs only in mesh_hash. That is not news."""
    g, cur = _golden(project)
    other = {n: dataclasses.replace(m, mesh_hash="0" * 16) for n, m in cur.items()}
    assert diff_golden(g, other) == []


@pytest.mark.parametrize("project", PROJECTS)
def test_translated_part_is_a_change(project):
    """Same volume, same bbox size, same surface area — only the position moved."""
    g, cur = _golden(project)
    name = sorted(cur)[0]
    m = cur[name]
    moved = dict(cur)
    moved[name] = dataclasses.replace(
        m,
        bbox_min=[m.bbox_min[0] + 0.5, *m.bbox_min[1:]],
        bbox_max=[m.bbox_max[0] + 0.5, *m.bbox_max[1:]],
    )
    fields = {c["field"] for c in diff_golden(g, moved)}
    assert {"bbox_min_x", "bbox_max_x"} <= fields


@pytest.mark.parametrize("project", PROJECTS)
def test_reshaped_at_constant_volume_is_a_change(project):
    """Surface area catches a part rearranged without changing volume or bbox."""
    g, cur = _golden(project)
    name = sorted(cur)[0]
    m = cur[name]
    reshaped = dict(cur)
    reshaped[name] = dataclasses.replace(m, surface_area=m.surface_area * 1.05)
    assert any(c["field"] == "surface_area" for c in diff_golden(g, reshaped))
