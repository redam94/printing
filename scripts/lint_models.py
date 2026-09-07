#!/usr/bin/env python
"""Lint model files for the library rules.

    uv run python scripts/lint_models.py [project ...]

Flags in models/<project>/model.py:
  * magic numbers: numeric literals other than 0, 1, 2, -1, 0.5 outside params.py
    (every dimension belongs in the PARAMETERS block)
  * inlined hole patterns: GridLocations/PolarLocations with hard-coded spacing,
    or Cylinder/Circle sized like screw hardware when lib.fasteners is not used
  * no library imports at all (the model reuses nothing — suspicious)
  * missing build() function
Exit 1 on any violation.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR, ROOT, list_projects  # noqa: E402

ALLOWED_LITERALS = {0, 1, 2, -1, 0.5, 90, 180, 270, 360}
PATTERN_CALLS = {"GridLocations", "PolarLocations", "HexLocations"}
HARDWARE_DIAMETERS = {1.6, 1.7, 2.0, 2.2, 2.4, 2.5, 2.7, 2.9, 3.0, 3.2, 3.4, 3.6, 4.0, 4.3, 4.5, 4.6, 5.0, 5.5}


def lint_file(path: Path) -> list[str]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    issues: list[str] = []
    rel = path.relative_to(ROOT)
    has_lib_import = any(
        (isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("lib")) or
        (isinstance(n, ast.Import) and any(al.name.startswith("lib") for al in n.names))
        for n in ast.walk(tree)
    )
    if not has_lib_import:
        issues.append(f"{rel}: imports nothing from lib/ — check PARTS.md before writing geometry from scratch")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "build" for n in tree.body):
        issues.append(f"{rel}: missing top-level build() -> dict[str, Part]")

    # numeric literals inside function bodies (module-level constants are fine only in params.py)
    for func in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(func):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                v = node.value
                if v in ALLOWED_LITERALS:
                    continue
                issues.append(f"{rel}:{node.lineno}: magic number {v!r} in {func.name}() — name it in params.py")
            if isinstance(node, ast.Call):
                fname = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if fname in PATTERN_CALLS:
                    if any(isinstance(arg, ast.Constant) for arg in node.args[:2]):
                        issues.append(f"{rel}:{node.lineno}: {fname} with literal spacing — hole patterns belong in lib/patterns")
                if fname in {"Cylinder", "Circle"} and node.args and isinstance(node.args[0], ast.Constant):
                    d = node.args[0].value * 2
                    if round(d, 1) in HARDWARE_DIAMETERS:
                        issues.append(f"{rel}:{node.lineno}: {fname} sized like screw hardware (Ø{d}) — use lib.fasteners.clearance_hole / heat_set_pocket")
    return issues


def main(argv: list[str]) -> int:
    projects = argv or list_projects()
    all_issues: list[str] = []
    for proj in projects:
        model = MODELS_DIR / proj / "model.py"
        if not model.exists():
            all_issues.append(f"models/{proj}/model.py missing")
            continue
        all_issues += lint_file(model)
    for i in all_issues:
        print(i)
    print(f"{len(all_issues)} issue(s) in {len(projects)} model(s)")
    return 1 if all_issues else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
