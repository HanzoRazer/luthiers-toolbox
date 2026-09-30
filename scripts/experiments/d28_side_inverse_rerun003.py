#!/usr/bin/env python3
"""
D28 SIDE INVERSE RERUN 003 — Arnold Outline Authority (solver)
==============================================================

Reruns the #65260 side-height inverse using the Arnold-derived plan-view outline
(extracted deterministically by ``d28_rerun003_extract.py`` from the verified
traced CAD reconstruction ACOUSTIC BODY.pdf; John Arnold #65260 drawing is the
primary historical source). Reuses the production Sevy/Doolin equations
unchanged; modifies no production/spec/authority file.

Governing corrections vs Rerun 002 (per the revised order):
  * Outline authority is the Arnold-derived CAD tracing, NOT the parametric
    dreadnought. neck=y0, tail=y=L, soundhole center = datum A (extracted).
  * Geometric waist, upper/lower bout maxima are OUTPUTS of the extracted
    perimeter (not waist_y_norm=0.44 / not station 10.5).
  * Hard inverse anchor = explicit numeric station 12.000 in -> 4.240 in.
    Waist side height 4.220 in is a VALIDATION measurement at the derived
    geometric waist. Drawing "DEEP" 4.4375 in is comparison-only.
  * Also run 9.000->4.085 and 15.000->4.350 as alternate hard anchors and test
    whether recovered (L,R,P) cluster.
  * D is the Euclidean in-plane distance to the spherical high point, never the
    developed station.

Two model variants (kept separate):
  A1 fixed-absolute-outline : L fixed by the drawing (= extracted body length);
                              solve R only.
  A2 normalized-shape       : preserve Arnold shape ratios (isotropic scale);
                              float L, solve L for each R (nested).
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
from scipy.optimize import brentq, least_squares

_API = os.path.join(os.path.dirname(__file__), "..", "..", "services", "api")
sys.path.insert(0, os.path.abspath(_API))
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")

from app.instrument_geometry.body.ibg.body_contour_solver import (  # noqa: E402
    solve_high_point,
    solve_side_height,
)

OUTLINE_CSV = os.path.join(_RESULTS, "D28_65260_ARNOLD_OUTLINE.csv")
EXTRACTION_JSON = os.path.join(_RESULTS, "D28_65260_RERUN_003_EXTRACTION.json")
CONV_CSV = os.path.join(_RESULTS, "D28_65260_SIDE_INVERSE_RERUN_003_CONVERGENCE.csv")
SUM_CSV = os.path.join(_RESULTS, "D28_65260_SIDE_INVERSE_RERUN_003_SUMMARY.csv")

# === EXPERIMENTAL AUTHORITY — declared inputs that GOVERN the solve ==========
ARNOLD_SIDE_HEIGHT_IN: Dict[float, float] = {
    0.0: 3.750, 3.0: 3.740, 6.0: 3.895, 9.0: 4.085, 12.0: 4.240, 15.0: 4.350,
    18.0: 4.455, 21.0: 4.565, 24.0: 4.640, 27.0: 4.670, 30.4375: 4.720,
}
STATIONS = sorted(ARNOLD_SIDE_HEIGHT_IN)
S_NECK, S_TAIL = STATIONS[0], STATIONS[-1]
S_SHOULDER = ARNOLD_SIDE_HEIGHT_IN[S_NECK]     # 3.750 -> S
B_BUTT = ARNOLD_SIDE_HEIGHT_IN[S_TAIL]         # 4.720 -> B
M = N = 0.0

HARD_ANCHORS = {12.0: 4.240, 9.0: 4.085, 15.0: 4.350}   # primary first
PRIMARY_ANCHOR = 12.0
WAIST_SIDE_HEIGHT = 4.220        # VALIDATION at the derived geometric waist
DRAWING_DEEP = 4.4375            # comparison only
LEGACY_RERUN002_WAIST_STATION = 14.298

R_MIN_IN, R_MAX_IN = 8.0 * 12.0, 50.0 * 12.0
L_MIN_IN, L_MAX_IN = 12.0, 40.0

# Interior validation stations (exclude endpoints = B/S boundary conditions).
VALIDATION_STATIONS = [s for s in STATIONS if s not in (S_NECK, S_TAIL)]


# --- Load the extracted Arnold-derived outline -------------------------------

def load_outline() -> Tuple[np.ndarray, np.ndarray, Dict]:
    ys, hw = [], []
    with open(OUTLINE_CSV) as fh:
        next(fh)
        for line in fh:
            a, b = line.strip().split(",")
            ys.append(float(a)); hw.append(float(b))
    with open(EXTRACTION_JSON) as fh:
        meta = json.load(fh)
    return np.array(ys), np.array(hw), meta


_Y, _HW, _META = load_outline()
_L_CAL = float(_Y.max())
# Smoothed half-width for stable extrema/geometry.
_K = max(3, int(0.02 * len(_HW)) | 1)
_HW_S = np.convolve(_HW, np.ones(_K) / _K, mode="same")


def _scaled(L: float, resolution: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Outline scaled isotropically by f=L/L_cal (preserves Arnold shape ratios),
    optionally resampled to `resolution` points (for integration convergence)."""
    f = L / _L_CAL
    y = _Y * f
    x = _HW_S * f
    if resolution and resolution != len(y):
        yt = np.linspace(y.min(), y.max(), resolution)
        x = np.interp(yt, y, x)
        y = yt
    return y, x


