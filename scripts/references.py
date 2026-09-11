#!/usr/bin/env python
"""Reference models: 3D models found online, filed next to a model or an idea as design guides.

A photo tells you what a part should look like; a reference model tells you how a part that
already prints was built.  For compliant mechanisms (bistable switches, snap-through buckles,
living hinges, flexure stages) that is the difference between guessing a beam thickness and
reading one off a mesh that somebody has printed a thousand times.

Where they live
---------------
``models/<project>/references/<id>.md``    attached to a built model
``ideas/<slug>/references/<id>.md``        attached to an idea
``.../references/files/``                  gitignored: downloaded meshes, page images, renders

The ``.md`` sidecar is front matter (id, target, created, source, url, title, author, license,
why, files, images, reading_model, tags) plus sections:

``## Page``          what the hosting page says: summary, description (HTML stripped, capped),
                     the page's tags, the files it offers, image URLs.  Written by ``add``.
``## Measurements``  numbers read off an attached mesh: bbox, volume, min wall, and per Z-slice
                     the thinnest and thickest members (this is the beam thickness you wanted).
                     Written by ``attach`` / ``add --file``.
``## Reading``       the structured reading of the reference (mechanism, principle, key
                     dimensions, features to borrow, print notes, build123d hints, library map)
                     written by a SMALL model that looked at the page images and the render.
                     ``reading_model: pending`` until ``set-reading`` runs.
``## Log``           dated lines: what was borrowed, into which sketch or model.

Sources
-------
``search`` asks the sites that answer without a key: Printables (GraphQL), GitHub (repository
search), Sketchfab (v3 API) and, when ``THINGIVERSE_TOKEN`` is set, Thingiverse.  Everything
else (Thangs, Cults3D, MyMiniFactory, the BYU compliant-mechanism library, YouTube, papers) is
found with the web-search tool and filed by URL; ``add`` reads the page title / description /
direct mesh links generically.  Downloads: Printables and Thingiverse need a login, so the mesh
is fetched by hand and ``attach``ed; GitHub files and any direct link are fetched by ``add``.

Commands
--------
  uv run python scripts/references.py                          list everything (pending readings flagged)
  uv run python scripts/references.py search "bistable switch" [--source all|printables|github|sketchfab|thingiverse] [-n 8]
  uv run python scripts/references.py show <url>               read a page (no filing)
  uv run python scripts/references.py add <url|mesh> --model p | --idea slug | --new "title" [--why "..."] [--file mesh ...]
  uv run python scripts/references.py attach <md> <mesh> [--scale 25.4]   add a hand-downloaded mesh: measure + render
  uv run python scripts/references.py measure <mesh> [--scale k] [--json]  numbers off any mesh, nothing filed
  uv run python scripts/references.py pending                  references whose reading is still pending
  uv run python scripts/references.py prompt                   the reading prompt (for the subagent)
  uv run python scripts/references.py set-reading <md> --json reading.json --model "haiku subagent"
  uv run python scripts/references.py sources                  where to look, per kind of part
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR, ROOT, list_projects  # noqa: E402
from scripts.ideas import IDEAS_DIR, list_ideas, parse_front_matter, split_sections  # noqa: E402
from scripts.inspiration import resolve_target as _resolve_target  # noqa: E402

DIRNAME = "references"
FILES_DIRNAME = "files"
MESH_EXT = (".stl", ".3mf", ".obj", ".ply", ".off", ".glb", ".gltf")
CAD_EXT = MESH_EXT + (".step", ".stp", ".scad", ".f3d", ".f3z", ".sldprt", ".fcstd", ".iges", ".igs", ".dxf", ".svg")
DESCRIPTION_CAP = 3500
MAX_IMAGES = 4
TIMEOUT = 25
UA = "printing-references/1.0 (+build123d parts repo; reads public model pages)"

# The one prompt every small model answers, so readings are comparable whoever wrote them.
READING_PROMPT = """You are reading a reference 3D model for a designer who writes parametric parts in build123d and prints them on an FDM printer. The designer will NOT see the page or the pictures, only your reading, and wants to use this model as a guide for a part of their own: usually a mechanism (bistable switch, snap-through buckle, living hinge, flexure, latch, compliant gripper) whose behaviour is hard to predict from first principles, so what matters most is HOW the thing is built and WHAT NUMBERS it uses. Read the page text, the measurements table if there is one, and every image or render you are given. Be concrete: name shapes, count members, estimate proportions, quote dimensions when the page or the measurements give them and say "estimated" when you inferred one from a picture.

Reply with only one JSON object with exactly these keys:
{
  "subject": "what the object is, one short line",
  "mechanism": "the kind of mechanism or structure (bistable snap-through beam pair, living hinge, parallel flexure, cantilever snap, none...)",
  "principle": "how it works in 2-4 sentences: what flexes, where the stable states are, what stores the energy, what stops the motion",
  "key_dimensions": ["one entry per dimension that governs the behaviour: 'beam thickness 1.2 mm (measured)', 'beam angle ~8 deg (estimated)', 'hinge 0.4 mm x 2 layers (page)'"],
  "features": ["distinct features worth borrowing, each a short phrase"],
  "print_notes": "orientation on the bed, material the page reports, supports, tolerances the author mentions, what failed for them. 1-3 sentences.",
  "build123d_hints": ["for each borrowed feature, how to build it: sketch + extrude of the beam pair, mirror, polar pattern, offset, fillet at the root..."],
  "library_map": ["which library component of ours this resembles or would extend, as '<category>.<name>: how', or 'gap: <proposed id>'"],
  "tags": ["3 to 8 lowercase tags"],
  "caption": "one line for a list"
}
If the designer's note (why they saved this) is given, make sure the reading answers it. If you cannot tell something from what you were given, say so in that field instead of inventing a number."""

SIDECAR_KEYS = ("id", "target", "created", "source", "url", "title", "author", "license", "why", "files", "images", "reading_model", "tags")
READING_KEYS = ("subject", "mechanism", "principle", "key_dimensions", "features", "print_notes", "build123d_hints", "library_map", "tags", "caption")
_LIST_KEYS = {"key_dimensions", "features", "build123d_hints", "library_map", "tags"}

# ---------------------------------------------------------------- the curated source list

