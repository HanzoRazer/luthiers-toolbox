"""Render the three scored groups onto the cuatro, per the standing rule.

The instrumented run says the winner is 246 x 551 px at 2.92% of the raster and the elongated
group lost. Both are claims about a detection, so neither gets quoted until the detection has
been drawn on the source and looked at.

Same runtime wrap as cuatro_instrumented.py -- edge_to_dxf.py is not edited.
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
WORK.mkdir(exist_ok=True)
OUT = Path(r"C:\Users\thepr\Downloads\CUATRO_scored_groups.png")

_orig = etd._score_contour_group
CAPTURED = []


def traced(group, iw, ih):
    s = _orig(group, iw, ih)
    CAPTURED.append((s, group))
    return s


etd._score_contour_group = traced

work_src = WORK / "cuatro_render.png"
shutil.copyfile(SRC, work_src)
extract_blueprint_to_dxf(source_path=str(work_src), output_path=str(WORK / "r.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)

img = cv2.imdecode(np.fromfile(str(SRC), dtype=np.uint8), cv2.IMREAD_COLOR)   # D-15-safe
H, W = img.shape[:2]
vis = cv2.addWeighted(img, 0.35, np.full_like(img, 255), 0.65, 0)

CAPTURED.sort(key=lambda t: -t[0])
COLORS = [(0, 0, 220), (0, 150, 0), (220, 0, 0)]
LBL = ["WINNER", "2nd", "3rd"]

for i, (score, g) in enumerate(CAPTURED[:3]):
    col = COLORS[i % 3]
    cs = getattr(g, "contours", None) or []
    for c in cs:
        arr = c if isinstance(c, np.ndarray) else np.asarray(c)
        cv2.drawContours(vis, [arr.astype(np.int32)], -1, col, 6)
    x, y, w, h = g.bbox
    cv2.rectangle(vis, (int(x), int(y)), (int(x + w), int(y + h)), col, 4)
    txt = f"{LBL[i]} s={score:.3f}  {w}x{h}px  {g.total_area/(W*H)*100:.2f}% area"
    cv2.putText(vis, txt, (int(x), max(40, int(y) - 18)),
                cv2.FONT_HERSHEY_SIMPLEX, 1.6, col, 4)
    print(f"{LBL[i]:>7} score={score:.4f}  bbox=({x},{y},{w},{h})  "
          f"contours={len(cs)}  area={g.total_area/(W*H)*100:.2f}%")

cv2.putText(vis, "5% area floor: ALL THREE CANDIDATES FALL BELOW IT",
            (40, H - 60), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 0), 5)
scale = 1500 / H
small = cv2.resize(vis, (int(W * scale), 1500), interpolation=cv2.INTER_AREA)
cv2.imencode(".png", small)[1].tofile(str(OUT))
print(f"\nraster {W} x {H}; {len(CAPTURED)} groups reached the scorer")
print(f"-> {OUT}")
