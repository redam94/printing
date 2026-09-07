#!/usr/bin/env python
"""Write a self-contained interactive 3D viewer (HTML) for a model's exported STLs.

    uv run python scripts/export_viewer.py <project>          # -> models/<project>/exports/view.html

Open the file in a browser: orbit, section plane along Z, wireframe, translucent,
parts laid out on a 10 mm bed grid, bbox/volume per part.  Uses three.js from
cdnjs (needs internet); the meshes are embedded, nothing else is fetched.

``write_viewer(runs, out, ...)`` is the reusable API: each run is
``{"id","label","title","eval","config","parts":[{"name","stl":<path>,"metrics":{}}],"report":str}``.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR, ROOT, load_golden  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent / "viewer_template.html"


def write_viewer(runs: list[dict], out: Path, title: str, heading: str | None = None) -> Path:
    payload = {"runs": []}
    for r in runs:
        parts = []
        for p in r["parts"]:
            stl = Path(p["stl"])
            parts.append({"name": p["name"], "stl": base64.b64encode(stl.read_bytes()).decode("ascii"), "metrics": p.get("metrics") or {}})
        payload["runs"].append({k: v for k, v in r.items() if k != "parts"} | {"parts": parts})
    data = json.dumps(payload).replace("</", "<\\/")
    page = (TEMPLATE.read_text()
            .replace("__TITLE__", html.escape(title))
            .replace("__HEADING__", html.escape(heading or title))
            .replace("__DATA__", data))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    return out


def project_run(project: str) -> dict:
    exports = MODELS_DIR / project / "exports"
    golden = load_golden(project) or {}
    gparts = golden.get("parts", {})
    stls = sorted(exports.glob("*.stl"))
    if not stls:
        raise SystemExit(f"no STLs in {exports} — run scripts/build.py {project} first")
    return {"id": project, "label": project, "title": project, "eval": "", "config": "",
            "parts": [{"name": s.stem, "stl": str(s), "metrics": gparts.get(s.stem, {})} for s in stls], "report": ""}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    a = ap.parse_args()
    out = write_viewer([project_run(a.project)], MODELS_DIR / a.project / "exports" / "view.html", f"{a.project} viewer", a.project)
    print(out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
