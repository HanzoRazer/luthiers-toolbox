#!/usr/bin/env python3
"""
D28 SIDE SOURCE AUTHORITY CLEANUP 004A
======================================

Corrects the experimental SOURCE model before the proportional-similitude study
(004B). Separates John Arnold's original numeric-station side-height
measurements (0,3,...,27) from later/inferred station assignments (10.5, 30.4375)
and re-runs the Rerun 003 inverse diagnostics using ONLY source-supported numeric
stations. Waist (4.220) and bottom (4.720) are retained as measured heights but
evaluated at GEOMETRIC positions (min-width point / tail), not numeric stations.

Reuses the Rerun 003 Arnold/JD traced outline and the production Sevy/Doolin
equations unchanged. Does NOT retrace the outline, does NOT alter any historical
measurement, does NOT use the 30.4375 normalized mapping (kept as 003A evidence),
and modifies no production/spec/authority file. Neither PDF is vendored. Runs
001/002/003/003A result files are untouched.

This run is NOT the proportional reconstruction (that is 004B).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import brentq, least_squares

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r3 = _load("r3_004a", "d28_side_inverse_rerun003.py")

# === CORRECTED SOURCE AUTHORITY (per the 004A order) =========================
# Original Arnold numeric-station measurements (side heights, exclude top/back):
STATIONED = {0.0: 3.750, 3.0: 3.740, 6.0: 3.895, 9.0: 4.085, 12.0: 4.240,
             15.0: 4.350, 18.0: 4.455, 21.0: 4.565, 24.0: 4.640, 27.0: 4.670}
ACTIVE_STATIONS = sorted(STATIONED)                       # 0..27 (NO 10.5, NO 30.4375)
# Named, unstationed measurements (heights only; positions are GEOMETRIC):
WAIST_HEIGHT = 4.220        # evaluated at the geometric minimum-width point
BOTTOM_HEIGHT = 4.720       # evaluated at the geometric tail endpoint
# Legacy/later assignments preserved as evidence only (NOT active):
LEGACY_WAIST_STATION = 10.5         # LEGACY_REPO_ASSIGNMENT
LEGACY_BOTTOM_STATION = 30.4375     # LEGACY_REPO_ASSIGNMENT / SUBSEQUENT_SOURCE
DRAWING_DEEP = 4.4375               # comparison only

ANCHORS = {9.0: 4.085, 12.0: 4.240, 15.0: 4.350}
S_NECK_STATION = 0.0
S_SHOULDER = STATIONED[S_NECK_STATION]     # 3.750 -> S (neck boundary)
B_BUTT = BOTTOM_HEIGHT                       # 4.720 -> B (bottom @ geometric tail)
L_CAL = r3._L_CAL
R_MIN, R_MAX = r3.R_MIN_IN, r3.R_MAX_IN
L_MIN, L_MAX = r3.L_MIN_IN, r3.L_MAX_IN
_GW = r3.geometric_waist(L_CAL)
S_CAD_TOTAL = _GW["half_perimeter"]         # 26.73 in plan-view half-perimeter

AUTH_JSON = os.path.join(_RESULTS, "D28_65260_SIDE_HEIGHT_AUTHORITY_004A.json")
CROSSWALK_CSV = os.path.join(_RESULTS, "D28_65260_SOURCE_AUTHORITY_CROSSWALK_004A.csv")
CONV_CSV = os.path.join(_RESULTS, "D28_65260_SIDE_AUTHORITY_004A_CONVERGENCE.csv")
SUM_CSV = os.path.join(_RESULTS, "D28_65260_SIDE_AUTHORITY_004A_SUMMARY.csv")
_DOC = os.path.join(_REPO_ROOT, "docs", "experiments", "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")


def in_domain(station: float) -> bool:
    return station <= S_CAD_TOTAL + 1e-9


# --- Literal plan-view developed-arc mapping (Rerun 003 convention) ----------

def map_station(L: float, station: float) -> Tuple[float, float, str]:
    y, x, s = r3.developed_arclen(L)
    Stot = float(s[-1])
    status = "OK" if station <= Stot + 1e-9 else "OUT_OF_DOMAIN"
    s_used = min(station, Stot)
    return float(np.interp(s_used, s, x)), float(np.interp(s_used, s, y)), status


def predict_station(L: float, R: float, station: float) -> Tuple[float, float, str]:
    P = r3.solve_high_point(L, B_BUTT, S_SHOULDER, R)
    x, y, status = map_station(L, station)
    D = math.hypot(x, y - (L - P))
    return r3.solve_side_height(B_BUTT, R, P, D, 0.0, 0.0), D, status


def predict_waist(L: float, R: float) -> Tuple[float, float]:
    gw = r3.geometric_waist(L)
    P = r3.solve_high_point(L, B_BUTT, S_SHOULDER, R)
    D = math.hypot(gw["x"], gw["y"] - (L - P))
    return r3.solve_side_height(B_BUTT, R, P, D, 0.0, 0.0), P


def predict_bottom(L: float, R: float) -> float:
    """Bottom = geometric tail endpoint (last outline point)."""
    y, x, s = r3.developed_arclen(L)
    P = r3.solve_high_point(L, B_BUTT, S_SHOULDER, R)
    xt, yt = float(x[-1]), float(y[-1])
    D = math.hypot(xt, yt - (L - P))
    return r3.solve_side_height(B_BUTT, R, P, D, 0.0, 0.0)


def admissible(L: float, R: float) -> bool:
    P = r3.solve_high_point(L, B_BUTT, S_SHOULDER, R)
    return (0.0 <= P <= L) and (abs(P) < R)


def _bound(R, L):
    return (abs(R - R_MIN) < 1e-6 or abs(R - R_MAX) < 1e-6
            or abs(L - L_MIN) < 1e-3 or abs(L - L_MAX) < 1e-3)


# Residual set: in-domain interior numeric stations (exclude neck boundary,
# the anchor, and OUT_OF_DOMAIN stations).
def residual_stations(anchor: Optional[float]) -> List[float]:
    return [s for s in ACTIVE_STATIONS
            if s != S_NECK_STATION and s != anchor and in_domain(s)]


# --- Convergence logger ------------------------------------------------------

CSV_FIELDS = ["run_id", "analysis", "anchor_station_in", "anchor_height_in",
              "outer_iteration", "inner_iteration", "body_length_in", "radius_in",
              "radius_ft", "high_point_P_in", "predicted_anchor_height_in",
              "anchor_residual_in", "numeric_series_rmse_in",
              "numeric_series_max_abs_resid_in", "predicted_waist_height_in",
              "waist_residual_in", "predicted_bottom_height_in", "bottom_residual_in",
              "solver_method", "physically_admissible", "bound_hit", "convergence_status"]


class Logger:
    def __init__(self): self.rows: List[dict] = []
    def add(self, **kw): self.rows.append({f: kw.get(f, "") for f in CSV_FIELDS})
    def write(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
            w.writeheader(); w.writerows(self.rows)


def _f(v, n=4):
    return "" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else str(v))


# --- Anchor-constrained inverse (sweep R, solve L; matches Rerun 003) --------

def solve_L(R: float, anchor: float, target: float) -> Optional[float]:
    def g(L): return predict_station(L, R, anchor)[0] - target
    grid = np.linspace(L_MIN, L_MAX, 71)
    gv = []
    for L in grid:
        try: gv.append(g(float(L)))
        except (ValueError, ZeroDivisionError): gv.append(math.nan)
    roots = []
    for i in range(len(grid) - 1):
        a, b = gv[i], gv[i + 1]
        if math.isnan(a) or math.isnan(b): continue
        if a * b < 0:
            try: roots.append(float(brentq(g, float(grid[i]), float(grid[i + 1]), xtol=1e-8)))
            except (ValueError, RuntimeError): pass
    if not roots: return None
    adm = [L for L in roots if 0 <= r3.solve_high_point(L, B_BUTT, S_SHOULDER, R) <= L]
    return min(adm or roots, key=lambda L: abs(L - 20.0))


def inverse(logger: Logger, anchor: float) -> Dict:
    target = ANCHORS[anchor]
    rstations = residual_stations(anchor)
    best = None
    prevL = prevR = None
    for oi, R in enumerate(np.linspace(R_MIN, R_MAX, 43)):
        R = float(R)
        L = solve_L(R, anchor, target)
        if L is None:
            logger.add(run_id=f"A_a{anchor}_R{oi:03d}", analysis="anchor",
                       anchor_station_in=_f(anchor), anchor_height_in=_f(target),
                       outer_iteration=oi, radius_in=_f(R, 3), radius_ft=_f(R / 12, 4),
                       solver_method="bisection", convergence_status="no_root")
            prevR = R; continue
        res = {s: predict_station(L, R, s)[0] - STATIONED[s] for s in rstations}
        e = float(np.sqrt(np.mean(np.array(list(res.values())) ** 2)))
        mx = max(abs(v) for v in res.values())
        wp, P = predict_waist(L, R); bp = predict_bottom(L, R)
        pa = predict_station(L, R, anchor)[0]
        logger.add(run_id=f"A_a{anchor}_R{oi:03d}", analysis="anchor",
                   anchor_station_in=_f(anchor), anchor_height_in=_f(target),
                   outer_iteration=oi, inner_iteration="final", body_length_in=_f(L, 4),
                   radius_in=_f(R, 3), radius_ft=_f(R / 12, 4), high_point_P_in=_f(P, 4),
                   predicted_anchor_height_in=_f(pa, 5), anchor_residual_in=_f(pa - target, 6),
                   numeric_series_rmse_in=_f(e, 6), numeric_series_max_abs_resid_in=_f(mx, 6),
                   predicted_waist_height_in=_f(wp, 4), waist_residual_in=_f(wp - WAIST_HEIGHT, 5),
                   predicted_bottom_height_in=_f(bp, 4), bottom_residual_in=_f(bp - BOTTOM_HEIGHT, 5),
                   solver_method="bisection", physically_admissible=admissible(L, R),
                   bound_hit=_bound(R, L), convergence_status="solved")
        if best is None or e < best["rmse"]:
            wp2, _ = predict_waist(L, R)
            best = {"anchor": anchor, "L": L, "R": R, "P": P, "rmse": e, "maxabs": mx,
                    "waist_pred": wp2, "waist_resid": wp2 - WAIST_HEIGHT,
                    "bottom_pred": bp, "bottom_resid": bp - BOTTOM_HEIGHT,
                    "admissible": admissible(L, R), "bound": _bound(R, L)}
        prevL, prevR = L, R
    return best or {"anchor": anchor, "L": None, "R": None, "P": None, "rmse": None,
                    "maxabs": None, "waist_pred": None, "waist_resid": None,
                    "bottom_pred": None, "bottom_resid": None, "admissible": None, "bound": None}


def global_ls(logger: Logger) -> Dict:
    rstations = [s for s in ACTIVE_STATIONS if in_domain(s)]     # includes neck + all in-domain
    cnt = {"n": 0}

    def resid(p):
        L, R = float(p[0]), float(p[1])
        out = []
        for s in rstations:
            try: H = predict_station(L, R, s)[0]
            except (ValueError, ZeroDivisionError): H = 1e3
            out.append(H - STATIONED[s])
        arr = np.array(out)
        wp, P = predict_waist(L, R); bp = predict_bottom(L, R)
        logger.add(run_id="GLOBAL_LS", analysis="least_squares", outer_iteration=0,
                   inner_iteration=cnt["n"], body_length_in=_f(L, 4), radius_in=_f(R, 3),
                   radius_ft=_f(R / 12, 4), high_point_P_in=_f(P, 4),
                   numeric_series_rmse_in=_f(float(np.sqrt(np.mean(arr ** 2))), 6),
                   predicted_waist_height_in=_f(wp, 4), waist_residual_in=_f(wp - WAIST_HEIGHT, 5),
                   predicted_bottom_height_in=_f(bp, 4), bottom_residual_in=_f(bp - BOTTOM_HEIGHT, 5),
                   solver_method="least_squares", physically_admissible=admissible(L, R),
                   bound_hit=_bound(R, L), convergence_status="iterating")
        cnt["n"] += 1
        return arr

    sol = least_squares(resid, x0=[20.0, 180.0], bounds=([L_MIN, R_MIN], [L_MAX, R_MAX]))
    L, R = float(sol.x[0]), float(sol.x[1])
    P = r3.solve_high_point(L, B_BUTT, S_SHOULDER, R)
    res = {s: predict_station(L, R, s)[0] - STATIONED[s] for s in rstations}
    wp, _ = predict_waist(L, R); bp = predict_bottom(L, R)
    return {"L": L, "R": R, "P": P, "rmse": float(np.sqrt(np.mean(sol.fun ** 2))),
            "maxabs": max(abs(v) for v in res.values()), "waist_pred": wp,
            "waist_resid": wp - WAIST_HEIGHT, "bottom_pred": bp, "bottom_resid": bp - BOTTOM_HEIGHT,
            "admissible": admissible(L, R), "bound": _bound(R, L)}


# --- Conclusion --------------------------------------------------------------

def conclude(anch: Dict[float, Dict], gls: Dict) -> Tuple[str, bool, List[str]]:
    notes = []
    ok = [d for d in anch.values() if d["L"] is not None]
    adm = [d for d in ok if d["admissible"] and not d["bound"]]
    Ls = [d["L"] for d in ok]
    clustered = bool(Ls) and (max(Ls) - min(Ls) < 2.0)
    if adm and clustered and (gls["admissible"] and not gls["bound"]):
        notes.append("Cleaned source now yields admissible, clustered, non-bound fits.")
        return "LEGACY_STATION_ASSIGNMENTS_CAUSED_PRIOR_FAILURE", False, notes
    if not ok or (not adm and all((d["P"] is not None and d["P"] < 0) for d in ok)):
        notes.append("Every anchor fit on the cleaned source still requires P<0 "
                     f"(anchors L~{min(Ls):.1f}-{max(Ls):.1f} in, all inadmissible); "
                     "global LS P<0 as well. Removing 10.5/30.4375 did not change this.")
        notes.append("Station 27 in is OUT_OF_DOMAIN (27 > plan half-perimeter 26.73 in); "
                     "the developed-length shortfall persists independent of the legacy stations.")
        return "SINGLE_RADIUS_MODEL_MISMATCH_PERSISTS", True, notes
    notes.append("Mixed/ambiguous admissibility across anchors.")
    return "SOURCE_CLEANUP_INCONCLUSIVE", False, notes


# --- Source authority record + crosswalk -------------------------------------

def write_authority_json():
    rec = {
        "experiment": "D28_SIDE_SOURCE_AUTHORITY_CLEANUP_004A",
        "note": "Corrected experimental source model. Numeric heights are Arnold "
                "SOURCE_MEASURED; 10.5/30.4375 station assignments are legacy/later "
                "and excluded from the active solve. No production spec is modified.",
        "stationed_measurements": [{"station_in": s, "height_in": STATIONED[s]}
                                   for s in ACTIVE_STATIONS],
        "named_unstationed_measurements": {
            "waist": {"height_in": WAIST_HEIGHT, "position": "geometric minimum-width point",
                      "classification": "SOURCE_MEASURED"},
            "bottom": {"height_in": BOTTOM_HEIGHT, "position": "geometric tail endpoint",
                       "classification": "SOURCE_MEASURED"}},
        "legacy_repo_assignments": {
            "waist_station_in": {"value": LEGACY_WAIST_STATION, "classification": "LEGACY_REPO_ASSIGNMENT",
                                 "active_in_004A": False},
            "bottom_station_in": {"value": LEGACY_BOTTOM_STATION,
                                  "classification": "LEGACY_REPO_ASSIGNMENT / SUBSEQUENT_SOURCE",
                                  "active_in_004A": False}},
        "unresolved_relationships": [
            "physical measuring-path convention behind any developed span (see Rerun 003A)",
            "relation of 10.5/30.4375 to the original numeric series"],
        "excluded_from_active_solve": [LEGACY_WAIST_STATION, LEGACY_BOTTOM_STATION],
        "normalized_30p4375_mapping_used": False,
    }
    os.makedirs(_RESULTS, exist_ok=True)
    with open(AUTH_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


def write_crosswalk():
    rows = []
    for s in ACTIVE_STATIONS:
        rows.append({"quantity": f"side height @ station {s}", "value": STATIONED[s], "unit": "in",
                     "current_repo_representation": f"side_profile_raw[{s}]", "original_source_support": "yes",
                     "later_source_support": "-", "classification": "SOURCE_MEASURED",
                     "active_in_004A": "yes", "notes": "Arnold numeric station"})
    rows += [
        {"quantity": "waist side height", "value": WAIST_HEIGHT, "unit": "in",
         "current_repo_representation": "side_profile_raw[10.5]", "original_source_support": "yes (height)",
         "later_source_support": "-", "classification": "SOURCE_MEASURED",
         "active_in_004A": "validation@geometric waist", "notes": "no source numeric station"},
        {"quantity": "bottom side height", "value": BOTTOM_HEIGHT, "unit": "in",
         "current_repo_representation": "side_profile_raw[30.4375]", "original_source_support": "yes (height)",
         "later_source_support": "-", "classification": "SOURCE_MEASURED",
         "active_in_004A": "validation@geometric tail / B boundary", "notes": "no source numeric station"},
        {"quantity": "waist station 10.5", "value": LEGACY_WAIST_STATION, "unit": "in",
         "current_repo_representation": "key in side_profile_raw", "original_source_support": "no",
         "later_source_support": "repo", "classification": "LEGACY_REPO_ASSIGNMENT",
         "active_in_004A": "no", "notes": "excluded from active solve"},
        {"quantity": "bottom station 30.4375", "value": LEGACY_BOTTOM_STATION, "unit": "in",
         "current_repo_representation": "key + total_length", "original_source_support": "no",
         "later_source_support": "repo/subsequent", "classification": "LEGACY_REPO_ASSIGNMENT / SUBSEQUENT_SOURCE",
         "active_in_004A": "no", "notes": "not used as span/normalization"},
        {"quantity": "body length", "value": 20.0, "unit": "in",
         "current_repo_representation": "dimensions.body_length", "original_source_support": "drawing",
         "later_source_support": "-", "classification": "DRAWING_DERIVED", "active_in_004A": "A1 fixed L",
         "notes": "CAD-labelled"},
        {"quantity": "CAD-traced waist position", "value": round(_GW["s_waist"], 3), "unit": "in (developed)",
         "current_repo_representation": "-", "original_source_support": "-", "later_source_support": "-",
         "classification": "VERIFIED_TRACED_RECONSTRUCTION / CALCULATED", "active_in_004A": "yes",
         "notes": "geometric min-width; y/L=%.3f" % _GW["y_norm"]},
        {"quantity": "CAD-traced plan half-perimeter", "value": round(S_CAD_TOTAL, 3), "unit": "in",
         "current_repo_representation": "-", "original_source_support": "-", "later_source_support": "-",
         "classification": "VERIFIED_TRACED_RECONSTRUCTION / CALCULATED", "active_in_004A": "yes",
         "notes": "station 27 exceeds this -> OUT_OF_DOMAIN"},
        {"quantity": "4.4375 DEEP", "value": DRAWING_DEEP, "unit": "in",
         "current_repo_representation": "notes", "original_source_support": "drawing annotation",
         "later_source_support": "-", "classification": "DRAWING_DERIVED",
         "active_in_004A": "comparison only", "notes": "assembled depth, not side height"},
    ]
    fields = ["quantity", "value", "unit", "current_repo_representation", "original_source_support",
              "later_source_support", "classification", "active_in_004A", "notes"]
    with open(CROSSWALK_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def write_summary(anch, gls, conclusion, authorize_004b):
    def a(x): return anch.get(x, {})
    row = {
        "active_numeric_stations": " ".join(str(int(s)) for s in ACTIVE_STATIONS),
        "excluded_legacy_stations": f"{LEGACY_WAIST_STATION} {LEGACY_BOTTOM_STATION}",
        "geometric_waist_station_in": f"{_GW['s_waist']:.3f}",
        "geometric_tail_location_in": f"{L_CAL:.3f}",
        "anchor9_L_R_P_RMSE": _fmt_anchor(a(9.0)),
        "anchor12_L_R_P_RMSE": _fmt_anchor(a(12.0)),
        "anchor15_L_R_P_RMSE": _fmt_anchor(a(15.0)),
        "global_ls_L_R_P_RMSE": (f"L={gls['L']:.2f} R={gls['R']/12:.2f}ft P={gls['P']:+.2f} "
                                 f"RMSE={gls['rmse']:.4f}"),
        "best_L_in": _f(a(12.0).get("L"), 2), "best_R_ft": (f"{a(12.0)['R']/12:.2f}" if a(12.0).get("R") else ""),
        "P_in": _f(a(12.0).get("P"), 2), "numeric_rmse_in": _f(a(12.0).get("rmse"), 4),
        "max_residual_in": _f(a(12.0).get("maxabs"), 4),
        "waist_prediction_in": _f(a(12.0).get("waist_pred"), 4), "waist_residual_in": _f(a(12.0).get("waist_resid"), 4),
        "bottom_prediction_in": _f(a(12.0).get("bottom_pred"), 4), "bottom_residual_in": _f(a(12.0).get("bottom_resid"), 4),
        "physical_admissibility": a(12.0).get("admissible"),
        "anchor_clustering": _clustering(anch), "identifiability": _clustering(anch),
        "conclusion": conclusion, "run_004b_authorized": authorize_004b,
    }
    with open(SUM_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row.keys()), lineterminator="\n")
        w.writeheader(); w.writerow(row)


def _fmt_anchor(d):
    if not d or d.get("L") is None: return "no root"
    return f"L={d['L']:.2f} R={d['R']/12:.2f}ft P={d['P']:+.2f} RMSE={d['rmse']:.4f} adm={d['admissible']}"


def _clustering(anch):
    Ls = [d["L"] for d in anch.values() if d.get("L") is not None]
    if not Ls: return "no solutions"
    return (f"clustered (L {min(Ls):.2f}-{max(Ls):.2f})" if max(Ls) - min(Ls) < 2.0
            else f"non-clustering (L {min(Ls):.2f}-{max(Ls):.2f})")


# --- Report ------------------------------------------------------------------

def git_sha():
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception: return "UNKNOWN"


_S, _E = "<!-- RERUN004A_START -->", "<!-- RERUN004A_END -->"


def build_section(anch, gls, conclusion, authorize_004b, notes) -> str:
    L = []; w = L.append
    w("## Run 004A — Original Side-Measurement Authority Cleanup")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Corrects the experimental source model before the 004B similitude study. Reuses the "
      "Rerun 003 Arnold/JD traced outline and Sevy/Doolin equations unchanged; no historical "
      "value, outline, or production/spec/authority file is modified; neither PDF is vendored.")
    w("- Artifacts: `D28_65260_SIDE_HEIGHT_AUTHORITY_004A.json`, "
      "`D28_65260_SOURCE_AUTHORITY_CROSSWALK_004A.csv`, "
      "`D28_65260_SIDE_AUTHORITY_004A_CONVERGENCE.csv`, `D28_65260_SIDE_AUTHORITY_004A_SUMMARY.csv`.")
    w("")
    w("### Source correction")
    w("")
    w("1. The production repo representation conflates measured heights with inferred station "
      "coordinates: waist 4.220 in with station **10.5 in**, and bottom 4.720 in with station "
      "**30.4375 in**.")
    w("2. Arnold's original numeric-station series establishes only the stations "
      "**0,3,6,9,12,15,18,21,24,27** (heights unchanged).")
    w("3. The numeric heights themselves remain valid (`SOURCE_MEASURED`).")
    w("4. **10.5 and 30.4375 are preserved as `LEGACY_REPO_ASSIGNMENT` evidence but excluded "
      "from the active 004A solve** (no 30.4375 span, no normalization, no 10.5 waist station).")
    w("5. Waist (4.220) and bottom (4.720) are now **geometric validation points** — waist at the "
      "minimum-width point, bottom at the tail endpoint.")
    w("")
    w("### Active mapping (literal plan-view developed arc; no clamping)")
    w("")
    w("| Arnold station (in) | in-domain? | status |")
    w("|---:|:--:|---|")
    for s in ACTIVE_STATIONS:
        w(f"| {s:.0f} | {in_domain(s)} | {'OK' if in_domain(s) else 'OUT_OF_DOMAIN'} |")
    w("")
    w(f"- Plan-view half-perimeter = {S_CAD_TOTAL:.3f} in; **station 27 in is OUT_OF_DOMAIN** "
      "(27 > 26.73), reported not clamped. Stations 0–24 map normally.")
    w(f"- Geometric waist developed station = {_GW['s_waist']:.3f} in (y/L={_GW['y_norm']:.3f}); "
      f"geometric tail at y={L_CAL:.2f} in.")
    w("")
    w("### Multi-anchor inverse (source-supported anchors 9 / 12 / 15 only)")
    w("")
    w("| anchor (in→in) | L (in) | R (ft) | P (in) | numeric RMSE | max resid | waist resid | bottom resid | admissible | bound |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|")
    for a in (9.0, 12.0, 15.0):
        d = anch[a]
        if d["L"] is None:
            w(f"| {a}→{ANCHORS[a]} | no root | | | | | | | | |")
        else:
            w(f"| {a}→{ANCHORS[a]} | {d['L']:.2f} | {d['R']/12:.2f} | {d['P']:+.2f} | {d['rmse']:.4f} "
              f"| {d['maxabs']:.4f} | {d['waist_resid']:+.4f} | {d['bottom_resid']:+.4f} | "
              f"{d['admissible']} | {d['bound']} |")
    w("")
    w("### Global least-squares (numeric stations 0–24 in-domain)")
    w("")
    w(f"- L = {gls['L']:.2f} in, R = {gls['R']/12:.2f} ft, P = {gls['P']:+.2f} in, "
      f"numeric RMSE = {gls['rmse']:.4f} in, max resid = {gls['maxabs']:.4f} in; "
      f"waist resid = {gls['waist_resid']:+.4f} in, bottom resid = {gls['bottom_resid']:+.4f} in; "
      f"admissible = {gls['admissible']}, bound = {gls['bound']}.")
    w("")
    w("### Comparison — Rerun 003 / 003A / Run 004A")
    w("")
    w("| aspect | Rerun 003 | Rerun 003A | Run 004A |")
    w("|---|---|---|---|")
    w("| active station count | 11 (0..30.4375) | 11 (+normalized test) | 10 (0..27) |")
    w("| 10.5 active | no (geometric waist) | no | no |")
    w("| 30.4375 active | yes (B boundary/clamp) | yes (normalized endpoint) | **no** |")
    w("| waist treatment | geometric | geometric | geometric validation |")
    w("| bottom treatment | station 30.4375 (B) | station 30.4375 | **geometric tail (B)** |")
    a12 = anch[12.0]
    w(f"| best L (anchor 12) | ~21.9 in | ~22.0 / ~12 (norm) | {a12['L']:.2f} in |" if a12['L'] else "| best L | ~21.9 | | no root |")
    w(f"| best R (anchor 12) | ~35 ft | ~34 / ~9 (norm) | {a12['R']/12:.2f} ft |" if a12['R'] else "| best R | | | |")
    w(f"| P (anchor 12) | <0 | <0 | {a12['P']:+.2f} in |" if a12['P'] is not None else "| P | <0 | <0 | |")
    w("| physical admissibility | inadmissible (P<0) | inadmissible (P<0) | "
      f"{'inadmissible (P<0)' if (a12['P'] is not None and a12['P']<0) else a12['admissible']} |")
    w("| disposition | SPHERICAL_MODEL_MISMATCH | STRENGTHENED | see conclusion |")
    w("")
    w("### Run 004A conclusion")
    w("")
    w(f"**`{conclusion}`**")
    w("")
    for n in notes:
        w(f"- {n}")
    w("")
    w("Note: the Rerun 003A normalized-30.4375 mapping is **not** used in the active 004A solve "
      "(the source does not establish 30.4375 as a terminal station); it is retained only as "
      "historical robustness evidence.")
    w("")
    w("### Next-step gate")
    w("")
    if authorize_004b:
        w("- Run 004A shows the single-radius spherical mismatch persists after source cleanup, so "
          "**RUN 004B — PROPORTIONAL DREADNOUGHT SIMILITUDE is AUTHORIZED** as the next experiment "
          "(not implemented here). 004B will normalize the generic dreadnought plan's body/side "
          "relationships, scale them onto the verified #65260 geometry, validate against the cleaned "
          "Arnold side-height dataset, and back-check against the measured #65260 bracing layout.")
    else:
        w("- Run 004B is not authorized by this result (cleanup changed the conclusion).")
    w("")
    w("### Classification ledger")
    w("")
    w("- `SOURCE_MEASURED`: Arnold numeric heights 0–27; waist 4.220; bottom 4.720.")
    w("- `LEGACY_REPO_ASSIGNMENT`: waist station 10.5; bottom station 30.4375 (excluded from solve).")
    w("- `CALCULATED`: geometric waist station, half-perimeter, inverse (L,R,P).")
    w("- `UNRESOLVED`: relation of 10.5/30.4375 to the original series; developed-span convention.")
    w("")
    return "\n".join(L)


def splice_doc(section):
    with open(_DOC) as fh: text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    else:
        marker = "<!-- RERUN003A_START -->"
        text = text[:text.index(marker)] + block + "\n\n---\n\n" + text[text.index(marker):]
    with open(_DOC, "w") as fh: fh.write(text)


def run_all():
    logger = Logger()
    anch = {a: inverse(logger, a) for a in ANCHORS}
    gls = global_ls(logger)
    conclusion, authorize_004b, notes = conclude(anch, gls)
    return logger, anch, gls, conclusion, authorize_004b, notes


def main():
    logger, anch, gls, conclusion, authorize, notes = run_all()
    section = build_section(anch, gls, conclusion, authorize, notes)
    if "--write" in sys.argv:
        write_authority_json(); write_crosswalk()
        logger.write(CONV_CSV); write_summary(anch, gls, conclusion, authorize)
        splice_doc(section)
        print(f"wrote {AUTH_JSON}\nwrote {CROSSWALK_CSV}")
        print(f"wrote {CONV_CSV} ({len(logger.rows)} rows)\nwrote {SUM_CSV}")
        print(f"spliced Run 004A into {_DOC}")
    else:
        print(section)
        print(f"\n[conclusion={conclusion}; 004B authorized={authorize}]")


if __name__ == "__main__":
    main()
