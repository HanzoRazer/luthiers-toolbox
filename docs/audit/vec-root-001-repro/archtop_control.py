"""The archtop through REFINED: the control for PROV's thesis. Prediction stated before the run.

PROV's thesis: the eligibility block's three premises are true of a PHOTOGRAPHED subject and false
of a drawn one. On a photograph:
  A  a silhouette contour encloses a region      -> should clear the 0.005 floor
  B  no page border to parent it                 -> should not be child_contour
  C  subject at 20-60% of frame                  -> should clear the 0.95 ceiling

PREDICTION: on the confound-free input the archtop body PASSES eligibility.
FALSIFIER : it dies at too_small or child_contour, which would mean the block is broken for
            reasons unrelated to photo premises and PROV's thesis is wrong.

CONFOUND, identified by looking BEFORE the run, not argued afterwards:
  The ORIGINAL photograph is shot against a plank wall with five or six full-width horizontal
  seams, plus a wall/floor boundary and a guitar stand. Any of those can trace as a contour larger
  than the guitar and parent it, firing premise B for a reason that does NOT refute the thesis.
  => the original is NON-DECISIVE and is run only for comparison.
  => the CONTROL is the rembg foreground (_02_foreground.jpg): pure black background, body cleanly
     isolated. rembg damaged the headstock face and the tailpiece region; the BODY is intact, and
     the body is the subject of the test.

Restored is NOT run here. Its path is findContours(RETR_LIST) + len(c)>=3 -- no hierarchy, no
border removal, no eligibility block, no grouping. It cannot confirm or refute any of this.
"""
import hashlib
import shutil

import cv2
import numpy as np

from _repro import (
    banner, corpus, etd, extract_blueprint_to_dxf, work_dir,
)

banner(__doc__)

RUNS = [("CONTROL  (rembg foreground, confound removed)", corpus("archtop_foreground")),
        ("compare  (original, plank-wall confound PRESENT)", corpus("archtop_original"))]
WORK = work_dir()


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


print("PREDICTION (before the run): on the CONTROL the archtop body passes eligibility.")
print("FALSIFIER: it dies at too_small or child_contour.\n")

for label, src in RUNS:
    if not src.is_file():
        print(f"{label}: NOT_RUN_SOURCE_ABSENT {src.name}\n"); continue

    before = sha(src)
    work = WORK / ("ctrl.jpg" if "CONTROL" in label else "orig.jpg")
    shutil.copyfile(src, work)                                    # D-16 guard

    img = cv2.imdecode(np.fromfile(str(work), dtype=np.uint8), cv2.IMREAD_COLOR)
    IH, IW = img.shape[:2]
    AREA = float(IW * IH)

    NODES, GROUPS = [], []
    _on, _os = etd._build_hierarchy_nodes, etd._score_contour_group

    def wn(c, h, iw, ih, mn=0.005, mx=0.95, *a, **k):
        n = _on(c, h, iw, ih, mn, mx, *a, **k); NODES.extend(n); return n

    def ws(g, iw, ih):
        s = _os(g, iw, ih); GROUPS.append((s, g)); return s

    etd._build_hierarchy_nodes, etd._score_contour_group = wn, ws

    out = WORK / (work.stem + "_refined.dxf")
    res = extract_blueprint_to_dxf(source_path=str(work), output_path=str(out),
                                   target_height_mm=500.0, warnings=[], isolate_body=True)
    etd._build_hierarchy_nodes, etd._score_contour_group = _on, _os

    reasons = {}
    for n in NODES:
        k = n.reject_reason or "ELIGIBLE"
        reasons[k] = reasons.get(k, 0) + 1

    print(f"=== {label} ===")
    print(f"  raster {IW} x {IH}   success={res.success}  {getattr(res,'error','') or ''}")
    print(f"  contours {len(NODES):,}   verdicts: " +
          ", ".join(f"{k}={v:,}" for k, v in sorted(reasons.items(), key=lambda kv: -kv[1])))

    rows = sorted(NODES, key=lambda n: -n.area_ratio)[:5]
    print(f"  {'area ratio':>11} {'bbox':>13} {'edges':>6} {'parent':>7}  verdict")
    for n in rows:
        x, y, w_, h_ = n.bbox
        print(f"  {n.area_ratio:>11.6f} {w_:>5}x{h_:<7} {n.edge_count:>6} "
              f"{str(n.parent_idx):>7}  {n.reject_reason or 'ELIGIBLE'}")

    elig = [n for n in NODES if n.is_eligible_root]
    big = max(NODES, key=lambda n: n.area_ratio) if NODES else None
    verdict = ("PASSES  -> prediction holds" if big is not None and big.is_eligible_root
               else f"DIES at {big.reject_reason} -> " +
                    ("NON-DECISIVE (confound present)" if "compare" in label
                     else "PREDICTION FALSIFIED, thesis wrong"))
    print(f"  largest-area contour: {verdict}")
    print(f"  eligible {len(elig)}   groups scored {len(GROUPS)}"
          + (f"   winner s={max(GROUPS)[0]:.4f}" if GROUPS else ""))
    print(f"  source untouched: {'OK' if sha(src) == before else 'CHANGED'}\n")
