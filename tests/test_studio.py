"""The repo overview (scripts/studio.py) collects without building anything and renders text + HTML."""
from scripts.studio import collect, format_text, write_html


def test_collect_and_render(tmp_path):
    d = collect(with_images=False)
    assert d["stats"]["components"] > 0
    assert {m["project"] for m in d["models"]} >= {"pi5_fan_case"}
    txt = format_text(d)
    for word in ("LIBRARY", "MODELS", "IDEAS", "ATTENTION"):
        assert word in txt
    out = write_html(d, tmp_path / "studio.html")
    page = out.read_text(encoding="utf-8")
    assert "__DATA__" not in page and "__TITLE__" not in page
    assert "<title>printing Studio</title>" in page
