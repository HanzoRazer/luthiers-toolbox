#!/usr/bin/env python3
"""
Rerun 003 — Arnold outline extraction (ACOUSTIC BODY.pdf -> plan-view half-outline)
===================================================================================

Deterministic extraction of the #65260 plan-view body perimeter from the
verified traced reconstruction ``ACOUSTIC BODY.pdf`` (drawn by JD, traced from
the John Arnold 1937 D-28 #65260 drawing; JD confirmed a traced reconstruction).

Authority chain:
  PRIMARY_HISTORICAL_SOURCE : John Arnold #65260 drawing        (1937 D-28.pdf)
  DRAWING_DERIVED_GEOMETRY   : JD "ACOUSTIC BODY" CAD tracing    (ACOUSTIC BODY.pdf)
  DIRECT_MEASUREMENT         : Arnold side-height correspondence (numeric series)

Method (robust to the dimension-annotation box and colored bracing):
  * render page 1 in colour;
  * the body perimeter is black while the X/back braces are coloured, and the
    dimension lines form a box OUTSIDE the perimeter;
  * seal all ink and flood-fill the interior from many seeds placed strictly
    inside the perimeter, accepting only bounded fills (rejects the trapped
    exterior and any leak), then bridge the internal brace lines and take the
    body silhouette contour;
  * calibrate longitudinally to the labelled 20.0 in body length (the sheet is
    1:4), cross-check width (15.7 / 11.7) and soundhole (Ø4.0);
  * the outline is CAD-symmetric by construction -> symmetry discrepancy = 0 by
    construction (NOT evidence the real 1937 instrument was symmetric).

Neither PDF is committed (public repo; copyrighted drawing). This script writes
the extracted geometry + a provenance manifest; the solver consumes the CSV.

Outputs (deterministic):
  docs/experiments/results/D28_65260_ARNOLD_OUTLINE.csv          (right half, neck->tail)
  docs/experiments/results/D28_65260_RERUN_003_PROVENANCE.json
  docs/experiments/results/D28_65260_RERUN_003_EXTRACTION.json   (calibration + landmarks)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")

# External source PDFs (agent uploads area; NOT vendored into the repo).
_UPLOADS = "/home/ubuntu/.cursor/projects/workspace/uploads"
ACOUSTIC_PDF = os.path.join(_UPLOADS, "ACOUSTIC_BODY_a692.pdf")
ARNOLD_PDF = os.path.join(_UPLOADS, "1937_D-28_fb03.pdf")

OUTLINE_CSV = os.path.join(_RESULTS, "D28_65260_ARNOLD_OUTLINE.csv")
PROVENANCE_JSON = os.path.join(_RESULTS, "D28_65260_RERUN_003_PROVENANCE.json")
EXTRACTION_JSON = os.path.join(_RESULTS, "D28_65260_RERUN_003_EXTRACTION.json")

# Labelled calibration dimensions on the CAD sheet (drawing-derived authority).
CAL_BODY_LENGTH_IN = 20.0     # longitudinal calibration reference
CAL_UPPER_BOUT_IN = 11.7      # cross-check
CAL_LOWER_BOUT_IN = 15.7      # cross-check
CAL_SOUNDHOLE_DIA_IN = 4.0    # cross-check
CENTERLINE_X_PT = 306.0       # vector centerline of the sheet
DPI = 400


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_silhouette(pdf_path: str) -> Tuple[np.ndarray, float, np.ndarray]:
    """Return (filled_body_mask, z, contour_px) from page 1 of the CAD PDF."""
    import fitz
    doc = fitz.open(pdf_path)
    pg = doc[0]
    z = DPI / 72.0
    pm = pg.get_pixmap(matrix=fitz.Matrix(z, z))
    img = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, :3]
    h, w = img.shape[:2]
    page = h * w
    V = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)[:, :, 2]
    ink = cv2.dilate((V < 210).astype(np.uint8),
                     cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    free = (1 - ink).astype(np.uint8)
    cx = CENTERLINE_X_PT * z
    acc = np.zeros((h, w), np.uint8)
    # Seeds strictly inside the perimeter; accept only bounded fills.
    for dx in range(-95, 96, 7):
        for yv in range(210, 589, 5):
            sx, sy = int(cx + dx * z), int(yv * z)
            if free[sy, sx] == 0 or acc[sy, sx] == 1:
                continue
            m = np.zeros((h + 2, w + 2), np.uint8)
            ff = free.copy()
            cv2.floodFill(ff, m, (sx, sy), 3)
            reg = (ff == 3)
            if reg.sum() < 0.20 * page:
                acc[reg] = 1
    body = cv2.morphologyEx(acc, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(body, 8)
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    comp = (lab == idx).astype(np.uint8)
    cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)
    filled = np.zeros_like(comp)
    cv2.drawContours(filled, [c], -1, 1, -1)
    return filled, z, c


def _detect_soundhole(pdf_path: str, z: float, y0_px: int, y1_px: int) -> Optional[Tuple[float, float, float]]:
    """Soundhole via the circular interior pocket near the centerline (px center/r)."""
    import fitz
    doc = fitz.open(pdf_path)
    pg = doc[0]
    pm = pg.get_pixmap(matrix=fitz.Matrix(z, z))
    img = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, :3]
    V = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)[:, :, 2]
    # Soundhole Ø4.0 in real -> 1.0 in on the 1:4 sheet -> radius ~0.5 in = 0.5*DPI px.
    circ = cv2.HoughCircles(V, cv2.HOUGH_GRADIENT, dp=1, minDist=int(400),
                            param1=120, param2=40,
                            minRadius=int(0.35 * DPI), maxRadius=int(0.65 * DPI))
    cx = CENTERLINE_X_PT * z
    if circ is not None:
        cand = [c for c in circ[0] if abs(c[0] - cx) < 60 * z and y0_px < c[1] < y1_px]
        if cand:
            c = min(cand, key=lambda c: abs(c[0] - cx))
            return float(c[0]), float(c[1]), float(c[2])
    return None


def extract() -> Dict:
    filled, z, contour = _extract_silhouette(ACOUSTIC_PDF)
    x, y, ww, hh = cv2.boundingRect(contour)
    # Longitudinal calibration: body pixel height -> 20.0 in (sheet is 1:4).
    in_per_px = CAL_BODY_LENGTH_IN / hh
    # Per-row half-widths about the centerline of the extracted silhouette.
    ys = np.where(filled.any(axis=1))[0]
    cols = np.where(filled.any(axis=0))[0]
    cx_px = 0.5 * (cols.min() + cols.max())
    rows: List[Tuple[float, float]] = []   # (y_from_neck_in, half_width_in)
    for yy in range(int(ys.min()), int(ys.max()) + 1):
        xs = np.where(filled[yy] > 0)[0]
        if xs.size == 0:
            continue
        half = 0.5 * (xs.max() - xs.min()) * in_per_px
        y_from_neck = (yy - ys.min()) * in_per_px
        rows.append((y_from_neck, half))
    rows_arr = np.array(rows)
    L_cal = rows_arr[:, 0].max()
    max_width = rows_arr[:, 1].max() * 2
    # Symmetry: CAD outline is symmetric by construction (single mirrored curve).
    symmetry_mode = "symmetric_by_construction"
    # Soundhole (datum A).
    sh = _detect_soundhole(ACOUSTIC_PDF, z, int(ys.min()), int(ys.max()))
    if sh is not None:
        sh_dia_in = 2 * sh[2] * in_per_px
        sh_y_from_neck = (sh[1] - ys.min()) * in_per_px
    else:
        sh_dia_in = None
        sh_y_from_neck = None

    # Landmarks from the perimeter (outputs, not inputs).
    yv = rows_arr[:, 0]
    hw = rows_arr[:, 1]
    # smooth half-width for robust extrema
    k = max(3, int(0.02 * len(hw)) | 1)
    ker = np.ones(k) / k
    hw_s = np.convolve(hw, ker, mode="same")
    from scipy.signal import find_peaks
    lb_i = int(np.argmax(hw_s))                       # lower bout = global max half-width
    # Upper bout = the most prominent local maximum on the neck side of the lower bout.
    peaks, _ = find_peaks(hw_s[:lb_i + 1], prominence=0.03)
    peaks = [p for p in peaks if 0.05 * L_cal < yv[p] < 0.5 * L_cal]
    if peaks:
        ub_i = int(peaks[int(np.argmax(hw_s[peaks]))])
    else:
        ub_i = int(np.argmax(np.where(yv < 0.28 * L_cal, hw_s, -1)))
    # Waist = minimum half-width between the upper-bout and lower-bout maxima.
    wi_local = ub_i + int(np.argmin(hw_s[ub_i:lb_i + 1]))
    # Report whether the waist is a sharp single minimum or a shallow region.
    waist_val = hw_s[wi_local]
    near = np.where(np.abs(hw_s[ub_i:lb_i + 1] - waist_val) < 0.02)[0]
    waist_shape = ("shallow_region" if near.size > 0.15 * (lb_i - ub_i + 1)
                   else "single_minimum")
    landmarks = {
        "upper_bout": {"y_from_neck_in": float(yv[ub_i]), "half_width_in": float(hw[ub_i]),
                       "full_width_in": float(2 * hw[ub_i])},
        "waist": {"y_from_neck_in": float(yv[wi_local]), "half_width_in": float(hw[wi_local]),
                  "full_width_in": float(2 * hw[wi_local]),
                  "y_norm": float(yv[wi_local] / L_cal), "shape": waist_shape},
        "lower_bout": {"y_from_neck_in": float(yv[lb_i]), "half_width_in": float(hw[lb_i]),
                       "full_width_in": float(2 * hw[lb_i])},
    }
    calibration = {
        "dpi": DPI, "in_per_px": in_per_px, "sheet_scale": "1:4 (labelled)",
        "body_length_cal_in": CAL_BODY_LENGTH_IN,
        "extracted_body_height_in": float(L_cal),
        "extracted_max_width_in": float(max_width),
        "cross_check": {
            "upper_bout_extracted_in": landmarks["upper_bout"]["full_width_in"],
            "upper_bout_label_in": CAL_UPPER_BOUT_IN,
            "lower_bout_extracted_in": landmarks["lower_bout"]["full_width_in"],
            "lower_bout_label_in": CAL_LOWER_BOUT_IN,
            "soundhole_dia_extracted_in": sh_dia_in,
            "soundhole_dia_label_in": CAL_SOUNDHOLE_DIA_IN,
        },
        "datum_A_soundhole": {
            "y_from_neck_in": sh_y_from_neck,
            "y_from_tail_in": (L_cal - sh_y_from_neck) if sh_y_from_neck is not None else None,
        },
        "symmetry_mode": symmetry_mode,
        "symmetry_discrepancy_in": 0.0,
    }
    return {"rows": rows_arr, "L_cal": L_cal, "landmarks": landmarks,
            "calibration": calibration}


def write_outputs(res: Dict) -> None:
    os.makedirs(_RESULTS, exist_ok=True)
    rows = res["rows"]
    # Outline CSV: right half, neck (y=0) -> tail (y=L). Deterministic, LF.
    with open(OUTLINE_CSV, "w", newline="") as fh:
        fh.write("y_from_neck_in,half_width_in\n")
        for y, hw in rows:
            fh.write(f"{y:.5f},{hw:.5f}\n")
    manifest = {
        "experiment": "D28_SIDE_INVERSE_RERUN_003",
        "note": "Source PDFs are NOT committed (public repo; copyrighted drawing). "
                "Only extracted geometry, checksums, and provenance are committed.",
        "sources": [
            {"filename": "1937 D-28.pdf", "role": "PRIMARY_HISTORICAL_SOURCE",
             "author": "John Arnold", "description": "1937 Martin D-28 serial #65260 "
             "hand-drawn construction drawing (rotated scan, PaperPort)",
             "repository_copy": False, "sha256": sha256(ARNOLD_PDF),
             "page_count": 1, "classification": "PRIMARY_HISTORICAL_SOURCE"},
            {"filename": "ACOUSTIC BODY.pdf", "role": "DRAWING_DERIVED_GEOMETRY_SOURCE",
             "draftsman": "JD", "description": "CAD 'ACOUSTIC BODY' layout; verified traced "
             "reconstruction of the John Arnold #65260 drawing (confirmed by JD). Datum A = soundhole.",
             "repository_copy": False, "sha256": sha256(ACOUSTIC_PDF),
             "page_count": 2, "classification": "DRAWING_DERIVED_GEOMETRY_SOURCE"},
        ],
        "extracted_geometry": os.path.relpath(OUTLINE_CSV, _REPO_ROOT),
        "calibration": res["calibration"],
        "landmarks": res["landmarks"],
    }
    with open(PROVENANCE_JSON, "w") as fh:
        json.dump(manifest, fh, indent=2)
    with open(EXTRACTION_JSON, "w") as fh:
        json.dump({"L_cal": res["L_cal"], "landmarks": res["landmarks"],
                   "calibration": res["calibration"],
                   "outline_point_count": int(len(rows))}, fh, indent=2)


if __name__ == "__main__":
    if not (os.path.exists(ACOUSTIC_PDF) and os.path.exists(ARNOLD_PDF)):
        raise SystemExit("STOP: source PDF(s) unavailable: "
                         f"ACOUSTIC={os.path.exists(ACOUSTIC_PDF)} "
                         f"ARNOLD={os.path.exists(ARNOLD_PDF)}")
    res = extract()
    write_outputs(res)
    lm = res["landmarks"]
    cc = res["calibration"]["cross_check"]
    print("Extraction OK")
    print(f"  outline points: {len(res['rows'])}, body length (cal): {res['L_cal']:.3f} in")
    print(f"  upper bout: {lm['upper_bout']['full_width_in']:.2f} in "
          f"(label {cc['upper_bout_label_in']}) @ y={lm['upper_bout']['y_from_neck_in']:.2f}")
    print(f"  waist:      {lm['waist']['full_width_in']:.2f} in @ y={lm['waist']['y_from_neck_in']:.2f} "
          f"(y/L={lm['waist']['y_norm']:.3f})")
    print(f"  lower bout: {lm['lower_bout']['full_width_in']:.2f} in "
          f"(label {cc['lower_bout_label_in']}) @ y={lm['lower_bout']['y_from_neck_in']:.2f}")
    print(f"  soundhole (datum A): dia={cc['soundhole_dia_extracted_in']} "
          f"y_from_neck={res['calibration']['datum_A_soundhole']['y_from_neck_in']}")
