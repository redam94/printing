"""Read ideas/<slug>/IDEA.md files: tiny front-matter parser + validation.

No PyYAML dependency: the front matter is a flat mapping of scalars, inline lists
``[a, b]`` and block lists (``- item``).  Everything after the closing ``---`` is
the markdown body, split into ``## Section`` chunks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from scripts._common import ROOT

IDEAS_DIR = ROOT / "ideas"
STATUSES = ("inbox", "idea", "sketching", "prototyping", "promoted", "parked")
KINDS = ("part", "library", "modification")
LIST_FIELDS = ("tags", "hardware", "reuse", "gaps")


@dataclass
class Idea:
    slug: str
    path: Path
    meta: dict
    sections: dict[str, str] = field(default_factory=dict)
    body: str = ""

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or self.slug.replace("_", " "))

    @property
    def status(self) -> str:
        return str(self.meta.get("status") or "idea")

    @property
    def kind(self) -> str:
        return str(self.meta.get("kind") or "part")

    def lst(self, key: str) -> list[str]:
        v = self.meta.get(key) or []
        return [str(x) for x in v] if isinstance(v, list) else [str(v)]

    @property
    def sketch(self) -> Path | None:
        p = self.path.parent / "sketch.py"
        return p if p.exists() else None

    @property
    def renders(self) -> list[Path]:
        return sorted((self.path.parent / "exports" / "renders").glob("*.png"))

    def to_dict(self) -> dict:
        return {
            "slug": self.slug, "path": str(self.path.relative_to(ROOT)), "title": self.title,
            "status": self.status, "kind": self.kind,
            "tags": self.lst("tags"), "hardware": self.lst("hardware"), "reuse": self.lst("reuse"), "gaps": self.lst("gaps"),
            "model": self.meta.get("model") or "", "created": str(self.meta.get("created") or ""),
            "updated": str(self.meta.get("updated") or ""), "sections": self.sections,
            "has_sketch": self.sketch is not None,
        }


def _scalar(s: str):
    s = s.strip()
    if s == "" or s.lower() in ("null", "~", "none"):
        return None
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def _inline_list(s: str) -> list:
    inner = s.strip()[1:-1].strip()
    return [] if not inner else [_scalar(x) for x in inner.split(",")]


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Return (meta, body). A file without front matter gives ({}, text)."""
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    head, body = m.group(1), m.group(2)
    meta: dict = {}
    key = None
    for raw in head.splitlines():
        line = raw.split(" #", 1)[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and key is not None:
            meta.setdefault(key, [])
            if not isinstance(meta[key], list):
                meta[key] = [] if meta[key] in (None, "") else [meta[key]]
            meta[key].append(_scalar(line.lstrip()[2:]))
            continue
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            meta[key] = _inline_list(val) if val.startswith("[") and val.endswith("]") else _scalar(val)
    for k in LIST_FIELDS:
        v = meta.get(k)
        if v is None:
            meta[k] = []
        elif not isinstance(v, list):
            meta[k] = [v]
    return meta, body


def split_sections(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    cur = "_intro"
    buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if buf and "".join(buf).strip():
                out[cur] = "\n".join(buf).strip()
            cur = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if buf and "".join(buf).strip():
        out[cur] = "\n".join(buf).strip()
    return out


def load_idea(path: Path) -> Idea:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    return Idea(slug=path.parent.name, path=path, meta=meta, sections=split_sections(body), body=body)


def list_ideas() -> list[Idea]:
    if not IDEAS_DIR.exists():
        return []
    return [load_idea(p) for p in sorted(IDEAS_DIR.glob("*/IDEA.md"))]


def validate(idea: Idea, component_ids: set[str], projects: set[str]) -> list[str]:
    problems = []
    if idea.status not in STATUSES:
        problems.append(f"status {idea.status!r} not in {STATUSES}")
    if idea.kind not in KINDS:
        problems.append(f"kind {idea.kind!r} not in {KINDS}")
    if not idea.meta.get("title"):
        problems.append("missing title")
    for cid in idea.lst("reuse"):
        if cid not in component_ids:
            problems.append(f"reuse lists unknown component {cid!r} (see PARTS.md; new ones go under gaps:)")
    for cid in idea.lst("gaps"):
        if cid in component_ids:
            problems.append(f"gap {cid!r} already exists in the library — move it to reuse:")
        if not re.match(r"^(patterns|mechanisms|fasteners|primitives)\.[a-z0-9_]+$", cid):
            problems.append(f"gap {cid!r} is not a <category>.<name> id")
    model = idea.meta.get("model")
    if idea.status in ("prototyping", "promoted") and idea.kind == "part" and not model:
        problems.append(f"status {idea.status} for a part idea needs model: <project>")
    if model and model not in projects:
        problems.append(f"model {model!r} is not in models/ (known: {', '.join(sorted(projects)) or 'none'})")
    return problems


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return s[:48] or "idea"


def new_idea_text(title: str, *, kind: str = "part", status: str = "inbox", text: str = "", hardware: list[str] | None = None,
                  reuse: list[str] | None = None, gaps: list[str] | None = None, tags: list[str] | None = None, source: str = "") -> str:
    import time

    today = time.strftime("%Y-%m-%d")
    fmt = lambda xs: "[" + ", ".join(xs or []) + "]"  # noqa: E731
    log = f"- {today} captured" + (f" from {source}" if source else "")
    return (
        "---\n"
        f"title: {title}\n"
        f"status: {status}\n"
        f"kind: {kind}\n"
        f"created: {today}\n"
        f"updated: {today}\n"
        f"tags: {fmt(tags)}\n"
        f"hardware: {fmt(hardware)}\n"
        f"reuse: {fmt(reuse)}\n"
        f"gaps: {fmt(gaps)}\n"
        "model:\n"
        "---\n\n"
        "## Problem\n"
        f"{text.strip() or '_(not written yet)_'}\n\n"
        "## Concept\n\n"
        "## Constraints\n\n"
        "## Reuse map\n"
        "| need | component | notes |\n|---|---|---|\n\n"
        "## Gaps\n\n"
        "## Open questions\n\n"
        "## Log\n"
        f"{log}\n"
    )
