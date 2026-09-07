"""scripts/sync_notes.py turns dumped review-page notes into print records, component evidence and filed ideas (dry run)."""
import json

from scripts.sync_notes import classify_print, ingest


def _dump(d, project, docs):
    (d / project / "notes").mkdir(parents=True)
    for i, doc in enumerate(docs):
        (d / project / "notes" / f"n{i}.json").write_text(json.dumps(doc), encoding="utf-8")


def test_classify_structured_and_inferred():
    assert classify_print({"kind": "print", "material": "PETG", "outcome": "ok", "text": "latches hold"}) == {"material": "PETG", "outcome": "ok", "inferred": False}
    assert classify_print({"text": "printed the lid in PLA and it fits nicely"}) == {"material": "PLA", "outcome": "ok", "inferred": True}
    assert classify_print({"text": "printed it, the latch snapped off"})["outcome"] == "fail"
    assert classify_print({"text": "boss is too close to the wall"}) is None
    assert classify_print({"kind": "critique", "text": "printed fine but move the vent"}) is None


def test_ingest_dry_run_produces_evidence_and_actions(tmp_path):
    _dump(tmp_path, "pi5_fan_case", [
        {"kind": "print", "material": "PETG", "outcome": "ok", "part": "lid_snap", "status": "resolved", "created": "2026-09-07T12:00:00Z",
         "text": "body + lid_snap in PETG, latches click and hold"},
        {"text": "boss at the USB end is too close to the wall", "status": "open", "created": "2026-09-07T12:01:00Z"},
    ])
    (tmp_path / "studio" / "ideas").mkdir(parents=True)
    (tmp_path / "studio" / "ideas" / "i1.json").write_text(json.dumps({"title": "Pen clip for the monitor bezel", "status": "inbox", "kind": "part", "text": "12 mm bezel"}), encoding="utf-8")

    s = ingest(tmp_path, dry_run=True, today="2026-09-07")
    m = s["models"]["pi5_fan_case"]
    assert m["notes"] == 2 and m["open_critiques"] == 1 and m["prints_added"] == 1
    added = {(e["component"], e["material"], e["outcome"]) for e in s["evidence_added"]}
    assert ("mechanisms.cantilever_latch", "PETG", "ok") in added
    assert ("primitives.box_lid", "PETG", "ok") in added
    assert not s["inferred"]
    assert s["ideas_filed"][0]["slug"] == "pen_clip_for_the_monitor_bezel"
    # db updates queued for Claude: stamp both notes synced, mark the idea filed
    kinds = [(a["collection"], a["data"].get("status", "synced")) for a in s["actions"]]
    assert kinds.count(("notes", "synced")) == 2 and ("ideas", "filed") in kinds


def test_components_override_limits_evidence(tmp_path):
    _dump(tmp_path, "pi5_fan_case", [{"kind": "print", "material": "PLA", "outcome": "fail", "created": "2026-09-07T12:00:00Z", "text": "PLA latch snapped"}])
    s = ingest(tmp_path, dry_run=True, today="2026-09-07", components_override={"n0": ["mechanisms.cantilever_latch"]})
    assert [(e["component"], e["outcome"]) for e in s["evidence_added"]] == [("mechanisms.cantilever_latch", "fail")]
