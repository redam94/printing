"""Every model builds, is printable, passes lint, and matches its committed golden metrics."""
import pytest

from scripts._common import build_parts, diff_golden, list_projects, load_golden, metrics
from scripts.check_printable import check_mesh
from scripts._common import to_trimesh
from scripts.lint_models import lint_file, MODELS_DIR

PROJECTS = list_projects()


@pytest.fixture(scope="module")
def built():
    return {p: build_parts(p) for p in PROJECTS}


def test_there_are_models():
    assert PROJECTS


@pytest.mark.parametrize("project", PROJECTS)
def test_model_lint(project):
    issues = lint_file(MODELS_DIR / project / "model.py")
    assert not issues, "\n".join(issues)


@pytest.mark.parametrize("project", PROJECTS)
def test_model_matches_golden(project, built):
    golden = load_golden(project)
    assert golden is not None, f"no golden for {project}: run scripts/build.py {project}"
    current = {n: metrics(s) for n, s in built[project].items()}
    changes = diff_golden(golden, current)
    real = [c for c in changes if c["kind"] != "mesh"]
    assert not real, f"{project} geometry changed vs golden: {real}\nIf intended: scripts/build.py {project} --update-golden"


@pytest.mark.parametrize("project", PROJECTS)
def test_model_is_printable(project, built):
    for name, shape in built[project].items():
        rep = check_mesh(to_trimesh(shape))
        assert rep["ok"], f"{project}/{name}: {rep['problems']}"
        assert abs(shape.bounding_box().min.Z) < 1e-6, f"{project}/{name} not sitting on the bed (z_min != 0) — return parts in print orientation"
