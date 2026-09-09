"""The brief form (scripts/brief.py): the field spec, the page, and a brief filed as a valid IDEA.md."""
import json

from scripts.brief import FIELDS, FRAMINGS, brief_markdown, completeness, idea_text_from_brief, page_data, write_html
from scripts.ideas import Idea, parse_front_matter, split_sections, validate
from scripts.sync_notes import ingest

BRIEF = {
    "id": "b1", "title": "Countertop drip pan", "framing": "problem", "kind": "part", "target": "", "status": "inbox",
    "tags": ["kitchen"], "fields": {
        "problem": "Water runs off the rack and sits on the counter.",
        "job": "Catch the runoff and send it into the basin.",
        "interfaces": "Countertop at the cutout, ~30 mm stone.",
        "success": "A cup of water on the rack ends in the basin.",
        "unknowns": "real counter thickness\nhow much reveal under the counter",
    },
}


def test_field_spec_is_well_formed():
    for framing in FRAMINGS:
        keys = [f["key"] for f in FIELDS[framing]]
        assert len(keys) == len(set(keys))
        for f in FIELDS[framing]:
            assert f["section"] in ("Problem", "Concept", "Constraints", "Open questions")
            assert f["weight"] in (1, 2, 3)
            assert f["hint"] and f["placeholder"] and f["label"]


def test_completeness_counts_only_the_framing_it_is_in():
    have, total, missing = completeness(BRIEF)
    assert 0 < have < total
    assert "Must / must not" in missing and "Form language" not in missing
    assert "**What goes wrong today**" in brief_markdown(BRIEF)


def test_brief_becomes_a_valid_idea_file():
    text = idea_text_from_brief(BRIEF, [{"author": "me", "text": "counter is 32 mm", "status": "open", "created": "2026-09-09"}],
                                today="2026-09-09")
    meta, body = parse_front_matter(text)
    idea = Idea(slug="countertop_drip_pan", path=None, meta=meta, sections=split_sections(body), body=body)
    idx = json.loads((__import__("scripts._common", fromlist=["ROOT"]).ROOT / "parts.json").read_text(encoding="utf-8"))
    assert validate(idea, set(idx["components"]), set()) == []
    assert "Water runs off the rack" in idea.sections["Problem"]
    assert "- real counter thickness" in idea.sections["Open questions"]
    assert "counter is 32 mm" in idea.sections["Open questions"]   # the thread carries into the write-up
    for section in ("Concept", "Constraints", "Reuse map", "Gaps", "Log"):
        assert section in idea.sections


def test_ingest_files_a_handed_over_brief(tmp_path):
    (tmp_path / "brief").mkdir(parents=True)
    (tmp_path / "brief" / "briefs.json").write_text(json.dumps([BRIEF | {"status": "draft", "id": "b0", "title": "Still a draft"}, BRIEF]), encoding="utf-8")
    (tmp_path / "brief" / "notes.json").write_text(json.dumps([
        {"id": "n1", "brief": "b1", "author": "me", "text": "counter is 32 mm", "status": "open", "created": "2026-09-09"},
        {"id": "n2", "brief": "b1", "author": "claude", "text": "then the throat grows 2 mm", "status": "open", "created": "2026-09-09"},
    ]), encoding="utf-8")
    s = ingest(tmp_path, dry_run=True, today="2026-09-09")
    assert [b["slug"] for b in s["briefs_filed"]] == ["countertop_drip_pan"]     # drafts are not filed
    filed = s["briefs_filed"][0]
    assert filed["framing"] == "problem" and filed["notes"] == 2 and 0 < filed["pct"] < 100
    assert [n["text"] for n in s["brief_notes"]] == ["counter is 32 mm"]         # Claude's own notes are not fed back


def test_page_renders(tmp_path):
    d = page_data()
    assert d["components"] and d["printer"]["bed"]
    out = write_html(d, tmp_path / "brief.html")
    page = out.read_text(encoding="utf-8")
    assert "__DATA__" not in page and "__TITLE__" not in page
    assert "<title>printing Briefs</title>" in page
