"""Does arc length discriminate body outline from text, with no area assumption anywhere?

Ruling to test: cv2.contourArea measures the ink a stroke encloses (~0) rather than the shape it
draws, so it is the wrong primitive on line art. Arc length measures what actually exists -- how
much line was drawn -- and cv2.arcLength is already used elsewhere in the file.

Prediction: body flank arcs occupy the top of an arc-length ranking; text fragments do not.
Falsifier: text blocks rank alongside the body arcs.

Regions are taken from geometry already established this session, not from eyeballing:
  FRET_TABLE  = the winning group's bbox, (888,286) 246x551
  LOWER_BOUT  = (950,2250)-(2100,3800), the region whose every contour was refused
  TITLE_TEXT  = the right-hand column carrying the drawing title
  WOOD_LEGEND = the species table along the bottom edge
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
OUT = Path(r"C:\Users\thepr\Downloads\CUATRO_top50_by_arclength.png")

img0 = cv2.imdecode(np.fromfile(str(SRC), dtype=np.uint8), cv2.IMREAD_COLOR)
IH, IW = img0.shape[:2]

REGIONS = {
    "FRET_TABLE":  (888, 286, 1134, 837),
    "LOWER_BOUT":  (950, 2250, 2100, 3800),
    "TITLE_TEXT":  (1950, 0, IW, 900),
    "WOOD_LEGEND": (0, 3750, 700, IH),
}

NODES = []
_orig = etd._build_hierarchy_nodes


def w(contours, hierarchy, iw, ih, mn=0.005, mx=0.95, *a, **k):
    nodes = _orig(contours, hierarchy, iw, ih, mn, mx, *a, **k)
    NODES.extend(nodes)
    return nodes


etd._build_hierarchy_nodes = w
shutil.copyfile(SRC, WORK / "cuatro_al.png")
extract_blueprint_to_dxf(source_path=str(WORK / "cuatro_al.png"),
                         output_path=str(WORK / "al.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)


def region_of(p):
    c = p.mean(0)
    for name, (x0, y0, x1, y1) in REGIONS.items():
        if x0 <= c[0] <= x1 and y0 <= c[1] <= y1:
            return name
    return "other"


rows = []
for n in NODES:
    p = np.asarray(n.contour).reshape(-1, 2)
    if len(p) < 2:
        continue
    rows.append((cv2.arcLength(p.astype(np.int32), False), n, p, region_of(p)))
rows.sort(key=lambda r: -r[0])

print(f"{len(rows):,} contours ranked by cv2.arcLength (no area anywhere)\n")
hdr = f"{'rank':>5} {'arc px':>10} {'bbox':>13} {'enclosed':>10} {'verdict':>14}  region"
print(hdr); print("-" * len(hdr))
for i, (L, n, p, reg) in enumerate(rows[:20]):
    x, y, w_, h_ = n.bbox
    print(f"{i+1:>5} {L:>10,.0f} {w_:>5}x{h_:<7} {n.area_ratio:>10.6f} "
          f"{(n.reject_reason or 'ELIGIBLE'):>14}  {reg}")

print("\n--- where each region's contours land in the ranking ---")
print(f"{'region':<13} {'count':>7} {'best rank':>10} {'median rank':>12} {'max arc px':>11}")
for name in list(REGIONS) + ["other"]:
    idx = [i for i, r in enumerate(rows) if r[3] == name]
    if not idx:
        print(f"{name:<13} {'0':>7}")
        continue
    arcs = [rows[i][0] for i in idx]
    print(f"{name:<13} {len(idx):>7,} {min(idx)+1:>10,} {int(np.median(idx))+1:>12,} "
          f"{max(arcs):>11,.0f}")

top50 = rows[:50]
c50 = {}
for _, _, _, reg in top50:
    c50[reg] = c50.get(reg, 0) + 1
print(f"\ncomposition of the top 50 by arc length: {c50}")
first_text = next((i + 1 for i, r in enumerate(rows)
                   if r[3] in ("FRET_TABLE", "TITLE_TEXT", "WOOD_LEGEND")), None)
first_bout = next((i + 1 for i, r in enumerate(rows) if r[3] == "LOWER_BOUT"), None)
print(f"highest-ranked lower-bout contour: #{first_bout}")
print(f"highest-ranked text contour:       #{first_text}")
print("\nVERDICT: " + ("arc length SEPARATES them -- body arcs outrank all text"
                       if first_text and first_bout and first_bout < first_text else
                       "arc length does NOT cleanly separate -- text ranks at or above the body"))

vis = cv2.addWeighted(img0, 0.20, np.full_like(img0, 255), 0.80, 0)
COL = {"LOWER_BOUT": (0, 150, 0), "FRET_TABLE": (0, 0, 230), "TITLE_TEXT": (255, 0, 255),
       "WOOD_LEGEND": (0, 200, 200), "other": (150, 150, 150)}
for L, n, p, reg in top50:
    cv2.polylines(vis, [p.astype(np.int32)], False, COL[reg], 6)
for i, (t, c) in enumerate([("top 50 contours by ARC LENGTH (no area test)", (0, 0, 0)),
                            ("green = lower bout   blue = fret table", (0, 0, 0)),
                            ("magenta = title text   cyan = wood legend", (0, 0, 0))]):
    cv2.putText(vis, t, (30, 80 + i * 70), cv2.FONT_HERSHEY_SIMPLEX, 1.9, c, 4)
sc = 1900 / IH
cv2.imencode(".png", cv2.resize(vis, (int(IW * sc), 1900),
                                interpolation=cv2.INTER_AREA))[1].tofile(str(OUT))
print(f"\n-> {OUT}")
