#!/usr/bin/env python
"""Run a throwaway build123d sketch for an idea: metrics, printability, render, viewer.

    uv run python scripts/sketch.py <slug>              # runs ideas/<slug>/sketch.py
    uv run python scripts/sketch.py path/to/any_file.py # any script defining build()
    uv run python scripts/sketch.py <slug> --stl        # also write STLs
    uv run python scripts/sketch.py --new <slug>        # write a starter sketch.py

The script must define ``build() -> Part | dict[str, Part]`` in print orientation
(a value may also be a trimesh.Trimesh from lib.form.mesh).
Outputs land in ideas/<slug>/exports/ (gitignored): renders/<part>.png (open with
Read), view.html (orbit + section plane), and STLs with --stl.  No golden, no lint,
no index: this is the fast loop for form exploration BEFORE a model exists.  When a
sketch settles, it becomes models/<project> through the printable-parts skill and
the freehand geometry is replaced by library components.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import ROOT, bbox_of, metrics, to_trimesh, write_stl  # noqa: E402
from scripts.check_printable import check_mesh, format_report  # noqa: E402
from scripts.ideas import IDEAS_DIR  # noqa: E402
from scripts.render import render_mesh  # noqa: E402


def rel(p: Path) -> Path:
    """Path relative to the repo when inside it, else as-is (sketches may live anywhere)."""
    try:
        return p.relative_to(ROOT)
    except ValueError:
        return p


STARTER = '''"""Sketch for ideas/{slug}: throwaway geometry, print orientation, bed at z=0.

Freehand is fine here.  Note in IDEA.md which library components replace each bit
before this becomes a model.
"""
from build123d import *  # noqa: F401,F403

from lib.component import on_bed

# --- knobs (mm) ---------------------------------------------------------------
LENGTH = 60.0
WIDTH = 40.0
HEIGHT = 20.0
WALL = 1.6


def build():
    outer = Box(LENGTH, WIDTH, HEIGHT)
    inner = Pos(0, 0, WALL) * Box(LENGTH - 2 * WALL, WIDTH - 2 * WALL, HEIGHT)
    return {{"body": on_bed(outer - inner)}}
'''


def resolve(target: str) -> tuple[Path, Path]:
    p = Path(target)
    if p.suffix == ".py" and p.exists():
        return p.resolve(), p.resolve().parent / "exports"
    d = IDEAS_DIR / target
    if (d / "sketch.py").exists():
        return d / "sketch.py", d / "exports"
    raise SystemExit(f"no sketch: give ideas/<slug> with a sketch.py or a .py path (tried {d / 'sketch.py'}); --new {target} writes a starter")


def load_build(script: Path):
    spec = importlib.util.spec_from_file_location(f"sketch_{script.parent.name}", script)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    if not hasattr(mod, "build"):
        raise SystemExit(f"{script} must define build() -> Part | dict[str, Part]")
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?")
    ap.add_argument("--new", metavar="SLUG", help="write ideas/<slug>/sketch.py starter and exit")
    ap.add_argument("--stl", action="store_true", help="also export STL per part")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--nozzle", type=float, default=0.4)
    ap.add_argument("--vase", action="store_true", help="check every part with the spiral / vase-mode rules")
    a = ap.parse_args()

    if a.new:
        d = IDEAS_DIR / a.new
        d.mkdir(parents=True, exist_ok=True)
        s = d / "sketch.py"
        if s.exists():
            raise SystemExit(f"{rel(s)} already exists")
        s.write_text(STARTER.format(slug=a.new), encoding="utf-8")
        print(f"wrote {rel(s)}  — edit it, then: uv run python scripts/sketch.py {a.new}")
        return 0
    if not a.target:
        ap.error("give a slug or a .py path (or --new SLUG)")

    script, out = resolve(a.target)
    label = script.parent.name if script.name == "sketch.py" else script.stem
    t0 = time.time()
    result = load_build(script).build()
    parts = result if isinstance(result, dict) else {label: result}
    print(f"sketch {label}: {len(parts)} part(s) in {time.time() - t0:.1f}s\n")

    ok = True
    viewer_parts = []
    for name, shape in parts.items():
        m = metrics(shape)
        print(f"{name}: bbox {m.bbox_size[0]} x {m.bbox_size[1]} x {m.bbox_size[2]} mm  (min z {m.bbox_min[2]})  "
              f"volume {m.volume / 1000:.2f} cm³  solids={m.solids} valid={m.valid}")
        if m.bbox_min[2] < -1e-3:
            print("      note: part sits below z=0 — wrap it in lib.component.on_bed() for print orientation")
        mesh = to_trimesh(shape)
        rep = check_mesh(mesh, a.nozzle, mode="vase" if a.vase else "normal")
        print(format_report(name, rep))
        ok &= rep["ok"] and m.valid
        entry = {"name": name, "metrics": m.to_dict() | {"wall_min_mm": rep.get("wall_min_mm")}}
        if not a.no_render:
            png = out / "renders" / f"{name}.png"
            render_mesh(mesh, png, f"{label} / {name}")
            print(f"      rendered {rel(png)}   <- open this with Read")
        if a.stl or not a.no_render:
            out.mkdir(parents=True, exist_ok=True)
            stl = write_stl(shape, out / f"{name}.stl")
            entry["stl"] = str(stl)
            if a.stl:
                print(f"      exported {rel(stl)}")
        viewer_parts.append(entry)
        print()

    if not a.no_render:
        from scripts.export_viewer import write_viewer
        run = {"id": label, "label": label, "title": f"sketch: {label}", "eval": "", "config": "", "parts": viewer_parts,
               "report": {"project": label, "docstring": (load_build(script).__doc__ or "").strip(), "components": [], "params": [],
                          "parts": {p["name"]: {"metrics": p["metrics"]} for p in viewer_parts}, "fit_checks": {}, "golden_changes": [], "review": {}}}
        html_out = write_viewer([run], out / "view.html", f"sketch {label}", label)
        print(f"viewer {rel(html_out)}")
        if not a.stl:
            for p in viewer_parts:
                Path(p["stl"]).unlink(missing_ok=True)
    print("\nsketch ok" if ok else "\nsketch has printability problems (see above) — fine to ignore while exploring form")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
