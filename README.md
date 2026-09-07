# printing — parametric 3D-printable parts

build123d models backed by a shared, versioned component library. Designed to be driven by two Claude Code skills in `.claude/skills/`: `design-studio` (repo overview, ideas, sketches) and
`printable-parts` (building models against the library), but every script works by hand.

```
uv sync                                        # build123d, trimesh, matplotlib, pytest
uv run python scripts/build.py esp32_devkit_case   # build → metrics → printability → STL/STEP/3MF → renders → review page → golden
uv run python scripts/reindex.py               # regenerate PARTS.md + parts.json after any lib/ change
uv run python scripts/impact.py fasteners.heat_set_boss   # what would a change to this component affect?
uv run python scripts/studio.py                 # repo overview: library, models, ideas, attention (--html -> exports/studio.html)
uv run python scripts/sketch.py --new my_idea     # throwaway sketch loop for ideas/<slug>/ before it becomes a model
uv run python -m pytest -q
```

Layout: `lib/{patterns,mechanisms,fasteners,primitives}` components with `@component` metadata ·
`models/<project>/{params.py,model.py}` · `ideas/<slug>/IDEA.md` (+ optional `sketch.py`) backlog and prototypes ·
`tests/regression/` golden metrics · `PARTS.md` / `parts.json` generated index · `studio.json` URL of the published Studio page.
Exports (`models/*/exports/`) are gitignored.
