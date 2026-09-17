"""The GitHub Pages site (scripts/site.py) builds from whatever exports exist and publishes nothing from tickets/."""
from scripts.site import build, collect, report_text, ticket_models, title_of


def test_titles_and_report_text():
    assert title_of("esp32_devkit_case") == "ESP32 DevKit case"
    assert title_of("pi5_fan_case") == "Pi 5 fan case"
    assert report_text("Reported in chat, not on the review page: printed and it works.") == "Printed and it works."
    assert report_text("printed and it works. Build 20260908-210557 (commit 1e5362f) — the bores fit") == "Printed and it works. The bores fit"


def test_build(tmp_path):
    d = collect()
    names = {x["project"] for x in d["designs"]}
    assert names >= {"pi5_fan_case"}
    assert not names & ticket_models()          # a design made for a requester is never a showcase piece
    out = build(tmp_path / "site")
    for page in ("index.html", "prints.html", "request.html", "style.css", ".nojekyll", "brand/logo.svg"):
        assert (out / page).exists()
    for x in d["designs"]:
        assert (out / "designs" / x["project"] / "index.html").exists()
    everything = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in out.rglob("*.html") if p.name != "viewer.html")
    assert "tickets/" not in everything and "PRINT-1 " not in everything
    assert "CONFIRM" in (out / "request.html").read_text(encoding="utf-8")
