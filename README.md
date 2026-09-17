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
uv run python scripts/references.py search "bistable switch"   # find printed reference models online; add <url> files one next to a model/idea and measures its mesh
uv run python scripts/tickets.py                 # design requests from other people, fronted by Jira Service Management (tickets/jira.json + JIRA_* env) or e-mail: board by status; jira check / fetch / ingest / quote / send / set; --html -> the Request page + the Tickets board
uv run python scripts/site.py [--serve|--deploy]   # public sales site in the Augur theme (work, pricing, track record, how to order; site.json holds the copy) -> _site/, --deploy force-pushes gh-pages
uv run python scripts/product_shot.py <project>     # clean product render (three.js in headless Chrome) used by the site
uv run python -m pytest -q
```

Layout: `lib/{patterns,mechanisms,fasteners,primitives}` components with `@component` metadata ·
`models/<project>/{params.py,model.py}` · `ideas/<slug>/IDEA.md` (+ optional `sketch.py`) backlog and prototypes ·
`tests/regression/` golden metrics · `PARTS.md` / `parts.json` generated index · `studio.json` URL of the published Studio page ·
`tickets/<KEY>/` design requests from other people (request, quotes, thread, status; `tickets/pricing.json` the rates, `tickets/jira.json` the Jira Service Management mapping).
Exports (`models/*/exports/`) are gitignored.
