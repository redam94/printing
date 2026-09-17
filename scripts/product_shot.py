#!/usr/bin/env python
"""Clean product shots of a model's parts for the public site: one isometric view, soft light, no axes.

    uv run python scripts/product_shot.py <project> [--out shot.png]

Renders with three.js in headless Chrome (a real z-buffer and smooth shading; matplotlib's painter's
algorithm leaves dark slivers on long thin triangles).  ``shot(stls, out)`` is the API; it returns
None when no Chrome is installed so callers can fall back to the build's render PNGs.
"""
from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._common import MODELS_DIR  # noqa: E402
from scripts.export_viewer import display_mesh  # noqa: E402

CHROME_CANDIDATES = (
    os.environ.get("CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "chromium", "chromium-browser",
)
SHOT_TIMEOUT_S = 120
SHOT_FACE_BUDGET = 120_000       # triangles per part; plenty for a 1200 px picture
# Augur palette: cream paper ground, sage part, ink-green shadow
BG = "#faf8f3"
PART = "#7f9a5c"
SHADOW = "#2a3528"

PAGE = """<!doctype html><meta charset="utf-8">
<style>html,body{margin:0;background:__BG__;overflow:hidden}canvas{display:block}</style>
<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const PARTS = __PARTS__, W = __W__, H = __H__;
function parseSTL(b64){const s=atob(b64);const buf=new ArrayBuffer(s.length);const u=new Uint8Array(buf);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);
  const dv=new DataView(buf);const n=dv.getUint32(80,true);const pos=new Float32Array(n*9);let o=84;
  for(let i=0;i<n;i++){o+=12;for(let v=0;v<9;v++){pos[i*9+v]=dv.getFloat32(o,true);o+=4;}o+=2;}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));
  const m=THREE.BufferGeometryUtils?THREE.BufferGeometryUtils.mergeVertices(g):g;m.computeVertexNormals();m.computeBoundingBox();return m;}
const r=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
r.setPixelRatio(1);r.setSize(W,H);r.shadowMap.enabled=true;r.shadowMap.type=THREE.PCFSoftShadowMap;
r.outputEncoding=THREE.sRGBEncoding;document.body.appendChild(r.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('__BG__');
const group=new THREE.Group();scene.add(group);
let x=0;
for(const p of PARTS){const g=parseSTL(p);const bb=g.boundingBox;
  const mesh=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:new THREE.Color('__PART__').convertSRGBToLinear(),roughness:0.62,metalness:0.0,flatShading:true}));
  mesh.position.set(x-bb.min.x,-(bb.min.y+bb.max.y)/2,-bb.min.z);mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);
  x+=bb.max.x-bb.min.x+12;}
const box=new THREE.Box3().setFromObject(group);const c=box.getCenter(new THREE.Vector3());const s=box.getSize(new THREE.Vector3());
group.position.sub(new THREE.Vector3(c.x,c.y,0));
const R=Math.max(s.x,s.y,s.z);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(R*20,R*20),new THREE.ShadowMaterial({color:'__SHADOW__',opacity:0.18}));
ground.receiveShadow=true;scene.add(ground);
scene.add(new THREE.HemisphereLight(0xffffff,0xb9b29a,0.6));
const key=new THREE.DirectionalLight(0xfff6e6,1.1);key.position.set(-R*0.8,-R*1.4,R*2.2);key.castShadow=true;
key.shadow.mapSize.set(2048,2048);const sc=key.shadow.camera;sc.left=-R*1.5;sc.right=R*1.5;sc.top=R*1.5;sc.bottom=-R*1.5;sc.near=0.1;sc.far=R*8;key.shadow.radius=6;
scene.add(key);const fill=new THREE.DirectionalLight(0xe6eef5,0.35);fill.position.set(R*1.5,R*0.6,R);scene.add(fill);
const cam=new THREE.PerspectiveCamera(22,W/H,1,R*40);cam.up.set(0,0,1);
const dir=new THREE.Vector3(-0.62,-1,0.72).normalize();
// fit: back off until every bbox corner projects inside the frame with a margin
const pts=[];for(const a of[-1,1])for(const b of[-1,1])for(const z of[0,1])pts.push(new THREE.Vector3(a*s.x/2,b*s.y/2,z*s.z));
const target=new THREE.Vector3(0,0,s.z*0.4);let d=R;
for(let i=0;i<60;i++){cam.position.copy(target).addScaledVector(dir,d);cam.lookAt(target);cam.updateMatrixWorld();cam.updateProjectionMatrix();
  if(pts.every(p=>{const q=p.clone().project(cam);return Math.abs(q.x)<0.86&&Math.abs(q.y)<0.84;}))break;d*=1.08;}
r.render(scene,cam);document.title='done';
</script>"""


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c if Path(c).exists() else shutil.which(c)
    return None


def shot(stls: list[Path], out: Path, width: int = 1200, height: int = 900) -> Path | None:
    chrome = find_chrome()
    if not chrome or not stls:
        return None
    parts = [base64.b64encode(display_mesh(Path(s), SHOT_FACE_BUDGET)).decode("ascii") for s in stls]
    page = (PAGE.replace("__PARTS__", "[" + ",".join(f'"{p}"' for p in parts) + "]")
            .replace("__W__", str(width)).replace("__H__", str(height))
            .replace("__BG__", BG).replace("__PART__", PART).replace("__SHADOW__", SHADOW))
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "shot.html"
        html.write_text(page, encoding="utf-8")
        if out.exists():
            out.unlink()
        # with a fresh profile Chrome writes the screenshot but may not exit (macOS keychain prompt), so
        # wait for the file to appear and settle, then stop it
        proc = subprocess.Popen([chrome, "--headless=new", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
                                 f"--window-size={width},{height}", "--virtual-time-budget=15000",
                                 f"--user-data-dir={tmp}/profile", f"--screenshot={out}", html.as_uri()],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline, last = time.time() + SHOT_TIMEOUT_S, -1
        while time.time() < deadline and proc.poll() is None:
            size = out.stat().st_size if out.exists() else -1
            if size > 0 and size == last:
                break
            last = size
            time.sleep(0.5)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
    return out if out.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    ex = MODELS_DIR / a.project / "exports"
    stls = sorted(ex.glob("*.stl"))
    out = shot(stls, a.out or ex / "renders" / "_shot.png")
    print(out or "no Chrome found")
    return 0 if out else 1


if __name__ == "__main__":
    raise SystemExit(main())
