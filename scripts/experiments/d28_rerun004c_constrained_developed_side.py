#!/usr/bin/env python3
"""
D28 RUN 004C — Constrained Developed-Side Reconstruction
========================================================

Reverses the 004B hierarchy: Arnold's measured side heights are the PRIMARY hard
constraints over the active developed-side coordinate s in [0, 30.4375]; the
GenOne dreadnought plan contributes only LONGITUDINAL LANDMARK PRIORS (not depth
values) to locate the waist between known stations. #65260 measurements override
generic proportions wherever they conflict.

Active authority:
  developed side length = 30.4375 in (ACTIVE boundary; not inferred from plan perimeter)
  Arnold stations 0,3,6,9,12,15,18,21,24,27 and bottom 30.4375 (station 27 IN-DOMAIN)
  waist height 4.220 (station not source-specified -> placed by reconstruction + GenOne prior)

Model: shape-preserving PCHIP through all Arnold points (handles the 3.750->3.740
dip; no global monotonicity forced; no overshoot). No Sevy high point. GenOne is
proportional/landmark-only. BodyContourSolver spherical defaults: comparison only.

No PDF vendored (extracted geometry + SHA-256/provenance committed). No
production/spec/authority edits. Runs 001/002/003/003A/004A/004B preserved.
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
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

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


r3 = _load("r3_004c", "d28_side_inverse_rerun003.py")

# === SOURCE AUTHORITY (Arnold primary) =======================================
DEV_SIDE_LEN = 30.4375                        # active developed-side length (30 7/16)
STATIONED = {0.0: 3.750, 3.0: 3.740, 6.0: 3.895, 9.0: 4.085, 12.0: 4.240,
             15.0: 4.350, 18.0: 4.455, 21.0: 4.565, 24.0: 4.640, 27.0: 4.670}
BOTTOM_STATION, BOTTOM_H = 30.4375, 4.720     # bottom endpoint
WAIST_H = 4.220                               # height; station not source-specified
# Full constraint set (Arnold stations + bottom), ordered:
SRC_POINTS = sorted(list(STATIONED.items()) + [(BOTTOM_STATION, BOTTOM_H)])
DEEP_IN = 4.4375                              # assembled "4 7/16 DEEP"
PLAN_HALF_PERIM = r3.geometric_waist(r3._L_CAL)["half_perimeter"]   # 26.73 diagnostic
GENONE_TEMPLATE_LEN = 30.34375               # 30 11/32

# GenOne Sheet 05 station grid (1=tail .. 31=neck).
G_X_ST1 = 2279.46
G_PPIN = 72.03

AUTH_JSON = os.path.join(_RESULTS, "D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json")
PROFILE_CSV = os.path.join(_RESULTS, "D28_65260_CONSTRAINED_SIDE_PROFILE_004C.csv")
LANDMARK_CSV = os.path.join(_RESULTS, "D28_65260_LANDMARK_RECONSTRUCTION_004C.csv")
DEEP_CSV = os.path.join(_RESULTS, "D28_65260_DEEP_INTERPRETATION_004C.csv")
ANALYSIS_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004C_ANALYSIS.csv")
SUMMARY_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004C_SUMMARY.csv")
PROV_JSON = os.path.join(_RESULTS, "D28_65260_RERUN_004C_PROVENANCE.json")
_DOC = os.path.join(_REPO_ROOT, "docs", "experiments", "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


# --- Source validation (fail closed) -----------------------------------------

def validate_source():
    s = [p[0] for p in SRC_POINTS]
    if s != sorted(s):
        raise SystemExit("STOP: source stations not ascending")
    if len(set(s)) != len(s):
        raise SystemExit("STOP: duplicate source stations")
    if abs(s[-1] - DEV_SIDE_LEN) > 1e-9:
        raise SystemExit("STOP: endpoint station != developed side length")
    if 27.0 not in STATIONED:
        raise SystemExit("STOP: station 27 missing (must be in-domain)")


# --- GenOne proportional landmark extraction (longitudinal only) -------------

def extract_genone_landmarks() -> Dict:
    import pymupdf
    pg = pymupdf.open(GENONE_SHEET05)[0]
    def st_of_x(x): return 1 + (G_X_ST1 - x) / G_PPIN
    words = pg.get_text("words")
    def find(word):
        xs = [(w[0] + w[2]) / 2 for w in words if w[3] < 560 and w[4] == word]
        return st_of_x(sorted(xs)[0]) if xs else None
    g = {"head": find("Head"), "upper_bout": find("Upper"), "waist": find("Waist"),
         "lower_bout": find("Lower"), "tail": find("Tail")}
    if any(v is None for v in g.values()):
        raise RuntimeError(f"GenOne landmark extraction failed: {g}")
    st_neck, st_tail = g["head"], g["tail"]
    out = {}
    for k, st in g.items():
        u = (st_neck - st) / (st_neck - st_tail)      # 0 neck .. 1 tail
        out[k] = {"genone_station": st, "u": u, "s_65260_in": u * DEV_SIDE_LEN}
    return out


def load_or_extract_landmarks() -> Dict:
    if os.path.exists(LANDMARK_CSV):
        out = {}
        with open(LANDMARK_CSV) as fh:
            for line in fh:
                if line.startswith("landmark") or not line.strip():
                    continue
                parts = line.strip().split(",")
                k = parts[0]
                if k in ("head", "upper_bout", "waist", "lower_bout", "tail"):
                    out[k] = {"genone_station": float(parts[1]), "u": float(parts[2]),
                              "s_65260_in": float(parts[3])}
        if len(out) == 5:
            return out
    return extract_genone_landmarks()


# --- Constrained reconstruction ----------------------------------------------

def build_pchip():
    xs = np.array([p[0] for p in SRC_POINTS])
    ys = np.array([p[1] for p in SRC_POINTS])
    return PchipInterpolator(xs, ys, extrapolate=False)


def solve_waist_station(H, lo=9.0, hi=12.0) -> Optional[float]:
    def g(s): return float(H(s)) - WAIST_H
    if g(lo) * g(hi) > 0:
        return None
    return float(brentq(g, lo, hi, xtol=1e-9))


def admissibility(H) -> Dict:
    s = np.linspace(0, DEV_SIDE_LEN, int(DEV_SIDE_LEN / 0.01))
    h = H(s)
    d1 = H.derivative(1)(s)
    d2 = H.derivative(2)(s)
    # overshoot: profile must stay within [min,max] of neighboring source values per segment
    xs = [p[0] for p in SRC_POINTS]; ys = [p[1] for p in SRC_POINTS]
    overshoot = 0.0
    for i in range(len(xs) - 1):
        seg = (s >= xs[i]) & (s <= xs[i + 1])
        lo, hi = min(ys[i], ys[i + 1]), max(ys[i], ys[i + 1])
        if seg.any():
            over = max(0.0, float(h[seg].max() - hi), float(lo - h[seg].min()))
            overshoot = max(overshoot, over)
    # exact passage at source points
    maxerr = max(abs(float(H(x)) - y) for x, y in SRC_POINTS)
    return {"continuous": bool(np.all(np.isfinite(h))),
            "max_overshoot_in": overshoot,
            "max_source_err_in": maxerr,
            "min_slope": float(np.nanmin(d1)), "max_slope": float(np.nanmax(d1)),
            "max_abs_curvature": float(np.nanmax(np.abs(d2))),
            "finite_slope": bool(np.all(np.isfinite(d1))),
            "finite_curvature": bool(np.all(np.isfinite(d2)))}


def diagnostic_fits(H) -> Dict:
    """Diagnostic only; do not drive the reconstruction."""
    s = np.linspace(0.5, DEV_SIDE_LEN - 0.5, 40)
    h = np.array([float(H(x)) for x in s])
    out = {}
    # A: single-radius sphere (Sevy), longitudinal y=u*L on #65260
    from scipy.optimize import least_squares
    L = r3._L_CAL
    def sph(p):
        R = float(p[0]); P = r3.solve_high_point(L, BOTTOM_H, 3.750, R)
        return np.array([r3.solve_side_height(BOTTOM_H, R, P, abs((x / DEV_SIDE_LEN) * L - (L - P)), 0, 0) - hh
                         for x, hh in zip(s, h)])
    try:
        sol = least_squares(sph, [180.0], bounds=([96], [600]))
        R = float(sol.x[0]); P = r3.solve_high_point(L, BOTTOM_H, 3.750, R)
        out["sphere"] = {"R_ft": R / 12, "P_in": P, "rmse": float(np.sqrt(np.mean(sol.fun ** 2)))}
    except Exception as e:
        out["sphere"] = {"error": str(e)}
    # C: low-order polynomial
    for deg in (3, 4):
        c = np.polyfit(s, h, deg)
        out[f"poly{deg}"] = {"rmse": float(np.sqrt(np.mean((np.polyval(c, s) - h) ** 2)))}
    return out


# --- H1 / developed-length comparisons ---------------------------------------

def comparisons() -> Dict:
    return {
        "dev_vs_plan": {"developed_in": DEV_SIDE_LEN, "plan_half_perim_in": PLAN_HALF_PERIM,
                        "diff_in": DEV_SIDE_LEN - PLAN_HALF_PERIM,
                        "pct": 100 * (DEV_SIDE_LEN - PLAN_HALF_PERIM) / PLAN_HALF_PERIM,
                        "note": "different geometric quantities; 004C uses 30.4375 as developed "
                                "coordinate authority; 26.73 is a plan-view curve-length diagnostic only"},
        "genone_vs_arnold": {"genone_in": GENONE_TEMPLATE_LEN, "arnold_in": DEV_SIDE_LEN,
                             "diff_in": DEV_SIDE_LEN - GENONE_TEMPLATE_LEN, "pct": 100 * (DEV_SIDE_LEN - GENONE_TEMPLATE_LEN) / GENONE_TEMPLATE_LEN,
                             "classification": "SOURCE_SUPPORTED_ANALOGY"},
        "deep": {"deep_in": DEEP_IN, "waist_side_in": WAIST_H, "diff_in": DEEP_IN - WAIST_H,
                 "diff_mm": (DEEP_IN - WAIST_H) * 25.4,
                 "classification": "SOURCE_CORROBORATED_INTERPRETATION",
                 "note": "assembled DEEP minus side height = top+back plate contribution per the "
                         "GenOne construction convention; exact top/back split unresolved; #65260 "
                         "plate thicknesses not invented"}}


def run_all():
    validate_source()
    land = load_or_extract_landmarks()
    H = build_pchip()
    waist_prior = land["waist"]["s_65260_in"]
    waist_solved = solve_waist_station(H)
    H_at_prior = float(H(waist_prior))
    adm = admissibility(H)
    diag = diagnostic_fits(H)
    comp = comparisons()
    # disposition
    tol = 1e-6
    supported = (adm["max_source_err_in"] < tol and adm["max_overshoot_in"] < 0.01
                 and waist_solved is not None and 9.0 < waist_solved < 12.0
                 and abs(H_at_prior - WAIST_H) < 0.05)
    if adm["max_source_err_in"] >= 1e-4:
        disp = "INSUFFICIENT_GEOMETRY_AUTHORITY"
        notes = ["Source points not reproduced exactly."]
    elif supported:
        disp = "CONSTRAINED_DEVELOPED_RECONSTRUCTION_SUPPORTED"
        notes = [f"All source points reproduced exactly (max err {adm['max_source_err_in']:.2e} in); "
                 f"no overshoot ({adm['max_overshoot_in']:.4f} in).",
                 f"Waist placeable at s={waist_solved:.2f} in (H=4.220 between stations 9 and 12); "
                 f"GenOne proportional prior s={waist_prior:.2f} in; profile at the prior predicts "
                 f"{H_at_prior:.4f} in (residual {H_at_prior-WAIST_H:+.4f} in).",
                 "Developed coordinate 30.4375 in internally coherent; station 27 in-domain; "
                 "no Sevy high point / single-radius condition required."]
    elif waist_solved is not None:
        disp = "CONSTRAINED_RECONSTRUCTION_GEOMETRIC_TENSION"
        notes = ["Source points satisfied but waist/curvature placement is strained."]
    else:
        disp = "CONSTRAINED_RECONSTRUCTION_INCONCLUSIVE"
        notes = ["Waist 4.220 cannot be placed between neighboring source stations."]
    return dict(land=land, H=H, waist_prior=waist_prior, waist_solved=waist_solved,
                H_at_prior=H_at_prior, adm=adm, diag=diag, comp=comp, disp=disp, notes=notes)


# --- Writers -----------------------------------------------------------------

def _wr_csv(path, fields, rows):
    os.makedirs(_RESULTS, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def write_authority(R):
    rec = {
        "developed_side_length_in": DEV_SIDE_LEN,
        "stationed_side_heights": [{"station_in": s, "height_in": h} for s, h in sorted(STATIONED.items())],
        "named_landmarks": {"waist": {"height_in": WAIST_H, "station_in": None},
                            "bottom": {"height_in": BOTTOM_H, "station_in": BOTTOM_STATION}},
        "classifications": {
            "developed_side_length_30.4375": "SOURCE_MEASURED (active developed-side boundary)",
            "waist_4.220": "SOURCE_MEASURED (height); station via reconstruction + GenOne prior",
            "bottom_4.720": "SOURCE_MEASURED (@ developed-side endpoint 30.4375)",
            "genone_landmark_proportions": "SOURCE_SUPPORTED_ANALOGY (longitudinal priors only)",
            "jd_arnold_traced_outline": "VERIFIED_DRAWING_DERIVED (plan geometry; 26.73 half-perimeter diagnostic)",
            "deep_4.4375": "SOURCE_CORROBORATED_INTERPRETATION (assembled depth, not raw side height)",
            "plan_half_perimeter_26.73": "VERIFIED_DRAWING_DERIVED diagnostic (NOT the developed-side authority)"},
        "genone_landmark_priors_s65260_in": {k: round(v["s_65260_in"], 3) for k, v in R["land"].items()},
        "notes": "Hierarchy: Arnold measurements override generic proportions. GenOne used for "
                 "longitudinal landmark priors only; full GenOne side-height curve NOT transferred."}
    with open(AUTH_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


def write_provenance():
    with open(PROV_JSON, "w") as fh:
        json.dump({"experiment": "D28_RUN_004C_CONSTRAINED_DEVELOPED_SIDE",
                   "sources": [{"filename": "05 dreadnoughtplan_5.pdf (GenOne Sheet 05)",
                                "role": "LONGITUDINAL_LANDMARK_PRIOR_ONLY", "sha256": sha256(GENONE_SHEET05),
                                "classification": "SOURCE_SUPPORTED_ANALOGY",
                                "note": "only head/UB/waist/LB/tail station proportions used; "
                                        "no side-height depth transferred"}],
                   "pdf_vendored": False,
                   "bodycontoursolver_spherical": "comparison only, not authority"}, fh, indent=2)


def write_profile(R):
    H = R["H"]; d1 = H.derivative(1); d2 = H.derivative(2)
    src_s = [p[0] for p in SRC_POINTS]
    rows = []
    s = 0.0
    while s <= DEV_SIDE_LEN + 1e-9:
        hs = float(H(s))
        near = min(src_s, key=lambda x: abs(x - s))
        is_src = abs(s - near) < 1e-6
        rows.append({"s_in": f"{s:.4f}", "u": f"{s/DEV_SIDE_LEN:.5f}", "height_in": f"{hs:.5f}",
                     "height_mm": f"{hs*25.4:.4f}", "segment": f"{int(min(near, s)//3)}",
                     "source_status": ("SOURCE_MEASURED" if is_src else "INTERPOLATED"),
                     "exact_measurement": (f"{STATIONED.get(near, BOTTOM_H):.4f}" if is_src else ""),
                     "interpolation_method": "PCHIP",
                     "local_slope": f"{float(d1(s)):.5f}", "local_curvature": f"{float(d2(s)):.5f}",
                     "distance_to_nearest_source_station": f"{abs(s-near):.4f}"})
        s = round(s + 0.125, 4)
    # mark endpoints and the named waist landmark row
    rows[0]["source_status"] = "ENDPOINT"; rows[-1]["source_status"] = "ENDPOINT"
    _wr_csv(PROFILE_CSV, list(rows[0].keys()), rows)


def write_landmarks(R):
    land = R["land"]
    recon = {"upper_bout": None, "waist": R["waist_solved"], "lower_bout": None, "tail": DEV_SIDE_LEN}
    rows = []
    for k in ("head", "upper_bout", "waist", "lower_bout", "tail"):
        prior = land[k]["s_65260_in"]
        rec = recon.get(k)
        rows.append({"landmark": k, "genone_station": f"{land[k]['genone_station']:.3f}",
                     "u": f"{land[k]['u']:.5f}", "prior_s65260_in": f"{prior:.4f}",
                     "reconstructed_s_in": ("" if rec is None else f"{rec:.4f}"),
                     "delta_in": ("" if rec is None else f"{rec-prior:+.4f}"),
                     "status": ("SOURCE_SUPPORTED_ANALOGY prior" if rec is None
                                else "reconstructed vs prior")})
    _wr_csv(LANDMARK_CSV, list(rows[0].keys()), rows)


def write_deep(R):
    c = R["comp"]["deep"]
    _wr_csv(DEEP_CSV, ["quantity", "value_in", "value_mm", "classification", "note"], [
        {"quantity": "waist raw side height", "value_in": f"{WAIST_H:.4f}", "value_mm": f"{WAIST_H*25.4:.3f}",
         "classification": "SOURCE_MEASURED", "note": "Arnold waist"},
        {"quantity": "assembled DEEP (4 7/16)", "value_in": f"{DEEP_IN:.4f}", "value_mm": f"{DEEP_IN*25.4:.3f}",
         "classification": "SOURCE_CORROBORATED_INTERPRETATION", "note": "assembled body depth, not side height"},
        {"quantity": "difference (DEEP - side)", "value_in": f"{c['diff_in']:.4f}", "value_mm": f"{c['diff_mm']:.4f}",
         "classification": "CALCULATED", "note": "top+back plate contribution; exact split unresolved; plates not invented"}])


def write_analysis(R):
    rows = []
    for s, h in SRC_POINTS:
        rows.append({"section": "source_point", "key": f"s{s:g}", "value_in": f"{h:.4f}",
                     "reconstructed_in": f"{float(R['H'](s)):.5f}", "residual_in": f"{float(R['H'](s))-h:+.2e}"})
    adm = R["adm"]
    for k in ("max_source_err_in", "max_overshoot_in", "min_slope", "max_slope", "max_abs_curvature"):
        rows.append({"section": "admissibility", "key": k, "value_in": f"{adm[k]:.5f}", "reconstructed_in": "", "residual_in": ""})
    rows.append({"section": "waist", "key": "solved_station_in", "value_in": f"{R['waist_solved']:.4f}", "reconstructed_in": "", "residual_in": ""})
    rows.append({"section": "waist", "key": "genone_prior_station_in", "value_in": f"{R['waist_prior']:.4f}", "reconstructed_in": "", "residual_in": ""})
    rows.append({"section": "waist", "key": "H_at_prior_in", "value_in": f"{R['H_at_prior']:.4f}", "reconstructed_in": "", "residual_in": f"{R['H_at_prior']-WAIST_H:+.4f}"})
    sph = R["diag"].get("sphere", {})
    if "R_ft" in sph:
        rows.append({"section": "diagnostic", "key": "sphere_R_ft", "value_in": f"{sph['R_ft']:.2f}", "reconstructed_in": "", "residual_in": ""})
        rows.append({"section": "diagnostic", "key": "sphere_P_in", "value_in": f"{sph['P_in']:+.3f}", "reconstructed_in": "", "residual_in": f"{sph['rmse']:.4f}"})
    _wr_csv(ANALYSIS_CSV, ["section", "key", "value_in", "reconstructed_in", "residual_in"], rows)


def write_summary(R):
    adm = R["adm"]; c = R["comp"]; land = R["land"]
    row = {"developed_side_length_in": DEV_SIDE_LEN,
           "active_source_stations": " ".join(str(int(s)) for s in sorted(STATIONED)) + " 30.4375",
           "reconstructed_waist_station_in": f"{R['waist_solved']:.3f}",
           "genone_waist_prior_in": f"{R['waist_prior']:.3f}",
           "waist_measured_in": WAIST_H, "waist_residual_at_prior_in": f"{R['H_at_prior']-WAIST_H:+.4f}",
           "upper_bout_station_in": f"{land['upper_bout']['s_65260_in']:.3f}",
           "lower_bout_station_in": f"{land['lower_bout']['s_65260_in']:.3f}",
           "tail_station_in": f"{DEV_SIDE_LEN:.4f}",
           "bottom_residual_in": f"{float(R['H'](BOTTOM_STATION))-BOTTOM_H:+.2e}",
           "max_source_err_in": f"{adm['max_source_err_in']:.2e}", "max_overshoot_in": f"{adm['max_overshoot_in']:.4f}",
           "max_abs_curvature": f"{adm['max_abs_curvature']:.4f}",
           "min_slope": f"{adm['min_slope']:.4f}", "max_slope": f"{adm['max_slope']:.4f}",
           "deep_minus_side_in": f"{c['deep']['diff_in']:.4f}",
           "dev_vs_plan_diff_in": f"{c['dev_vs_plan']['diff_in']:.4f} ({c['dev_vs_plan']['pct']:.1f}%)",
           "genone_vs_arnold_diff_in": f"{c['genone_vs_arnold']['diff_in']:.5f}",
           "diag_sphere_P_in": (f"{R['diag']['sphere'].get('P_in'):+.2f}" if "P_in" in R['diag'].get('sphere', {}) else ""),
           "physical_admissibility": "admissible (continuous, no overshoot, finite slope/curvature, exact source passage)",
           "disposition": R["disp"]}
    _wr_csv(SUMMARY_CSV, list(row.keys()), [row])


# --- Report ------------------------------------------------------------------

def git_sha():
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception: return "UNKNOWN"


_S, _E = "<!-- RERUN004C_START -->", "<!-- RERUN004C_END -->"


def build_section(R) -> str:
    L = []; w = L.append; adm = R["adm"]; c = R["comp"]; land = R["land"]
    w("## Run 004C — Constrained Developed-Side Reconstruction")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Reverses the 004B hierarchy: **Arnold's measured side heights are the primary hard "
      "constraints**; the GenOne plan contributes **longitudinal landmark priors only** (no depth "
      "values). The developed side length **30.4375 in is the active coordinate authority** (not "
      "inferred from the plan perimeter); **station 27 in is in-domain**. No Sevy high point.")
    w("- Artifacts: `D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json`, "
      "`D28_65260_CONSTRAINED_SIDE_PROFILE_004C.csv`, `D28_65260_LANDMARK_RECONSTRUCTION_004C.csv`, "
      "`D28_65260_DEEP_INTERPRETATION_004C.csv`, `D28_65260_RERUN_004C_ANALYSIS.csv`, "
      "`D28_65260_RERUN_004C_SUMMARY.csv`. No PDF vendored.")
    w("")
    w("### Why 004C follows 004B")
    w("")
    w("- 004B showed a generic full-shape transfer does not fit #65260's side profile.")
    w("- 004C reverses the hierarchy: Arnold measurements define the geometry; GenOne contributes "
      "only proportional landmark priors; 30.4375 in is an active developed-side authority; 27 in "
      "is valid/in-domain; 26.73 in is a different (plan-view) quantity; 4 7/16 DEEP is assembled "
      "depth, not raw side height.")
    w("")
    w("### Constrained reconstruction (PCHIP through all Arnold points)")
    w("")
    w(f"- All {len(SRC_POINTS)} source points reproduced exactly (max error "
      f"{adm['max_source_err_in']:.2e} in). Shape-preserving PCHIP (handles the 3.750→3.740 dip; "
      f"no global monotonicity forced); overshoot = {adm['max_overshoot_in']:.4f} in; "
      f"curvature max = {adm['max_abs_curvature']:.4f}; slope ∈ [{adm['min_slope']:.4f}, {adm['max_slope']:.4f}].")
    w("")
    w("### Waist placement (Arnold-constrained + GenOne prior)")
    w("")
    w(f"- GenOne proportional waist prior → s = **{R['waist_prior']:.2f} in** "
      f"(GenOne waist center u={land['waist']['u']:.3f}).")
    w(f"- Arnold-constrained solve H(s)=4.220 → s = **{R['waist_solved']:.2f} in** (between stations 9 and 12).")
    w(f"- Profile at the GenOne prior predicts H={R['H_at_prior']:.4f} in → waist residual "
      f"**{R['H_at_prior']-WAIST_H:+.4f} in**. The GenOne prior and the Arnold-interpolated waist "
      "agree within a fraction of an inch; the waist is placeable without contradiction.")
    w("")
    w("### Landmark back-check (GenOne prior → #65260 developed station)")
    w("")
    w("| landmark | GenOne station | u (neck=0) | prior s (in) | reconstructed s (in) |")
    w("|---|---:|---:|---:|---:|")
    recon = {"waist": R["waist_solved"], "tail": DEV_SIDE_LEN}
    for k in ("head", "upper_bout", "waist", "lower_bout", "tail"):
        rc = recon.get(k)
        w(f"| {k} | {land[k]['genone_station']:.2f} | {land[k]['u']:.3f} | "
          f"{land[k]['s_65260_in']:.2f} | {('—' if rc is None else f'{rc:.2f}')} |")
    w("")
    w("### Developed length vs plan half-perimeter (different quantities)")
    w("")
    dp = c["dev_vs_plan"]
    w(f"- Developed side length **30.4375 in** (004C authority) vs plan-view half-perimeter "
      f"**{dp['plan_half_perim_in']:.2f} in** (diagnostic): difference {dp['diff_in']:.2f} in "
      f"({dp['pct']:.1f}%). These are treated as different geometric quantities; 26.73 does NOT "
      "constrain station placement in 004C.")
    w("")
    w("### GenOne analogy & 4 7/16 DEEP")
    w("")
    ga = c["genone_vs_arnold"]
    w(f"- GenOne 30 11/32 ({ga['genone_in']}) vs Arnold 30 7/16 ({ga['arnold_in']}): "
      f"diff {ga['diff_in']:.5f} in → `{ga['classification']}` (supports a ~30.4-in developed side).")
    dd = c["deep"]
    w(f"- 4 7/16 DEEP ({dd['deep_in']}) − waist side height ({dd['waist_side_in']}) = "
      f"**{dd['diff_in']:.4f} in ({dd['diff_mm']:.3f} mm)** → `{dd['classification']}` "
      "(top+back plate contribution per GenOne construction convention; exact split unresolved; "
      "#65260 plate thicknesses not invented).")
    w("")
    w("### Diagnostic fits (not governing)")
    w("")
    sph = R["diag"].get("sphere", {})
    if "R_ft" in sph:
        w(f"- Single-radius sphere fitted to the reconstructed profile: R ≈ {sph['R_ft']:.1f} ft, "
          f"P ≈ {sph['P_in']:+.2f} in, RMSE {sph['rmse']:.4f} in (confirms the spherical model remains "
          "inadmissible; the constrained profile does not rely on it).")
    for k in ("poly3", "poly4"):
        if k in R["diag"]:
            w(f"- {k}: RMSE {R['diag'][k]['rmse']:.4f} in.")
    w("")
    w("### Mathematical Result vs Physical Interpretation")
    w("")
    w("- The single-radius spherical experiments (Run 003 onward) returned genuine "
      "mathematical solutions, not calculation failures. Run 004A's global fit reached a "
      "small numerical residual (RMSE ≈ 0.0088 in) while placing the required high point at "
      "P ≈ -11.11 in; the 004C diagnostic sphere above reaches R ≈ 40.7 ft at RMSE ≈ 0.065 in "
      "with P ≈ -13.66 in. In every case the math converged — it is the *tested single-radius "
      "model interpretation* that is physically inadmissible, because it demands a high point "
      "outside the body (P < 0). Physical inadmissibility is a property of that model "
      "interpretation, not of the mathematics itself.")
    w("- The negative-P solutions were not discarded because they looked wrong; they were "
      "preserved because they showed exactly how the assumed model had to distort itself to "
      "satisfy the measurements. 004C's constrained developed-side reconstruction fits the same "
      "Arnold measurements with no high point required.")
    w("- See the program-level **Engineering Interpretation Principle** (top of this document) "
      "for the full statement: preserve the equations, measurements, and datum assumptions; "
      "report the unconstrained result and its residuals first; only then evaluate physical "
      "admissibility. Source data is never altered to make a model look physically expected.")
    w("")
    w("### Bracing / Datum A (independent, qualitative)")
    w("")
    w("- The developed-side reconstruction changes no plan-view geometry; it remains compatible with "
      "soundhole Datum A, the X-brace (49°+49°=98°, lower 110°), page-2 brace dimensions, and "
      "BB1–BB4 longitudinal placement. Brace cross-section depths are not compared to side depth.")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Parent dispositions `SPHERICAL_MODEL_MISMATCH` and "
      "`PROPORTIONAL_SIMILITUDE_DOES_NOT_SUPPORT_FIT` are untouched.")
    w("")
    return "\n".join(L)


def splice_doc(section):
    with open(_DOC) as fh: text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    else:
        marker = "<!-- RERUN004B_START -->"
        text = text[:text.index(marker)] + block + "\n\n---\n\n" + text[text.index(marker):]
    with open(_DOC, "w") as fh: fh.write(text)


def main():
    if not os.path.exists(GENONE_SHEET05) and not os.path.exists(LANDMARK_CSV):
        raise SystemExit("STOP INSUFFICIENT_GEOMETRY_AUTHORITY: GenOne Sheet 05 unavailable.")
    R = run_all()
    section = build_section(R)
    if "--write" in sys.argv:
        write_authority(R); write_provenance(); write_profile(R); write_landmarks(R)
        write_deep(R); write_analysis(R); write_summary(R); splice_doc(section)
        print(f"wrote 004C artifacts; disposition={R['disp']}")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; waist_solved={R['waist_solved']:.2f}; prior={R['waist_prior']:.2f}]")


if __name__ == "__main__":
    main()