SOURCES = [
    ("printables", "https://www.printables.com/search/models?q=<query>", "keyless search + page read here; download by hand (login)",
     "the largest pool of functional prints with print settings in the description; filter by makes"),
    ("thingiverse", "https://www.thingiverse.com/search?q=<query>", "search here with THINGIVERSE_TOKEN; else web search `site:thingiverse.com <query>`",
     "old and huge; many classic compliant-mechanism demos (bistable switches, flexure fidgets) live here"),
    ("github", "https://github.com/search?q=<query>+stl", "keyless repo search + file listing here; files download here",
     "source models (OpenSCAD, build123d, CadQuery, FreeCAD) show the *parameters*, not just the mesh"),
    ("sketchfab", "https://sketchfab.com/search?q=<query>&type=models", "keyless search here; download needs a login",
     "good for looking at a mechanism from every side in the browser"),
    ("byu-cmr", "https://www.compliantmechanisms.byu.edu/maker-resources", "web search `site:compliantmechanisms.byu.edu <query>`",
     "the BYU Compliant Mechanisms Research library: printable bistable, LET-joint, ortho-planar, lamina-emergent demos with explanations"),
    ("thangs", "https://thangs.com/search/<query>", "web search `site:thangs.com <query>`", "geometry search across other hosts; useful when the name is unknown"),
    ("cults3d", "https://cults3d.com/en/search?q=<query>", "web search `site:cults3d.com <query>`", "paid + free; designers often document tolerances"),
    ("myminifactory", "https://www.myminifactory.com/search/?query=<query>", "web search `site:myminifactory.com <query>`", "curated, every object has a print photo"),
    ("papers", "alphaXiv / arXiv: `compliant bistable mechanism 3D printed`", "the alphaXiv tools", "for the equations: beam geometry vs. snap force, material vs. fatigue"),
    ("youtube", "https://www.youtube.com/results?search_query=<query>+3d+print", "web search", "build videos show the print orientation and the failure modes the page omits"),
]

# ---------------------------------------------------------------- network (monkeypatched in tests)


def http_get(url: str, *, headers: dict | None = None, data: bytes | None = None, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — public model pages
        return resp.read()


def get_json(url: str, *, headers: dict | None = None, data: dict | None = None) -> dict:
    body = json.dumps(data).encode("utf-8") if data is not None else None
    hdrs = {"Accept": "application/json", **({"Content-Type": "application/json"} if data is not None else {}), **(headers or {})}
    return json.loads(http_get(url, headers=hdrs, data=body).decode("utf-8"))


# ---------------------------------------------------------------- html -> text


class _Text(HTMLParser):
    _BREAK = {"p", "br", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol", "figure", "pre"}

    def __init__(self):
        super().__init__()
        self.out: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag == "li":
            self.out.append("\n- ")
        elif tag == "td" or tag == "th":
            self.out.append(" | ")
        elif tag in self._BREAK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        elif tag in self._BREAK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def strip_html(s: str, cap: int = DESCRIPTION_CAP) -> str:
    p = _Text()
    p.feed(s or "")
    text = html.unescape("".join(p.out))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > cap:
        text = text[:cap].rsplit("\n", 1)[0] + "\n…(truncated)"
    return text


def _meta_tag(page: str, prop: str) -> str:
    m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)["\']' % re.escape(prop), page, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']%s["\']' % re.escape(prop), page, re.I)
    return html.unescape(m.group(1)).strip() if m else ""


# ---------------------------------------------------------------- source adapters
# Each adapter has: ``match(url) -> native id | None``, ``search(q, n) -> [hit]``, ``fetch(native id) -> page``.
# A page is {source, id, url, title, author, license, summary, description, tags, files, images, downloadable}.
# A hit is the same shape, thinner.

_PRINTABLES_GQL = "https://api.printables.com/graphql/"
_PRINTABLES_SEARCH = """query ($q: String!, $n: Int!) { searchPrints2(query: $q, limit: $n) {
  items { id name slug summary likesCount downloadCount makesCount license { name } user { publicUsername } tags { name } } } }"""
_PRINTABLES_PRINT = """query ($id: ID!) { print(id: $id) { id name slug summary description datePublished likesCount downloadCount makesCount
  category { name } tags { name } license { name } user { publicUsername }
  stls { id name fileSize } gcodes { id name } images { filePath } } }"""


def _printables_url(pid: str, slug: str = "") -> str:
    return f"https://www.printables.com/model/{pid}" + (f"-{slug}" if slug else "")


def printables_match(url: str) -> str | None:
    m = re.search(r"printables\.com/(?:[a-z]{2}/)?model/(\d+)", url)
    return m.group(1) if m else None


def printables_search(q: str, n: int) -> list[dict]:
    d = get_json(_PRINTABLES_GQL, data={"query": _PRINTABLES_SEARCH, "variables": {"q": q, "n": n}})
    out = []
    for it in (d.get("data") or {}).get("searchPrints2", {}).get("items", []) or []:
        out.append({"source": "printables", "id": str(it["id"]), "url": _printables_url(it["id"], it.get("slug", "")), "title": it.get("name", ""),
                    "author": (it.get("user") or {}).get("publicUsername", ""), "license": (it.get("license") or {}).get("name", ""),
                    "summary": it.get("summary", "") or "", "score": f"{it.get('likesCount', 0)} likes · {it.get('makesCount', 0)} makes",
                    "tags": [t["name"] for t in it.get("tags") or []], "downloadable": "login"})
    return out


def printables_fetch(pid: str) -> dict:
    d = get_json(_PRINTABLES_GQL, data={"query": _PRINTABLES_PRINT, "variables": {"id": pid}})
    p = (d.get("data") or {}).get("print")
    if not p:
        raise ValueError(f"printables: no model with id {pid}: {d.get('errors')}")
    return {"source": "printables", "id": str(p["id"]), "url": _printables_url(p["id"], p.get("slug", "")), "title": p.get("name", ""),
            "author": (p.get("user") or {}).get("publicUsername", ""), "license": (p.get("license") or {}).get("name", ""),
            "summary": p.get("summary", "") or "", "description": strip_html(p.get("description", "")),
            "tags": [t["name"] for t in p.get("tags") or []] + ([p["category"]["name"]] if p.get("category") else []),
            "files": [f"{f['name']} ({(f.get('fileSize') or 0) // 1024} KB)" for f in p.get("stls") or []] + [g["name"] for g in p.get("gcodes") or []],
            "images": ["https://media.printables.com/" + im["filePath"] for im in (p.get("images") or [])[:MAX_IMAGES] if im.get("filePath")],
            "score": f"{p.get('likesCount', 0)} likes · {p.get('makesCount', 0)} makes · {p.get('downloadCount', 0)} downloads",
            "downloadable": "login", "published": (p.get("datePublished") or "")[:10]}


_GH_API = "https://api.github.com"


def _gh_headers() -> dict:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    return {"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {tok}"} if tok else {})}


def github_match(url: str) -> str | None:
    m = re.search(r"github\.com/([\w.-]+)/([\w.-]+)", url)
    return f"{m.group(1)}/{m.group(2).removesuffix('.git')}" if m else None


