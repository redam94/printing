#!/usr/bin/env python
"""Render a model's parts to PNG: isometric + top + front views in one image.

    uv run python scripts/render.py <project> [--part NAME] [--out DIR]

Output: models/<project>/exports/renders/<part>.png (three panels), which the
agent can open with the Read tool to see what it built.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR, build_parts, to_trimesh  # noqa: E402

VIEWS = [("isometric", 30, -60), ("top (XY)", 90, -90), ("front (XZ)", 0, -90)]


def render_mesh(mesh, out_png: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    v, f = mesh.vertices, mesh.faces
    tris = v[f]
    normals = mesh.face_normals
    light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(normals @ light, 0, 1)
    base = np.array([0.36, 0.60, 0.86])
    colors = np.clip(shade[:, None] * base[None, :], 0, 1)

    mn, mx = v.min(axis=0), v.max(axis=0)
    ctr, span = (mn + mx) / 2, (mx - mn).max() * 0.55 + 1e-6
    size = mx - mn

    fig = plt.figure(figsize=(15, 5.2), dpi=110)
    for i, (name, elev, azim) in enumerate(VIEWS, 1):
        ax = fig.add_subplot(1, 3, i, projection="3d")
        coll = Poly3DCollection(tris, facecolors=colors, edgecolors=(0, 0, 0, 0.08), linewidths=0.2)
        ax.add_collection3d(coll)
        for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), ctr):
            setter(c - span, c + span)
        ax.view_init(elev=elev, azim=azim)
        ax.set_proj_type("ortho")
        ax.set_box_aspect((1, 1, 1))
        ax.set_title(name, fontsize=11)
        ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
        ax.tick_params(labelsize=6)
    fig.suptitle(f"{title}   —   {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm   vol {mesh.volume/1000:.1f} cm³", fontsize=12)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png)
    plt.close(fig)


def render_project(project: str, part: str | None = None, out_dir: Path | None = None, parts: dict | None = None) -> list[Path]:
    parts = parts or build_parts(project)
    out_dir = out_dir or MODELS_DIR / project / "exports" / "renders"
    written = []
    for name, shape in parts.items():
        if part and name != part:
            continue
        png = out_dir / f"{name}.png"
        render_mesh(to_trimesh(shape), png, f"{project} / {name}")
        written.append(png)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--part")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    for p in render_project(a.project, a.part, a.out):
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
