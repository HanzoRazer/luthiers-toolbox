#!/usr/bin/env python3
"""
D28 RUN 004B — Proportional Dreadnought Similitude
==================================================

Replaces the single-radius spherical model (falsified in 003/004A) with a
PURE NORMALIZED SHAPE TRANSFER: extract the real generic-dreadnought side-depth
contour from the GenOne Luthier Supply "Dreadnought Side Contour Template"
(Sheet 05), normalize it by its own developed station coordinate, and transfer
that shape onto the verified Arnold/JD #65260 side endpoints. Then test whether
the cleaned 004A Arnold side-height dataset is reproduced WITHOUT any spherical
high point.

Locked design (per order):
  1. Reference = GenOne Sheet 05 side-contour template (NOT BodyContourSolver /
     Sevy). If it cannot be reliably extracted -> STOP INSUFFICIENT_REFERENCE_GEOMETRY.
  2. Pure shape transfer; no Sevy high-point P governs the model. P/R computed
     afterward only as a diagnostic.
  3. Normalize the GenOne template by its own station coordinate (developed,
     0=neck .. 1=tail). Do not force Arnold 30 7/16 to equal any GenOne dim.
  4. Rescale to #65260 side endpoints: neck 3.750 in, bottom 4.720 in.
  5. Validate against cleaned 004A Arnold stations 0,3,...,27; waist 4.220 at the
     geometric waist; bottom 4.720 at the geometric tail. No 10.5 / 30.4375.
  6. GenOne template depth includes top+back plates; plate values are NOT
     numerically dimensioned in the GenOne set (Sheet 02: "Top Thickness
     Varies"). A constant plate offset is invariant under the endpoint rescale
     to Arnold's SIDE-ONLY heights, so the subtraction is subsumed by step 4;
     any plate-thickness variation is unquantified and flagged (not assumed).
  7. Bracing back-check: qualitative geometric compatibility only.
  8. Known-answer fixture: extract -> normalize -> denormalize round-trip; report
     RMSE + max error (tol <= 0.010 in).
  9. Disposition vocab: PROPORTIONAL_SIMILITUDE_SUPPORTS_ADMISSIBLE_FIT /
     ..._DOES_NOT_SUPPORT_FIT / SIMILITUDE_INCONCLUSIVE / INSUFFICIENT_REFERENCE_GEOMETRY.
     Parent SPHERICAL_MODEL_MISMATCH untouched.

H1 (datum reconciliation): GenOne 30 11/32 (30.34375) ~ Arnold 30 7/16 (30.4375);
diff 3/32 in (0.31%). Both are developed side lengths (head/tail block ends) ->
source-supported analogy (documented, not used to tune the fit).

No PDF vendored; extracted geometry + SHA256/provenance committed. No
production/spec/authority edits. Runs 001/002/003/003A/004A preserved.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_UPLOADS = "/home/ubuntu/.cursor/projects/workspace/uploads"
GENONE_SHEET05 = os.path.join(_UPLOADS, "05_dreadnoughtplan_5_a985.pdf")


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r3 = _load("r3_004b", "d28_side_inverse_rerun003.py")

# --- Cleaned 004A Arnold authority -------------------------------------------
ARNOLD = {0.0: 3.750, 3.0: 3.740, 6.0: 3.895, 9.0: 4.085, 12.0: 4.240, 15.0: 4.350,
          18.0: 4.455, 21.0: 4.565, 24.0: 4.640, 27.0: 4.670}
ACTIVE_STATIONS = sorted(ARNOLD)
NECK_H, BOTTOM_H = 3.750, 4.720     # #65260 side endpoints (Arnold)
WAIST_H = 4.220                      # validation @ geometric waist
ARNOLD_SPAN = 30.4375               # 30 7/16 (later-source developed span; datum per 003A)
GENONE_TEMPLATE_LEN = 30.34375      # 30 11/32 (developed side-template length)

# GenOne Sheet 05 side-contour calibration (from vector text):
G_X_ST1 = 2279.46       # station 1 (tail block center) x, pt
G_PPIN = 72.03          # pt per 1-inch station
G_N_STATIONS = 31       # stations 1..31

OUTLINE_CSV = os.path.join(_RESULTS, "D28_65260_ARNOLD_OUTLINE.csv")   # #65260 (Rerun 003)
GENONE_CSV = os.path.join(_RESULTS, "D28_65260_GENONE_SIDE_CONTOUR_004B.csv")
PROV_JSON = os.path.join(_RESULTS, "D28_65260_RERUN_004B_PROVENANCE.json")
ANALYSIS_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004B_ANALYSIS.csv")
SUMMARY_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004B_SUMMARY.csv")
_DOC = os.path.join(_REPO_ROOT, "docs", "experiments", "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


# --- GenOne Sheet 05 side-contour extraction (deterministic) -----------------

def extract_genone_contour() -> Dict:
    """Extract total-depth-vs-station from the Sheet 05 side-contour template.
    top reference edge is a constant horizontal line; the bottom contour is the
    lower envelope. depth(station) = (y_bottom - y_top)/72 in. Returns per-station
    total depths (incl plates) and the normalized side shape f(u), u: 0=neck..1=tail.
    """
    import pymupdf
    pg = pymupdf.open(GENONE_SHEET05)[0]
    segs = []
    for p in pg.get_drawings():
        for it in p["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                x0, y0, x1, y1 = a.x, a.y, b.x, b.y
                if min(y0, y1) < 90 or max(y0, y1) > 520:
                    continue
                if min(x0, x1) < 110 or max(x0, x1) > 2290:
                    continue
                if abs(x1 - x0) > abs(y1 - y0) and abs(x1 - x0) > 5:
                    segs.append((x0, y0, x1, y1))
    if len(segs) < 30:
        raise RuntimeError("GenOne side-contour: too few strip segments extracted")

    def ys_at(xq):
        out = []
        for x0, y0, x1, y1 in segs:
            if (x0 - xq) * (x1 - xq) <= 0 and x0 != x1:
                t = (xq - x0) / (x1 - x0)
                out.append(y0 + t * (y1 - y0))
        return sorted(out)

    def xof(st):
        return G_X_ST1 - (st - 1) * G_PPIN

    # Top reference edge: the dominant minimum-y line (constant across stations).
    tops = []
    for st in range(2, G_N_STATIONS):
        ys = ys_at(xof(st))
        if ys:
            tops.append(ys[0])
    y_top = float(np.median(tops))
    # Per-station total depth = (bottom contour - top edge)/ppin.
    depth = {}
    for st in range(1, G_N_STATIONS + 1):
        ys = [y for y in ys_at(xof(st)) if y > y_top + 10]
        if not ys:
            continue
        y_bot = max(ys)
        depth[st] = (y_bot - y_top) / G_PPIN
    if len(depth) < 25:
        raise RuntimeError("GenOne side-contour: insufficient per-station depths")
    # station -> normalized u (0 at neck=station 31, 1 at tail=station 1)
    sts = sorted(depth)
    # neck depth = station max present; tail depth = station 1 present
    st_neck = max(sts); st_tail = min(sts)
    z_neck, z_tail = depth[st_neck], depth[st_tail]
    rows = []
    for st in sts:
        u = (st_neck - st) / (st_neck - st_tail)        # 0 neck .. 1 tail
        f = (depth[st] - z_neck) / (z_tail - z_neck)    # normalized side shape
        rows.append({"station": st, "total_depth_in": depth[st], "u": u, "f_shape": f})
    rows.sort(key=lambda r: r["u"])
    return {"rows": rows, "y_top": y_top, "z_neck_total": z_neck, "z_tail_total": z_tail,
            "st_neck": st_neck, "st_tail": st_tail, "n_stations": len(depth)}


def load_or_extract() -> Dict:
    if os.path.exists(GENONE_CSV):
        rows = []
        meta = {}
        with open(GENONE_CSV) as fh:
            for line in fh:
                if line.startswith("#"):
                    k, v = line[1:].strip().split("=", 1)
                    meta[k] = float(v)
                    continue
                if line.startswith("u,"):
                    continue
                u, f, st, z = line.strip().split(",")
                rows.append({"u": float(u), "f_shape": float(f), "station": float(st),
                             "total_depth_in": float(z)})
        return {"rows": rows, **meta}
    return extract_genone_contour()


# --- Normalized shape f(u) interpolator --------------------------------------

def shape_f(gen: Dict, u: float) -> float:
    us = np.array([r["u"] for r in gen["rows"]])
    fs = np.array([r["f_shape"] for r in gen["rows"]])
    return float(np.interp(min(max(u, 0.0), 1.0), us, fs))


def transfer_height(gen: Dict, u: float) -> float:
    return NECK_H + shape_f(gen, u) * (BOTTOM_H - NECK_H)


# --- #65260 geometric waist fraction (Rerun 003 outline) ---------------------

def waist_u() -> float:
    gw = r3.geometric_waist(r3._L_CAL)
    return gw["s_waist"] / gw["half_perimeter"]      # fractional developed position (neck..tail)


# --- Known-answer round-trip fixture -----------------------------------------

def roundtrip_fixture(gen: Dict) -> Dict:
    """extract total depth -> normalize f(u) -> reconstruct total depth using the
    GenOne endpoints -> compare to extracted. Also test interpolation resolution."""
    us = np.array([r["u"] for r in gen["rows"]])
    z = np.array([r["total_depth_in"] for r in gen["rows"]])
    z_neck, z_tail = gen["z_neck_total"], gen["z_tail_total"]
    f = (z - z_neck) / (z_tail - z_neck)
    z_rt = z_neck + f * (z_tail - z_neck)
    err = np.abs(z_rt - z)
    # interpolation round-trip at a denser u grid, back to the sample u
    ugrid = np.linspace(0, 1, 4 * len(us))
    fg = np.interp(ugrid, us, f)
    f_back = np.interp(us, ugrid, fg)
    interp_err = np.abs(f_back - f) * (z_tail - z_neck)
    return {"rmse_in": float(np.sqrt(np.mean(err ** 2))), "max_in": float(err.max()),
            "interp_rmse_in": float(np.sqrt(np.mean(interp_err ** 2))),
            "interp_max_in": float(interp_err.max())}


# --- Transfer + validation ---------------------------------------------------

def evaluate(gen: Dict) -> Dict:
    rows = []
    for s in ACTIVE_STATIONS:
        u = s / ARNOLD_SPAN
        Hp = transfer_height(gen, u)
        rows.append({"station": s, "u": u, "measured": ARNOLD[s], "predicted": Hp,
                     "residual": Hp - ARNOLD[s], "role": "endpoint" if s == 0.0 else "validation"})
    # waist @ geometric waist fraction
    uw = waist_u()
    Hw = transfer_height(gen, uw)
    waist = {"u": uw, "measured": WAIST_H, "predicted": Hw, "residual": Hw - WAIST_H}
    # bottom @ geometric tail (u=1) -> equals BOTTOM_H by construction
    Hb = transfer_height(gen, 1.0)
    bottom = {"u": 1.0, "measured": BOTTOM_H, "predicted": Hb, "residual": Hb - BOTTOM_H}
    interior = [r for r in rows if r["station"] not in (0.0,)]
    res = np.array([r["residual"] for r in interior])
    return {"rows": rows, "waist": waist, "bottom": bottom,
            "rmse": float(np.sqrt(np.mean(res ** 2))), "maxabs": float(np.abs(res).max())}


def diagnostic_equivalent_radius(gen: Dict) -> Dict:
    """Diagnostic only (NOT governing): fit a single Sevy sphere to the transferred
    heights and report its P/R, to show the shape model avoids the P<0 regime."""
    from scipy.optimize import least_squares
    us = np.linspace(0.05, 0.95, 19)
    Hs = np.array([transfer_height(gen, u) for u in us])
    L = r3._L_CAL

    def resid(p):
        R = float(p[0])
        P = r3.solve_high_point(L, BOTTOM_H, NECK_H, R)
        out = []
        for u, H in zip(us, Hs):
            y = u * L
            D = abs(y - (L - P))
            out.append(r3.solve_side_height(BOTTOM_H, R, P, D, 0, 0) - H)
        return np.array(out)
    try:
        sol = least_squares(resid, x0=[180.0], bounds=([96.0], [600.0]))
        R = float(sol.x[0]); P = r3.solve_high_point(L, BOTTOM_H, NECK_H, R)
        return {"R_ft": R / 12, "P_in": P, "rmse": float(np.sqrt(np.mean(sol.fun ** 2))),
                "note": "diagnostic only; the shape model needs no high point"}
    except Exception as e:
        return {"R_ft": None, "P_in": None, "rmse": None, "note": str(e)}


# --- H1 datum reconciliation -------------------------------------------------

def h1() -> Dict:
    diff = ARNOLD_SPAN - GENONE_TEMPLATE_LEN
    return {
        "genone_30_11_32_in": GENONE_TEMPLATE_LEN,
        "arnold_30_7_16_in": ARNOLD_SPAN,
        "difference_in": diff, "difference_frac": "3/32 in",
        "relative_pct": 100 * diff / GENONE_TEMPLATE_LEN,
        "genone_endpoints": "tail-block center (station 1) to head/neck end of the "
                            "side-contour template (developed side length)",
        "arnold_endpoints": "neck end to bottom end (Arnold 'distance from neck end'); "
                            "datum convention unresolved per 003A",
        "classification": "SOURCE_SUPPORTED_ANALOGY",
        "finding": "Both quantities are developed side lengths of a dreadnought measured "
                   "between the head/neck and tail block ends. The 3/32 in (0.31%) "
                   "difference is consistent with minor endpoint-convention or build "
                   "differences, not a different measurement type. Note the separate, "
                   "still-open tension: the ACOUSTIC-BODY-traced #65260 plan-view "
                   "half-perimeter (26.73 in, Rerun 003) is ~3.6 in shorter than both "
                   "developed side lengths, which remains UNRESOLVED.",
        "used_to_tune_fit": False,
    }


# --- Disposition -------------------------------------------------------------

def classify(ev: Dict, fixture: Dict, gen_ok: bool) -> Tuple[str, List[str]]:
    notes = []
    if not gen_ok:
        return "INSUFFICIENT_REFERENCE_GEOMETRY", [
            "GenOne Sheet 05 side-contour template could not be reliably extracted."]
    # admissible by construction (no high point). Judge the shape fit.
    rmse, mx = ev["rmse"], ev["maxabs"]
    wr = abs(ev["waist"]["residual"])
    notes.append(f"Model is admissible by construction (pure shape transfer; no high point / no P<0).")
    notes.append(f"Interior numeric-station RMSE = {rmse:.4f} in, max |resid| = {mx:.4f} in; "
                 f"waist residual = {ev['waist']['residual']:+.4f} in.")
    if rmse <= 0.03 and mx <= 0.06 and wr <= 0.05:
        return "PROPORTIONAL_SIMILITUDE_SUPPORTS_ADMISSIBLE_FIT", notes
    if rmse <= 0.06 and mx <= 0.12:
        notes.append("Fit is admissible and moderate but exceeds the tight-fit threshold "
                     "(esp. the waist); classed inconclusive.")
        return "SIMILITUDE_INCONCLUSIVE", notes
    notes.append("Transferred generic-dreadnought shape does not reproduce the Arnold "
                 "side-height sequence within acceptable residuals.")
    return "PROPORTIONAL_SIMILITUDE_DOES_NOT_SUPPORT_FIT", notes


# --- Writers -----------------------------------------------------------------

def write_genone_csv(gen: Dict):
    os.makedirs(_RESULTS, exist_ok=True)
    with open(GENONE_CSV, "w", newline="") as fh:
        fh.write(f"#y_top={gen['y_top']:.4f}\n#z_neck_total={gen['z_neck_total']:.5f}\n")
        fh.write(f"#z_tail_total={gen['z_tail_total']:.5f}\n#st_neck={gen['st_neck']}\n")
        fh.write(f"#st_tail={gen['st_tail']}\n#n_stations={gen['n_stations']}\n")
        fh.write("u,f_shape,station,total_depth_in\n")
        for r in gen["rows"]:
            fh.write(f"{r['u']:.5f},{r['f_shape']:.5f},{r['station']:.0f},{r['total_depth_in']:.5f}\n")


def write_provenance(gen: Dict):
    manifest = {
        "experiment": "D28_RUN_004B_PROPORTIONAL_SIMILITUDE",
        "note": "Source PDFs NOT committed (public repo; copyrighted plan). Only extracted "
                "geometry + checksums + provenance committed.",
        "sources": [{
            "filename": "05 dreadnoughtplan_5.pdf (GenOne Luthier Supply, Dreadnought Guitar Plan, Sheet 05)",
            "role": "GENERIC_DREADNOUGHT_SIDE_CONTOUR_REFERENCE",
            "publisher": "GenOne Luthier Supply", "sha256": sha256(GENONE_SHEET05),
            "page_count": 1, "classification": "DRAWING_DERIVED",
            "notes": "Dreadnought Side Contour Template; 1 in / 25.4 mm station grid; "
                     "end depths 4 3/4 / 3 3/4 in (incl plates); length 30 11/32 in; back arch R 3657.6 mm."},
        ],
        "plate_thickness": "NOT numerically dimensioned in the GenOne set (Sheet 02: 'Top "
                           "Thickness Varies'). Not assumed. Endpoint rescale to Arnold "
                           "side-only heights subsumes a constant plate offset.",
        "repo_spherical_default_role": "comparison diagnostic only (NOT the 004B reference)",
        "calibration": {"pt_per_inch": G_PPIN, "station1_x_pt": G_X_ST1,
                        "y_top_pt": gen["y_top"], "z_neck_total_in": gen["z_neck_total"],
                        "z_tail_total_in": gen["z_tail_total"], "n_stations": gen["n_stations"]},
    }
    with open(PROV_JSON, "w") as fh:
        json.dump(manifest, fh, indent=2)


def write_analysis_csv(gen: Dict, ev: Dict, fixture: Dict, diag: Dict, H: Dict):
    fields = ["section", "key", "station_in", "u", "measured_in", "predicted_in",
              "residual_in", "value", "notes"]
    rows = []
    for r in ev["rows"]:
        rows.append({"section": "transfer", "key": f"station_{r['station']:.0f}",
                     "station_in": f"{r['station']:.4f}", "u": f"{r['u']:.5f}",
                     "measured_in": f"{r['measured']:.4f}", "predicted_in": f"{r['predicted']:.4f}",
                     "residual_in": f"{r['residual']:+.5f}", "value": "", "notes": r["role"]})
    for k, d in (("waist", ev["waist"]), ("bottom", ev["bottom"])):
        rows.append({"section": "validation", "key": k, "station_in": "",
                     "u": f"{d['u']:.5f}", "measured_in": f"{d['measured']:.4f}",
                     "predicted_in": f"{d['predicted']:.4f}", "residual_in": f"{d['residual']:+.5f}",
                     "value": "", "notes": "geometric position"})
    for k, v in (("rmse_in", ev["rmse"]), ("maxabs_in", ev["maxabs"]),
                 ("roundtrip_rmse_in", fixture["rmse_in"]), ("roundtrip_max_in", fixture["max_in"]),
                 ("interp_max_in", fixture["interp_max_in"]),
                 ("diag_equiv_R_ft", diag["R_ft"]), ("diag_equiv_P_in", diag["P_in"]),
                 ("H1_genone_len_in", H["genone_30_11_32_in"]), ("H1_arnold_span_in", H["arnold_30_7_16_in"]),
                 ("H1_diff_in", H["difference_in"])):
        rows.append({"section": "metric", "key": k, "station_in": "", "u": "", "measured_in": "",
                     "predicted_in": "", "residual_in": "", "value": (f"{v:.5f}" if isinstance(v, float) else str(v)),
                     "notes": ""})
    with open(ANALYSIS_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def write_summary_csv(gen: Dict, ev: Dict, fixture: Dict, diag: Dict, H: Dict, disp: str):
    row = {
        "reference": "GenOne Sheet 05 Dreadnought Side Contour Template",
        "reference_classification": "DRAWING_DERIVED (real template, not Sevy)",
        "model": "pure normalized shape transfer (no high point)",
        "genone_n_stations": gen["n_stations"],
        "genone_depth_neck_in": f"{gen['z_neck_total']:.3f}", "genone_depth_tail_in": f"{gen['z_tail_total']:.3f}",
        "endpoints_neck_in": NECK_H, "endpoints_bottom_in": BOTTOM_H,
        "numeric_rmse_in": f"{ev['rmse']:.4f}", "numeric_maxabs_in": f"{ev['maxabs']:.4f}",
        "waist_predicted_in": f"{ev['waist']['predicted']:.4f}", "waist_residual_in": f"{ev['waist']['residual']:+.4f}",
        "bottom_residual_in": f"{ev['bottom']['residual']:+.4f}",
        "physical_admissibility": "admissible by construction (no P)",
        "diag_equiv_R_ft": (f"{diag['R_ft']:.1f}" if diag["R_ft"] else ""),
        "diag_equiv_P_in": (f"{diag['P_in']:+.2f}" if diag["P_in"] is not None else ""),
        "roundtrip_max_in": f"{fixture['max_in']:.5f}", "roundtrip_interp_max_in": f"{fixture['interp_max_in']:.5f}",
        "H1_class": H["classification"], "H1_diff_in": f"{H['difference_in']:.5f}",
        "disposition": disp, "parent_spherical_mismatch": "untouched",
    }
    with open(SUMMARY_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row.keys()), lineterminator="\n")
        w.writeheader(); w.writerow(row)


# --- Report ------------------------------------------------------------------

def git_sha():
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception: return "UNKNOWN"


_S, _E = "<!-- RERUN004B_START -->", "<!-- RERUN004B_END -->"


def build_section(gen, ev, fixture, diag, H, disp, notes) -> str:
    L = []; w = L.append
    w("## Run 004B — Proportional Dreadnought Similitude")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Replaces the falsified single-radius spherical model with a **pure normalized "
      "side-depth shape transfer** from the **GenOne Sheet 05 Dreadnought Side Contour "
      "Template** (a real drawn template, not BodyContourSolver/Sevy). No spherical high "
      "point governs the model, so a P<0 result is impossible by construction.")
    w("- Neither PDF is vendored; extracted geometry + SHA-256/provenance committed "
      "(`D28_65260_GENONE_SIDE_CONTOUR_004B.csv`, `D28_65260_RERUN_004B_PROVENANCE.json`, "
      "`D28_65260_RERUN_004B_ANALYSIS.csv`, `D28_65260_RERUN_004B_SUMMARY.csv`).")
    w("")
    w("### Reference extraction (GenOne Sheet 05)")
    w("")
    w(f"- Side-contour template extracted on a 1 in = {G_PPIN:.2f} pt station grid "
      f"(stations 1=tail .. {gen['st_neck']}=neck); {gen['n_stations']} per-station depths.")
    w(f"- Total depth (incl. plates): neck = {gen['z_neck_total']:.3f} in, tail = "
      f"{gen['z_tail_total']:.3f} in (drawing end dims 3 3/4 / 4 3/4 in).")
    w("- **Plate thickness** is NOT numerically dimensioned in the GenOne set (Sheet 02: "
      "\"Top Thickness Varies\"); not assumed. The endpoint rescale to Arnold's side-only "
      "heights subsumes a constant plate offset (normalized shape is invariant to it); any "
      "plate-thickness variation is unquantified and flagged. Repo 25-ft spherical contour "
      "used only as a comparison diagnostic.")
    w("")
    w("### Known-answer round-trip fixture")
    w("")
    w(f"- extract → normalize → denormalize: RMSE = {fixture['rmse_in']:.5f} in, max = "
      f"{fixture['max_in']:.5f} in (identity, numerical precision).")
    w(f"- interpolation round-trip (4× resolution): max = {fixture['interp_max_in']:.5f} in "
      f"(≤ 0.010 in tolerance: {'PASS' if fixture['interp_max_in'] <= 0.010 else 'REVIEW'}).")
    w("")
    w("### Transfer onto #65260 (endpoints 3.750 neck / 4.720 bottom)")
    w("")
    w("`H(u) = 3.750 + f_GenOne(u)·(4.720 − 3.750)`, u = developed fraction (0 neck .. 1 tail); "
      "Arnold station u = station / 30.4375.")
    w("")
    w("| Arnold station (in) | u | measured H (in) | predicted H (in) | residual (in) |")
    w("|---:|---:|---:|---:|---:|")
    for r in ev["rows"]:
        w(f"| {r['station']:.0f} | {r['u']:.3f} | {r['measured']:.4f} | {r['predicted']:.4f} | {r['residual']:+.4f} |")
    w(f"| waist @u={ev['waist']['u']:.3f} | {ev['waist']['u']:.3f} | {ev['waist']['measured']:.4f} "
      f"| {ev['waist']['predicted']:.4f} | {ev['waist']['residual']:+.4f} |")
    w(f"| bottom @u=1.000 | 1.000 | {ev['bottom']['measured']:.4f} | {ev['bottom']['predicted']:.4f} "
      f"| {ev['bottom']['residual']:+.4f} |")
    w("")
    w(f"- Interior numeric-station **RMSE = {ev['rmse']:.4f} in**, max |resid| = {ev['maxabs']:.4f} in; "
      f"waist residual {ev['waist']['residual']:+.4f} in.")
    w("")
    w("### Diagnostic (not governing): equivalent single-radius sphere")
    w("")
    if diag["R_ft"] is not None:
        w(f"- A sphere fitted to the transferred heights would need R ≈ {diag['R_ft']:.1f} ft, "
          f"P ≈ {diag['P_in']:+.2f} in — reported only to compare with the falsified model; "
          "the shape transfer itself uses no high point.")
    w("")
    w("### H1 — datum reconciliation (promoted)")
    w("")
    w(f"- GenOne **30 11/32 in = {H['genone_30_11_32_in']}** (developed side-template length: "
      "tail-block center → head/neck end).")
    w(f"- Arnold **30 7/16 in = {H['arnold_30_7_16_in']}** (developed 'distance from neck end'; "
      "datum per 003A).")
    w(f"- Difference = **{H['difference_in']:.5f} in (3/32 in, {H['relative_pct']:.2f}%)**.")
    w(f"- Classification: **`{H['classification']}`** — {H['finding']}")
    w("- H1 was NOT used to tune the fit; it guided only the side-length-convention investigation.")
    w("")
    w("### Bracing / Datum A compatibility (qualitative)")
    w("")
    w("- The shape transfer changes only the side-height profile; it does not alter the #65260 "
      "plan outline, soundhole Datum A, or the X-brace/back-brace plan layout. The reconstructed "
      "side geometry remains compatible with the measured #65260 brace positions and Datum A "
      "relationships (no plan-view geometry changed). Brace cross-section depths are NOT compared "
      "to back-arch rise (unrelated quantities).")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{disp}`**")
    w("")
    for n in notes:
        w(f"- {n}")
    w("")
    w("Parent `SPHERICAL_MODEL_MISMATCH` is untouched. Classification ledger: GenOne template = "
      "`DRAWING_DERIVED`; transferred heights/residuals/round-trip = `CALCULATED`; H1 analogy = "
      "`SOURCE_SUPPORTED_ANALOGY`; #65260↔developed-span reconciliation (26.73 vs 30.4) = `UNRESOLVED`.")
    w("")
    return "\n".join(L)


def splice_doc(section):
    with open(_DOC) as fh: text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    else:
        marker = "<!-- RERUN004A_START -->"
        text = text[:text.index(marker)] + block + "\n\n---\n\n" + text[text.index(marker):]
    with open(_DOC, "w") as fh: fh.write(text)


def run_all():
    gen = load_or_extract()
    gen_ok = gen.get("n_stations", 0) >= 25
    ev = evaluate(gen)
    fixture = roundtrip_fixture(gen)
    diag = diagnostic_equivalent_radius(gen)
    H = h1()
    disp, notes = classify(ev, fixture, gen_ok)
    return gen, ev, fixture, diag, H, disp, notes


def main():
    if not os.path.exists(GENONE_SHEET05) and not os.path.exists(GENONE_CSV):
        raise SystemExit("STOP INSUFFICIENT_REFERENCE_GEOMETRY: GenOne Sheet 05 not available.")
    gen, ev, fixture, diag, H, disp, notes = run_all()
    section = build_section(gen, ev, fixture, diag, H, disp, notes)
    if "--write" in sys.argv:
        write_genone_csv(gen); write_provenance(gen)
        write_analysis_csv(gen, ev, fixture, diag, H); write_summary_csv(gen, ev, fixture, diag, H, disp)
        splice_doc(section)
        print(f"wrote {GENONE_CSV}\nwrote {PROV_JSON}\nwrote {ANALYSIS_CSV}\nwrote {SUMMARY_CSV}")
        print(f"spliced Run 004B into {_DOC}")
    else:
        print(section)
        print(f"\n[disposition={disp}]")


if __name__ == "__main__":
    main()
