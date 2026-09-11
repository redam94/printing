# Where reference models live, and how to ask for them

`uv run python scripts/references.py search "<phrase>"` covers the first four rows without a key.
The rest are reached with the web-search tool (`site:` filters) and filed by URL with
`references.py add <url> ...`, which reads any page's title, description, direct mesh links and
Open Graph image.

| source | reach it | good for | download |
|---|---|---|---|
| Printables | `references.py search` (GraphQL, keyless) | functional prints; descriptions carry print settings, material, sometimes beam thickness; the *makes* count says it prints | login: save by hand, then `attach` |
| GitHub | `references.py search` (repo search, keyless; set `GITHUB_TOKEN` for a higher rate limit) | source models (OpenSCAD, build123d, CadQuery, FreeCAD, Fusion) where the parameters are in the file; research code from papers | direct: `add --download <blob url>` |
| Sketchfab | `references.py search` (v3 API, keyless) | turning a mechanism around in the browser; many university demos | login |
| Thingiverse | `references.py search` with `THINGIVERSE_TOKEN` (thingiverse.com/developers); else web search `site:thingiverse.com` | the old classics: bistable switches, flexure fidgets, print-in-place hinges; comments hold years of print feedback | login (token gives file URLs) |
| BYU CMR maker library | web search `site:compliantmechanisms.byu.edu` | the canonical printable compliant mechanisms with explanations: bistable switch, LET joints, ortho-planar springs, lamina-emergent mechanisms, compliant grippers; they also publish on Printables as "BYU CMR" | usually Printables |
| Thangs | web search `site:thangs.com` | geometry search across hosts when the name is unknown | varies |
| Cults3D | web search `site:cults3d.com` | designers who document tolerances; some paid | login |
| MyMiniFactory | web search `site:myminifactory.com` | every object has a print photo | login |
| alphaXiv / arXiv | the alphaXiv tools | the equations: beam geometry vs snap force, pseudo-rigid-body models, fatigue vs material; supplementary STLs in some papers | paper |
| YouTube | web search | build videos show print orientation and failure modes the page omits | none |

## Search phrases that work

Mechanism noun + "compliant" or "print in place" + function. Sites tag inconsistently, so try
two phrasings.

| looking for | phrases |
|---|---|
| bistable toggle / switch | `bistable compliant switch`, `bistable mechanism print in place`, `snap through toggle` |
| snap-through buckle / clip | `bistable clip`, `snap through buckle`, `cable clip bistable` |
| living hinge | `living hinge box`, `print in place hinge flat`, `lamina emergent` |
| flexure stage / spring | `parallel flexure`, `flexure stage linear`, `ortho-planar spring`, `compliant spring 3d print` |
| rotary flexure | `cross axis flexural pivot`, `LET joint`, `compliant rotary joint` |
| latch / catch | `toggle latch print in place`, `cantilever snap latch`, `compliant latch` |
| gripper | `compliant gripper`, `fin ray gripper`, `flexure gripper` |
| constant force / detent | `constant force mechanism`, `compliant detent`, `click mechanism print` |
| print-in-place joints | `print in place hinge`, `print in place ball joint`, `articulated print in place` |

## Judging a hit

Prefer, in order: a description that states material, orientation and at least one governing
dimension; makes / print photos (evidence it prints); the source file available (parameters
visible); a permissive licence. A model with a pretty render and no makes is a sketch, not a
reference.

Record the licence in the sidecar (`add` does). NonCommercial and NoDerivatives terms do not
stop you learning a beam thickness from a mesh, but they do stop the mesh going into `models/`;
references guide the user's own parametric part.
