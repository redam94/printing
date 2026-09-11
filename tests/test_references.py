"""scripts/references.py: online 3D models file next to a model or idea as guides; meshes get measured; readings attach."""
import json

import pytest

from scripts import references as refs
from scripts.ideas import parse_front_matter, split_sections

PRINTABLES_PRINT = {"data": {"print": {
    "id": "581016", "name": "Bistable Compliant Switch", "slug": "bistable-compliant-switch",
    "summary": "an example of a compliant mechanism", "datePublished": "2023-09-29T10:00:00",
    "description": "<p>Living hinges are used.</p><ul><li>beam 1.2 mm</li><li>print flat</li></ul><script>ignored()</script>",
    "likesCount": 190, "downloadCount": 1870, "makesCount": 18, "category": {"name": "Engineering"},
    "tags": [{"name": "switch"}, {"name": "bistable"}], "license": {"name": "CC BY-NC"}, "user": {"publicUsername": "BYU CMR"},
    "stls": [{"id": "1", "name": "Bistable_Switch.STL", "fileSize": 88000}], "gcodes": [],
    "images": [{"filePath": "media/prints/581016/images/a.jpg"}],
}}}
PRINTABLES_SEARCH = {"data": {"searchPrints2": {"items": [
    {"id": "581016", "name": "Bistable Compliant Switch", "slug": "bistable-compliant-switch", "summary": "s", "likesCount": 190, "downloadCount": 1,
     "makesCount": 18, "license": {"name": "CC BY-NC"}, "user": {"publicUsername": "BYU CMR"}, "tags": [{"name": "bistable"}]}]}}}
GITHUB_SEARCH = {"items": [{"full_name": "a/bistable", "html_url": "https://github.com/a/bistable", "owner": {"login": "a"}, "license": {"spdx_id": "MIT"},
                            "description": "bistable beams", "stargazers_count": 3, "topics": ["compliant"]}]}

