#!/usr/bin/env python3
"""
The Reverse Engineering of the Martin D-28 #65260 — Corrected Rerun 002
=======================================================================

Isolated mathematical experiment (branch experiment/d28-side-profile-inverse-
convergence). Evidence gathering ONLY — it reuses the production Sevy/Doolin
equations and the repository body-outline authority unchanged and modifies no
production, spec, or authority file.

What Rerun 002 corrects (see docs/experiments/D28_SIDE_INVERSE_RERUN_002.md)
---------------------------------------------------------------------------
* The hard waist constraint is the John Arnold **side height 4.220 in**, not the
  drawing "DEEP" annotation 4.4375 in. 4.4375 in is a separate assembled-body
  depth measurement, used here for comparison only — never as side height.
* The waist station is **not** assumed to be 10.5 in. The geometric waist point
  is found on the D-28 plan-view outline and its developed neck-to-waist side
  arc length ``s_waist`` is derived and reported (and compared to the legacy
  10.5 in assumption).
* Stations map to perimeter points by **developed (absolute) side arc length**;
  ``D`` is the Euclidean in-plane distance from the spherical high point to the
  mapped point — never the developed station itself.

Experimental-authority rule
---------------------------
Only the values declared in the input block below govern the solve. Repository
values are read only for outline mapping/interpretation, provenance, comparison,
validation, and inconsistency detection — never silently substituted for a
declared experimental value. A missing declared value stops the run.

Even a clean convergence near 20 in would NOT license editing the historical
spec; any production/authority change needs a separate owner-reviewed order.
"""
from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import least_squares

# --- Reuse the production equations and outline authority (read-only) --------
_API = os.path.join(os.path.dirname(__file__), "..", "..", "services", "api")
sys.path.insert(0, os.path.abspath(_API))
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.instrument_geometry.body.ibg.body_contour_solver import (  # noqa: E402
    BodyConstraints,
    BodyContourSolver,
    solve_high_point,
    solve_side_height,
)

# --- Repository spec (read-only; JSON is the intact copy) --------------------
_SPEC_JSON = os.path.join(_API, "app", "instrument_geometry", "specs",
                          "martin_d28_1937.json")
with open(_SPEC_JSON) as _fh:
    _SPEC = json.load(_fh)

# === EXPERIMENTAL AUTHORITY — declared inputs that GOVERN the solve ==========
# Direct John Arnold correspondence: side-height observations (exclude top/back).
# The waist (4.220) has NO source-declared numeric station; it is applied at the
# geometrically derived waist location. So the numeric station list omits it.
ARNOLD_SIDE_HEIGHT_IN: Dict[float, float] = {
    0.0: 3.750,
    3.0: 3.740,
    6.0: 3.895,
    9.0: 4.085,
    12.0: 4.240,
    15.0: 4.350,
    18.0: 4.455,
    21.0: 4.565,
    24.0: 4.640,
    27.0: 4.670,
    30.4375: 4.720,
}
STATIONS = sorted(ARNOLD_SIDE_HEIGHT_IN)
S_NECK_STATION = STATIONS[0]        # 0.0
S_TAIL_STATION = STATIONS[-1]       # 30.4375 (Arnold "bottom end")
S_SHOULDER = ARNOLD_SIDE_HEIGHT_IN[S_NECK_STATION]   # 3.750 -> S
B_BUTT = ARNOLD_SIDE_HEIGHT_IN[S_TAIL_STATION]       # 4.720 -> B
M = N = 0.0                                          # raw side height excludes plate

WAIST_SIDE_HEIGHT = 4.220           # HARD constraint (Arnold side height)
DRAWING_DEEP = 4.4375               # separate "DEEP" drawing depth; COMPARISON ONLY
DRAWING_MINUS_SIDE = DRAWING_DEEP - WAIST_SIDE_HEIGHT   # 0.2175 in

# Interior validation points (residuals): numeric stations excluding the two
# endpoints (which are the B/S boundary conditions). The waist is a separate
# hard constraint at the derived station, so it is not in this list.
VALIDATION_STATIONS = [s for s in STATIONS if s not in (S_NECK_STATION, S_TAIL_STATION)]

# Sweep/solve bounds (broad; not narrowed to force a historical result).
R_MIN_IN, R_MAX_IN = 8.0 * 12.0, 50.0 * 12.0    # 96 .. 600 in
L_MIN_IN, L_MAX_IN = 12.0, 40.0

# Repository geometry read ONLY to map developed stations to perimeter points.
LOWER_BOUT = float(_SPEC["dimensions"]["lower_bout_width"])
UPPER_BOUT = float(_SPEC["dimensions"]["upper_bout_width"])
WAIST_W = float(_SPEC["dimensions"]["waist_width"])
WAIST_Y_NORM = 0.44                              # BodyContourSolver dreadnought default
BODY_LENGTH_SPEC = float(_SPEC["dimensions"]["body_length"])     # 20.0 (datum under test)
TOTAL_LENGTH_SPEC = float(_SPEC["dimensions"]["total_length"])   # 30.4375

# First-run (SUPERSEDED) headline results, for the run1-vs-run2 comparison.
LEGACY_WAIST_STATION = 10.5
FIRST_RUN = {
    "waist_side_height_in": 4.4375,   # WRONG: used the DEEP value as side height
    "waist_station_in": 10.5,         # assumed, not derived
    "R_star_ft": 8.0,                 # on lower bound
    "L_star_in": 20.29,
    "P_star_in": 5.59,
    "validation_rmse_in": 0.1897,
    "disposition": "UNDERDETERMINED",
}

EXPERIMENTAL_INPUTS = {
    "waist_side_height_in": WAIST_SIDE_HEIGHT,
    "waist_station": "GEOMETRICALLY DERIVED (not assumed 10.5)",
    "drawing_deep_in_comparison_only": DRAWING_DEEP,
    "S_shoulder_in": S_SHOULDER,
    "B_butt_in": B_BUTT,
    "M_top_in": M,
    "N_back_in": N,
    "R_bounds_ft": (R_MIN_IN / 12.0, R_MAX_IN / 12.0),
    "L_bounds_in": (L_MIN_IN, L_MAX_IN),
    "side_height_source": "John Arnold direct correspondence (D28_SIDE_INVERSE_RERUN_002.md)",
}
MAPPING_INPUTS = {
    "lower_bout_width_in": LOWER_BOUT,
    "upper_bout_width_in": UPPER_BOUT,
    "waist_width_in": WAIST_W,
    "waist_y_norm": WAIST_Y_NORM,
    "outline_authority": "BodyContourSolver two-arc outline (parametric)",
    "station_mapping": "absolute developed arc length from neck",
}
COMPARISON_TARGETS = {
    "body_length_in": BODY_LENGTH_SPEC,
    "total_length_in": TOTAL_LENGTH_SPEC,
    "legacy_waist_station_in": LEGACY_WAIST_STATION,
    "drawing_deep_in": DRAWING_DEEP,
}

