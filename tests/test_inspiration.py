"""scripts/inspiration.py: photos file next to their model or idea with a small-model brief sidecar; the page inbox ingests."""
import base64
import io
import json

import pytest

from scripts import inspiration as insp
from scripts._common import ROOT
from scripts.ideas import parse_front_matter, split_sections


def _png(w=1600, h=1200) -> bytes:
    from PIL import Image
    im = Image.new("RGB", (w, h), (200, 120, 60))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def _uri(data: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


BRIEF = {"subject": "ribbed ceramic vase", "style": ["ribbed", "mid-century"], "form": "tall cylinder with a fat shoulder",
         "surface": "vertical ribs", "features": ["vertical ribs", "fat shoulder"], "materials_colors": "glazed clay, terracotta",
         "print_notes": "base on the bed, no supports", "build123d_hints": ["revolve a spline profile", "polar pattern of rib extrusions"],
         "tags": ["Vase", "ribbed", "ribbed"], "caption": "ribbed vase"}


def test_shrink_fits_budget():
    out = insp.shrink(_png(3000, 2000), max_px=800, max_bytes=40_000)
    from PIL import Image
    im = Image.open(io.BytesIO(out))
    assert im.format == "JPEG" and max(im.size) <= 800 and len(out) <= 40_000


def test_normalize_brief_coerces_and_dedups_tags():
    nb = insp.normalize_brief(json.dumps(BRIEF))
    assert nb["tags"] == ["ribbed", "vase"] and nb["features"] == ["vertical ribs", "fat shoulder"]
    assert insp.normalize_brief({"caption": "only a caption"}) is None
    assert insp.normalize_brief("not json") is None


def test_sidecar_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(insp, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(insp, "ROOT", tmp_path)
    (tmp_path / "models" / "demo").mkdir(parents=True)
    rec = insp.store("model", "demo", "abc123", _png(), caption="the ribs: nice", source="test", brief=BRIEF, brief_model="test-model")
    md = tmp_path / rec["path"]
    assert (tmp_path / rec["image"]).exists() and not rec["pending"]
    meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
    assert meta["id"] == "abc123" and meta["caption"] == "the ribs: nice" and meta["tags"] == ["ribbed", "vase"] and meta["brief_model"] == "test-model"
    assert "**Subject:** ribbed ceramic vase" in split_sections(body)["Brief"]
    # pending, then set-brief
    rec2 = insp.store("model", "demo", "def456", _png(), caption="", source="test")
    assert rec2["pending"]
    monkeypatch.setattr(insp, "MODELS_DIR", tmp_path / "models")
    loaded = insp.load_record(tmp_path / rec2["path"])
    assert loaded["pending"] and loaded["kind"] == "model" and loaded["target"] == "demo"
    done = insp.set_brief(tmp_path / rec2["path"], BRIEF, "haiku")
    assert not done["pending"] and done["subject"] == "ribbed ceramic vase" and done["caption"] == "ribbed vase"


def test_ingest_dry_run_files_new_idea_and_reports_pending(tmp_path):
    sync = tmp_path / ".sync"
    (sync / "inspiration").mkdir(parents=True)
    (sync / "inspiration.json").write_text(json.dumps([
        {"id": "p1", "status": "inbox", "target_kind": "new", "title": "Test vase from photo zz", "caption": "ribs", "image": _uri(_png()),
         "created": "2026-09-07T12:00:00Z", "brief": BRIEF, "brief_model": "page quick tier"},
        {"id": "p2", "status": "inbox", "target_kind": "model", "target": "pi5_fan_case", "caption": "", "image": _uri(_png()), "created": "2026-09-07T12:01:00Z", "brief": None},
        {"id": "p3", "status": "inbox", "target_kind": "model", "target": "does_not_exist", "image": _uri(_png()), "created": "2026-09-07T12:02:00Z"},
        {"id": "p4", "status": "inbox", "target_kind": "idea", "target": "lid_skirt_tab", "image": "not a data uri", "created": "2026-09-07T12:03:00Z"},
    ]), encoding="utf-8")
    s = insp.ingest(sync, dry_run=True)
    assert s["docs"] == 4
    assert [r["id"] for r in s["filed"]] == ["p1", "p2"]
    assert s["ideas_created"] == ["ideas/test_vase_from_photo_zz/IDEA.md"]
    assert s["pending"] == ["models/pi5_fan_case/inspiration/p2.md"]
    assert {e[0] for e in s["errors"]} == {"p3", "p4"}
    assert {a["doc_id"] for a in s["actions"]} == {"p1", "p2"} and all(a["data"]["status"] == "filed" for a in s["actions"])
    assert not (ROOT / "ideas" / "test_vase_from_photo_zz").exists()  # dry run wrote nothing
    assert not (ROOT / "models" / "pi5_fan_case" / "inspiration" / "p2.jpg").exists()
    txt = insp.format_ingest(s, True)
    assert "BRIEF PENDING" in txt and "ERROR  p3" in txt


def test_page_and_list_render(tmp_path):
    d = insp.page_data(with_images=False)
    assert {m["project"] for m in d["models"]} >= {"pi5_fan_case"}
    out = insp.write_html(d, tmp_path / "inspiration.html")
    page = out.read_text(encoding="utf-8")
    assert "__DATA__" not in page and "__PROMPT__" not in page and "__TITLE__" not in page
    assert "<title>printing Inspiration</title>" in page and "build123d_hints" in page
    assert isinstance(insp.format_list(insp.list_records()), str)


@pytest.mark.parametrize("rec", insp.list_records(), ids=lambda r: r["path"])
def test_every_sidecar_has_its_image(rec):
    assert rec["image"], f"{rec['path']} has no image file next to it"
    assert not rec["subject"].startswith("(unreadable"), rec["subject"]