def github_search(q: str, n: int) -> list[dict]:
    d = get_json(f"{_GH_API}/search/repositories?q={urllib.parse.quote(q)}&per_page={n}", headers=_gh_headers())
    out = []
    for r in d.get("items", []) or []:
        out.append({"source": "github", "id": r["full_name"], "url": r["html_url"], "title": r["full_name"], "author": r["owner"]["login"],
                    "license": ((r.get("license") or {}).get("spdx_id") or ""), "summary": r.get("description") or "",
                    "score": f"{r.get('stargazers_count', 0)} stars", "tags": r.get("topics") or [], "downloadable": "yes"})
    return out


def github_fetch(full: str) -> dict:
    r = get_json(f"{_GH_API}/repos/{full}", headers=_gh_headers())
    branch = r.get("default_branch", "HEAD")
    try:
        tree = get_json(f"{_GH_API}/repos/{full}/git/trees/{branch}?recursive=1", headers=_gh_headers()).get("tree", [])
    except Exception:  # noqa: BLE001
        tree = []
    cad = [t["path"] for t in tree if t.get("type") == "blob" and t["path"].lower().endswith(CAD_EXT)]
    imgs = [t["path"] for t in tree if t.get("type") == "blob" and t["path"].lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))]
    readme = ""
    for name in ("README.md", "readme.md", "README.rst", "README.txt", "README"):
        try:
            readme = http_get(f"https://raw.githubusercontent.com/{full}/{branch}/{name}").decode("utf-8", "replace")
            break
        except Exception:  # noqa: BLE001
            continue
    raw = f"https://raw.githubusercontent.com/{full}/{branch}/"
    return {"source": "github", "id": full, "url": r["html_url"], "title": r["full_name"], "author": r["owner"]["login"],
            "license": ((r.get("license") or {}).get("spdx_id") or ""), "summary": r.get("description") or "",
            "description": strip_html(readme) if "<" in readme[:200] else readme[:DESCRIPTION_CAP],
            "tags": r.get("topics") or [], "files": [raw + p for p in cad[:40]], "images": [raw + p for p in imgs[:MAX_IMAGES]],
            "score": f"{r.get('stargazers_count', 0)} stars", "downloadable": "yes", "published": (r.get("pushed_at") or "")[:10]}


_SKF_API = "https://api.sketchfab.com/v3"


def sketchfab_match(url: str) -> str | None:
    m = re.search(r"sketchfab\.com/(?:3d-models|models)/(?:[\w-]+-)?([0-9a-f]{32})", url)
    return m.group(1) if m else None


def sketchfab_search(q: str, n: int) -> list[dict]:
    d = get_json(f"{_SKF_API}/search?type=models&q={urllib.parse.quote(q)}&count={n}")
    out = []
    for r in d.get("results", []) or []:
        out.append({"source": "sketchfab", "id": r["uid"], "url": r.get("viewerUrl", ""), "title": r.get("name", ""),
                    "author": (r.get("user") or {}).get("username", ""), "license": ((r.get("license") or {}).get("label") or ""),
                    "summary": "", "score": f"{r.get('likeCount', 0)} likes · {r.get('viewCount', 0)} views",
                    "tags": [t["name"] for t in r.get("tags") or []], "downloadable": "login" if r.get("isDownloadable") else "no"})
    return out


def sketchfab_fetch(uid: str) -> dict:
    r = get_json(f"{_SKF_API}/models/{uid}")
    thumbs = sorted(((r.get("thumbnails") or {}).get("images") or []), key=lambda t: -t.get("width", 0))
    return {"source": "sketchfab", "id": uid, "url": r.get("viewerUrl", ""), "title": r.get("name", ""),
            "author": (r.get("user") or {}).get("username", ""), "license": ((r.get("license") or {}).get("label") or ""),
            "summary": "", "description": strip_html(r.get("description", "")), "tags": [t["name"] for t in r.get("tags") or []],
            "files": [], "images": [t["url"] for t in thumbs[:1]], "score": f"{r.get('likeCount', 0)} likes · {r.get('viewCount', 0)} views",
            "downloadable": "login" if r.get("isDownloadable") else "no", "published": (r.get("publishedAt") or "")[:10]}


_TV_API = "https://api.thingiverse.com"


def _tv_headers() -> dict | None:
    tok = os.environ.get("THINGIVERSE_TOKEN")
    return {"Authorization": f"Bearer {tok}"} if tok else None


def thingiverse_match(url: str) -> str | None:
    m = re.search(r"thingiverse\.com/thing:(\d+)", url)
    return m.group(1) if m else None


def thingiverse_search(q: str, n: int) -> list[dict]:
    h = _tv_headers()
    if not h:
        return [{"source": "thingiverse", "id": "", "url": f"https://www.thingiverse.com/search?q={urllib.parse.quote(q)}", "title": "(no THINGIVERSE_TOKEN)",
                 "author": "", "license": "", "summary": "set THINGIVERSE_TOKEN (thingiverse.com/developers) or web-search `site:thingiverse.com " + q + "`",
                 "score": "", "tags": [], "downloadable": "?"}]
    d = get_json(f"{_TV_API}/search/{urllib.parse.quote(q)}?type=things&per_page={n}", headers=h)
    out = []
    for r in (d.get("hits") if isinstance(d, dict) else d) or []:
        out.append({"source": "thingiverse", "id": str(r["id"]), "url": r.get("public_url", ""), "title": r.get("name", ""),
                    "author": (r.get("creator") or {}).get("name", ""), "license": r.get("license", ""), "summary": "",
                    "score": f"{r.get('like_count', 0)} likes · {r.get('download_count', 0)} downloads", "tags": [], "downloadable": "token"})
    return out


def thingiverse_fetch(tid: str) -> dict:
    h = _tv_headers()
    url = f"https://www.thingiverse.com/thing:{tid}"
    if not h:
        page = generic_fetch(url)
        page.update({"source": "thingiverse", "id": tid, "downloadable": "login"})
        page["summary"] = page["summary"] or "no THINGIVERSE_TOKEN: only the page's meta tags were read; paste the description into the sidecar or set the token and re-add"
        return page
    r = get_json(f"{_TV_API}/things/{tid}", headers=h)
    try:
        files = get_json(f"{_TV_API}/things/{tid}/files", headers=h)
    except Exception:  # noqa: BLE001
        files = []
    try:
        images = get_json(f"{_TV_API}/things/{tid}/images", headers=h)
    except Exception:  # noqa: BLE001
        images = []
    imgs = []
    for im in images[:MAX_IMAGES]:
        best = next((s["url"] for s in im.get("sizes", []) if s.get("type") == "display" and s.get("size") == "large"), None)
        if best:
            imgs.append(best)
    return {"source": "thingiverse", "id": tid, "url": r.get("public_url", url), "title": r.get("name", ""), "author": (r.get("creator") or {}).get("name", ""),
            "license": r.get("license", ""), "summary": "", "description": strip_html(r.get("description_html") or r.get("description") or ""),
            "tags": [t["name"] for t in r.get("tags") or []] if isinstance(r.get("tags"), list) else [],
            "files": [f"{f['name']} ({(f.get('size') or 0) // 1024} KB) {f.get('download_url', '')}" for f in files],
            "images": imgs, "score": f"{r.get('like_count', 0)} likes · {r.get('download_count', 0)} downloads",
            "downloadable": "token", "published": (r.get("added") or "")[:10]}


