"""Every ideas/<slug>/IDEA.md parses, uses a known status/kind, and only references components and models that exist."""
import json

import pytest

from scripts._common import ROOT, list_projects
from scripts.ideas import list_ideas, new_idea_text, parse_front_matter, split_sections, validate

IDEAS = list_ideas()


def _component_ids() -> set[str]:
    p = ROOT / "parts.json"
    return set(json.loads(p.read_text(encoding="utf-8"))["components"]) if p.exists() else set()


def test_front_matter_parser_handles_inline_and_block_lists():
    meta, body = parse_front_matter("---\ntitle: T\nstatus: idea\ntags: [a, b]\nreuse:\n  - x.y\n  - x.z\nmodel:\n---\n\n## Problem\nhi\n\n## Log\n- day\n")
    assert meta["title"] == "T" and meta["tags"] == ["a", "b"] and meta["reuse"] == ["x.y", "x.z"] and meta["model"] is None
    assert meta["gaps"] == [] and meta["hardware"] == []
    assert split_sections(body) == {"Problem": "hi", "Log": "- day"}


def test_new_idea_text_round_trips():
    meta, body = parse_front_matter(new_idea_text("Wall mount for label printer", kind="part", hardware=["Brother QL-800"], text="lives on the shelf edge"))
    assert meta["title"] == "Wall mount for label printer" and meta["status"] == "inbox" and meta["hardware"] == ["Brother QL-800"]
    assert "lives on the shelf edge" in split_sections(body)["Problem"]


@pytest.mark.parametrize("idea", IDEAS, ids=[i.slug for i in IDEAS])
def test_idea_is_well_formed(idea):
    problems = validate(idea, _component_ids(), set(list_projects()))
    assert not problems, f"{idea.path.relative_to(ROOT)}:\n  " + "\n  ".join(problems)
