"""Does the eligible contour contain a NECK, or a fret ladder? Owner: "we never could construct the neck."

The previous render drew the single eligible contour (red, t=4) and the winning group's member
contours (green, t=2) on top of it, so what is visible is mostly the group. That conflates two
different things and cannot answer the question.

Here the ONE eligible contour is drawn alone, and the neck region is shown enlarged. A constructed
neck means the contour carries the neck's two long side edges. A fret ladder means it carries
transverse rungs and inlay blocks and no continuous sides.
"""
import shutil

import cv2
import numpy as np

from _repro import (
    banner, corpus, etd, extract_blueprint_to_dxf, out_path, work_dir,
)

banner(__doc__)

SRC = corpus("archtop_original")              # the run that scored 0.9894
WORK = work_dir()
OUT = out_path("ARCHTOP_neck_check.png")

work = WORK / "neck.jpg"
shutil.copyfile(SRC, work)
img = cv2.imdecode(np.fromfile(str(work), dtype=np.uint8), cv2.IMREAD_COLOR)
IH, IW = img.shape[:2]

NODES = []
_on = etd._build_hierarchy_nodes


def wn(c, h, iw, ih, mn=0.005, mx=0.95, *a, **k):
    n = _on(c, h, iw, ih, mn, mx, *a, **k); NODES.extend(n); return n


etd._build_hierarchy_nodes = wn
extract_blueprint_to_dxf(source_path=str(work), output_path=str(WORK / "neck.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)
etd._build_hierarchy_nodes = _on

elig = [n for n in NODES if n.is_eligible_root]
print(f"{len(elig)} eligible contour(s)")
n = elig[0]
p = np.asarray(n.contour).reshape(-1, 2)
x, y, w_, h_ = n.bbox
print(f"  bbox {w_}x{h_} at ({x},{y})   points {len(p):,}   arc {cv2.arcLength(p.astype(np.int32), False):,.0f} px")

# How much of the contour lies in the neck corridor, and is it vertical or transverse?
NECK = (int(IW * 0.40), int(IH * 0.05), int(IW * 0.62), int(IH * 0.42))
m = ((p[:, 0] >= NECK[0]) & (p[:, 0] <= NECK[2]) &
     (p[:, 1] >= NECK[1]) & (p[:, 1] <= NECK[3]))
seg = np.diff(p, axis=0)
in_neck = m[:-1]
if in_neck.sum():
    d = seg[in_neck]
    vert = np.abs(d[:, 1]) > np.abs(d[:, 0])
    print(f"  points inside the neck corridor: {m.sum():,} of {len(p):,} ({m.sum()/len(p)*100:.1f}%)")
    print(f"  of those segments: {vert.sum():,} vertical-dominant, "
          f"{(~vert).sum():,} horizontal-dominant  -> "
          f"{'sides present' if vert.sum() > (~vert).sum() else 'TRANSVERSE (ladder), no continuous sides'}")
    ys = p[m][:, 1]
    print(f"  vertical span covered in the corridor: {ys.max()-ys.min()} px of "
          f"{NECK[3]-NECK[1]} px ({(ys.max()-ys.min())/(NECK[3]-NECK[1])*100:.0f}%)")
else:
    print("  the eligible contour does not enter the neck corridor at all")

vis = cv2.addWeighted(img, 0.35, np.full_like(img, 255), 0.65, 0)
cv2.polylines(vis, [p.astype(np.int32)], True, (0, 0, 230), 3)
cv2.rectangle(vis, NECK[:2], NECK[2:], (255, 0, 255), 2)
crop = vis[NECK[1]:NECK[3], max(0, NECK[0] - 60):min(IW, NECK[2] + 60)]
crop = cv2.resize(crop, (crop.shape[1] * 2, crop.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
cv2.putText(crop, "THE ONE ELIGIBLE CONTOUR, neck corridor x2", (15, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 3)
full = cv2.resize(vis, (int(IW * crop.shape[0] / IH), crop.shape[0]))
cv2.imencode(".png", np.hstack([full, crop]))[1].tofile(str(OUT))
print(f"-> {OUT}")