def generic_fetch(url: str) -> dict:
    page = http_get(url, headers={"Accept": "text/html,*/*"}).decode("utf-8", "replace")
    title = _meta_tag(page, "og:title") or (re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S) or [None, ""])[1]
    desc = _meta_tag(page, "og:description") or _meta_tag(page, "description")
    img = _meta_tag(page, "og:image")
    base = url
    links = []
    for m in re.finditer(r'href=["\']([^"\']+)["\']', page, re.I):
        href = html.unescape(m.group(1))
        if href.lower().split("?")[0].endswith(CAD_EXT + (".zip",)):
            links.append(urllib.parse.urljoin(base, href))
    body = strip_html(page, cap=DESCRIPTION_CAP)
    return {"source": "web", "id": hashlib.sha1(url.encode()).hexdigest()[:10], "url": url, "title": html.unescape(title or "").strip(), "author": "",
            "license": "", "summary": desc, "description": body, "tags": [], "files": sorted(set(links))[:40],
            "images": [urllib.parse.urljoin(base, img)] if img else [], "score": "", "downloadable": "yes" if links else "?", "published": ""}


ADAPTERS = {
    "printables": (printables_match, printables_search, printables_fetch),
    "github": (github_match, github_search, github_fetch),
    "sketchfab": (sketchfab_match, sketchfab_search, sketchfab_fetch),
    "thingiverse": (thingiverse_match, thingiverse_search, thingiverse_fetch),
}


def identify(url: str) -> tuple[str, str]:
    """Return (source, native id) for a URL; ('web', sha) when no adapter matches."""
    for name, (match, _s, _f) in ADAPTERS.items():
        nid = match(url)
        if nid:
            return name, nid
    return "web", hashlib.sha1(url.encode()).hexdigest()[:10]


def fetch_page(url: str) -> dict:
    source, nid = identify(url)
    if source == "web":
        return generic_fetch(url)
    return ADAPTERS[source][2](nid)


def search(q: str, n: int = 8, source: str = "all") -> list[dict]:
    names = list(ADAPTERS) if source == "all" else [source]
    hits: list[dict] = []
    for name in names:
        try:
            hits += ADAPTERS[name][1](q, n)
        except Exception as e:  # noqa: BLE001 — one site down must not hide the others
            hits.append({"source": name, "id": "", "url": "", "title": f"(search failed: {e})", "author": "", "license": "", "summary": "",
                         "score": "", "tags": [], "downloadable": "?"})
    return hits


def format_search(hits: list[dict]) -> str:
    if not hits:
        return "(no hits)"
    lines = []
    for h in hits:
        dl = {"yes": "download: direct", "login": "download: needs login (attach by hand)", "token": "download: with token", "no": "download: no", "?": ""}.get(h.get("downloadable", "?"), "")
        head = f"[{h['source']}] {h['title']}" + (f"  — {h['author']}" if h.get("author") else "") + (f"  ({h['score']})" if h.get("score") else "")
        lines.append(head)
        if h.get("url"):
            lines.append(f"    {h['url']}")
        meta = "  ·  ".join(x for x in (h.get("license", ""), dl, ", ".join(h.get("tags", [])[:6])) if x)
        if meta:
            lines.append(f"    {meta}")
        if h.get("summary"):
            lines.append(f"    {h['summary'][:160]}")
    return "\n".join(lines)


def format_page(p: dict) -> str:
    lines = [f"{p['title']}   [{p['source']}:{p['id']}]", f"{p['url']}",
             "  ·  ".join(x for x in (p.get("author") and f"by {p['author']}", p.get("license"), p.get("score"), p.get("published")) if x)]
    if p.get("summary"):
        lines += ["", p["summary"]]
    if p.get("tags"):
        lines.append("tags: " + ", ".join(p["tags"][:12]))
    if p.get("files"):
        lines.append(f"files ({len(p['files'])}, download {p.get('downloadable', '?')}):")
        lines += [f"  {f}" for f in p["files"][:15]]
    if p.get("images"):
        lines.append(f"images: {len(p['images'])}")
    if p.get("description"):
        lines += ["", p["description"]]
    return "\n".join(lines)


# ---------------------------------------------------------------- mesh measurement


def load_mesh(path: Path, scale: float = 1.0):
    import trimesh

    m = trimesh.load(str(path), force="mesh")
    if scale != 1.0:
        m.apply_scale(scale)
    return m


WIDTH_LADDER = (0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0)


def _count(geom) -> int:
    return 0 if geom.is_empty else len(getattr(geom, "geoms", [geom]))