_SOLVER = BodyContourSolver(
    BodyConstraints(back_radius_mm=7620.0, butt_depth_mm=B_BUTT * 25.4,
                    shoulder_depth_mm=S_SHOULDER * 25.4, top_thickness_mm=0.0,
                    back_thickness_mm=0.0, scale_length_mm=645.0),
    family="dreadnought",
)
_N_PATH = 400


# --- Outline authority + developed arc-length geometry -----------------------

def neck_to_tail_path(L: float, n: int = _N_PATH) -> np.ndarray:
    """Right-half outline ordered neck (0, L) -> tail (0, 0), inches. Uses the
    repository BodyContourSolver arc construction with D-28 widths fixed and
    only the body length scaled (arc math is unit-agnostic)."""
    y_waist = WAIST_Y_NORM * L
    p0 = (0.0, 0.0)
    p1 = (LOWER_BOUT / 2.0, y_waist * 0.25)
    p2 = (WAIST_W / 2.0, y_waist)
    p3 = (UPPER_BOUT / 2.0, y_waist + (L - y_waist) * 0.55)
    p4 = (0.0, L)
    per = n // 2
    a = _SOLVER._generate_arc_segment(p0, p1, p2, per)   # butt -> waist
    b = _SOLVER._generate_arc_segment(p2, p3, p4, per)   # waist -> neck
    return np.asarray(list(reversed(a + b[1:])), dtype=float)   # neck -> tail


def cumulative_arclen(path: np.ndarray) -> np.ndarray:
    seg = np.hypot(np.diff(path[:, 0]), np.diff(path[:, 1]))
    return np.concatenate([[0.0], np.cumsum(seg)])


def geometric_waist(L: float) -> Dict[str, float]:
    """Geometric waist = the single interior local minimum of half-width along
    the neck->tail outline (the pinch flanked by the two bouts). Its developed
    neck-to-waist arc length is ``s_waist``."""
    path = neck_to_tail_path(L)
    cum = cumulative_arclen(path)
    x, y = path[:, 0], path[:, 1]
    mins = [i for i in range(2, len(x) - 2)
            if x[i - 1] > x[i] < x[i + 1] and 0.05 * L < y[i] < 0.95 * L]
    if not mins:
        raise ValueError("no interior waist minimum on outline")
    iw = min(mins, key=lambda i: x[i])
    return {"x": float(x[iw]), "y": float(y[iw]), "s_waist": float(cum[iw]),
            "half_perimeter": float(cum[-1])}


def point_at_arclen(L: float, s: float) -> Tuple[float, float, bool]:
    """Perimeter point at developed arc length ``s`` from the neck. Beyond the
    tail it clamps to the tail and flags it (developed span exceeds the model
    outline's half-perimeter)."""
    path = neck_to_tail_path(L)
    cum = cumulative_arclen(path)
    total = float(cum[-1])
    clamped = s > total
    t = min(s, total)
    x = float(np.interp(t, cum, path[:, 0]))
    y = float(np.interp(t, cum, path[:, 1]))
    return x, y, clamped


def _H_at_point(R: float, P: float, x: float, y: float) -> float:
    D = math.hypot(x - 0.0, y - P)
    return solve_side_height(B_BUTT, R, P, D, M, N)


def predict_waist_height(L: float, R: float) -> Tuple[float, float, float, float]:
    """Return (H_waist, D_waist, P, s_waist) at the geometric waist for (L, R)."""
    gw = geometric_waist(L)
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    D = math.hypot(gw["x"], gw["y"] - P)
    H = solve_side_height(B_BUTT, R, P, D, M, N)
    return H, D, P, gw["s_waist"]


def predict_station_height(L: float, R: float, station: float) -> Tuple[float, float, bool]:
    """Return (H, D, clamped) at an Arnold numeric station via absolute arc len."""
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    x, y, clamped = point_at_arclen(L, station)
    D = math.hypot(x, y - P)
    return solve_side_height(B_BUTT, R, P, D, M, N), D, clamped


def validation_residuals(L: float, R: float) -> Dict[float, float]:
    return {s: predict_station_height(L, R, s)[0] - ARNOLD_SIDE_HEIGHT_IN[s]
            for s in VALIDATION_STATIONS}


def is_admissible(L: float, R: float) -> Tuple[bool, List[str]]:
    """Physical admissibility: high point inside the body and no sqrt-domain
    clamping in the Sevy geometry."""
    reasons: List[str] = []
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    if P < 0:
        reasons.append("P<0 (high point beyond tail)")
    if P > L:
        reasons.append("P>L (high point beyond neck)")
    if abs(P) >= R:
        reasons.append("|P|>=R (sqrt domain)")
    _, D_w, _, _ = predict_waist_height(L, R)
    if D_w >= R:
        reasons.append("D_waist>=R (sqrt domain)")
    for s in VALIDATION_STATIONS:
        _, D, _ = predict_station_height(L, R, s)
        if D >= R:
            reasons.append(f"D>=R at station {s}")
            break
    return (len(reasons) == 0), reasons


def rmse(res: Dict[float, float]) -> float:
    v = np.array(list(res.values()), dtype=float)
    return float(np.sqrt(np.mean(v ** 2)))


# --- Convergence logger ------------------------------------------------------

CSV_FIELDS = [
    "run_id", "analysis", "outer_iteration", "inner_iteration", "radius_in",
    "radius_ft", "body_length_in", "high_point_P_in", "waist_station_derived_in",
    "target_waist_height_in", "predicted_waist_height_in", "waist_residual_in",
    "validation_rmse_in", "validation_max_abs_resid_in", "objective",
    "delta_radius_in", "delta_body_length_in", "solver_method",
    "physically_admissible", "bound_hit", "convergence_status",
]


