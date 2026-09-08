#!/usr/bin/env python
"""Inspiration images: photos attached to a model or an idea, each with a small-model brief.

Where they live
---------------
``models/<project>/inspiration/<id>.jpg`` + ``<id>.md``   attached to a built model
``ideas/<slug>/inspiration/<id>.jpg``   + ``<id>.md``     attached to an idea

The ``.md`` sidecar has front matter (id, target, created, source, caption, image, brief_model,
tags) and a ``## Brief`` section: the structured reading of the photo written by a *small* model
(the Inspiration page's quick tier, or a Haiku subagent locally).  The large model designing
the part reads the brief, never the pixels.

How they arrive
---------------
1. The published Inspiration page (``scripts/inspiration.py --html`` -> ``exports/inspiration.html``)
   stores each upload in the artifact db, collection ``inspiration``: downscaled JPEG as a data
   URI, target, caption, and the brief the page asked Claude for.  ``ingest`` reads a dump of
   that collection from ``.sync/inspiration.json`` (or ``.sync/inspiration/<id>.json``) and
   files every ``status: inbox`` document into the repo.
2. ``add <image> --model <p> | --idea <slug> | --new "<title>"`` files a photo that is already
   on disk (downscaled the same way); its brief is ``pending`` until ``set-brief`` runs.

Commands
--------
  uv run python scripts/inspiration.py                      list everything (pending briefs flagged)
  uv run python scripts/inspiration.py ingest [--dry-run]   file the page inbox from .sync/
  uv run python scripts/inspiration.py add photo.jpg --model pi5_fan_case --caption "..."
  uv run python scripts/inspiration.py pending              images whose brief is still pending
  uv run python scripts/inspiration.py prompt               the brief prompt (for the subagent)
  uv run python scripts/inspiration.py set-brief <md> --json brief.json --model haiku
  uv run python scripts/inspiration.py --html               write exports/inspiration.html
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import html
import io
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR, ROOT, list_projects  # noqa: E402
from scripts.ideas import IDEAS_DIR, list_ideas, new_idea_text, parse_front_matter, slugify, split_sections  # noqa: E402

DIRNAME = "inspiration"
SYNC_DIR = ROOT / ".sync"
INSPIRATION_JSON = ROOT / "inspiration.json"
TEMPLATE = ROOT / "scripts" / "inspiration_template.html"
OUT_HTML = ROOT / "exports" / "inspiration.html"
MAX_PX = 1024          # longest side of a stored image
MAX_BYTES = 150_000    # stored JPEG budget (a db document is capped at 256 KiB incl. base64 + brief)
THUMB_PX = 320

# The one prompt every small model answers, so briefs are comparable whoever wrote them.
# The page injects it as __PROMPT__; the Haiku subagent gets it from `inspiration.py prompt`.
BRIEF_PROMPT = """You are describing a reference photo for a 3D-printing designer who works in build123d (a parametric CAD library). The designer will NOT see the photo, only your reading of it, and wants to borrow its look for a mostly artistic (not purely functional) printed part. Be concrete and visual; name shapes, proportions and surface treatments, not feelings.

