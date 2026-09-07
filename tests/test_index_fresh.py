"""PARTS.md / parts.json must match what reindex.py generates from lib/ right now."""
import json

from scripts.reindex import PARTS_JSON, PARTS_MD, build_index, render_markdown


def test_index_is_fresh():
    index = build_index()
    assert PARTS_MD.exists() and PARTS_JSON.exists(), "run scripts/reindex.py"
    assert PARTS_MD.read_text() == render_markdown(index), "PARTS.md is stale — run scripts/reindex.py"
    assert json.loads(PARTS_JSON.read_text()) == json.loads(json.dumps(index, default=str)), "parts.json is stale — run scripts/reindex.py"


def test_index_has_locations_and_reverse_deps():
    idx = json.loads(PARTS_JSON.read_text())
    for cid, c in idx["components"].items():
        assert c["file"].startswith("lib/") and c["line"] > 0, cid
        assert "used_by" in c and "import" in c
    used = [c for c in idx["components"].values() if c["used_by"]]
    assert used, "reverse dependency map is empty although models exist"