class ConvergenceLogger:
    def __init__(self) -> None:
        self.rows: List[Dict[str, object]] = []

    def add(self, **kw) -> None:
        row = {f: kw.get(f, "") for f in CSV_FIELDS}
        self.rows.append(row)

    def write_csv(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(self.rows)


def _fmt(v: Optional[float], nd: int = 4) -> str:
    return "" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def _bound_hit(R: float) -> bool:
    return abs(R - R_MIN_IN) < 1e-6 or abs(R - R_MAX_IN) < 1e-6


# --- Recorded bisection root-finder for L (deterministic; logs inner steps) --

def solve_L_recorded(R: float, target: float, logger: Optional[ConvergenceLogger],
                     run_id: str, analysis: str, outer_iter: int,
                     predict: Callable[[float, float], float],
                     log_inner: bool = True, maxit: int = 60,
                     tol: float = 1e-7) -> Optional[float]:
    """Solve predict(L, R) = target for L by bracketed bisection over the L
    bounds, preferring a physically admissible root (P in [0, L]). Logs every
    inner iteration when a logger is supplied."""
    def g(L: float) -> float:
        return predict(L, R) - target

    grid = np.linspace(L_MIN_IN, L_MAX_IN, 113)
    gv = []
    prev_L = None
    for gi, L in enumerate(grid):
        L = float(L)
        try:
            val = g(L)
        except (ValueError, ZeroDivisionError):
            val = math.nan
        gv.append(val)
        if log_inner and logger is not None and not math.isnan(val):
            P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
            adm, _ = is_admissible(L, R)
            _, _, _, sw = predict_waist_height(L, R)
            logger.add(run_id=run_id, analysis=analysis, outer_iteration=outer_iter,
                       inner_iteration=f"scan{gi}", radius_in=_fmt(R, 3), radius_ft=_fmt(R / 12, 4),
                       body_length_in=_fmt(L, 6), high_point_P_in=_fmt(P, 6),
                       waist_station_derived_in=_fmt(sw, 4),
                       target_waist_height_in=_fmt(target, 4),
                       predicted_waist_height_in=_fmt(val + target, 6),
                       waist_residual_in=_fmt(val, 8),
                       delta_body_length_in=_fmt((L - prev_L) if prev_L is not None else None, 6),
                       solver_method="grid_scan", physically_admissible=adm,
                       bound_hit=_bound_hit(R), convergence_status="scanning")
        prev_L = L
    brackets = []
    for i in range(len(grid) - 1):
        a, b = gv[i], gv[i + 1]
        if math.isnan(a) or math.isnan(b) or a == 0.0:
            continue
        if a * b < 0:
            brackets.append((float(grid[i]), float(grid[i + 1])))

    def bisect(lo: float, hi: float) -> float:
        flo = g(lo)
        prev = None
        L = 0.5 * (lo + hi)
        for k in range(maxit):
            L = 0.5 * (lo + hi)
            fL = g(L)
            if log_inner and logger is not None:
                P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
                adm, _ = is_admissible(L, R)
                _, _, _, sw = predict_waist_height(L, R)
                logger.add(run_id=run_id, analysis=analysis, outer_iteration=outer_iter,
                           inner_iteration=k, radius_in=_fmt(R, 3), radius_ft=_fmt(R / 12, 4),
                           body_length_in=_fmt(L, 6), high_point_P_in=_fmt(P, 6),
                           waist_station_derived_in=_fmt(sw, 4),
                           target_waist_height_in=_fmt(target, 4),
                           predicted_waist_height_in=_fmt(fL + target, 6),
                           waist_residual_in=_fmt(fL, 8),
                           delta_body_length_in=_fmt((L - prev) if prev is not None else None, 6),
                           solver_method="bisection", physically_admissible=adm,
                           bound_hit=_bound_hit(R),
                           convergence_status=("converged" if abs(fL) < tol else "iterating"))
            prev = L
            if abs(fL) < tol or (hi - lo) < tol:
                return L
            if flo * fL < 0:
                hi = L
            else:
                lo, flo = L, fL
        return L

    roots = []
    for lo, hi in brackets:
        roots.append(bisect(lo, hi))
    if not roots:
        return None
    adm_roots = [L for L in roots if 0.0 <= solve_high_point(L, B_BUTT, S_SHOULDER, R) <= L]
    pool = adm_roots or roots
    return min(pool, key=lambda L: abs(L - BODY_LENGTH_SPEC))


# --- Analysis A: corrected waist-constrained nested solve --------------------

@dataclass
class RowA:
    R_in: float
    L_in: Optional[float]
    P_in: Optional[float]
    s_waist_in: Optional[float]
    rmse_in: Optional[float]
    max_abs_in: Optional[float]
    admissible: Optional[bool]
    bound_hit: bool


def analysis_A(logger: ConvergenceLogger, n_R: int = 43) -> List[RowA]:
    rows: List[RowA] = []
    prev_L = None
    prev_R = None
    for oi, R in enumerate(np.linspace(R_MIN_IN, R_MAX_IN, n_R)):
        R = float(R)
        L = solve_L_recorded(R, WAIST_SIDE_HEIGHT, logger, f"A_R{oi:03d}", "A", oi,
                             lambda LL, RR: predict_waist_height(LL, RR)[0])
        if L is None:
            logger.add(run_id=f"A_R{oi:03d}", analysis="A", outer_iteration=oi,
                       inner_iteration="", radius_in=_fmt(R, 3), radius_ft=_fmt(R / 12, 4),
                       target_waist_height_in=_fmt(WAIST_SIDE_HEIGHT, 4),
                       solver_method="bisection", bound_hit=_bound_hit(R),
                       delta_radius_in=_fmt((R - prev_R) if prev_R is not None else None, 3),
                       convergence_status="no_root")
            rows.append(RowA(R, None, None, None, None, None, None, _bound_hit(R)))
            prev_R = R
            continue
        Hw, _, P, sw = predict_waist_height(L, R)
        res = validation_residuals(L, R)
        e = rmse(res)
        mx = max(abs(v) for v in res.values())
        adm, _ = is_admissible(L, R)
        logger.add(run_id=f"A_R{oi:03d}", analysis="A", outer_iteration=oi,
                   inner_iteration="final", radius_in=_fmt(R, 3), radius_ft=_fmt(R / 12, 4),
                   body_length_in=_fmt(L, 6), high_point_P_in=_fmt(P, 6),
                   waist_station_derived_in=_fmt(sw, 4),
                   target_waist_height_in=_fmt(WAIST_SIDE_HEIGHT, 4),
                   predicted_waist_height_in=_fmt(Hw, 6), waist_residual_in=_fmt(Hw - WAIST_SIDE_HEIGHT, 8),
                   validation_rmse_in=_fmt(e, 6), validation_max_abs_resid_in=_fmt(mx, 6),
                   objective=_fmt(e, 6),
                   delta_radius_in=_fmt((R - prev_R) if prev_R is not None else None, 3),
                   delta_body_length_in=_fmt((L - prev_L) if prev_L is not None else None, 6),
                   solver_method="bisection", physically_admissible=adm,
                   bound_hit=_bound_hit(R), convergence_status="solved")
        rows.append(RowA(R, L, P, sw, e, mx, adm, _bound_hit(R)))
        prev_L, prev_R = L, R
    return rows


def best_A(rows: List[RowA]) -> Optional[RowA]:
    valid = [r for r in rows if r.rmse_in is not None]
    return min(valid, key=lambda r: r.rmse_in) if valid else None


# --- Analysis B: full least squares in (L, R), with admissibility flags ------

def analysis_B(logger: ConvergenceLogger,
               inits: List[Tuple[float, float]]) -> List[dict]:
    results = []
    for si, (L0, R0) in enumerate(inits):
        counter = {"n": 0}
        prev = {"R": None, "L": None}

        def resid(x: np.ndarray) -> np.ndarray:
            L, R = float(x[0]), float(x[1])
            out = []
            for s in VALIDATION_STATIONS:
                try:
                    H, _, _ = predict_station_height(L, R, s)
                except (ValueError, ZeroDivisionError):
                    H = 1e3
                out.append(H - ARNOLD_SIDE_HEIGHT_IN[s])
            # waist as a soft term as well (it is the hard anchor in A).
            try:
                Hw = predict_waist_height(L, R)[0]
            except (ValueError, ZeroDivisionError):
                Hw = 1e3
            out.append(Hw - WAIST_SIDE_HEIGHT)
            arr = np.array(out, dtype=float)
            k = counter["n"]
            P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
            adm, _ = is_admissible(L, R)
            _, _, _, sw = predict_waist_height(L, R)
            logger.add(run_id=f"B_start{si}", analysis="B", outer_iteration=si,
                       inner_iteration=k, radius_in=_fmt(R, 3), radius_ft=_fmt(R / 12, 4),
                       body_length_in=_fmt(L, 6), high_point_P_in=_fmt(P, 6),
                       waist_station_derived_in=_fmt(sw, 4),
                       target_waist_height_in=_fmt(WAIST_SIDE_HEIGHT, 4),
                       predicted_waist_height_in=_fmt(Hw, 6), waist_residual_in=_fmt(Hw - WAIST_SIDE_HEIGHT, 8),
                       objective=_fmt(float(np.sqrt(np.mean(arr ** 2))), 6),
                       delta_radius_in=_fmt((R - prev["R"]) if prev["R"] is not None else None, 4),
                       delta_body_length_in=_fmt((L - prev["L"]) if prev["L"] is not None else None, 6),
                       solver_method="least_squares", physically_admissible=adm,
                       bound_hit=(abs(R - R_MIN_IN) < 1e-3 or abs(R - R_MAX_IN) < 1e-3
                                  or abs(L - L_MIN_IN) < 1e-3 or abs(L - L_MAX_IN) < 1e-3),
                       convergence_status="iterating")
            counter["n"] += 1
            prev["R"], prev["L"] = R, L
            return arr

        sol = least_squares(resid, x0=[L0, R0],
                            bounds=([L_MIN_IN, R_MIN_IN], [L_MAX_IN, R_MAX_IN]))
        L, R = float(sol.x[0]), float(sol.x[1])
        P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
        adm, reasons = is_admissible(L, R)
        bound = (abs(R - R_MIN_IN) < 1e-2 or abs(R - R_MAX_IN) < 1e-2
                 or abs(L - L_MIN_IN) < 1e-2 or abs(L - L_MAX_IN) < 1e-2)
        logger.add(run_id=f"B_start{si}", analysis="B", outer_iteration=si,
                   inner_iteration="final", radius_in=_fmt(R, 3), radius_ft=_fmt(R / 12, 4),
                   body_length_in=_fmt(L, 6), high_point_P_in=_fmt(P, 6),
                   target_waist_height_in=_fmt(WAIST_SIDE_HEIGHT, 4),
                   objective=_fmt(float(np.sqrt(np.mean(sol.fun ** 2))), 6),
                   solver_method="least_squares", physically_admissible=adm,
                   bound_hit=bound, convergence_status=("converged" if sol.success else "stopped"))
        results.append({"L0": L0, "R0": R0, "L": L, "R": R, "P": P,
                        "rmse": float(np.sqrt(np.mean(sol.fun ** 2))),
                        "admissible": adm, "reasons": reasons, "bound_hit": bound,
                        "success": bool(sol.success)})
    return results


# --- Analysis C: leave-one-out / alternate-anchor identifiability ------------

def analysis_C(logger: ConvergenceLogger, n_R: int = 22) -> List[dict]:
    anchors = VALIDATION_STATIONS + ["WAIST"]
    out = []
    for anchor in anchors:
        tag = "WAIST" if anchor == "WAIST" else f"{anchor}"
        target = WAIST_SIDE_HEIGHT if anchor == "WAIST" else ARNOLD_SIDE_HEIGHT_IN[anchor]
        if anchor == "WAIST":
            predict = lambda LL, RR: predict_waist_height(LL, RR)[0]
        else:
            predict = lambda LL, RR, a=anchor: predict_station_height(LL, RR, a)[0]
        others = [s for s in VALIDATION_STATIONS if s != anchor]
        best = None
        for oi, R in enumerate(np.linspace(R_MIN_IN, R_MAX_IN, n_R)):
            R = float(R)
            L = solve_L_recorded(R, target, logger, f"C_{tag}_R{oi:03d}", "C", oi,
                                 predict, log_inner=False)
            if L is None:
                continue
            res = [predict_station_height(L, R, s)[0] - ARNOLD_SIDE_HEIGHT_IN[s] for s in others]
            e = float(np.sqrt(np.mean(np.array(res) ** 2)))
            P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
            adm, _ = is_admissible(L, R)
            logger.add(run_id=f"C_{tag}_R{oi:03d}", analysis="C", outer_iteration=oi,
                       inner_iteration="final", radius_in=_fmt(R, 3), radius_ft=_fmt(R / 12, 4),
                       body_length_in=_fmt(L, 6), high_point_P_in=_fmt(P, 6),
                       target_waist_height_in=_fmt(target, 4), objective=_fmt(e, 6),
                       validation_rmse_in=_fmt(e, 6), solver_method="bisection(outer)",
                       physically_admissible=adm, bound_hit=_bound_hit(R),
                       convergence_status="solved")
            if best is None or e < best["rmse"]:
                best = {"anchor": tag, "L": L, "R": R, "P": P, "rmse": e, "admissible": adm}
        out.append(best or {"anchor": tag, "L": None, "R": None, "P": None,
                            "rmse": None, "admissible": None})
    return out


# --- Disposition -------------------------------------------------------------

def classify(bestA: Optional[RowA], fitB: List[dict], loo: List[dict],
             floor_H: float) -> Tuple[str, List[str]]:
    notes: List[str] = []
    if bestA is None or bestA.L_in is None:
        okB = [f for f in fitB if "L" in f]
        b_adm = [f for f in okB if f["admissible"] and not f["bound_hit"]]
        notes = [
            f"Analysis A found no admissible root at any R: the model's minimum "
            f"achievable waist side height ({floor_H:.4f} in) exceeds the 4.220 in "
            "target, so the hard constraint at the geometric waist cannot be met.",
            "The geometric waist location comes from the parametric outline authority "
            "(BodyContourSolver, waist_y_norm=0.44); its developed station (~14.3 in) "
            "disagrees with where the 4.220 in reading sits in Arnold's monotonic series "
            "(~10.5 in), so the constraint and the outline cannot be reconciled.",
        ]
        if not b_adm:
            notes.append("Every unconstrained least-squares solution is physically "
                         "inadmissible (P<0) and/or radius-bound-pinned, so B offers no "
                         "admissible cross-check either.")
        return "INSUFFICIENT_GEOMETRY_AUTHORITY", notes
    loo_ok = [d for d in loo if d["L"] is not None]
    loo_L = [d["L"] for d in loo_ok]
    loo_clusters = bool(loo_L) and (max(loo_L) - min(loo_L) < 2.0)
    okB = [f for f in fitB if "L" in f]
    b_adm = [f for f in okB if f["admissible"] and not f["bound_hit"]]
    ab_agree = bool(b_adm) and any(abs(f["L"] - bestA.L_in) < 1.0 for f in b_adm)

    if not loo_clusters:
        notes.append(f"Leave-one-out anchors do NOT cluster (recovered L spans "
                     f"{min(loo_L):.2f}..{max(loo_L):.2f} in): L and R are not "
                     "separately identifiable from these data.")
    if bestA.bound_hit:
        notes.append(f"Analysis A optimum sits on the R bound ({bestA.R_in/12:.1f} ft) "
                     "— no interior minimum.")
    if not b_adm:
        notes.append("Every unconstrained least-squares solution is physically "
                     "inadmissible (P<0/P>L) or bound-pinned.")
    if not loo_clusters or bestA.bound_hit or not b_adm:
        return "UNDERDETERMINED", notes
    if abs(bestA.L_in - BODY_LENGTH_SPEC) < 1.0 and ab_agree:
        notes.append("A and B agree and recovered L is within 1 in of 20.")
        return "CONVERGES_AND_SUPPORTS_20IN", notes
    notes.append(f"Stable but recovered L = {bestA.L_in:.2f} in (not ~20).")
    return "CONVERGES_BUT_NOT_20IN", notes


# --- Inconsistency register --------------------------------------------------

def inconsistency_register(bestA: Optional[RowA], hp_20: float,
                           s_waist_20: float) -> List[dict]:
    reg = [
        {"field": "waist side height", "experimental": f"{WAIST_SIDE_HEIGHT} in (Arnold side height)",
         "conflicting": f"repo side_profile_raw['10.5']={_SPEC['side_profile_raw']['10.5']} in (same number, labelled waist)",
         "difference": "0.000 in (value agrees; label/station differ)",
         "source": "Arnold correspondence vs martin_d28_1937.json",
         "effect": "hard constraint value confirmed; applied at derived station not 10.5",
         "class": "EXPERIMENTAL_OVERRIDE",
         "disposition": "use 4.220 as side height; repo unchanged"},
        {"field": "4.4375 in DEEP drawing value", "experimental": "comparison-only (assembled depth)",
         "conflicting": f"first run used it as side height; Δ vs side height = {DRAWING_MINUS_SIDE:+.4f} in",
         "difference": f"{DRAWING_MINUS_SIDE:+.4f} in",
         "source": "Arnold drawing annotation vs Arnold correspondence",
         "effect": "excluded from the side-height solve (see reconciliation, section E)",
         "class": "SOURCE_CONFLICT",
         "disposition": "treat 0.2175 in as unresolved datum/method difference (hypothesis only)"},
        {"field": "waist developed station", "experimental": f"derived s_waist={s_waist_20:.3f} in (@L=20)",
         "conflicting": f"legacy assumed {LEGACY_WAIST_STATION} in",
         "difference": f"{s_waist_20 - LEGACY_WAIST_STATION:+.3f} in",
         "source": "outline geometry vs first-run assumption",
         "effect": "moves the hard-constraint location toward the tail vs the legacy guess",
         "class": "DERIVATION_MISMATCH",
         "disposition": "use geometrically derived station; 10.5 was never source-measured"},
        {"field": "30.4375 in", "experimental": "developed side-strip span (Arnold bottom-end station)",
         "conflicting": f"repo total_length={TOTAL_LENGTH_SPEC} in; outline half-perimeter@L=20={hp_20:.2f} in",
         "difference": f"{hp_20 - TOTAL_LENGTH_SPEC:+.2f} in vs half-perimeter",
         "source": "repo dimensions.total_length; derived outline",
         "effect": "governs absolute arc-length mapping; 'body length' reading falsified previously",
         "class": "UNIT_OR_DATUM_AMBIGUITY",
         "disposition": "read 30.4375 in as developed side span, not centerline body length"},
        {"field": "Arnold 12-pt profile vs spherical-back model", "experimental": "12 side-height points",
         "conflicting": "single-radius spherical back",
         "difference": f"A best validation RMSE={bestA.rmse_in:.4f} in" if bestA and bestA.rmse_in else "n/a",
         "source": "Arnold correspondence vs Sevy/Doolin model",
         "effect": "residual pattern + non-identifiability indicate limited model fit",
         "class": "UNRESOLVED",
         "disposition": "report as-is; do not force the model to match"},
        {"field": "plan-view outline authority", "experimental": "not declared",
         "conflicting": f"BodyContourSolver parametric outline; waist_y_norm={WAIST_Y_NORM} family default",
         "difference": "model dependence",
         "source": "body_contour_solver FAMILY_DEFAULTS",
         "effect": "derived s_waist and D mapping depend on the parametric outline shape",
         "class": "UNRESOLVED",
         "disposition": "replace with a measured #65260 perimeter if one becomes available"},
        {"field": "martin_d28_1937.py module", "experimental": "n/a",
         "conflicting": "single line; early # comment swallows all code (exports nothing)",
         "difference": "code vs data-bearing .json",
         "source": "services/api/app/instrument_geometry/specs/martin_d28_1937.py",
         "effect": "none (observations sourced from the rerun order / .json)",
         "class": "REPO_CONFLICT",
         "disposition": "flag for owner; not fixed here"},
    ]
    return reg


# --- Startup confirmation + input guard --------------------------------------

def active_inputs_lines() -> List[str]:
    out = ["ACTIVE EXPERIMENTAL INPUTS (Rerun 002 — Arnold side-height authority)"]
    out.append(f"  waist_side_height_in   = {WAIST_SIDE_HEIGHT}  (HARD constraint)")
    out.append(f"  waist_station          = GEOMETRICALLY DERIVED (not 10.5)")
    out.append(f"  drawing_DEEP_in        = {DRAWING_DEEP}  (COMPARISON ONLY — not side height)")
    out.append(f"  S_shoulder_in @0.0     = {S_SHOULDER}")
    out.append(f"  B_butt_in @{S_TAIL_STATION}   = {B_BUTT}")
    out.append(f"  M_top_in / N_back_in   = {M} / {N}")
    out.append(f"  R_bounds_ft            = {EXPERIMENTAL_INPUTS['R_bounds_ft']}")
    out.append(f"  L_bounds_in            = {EXPERIMENTAL_INPUTS['L_bounds_in']}")
    out.append("  Arnold side heights (in; developed station -> side height):")
    for s in STATIONS:
        out.append(f"    {s:>8} -> {ARNOLD_SIDE_HEIGHT_IN[s]:.4f}")
    out.append(f"    WAIST    -> {WAIST_SIDE_HEIGHT:.4f}  (@derived station)")
    out.append("  mapping geometry (repo, mapping-only, NOT a solve input):")
    for k, v in MAPPING_INPUTS.items():
        out.append(f"    {k} = {v}")
    return out


def check_required_inputs() -> None:
    required = {"waist_side_height_in": WAIST_SIDE_HEIGHT, "S_shoulder_in": S_SHOULDER,
                "B_butt_in": B_BUTT, "M_top_in": M, "N_back_in": N}
    missing = [k for k, v in required.items() if v is None]
    if missing:
        raise SystemExit(f"STOP: required experimental input(s) missing: {missing}. "
                         "Declare them; do not fall back to repo values.")


# --- Orchestration -----------------------------------------------------------

def waist_height_floor() -> Tuple[float, float, float]:
    """Minimum achievable model waist side height over the (L, R) search box.
    If this floor exceeds the 4.220 in target, Analysis A has no root."""
    best = None
    for R in np.linspace(R_MIN_IN, R_MAX_IN, 29):
        for L in np.linspace(L_MIN_IN, L_MAX_IN, 29):
            try:
                H = predict_waist_height(float(L), float(R))[0]
            except (ValueError, ZeroDivisionError):
                continue
            if best is None or H < best[0]:
                best = (H, float(L), float(R))
    return best if best else (math.nan, math.nan, math.nan)


@dataclass
class RunResult:
    logger: ConvergenceLogger
    rowsA: List[RowA]
    bestA: Optional[RowA]
    fitB: List[dict]
    loo: List[dict]
    disposition: str
    notes: List[str]
    s_waist_20: float
    hp_20: float
    h_waist_floor: float
    floor_L: float
    floor_R: float
    stop_condition: Optional[str]


def run_all() -> RunResult:
    logger = ConvergenceLogger()
    gw20 = geometric_waist(BODY_LENGTH_SPEC)
    floor_H, floor_L, floor_R = waist_height_floor()
    rowsA = analysis_A(logger)
    bestA = best_A(rowsA)
    inits = [(20.0, 180.0), (18.0, 300.0), (22.0, 120.0), (16.0, 500.0), (30.0, 250.0)]
    fitB = analysis_B(logger, inits)
    loo = analysis_C(logger)
    disposition, notes = classify(bestA, fitB, loo, floor_H)
    stop = None
    if bestA is None:
        stop = (f"Hard waist constraint {WAIST_SIDE_HEIGHT} in is unsatisfiable with "
                f"physically admissible geometry: the model's minimum achievable waist "
                f"side height over the search box is {floor_H:.4f} in > {WAIST_SIDE_HEIGHT} in. "
                f"The geometric waist (developed s={gw20['s_waist']:.2f} in from the outline "
                f"authority) cannot be reconciled with the Arnold 4.220 in reading under the "
                f"spherical-back model.")
    return RunResult(logger, rowsA, bestA, fitB, loo, disposition, notes,
                     gw20["s_waist"], gw20["half_perimeter"], floor_H, floor_L, floor_R, stop)


def summary_rows(rr: RunResult) -> List[Dict[str, object]]:
    b = rr.bestA
    loo_ok = [d for d in rr.loo if d["L"] is not None]
    loo_L = [d["L"] for d in loo_ok]
    ident = ("clusters" if loo_L and (max(loo_L) - min(loo_L) < 2.0)
             else f"non-clustering (L spans {min(loo_L):.2f}..{max(loo_L):.2f} in)"
             if loo_L else "no solutions")
    return [{
        "best_fit_R_in": _fmt(b.R_in, 2) if b else "",
        "best_fit_R_ft": _fmt(b.R_in / 12, 3) if b else "",
        "best_fit_L_in": _fmt(b.L_in, 3) if b and b.L_in else "",
        "high_point_P_in": _fmt(b.P_in, 3) if b and b.P_in else "",
        "derived_waist_station_in": _fmt(b.s_waist_in, 3) if b and b.s_waist_in else _fmt(rr.s_waist_20, 3),
        "legacy_waist_station_in": _fmt(LEGACY_WAIST_STATION, 3),
        "validation_rmse_in": _fmt(b.rmse_in, 4) if b and b.rmse_in else "",
        "validation_max_abs_resid_in": _fmt(b.max_abs_in, 4) if b and b.max_abs_in else "",
        "physically_admissible": (b.admissible if b else ""),
        "A_optimum_on_bound": (b.bound_hit if b else ""),
        "identifiability": ident,
        "final_disposition": rr.disposition,
    }]


def write_summary_csv(rr: RunResult, path: str) -> None:
    rows = summary_rows(rr)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


# --- Rerun 002 report section (spliced into the results doc) -----------------

def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       cwd=_REPO_ROOT).decode().strip()
    except Exception:
        return "UNKNOWN"


