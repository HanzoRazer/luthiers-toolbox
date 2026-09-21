"""How much of the cuatro is discarded by measuring ENCLOSED area on stroke-traced geometry?

findContours traces a drawn stroke up one side and back down the other. The resulting contour
draws the shape but encloses almost nothing, so cv2.contourArea is near zero however large the
shape is. edge_to_dxf.py:943 tests exactly that quantity:

    elif area_ratio < min_area_ratio:   reject_reason = "too_small"      # 0.005

Convex-hull area measures the shape the contour DRAWS rather than the ink it encloses. This counts
how the verdicts change under that one substitution. It is a measurement of the existing gate, not
a proposed fix -- what to replace contourArea with is a design question this does not answer.
"""
import shutil

import cv2
import numpy as np

from _repro import (
    banner, corpus, etd, extract_blueprint_to_dxf, imread, work_dir,
)

banner(__doc__)

SRC = corpus("cuatro")
WORK = work_dir()
FLOOR = 0.005

img0 = imread(SRC)
IH, IW = img0.shape[:2]
AREA = float(IW * IH)
BOUT = (950, 2250, 2100, 3800)

NODES = []
_orig = etd._build_hierarchy_nodes


def w(contours, hierarchy, iw, ih, mn=0.005, mx=0.95, *a, **k):
    nodes = _orig(contours, hierarchy, iw, ih, mn, mx, *a, **k)
    NODES.extend(nodes)
    return nodes


etd._build_hierarchy_nodes = w
shutil.copyfile(SRC, WORK / "cuatro_hv.png")
extract_blueprint_to_dxf(source_path=str(WORK / "cuatro_hv.png"),
                         output_path=str(WORK / "hv.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)


def hull_ratio(n):
    p = np.asarray(n.contour).reshape(-1, 2).astype(np.int32)
    return cv2.contourArea(cv2.convexHull(p)) / AREA if len(p) >= 3 else 0.0


def overlaps(bb):
    x, y, w_, h_ = bb
    return not (x + w_ < BOUT[0] or x > BOUT[2] or y + h_ < BOUT[1] or y > BOUT[3])


for label, sel in (("WHOLE SHEET", NODES),
                   ("LOWER BOUT", [n for n in NODES if overlaps(n.bbox)])):
    elig = sum(1 for n in NODES if n.is_eligible_root) if label == "WHOLE SHEET" else \
        sum(1 for n in sel if n.is_eligible_root)
    small = [n for n in sel if n.reject_reason == "too_small"]
    rescued = [n for n in small if hull_ratio(n) >= FLOOR]
    print(f"--- {label} ---")
    print(f"  contours                      {len(sel):>7,}")
    print(f"  eligible under contourArea    {elig:>7,}")
    print(f"  refused too_small             {len(small):>7,}")
    print(f"  of those, hull area >= 0.005  {len(rescued):>7,}   "
          f"({len(rescued)/max(len(small),1)*100:.1f}% of the refusals)")
    if rescued:
        hr = sorted((hull_ratio(n) for n in rescued), reverse=True)
        print("  largest hull ratios: " + ", ".join(f"{v:.4f}" for v in hr[:6]))
        mult = []
        for n in sorted(rescued, key=hull_ratio, reverse=True)[:6]:
            mult.append(hull_ratio(n) / max(n.area_ratio, 1e-12))
        print("  hull/enclosed multiple:   " + ", ".join(f"{v:>7,.0f}x" for v in mult))
    print()
