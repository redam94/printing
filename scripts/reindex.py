#!/usr/bin/env python
"""Regenerate PARTS.md and parts.json from the component metadata in lib/.

    uv run python scripts/reindex.py            # rewrite both files
    uv run python scripts/reindex.py --check    # exit 1 if the committed files are stale

Run this after ANY change under lib/, in the same commit.  A stale index is a
bug: the agent designs from PARTS.md, so a missing component gets re-invented.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import pkgutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import LIB_DIR, MODELS_DIR, ROOT  # noqa: E402

import lib  # noqa: E402
from lib.component import CATEGORIES, REGISTRY  # noqa: E402

PARTS_MD = ROOT / "PARTS.md"
PARTS_JSON = ROOT / "parts.json"


def import_all_components() -> None:
    for m in pkgutil.walk_packages(lib.__path__, prefix="lib."):
        importlib.import_module(m.name)


def _module_functions() -> dict[tuple[str, str], str]:
    """(module, function name) -> component id."""
    return {(m.module, m.qualname): cid for cid, m in REGISTRY.items()}


def scan_model_imports() -> dict[str, list[str]]:
    """Reverse dependency map: component id -> sorted list of model files (repo-relative)."""
    fn_index = _module_functions()
    by_module: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for (mod, fn), cid in fn_index.items():
        by_module[mod].append((fn, cid))
    used_by: dict[str, set[str]] = defaultdict(set)

    for py in sorted(MODELS_DIR.glob("*/*.py")):
        rel = str(py.relative_to(ROOT))
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        module_aliases: dict[str, str] = {}   # local name -> lib module path
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("lib"):
                for alias in node.names:
                    if alias.name == "*":
                        for fn, cid in by_module.get(node.module, []):
                            used_by[cid].add(rel)
                        continue
                    key = (node.module, alias.name)
                    if key in fn_index:
                        used_by[fn_index[key]].add(rel)
                    else:
                        # `from lib.patterns import pi` -> module alias
                        sub = f"{node.module}.{alias.name}"
                        if sub in by_module:
                            module_aliases[alias.asname or alias.name] = sub
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("lib.") and alias.name in by_module:
                        module_aliases[alias.asname or alias.name] = alias.name
        if module_aliases:
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in module_aliases:
                    key = (module_aliases[node.value.id], node.attr)
                    if key in fn_index:
                        used_by[fn_index[key]].add(rel)
    return {cid: sorted(v) for cid, v in used_by.items()}


VALIDATION_JSON = ROOT / "lib" / "validation.json"


def load_evidence() -> dict:
    """Field evidence from lib/validation.json (written by scripts/sync_notes.py from review-page print reports)."""
    if not VALIDATION_JSON.exists():
        return {}
    return json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))


def build_index() -> dict:
    import_all_components()
    used_by = scan_model_imports()
    evidence = load_evidence()
    components = {}
    for cid in sorted(REGISTRY):
        m = REGISTRY[cid]
        d = m.to_dict()
        d["file"] = str(Path(m.file).resolve().relative_to(ROOT))
        d["used_by"] = used_by.get(cid, [])
        d["import"] = f"from {m.module} import {m.qualname}"
        ev = evidence.get(cid, [])
        d["material_notes"]["evidence"] = ev
        d["material_notes"]["field_validated"] = sorted({e["material"] for e in ev if e.get("outcome") == "ok" and e.get("material")})
        d["material_notes"]["field_failed"] = sorted({e["material"] for e in ev if e.get("outcome") == "fail" and e.get("material")})
        components[cid] = d
    models = {}
    for proj_dir in sorted(p.parent for p in MODELS_DIR.glob("*/model.py")):
        rel_files = {str(p.relative_to(ROOT)) for p in proj_dir.glob("*.py")}
        models[proj_dir.name] = {
            "path": str(proj_dir.relative_to(ROOT)),
            "components": sorted(cid for cid, files in used_by.items() if rel_files & set(files)),
            "golden": (ROOT / "tests" / "regression" / f"{proj_dir.name}.json").exists(),
        }
    return {"schema": 1, "components": components, "models": models}


def _fmt_default(v) -> str:
    if v is None:
        return "auto"
    if isinstance(v, str):
        return f'"{v}"'
    return str(v)


def render_markdown(index: dict) -> str:
    comps = index["components"]
    out = ["# Parts library index", "",
           "Generated by `scripts/reindex.py` — do not edit by hand. Import path and definition location are in `parts.json`.", "",
           f"**{len(comps)} components** in {len(CATEGORIES)} categories. Versions are per-component semver.", ""]
    for cat in CATEGORIES:
        rows = [c for c in comps.values() if c["category"] == cat]
        if not rows:
            continue
        out += [f"## {cat}", ""]
        for c in rows:
            out += [f"### `{c['id']}` v{c['version']}", "", c["summary"], ""]
            out += [f"- **import:** `{c['import']}`  ", f"- **returns:** `{c['returns']}`  ", f"- **tags:** {', '.join(c['tags'])}  "]
            mn = c["material_notes"]
            val = ", ".join(mn["validated"]) if mn["validated"] else "UNVALIDATED"
            out += [f"- **validated in:** {val}  "]
            if mn.get("field_validated") or mn.get("field_failed"):
                ok = [f"{e['material']} ({e['model']} {e['date']})" for e in mn["evidence"] if e.get("outcome") == "ok"]
                bad = [f"{e['material']} ({e['model']} {e['date']})" for e in mn["evidence"] if e.get("outcome") == "fail"]
                out += [f"- **field-validated:** {', '.join(ok) or '—'}" + (f"; **failed:** {', '.join(bad)}" if bad else "") + "  "]
            out += [f"- **orientation:** {mn['orientation']}  "]
            if mn.get("notes"):
                out += [f"- **notes:** {mn['notes']}  "]
            if c["used_by"]:
                out += [f"- **used by:** {', '.join(c['used_by'])}  "]
            out += ["", "| param | type | units | default | description |", "|---|---|---|---|---|"]
            for p in c["params"]:
                out.append(f"| `{p['name']}` | {p['type']} | {p['units']} | `{_fmt_default(p['default'])}` | {p['description']} |")
            out.append("")
            if c["example"]:
                out += ["```python", c["example"], "```", ""]
    if index["models"]:
        out += ["## models", "", "| project | components used | golden |", "|---|---|---|"]
        for name, m in index["models"].items():
            out.append(f"| `{name}` | {', '.join(f'`{c}`' for c in m['components']) or '—'} | {'yes' if m['golden'] else 'no'} |")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 if PARTS.md/parts.json are stale")
    args = ap.parse_args()
    index = build_index()
    md = render_markdown(index)
    js = json.dumps(index, indent=2, default=str) + "\n"
    if args.check:
        stale = []
        if not PARTS_MD.exists() or PARTS_MD.read_text(encoding="utf-8") != md:
            stale.append("PARTS.md")
        if not PARTS_JSON.exists() or PARTS_JSON.read_text(encoding="utf-8") != js:
            stale.append("parts.json")
        if stale:
            print(f"STALE INDEX: {', '.join(stale)} — run `uv run python scripts/reindex.py`")
            return 1
        print("index is fresh")
        return 0
    PARTS_MD.write_text(md, encoding="utf-8")
    PARTS_JSON.write_text(js, encoding="utf-8")
    n_used = sum(1 for c in index["components"].values() if c["used_by"])
    print(f"wrote PARTS.md and parts.json: {len(index['components'])} components ({n_used} used by models), {len(index['models'])} models")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