def build_rerun_section(rr: RunResult) -> str:
    b = rr.bestA
    L = []
    w = L.append
    w("## Corrected Rerun 002 — Arnold Side Height Authority")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w(f"- Convergence log: `docs/experiments/results/D28_65260_SIDE_INVERSE_RERUN_002_CONVERGENCE.csv`")
    w(f"- Summary: `docs/experiments/results/D28_65260_SIDE_INVERSE_RERUN_002_SUMMARY.csv`")
    w("")
    w("### Experimental authority rule (read first)")
    w("")
    w("Only the declared inputs govern the solve. The hard waist constraint is the")
    w(f"John Arnold **side height {WAIST_SIDE_HEIGHT} in**; the drawing annotation")
    w(f"**{DRAWING_DEEP} in DEEP** is a separate assembled-depth measurement used for")
    w("comparison only and is never used as side height. The waist station is derived")
    w("from the outline geometry, not assumed. Repo values are read only for mapping,")
    w("provenance, comparison, validation, and inconsistency detection. No production,")
    w("spec, or authority file is modified.")
    w("")
    w("### Active experimental inputs")
    w("")
    w("```text")
    for line in active_inputs_lines():
        w(line)
    w("```")
    w("")
    w("### Geometric waist derivation")
    w("")
    gw = geometric_waist(BODY_LENGTH_SPEC)
    w(f"- Geometric waist point (@ nominal L = 20 in): "
      f"(x = {gw['x']:.3f} in, y = {gw['y']:.3f} in from tail).")
    w(f"- Derived developed neck-to-waist station `s_waist` (@ L = 20 in): "
      f"**{gw['s_waist']:.3f} in**.")
    if b and b.s_waist_in:
        w(f"- Derived `s_waist` at the recovered L* = {b.L_in:.2f} in: **{b.s_waist_in:.3f} in**.")
    w(f"- Legacy assumed waist station: {LEGACY_WAIST_STATION} in.")
    w(f"- Difference (derived − legacy, @ L = 20): "
      f"**{gw['s_waist'] - LEGACY_WAIST_STATION:+.3f} in**. The 10.5 in figure was never "
      "source-measured; it was inferred from lying between stations 9 and 12.")
    w(f"- Outline half-perimeter (neck→tail) @ L = 20 in: {gw['half_perimeter']:.3f} in.")
    w("- Mapping: each Arnold station maps to the perimeter point at that **absolute**")
    w("  developed arc length from the neck; `D` is the Euclidean in-plane distance from")
    w("  the spherical high point to the mapped point (never the station).")
    w("")
    w("### A. Corrected waist-constrained nested solve (H_waist = 4.220 in)")
    w("")
    w("| R (in) | R (ft) | L (in) | P (in) | s_waist (in) | val RMSE (in) | max|resid| (in) | admissible | bound |")
    w("|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|")
    for r in rr.rowsA[::3]:
        if r.L_in is None:
            w(f"| {r.R_in:.1f} | {r.R_in/12:.2f} | n/a | n/a | n/a | n/a | n/a | n/a | {r.bound_hit} |")
        else:
            w(f"| {r.R_in:.1f} | {r.R_in/12:.2f} | {r.L_in:.3f} | {r.P_in:.3f} | {r.s_waist_in:.3f} "
              f"| {r.rmse_in:.4f} | {r.max_abs_in:.4f} | {r.admissible} | {r.bound_hit} |")
    w("")
    if b:
        w(f"- Best (min validation RMSE): R* = {b.R_in:.2f} in ({b.R_in/12:.2f} ft), "
          f"L* = {b.L_in:.3f} in, P* = {b.P_in:.3f} in, s_waist = {b.s_waist_in:.3f} in, "
          f"RMSE = {b.rmse_in:.4f} in, max|resid| = {b.max_abs_in:.4f} in, "
          f"admissible = {b.admissible}, on-bound = {b.bound_hit}.")
    else:
        w(f"- **No admissible root at any R.** The model's minimum achievable waist side "
          f"height over the (L, R) search box is **{rr.h_waist_floor:.4f} in** "
          f"(at L = {rr.floor_L:.1f} in, R = {rr.floor_R/12:.1f} ft), which is above the "
          f"**{WAIST_SIDE_HEIGHT} in** target. The 4.220 in constraint at the geometric "
          "waist (developed s ≈ 14.3 in) is therefore unsatisfiable — the bracketing grid "
          "scan (logged in the convergence CSV) shows the waist residual never changes sign.")
    w("")
    if b and b.L_in:
        w("#### Residuals at the best Analysis-A solution")
        w("")
        w("| station (in) | measured H (in) | predicted H (in) | residual (in) | D (in) |")
        w("|---:|---:|---:|---:|---:|")
        for s in STATIONS:
            Hp, D, _ = predict_station_height(b.L_in, b.R_in, s)
            meas = ARNOLD_SIDE_HEIGHT_IN[s]
            bc = " (S bc)" if s == S_NECK_STATION else (" (B bc)" if s == S_TAIL_STATION else "")
            w(f"| {s}{bc} | {meas:.4f} | {Hp:.4f} | {Hp-meas:+.4f} | {D:.3f} |")
        Hw, Dw, _, sw = predict_waist_height(b.L_in, b.R_in)
        w(f"| WAIST @{sw:.2f}* | {WAIST_SIDE_HEIGHT:.4f} | {Hw:.4f} | {Hw-WAIST_SIDE_HEIGHT:+.4f} | {Dw:.3f} |")
        w("")
        w("`(S bc)`/`(B bc)` are the boundary depths; `*` is the hard waist constraint.")
    w("")
    w("### B. Full least-squares cross-check (L, R)")
    w("")
    w("| L0 | R0 | L (in) | R (in/ft) | P (in) | RMSE (in) | admissible | bound | flags |")
    w("|---:|---:|---:|---:|---:|---:|:--:|:--:|---|")
    for f in rr.fitB:
        flags = "" if f["admissible"] and not f["bound_hit"] else "; ".join(f["reasons"] + (["bound"] if f["bound_hit"] else []))
        w(f"| {f['L0']:.0f} | {f['R0']:.0f} | {f['L']:.3f} | {f['R']:.1f}/{f['R']/12:.2f} "
          f"| {f['P']:.3f} | {f['rmse']:.4f} | {f['admissible']} | {f['bound_hit']} | {flags} |")
    w("")
    w("### C. Anchor / leave-one-out identifiability")
    w("")
    w("| anchor | L (in) | R (in/ft) | P (in) | RMSE others (in) | admissible |")
    w("|---|---:|---:|---:|---:|:--:|")
    for d in rr.loo:
        if d["L"] is None:
            w(f"| {d['anchor']} | n/a | n/a | n/a | n/a | n/a |")
        else:
            w(f"| {d['anchor']} | {d['L']:.3f} | {d['R']:.1f}/{d['R']/12:.2f} | {d['P']:.3f} "
              f"| {d['rmse']:.4f} | {d['admissible']} |")
    loo_ok = [d for d in rr.loo if d["L"] is not None]
    if loo_ok:
        Ls = [d["L"] for d in loo_ok]
        w("")
        w(f"- Recovered L spread: {min(Ls):.2f} .. {max(Ls):.2f} in (range {max(Ls)-min(Ls):.2f} in).")
    w("")
    w("### D. First run (superseded) vs Rerun 002")
    w("")
    r2L = f"{b.L_in:.2f} in" if b else "no admissible solution"
    r2R = (f"{b.R_in/12:.2f} ft{' (bound)' if b.bound_hit else ''}" if b else "n/a")
    r2P = f"{b.P_in:.2f} in" if b else "n/a"
    r2RMSE = f"{b.rmse_in:.4f} in" if b else "n/a"
    w("| quantity | first run (superseded) | Rerun 002 |")
    w("|---|---|---|")
    w(f"| waist side height | {FIRST_RUN['waist_side_height_in']} in (DEEP mis-used) | {WAIST_SIDE_HEIGHT} in (Arnold side height) |")
    w(f"| waist station | {FIRST_RUN['waist_station_in']} in (assumed) | {gw['s_waist']:.2f} in (derived @L=20) |")
    w(f"| recovered L* | {FIRST_RUN['L_star_in']} in | {r2L} |")
    w(f"| recovered R* | {FIRST_RUN['R_star_ft']} ft (bound) | {r2R} |")
    w(f"| P* | {FIRST_RUN['P_star_in']} in | {r2P} |")
    w(f"| validation RMSE | {FIRST_RUN['validation_rmse_in']} in | {r2RMSE} |")
    w(f"| disposition | {FIRST_RUN['disposition']} | {rr.disposition} |")
    w("")
    w("The first run appeared to 'support 20 in' only because it imposed the wrong")
    w("(higher) 4.4375 in value at an assumed 10.5 in station. With the correct 4.220 in")
    w("side height at the geometrically derived waist, that apparent support disappears.")
    w("")
    w("### E. Drawing-depth reconciliation (side height vs DEEP)")
    w("")
    w(f"- Drawing waist DEEP = {DRAWING_DEEP} in; Arnold waist side height = {WAIST_SIDE_HEIGHT} in; "
      f"difference = **{DRAWING_MINUS_SIDE:.4f} in** ({DRAWING_MINUS_SIDE*25.4:.4f} mm).")
    w("- The inverse side-height solve is NOT forced to explain this offset. The spec")
    w("  side profile excludes top/back thickness (M=N=0), and the repo records no")
    w("  #65260 top/back plate thickness that provenance-links to 0.2175 in, so the")
    w("  offset is left as an **unresolved datum/measurement-method difference**")
    w("  (assembled 'DEEP' depth vs bare side height) — a hypothesis, not a conclusion.")
    w("")
    if rr.stop_condition:
        w("### STOP condition encountered")
        w("")
        w(f"- {rr.stop_condition}")
        w("- Per the rerun order, this is reported rather than resolved by inventing")
        w("  geometry or by treating the developed station as `D`.")
        w("")
    w("### Disposition")
    w("")
    w(f"**{rr.disposition}**")
    w("")
    for n in rr.notes:
        w(f"- {n}")
    w("")
    w("### Inconsistency audit")
    w("")
    reg = inconsistency_register(b, rr.hp_20, rr.s_waist_20)
    w("| field / value | experimental | conflicting repo/source | difference | source | effect | class | disposition |")
    w("|---|---|---|---|---|---|---|---|")
    for r in reg:
        w(f"| {r['field']} | {r['experimental']} | {r['conflicting']} | {r['difference']} "
          f"| {r['source']} | {r['effect']} | `{r['class']}` | {r['disposition']} |")
    w("")
    w("Classes: `EXPERIMENTAL_OVERRIDE`, `REPO_CONFLICT`, `SOURCE_CONFLICT`, "
      "`DERIVATION_MISMATCH`, `UNIT_OR_DATUM_AMBIGUITY`, `UNRESOLVED`.")
    w("")
    return "\n".join(L)


