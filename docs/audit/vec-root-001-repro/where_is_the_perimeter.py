"""Is the cuatro's lower-bout PERIMETER traced at all, under any label?

Two readings have now been overturned by looking: the aspect mechanism, and my own reading of the
7,421 px reject as the body (it is the soundhole rim, centreline and bridge). So this asks the
question directly instead of inferring it from a statistic.

Every contour whose bbox overlaps the lower-bout region is drawn, coloured by the reason the
production gate gave for refusing it. If the perimeter is traced, it appears as a long arc down
the left and right flanks of the lower bout in one of these colours. If it is absent, those flanks
are bare.
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
OUT = Path(r"C:\Users\thepr\Downloads\CUATRO_lower_bout_by_reason.png")

img0 = cv2.imdecode(np.fromfile(str(SRC), dtype=np.uint8), cv2.IMREAD_COLOR)
IH, IW = img0.shape[:2]
BOUT = (950, 2250, 2100, 3800)        # x0, y0, x1, y1 -- the lower bout, generously

NODES = []
_orig = etd._build_hierarchy_nodes


def w(contours, hierarchy, iw, ih, mn=0.005, mx=0.95, *a, **k):
    nodes = _orig(contours, hierarchy, iw, ih, mn, mx, *a, **k)
    NODES.extend(nodes)
    return nodes


etd._build_hierarchy_nodes = w
shutil.copyfile(SRC, WORK / "cuatro_wp.png")
extract_blueprint_to_dxf(source_path=str(WORK / "cuatro_wp.png"),
                         output_path=str(WORK / "wp.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)

COL = {"": (0, 0, 230), "too_small": (0, 150, 0), "child_contour": (230, 0, 0),
       "page_border": (255, 0, 255), "too_large": (0, 200, 200)}


def overlaps(bb):
    x, y, w_, h_ = bb
    return not (x + w_ < BOUT[0] or x > BOUT[2] or y + h_ < BOUT[1] or y > BOUT[3])


sel = [n for n in NODES if overlaps(n.bbox)]
print(f"{len(sel):,} contours overlap the lower-bout box {BOUT}\n")

rows = []
for n in sel:
    p = np.asarray(n.contour).reshape(-1, 2)
    L = float(np.hypot(*(np.diff(p, axis=0).T)).sum()) if len(p) > 1 else 0.0
    rows.append((L, n, p))
rows.sort(key=lambda r: -r[0])

hdr = f"{'arc px':>10} {'bbox w x h':>14} {'area ratio':>11} {'reason':>15}"
print(hdr); print("-" * len(hdr))
for L, n, p in rows[:12]:
    x, y, w_, h_ = n.bbox
    print(f"{L:>10,.0f} {w_:>6} x {h_:<5} {n.area_ratio:>11.6f} "
          f"{(n.reject_reason or 'ELIGIBLE'):>15}")

vis = cv2.addWeighted(img0, 0.22, np.full_like(img0, 255), 0.78, 0)
for L, n, p in rows:
    if L < 150:            # draw only substantial arcs, so the picture is readable
        continue
    cv2.polylines(vis, [p.astype(np.int32)], False,
                  COL.get(n.reject_reason, (120, 120, 120)), 5)
cv2.rectangle(vis, BOUT[:2], BOUT[2:], (255, 0, 255), 4)
for i, (t, c) in enumerate([("arcs >150px in the lower bout, by gate verdict", (0, 0, 0)),
                            ("blue = ELIGIBLE", (0, 0, 230)),
                            ("green = too_small", (0, 150, 0)),
                            ("red = child_contour", (230, 0, 0))]):
    cv2.putText(vis, t, (30, 80 + i * 68), cv2.FONT_HERSHEY_SIMPLEX, 1.9, c, 4)
sc = 1600 / IH
cv2.imencode(".png", cv2.resize(vis, (int(IW * sc), 1600),
                                interpolation=cv2.INTER_AREA))[1].tofile(str(OUT))
print(f"\ndrawn: {sum(1 for L, _, _ in rows if L >= 150):,} arcs >= 150 px")
print(f"-> {OUT}")