def _slice_stats(mesh, z: float) -> dict | None:
    """Members of the cross-section at height z, read with morphological erosion.

    The section becomes shapely polygons.  Insetting the shape by r removes every member thinner
    than 2r; insetting then outsetting (an opening) gives back everything else, so the area lost
    at each r is the area of members thinner than 2r.  Three readings come out of that:

    * ``members``: for a ladder of widths, the % of area in members at most that wide (fragments
      shorter than two widths are ignored: the disc also shaves the convex corners of blocks).
    * ``hinge_mm``: the width at which the eroded shape first breaks into MORE pieces (or a piece
      vanishes).  That is a living hinge or a neck joining two bodies: tiny in area, so an area
      threshold never sees it, but it is the member that flexes.
    * ``beam_mm``: the first ladder width after the hinge's own step at which members holding at
      least 1 % of the area appear: the flexing beams.  ``thinnest_member_mm`` is the smaller of
      hinge and beam; ``thickest_member_mm`` is the largest inscribed disc (the hub or block).
      All of these are widths IN THE SLICE PLANE; the part's depth is the Z extent.
    """
    import numpy as np
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    def buf(g, r):  # round joins: a true disc opening (a disc cannot reach a sharp corner, so a box loses ~0.02 %)
        return g.buffer(r)

    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return None
    try:
        planar, _ = sec.to_2D() if hasattr(sec, "to_2D") else sec.to_planar()
        polys = [Polygon(p.exterior.coords, [i.coords for i in p.interiors]) for p in planar.polygons_full]
    except Exception:  # noqa: BLE001
        return None
    polys = [p for p in polys if p.is_valid and p.area > 1e-6]
    if not polys:
        return None
    shape = unary_union(polys)
    area = shape.area
    if area <= 0:
        return None
    islands = _count(shape)
    # thickest: largest inset leaving material
    lo, hi = 0.0, float(max(mesh.extents[:2]))
    for _ in range(30):
        mid = (lo + hi) / 2
        if buf(shape, -mid).is_empty:
            hi = mid
        else:
            lo = mid
    thickest = 2 * lo
    # width ladder: area in members no wider than w, and the first width that breaks the section
    members = []
    hinge = None
    hinge_step = None
    beam = None
    prev = 0.0
    for w in WIDTH_LADDER:
        if w > thickest:
            break
        eroded = buf(shape, -w / 2)
        # what the opening removes, but only fragments at least ~2 widths long: a disc also shaves
        # every convex corner of a block, and those slivers are not members
        gone = shape.difference(buf(eroded, w / 2))
        lost = sum(g.area for g in getattr(gone, "geoms", [gone]) if g.area >= 2.0 * w * w)
        lost_pct = max(prev, 100.0 * lost / area)
        step = lost_pct - prev
        members.append({"width_mm": w, "area_pct": round(lost_pct, 2), "step_pct": round(step, 2)})
        if hinge is None and _count(eroded) != islands:
            hinge = w
            hinge_step = w
        # beam: the first width AFTER the hinge's own step whose members add at least 1 % of the area
        if beam is None and step >= 1.0 and (hinge_step is None or w > hinge_step) and w > WIDTH_LADDER[0]:
            beam = w
        prev = lost_pct
    # refine the hinge width by bisection inside its ladder step
    if hinge is not None:
        i = WIDTH_LADDER.index(hinge)
        lo = WIDTH_LADDER[i - 1] if i else 0.0
        hi = hinge
        for _ in range(12):
            mid = (lo + hi) / 2
            if _count(buf(shape, -mid / 2)) != islands:
                hi = mid
            else:
                lo = mid
        hinge = round(hi, 2)
    cands = [x for x in (hinge, beam) if x is not None]
    thinnest = min(cands) if cands else None
    return {"z_mm": round(float(z), 2), "islands": int(islands), "area_mm2": round(float(area), 1),
            "thinnest_member_mm": thinnest, "hinge_mm": hinge, "beam_mm": beam, "thickest_member_mm": round(float(thickest), 2),
            "members": members, "bbox_mm": [round(float(x), 1) for x in np.array(shape.bounds)[2:] - np.array(shape.bounds)[:2]]}


def measure(mesh, *, slices: tuple[float, ...] = (0.15, 0.35, 0.5, 0.65, 0.85), samples: int = 3000) -> dict:
    from scripts.check_printable import check_mesh

    rep = check_mesh(mesh, samples=samples)
    zmin, zmax = float(mesh.bounds[0][2]), float(mesh.bounds[1][2])
    out = {"faces": int(len(mesh.faces)), "watertight": rep["watertight"], "bodies": rep["bodies"], "bbox_mm": rep["bbox_mm"],
           "volume_mm3": rep["volume_mm3"], "wall_min_mm": rep.get("wall_min_mm"), "wall_p05_mm": rep.get("wall_p05_mm"),
           "overhang_pct_of_surface": rep["overhang_pct_of_surface"], "bed_contact_area_mm2": rep["bed_contact_area_mm2"],
           "slices": [s for s in (_slice_stats(mesh, zmin + f * (zmax - zmin)) for f in slices) if s]}
    ext = max(out["bbox_mm"])
    out["units_note"] = ("extents under 5 mm: probably inches or metres, re-run with --scale 25.4 or 1000" if ext < 5
                         else "extents over 600 mm: probably not millimetres, re-run with --scale 0.1 or 0.001" if ext > 600 else "")
    thin = [s["thinnest_member_mm"] for s in out["slices"] if s["thinnest_member_mm"] is not None]
    out["thinnest_member_mm"] = min(thin) if thin else None
    hinges = [s["hinge_mm"] for s in out["slices"] if s["hinge_mm"] is not None]
    out["hinge_mm"] = min(hinges) if hinges else None
    beams = [s["beam_mm"] for s in out["slices"] if s["beam_mm"] is not None]
    out["beam_mm"] = min(beams) if beams else None
    thick = [s["thickest_member_mm"] for s in out["slices"]]
    out["thickest_member_mm"] = max(thick) if thick else None
    return out