# --- Doc splice --------------------------------------------------------------

_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                    "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_CONV_CSV = os.path.join(_REPO_ROOT, "docs", "experiments", "results",
                         "D28_65260_SIDE_INVERSE_RERUN_002_CONVERGENCE.csv")
_SUM_CSV = os.path.join(_REPO_ROOT, "docs", "experiments", "results",
                        "D28_65260_SIDE_INVERSE_RERUN_002_SUMMARY.csv")
_START, _END = "<!-- RERUN002_START -->", "<!-- RERUN002_END -->"


def splice_doc(section: str) -> None:
    with open(_DOC) as fh:
        text = fh.read()
    block = f"{_START}\n{section}\n{_END}"
    if _START in text and _END in text:
        pre = text[:text.index(_START)]
        post = text[text.index(_END) + len(_END):]
        text = pre + block + post
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    with open(_DOC, "w") as fh:
        fh.write(text)


def main() -> None:
    check_required_inputs()
    print("\n".join(active_inputs_lines()), file=sys.stderr)
    print("--- solving (Rerun 002) ---", file=sys.stderr)
    rr = run_all()
    section = build_rerun_section(rr)
    if "--write" in sys.argv:
        rr.logger.write_csv(_CONV_CSV)
        write_summary_csv(rr, _SUM_CSV)
        splice_doc(section)
        print(f"wrote {_CONV_CSV} ({len(rr.logger.rows)} rows)")
        print(f"wrote {_SUM_CSV}")
        print(f"spliced Rerun 002 section into {_DOC}")
    else:
        print(section)
        print(f"\n[convergence rows: {len(rr.logger.rows)}; disposition: {rr.disposition}]")


if __name__ == "__main__":
    main()