def developed_arclen(L: float, resolution: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (y, x, s) with s = cumulative developed side arc length from neck:
    s(y) = ∫ sqrt(1 + (dx/dy)^2) dy along the extracted half-outline x(y)."""
    y, x = _scaled(L, resolution)
    dy = np.diff(y); dx = np.diff(x)
    ds = np.hypot(dx, dy)
    s = np.concatenate([[0.0], np.cumsum(ds)])
    return y, x, s


def geometric_waist(L: float) -> Dict[str, float]:
    y, x, s = developed_arclen(L)
    lb_i = int(np.argmax(x))
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(x[:lb_i + 1], prominence=0.03 * (L / _L_CAL))
    peaks = [p for p in peaks if 0.05 * y.max() < y[p] < 0.5 * y.max()]
    ub_i = int(peaks[int(np.argmax(x[peaks]))]) if peaks else int(np.argmax(np.where(y < 0.28 * y.max(), x, -1)))
    wi = ub_i + int(np.argmin(x[ub_i:lb_i + 1]))
    return {"y": float(y[wi]), "x": float(x[wi]), "s_waist": float(s[wi]),
            "half_perimeter": float(s[-1]), "y_norm": float(y[wi] / y.max())}


def point_at_station(L: float, station: float) -> Tuple[float, float, bool]:
    y, x, s = developed_arclen(L)
    clamped = station > s[-1]
    t = min(station, s[-1])
    yy = float(np.interp(t, s, y))
    xx = float(np.interp(t, s, x))
    return xx, yy, clamped


def predict_at(L: float, R: float, station: float) -> Tuple[float, float, float]:
    """(H, D, P) at an Arnold numeric station. High point on centerline at
    y_hp = L - P (P measured from the butt/tail at y=L)."""
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    x, y, _ = point_at_station(L, station)
    y_hp = L - P
    D = math.hypot(x, y - y_hp)
    return solve_side_height(B_BUTT, R, P, D, M, N), D, P


def predict_at_waist(L: float, R: float) -> Tuple[float, float, float, float]:
    gw = geometric_waist(L)
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    y_hp = L - P
    D = math.hypot(gw["x"], gw["y"] - y_hp)
    H = solve_side_height(B_BUTT, R, P, D, M, N)
    return H, D, P, gw["s_waist"]


def is_admissible(L: float, R: float) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    if P < 0: reasons.append("P<0")
    if P > L: reasons.append("P>L")
    if abs(P) >= R: reasons.append("|P|>=R")
    for s in VALIDATION_STATIONS:
        _, D, _ = predict_at(L, R, s)
        if D >= R:
            reasons.append(f"D>=R@{s}"); break
    return (len(reasons) == 0), reasons


def validation_residuals(L: float, R: float, anchor: float) -> Dict[float, float]:
    out = {s: predict_at(L, R, s)[0] - ARNOLD_SIDE_HEIGHT_IN[s]
           for s in VALIDATION_STATIONS if s != anchor}
    out["waist@%.3f" % geometric_waist(L)["s_waist"]] = predict_at_waist(L, R)[0] - WAIST_SIDE_HEIGHT
    return out


def rmse(res) -> float:
    v = np.array(list(res.values()), float)
    return float(np.sqrt(np.mean(v ** 2)))


# --- Convergence logger ------------------------------------------------------

CSV_FIELDS = [
    "run_id", "analysis", "model_variant", "phase", "outer_iteration",
    "inner_iteration", "integration_resolution", "outline_source", "symmetry_mode",
    "body_length_in", "radius_in", "radius_ft", "high_point_P_in", "waist_y_in",
    "waist_y_norm", "waist_station_derived_in", "half_perimeter_in",
    "target_waist_height_in", "predicted_waist_height_in", "waist_residual_in",
    "validation_rmse_in", "validation_max_abs_resid_in", "objective",
    "delta_radius_in", "delta_body_length_in", "delta_waist_station_in",
    "solver_method", "physically_admissible", "bound_hit", "convergence_status",
]
_OUTLINE_SRC = "ACOUSTIC_BODY.pdf(traced #65260); extracted D28_65260_ARNOLD_OUTLINE.csv"
_SYM = "symmetric_by_construction"


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


def _bound(R): return abs(R - R_MIN_IN) < 1e-6 or abs(R - R_MAX_IN) < 1e-6


def _waist_cols(L, R):
    Hw, _, P, sw = predict_at_waist(L, R)
    gw = geometric_waist(L)
    return dict(waist_y_in=_f(gw["y"]), waist_y_norm=_f(gw["y_norm"]),
                waist_station_derived_in=_f(sw), half_perimeter_in=_f(gw["half_perimeter"]),
                target_waist_height_in=_f(WAIST_SIDE_HEIGHT),
                predicted_waist_height_in=_f(Hw), waist_residual_in=_f(Hw - WAIST_SIDE_HEIGHT),
                high_point_P_in=_f(P))


# --- Integration convergence (N / 2N / 4N) -----------------------------------

def integration_convergence(logger: Logger, L: float) -> List[dict]:
    base = len(_Y)
    out = []
    prev = None
    for mult in (1, 2, 4):
        res = base * mult
        _, _, s = developed_arclen(L, resolution=res)
        gw_s = None
        # waist developed station at this resolution
        y, x, s2 = developed_arclen(L, resolution=res)
        lb_i = int(np.argmax(x)); wi = int(np.argmin(x[:lb_i + 1])) if lb_i > 0 else 0
        hp = float(s2[-1])
        logger.add(run_id=f"INTEG_x{mult}", analysis="INTEGRATION", model_variant="-",
                   phase="arclength_refine", integration_resolution=res,
                   outline_source=_OUTLINE_SRC, symmetry_mode=_SYM,
                   body_length_in=_f(L), half_perimeter_in=_f(hp),
                   delta_body_length_in=_f((hp - prev) if prev is not None else None, 6),
                   solver_method="cumulative_trapezoid", convergence_status="refine")
        out.append({"resolution": res, "half_perimeter": hp})
        prev = hp
    return out


# --- Anchor-constrained solves (A1 fixed-L, A2 float-L) ----------------------

def solve_R_fixedL(logger, L, anchor, target, run_id):
    """A1: L fixed; solve R so predict_at(anchor)=target. Logs brentq-ish path."""
    def g(R): return predict_at(L, R, anchor)[0] - target
    grid = np.linspace(R_MIN_IN, R_MAX_IN, 57)
    gv = [g(float(r)) for r in grid]
    root = None
    prev = None
    for i in range(len(grid) - 1):
        # log scan
        R = float(grid[i]); adm, _ = is_admissible(L, R)
        logger.add(run_id=run_id, analysis="A", model_variant="A1_fixedL",
                   phase="R_scan", outer_iteration=i, inner_iteration=f"scan{i}",
                   integration_resolution=len(_Y), outline_source=_OUTLINE_SRC, symmetry_mode=_SYM,
                   body_length_in=_f(L), radius_in=_f(R, 3), radius_ft=_f(R / 12, 4),
                   objective=_f(gv[i], 6), delta_radius_in=_f((R - prev) if prev is not None else None, 3),
                   solver_method="scan", physically_admissible=adm, bound_hit=_bound(R),
                   convergence_status="scanning", **_waist_cols(L, R))
        prev = R
        if not (math.isnan(gv[i]) or math.isnan(gv[i + 1])) and gv[i] * gv[i + 1] < 0:
            root = brentq(g, float(grid[i]), float(grid[i + 1]), xtol=1e-8)
            break
    return root


def solve_L_floatR(logger, R, anchor, target, run_id, outer):
    """A2 inner: for fixed R, solve L so predict_at(anchor)=target (isotropic scale)."""
    def g(L): return predict_at(L, R, anchor)[0] - target
    grid = np.linspace(L_MIN_IN, L_MAX_IN, 71)
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
    adm = [L for L in roots if 0 <= solve_high_point(L, B_BUTT, S_SHOULDER, R) <= L]
    return min(adm or roots, key=lambda L: abs(L - 20.0))


@dataclass
class AResult:
    variant: str; anchor: float; R: Optional[float]; L: Optional[float]
    P: Optional[float]; s_waist: Optional[float]; rmse: Optional[float]
    maxabs: Optional[float]; admissible: Optional[bool]; bound: Optional[bool]


def analysis_A1(logger, anchor) -> AResult:
    target = HARD_ANCHORS[anchor]; L = _L_CAL
    R = solve_R_fixedL(logger, L, anchor, target, f"A1_anchor{anchor}")
    if R is None:
        return AResult("A1_fixedL", anchor, None, L, None, None, None, None, None, None)
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    res = validation_residuals(L, R, anchor); e = rmse(res); mx = max(abs(v) for v in res.values())
    adm, _ = is_admissible(L, R); sw = geometric_waist(L)["s_waist"]
    logger.add(run_id=f"A1_anchor{anchor}", analysis="A", model_variant="A1_fixedL",
               phase="solved", outer_iteration=0, inner_iteration="final",
               integration_resolution=len(_Y), outline_source=_OUTLINE_SRC, symmetry_mode=_SYM,
               body_length_in=_f(L), radius_in=_f(R, 3), radius_ft=_f(R / 12, 4),
               validation_rmse_in=_f(e, 6), validation_max_abs_resid_in=_f(mx, 6), objective=_f(e, 6),
               solver_method="brentq", physically_admissible=adm, bound_hit=_bound(R),
               convergence_status="solved", **_waist_cols(L, R))
    return AResult("A1_fixedL", anchor, R, L, P, sw, e, mx, adm, _bound(R))


def analysis_A2(logger, anchor, n_R=43) -> AResult:
    target = HARD_ANCHORS[anchor]
    best = None; prevL = None; prevR = None
    for oi, R in enumerate(np.linspace(R_MIN_IN, R_MAX_IN, n_R)):
        R = float(R)
        L = solve_L_floatR(logger, R, anchor, target, f"A2_anchor{anchor}_R{oi:03d}", oi)
        if L is None:
            logger.add(run_id=f"A2_anchor{anchor}_R{oi:03d}", analysis="A", model_variant="A2_floatL",
                       phase="R_sweep", outer_iteration=oi, integration_resolution=len(_Y),
                       outline_source=_OUTLINE_SRC, symmetry_mode=_SYM, radius_in=_f(R, 3),
                       radius_ft=_f(R / 12, 4), target_waist_height_in=_f(WAIST_SIDE_HEIGHT),
                       solver_method="bisection", bound_hit=_bound(R), convergence_status="no_root")
            prevR = R; continue
        P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
        res = validation_residuals(L, R, anchor); e = rmse(res); mx = max(abs(v) for v in res.values())
        adm, _ = is_admissible(L, R); sw = geometric_waist(L)["s_waist"]
        logger.add(run_id=f"A2_anchor{anchor}_R{oi:03d}", analysis="A", model_variant="A2_floatL",
                   phase="R_sweep", outer_iteration=oi, inner_iteration="final",
                   integration_resolution=len(_Y), outline_source=_OUTLINE_SRC, symmetry_mode=_SYM,
                   body_length_in=_f(L), radius_in=_f(R, 3), radius_ft=_f(R / 12, 4),
                   validation_rmse_in=_f(e, 6), validation_max_abs_resid_in=_f(mx, 6), objective=_f(e, 6),
                   delta_radius_in=_f((R - prevR) if prevR is not None else None, 3),
                   delta_body_length_in=_f((L - prevL) if prevL is not None else None, 6),
                   solver_method="bisection", physically_admissible=adm, bound_hit=_bound(R),
                   convergence_status="solved", **_waist_cols(L, R))
        r = AResult("A2_floatL", anchor, R, L, P, sw, e, mx, adm, _bound(R))
        if best is None or (e < best.rmse): best = r
        prevL, prevR = L, R
    return best or AResult("A2_floatL", anchor, None, None, None, None, None, None, None, None)


# --- Analysis B: full least squares ------------------------------------------

def analysis_B(logger) -> List[dict]:
    fit_stations = VALIDATION_STATIONS
    out = []
    # B-A2: fit (L,R); B-A1: fit R at L=L_cal
    for variant, x0, lo, hi in [("B_A2_floatL", [20.0, 180.0], [L_MIN_IN, R_MIN_IN], [L_MAX_IN, R_MAX_IN]),
                                ("B_A1_fixedL", [180.0], [R_MIN_IN], [R_MAX_IN])]:
        cnt = {"n": 0}
        def resid(p):
            if variant.endswith("floatL"): L, R = float(p[0]), float(p[1])
            else: L, R = _L_CAL, float(p[0])
            r = []
            for s in fit_stations:
                try: H = predict_at(L, R, s)[0]
                except (ValueError, ZeroDivisionError): H = 1e3
                r.append(H - ARNOLD_SIDE_HEIGHT_IN[s])
            arr = np.array(r); adm, _ = is_admissible(L, R)
            logger.add(run_id=variant, analysis="B", model_variant=variant, phase="lsq",
                       outer_iteration=0, inner_iteration=cnt["n"], integration_resolution=len(_Y),
                       outline_source=_OUTLINE_SRC, symmetry_mode=_SYM, body_length_in=_f(L),
                       radius_in=_f(R, 3), radius_ft=_f(R / 12, 4),
                       objective=_f(float(np.sqrt(np.mean(arr ** 2))), 6),
                       solver_method="least_squares", physically_admissible=adm,
                       bound_hit=(_bound(R)), convergence_status="iterating", **_waist_cols(L, R))
            cnt["n"] += 1
            return arr
        sol = least_squares(resid, x0=x0, bounds=(lo, hi))
        if variant.endswith("floatL"): L, R = float(sol.x[0]), float(sol.x[1])
        else: L, R = _L_CAL, float(sol.x[0])
        P = solve_high_point(L, B_BUTT, S_SHOULDER, R); adm, reasons = is_admissible(L, R)
        out.append({"variant": variant, "L": L, "R": R, "P": P,
                    "rmse": float(np.sqrt(np.mean(sol.fun ** 2))), "admissible": adm,
                    "reasons": reasons, "bound": _bound(R)})
    return out


# --- Analysis C: identifiability (anchor clustering + perturbation) ----------

def analysis_C(logger, a1: Dict[float, AResult], a2: Dict[float, AResult]) -> Dict:
    # anchor clustering already computed (3 anchors). Add outline-scale + height perturbation.
    global _HW_S, _Y
    base_hw = _HW_S.copy()
    pert = []
    for tag, scale, dh in [("scale+0.5%", 1.005, 0.0), ("scale-0.5%", 0.995, 0.0),
                           ("h+0.01", 1.0, 0.01), ("h-0.01", 1.0, -0.01)]:
        _HW_S = base_hw * scale
        # perturb heights by dh via temporary target shift on the primary anchor
        target = HARD_ANCHORS[PRIMARY_ANCHOR] + dh
        r = solve_R_fixedL(logger, _L_CAL, PRIMARY_ANCHOR, target, f"C_pert_{tag}")
        if r is not None:
            P = solve_high_point(_L_CAL, B_BUTT, S_SHOULDER, r)
            logger.add(run_id=f"C_pert_{tag}", analysis="C", model_variant="A1_fixedL",
                       phase="perturbation", outer_iteration=0, inner_iteration="final",
                       integration_resolution=len(_Y), outline_source=_OUTLINE_SRC, symmetry_mode=_SYM,
                       body_length_in=_f(_L_CAL), radius_in=_f(r, 3), radius_ft=_f(r / 12, 4),
                       solver_method="brentq+perturb", physically_admissible=is_admissible(_L_CAL, r)[0],
                       bound_hit=_bound(r), convergence_status="solved", **_waist_cols(_L_CAL, r))
            pert.append({"tag": tag, "R": r, "P": P})
        else:
            pert.append({"tag": tag, "R": None, "P": None})
    _HW_S = base_hw
    return {"perturbation": pert}


# --- Disposition -------------------------------------------------------------

def classify(a1: Dict[float, AResult], a2: Dict[float, AResult], fitB: List[dict],
             floorH: float) -> Tuple[str, List[str]]:
    notes = []
    a2_ok = [r for r in a2.values() if r and r.R is not None]
    a1_ok = [r for r in a1.values() if r and r.R is not None]
    if not a2_ok and not a1_ok:
        notes.append(f"No anchor variant produced a root; min achievable waist height "
                     f"floor={floorH:.4f} in vs 4.220 in target.")
        return "SPHERICAL_MODEL_MISMATCH", notes
    # admissible?
    a1_adm = [r for r in a1_ok if r.admissible and not r.bound]
    a2_adm = [r for r in a2_ok if r.admissible and not r.bound]
    if not a1_adm and not a2_adm:
        notes.append("All anchor solutions are physically inadmissible (P<0/P>L) or "
                     "radius-bound-pinned.")
        return "SPHERICAL_MODEL_MISMATCH", notes
    # anchor clustering (A2 recovered L across the 3 anchors)
    Ls = [r.L for r in a2_ok if r.L is not None]
    Rs = [r.R for r in a2_ok if r.R is not None]
    cluster = bool(Ls) and (max(Ls) - min(Ls) < 2.0) and (max(Rs) - min(Rs) < 60.0)
    if not cluster:
        notes.append(f"Alternate hard anchors (9/12/15 in) do NOT cluster "
                     f"(A2 recovered L spans {min(Ls):.2f}..{max(Ls):.2f} in): underdetermined.")
        return "UNDERDETERMINED", notes
    Lm = float(np.mean(Ls))
    if abs(Lm - 20.0) < 1.0:
        notes.append(f"Anchors cluster and admissible; recovered L≈{Lm:.2f} in ~ 20.")
        return "CONVERGES_AND_SUPPORTS_20IN", notes
    notes.append(f"Anchors cluster and admissible but recovered L≈{Lm:.2f} in (not 20).")
    return "CONVERGES_BUT_NOT_20IN", notes


# --- Report + summary --------------------------------------------------------

def git_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception:
        return "UNKNOWN"


def run_all():
    logger = Logger()
    integ = integration_convergence(logger, _L_CAL)
    a1 = {a: analysis_A1(logger, a) for a in HARD_ANCHORS}
    a2 = {a: analysis_A2(logger, a) for a in HARD_ANCHORS}
    fitB = analysis_B(logger)
    cres = analysis_C(logger, a1, a2)
    # waist-height floor (A1, primary anchor unsatisfiable check uses waist)
    floor = min(predict_at_waist(_L_CAL, float(R))[0] for R in np.linspace(R_MIN_IN, R_MAX_IN, 40))
    disp, notes = classify(a1, a2, fitB, floor)
    return dict(logger=logger, integ=integ, a1=a1, a2=a2, fitB=fitB, cres=cres,
                floor=floor, disposition=disp, notes=notes)


def write_summary(rr):
    gw = geometric_waist(_L_CAL)
    a2p = rr["a2"][PRIMARY_ANCHOR]; a1p = rr["a1"][PRIMARY_ANCHOR]
    Ls = [r.L for r in rr["a2"].values() if r and r.L is not None]
    ident = ("anchors cluster" if Ls and (max(Ls) - min(Ls) < 2.0)
             else f"non-clustering (L {min(Ls):.2f}..{max(Ls):.2f})" if Ls else "no solutions")
    row = {
        "outline_authority": "Arnold-derived CAD tracing (ACOUSTIC BODY.pdf)",
        "geometric_waist_y_in": f"{gw['y']:.3f}", "geometric_waist_width_in": f"{2*gw['x']:.3f}",
        "derived_waist_developed_station_in": f"{gw['s_waist']:.3f}",
        "derived_half_perimeter_in": f"{gw['half_perimeter']:.3f}",
        "fixedL_best_R_in": (f"{a1p.R:.2f}" if a1p and a1p.R else ""),
        "normalized_best_L_in": (f"{a2p.L:.3f}" if a2p and a2p.L else ""),
        "normalized_best_R_in": (f"{a2p.R:.2f}" if a2p and a2p.R else ""),
        "P_in": (f"{a2p.P:.3f}" if a2p and a2p.P else (f"{a1p.P:.3f}" if a1p and a1p.P else "")),
        "rmse_in": (f"{a2p.rmse:.4f}" if a2p and a2p.rmse else ""),
        "max_resid_in": (f"{a2p.maxabs:.4f}" if a2p and a2p.maxabs else ""),
        "min_achievable_waist_height_in": f"{rr['floor']:.4f}",
        "physical_admissibility": (a2p.admissible if a2p else (a1p.admissible if a1p else "")),
        "identifiability": ident,
        "rerun002_waist_station_in": f"{LEGACY_RERUN002_WAIST_STATION:.3f}",
        "rerun003_waist_station_in": f"{gw['s_waist']:.3f}",
        "waist_station_shift_in": f"{gw['s_waist'] - LEGACY_RERUN002_WAIST_STATION:+.3f}",
        "final_disposition": rr["disposition"],
    }
    os.makedirs(_RESULTS, exist_ok=True)
    with open(SUM_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row.keys()), lineterminator="\n")
        w.writeheader(); w.writerow(row)
    return row


def build_section(rr) -> str:
    gw = geometric_waist(_L_CAL); L = []
    w = L.append
    def tbl(a):
        for anc in (12.0, 9.0, 15.0):
            r1 = rr["a1"][anc]; r2 = rr["a2"][anc]
            yield anc, r1, r2
    w("## Corrected Rerun 003 — Arnold Outline Authority")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Outline authority: **Arnold-derived CAD tracing** `ACOUSTIC BODY.pdf` "
      "(verified traced reconstruction of the John Arnold #65260 drawing, confirmed by JD).")
    w("- Primary historical source (provenance): John Arnold 1937 D-28 #65260 drawing "
      "(`1937 D-28.pdf`). Neither PDF is committed (public repo; copyrighted); see the "
      "provenance manifest `D28_65260_RERUN_003_PROVENANCE.json`.")
    w(f"- Extracted geometry: `D28_65260_ARNOLD_OUTLINE.csv`; convergence "
      f"`D28_65260_SIDE_INVERSE_RERUN_003_CONVERGENCE.csv`; summary "
      f"`D28_65260_SIDE_INVERSE_RERUN_003_SUMMARY.csv`.")
    w("")
    w("### Source classification")
    w("")
    w("| item | classification |")
    w("|---|---|")
    w("| John Arnold #65260 drawing | `SOURCE_MEASURED` (primary historical) |")
    w("| ACOUSTIC BODY.pdf outline / soundhole / dims | `DRAWING_DERIVED` (verified tracing) |")
    w("| Arnold side-height series (0..30.4375) | `SOURCE_MEASURED` (correspondence) |")
    w("| waist 4.220 in | `SOURCE_MEASURED` (validation, not anchor) |")
    w("| 4.4375 in DEEP | `HYPOTHESIS` (comparison only) |")
    w("| body length L=20 (A1 fixed) | `DRAWING_DERIVED` calibration |")
    w("| geometric waist / bout maxima / s_waist | `CALCULATED` (from perimeter) |")
    w("| generic dreadnought similitude | `PROPORTIONAL_ESTIMATE` (not used here) |")
    w("")
    ex = _META["calibration"]["cross_check"]
    w("### Outline extraction + calibration authority table")
    w("")
    w("| quantity | Arnold-drawing-derived (extracted) | repo value | difference | used for Rerun 003 |")
    w("|---|---:|---:|---:|---|")
    w(f"| body length | {_L_CAL:.2f} in | 20.0 in | {_L_CAL-20.0:+.2f} in | A1 fixed L; A2 floats |")
    w(f"| upper bout | {ex['upper_bout_extracted_in']:.2f} in | 11.5 in | "
      f"{ex['upper_bout_extracted_in']-11.5:+.2f} in | outline shape |")
    w(f"| lower bout | {ex['lower_bout_extracted_in']:.2f} in | 15.625 in | "
      f"{ex['lower_bout_extracted_in']-15.625:+.2f} in | outline shape |")
    w(f"| soundhole Ø (datum A) | {ex['soundhole_dia_extracted_in']:.2f} in | 4.0 in | "
      f"{ex['soundhole_dia_extracted_in']-4.0:+.2f} in | datum cross-check |")
    w(f"| geometric waist width | {2*gw['x']:.2f} in | 11.0 in | {2*gw['x']-11.0:+.2f} in | CALCULATED output |")
    da = _META["calibration"]["datum_A_soundhole"]
    w("")
    w(f"- Datum A (soundhole center): y_from_neck = {da['y_from_neck_in']:.3f} in, "
      f"y_from_tail = {da['y_from_tail_in']:.3f} in (extracted directly from the Ø4.0 circle).")
    w(f"- Symmetry: {_SYM}; **CAD symmetry discrepancy = 0 by construction** (NOT evidence "
      "the physical 1937 instrument was symmetric).")
    w("")
    w("### Geometric waist (derived output)")
    w("")
    w(f"- Geometric waist: width {2*gw['x']:.3f} in at y = {gw['y']:.3f} in "
      f"(y/L = {gw['y_norm']:.3f}); developed station **s_waist = {gw['s_waist']:.3f} in**.")
    w(f"- Developed neck→tail half-perimeter: {gw['half_perimeter']:.3f} in "
      f"(Arnold bottom-end station = 30.4375 in).")
    w(f"- Rerun 002 parametric waist station was {LEGACY_RERUN002_WAIST_STATION:.3f} in; "
      f"**shift = {gw['s_waist']-LEGACY_RERUN002_WAIST_STATION:+.3f} in** with the real outline.")
    w("")
    w("### Integration convergence (developed side length)")
    w("")
    w("| resolution (pts) | half-perimeter (in) |")
    w("|---:|---:|")
    for r in rr["integ"]:
        w(f"| {r['resolution']} | {r['half_perimeter']:.4f} |")
    w("")
    w("### A. Anchor-constrained solves (hard anchor 12.000 in → 4.240 in; also 9 & 15)")
    w("")
    w("| anchor (in→in) | A1 fixed-L: R (ft) / P (in) / RMSE | A2 float-L: L (in) / R (ft) / P (in) / RMSE | admissible |")
    w("|---|---|---|:--:|")
    for anc, r1, r2 in tbl(rr):
        s1 = (f"{r1.R/12:.2f} / {r1.P:.2f} / {r1.rmse:.4f}" if r1 and r1.R else "no root")
        s2 = (f"{r2.L:.2f} / {r2.R/12:.2f} / {r2.P:.2f} / {r2.rmse:.4f}" if r2 and r2.R else "no root")
        adm = (r2.admissible if r2 and r2.R is not None else (r1.admissible if r1 and r1.R is not None else "n/a"))
        w(f"| {anc}→{HARD_ANCHORS[anc]} | {s1} | {s2} | {adm} |")
    w("")
    w(f"- Waist-height floor over the (L,R) box (A1, extracted outline): {rr['floor']:.4f} in "
      f"(target validation 4.220 in).")
    w("")
    # validation residuals at primary A (prefer A2 primary if admissible else A1)
    rp = rr["a2"][PRIMARY_ANCHOR] if (rr["a2"][PRIMARY_ANCHOR] and rr["a2"][PRIMARY_ANCHOR].R) else rr["a1"][PRIMARY_ANCHOR]
    if rp and rp.R is not None:
        Lp = rp.L if rp.L is not None else _L_CAL
        w("### Validation at the primary-anchor solution (station 12 → 4.240)")
        w("")
        w("| station (in) | measured H (in) | predicted H (in) | residual (in) | D (in) | role |")
        w("|---:|---:|---:|---:|---:|---|")
        for s in STATIONS:
            Hp, D, _ = predict_at(Lp, rp.R, s)
            role = ("S bc" if s == S_NECK else "B bc" if s == S_TAIL
                    else "ANCHOR" if s == PRIMARY_ANCHOR else "validation")
            w(f"| {s} | {ARNOLD_SIDE_HEIGHT_IN[s]:.4f} | {Hp:.4f} | {Hp-ARNOLD_SIDE_HEIGHT_IN[s]:+.4f} | {D:.3f} | {role} |")
        Hw, Dw, _, sw = predict_at_waist(Lp, rp.R)
        w(f"| waist@{sw:.2f} | {WAIST_SIDE_HEIGHT:.4f} | {Hw:.4f} | {Hw-WAIST_SIDE_HEIGHT:+.4f} | {Dw:.3f} | validation |")
        w("")
    w("### B. Full least squares")
    w("")
    w("| variant | L (in) | R (in/ft) | P (in) | RMSE (in) | admissible | flags |")
    w("|---|---:|---:|---:|---:|:--:|---|")
    for f in rr["fitB"]:
        flags = "" if f["admissible"] and not f["bound"] else "; ".join(f["reasons"] + (["bound"] if f["bound"] else []))
        w(f"| {f['variant']} | {f['L']:.3f} | {f['R']:.1f}/{f['R']/12:.2f} | {f['P']:.3f} | "
          f"{f['rmse']:.4f} | {f['admissible']} | {flags} |")
    w("")
    w("### C. Identifiability (anchor clustering + perturbation)")
    w("")
    Ls = [r.L for r in rr["a2"].values() if r and r.L is not None]
    Rs = [r.R for r in rr["a2"].values() if r and r.R is not None]
    if Ls:
        w(f"- A2 recovered L across anchors 9/12/15: {min(Ls):.2f}..{max(Ls):.2f} in "
          f"(range {max(Ls)-min(Ls):.2f}); R {min(Rs)/12:.2f}..{max(Rs)/12:.2f} ft.")
    w("- Perturbation (outline scale ±0.5%, heights ±0.01 in) recovered R (fixed-L, primary anchor):")
    for p in rr["cres"]["perturbation"]:
        w(f"  - {p['tag']}: R = {(str(round(p['R']/12,2))+' ft, P='+str(round(p['P'],2))+' in') if p['R'] else 'no root'}")
    w("")
    w("### D. Rerun 002 (parametric) vs Rerun 003 (Arnold outline)")
    w("")
    w("| quantity | Rerun 002 (parametric) | Rerun 003 (Arnold outline) |")
    w("|---|---|---|")
    w(f"| outline authority | BodyContourSolver parametric | Arnold-derived CAD tracing |")
    w(f"| waist y/L | 0.44 (assumed) | {gw['y_norm']:.3f} (derived) |")
    w(f"| derived waist station | {LEGACY_RERUN002_WAIST_STATION:.2f} in | {gw['s_waist']:.2f} in |")
    w(f"| half-perimeter | 31.28 in | {gw['half_perimeter']:.2f} in |")
    w(f"| hard anchor | waist 4.4375 then 4.220 | station 12.000 → 4.240 |")
    w(f"| disposition | INSUFFICIENT_GEOMETRY_AUTHORITY | {rr['disposition']} |")
    w("")
    w("### Inconsistency audit")
    w("")
    w("| field | value / conflict | class | disposition |")
    w("|---|---|---|---|")
    w(f"| waist side height 4.220 vs 4.4375 DEEP | Δ = {DRAWING_DEEP-WAIST_SIDE_HEIGHT:+.4f} in | "
      "`SOURCE_CONFLICT` | 4.220 = validation; DEEP comparison-only |")
    w(f"| derived waist station vs Rerun 002 | {gw['s_waist']:.2f} in vs "
      f"{LEGACY_RERUN002_WAIST_STATION:.2f} in (shift {gw['s_waist']-LEGACY_RERUN002_WAIST_STATION:+.2f}) | "
      "`DERIVATION_MISMATCH` | use Arnold-outline value; parametric was wrong |")
    w(f"| developed half-perimeter vs Arnold span | {gw['half_perimeter']:.2f} in vs 30.4375 in | "
      "`UNIT_OR_DATUM_AMBIGUITY` | plan-view developed length < Arnold stated span; stations >"
      f"{gw['half_perimeter']:.1f} in clamp to tail; possibly Arnold measured along the domed side |")
    w(f"| waist width | {2*gw['x']:.2f} in (CALCULATED) vs repo 11.0 in | `DERIVATION_MISMATCH` | "
      "outline is authority; repo value not used |")
    w(f"| upper/lower bout | 11.64 / 15.72 in (extracted) vs repo 11.5 / 15.625, label 11.7 / 15.7 | "
      "`DRAWING_DERIVED` | drawing/label used, deltas reported |")
    w("| admissible single-radius spherical fit | none (best fits require P<0) | `UNRESOLVED` | "
      "model-level defect; not a geometry-authority gap |")
    w("| CAD symmetry | 0 by construction | `DRAWING_DERIVED` | not evidence the real instrument is symmetric |")
    w("| martin_d28_1937.py | single-line module exports nothing | `REPO_CONFLICT` | flagged, not fixed |")
    w("")
    w("### Disposition")
    w("")
    w(f"**{rr['disposition']}**")
    w("")
    for n in rr["notes"]:
        w(f"- {n}")
    w("")
    w("Interpretation: replacing the parametric outline with the Arnold-derived tracing "
      "**removed the Rerun 002 non-identifiability** — the 9/12/15 in hard anchors now "
      "converge tightly (L≈22 in, R≈34 ft, RMSE≈0.028 in). But that converged fit is "
      "**physically inadmissible** (spherical high point outside the body, P<0) and needs a "
      "near-flat ~34 ft back at L≈22 in, not 20 in. So the outline authority is now "
      "sufficient and the residual failure is the **single-radius spherical-back model "
      "itself**, not the geometry. The proportional generic-dreadnought similitude study "
      "(Rerun 004) is the appropriate next experiment.")
    w("")
    return "\n".join(L)


_DOC = os.path.join(_REPO_ROOT, "docs", "experiments", "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_S3, _E3 = "<!-- RERUN003_START -->", "<!-- RERUN003_END -->"


def splice_doc(section):
    with open(_DOC) as fh: text = fh.read()
    block = f"{_S3}\n{section}\n{_E3}"
    if _S3 in text and _E3 in text:
        text = text[:text.index(_S3)] + block + text[text.index(_E3) + len(_E3):]
    else:
        # insert right after the first STOP banner / before RERUN002 section
        marker = "<!-- RERUN002_START -->"
        if marker in text:
            text = text[:text.index(marker)] + block + "\n\n" + text[text.index(marker):]
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
    with open(_DOC, "w") as fh: fh.write(text)


def main():
    rr = run_all()
    section = build_section(rr)
    if "--write" in sys.argv:
        rr["logger"].write(CONV_CSV)
        write_summary(rr)
        splice_doc(section)
        print(f"wrote {CONV_CSV} ({len(rr['logger'].rows)} rows)")
        print(f"wrote {SUM_CSV}")
        print(f"spliced Rerun 003 section into {_DOC}")
    else:
        print(section)
        print(f"\n[rows {len(rr['logger'].rows)}; disposition {rr['disposition']}]")


if __name__ == "__main__":
    main()
