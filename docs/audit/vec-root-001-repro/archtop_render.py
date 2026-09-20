"""Draw the archtop's eligible contour on the source. The run says it passed; this says what it is.

A score of 0.8464 on the control and 0.9894 on the original means nothing until the thing that
earned it has been looked at -- the fret table scored 0.732.
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

GP = Path(r"C:\Users\thepr\Downloads\luthiers-toolbox\Guitar Plans")
BASE = "Jumbo Tiger Maple Archtop Guitar with a Florentine Cutaway"
WORK = SP / "archtop_run"
OUT = Path(r"C:\Users\thepr\Downloads\ARCHTOP_eligible.png")

panels = []
for tag, src in (("CONTROL foreground", GP / f"{BASE}_02_foreground.jpg"),
                 ("original + plank wall", GP / f"{BASE}_00_original.jpg")):
    work = WORK / f"r_{tag.split()[0]}.jpg"
    shutil.copyfile(src, work)
    img = cv2.imdecode(np.fromfile(str(work), dtype=np.uint8), cv2.IMREAD_COLOR)

    NODES, GROUPS = [], []
    _on, _os = etd._build_hierarchy_nodes, etd._score_contour_group
    etd._build_hierarchy_nodes = lambda c, h, iw, ih, mn=0.005, mx=0.95, *a, **k: (
        NODES.extend(_on(c, h, iw, ih, mn, mx, *a, **k)) or NODES)

    def ws(g, iw, ih):
        s = _os(g, iw, ih); GROUPS.append((s, g)); return s
    etd._score_contour_group = ws

    extract_blueprint_to_dxf(source_path=str(work), output_path=str(WORK / f"{tag[:4]}.dxf"),
                             target_height_mm=500.0, warnings=[], isolate_body=True)
    etd._build_hierarchy_nodes, etd._score_contour_group = _on, _os

    vis = cv2.addWeighted(img, 0.45, np.full_like(img, 255), 0.55, 0)
    elig = [n for n in NODES if n.is_eligible_root]
    for n in elig:
        cv2.drawContours(vis, [np.asarray(n.contour).astype(np.int32)], -1, (0, 0, 230), 4)
    if GROUPS:
        s, g = max(GROUPS, key=lambda t: t[0])
        for c in (getattr(g, "member_contours", None) or []):
            cv2.drawContours(vis, [np.asarray(c).astype(np.int32)], -1, (0, 160, 0), 2)
        cv2.putText(vis, f"winner s={s:.4f}", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 160, 0), 3)
    cv2.putText(vis, tag, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 3)
    cv2.putText(vis, f"eligible={len(elig)}  red=ELIGIBLE", (20, 155),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 230), 3)
    panels.append(vis)
    print(f"{tag}: eligible={len(elig)}, groups={len(GROUPS)}")

h = min(p.shape[0] for p in panels)
panels = [cv2.resize(p, (int(p.shape[1] * h / p.shape[0]), h)) for p in panels]
cv2.imencode(".png", np.hstack(panels))[1].tofile(str(OUT))
print(f"-> {OUT}")