Reply with only one JSON object with exactly these keys:
{
  "subject": "what the object is, one short line",
  "style": ["3 to 6 style words, e.g. art deco, ribbed, organic, faceted"],
  "form": "silhouette, primary volumes and how they join, proportions (ratios, not mm), symmetry, taper. 2-3 sentences.",
  "surface": "textures, patterns, edge treatment (fillets, chamfers, sharp), finish. 1-2 sentences.",
  "features": ["distinct features worth borrowing, each a short phrase"],
  "materials_colors": "what it seems to be made of and its colours, one line",
  "print_notes": "if printed as-is: overhangs, thin parts, which face would go on the bed, supports. One or two sentences.",
  "build123d_hints": ["for each borrowed feature, how to build it: extrude/revolve/loft/sweep, fillet, polar or linear pattern, offset shell..."],
  "tags": ["3 to 8 lowercase tags"],
  "caption": "one line for a gallery card"
}
If a caption from the uploader is given, treat it as what they liked about the photo and make sure those aspects are covered."""

SIDECAR_KEYS = ("id", "target", "created", "source", "caption", "image", "brief_model", "tags")
BRIEF_KEYS = ("subject", "style", "form", "surface", "features", "materials_colors", "print_notes", "build123d_hints", "tags", "caption")
_LIST_KEYS = {"style", "features", "build123d_hints", "tags"}
_DATA_URI = re.compile(r"^data:(image/[\w.+-]+);base64,(.*)$", re.S)


# ---------------------------------------------------------------- targets

def target_dir(kind: str, slug: str) -> Path:
    if kind == "model":
        return MODELS_DIR / slug / DIRNAME
    if kind == "idea":
        return IDEAS_DIR / slug / DIRNAME
    raise ValueError(f"unknown target kind {kind!r}")


def resolve_target(kind: str, slug: str = "", title: str = "", *, caption: str = "", source: str = "",
                   dry_run: bool = False) -> tuple[str, str, str | None]:
    """Return (kind, slug, created_idea_path).  ``new`` creates an inbox idea from ``title``."""
    kind = (kind or "").strip().lower()
    slug = (slug or "").strip()
    if kind == "model":
        if slug not in list_projects():
            raise ValueError(f"no such model: models/{slug}")
        return kind, slug, None
    if kind == "idea":
        if not (IDEAS_DIR / slug / "IDEA.md").exists():
            raise ValueError(f"no such idea: ideas/{slug}/IDEA.md")
        return kind, slug, None
    if kind == "new":
        title = (title or "").strip() or (caption or "").strip().split("\n")[0][:60]
        if not title:
            raise ValueError("a new idea needs a title")
        slug = slugify(title)
        path = IDEAS_DIR / slug / "IDEA.md"
        if path.exists():
            return "idea", slug, None
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_idea_text(title, kind="part", status="inbox", text=caption, source=source or "inspiration photo"),
                            encoding="utf-8")
        return "idea", slug, str(path.relative_to(ROOT))
    raise ValueError(f"target kind must be model, idea or new (got {kind!r})")


# ---------------------------------------------------------------- images

def _pil():
    from PIL import Image, ImageOps  # matplotlib dependency, always present
    return Image, ImageOps


def shrink(data: bytes, *, max_px: int = MAX_PX, max_bytes: int = MAX_BYTES) -> bytes:
    """Re-encode any raster as a JPEG that fits the size budget (EXIF orientation applied)."""
    Image, ImageOps = _pil()
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    if im.mode not in ("RGB", "L"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
        im = bg
    elif im.mode == "L":
        im = im.convert("RGB")
    side = max_px
    quality = 85
    while True:
        cur = im.copy()
        cur.thumbnail((side, side))
        buf = io.BytesIO()
        cur.save(buf, "JPEG", quality=quality, optimize=True)
        if buf.tell() <= max_bytes or (side <= 320 and quality <= 50):
            return buf.getvalue()
        if quality > 60:
            quality -= 10
        else:
            side = int(side * 0.8)


def thumb_data_uri(path: Path, max_px: int = THUMB_PX) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(shrink(path.read_bytes(), max_px=max_px, max_bytes=60_000)).decode("ascii")


def decode_data_uri(uri: str) -> bytes:
    m = _DATA_URI.match(uri.strip())
    if not m:
        raise ValueError("not an image data URI")
    try:
        return base64.b64decode(m.group(2), validate=False)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"bad base64: {e}") from e


# ---------------------------------------------------------------- sidecar

def normalize_brief(brief) -> dict | None:
    """Coerce whatever a small model returned into the fixed key set; None if unusable."""
    if isinstance(brief, str):
        try:
            brief = json.loads(brief)
        except json.JSONDecodeError:
            return None
    if not isinstance(brief, dict):
        return None
    out: dict = {}
    for k in BRIEF_KEYS:
        v = brief.get(k)
        if k in _LIST_KEYS:
            if isinstance(v, str):
                v = [x.strip() for x in re.split(r"[,\n]", v) if x.strip()]
            out[k] = [str(x).strip() for x in (v or []) if str(x).strip()]
        else:
            out[k] = str(v or "").strip()
    if not any(out[k] for k in ("subject", "form", "features")):
        return None
    out["tags"] = sorted({re.sub(r"[^a-z0-9+_-]+", "-", t.lower()).strip("-") for t in out["tags"]} - {""})
    return out


def brief_markdown(brief: dict) -> str:
    def lst(xs):
        return "\n".join(f"- {x}" for x in xs) if xs else "-"
    return (
        "## Brief\n"
        f"**Subject:** {brief['subject'] or '-'}\n\n"
        f"**Style:** {', '.join(brief['style']) or '-'}\n\n"
        f"**Form:** {brief['form'] or '-'}\n\n"
        f"**Surface:** {brief['surface'] or '-'}\n\n"
        f"**Features to borrow:**\n{lst(brief['features'])}\n\n"
        f"**Materials / colours:** {brief['materials_colors'] or '-'}\n\n"
        f"**Print notes:** {brief['print_notes'] or '-'}\n\n"
        f"**build123d hints:**\n{lst(brief['build123d_hints'])}\n"
    )


def sidecar_text(meta: dict, brief: dict | None, log: list[str]) -> str:
    fm = "---\n" + "".join(
        f"{k}: {json.dumps(v) if isinstance(v, str) and (':' in v or v == '' or v[0] in '[{#') else v}\n"
        if not isinstance(v, list) else f"{k}: [{', '.join(v)}]\n"
        for k, v in meta.items()) + "---\n\n"
    body = brief_markdown(brief) if brief else "## Brief\n_(pending — no small-model reading yet; run the design-inspiration skill)_\n"
    return fm + body + "\n## Log\n" + "\n".join(log) + "\n"


def load_record(md: Path) -> dict:
    md = md.resolve()
    meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
    secs = split_sections(body)
    d = md.parent.parent
    kind = "model" if d.parent == MODELS_DIR else "idea"
    brief = secs.get("Brief", "")
    pending = str(meta.get("brief_model") or "none") in ("none", "pending") or brief.startswith("_(pending")
    subject = ""
    m = re.search(r"\*\*Subject:\*\*\s*(.+)", brief)
    if m:
        subject = m.group(1).strip()
    image = md.parent / str(meta.get("image") or f"{md.stem}.jpg")
    return {
        "id": str(meta.get("id") or md.stem), "kind": kind, "target": d.name, "path": str(md.relative_to(ROOT)),
        "image": str(image.relative_to(ROOT)) if image.exists() else "", "caption": str(meta.get("caption") or ""),
        "created": str(meta.get("created") or "")[:10], "source": str(meta.get("source") or ""),
        "brief_model": str(meta.get("brief_model") or "none"), "pending": pending, "subject": subject,
        "tags": [str(t) for t in (meta.get("tags") or [])], "brief": brief, "sections": secs,
    }


def list_records(kind: str | None = None, target: str | None = None) -> list[dict]:
    dirs: list[Path] = []
    if kind in (None, "model"):
        dirs += [MODELS_DIR / p / DIRNAME for p in list_projects() if target in (None, p)]
    if kind in (None, "idea"):
        dirs += [i.path.parent / DIRNAME for i in list_ideas() if target in (None, i.slug)]
    out = []
    for d in dirs:
        for md in sorted(d.glob("*.md")) if d.exists() else []:
            try:
                out.append(load_record(md))
            except Exception as e:  # noqa: BLE001 — a malformed sidecar must not hide the others
                out.append({"id": md.stem, "kind": "model" if d.parent.parent == MODELS_DIR else "idea", "target": d.parent.name,
                            "path": str(md.relative_to(ROOT)), "image": "", "caption": "", "created": "", "source": "",
                            "brief_model": "none", "pending": True, "subject": f"(unreadable sidecar: {e})", "tags": [], "brief": "", "sections": {}})
    return out


def filed_ids() -> set[str]:
    return {r["id"] for r in list_records()}


# ---------------------------------------------------------------- writing

def store(kind: str, slug: str, doc_id: str, image_bytes: bytes, *, caption: str = "", source: str = "", created: str = "",
          brief=None, brief_model: str = "", dry_run: bool = False) -> dict:
    """Write <id>.jpg + <id>.md under the target.  Returns the record dict (paths relative to ROOT)."""
    d = target_dir(kind, slug)
    jpg, md = d / f"{doc_id}.jpg", d / f"{doc_id}.md"
    nb = normalize_brief(brief)
    created = (created or time.strftime("%Y-%m-%dT%H:%M:%S"))
    meta = {"id": doc_id, "target": f"{'models' if kind == 'model' else 'ideas'}/{slug}", "created": created,
            "source": source or "local", "caption": caption.strip(), "image": jpg.name,
            "brief_model": (brief_model or "unknown") if nb else "pending", "tags": nb["tags"] if nb else []}
    text = sidecar_text(meta, nb, [f"- {created[:10]} filed from {source or 'local'}" + (f" (brief by {meta['brief_model']})" if nb else " (brief pending)")])
    if not dry_run:
        d.mkdir(parents=True, exist_ok=True)
        jpg.write_bytes(shrink(image_bytes))
        md.write_text(text, encoding="utf-8")
    return {"id": doc_id, "kind": kind, "target": slug, "path": str(md.relative_to(ROOT)), "image": str(jpg.relative_to(ROOT)),
            "pending": nb is None, "caption": meta["caption"], "tags": meta["tags"]}


def set_brief(md: Path, brief, model: str) -> dict:
    nb = normalize_brief(brief)
    if nb is None:
        raise ValueError("brief has none of subject/form/features — refusing to write an empty brief")
    md = md.resolve()
    raw, body = parse_front_matter(md.read_text(encoding="utf-8"))
    secs = split_sections(body)
    meta = {k: raw.get(k) for k in SIDECAR_KEYS if raw.get(k) not in (None, "")}  # the idea-file parser adds hardware/reuse/gaps defaults
    meta["brief_model"] = model
    meta["tags"] = nb["tags"]
    if nb["caption"] and not meta.get("caption"):
        meta["caption"] = nb["caption"]
    log = [ln for ln in secs.get("Log", "").splitlines() if ln.strip()]
    entry = f"- {time.strftime('%Y-%m-%d')} brief written by {model}"
    if not log or log[-1] != entry:
        log.append(entry)
    md.write_text(sidecar_text(meta, nb, log), encoding="utf-8")
    return load_record(md)


# ---------------------------------------------------------------- ingest (page inbox -> repo)

def _load_docs(sync_dir: Path) -> list[dict]:
    from scripts.sync_notes import load_docs
    return load_docs(sync_dir / DIRNAME)


def ingest(sync_dir: Path = SYNC_DIR, *, dry_run: bool = False) -> dict:
    docs = _load_docs(sync_dir)
    already = filed_ids()
    s: dict = {"docs": len(docs), "filed": [], "skipped": [], "errors": [], "pending": [], "ideas_created": [], "actions": []}
    for doc in docs:
        did = str(doc.get("id"))
        if doc.get("status", "inbox") != "inbox" and did in already:
            s["skipped"].append((did, "already filed"))
            continue
        if did in already:
            s["skipped"].append((did, "already in repo (db doc still says inbox — stamp it filed)"))
            rec = next(r for r in list_records() if r["id"] == did)
            s["actions"].append({"op": "update", "collection": "inspiration", "doc_id": did, "data": {"status": "filed", "path": rec["path"]}})
            continue
        try:
            img = decode_data_uri(str(doc.get("image") or ""))
            kind, slug, created_idea = resolve_target(str(doc.get("target_kind") or ""), str(doc.get("target") or ""),
                                                      str(doc.get("title") or ""), caption=str(doc.get("caption") or ""),
                                                      source="inspiration page", dry_run=dry_run)
        except ValueError as e:
            s["errors"].append((did, str(e)))
            continue
        if created_idea:
            s["ideas_created"].append(created_idea)
        rec = store(kind, slug, did, img, caption=str(doc.get("caption") or ""), source="inspiration page",
                    created=str(doc.get("created") or ""), brief=doc.get("brief"), brief_model=str(doc.get("brief_model") or "page quick tier"),
                    dry_run=dry_run)
        s["filed"].append(rec)
        if rec["pending"]:
            s["pending"].append(rec["path"])
        s["actions"].append({"op": "update", "collection": "inspiration", "doc_id": did,
                             "data": {"status": "filed", "path": rec["path"], "target_kind": kind, "target": slug}})
    if not dry_run:
        SYNC_DIR.mkdir(exist_ok=True)
        (SYNC_DIR / "inspiration_actions.json").write_text(json.dumps(s["actions"], indent=1), encoding="utf-8")
    return s


def format_ingest(s: dict, dry_run: bool) -> str:
    lines = [f"{'DRY RUN — ' if dry_run else ''}{s['docs']} document(s) in the inspiration inbox dump"]
    for r in s["filed"]:
        lines.append(f"  filed  {r['path']}   {'BRIEF PENDING' if r['pending'] else 'brief ok'}   {r['caption'][:60]}")
    for p in s["ideas_created"]:
        lines.append(f"  new idea  {p}  (status inbox — write it up)")
    for did, why in s["skipped"]:
        lines.append(f"  skip   {did}: {why}")
    for did, why in s["errors"]:
        lines.append(f"  ERROR  {did}: {why}  (left in the inbox; fix the target on the page or re-file by hand)")
    if s["pending"]:
        lines += ["", "briefs pending (write them with a Haiku subagent, then `set-brief`):"] + [f"  {p}" for p in s["pending"]]
    if not dry_run:
        lines.append(f"\ndb updates to apply (interactive sessions): .sync/inspiration_actions.json  ({len(s['actions'])})")
    return "\n".join(lines)


# ---------------------------------------------------------------- page

def page_data(with_images: bool = True) -> dict:
    from scripts.studio import git_head
    ideas = [{"slug": i.slug, "title": i.title, "status": i.status, "kind": i.kind} for i in list_ideas()]
    models = []
    for p in list_projects():
        doc = ""
        try:
            from scripts.studio import model_docstring
            doc = model_docstring(p).strip().split("\n\n")[0].replace("\n", " ")
        except Exception:  # noqa: BLE001
            pass
        models.append({"project": p, "summary": doc[:140]})
    recs = []
    for r in list_records():
        d = {k: r[k] for k in ("id", "kind", "target", "path", "caption", "created", "brief_model", "pending", "subject", "tags")}
        d["features"] = [ln[2:] for ln in (r["sections"].get("Brief", "").split("**Features to borrow:**")[-1].split("**")[0].splitlines()) if ln.startswith("- ")]
        if with_images and r["image"]:
            try:
                d["thumb"] = thumb_data_uri(ROOT / r["image"])
            except Exception:  # noqa: BLE001
                d["thumb"] = ""
        recs.append(d)
    return {"generated": time.strftime("%Y-%m-%d %H:%M"), "git": git_head(), "repo": ROOT.name, "models": models, "ideas": ideas,
            "filed": recs, "max_bytes": MAX_BYTES, "max_px": MAX_PX,
            "page": json.loads(INSPIRATION_JSON.read_text(encoding="utf-8")) if INSPIRATION_JSON.exists() else {}}


def write_html(d: dict, out: Path = OUT_HTML) -> Path:
    data = json.dumps(d).replace("</", "<\\/")
    page = (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", html.escape(f"{d['repo']} Inspiration"))
            .replace("__PROMPT__", json.dumps(BRIEF_PROMPT))
            .replace("__DATA__", data))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


# ---------------------------------------------------------------- cli

def format_list(recs: list[dict]) -> str:
    if not recs:
        return "no inspiration images yet (Inspiration page inbox, or `inspiration.py add <photo> --model|--idea|--new`)"
    lines = []
    cur = None
    for r in sorted(recs, key=lambda r: (r["kind"], r["target"], r["created"])):
        key = f"{'models' if r['kind'] == 'model' else 'ideas'}/{r['target']}"
        if key != cur:
            cur = key
            lines.append(f"{key}/{DIRNAME}/")
        flag = "BRIEF PENDING" if r["pending"] else f"brief by {r['brief_model']}"
        lines.append(f"  {r['id']:<22s} {r['created']:<10s} {flag:<22s} {r['subject'] or r['caption'] or '-'}")
        if r["caption"] and r["subject"]:
            lines.append(f"      caption: {r['caption'][:100]}")
        if r["tags"]:
            lines.append(f"      tags: {', '.join(r['tags'])}")
    n = sum(1 for r in recs if r["pending"])
    if n:
        lines.append(f"\n{n} brief(s) pending — `uv run python scripts/inspiration.py pending` lists them")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html", action="store_true", help="write exports/inspiration.html (the upload page)")
    ap.add_argument("--json", action="store_true", help="list as JSON")
    ap.add_argument("--out", type=Path, default=OUT_HTML)
    sub = ap.add_subparsers(dest="cmd")
    ing = sub.add_parser("ingest", help="file the page inbox dumped under .sync/")
    ing.add_argument("sync_dir", nargs="?", type=Path, default=SYNC_DIR)
    ing.add_argument("--dry-run", action="store_true")
    add = sub.add_parser("add", help="file a photo from disk")
    add.add_argument("image", type=Path)
    g = add.add_mutually_exclusive_group(required=True)
    g.add_argument("--model")
    g.add_argument("--idea")
    g.add_argument("--new", metavar="TITLE", help="create a new inbox idea with this title")
    add.add_argument("--caption", default="")
    add.add_argument("--brief", type=Path, help="JSON brief already written by a small model")
    add.add_argument("--brief-model", default="haiku")
    sub.add_parser("pending", help="sidecars whose brief is pending")
    sub.add_parser("prompt", help="print the brief prompt")
    sb = sub.add_parser("set-brief", help="attach a brief JSON to a sidecar")
    sb.add_argument("md", type=Path)
    sb.add_argument("--json", dest="brief_json", type=Path, required=True)
    sb.add_argument("--model", default="haiku")
    a = ap.parse_args(argv)

    if a.cmd == "ingest":
        s = ingest(a.sync_dir, dry_run=a.dry_run)
        print(format_ingest(s, a.dry_run))
        return 1 if s["errors"] and not s["filed"] else 0
    if a.cmd == "add":
        kind, slug, title = ("model", a.model, "") if a.model else ("idea", a.idea, "") if a.idea else ("new", "", a.new)
        kind, slug, created = resolve_target(kind, slug, title, caption=a.caption, source=f"local {a.image.name}")
        if created:
            print(f"new idea {created}")
        brief = json.loads(a.brief.read_text(encoding="utf-8")) if a.brief else None
        h = hashlib.sha1(a.image.read_bytes()).hexdigest()[:10]
        rec = store(kind, slug, f"l{h}", a.image.read_bytes(), caption=a.caption, source=f"local {a.image.name}", brief=brief, brief_model=a.brief_model)
        print(f"filed {rec['path']}  ({'brief pending' if rec['pending'] else 'brief ok'})")
        return 0
    if a.cmd == "pending":
        for r in list_records():
            if r["pending"]:
                print(f"{r['path']}\t{r['image']}\t{r['caption']}")
        return 0
    if a.cmd == "prompt":
        print(BRIEF_PROMPT)
        return 0
    if a.cmd == "set-brief":
        rec = set_brief(a.md, json.loads(a.brief_json.read_text(encoding="utf-8")), a.model)
        print(f"brief written: {rec['path']}  subject: {rec['subject']}  tags: {', '.join(rec['tags'])}")
        return 0

    recs = list_records()
    if a.json:
        print(json.dumps([{k: v for k, v in r.items() if k != "sections"} for r in recs], indent=1))
    else:
        print(format_list(recs))
        if INSPIRATION_JSON.exists():
            print(f"inspiration page: {json.loads(INSPIRATION_JSON.read_text())['artifact_url']}   (inbox: Artifact read_db collection 'inspiration' where status == inbox)")
    if a.html:
        out = write_html(page_data(True), a.out)
        print(f"\ninspiration page {out.relative_to(ROOT)}   ({out.stat().st_size // 1024} kB)")
        if INSPIRATION_JSON.exists():
            print(f"published at {json.loads(INSPIRATION_JSON.read_text())['artifact_url']}  — republish with the Artifact tool, url=<that>, same file path")
        else:
            print('not yet published: publish with the Artifact tool (capabilities {"db": {}, "sample": {}}) and record the URL in inspiration.json')
    return 0


if __name__ == "__main__":
    sys.exit(main())
