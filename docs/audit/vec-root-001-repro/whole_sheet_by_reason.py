"""The whole sheet by gate verdict. No region box -- the previous render cut the body at y=2250.

Every contour on the sheet, coloured by the verdict the production eligibility gate gave it.
No crop, no region filter, no arbitrary "body-scale" threshold of mine. The only filter is a
minimum arc length so the picture stays readable, and it is stated on the image.
"""
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

SP = Path(__file__).parent
sys.path.insert(0, r"C:\Users\thepr\Downloads\luthiers-toolbox\services\api")
sys.path.insert(0, r"C:\Users\thepr\Downloads\luthiers-toolbox\services\photo-vectorizer")

import edge_to_dxf as etd                                            # noqa: E402
from app.services.blueprint_extract import extract_blueprint_to_dxf  # noqa: E402

SRC = SP / "stocktake" / "cuatro_ascii.png"
WORK = SP / "instr_run"
OUT = Path(r"C:\Users\thepr\Downloads\CUATRO_whole_sheet_by_reason.png")
MIN_ARC = 120

img0 = cv2.imdecode(np.fromfile(str(SRC), dtype=np.uint8), cv2.IMREAD_COLOR)
IH, IW = img0.shape[:2]

NODES = []
_orig = etd._build_hierarchy_nodes


def w(contours, hierarchy, iw, ih, mn=0.005, mx=0.95, *a, **k):
    nodes = _orig(contours, hierarchy, iw, ih, mn, mx, *a, **k)
    NODES.extend(nodes)
    return nodes


etd._build_hierarchy_nodes = w
shutil.copyfile(SRC, WORK / "cuatro_ws.png")
extract_blueprint_to_dxf(source_path=str(WORK / "cuatro_ws.png"),
                         output_path=str(WORK / "ws.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)

rows = []
for n in NODES:
    p = np.asarray(n.contour).reshape(-1, 2)
    L = float(np.hypot(*(np.diff(p, axis=0).T)).sum()) if len(p) > 1 else 0.0
    rows.append((L, n, p))
rows.sort(key=lambda r: r[0])                      # long arcs drawn last, on top

COL = {"": (200, 40, 40), "too_small": (0, 150, 0), "child_contour": (0, 130, 255),
       "page_border": (255, 0, 255), "too_large": (0, 200, 200)}

vis = cv2.addWeighted(img0, 0.20, np.full_like(img0, 255), 0.80, 0)
drawn = {}
for L, n, p in rows:
    if L < MIN_ARC:
        continue
    r = n.reject_reason or ""
    drawn[r or "ELIGIBLE"] = drawn.get(r or "ELIGIBLE", 0) + 1
    cv2.polylines(vis, [p.astype(np.int32)], False, COL.get(r, (120, 120, 120)),
                  7 if not r else 4)

lines = [(f"every contour on the sheet, arc >= {MIN_ARC}px, by eligibility verdict", (0, 0, 0)),
         (f"RED = ELIGIBLE ({drawn.get('ELIGIBLE', 0)})  -- the only things the scorer sees",
          (200, 40, 40)),
         (f"GREEN = too_small ({drawn.get('too_small', 0)})  -- refused on ENCLOSED area",
          (0, 150, 0)),
         (f"ORANGE = child_contour ({drawn.get('child_contour', 0)})", (0, 130, 255))]
for i, (t, c) in enumerate(lines):
    cv2.putText(vis, t, (30, 80 + i * 72), cv2.FONT_HERSHEY_SIMPLEX, 1.9, c, 4)

sc = 1900 / IH
cv2.imencode(".png", cv2.resize(vis, (int(IW * sc), 1900),
                                interpolation=cv2.INTER_AREA))[1].tofile(str(OUT))
print(f"{len(NODES):,} contours; drawn (arc >= {MIN_ARC}px):")
for k, v in sorted(drawn.items(), key=lambda kv: -kv[1]):
    print(f"   {v:>6,}  {k}")
print(f"\n-> {OUT}")