def measurements_markdown(m: dict, name: str) -> str:
    bb = " x ".join(f"{x:g}" for x in m["bbox_mm"])
    lines = ["## Measurements", f"`{name}` — {m['faces']} faces, {'watertight' if m['watertight'] else 'NOT watertight'}, {m['bodies']} body(ies)", "",
             "| metric | value |", "|---|---|", f"| bbox X x Y x Z (mm) | {bb} |", f"| depth along Z (print height as filed) | {m['bbox_mm'][2]:g} mm |",
             f"| volume | {m['volume_mm3'] / 1000:.1f} cm³ |",
             f"| min wall (inward ray) | {m['wall_min_mm']} mm (p05 {m['wall_p05_mm']}) |",
             f"| living hinge / neck width in plane (splits the section) | {m['hinge_mm'] if m.get('hinge_mm') is not None else 'none found'} mm |",
             f"| beam width in plane (first members holding ≥1 % of area after the hinge) | {m['beam_mm'] if m.get('beam_mm') is not None else 'none found'} mm |",
             f"| thinnest member in plane | {m['thinnest_member_mm']} mm |",
             f"| thickest member in plane (largest inscribed disc: hub / block) | {m['thickest_member_mm']} mm |",
             f"| overhang > 45° | {m['overhang_pct_of_surface']}% of surface |", f"| bed contact | {m['bed_contact_area_mm2']} mm² |"]
    if m["slices"]:
        lines += ["", "| slice z | islands | area mm² | hinge | beam | thickest | extent |", "|---|---|---|---|---|---|---|"]
        lines += [f"| {s['z_mm']} | {s['islands']} | {s['area_mm2']} | {s['hinge_mm'] if s['hinge_mm'] is not None else '-'} | {s['beam_mm'] if s['beam_mm'] is not None else '-'} | {s['thickest_member_mm']} | {' x '.join(f'{x:g}' for x in s['bbox_mm'])} |"
                  for s in m["slices"]]
        mid = m["slices"][len(m["slices"]) // 2]
        if mid.get("members"):
            lines += ["", "member width histogram (mid slice; % of area first appearing at each width): "
                      + (", ".join(f"{x['width_mm']:g} mm +{x['step_pct']:g}%" for x in mid["members"] if x["step_pct"] >= 0.3) or "-")]
    if m.get("units_note"):
        lines += ["", f"⚠ {m['units_note']}"]
    lines += ["", "All member widths are measured IN THE SLICE PLANE (XY); the Z depth is the row above. hinge = thinnest neck joining two pieces of the section (a living hinge); beam = first width after it where members holding ≥1 % of the area appear.",
              "Members are read per Z slice as the mesh sits: re-orient (or re-run `measure` on a rotated copy) if the flexing members do not lie in XY."]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- sidecars


def target_dir(kind: str, slug: str) -> Path:
    if kind == "model":
        return MODELS_DIR / slug / DIRNAME
    if kind == "idea":
        return IDEAS_DIR / slug / DIRNAME
    raise ValueError(f"unknown target kind {kind!r}")


def resolve_target(kind: str, slug: str = "", title: str = "", *, why: str = "", source: str = "", dry_run: bool = False):
    return _resolve_target(kind, slug, title, caption=why, source=source or "reference model", dry_run=dry_run)


def normalize_reading(reading) -> dict | None:
    if isinstance(reading, str):
        s = reading.strip()
        if s.startswith("```"):
            s = re.sub(r"^```\w*\n|\n```$", "", s, flags=re.S)
        try:
            reading = json.loads(s)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", s, re.S)
            if not m:
                return None
            try:
                reading = json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    if not isinstance(reading, dict):
        return None
    out: dict = {}
    for k in READING_KEYS:
        v = reading.get(k)
        if k in _LIST_KEYS:
            if isinstance(v, str):
                v = [x.strip() for x in re.split(r"[,\n]", v) if x.strip()]
            out[k] = [str(x).strip() for x in (v or []) if str(x).strip()]
        else:
            out[k] = str(v or "").strip()
    seen: set[str] = set()
    out["tags"] = [t for t in (t.lower().strip() for t in out["tags"]) if t and not (t in seen or seen.add(t))]
    if not (out["subject"] or out["mechanism"] or out["features"] or out["key_dimensions"]):
        return None
    return out


def reading_markdown(r: dict) -> str:
    def lst(xs):
        return "\n".join(f"- {x}" for x in xs) if xs else "-"
    return ("## Reading\n"
            f"**Subject:** {r['subject'] or '-'}\n\n"
            f"**Mechanism:** {r['mechanism'] or '-'}\n\n"
            f"**Principle:** {r['principle'] or '-'}\n\n"
            f"**Key dimensions:**\n{lst(r['key_dimensions'])}\n\n"
            f"**Features to borrow:**\n{lst(r['features'])}\n\n"
            f"**Print notes:** {r['print_notes'] or '-'}\n\n"
            f"**build123d hints:**\n{lst(r['build123d_hints'])}\n\n"
            f"**Library map:**\n{lst(r['library_map'])}\n")


PENDING_READING = "## Reading\n_(pending — no small-model reading yet; run the design-references skill)_\n"


def page_markdown(p: dict) -> str:
    lines = ["## Page"]
    if p.get("summary"):
        lines.append(p["summary"])
    if p.get("score") or p.get("published"):
        lines.append("  ·  ".join(x for x in (p.get("score"), p.get("published") and f"published {p['published']}") if x))
    if p.get("tags"):
        lines.append("tags: " + ", ".join(p["tags"][:15]))
    if p.get("files"):
        lines.append(f"files on the page (download {p.get('downloadable', '?')}):")
        lines += [f"- {f}" for f in p["files"][:15]]
    if p.get("images"):
        lines.append("images:")
        lines += [f"- {u}" for u in p["images"]]
    if p.get("description"):
        lines += ["", "### Description", p["description"]]
    return "\n".join(lines) + "\n"


def _fm_value(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    v = "" if v is None else str(v)
    return json.dumps(v) if (v == "" or ":" in v or "#" in v or v[0] in "[{\"'") else v


def sidecar_text(meta: dict, sections: dict[str, str], log: list[str]) -> str:
    fm = "---\n" + "".join(f"{k}: {_fm_value(meta.get(k))}\n" for k in SIDECAR_KEYS) + "---\n\n"
    body = sections.get("Page", "## Page\n-\n") + "\n" + sections.get("Measurements", "") + ("\n" if sections.get("Measurements") else "") \
        + sections.get("Reading", PENDING_READING)
    return fm + body + "\n## Log\n" + "\n".join(log) + "\n"


def _section_text(secs: dict[str, str], name: str) -> str:
    return f"## {name}\n{secs[name]}\n" if secs.get(name) else ""


def load_record(md: Path) -> dict:
    md = md.resolve()
    meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
    secs = split_sections(body)
    d = md.parent.parent
    kind = "model" if d.parent == MODELS_DIR else "idea"
    reading = secs.get("Reading", "")
    pending = str(meta.get("reading_model") or "none") in ("none", "pending") or reading.startswith("_(pending")
    m = re.search(r"\*\*Mechanism:\*\*\s*(.+)", reading)
    mechanism = m.group(1).strip() if m else ""
    m = re.search(r"\*\*Subject:\*\*\s*(.+)", reading)
    subject = m.group(1).strip() if m else ""
    files = [str(f) for f in (meta.get("files") or []) if f]
    fdir = md.parent / FILES_DIRNAME
    return {
        "id": str(meta.get("id") or md.stem), "kind": kind, "target": d.name, "path": str(md.relative_to(ROOT)),
        "source": str(meta.get("source") or ""), "url": str(meta.get("url") or ""), "title": str(meta.get("title") or md.stem),
        "author": str(meta.get("author") or ""), "license": str(meta.get("license") or ""), "why": str(meta.get("why") or ""),
        "created": str(meta.get("created") or "")[:10], "files": files, "files_present": [f for f in files if (fdir / f).exists()],
        "images": [str(x) for x in (meta.get("images") or []) if x], "reading_model": str(meta.get("reading_model") or "none"),
        "pending": pending, "subject": subject, "mechanism": mechanism, "tags": [str(t) for t in (meta.get("tags") or [])],
        "measured": bool(secs.get("Measurements")), "sections": secs, "log": secs.get("Log", ""),
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
                            "path": str(md.relative_to(ROOT)), "source": "", "url": "", "title": f"(unreadable sidecar: {e})", "author": "",
                            "license": "", "why": "", "created": "", "files": [], "files_present": [], "images": [], "reading_model": "none",
                            "pending": True, "subject": "", "mechanism": "", "tags": [], "measured": False, "sections": {}, "log": ""})
    return out


def _rewrite(md: Path, meta: dict, secs: dict[str, str], log_line: str | None = None) -> None:
    log = [ln for ln in secs.get("Log", "").splitlines() if ln.strip()]
    if log_line:
        log.append(log_line)
    sections = {"Page": _section_text(secs, "Page"), "Measurements": _section_text(secs, "Measurements"),
                "Reading": _section_text(secs, "Reading") or PENDING_READING}
    md.write_text(sidecar_text(meta, sections, log), encoding="utf-8")


def _slug_id(source: str, nid: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", f"{source}-{nid}").strip("-")[:80]


def store(kind: str, slug: str, page: dict, *, why: str = "", created: str = "") -> dict:
    """Write the sidecar for a fetched page. Returns the record."""
    d = target_dir(kind, slug)
    d.mkdir(parents=True, exist_ok=True)
    rid = _slug_id(page["source"], page["id"])
    md = d / f"{rid}.md"
    today = created or time.strftime("%Y-%m-%d")
    meta = {"id": rid, "target": f"{kind}:{slug}", "created": today, "source": page["source"], "url": page.get("url", ""),
            "title": page.get("title", "") or rid, "author": page.get("author", ""), "license": page.get("license", ""), "why": why,
            "files": [], "images": [], "reading_model": "pending", "tags": [t.lower() for t in page.get("tags", [])][:8]}
    secs: dict[str, str] = {}
    if md.exists():  # re-add: keep files, measurements, reading and log; refresh the page read
        old_meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
        secs = split_sections(body)
        for k in ("files", "images", "reading_model", "created"):
            meta[k] = old_meta.get(k) or meta[k]
        meta["why"] = why or str(old_meta.get("why") or "")
        log_line = f"- {today} page re-read"
    else:
        log_line = f"- {today} filed from {page['source']}" + (f": {why}" if why else "")
    secs["Page"] = page_markdown(page).split("\n", 1)[1]
    _rewrite(md, meta, secs, log_line)
    return load_record(md)


def save_images(md: Path, urls: list[str]) -> list[str]:
    """Download page images (downscaled) into files/ for the small model to read. Returns relative names."""
    from scripts.inspiration import shrink

    fdir = md.parent / FILES_DIRNAME
    fdir.mkdir(exist_ok=True)
    names = []
    for i, u in enumerate(urls[:MAX_IMAGES], 1):
        name = f"{md.stem}-img{i}.jpg"
        try:
            (fdir / name).write_bytes(shrink(http_get(u, headers={"Accept": "image/*"})))
            names.append(name)
        except Exception as e:  # noqa: BLE001
            print(f"  image {u}: {e}", file=sys.stderr)
    if names:
        meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
        meta["images"] = sorted(set([str(x) for x in (meta.get("images") or []) if x] + names))
        _rewrite(md, meta, split_sections(body))
    return names


def attach(md: Path, mesh_path: Path, *, scale: float = 1.0, render: bool = True) -> dict:
    """Copy a mesh into files/, measure it, render it, and write the Measurements section."""
    fdir = md.parent / FILES_DIRNAME
    fdir.mkdir(exist_ok=True)
    dest = fdir / mesh_path.name
    if mesh_path.resolve() != dest.resolve():
        shutil.copy2(mesh_path, dest)
    mesh = load_mesh(dest, scale)
    m = measure(mesh)
    meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
    secs = split_sections(body)
    existing = secs.get("Measurements", "")
    block = measurements_markdown(m, mesh_path.name + (f" (scaled x{scale:g})" if scale != 1.0 else "")).split("\n", 1)[1].rstrip()
    secs["Measurements"] = (existing.rstrip() + "\n\n" + block) if existing and f"`{mesh_path.name}" not in existing else block
    meta["files"] = sorted(set([str(x) for x in (meta.get("files") or []) if x] + [mesh_path.name]))
    png = ""
    if render:
        try:
            from scripts.render import render_mesh
            png = f"{md.stem}-{mesh_path.stem}-render.png"
            render_mesh(mesh, fdir / png, f"{meta.get('title', md.stem)} / {mesh_path.name}")
            meta["images"] = sorted(set([str(x) for x in (meta.get("images") or []) if x] + [png]))
        except Exception as e:  # noqa: BLE001
            print(f"  render failed: {e}", file=sys.stderr)
            png = ""
    _rewrite(md, meta, secs, f"- {time.strftime('%Y-%m-%d')} attached {mesh_path.name}: thinnest member {m['thinnest_member_mm']} mm, min wall {m['wall_min_mm']} mm")
    m["render"] = png
    return m


def download_file(url: str, md: Path) -> Path:
    """Fetch a direct mesh/CAD link into files/ (GitHub blob URLs are turned into raw URLs)."""
    m = re.match(r"https?://github\.com/([\w.-]+/[\w.-]+)/blob/([^/]+)/(.+)", url)
    if m:
        url = f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{m.group(3)}"
    name = Path(urllib.parse.urlparse(url).path).name or "download.bin"
    fdir = md.parent / FILES_DIRNAME
    fdir.mkdir(exist_ok=True)
    dest = fdir / name
    dest.write_bytes(http_get(url, headers={"Accept": "*/*"}))
    if not name.lower().endswith(MESH_EXT):
        meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
        meta["files"] = sorted(set([str(x) for x in (meta.get("files") or []) if x] + [name]))
        _rewrite(md, meta, split_sections(body), f"- {time.strftime('%Y-%m-%d')} downloaded {name} (source file, not measured)")
    return dest


def set_reading(md: Path, reading, model: str) -> dict:
    nr = normalize_reading(reading)
    if nr is None:
        raise ValueError("reading has no subject / mechanism / features / key dimensions: refusing to mark it read")
    meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
    secs = split_sections(body)
    secs["Reading"] = reading_markdown(nr).split("\n", 1)[1].rstrip()
    meta["reading_model"] = model
    tags = [str(t) for t in (meta.get("tags") or [])]
    meta["tags"] = list(dict.fromkeys(nr["tags"] + tags))[:10]
    _rewrite(md, meta, secs, f"- {time.strftime('%Y-%m-%d')} reading by {model}")
    return load_record(md)


def add_log(md: Path, text: str) -> None:
    meta, body = parse_front_matter(md.read_text(encoding="utf-8"))
    _rewrite(md, meta, split_sections(body), f"- {time.strftime('%Y-%m-%d')} {text}")


# ---------------------------------------------------------------- listing


def format_list(recs: list[dict]) -> str:
    if not recs:
        return "no reference models filed yet (references.py search \"...\" then add <url> --model p | --idea slug | --new \"title\")"
    lines = []
    cur = None
    for r in recs:
        key = (r["kind"], r["target"])
        if key != cur:
            cur = key
            lines.append(f"{r['kind']} {r['target']}")
        flag = "READING PENDING  " if r["pending"] else ""
        what = r["mechanism"] or r["subject"] or r["why"] or "-"
        lines.append(f"  {r['path']}  {flag}{r['title'][:60]}  [{r['source']}]  {what[:80]}")
        extra = []
        if r["files"]:
            missing = [f for f in r["files"] if f not in r["files_present"]]
            extra.append(f"files: {', '.join(r['files'])}" + (f" (missing locally: {', '.join(missing)}; re-download and attach)" if missing else ""))
        if r["measured"]:
            extra.append("measured")
        if r["url"]:
            extra.append(r["url"])
        if extra:
            lines.append("      " + "  ·  ".join(extra))
    return "\n".join(lines)


def format_sources() -> str:
    lines = ["where to look (search recipes; `references.py search` covers the first four without a key):", ""]
    for name, url, how, note in SOURCES:
        lines += [f"{name:<14s} {url}", f"{'':14s} how: {how}", f"{'':14s} {note}", ""]
    lines += ["search phrases that find mechanisms: the mechanism noun + 'compliant' or 'print in place' + the function, e.g.",
              "  'bistable compliant switch', 'snap through buckle clip', 'living hinge box', 'flexure stage linear', 'ortho-planar spring',",
              "  'LET joint', 'compliant gripper', 'constant force mechanism', 'toggle latch print in place'.",
              "prefer hits with makes / print photos and a description that states material and beam thickness; those numbers are the point."]
    return "\n".join(lines)


# ---------------------------------------------------------------- cli


def _target_args(p: argparse.ArgumentParser) -> None:
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--model", help="attach to models/<project>")
    g.add_argument("--idea", help="attach to ideas/<slug>")
    g.add_argument("--new", metavar="TITLE", help="create ideas/<slug>/IDEA.md (status inbox) and attach there")


def _resolve_from_args(a, *, why: str = "", source: str = "") -> tuple[str, str, str | None]:
    if a.model:
        return resolve_target("model", a.model)
    if a.idea:
        return resolve_target("idea", a.idea)
    return resolve_target("new", title=a.new, why=why, source=source)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("search", help="search the keyless sites")
    p.add_argument("query")
    p.add_argument("--source", default="all", choices=["all", *ADAPTERS])
    p.add_argument("-n", type=int, default=8)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("show", help="read a model page without filing it")
    p.add_argument("url")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("add", help="file a reference (URL or local mesh) next to a model or idea")
    p.add_argument("what", help="page URL or a local mesh file")
    _target_args(p)
    p.add_argument("--why", default="", help="one line: what you want to learn from it")
    p.add_argument("--file", action="append", default=[], help="local mesh(es) to attach and measure")
    p.add_argument("--download", action="append", default=[], help="direct file URL(s) to fetch into files/ (GitHub blob links ok)")
    p.add_argument("--scale", type=float, default=1.0, help="scale attached meshes (25.4 for inches)")
    p.add_argument("--no-images", action="store_true", help="do not download the page's images")
    p = sub.add_parser("attach", help="attach a hand-downloaded mesh to a filed reference and measure it")
    p.add_argument("md", type=Path)
    p.add_argument("mesh", type=Path)
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--no-render", action="store_true")
    p = sub.add_parser("measure", help="numbers off a mesh, nothing filed")
    p.add_argument("mesh", type=Path)
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--json", action="store_true")
    sub.add_parser("pending", help="references without a reading")
    sub.add_parser("prompt", help="print the reading prompt")
    sub.add_parser("sources", help="where to look")
    p = sub.add_parser("set-reading", help="attach a small model's reading to a sidecar")
    p.add_argument("md", type=Path)
    p.add_argument("--json", type=Path, required=True, help="file holding the reading JSON")
    p.add_argument("--model", required=True, help="who wrote it, e.g. 'haiku subagent'")
    p = sub.add_parser("log", help="append a dated line to a sidecar's Log")
    p.add_argument("md", type=Path)
    p.add_argument("text")
    p = sub.add_parser("list", help="list filed references (default)")
    p.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "search":
        hits = search(a.query, a.n, a.source)
        print(json.dumps(hits, indent=1) if a.json else format_search(hits))
        return 0
    if a.cmd == "show":
        page = fetch_page(a.url)
        print(json.dumps(page, indent=1) if a.json else format_page(page))
        return 0
    if a.cmd == "sources":
        print(format_sources())
        return 0
    if a.cmd == "prompt":
        print(READING_PROMPT)
        return 0
    if a.cmd == "measure":
        m = measure(load_mesh(a.mesh, a.scale))
        print(json.dumps(m, indent=1) if a.json else measurements_markdown(m, a.mesh.name))
        return 0
    if a.cmd == "add":
        local = Path(a.what)
        is_file = local.exists() and local.suffix.lower() in MESH_EXT
        kind, slug, created_idea = _resolve_from_args(a, why=a.why, source="reference model")
        if created_idea:
            print(f"created {created_idea} (status inbox)")
        if is_file:
            page = {"source": "file", "id": hashlib.sha1(local.read_bytes()).hexdigest()[:10], "url": "", "title": local.stem, "author": "",
                    "license": "", "summary": f"local mesh {local.name}", "description": "", "tags": [], "files": [], "images": [], "score": "", "downloadable": "yes"}
            files = [local] + [Path(f) for f in a.file]
        else:
            page = fetch_page(a.what)
            files = [Path(f) for f in a.file]
        rec = store(kind, slug, page, why=a.why)
        md = ROOT / rec["path"]
        print(f"filed {rec['path']}  ({page['source']}: {page['title']})")
        if not is_file and not a.no_images and page.get("images"):
            names = save_images(md, page["images"])
            print(f"  images for the reader: {', '.join(names) or 'none fetched'}  (in {md.parent.name}/{FILES_DIRNAME}/, gitignored)")
        for u in a.download:
            try:
                dest = download_file(u, md)
                print(f"  downloaded {dest.name}")
                if dest.suffix.lower() in MESH_EXT:
                    files.append(dest)
            except Exception as e:  # noqa: BLE001
                print(f"  download {u}: {e}")
        for f in files:
            m = attach(md, f, scale=a.scale)
            print(f"  attached {f.name}: bbox {' x '.join(f'{x:g}' for x in m['bbox_mm'])} mm, thinnest member {m['thinnest_member_mm']} mm, min wall {m['wall_min_mm']} mm"
                  + (f", render {FILES_DIRNAME}/{m['render']}" if m.get("render") else ""))
        if page.get("downloadable") == "login" and not files:
            print(f"  the mesh needs a login to download: save it by hand, then `references.py attach {rec['path']} <file.stl>`")
        print(f"  reading pending: a Haiku subagent reads the sidecar + {FILES_DIRNAME}/ images with `references.py prompt`, then `set-reading`")
        return 0
    if a.cmd == "attach":
        m = attach(a.md, a.mesh, scale=a.scale, render=not a.no_render)
        print(measurements_markdown(m, a.mesh.name))
        if m.get("render"):
            print(f"render: {a.md.parent / FILES_DIRNAME / m['render']}")
        return 0
    if a.cmd == "set-reading":
        rec = set_reading(a.md, json.loads(a.json.read_text(encoding="utf-8")), a.model)
        print(f"reading attached to {rec['path']}: {rec['mechanism'] or rec['subject']}")
        return 0
    if a.cmd == "log":
        add_log(a.md, a.text)
        return 0
    if a.cmd == "pending":
        recs = [r for r in list_records() if r["pending"]]
        print(format_list(recs) if recs else "no readings pending")
        return 0
    recs = list_records()
    print(json.dumps(recs, indent=1) if getattr(a, "json", False) else format_list(recs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
