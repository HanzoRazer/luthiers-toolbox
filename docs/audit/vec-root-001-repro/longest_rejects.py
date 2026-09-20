"""What are the longest contours rejected as too_small, and is one of them the body?

too_small is `cv2.contourArea(contour) / image_area < 0.005` (edge_to_dxf.py:943). contourArea is
ENCLOSED area. A stroke outline traced by findContours runs up one side of the ink and back down
the other, so it encloses almost nothing however large the shape it draws. The lower-bout histogram
holds a fragment with an 8,290 px arc length, which is about twice the perimeter of the cuatro body
-- the exact signature of a closed outline traced as a thin stroke.

If that fragment's bbox is body-sized, the body IS traced as one contour and the defect is an area
test applied to a stroke. Rendered before anything is claimed.
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
OUT = Path(r"C:\Users\thepr\Downloads\CUATRO_the_rejected_body.png")

img0 = cv2.imdecode(np.fromfile(str(SRC), dtype=np.uint8), cv2.IMREAD_COLOR)
IH, IW = img0.shape[:2]
IMG_AREA = float(IW * IH)

ROWS = []
_orig = etd._build_hierarchy_nodes


def w(contours, hierarchy, iw, ih, mn=0.005, mx=0.95, *a, **k):
    nodes = _orig(contours, hierarchy, iw, ih, mn, mx, *a, **k)
    for n in nodes:
        p = np.asarray(n.contour).reshape(-1, 2)
        L = float(np.hypot(*(np.diff(p, axis=0).T)).sum()) if len(p) > 1 else 0.0
        ROWS.append((L, n.reject_reason, n.area, n.area_ratio, n.bbox, p, n.parent_idx))
    return nodes


etd._build_hierarchy_nodes = w
shutil.copyfile(SRC, WORK / "cuatro_lr.png")
extract_blueprint_to_dxf(source_path=str(WORK / "cuatro_lr.png"),
                         output_path=str(WORK / "lr.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)

ROWS.sort(key=lambda r: -r[0])
print(f"{len(ROWS):,} nodes.  min_area_ratio = 0.005  =>  area floor = "
      f"{0.005*IMG_AREA:,.0f} px^2\n")
hdr = (f"{'#':>3} {'arc len px':>11} {'bbox w x h':>14} {'area px^2':>12} {'area ratio':>11} "
       f"{'reject':>14}")
print(hdr); print("-" * len(hdr))
for i, (L, rr, ar, arr, bb, p, par) in enumerate(ROWS[:12]):
    x, y, w_, h_ = bb
    print(f"{i:>3} {L:>11,.0f} {w_:>6} x {h_:<5} {ar:>12,.0f} {arr:>11.6f} "
          f"{(rr or 'ELIGIBLE'):>14}")

# the longest thing that was thrown away
thrown = [r for r in ROWS if r[1] == "too_small"]
big = max(thrown, key=lambda r: r[4][2] * r[4][3])
L, rr, ar, arr, bb, p, par = big
x, y, w_, h_ = bb
print(f"\nLargest-bbox contour refused as too_small:")
print(f"  bbox {w_} x {h_} px at ({x},{y})  = {w_/IW*100:.0f}% x {h_/IH*100:.0f}% of the raster")
print(f"  arc length {L:,.0f} px")
print(f"  enclosed area {ar:,.0f} px^2  (ratio {arr:.6f}, floor {0.005:.3f})")
print(f"  short of the floor by {0.005/max(arr,1e-12):,.0f}x")
print(f"  parent_idx {par}")
hull = cv2.contourArea(cv2.convexHull(p.astype(np.int32)))
print(f"  convex-hull area {hull:,.0f} px^2  (ratio {hull/IMG_AREA:.4f}) -> "
      f"{'WOULD PASS the same floor on hull area' if hull/IMG_AREA >= 0.005 else 'still fails'}")

vis = cv2.addWeighted(img0, 0.25, np.full_like(img0, 255), 0.75, 0)
cv2.polylines(vis, [p.astype(np.int32)], False, (0, 0, 230), 6)
cv2.rectangle(vis, (x, y), (x + w_, y + h_), (255, 0, 255), 4)
for t, yy in [(f"rejected too_small: bbox {w_}x{h_}px, arc {L:,.0f}px", 80),
              (f"enclosed area {ar:,.0f}px2 = {arr:.5f} of raster (floor 0.005)", 150),
              (f"convex hull {hull:,.0f}px2 = {hull/IMG_AREA:.4f}", 220)]:
    cv2.putText(vis, t, (30, yy), cv2.FONT_HERSHEY_SIMPLEX, 1.9, (0, 0, 0), 4)
sc = 1600 / IH
cv2.imencode(".png", cv2.resize(vis, (int(IW * sc), 1600),
                                interpolation=cv2.INTER_AREA))[1].tofile(str(OUT))
print(f"\n-> {OUT}")
