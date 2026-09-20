"""The falsifiable prediction: is L-00's body perimeter sitting in its too_small pile?

If line 943's enclosed-area gate is global, it discarded the body on every plan the refined lane
touched. On L-00 the classified path certified 0.71 mm of corner residue as the body (D-13). If
L-00's perimeter is in its too_small pile, D-13 and the cuatro fret table have ONE cause at line
943 and two investigations collapse into one defect.

If it is NOT in that pile, the prediction is dead and D-13 needs its own explanation.

The prediction is stated before the run and is not adjusted afterwards.

D-16 guard: the extractor overwrites its input when it downscales; the source is copied first and
the ORIGINAL is hashed before and after.
"""
import hashlib
import shutil

import cv2
import numpy as np

from _repro import (
    banner, corpus, etd, extract_blueprint_to_dxf, out_path, work_dir,
)

banner(__doc__)

SRC = corpus("l00")
WORK = work_dir()
OUT = out_path("L00_too_small_pile.png")
FLOOR = 0.005


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


before = sha(SRC)
work = WORK / "L00_pred.png"
shutil.copyfile(SRC, work)

img0 = cv2.imdecode(np.fromfile(str(work), dtype=np.uint8), cv2.IMREAD_COLOR)
IH, IW = img0.shape[:2]
AREA = float(IW * IH)
print(f"L-00 raster {IW} x {IH}\n")
print("PREDICTION (stated before the run): L-00's body perimeter is in the too_small pile,")
print("as long arcs with near-zero enclosed area and large convex hulls.\n")

NODES = []
_orig = etd._build_hierarchy_nodes


def w(contours, hierarchy, iw, ih, mn=0.005, mx=0.95, *a, **k):
    nodes = _orig(contours, hierarchy, iw, ih, mn, mx, *a, **k)
    NODES.extend(nodes)
    return nodes


etd._build_hierarchy_nodes = w
extract_blueprint_to_dxf(source_path=str(work), output_path=str(WORK / "pred.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)

rows = []
for n in NODES:
    p = np.asarray(n.contour).reshape(-1, 2)
    if len(p) < 3:
        continue
    hull = cv2.contourArea(cv2.convexHull(p.astype(np.int32))) / AREA
    rows.append((cv2.arcLength(p.astype(np.int32), False), hull, n, p))
rows.sort(key=lambda r: -r[0])

small = [r for r in rows if r[2].reject_reason == "too_small"]
elig = [r for r in rows if r[2].is_eligible_root]
rescued = [r for r in small if r[1] >= FLOOR]

print(f"contours                       {len(rows):>7,}")
print(f"eligible under contourArea     {len(elig):>7,}")
print(f"refused too_small              {len(small):>7,}")
print(f"of those, hull >= {FLOOR}        {len(rescued):>7,}\n")

hdr = f"{'rank':>5} {'arc px':>10} {'bbox':>13} {'enclosed':>10} {'hull':>9} {'verdict':>14}"
print(hdr); print("-" * len(hdr))
for i, (L, hull, n, p) in enumerate(rows[:15]):
    x, y, w_, h_ = n.bbox
    print(f"{i+1:>5} {L:>10,.0f} {w_:>5}x{h_:<7} {n.area_ratio:>10.6f} {hull:>9.4f} "
          f"{(n.reject_reason or 'ELIGIBLE'):>14}")

if small:
    L, hull, n, p = max(small, key=lambda r: r[1])
    x, y, w_, h_ = n.bbox
    print("\nlargest-hull contour in the too_small pile:")
    print(f"  bbox {w_} x {h_} at ({x},{y}) = {w_/IW*100:.0f}% x {h_/IH*100:.0f}% of raster")
    print(f"  arc {L:,.0f} px   enclosed {n.area_ratio:.6f}   hull {hull:.4f}   "
          f"hull/enclosed {hull/max(n.area_ratio,1e-12):,.0f}x")

vis = cv2.addWeighted(img0, 0.20, np.full_like(img0, 255), 0.80, 0)
for L, hull, n, p in rows:
    if L < 200:
        continue
    col = (200, 40, 40) if n.is_eligible_root else \
        (0, 0, 230) if hull >= FLOOR else (0, 150, 0)
    cv2.polylines(vis, [p.astype(np.int32)], False, col, 4)
for i, (t, c) in enumerate([("L-00, arcs >=200px", (0, 0, 0)),
                            (f"BLUE(bgr) = ELIGIBLE ({len(elig)})", (200, 40, 40)),
                            (f"RED = too_small but hull>=0.005 ({len(rescued)})", (0, 0, 230)),
                            ("GREEN = too_small, hull<0.005", (0, 150, 0))]):
    cv2.putText(vis, t, (25, 55 + i * 52), cv2.FONT_HERSHEY_SIMPLEX, 1.3, c, 3)
sc = 1500 / IH
cv2.imencode(".png", cv2.resize(vis, (int(IW * sc), 1500),
                                interpolation=cv2.INTER_AREA))[1].tofile(str(OUT))
print(f"\noriginal untouched: {'OK' if sha(SRC) == before else 'CHANGED'}")
print(f"-> {OUT}")
