#!/usr/bin/env python
"""Write a self-contained interactive 3D viewer (HTML) for a model's exported STLs.

    uv run python scripts/export_viewer.py <project>          # -> models/<project>/exports/view.html

Open the file in a browser: orbit, section plane along Z, wireframe, translucent,
parts laid out on a 10 mm bed grid, bbox/volume per part, a Report tab (from
exports/build_report.json) and a Notes tab for critiques.  Notes persist in the
artifact database when the page is published with the Artifact tool
(capabilities {"db": {}}) and in localStorage when opened as a local file.
Uses three.js from cdnjs (needs internet); the meshes are embedded.

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
VIEWER_FACE_BUDGET = 160_000    # triangles per part before the page is decimated for display
DECIMATE_STEPS = (0.03, 0.06, 0.12, 0.25, 0.5)   # mm, tolerances tried in turn


def display_mesh(stl: Path, budget: int = VIEWER_FACE_BUDGET) -> bytes:
    """The STL bytes to embed: the file itself, or a decimated copy if it is too heavy to ship.

    A textured, openwork part can carry a third of a million triangles, and the page embeds the mesh
    base64 — which is a 22 MB page for something nobody is going to inspect below a tenth of a
    millimetre on screen.  This is a DISPLAY copy only: the exported STL/3MF the slicer gets is
    untouched, and the decimation is allowed to do things (pinch a thin web into two touching
    sheets) that would not be acceptable in a printable mesh.
    """
    raw = stl.read_bytes()
    try:
        import numpy as np
        import trimesh
        from manifold3d import Manifold, Mesh
    except ImportError:                                  # pragma: no cover - display nicety only
        return raw
    mesh = trimesh.load(stl, force="mesh")
    if len(mesh.faces) <= budget:
        return raw
    try:
        man = Manifold(Mesh(vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
                            tri_verts=np.asarray(mesh.faces, dtype=np.uint32)))
        for tol in DECIMATE_STEPS:
            small = man.simplify(tol).to_mesh()
            if len(small.tri_verts) <= budget:
                break
        out = trimesh.Trimesh(vertices=np.asarray(small.vert_properties)[:, :3],
                              faces=np.asarray(small.tri_verts), process=False)
        return out.export(file_type="stl")
    except Exception:                                    # pragma: no cover - never fail a build on this
        return raw


def write_viewer(runs: list[dict], out: Path, title: str, heading: str | None = None) -> Path:
    payload = {"runs": []}
    for r in runs:
        parts = []
        for p in r["parts"]:
            stl = Path(p["stl"])
            parts.append({"name": p["name"], "stl": base64.b64encode(display_mesh(stl)).decode("ascii"),
                          "metrics": p.get("metrics") or {}})
        payload["runs"].append({k: v for k, v in r.items() if k != "parts"} | {"parts": parts})
    data = json.dumps(payload).replace("</", "<\\/")
    page = (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", html.escape(title))
            .replace("__HEADING__", html.escape(heading or title))
            .replace("__DATA__", data))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def project_run(project: str) -> dict:
    exports = MODELS_DIR / project / "exports"
    golden = load_golden(project) or {}
    gparts = golden.get("parts", {})
    report_path = exports / "build_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else ""
    # the report's part list is the truth: a renamed / removed part leaves a stale STL behind
    stls = [exports / f"{n}.stl" for n in report["parts"]] if report else sorted(exports.glob("*.stl"))
    stls = [s for s in stls if s.exists()]
    if not stls:
        raise SystemExit(f"no STLs in {exports} — run scripts/build.py {project} first")
    parts = []
    for s in stls:
        m = dict(gparts.get(s.stem, {}))
        if report and s.stem in report.get("parts", {}):
            m["wall_min_mm"] = report["parts"][s.stem].get("printability", {}).get("wall_min_mm")
        parts.append({"name": s.stem, "stl": str(s), "metrics": m})
    return {"id": project, "label": project, "title": project, "eval": "", "config": "", "parts": parts, "report": report}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    a = ap.parse_args()
    out = write_viewer([project_run(a.project)], MODELS_DIR / a.project / "exports" / "view.html", f"{a.project} viewer", a.project)
    print(out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
