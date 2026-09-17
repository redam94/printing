"""The help space (scripts/confluence.py): Markdown -> storage format, and the comparison that keeps push idempotent."""
import pytest

from scripts.confluence import fill, normalise, read_docs, to_storage, values


def test_markdown_subset():
    out = to_storage("## Head\n\n**Bold** start of a paragraph with `code`.\n\n- one\n- two\n\n"
                     "| A | B |\n|---|---|\n| 1 | 2 |\n\n::: tip Title\nInside.\n:::\n\n[[children]]\n")
    assert "<h2><span" in out and "<strong>Bold</strong>" in out and "<code>code</code>" in out
    assert out.count("<li>") == 2 and "<th" in out and "<td>1</td>" in out
    assert 'ac:name="panel"' in out and "Title" in out and "<p>Inside.</p>" in out
    assert 'ac:name="children"' in out


def test_placeholders_are_repo_values():
    v = values()
    assert v["printer.bed"].startswith("270") and v["price.design_fee"].startswith("$")
    assert fill("bed {printer.bed}", v) == f"bed {v['printer.bed']}"
    with pytest.raises(SystemExit):
        fill("{price.nonsense}", v)


def test_docs_render_and_compare_equal_after_confluence_rewrites():
    docs = read_docs(values())
    assert len(docs) >= 10 and docs[0]["home"]
    for d in docs:
        assert d["title"] and d["storage"] and "{" not in d["title"]
    # Confluence stores hex colours as rgb(), escapes characters and reorders macro parameters;
    # normalise() must see through all three or every push would rewrite every page
    mine = ('<p>270 × 270 mm</p><ac:structured-macro ac:name="panel"><ac:parameter ac:name="bgColor">#f3f0e6</ac:parameter>'
            '<ac:parameter ac:name="title">T</ac:parameter><ac:rich-text-body><p>x</p></ac:rich-text-body></ac:structured-macro>')
    theirs = ('<p>270 &times; 270 mm</p><ac:structured-macro ac:name="panel" ac:macro-id="abc-123">'
              '<ac:parameter ac:name="title">T</ac:parameter><ac:parameter ac:name="bgColor">rgb(243,240,230)</ac:parameter>'
              '<ac:rich-text-body><p>x</p></ac:rich-text-body></ac:structured-macro>')
    assert normalise(mine) == normalise(theirs)