READING = {"subject": "bistable toggle switch", "mechanism": "bistable four-bar with living hinges", "principle": "two arms buckle past centre",
           "key_dimensions": ["beam thickness 1.2 mm (measured)", "arm angle ~10 deg (estimated)"], "features": ["living hinge pairs", "stop contacts"],
           "print_notes": "flat on the bed, polypropylene best", "build123d_hints": ["sketch the arm polyline, extrude, mirror"],
           "library_map": ["mechanisms.living_hinge: the joints", "gap: mechanisms.bistable_beam"], "tags": ["Bistable", "switch", "bistable"], "caption": "toggle"}


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway repo root with one model and one idea, and no network."""
    (tmp_path / "models" / "demo").mkdir(parents=True)
    (tmp_path / "models" / "demo" / "model.py").write_text("def build():\n    return {}\n")
    (tmp_path / "ideas" / "toggle").mkdir(parents=True)
    (tmp_path / "ideas" / "toggle" / "IDEA.md").write_text("---\ntitle: Toggle\nstatus: idea\nkind: part\n---\n\n## Problem\nx\n")
    import scripts._common as common
    import scripts.ideas as ideas
    import scripts.inspiration as insp
    for m in (refs, insp):
        monkeypatch.setattr(m, "ROOT", tmp_path)
        monkeypatch.setattr(m, "MODELS_DIR", tmp_path / "models")
        monkeypatch.setattr(m, "IDEAS_DIR", tmp_path / "ideas")
    monkeypatch.setattr(common, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(ideas, "IDEAS_DIR", tmp_path / "ideas")
    monkeypatch.setattr(refs, "http_get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no network in tests")))
    return tmp_path


def _fake_json(routes):
    def get_json(url, *, headers=None, data=None):
        for key, resp in routes.items():
            if key in url or (data and key in json.dumps(data)):
                return resp
        raise RuntimeError(f"unexpected request {url}")
    return get_json


def test_identify_urls():
    assert refs.identify("https://www.printables.com/model/581016-bistable-compliant-switch") == ("printables", "581016")
    assert refs.identify("https://www.printables.com/cs/model/581016") == ("printables", "581016")
    assert refs.identify("https://github.com/a/b.git") == ("github", "a/b")
    assert refs.identify("https://www.thingiverse.com/thing:1663644") == ("thingiverse", "1663644")
    assert refs.identify("https://sketchfab.com/3d-models/none-a2bd37c4813d46848393f8d1329d7a8e") == ("sketchfab", "a2bd37c4813d46848393f8d1329d7a8e")
    assert refs.identify("https://example.org/thing")[0] == "web"


def test_strip_html_keeps_structure_drops_scripts():
    t = refs.strip_html("<p>Hi</p><ul><li>a</li><li>b</li></ul><script>x()</script><table><tr><td>1</td><td>2</td></tr></table>")
    assert "Hi" in t and "- a" in t and "- b" in t and "x()" not in t and "| 1 | 2" in t
    assert refs.strip_html("x" * 100, cap=20).endswith("…(truncated)")


def test_printables_fetch_and_search(monkeypatch):
    monkeypatch.setattr(refs, "get_json", _fake_json({"searchPrints2": PRINTABLES_SEARCH, "print(id": PRINTABLES_PRINT}))
    page = refs.fetch_page("https://www.printables.com/model/581016")
    assert page["title"] == "Bistable Compliant Switch" and page["license"] == "CC BY-NC" and page["downloadable"] == "login"
    assert "- beam 1.2 mm" in page["description"] and "ignored" not in page["description"]
    assert page["files"] == ["Bistable_Switch.STL (85 KB)"] and page["images"][0].startswith("https://media.printables.com/media/")
    assert "Engineering" in page["tags"]
    hits = refs.search("bistable", 3, "printables")
    assert hits[0]["url"] == "https://www.printables.com/model/581016-bistable-compliant-switch" and "18 makes" in hits[0]["score"]
    out = refs.format_search(hits)
    assert "[printables] Bistable Compliant Switch" in out and "needs login" in out


def test_search_survives_a_failing_site(monkeypatch):
    def get_json(url, **k):
        if "github" in url:
            return GITHUB_SEARCH
        raise RuntimeError("down")
    monkeypatch.setattr(refs, "get_json", get_json)
    monkeypatch.delenv("THINGIVERSE_TOKEN", raising=False)
    hits = refs.search("bistable", 3, "all")
    by = {h["source"]: h for h in hits}
    assert by["github"]["title"] == "a/bistable" and by["github"]["downloadable"] == "yes"
    assert "search failed" in by["printables"]["title"] and "search failed" in by["sketchfab"]["title"]
    assert "THINGIVERSE_TOKEN" in by["thingiverse"]["title"]


def test_store_reading_and_list(repo, monkeypatch):
    monkeypatch.setattr(refs, "get_json", _fake_json({"print(id": PRINTABLES_PRINT}))
    page = refs.fetch_page("https://www.printables.com/model/581016")
    rec = refs.store("idea", "toggle", page, why="beam thickness")
    md = repo / rec["path"]
    assert md == repo / "ideas" / "toggle" / "references" / "printables-581016.md"
    meta, body = parse_front_matter(md.read_text())
    secs = split_sections(body)
    assert meta["url"] == "https://www.printables.com/model/581016-bistable-compliant-switch" and meta["reading_model"] == "pending"
    assert meta["why"] == "beam thickness" and "bistable" in meta["tags"]
    assert "- beam 1.2 mm" in secs["Page"] and secs["Reading"].startswith("_(pending") and "filed from printables: beam thickness" in secs["Log"]
    assert rec["pending"] and rec["kind"] == "idea" and rec["target"] == "toggle"

    # reading attaches, tags merge, log grows; empty reading refused
    with pytest.raises(ValueError):
        refs.set_reading(md, {"caption": "only"}, "test")
    rec2 = refs.set_reading(md, json.dumps(READING), "haiku subagent")
    assert not rec2["pending"] and rec2["mechanism"] == "bistable four-bar with living hinges"
    meta, body = parse_front_matter(md.read_text())
    secs = split_sections(body)
    assert meta["reading_model"] == "haiku subagent" and meta["tags"][:2] == ["bistable", "switch"] and "- beam 1.2 mm" in secs["Page"]
    assert "**Key dimensions:**\n- beam thickness 1.2 mm (measured)" in secs["Reading"] and "gap: mechanisms.bistable_beam" in secs["Reading"]
    assert secs["Log"].count("\n") == 1

    # re-adding refreshes the page but keeps the reading and log
    refs.store("idea", "toggle", page, why="")
    meta, body = parse_front_matter(md.read_text())
    secs = split_sections(body)
    assert meta["reading_model"] == "haiku subagent" and meta["why"] == "beam thickness" and "page re-read" in secs["Log"] and "Mechanism" in secs["Reading"]

    recs = refs.list_records()
    assert [r["id"] for r in recs] == ["printables-581016"]
    txt = refs.format_list(recs)
    assert "idea toggle" in txt and "bistable four-bar" in txt and "READING PENDING" not in txt
    assert refs.list_records(kind="model") == []


def test_normalize_reading_accepts_fenced_json():
    nr = refs.normalize_reading("```json\n" + json.dumps(READING) + "\n```")
    assert nr["tags"] == ["bistable", "switch"] and nr["key_dimensions"][0].startswith("beam thickness")
    assert refs.normalize_reading("not json") is None
    assert refs.normalize_reading({"features": "a, b"})["features"] == ["a", "b"]


def _flexure_mesh():
    import trimesh

    def box(w, d, h, x=0, y=0):
        b = trimesh.creation.box((w, d, h))
        b.apply_translation((x, y, h / 2))
        return b
    parts = [box(8, 12, 5, -14, 0), box(8, 12, 5, 14, 0), box(21, 1.2, 5, 0, 4), box(21, 1.2, 5, 0, -4)]
    try:
        return trimesh.boolean.union(parts, engine="manifold")
    except Exception:  # noqa: BLE001
        return trimesh.util.concatenate(parts)


def _hinged_mesh():
    """Two 10 mm blocks joined by a 0.5 mm living hinge: tiny area, but it is the member that flexes."""
    import trimesh

    def box(w, d, h, x=0, y=0):
        b = trimesh.creation.box((w, d, h))
        b.apply_translation((x, y, h / 2))
        return b
    parts = [box(10, 10, 2, -6, 0), box(10, 10, 2, 6, 0), box(2.2, 0.5, 2, 0, 0)]
    try:
        return trimesh.boolean.union(parts, engine="manifold")
    except Exception:  # noqa: BLE001
        return trimesh.util.concatenate(parts)


def test_measure_finds_living_hinge_by_splitting():
    m = refs.measure(_hinged_mesh(), samples=1000)
    assert abs(m["hinge_mm"] - 0.5) < 0.05 and abs(m["thinnest_member_mm"] - 0.5) < 0.05
    assert abs(m["thickest_member_mm"] - 10.0) < 0.3
    mid = m["slices"][len(m["slices"]) // 2]
    assert mid["islands"] == 1 and (mid["beam_mm"] is None or mid["beam_mm"] >= 8.0)  # nothing between the hinge and the blocks
    text = refs.measurements_markdown(m, "hinged.stl")
    assert "(splits the section) | 0.5 mm" in text and "| hinge | beam |" in text and "depth along Z" in text


def test_measure_finds_beam_and_block(repo, monkeypatch):
    mesh = _flexure_mesh()
    m = refs.measure(mesh, samples=1500)
    assert m["bbox_mm"] == [36.0, 12.0, 5.0] and m["slices"]
    assert abs(m["thinnest_member_mm"] - 1.2) < 0.15 and abs(m["thickest_member_mm"] - 8.0) < 0.3
    assert abs(m["hinge_mm"] - 1.2) < 0.15  # the beams are what joins the blocks, so they read as the neck
    assert m["slices"][2]["members"][0]["width_mm"] == 0.3 and m["slices"][2]["members"][0]["area_pct"] < 0.1
    assert m["units_note"] == ""
    text = refs.measurements_markdown(m, "flexure.stl")
    assert "| thinnest member in plane | " in text and "| slice z |" in text
    tiny = mesh.copy()
    tiny.apply_scale(0.03)
    assert "inches" in refs.measure(tiny, samples=300)["units_note"]

    # attach: copies into files/, writes Measurements, records the file, renders
    stl = repo / "dl" / "flexure.stl"
    stl.parent.mkdir()
    mesh.export(str(stl))
    page = {"source": "file", "id": "abc", "url": "", "title": "flexure", "author": "", "license": "", "summary": "local", "description": "",
            "tags": [], "files": [], "images": [], "score": "", "downloadable": "yes"}
    rec = refs.store("model", "demo", page, why="beam")
    md = repo / rec["path"]
    out = refs.attach(md, stl, render=False)
    assert abs(out["thinnest_member_mm"] - 1.2) < 0.15
    assert (md.parent / "files" / "flexure.stl").exists()
    meta, body = parse_front_matter(md.read_text())
    secs = split_sections(body)
    assert meta["files"] == ["flexure.stl"] and "`flexure.stl`" in secs["Measurements"] and "thinnest member 1.2 mm" in secs["Log"]
    rec = refs.load_record(md)
    assert rec["measured"] and rec["files_present"] == ["flexure.stl"] and rec["pending"]
    # attaching the same file again replaces rather than duplicates its block
    refs.attach(md, stl, render=False)
    assert split_sections(parse_front_matter(md.read_text())[1])["Measurements"].count("`flexure.stl`") == 1


def test_generic_page_read(monkeypatch):
    html_page = """<html><head><title>Snap toggle</title><meta property="og:description" content="a snap-through toggle">
    <meta property="og:image" content="/img/t.jpg"></head><body><h1>Snap toggle</h1><a href="files/toggle.stl">stl</a><a href="/x.zip">zip</a></body></html>"""
    monkeypatch.setattr(refs, "http_get", lambda url, **k: html_page.encode())
    p = refs.fetch_page("https://example.org/models/toggle")
    assert p["source"] == "web" and p["title"] == "Snap toggle" and p["summary"] == "a snap-through toggle"
    assert p["files"] == ["https://example.org/models/files/toggle.stl", "https://example.org/x.zip"] and p["images"] == ["https://example.org/img/t.jpg"]
    assert p["downloadable"] == "yes"


def test_sidecar_quotes_awkward_scalars(repo):
    page = {"source": "web", "id": "z1", "url": "https://e.org/a?b=c#frag", "title": "Title: with colon", "author": "", "license": "CC BY 4.0",
            "summary": "", "description": "", "tags": [], "files": [], "images": [], "score": "", "downloadable": "?"}
    rec = refs.store("model", "demo", page, why="")
    meta, _ = parse_front_matter((repo / rec["path"]).read_text())
    assert meta["url"] == "https://e.org/a?b=c#frag" and meta["title"] == "Title: with colon" and meta["why"] == ""


def test_sources_and_prompt():
    assert "printables" in refs.format_sources() and "byu-cmr" in refs.format_sources()
    assert all(f'"{k}"' in refs.READING_PROMPT for k in refs.READING_KEYS)
