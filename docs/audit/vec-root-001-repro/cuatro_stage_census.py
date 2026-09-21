"""Which stage eats the cuatro body? Count contours at every gate, and draw what survives.

Production path in convert() (edge_to_dxf.py at HEAD):
    1624  contours, hierarchy = cv2.findContours(RETR_TREE)
    1632  contours, _         = _remove_page_borders_early(...)
    1645  valid, group_result = _isolate_with_grouping(...)
    1233      nodes           = _build_hierarchy_nodes(min_area 0.005, max_area 0.95)
              groups formed -> _score_contour_group per group

The scorer saw 3 groups and the body was not among them. This names the gate it died at.

A "body-scale" contour is one whose bbox spans >25% of the raster in BOTH axes -- the cuatro body
is roughly 1500 x 1800 px on a 2232 x 4000 sheet, so it qualifies and almost nothing else does.
Counting those per stage is scale-free and needs no detector.

FREEZE: every hook is a runtime wrap. edge_to_dxf.py is not edited.
"""
import shutil

import cv2
import numpy as np

from _repro import (
    banner, corpus, etd, extract_blueprint_to_dxf, imread, out_path, work_dir,
)

banner(__doc__)

SRC = corpus("cuatro")
WORK = work_dir()
OUT = out_path("CUATRO_stage_census.png")

img0 = imread(SRC)
IH, IW = img0.shape[:2]
BIG_W, BIG_H = 0.25 * IW, 0.25 * IH

STAGES = []          # (name, [contour arrays])
REJECTS = {}         # reject_reason -> count, from the production eligibility gate


def census(name, contours):
    rows = []
    for c in contours:
        a = np.asarray(c)
        if a.ndim == 3:
            a = a.reshape(-1, 2)
        if len(a) < 2:
            continue
        x0, y0 = a.min(0)
        x1, y1 = a.max(0)
        rows.append((x1 - x0, y1 - y0, int(x0), int(y0), a))
    big = [r for r in rows if r[0] >= BIG_W and r[1] >= BIG_H]
    STAGES.append((name, rows, big))
    return rows, big


# ---- hook 1+2: border removal sees the raw findContours output -------------
_orig_border = etd._remove_page_borders_early


def w_border(contours, hierarchy, w, h, *a, **k):
    census("1. cv2.findContours (RETR_TREE)", contours)
    out = _orig_border(contours, hierarchy, w, h, *a, **k)
    kept = out[0] if isinstance(out, tuple) else out
    census("2. after _remove_page_borders_early", kept)
    return out


etd._remove_page_borders_early = w_border

# ---- hook 3: the degenerate/area filter -----------------------------------
_orig_nodes = etd._build_hierarchy_nodes


def w_nodes(contours, hierarchy, iw, ih, min_area_ratio=0.005, max_area_ratio=0.95, *a, **k):
    nodes = _orig_nodes(contours, hierarchy, iw, ih, min_area_ratio, max_area_ratio, *a, **k)
    census(f"3. after _build_hierarchy_nodes (area {min_area_ratio}-{max_area_ratio})",
           [contours[n.idx] for n in nodes if n.idx < len(contours)])
    # production field is is_eligible_root; is_outer_candidate belongs to the DEBUG node class
    cand = [contours[n.idx] for n in nodes
            if getattr(n, "is_eligible_root", False) and n.idx < len(contours)]
    census("4. of those, is_eligible_root (production)", cand)
    why = {}
    for n in nodes:
        if not getattr(n, "is_eligible_root", False):
            why[getattr(n, "reject_reason", "?") or "(blank)"] = \
                why.get(getattr(n, "reject_reason", "?") or "(blank)", 0) + 1
    REJECTS.update(why)
    return nodes


etd._build_hierarchy_nodes = w_nodes

# ---- hook 4: the groups that reach the scorer ------------------------------
_orig_score = etd._score_contour_group
GROUPS = []


def w_score(group, iw, ih):
    s = _orig_score(group, iw, ih)
    GROUPS.append((s, group))
    return s


etd._score_contour_group = w_score

work = WORK / "cuatro_census.png"
shutil.copyfile(SRC, work)
extract_blueprint_to_dxf(source_path=str(work), output_path=str(WORK / "c.dxf"),
                         target_height_mm=500.0, warnings=[], isolate_body=True)

census("5. groups reaching _score_contour_group",
       [np.vstack([np.asarray(c).reshape(-1, 2) for c in g.member_contours])
        for _, g in GROUPS if getattr(g, "member_contours", None)])

# ---------------------------------------------------------------------------
print(f"cuatro raster {IW} x {IH}.  'body-scale' = bbox >= {BIG_W:.0f} x {BIG_H:.0f} px "
      f"(25% of each axis)\n")
hdr = f"{'stage':<48} {'contours':>9} {'body-scale':>11}"
print(hdr); print("-" * len(hdr))
for name, rows, big in STAGES:
    print(f"{name:<48} {len(rows):>9,} {len(big):>11}")
    for bw, bh, bx, by, _ in sorted(big, key=lambda r: -r[0] * r[1])[:3]:
        print(f"{'':<48} {'':>9}   -> {bw}x{bh} px at ({bx},{by})")

print(f"\n{len(GROUPS)} groups scored.  member_contours retained: "
      f"{[len(getattr(g, 'member_contours', []) or []) for _, g in GROUPS]}")

print("\nwhy contours were refused eligible-root status:")
for reason, n in sorted(REJECTS.items(), key=lambda kv: -kv[1]):
    print(f"   {n:>7,}  {reason}")

# ---- the render, now with the real attribute ------------------------------
vis = cv2.addWeighted(img0, 0.30, np.full_like(img0, 255), 0.70, 0)
GROUPS.sort(key=lambda t: -t[0])
COL = [(0, 0, 220), (0, 150, 0), (220, 0, 0)]
LBL = ["WINNER", "2nd", "3rd"]
for i, (s, g) in enumerate(GROUPS[:3]):
    for c in (getattr(g, "member_contours", None) or []):
        cv2.drawContours(vis, [np.asarray(c).astype(np.int32)], -1, COL[i], 5)
    x, y, w, h = g.bbox
    cv2.putText(vis, f"{LBL[i]} s={s:.3f} ({len(g.member_contours)} contours)",
                (int(x), max(40, int(y) - 16)), cv2.FONT_HERSHEY_SIMPLEX, 1.5, COL[i], 4)

_, _, big5 = STAGES[0]
for bw, bh, bx, by, a in sorted(big5, key=lambda r: -r[0] * r[1])[:4]:
    cv2.drawContours(vis, [a.astype(np.int32)], -1, (255, 0, 255), 3)
cv2.putText(vis, "magenta = body-scale contours present at stage 1 (findContours)",
            (30, IH - 100), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 0, 255), 4)
cv2.putText(vis, "colour = what the scorer actually saw",
            (30, IH - 40), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 0), 4)

sc = 1600 / IH
cv2.imencode(".png", cv2.resize(vis, (int(IW * sc), 1600),
                                interpolation=cv2.INTER_AREA))[1].tofile(str(OUT))
print(f"\n-> {OUT}")
