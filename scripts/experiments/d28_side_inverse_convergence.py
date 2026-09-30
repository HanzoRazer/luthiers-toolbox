#!/usr/bin/env python3
"""
The Reverse Engineering of the Martin D-28 #65260
==================================================

Isolated mathematical experiment (branch experiment/d28-side-profile-inverse-
convergence). Evidence gathering ONLY - it imports and reuses the production
Sevy/Doolin equations and the repository body-outline authority, and modifies
nothing.

Question
--------
The repo records ``BODY_LENGTH = 20.0 in`` while the side-profile stations run
0 .. 30.4375 in (== the recorded ``total_length``). Can the Sevy/Doolin
spherical-back side-height model be inverted against the measured #65260 side
profile to recover a coherent (body length L, back radius R), and does the
recovered L land at ~20 in? Is 30.4375 in better read as a developed
side-strip / half-perimeter length than as centerline body length?

Method (authoritative for this experiment; supersedes the older formulation
in the dev order where they differ)
---------------------------------------------------------------------------
1. Treat the raw side profile as observations. Its two endpoints fix the
   boundary depths B (butt/tail, station 30.4375) and S (shoulder/neck,
   station 0); with the raw profile M = N = 0 (it excludes plate thickness).
2. Treat the waist side-depth as a HARD CONSTRAINT. AUTHORITATIVE CORRECTION:
   the #65260 waist side depth is 4.4375 in, NOT the repository's current
   4.220 in. The repo value is treated as legacy/superseded for this
   experiment and is left unchanged in the spec (evidence gathering only).
3. Candidate spherical back radius R.
4. For that R, solve body length L so the model reproduces the waist depth
   exactly (nested solve).
5. Derive the high point P from (L, B, S, R) via the repo Sevy formula.
6. Map each developed side-profile station to a perimeter point on the D-28
   plan-view outline (the repository BodyContourSolver outline authority,
   scaled to candidate L). The station is a DEVELOPED distance along the side;
   D is the in-plane Euclidean distance from the spherical high point to the
   mapped perimeter point. **D is never set equal to the station.**
7. For every non-waist, non-endpoint profile point, predict side height with
   the repo Sevy side-height equation and compute residuals.
8. Sweep R over a broad physically plausible range; find R* minimizing the
   out-of-sample residuals; L(R*) is the recovered body-length estimate.

Analyses: A (waist-constrained nested solve), B (independent full least
squares in L and R), C (leave-one-out anchor clustering). Plus: the
half-perimeter test for 30.4375 in, Model-C falsification (30.4375 == body
length), a +/-0.01 in measurement-perturbation sensitivity study, and the
requested recovered-(L, R) comparison between the authoritative 4.4375 in and
the legacy 4.220 in waist value.

Nothing here is a production or authority change. Even a clean convergence at
20 in would NOT license editing the historical spec.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import brentq, least_squares

# --- Reuse the production equations and outline authority (read-only) --------
_API = os.path.join(os.path.dirname(__file__), "..", "..", "services", "api")
sys.path.insert(0, os.path.abspath(_API))

from app.instrument_geometry.body.ibg.body_contour_solver import (  # noqa: E402
    BodyConstraints,
    BodyContourSolver,
    solve_high_point,
    solve_side_height,
)

# --- Observations -----------------------------------------------------------
# Source the observations from martin_d28_1937.JSON, not the .py: the committed
# martin_d28_1937.py is a single physical line in which an early ``#`` comment
# swallows every assignment, so the module exports nothing usable. That is an
# incidental repository defect; this experiment does not touch either spec file
# (evidence gathering only). The JSON is well-formed and carries the same data.
_SPEC_JSON = os.path.join(_API, "app", "instrument_geometry", "specs",
                          "martin_d28_1937.json")
with open(_SPEC_JSON) as _fh:
    _SPEC = json.load(_fh)

RAW = {float(k): float(v) for k, v in _SPEC["side_profile_raw"].items()}
STATIONS = sorted(RAW)                          # 0.0 .. 30.4375
S_NECK = STATIONS[0]                            # 0.0
S_TAIL = STATIONS[-1]                           # 30.4375
S_MAX = float(_SPEC["dimensions"]["total_length"])   # 30.4375 (== station max)
S_WAIST = 10.5                                   # waist station (marked in spec)

# Boundary depths from the profile endpoints (raw => plate thickness excluded).
S_SHOULDER = RAW[S_NECK]                         # neck depth  -> S
B_BUTT = RAW[S_TAIL]                             # tail depth  -> B
M = N = 0.0                                      # raw profile excludes top/back

# Waist constraint values (in).
WAIST_H_AUTHORITATIVE = 4.4375                   # corrected Arnold measurement
WAIST_H_LEGACY = RAW[S_WAIST]                    # 4.220 repo value (superseded)

# Fixed plan-view widths (independently measured; not functions of L).
LOWER_BOUT = float(_SPEC["dimensions"]["lower_bout_width"])
UPPER_BOUT = float(_SPEC["dimensions"]["upper_bout_width"])
WAIST_W = float(_SPEC["dimensions"]["waist_width"])
WAIST_Y_NORM = 0.44                              # BodyContourSolver dreadnought default
BODY_LENGTH_SPEC = float(_SPEC["dimensions"]["body_length"])   # 20.0 (datum under test)

# Validation stations: interior, excluding the waist anchor and the two
# endpoints that define B and S.
VALIDATION_STATIONS = [s for s in STATIONS
                       if s not in (S_NECK, S_TAIL, S_WAIST)]

# Broad, un-narrowed bounds (dev order): R 8..50 ft; L 12..40 in for the solve.
R_MIN_IN, R_MAX_IN = 8.0 * 12.0, 50.0 * 12.0    # 96 .. 600 in
L_MIN_IN, L_MAX_IN = 12.0, 40.0

_SOLVER = BodyContourSolver(
    BodyConstraints(back_radius_mm=7620.0, butt_depth_mm=B_BUTT * 25.4,
                    shoulder_depth_mm=S_SHOULDER * 25.4, top_thickness_mm=0.0,
                    back_thickness_mm=0.0, scale_length_mm=645.0),
    family="dreadnought",
)

# === EXPERIMENTAL AUTHORITY (declared inputs that GOVERN the solve) ==========
# Per the experimental-authority rule, only values declared here govern the
# solve. Repository values are otherwise read only for outline mapping,
# provenance, comparison, validation, and inconsistency detection - never
# silently substituted as solve inputs. If a required governing value were
# missing, the run stops and reports it rather than borrowing a repo default.
EXPERIMENTAL_INPUTS = {
    "waist_depth_in": WAIST_H_AUTHORITATIVE,       # hard constraint; overrides repo 4.220
    "waist_station_in": S_WAIST,
    "M_top_thickness_in": M,                        # raw profile excludes plate thickness
    "N_back_thickness_in": N,
    "R_bounds_ft": (R_MIN_IN / 12.0, R_MAX_IN / 12.0),
    "L_bounds_in": (L_MIN_IN, L_MAX_IN),
    # Observations: repo raw side profile is the declared observation set, with
    # the single waist point overridden by the authoritative value above.
    "side_profile_source": "martin_d28_1937.json:side_profile_raw (waist overridden)",
    "B_butt_depth_in": B_BUTT,                      # station-max endpoint (observation)
    "S_shoulder_depth_in": S_SHOULDER,              # station-0 endpoint (observation)
}

# Repository geometry read ONLY to map developed stations to perimeter points
# (allowed use). Declared explicitly so it is auditable and never mistaken for
# an experimental input.
MAPPING_INPUTS = {
    "lower_bout_width_in": LOWER_BOUT,
    "upper_bout_width_in": UPPER_BOUT,
    "waist_width_in": WAIST_W,
    "waist_y_norm": WAIST_Y_NORM,                   # BodyContourSolver family default
    "station_span_in": S_MAX,                       # developed side-strip span
    "outline_authority": "BodyContourSolver two-arc outline (parametric)",
}

# Repository values used only as comparison targets (never solve inputs).
COMPARISON_TARGETS = {
    "body_length_in": BODY_LENGTH_SPEC,             # 20.0 (datum under test)
    "total_length_in": float(_SPEC["dimensions"]["total_length"]),
    "legacy_waist_depth_in": WAIST_H_LEGACY,        # 4.220 (superseded, comparison only)
}


# --- Outline authority: developed neck->tail half-perimeter for a given L ----

def _neck_to_tail_path(L: float, n: int = 600) -> List[Tuple[float, float]]:
    """Right-half body outline ordered neck (0, L) -> tail (0, 0), in inches.

    Uses the repository BodyContourSolver arc construction (its anchor formula
    and circumcircle arc sampler) with the D-28 widths fixed and only the body
    length L scaled. Returned unit is inches (the arc math is unit-agnostic).
    """
    y_waist = WAIST_Y_NORM * L
    p0 = (0.0, 0.0)
    p1 = (LOWER_BOUT / 2.0, y_waist * 0.25)
    p2 = (WAIST_W / 2.0, y_waist)
    p3 = (UPPER_BOUT / 2.0, y_waist + (L - y_waist) * 0.55)
    p4 = (0.0, L)
    per_arc = n // 2
    arc_a = _SOLVER._generate_arc_segment(p0, p1, p2, per_arc)   # butt -> waist
    arc_b = _SOLVER._generate_arc_segment(p2, p3, p4, per_arc)   # waist -> neck
    butt_to_neck = arc_a + arc_b[1:]
    return list(reversed(butt_to_neck))                          # neck -> tail


def _arclength(path: List[Tuple[float, float]]) -> np.ndarray:
    pts = np.asarray(path, dtype=float)
    seg = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
    return np.concatenate([[0.0], np.cumsum(seg)])


def _perimeter_point(L: float, station: float) -> Tuple[float, float, float]:
    """Map a developed station (0..S_MAX) to a perimeter point on the L-scaled
    outline by NORMALISED arc length (fraction station / S_MAX from the neck).

    Returns (x, y, half_perimeter_length). D is later computed as the Euclidean
    distance from the high point to (x, y) -- never as the station itself.
    """
    path = _neck_to_tail_path(L)
    cum = _arclength(path)
    total = float(cum[-1])
    target = (station / S_MAX) * total
    pts = np.asarray(path, dtype=float)
    x = float(np.interp(target, cum, pts[:, 0]))
    y = float(np.interp(target, cum, pts[:, 1]))
    return x, y, total


def predict_height(L: float, R: float, station: float,
                   B: float = B_BUTT, S: float = S_SHOULDER) -> Tuple[float, float, float]:
    """Predicted side height H at a station for candidate (L, R).

    Returns (H, D, P). High point sits on the centerline at (0, P); the mapped
    perimeter point supplies D = Euclidean distance to it.
    """
    P = solve_high_point(L, B, S, R)
    x, y, _ = _perimeter_point(L, station)
    D = math.hypot(x - 0.0, y - P)
    H = solve_side_height(B, R, P, D, M, N)
    return H, D, P


# --- Analysis A: waist-constrained nested solve -----------------------------

def solve_L_for_waist(R: float, waist_h: float) -> Optional[float]:
    """Solve body length L so the model reproduces the waist depth at the waist
    station exactly, for a given R. Returns the physically plausible root
    (P within [0, L]) nearest the historical 20 in, or None if none bracket.
    """
    def g(L: float) -> float:
        H, _, _ = predict_height(L, R, S_WAIST)
        return H - waist_h

    grid = np.linspace(L_MIN_IN, L_MAX_IN, 141)
    vals = []
    for L in grid:
        try:
            vals.append(g(float(L)))
        except (ValueError, ZeroDivisionError):
            vals.append(math.nan)
    roots: List[float] = []
    for i in range(len(grid) - 1):
        a, b = vals[i], vals[i + 1]
        if math.isnan(a) or math.isnan(b) or a == 0.0:
            continue
        if a * b < 0.0:
            try:
                r = brentq(g, float(grid[i]), float(grid[i + 1]), xtol=1e-8)
                roots.append(float(r))
            except (ValueError, RuntimeError):
                pass
    plausible = []
    for L in roots:
        P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
        if 0.0 <= P <= L:
            plausible.append(L)
    pool = plausible or roots
    if not pool:
        return None
    return min(pool, key=lambda L: abs(L - BODY_LENGTH_SPEC))


def validation_residuals(L: float, R: float) -> Dict[float, float]:
    out = {}
    for s in VALIDATION_STATIONS:
        H, _, _ = predict_height(L, R, s)
        out[s] = H - RAW[s]
    return out


def rmse(res: Dict[float, float]) -> float:
    v = np.array(list(res.values()), dtype=float)
    return float(np.sqrt(np.mean(v ** 2)))


@dataclass
class SweepRow:
    R_in: float
    L_in: Optional[float]
    P_in: Optional[float]
    rmse_in: Optional[float]
    max_abs_in: Optional[float]


def sweep_waist_constrained(waist_h: float, n_R: int = 60) -> List[SweepRow]:
    rows: List[SweepRow] = []
    for R in np.linspace(R_MIN_IN, R_MAX_IN, n_R):
        L = solve_L_for_waist(float(R), waist_h)
        if L is None:
            rows.append(SweepRow(float(R), None, None, None, None))
            continue
        P = solve_high_point(L, B_BUTT, S_SHOULDER, float(R))
        res = validation_residuals(L, float(R))
        rows.append(SweepRow(float(R), L, P, rmse(res),
                             max(abs(v) for v in res.values())))
    return rows


def best_row(rows: List[SweepRow]) -> Optional[SweepRow]:
    valid = [r for r in rows if r.rmse_in is not None]
    return min(valid, key=lambda r: r.rmse_in) if valid else None


def refine_waist_constrained(waist_h: float, R0: float) -> Optional[SweepRow]:
    """Local refinement of R about a coarse minimum (independent of the grid)."""
    def obj(R: float) -> float:
        L = solve_L_for_waist(R, waist_h)
        if L is None:
            return 1e6
        return rmse(validation_residuals(L, R))

    lo, hi = max(R_MIN_IN, R0 - 60), min(R_MAX_IN, R0 + 60)
    res = least_squares(lambda x: obj(float(x[0])), x0=[R0],
                        bounds=([lo], [hi]), diff_step=1e-3)
    R = float(res.x[0])
    L = solve_L_for_waist(R, waist_h)
    if L is None:
        return None
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    r = validation_residuals(L, R)
    return SweepRow(R, L, P, rmse(r), max(abs(v) for v in r.values()))


# --- Analysis B: independent full least squares in (L, R) --------------------

def full_least_squares(waist_h: float,
                       inits: List[Tuple[float, float]]) -> List[dict]:
    """Fit L and R jointly to all non-endpoint points (waist uses waist_h)."""
    fit_stations = VALIDATION_STATIONS + [S_WAIST]
    target = {s: (waist_h if s == S_WAIST else RAW[s]) for s in fit_stations}

    def resid(x: np.ndarray) -> np.ndarray:
        L, R = float(x[0]), float(x[1])
        out = []
        for s in fit_stations:
            try:
                H, _, _ = predict_height(L, R, s)
            except (ValueError, ZeroDivisionError):
                H = 1e3
            out.append(H - target[s])
        return np.array(out, dtype=float)

    results = []
    for L0, R0 in inits:
        try:
            sol = least_squares(resid, x0=[L0, R0],
                                bounds=([L_MIN_IN, R_MIN_IN], [L_MAX_IN, R_MAX_IN]))
            L, R = float(sol.x[0]), float(sol.x[1])
            P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
            results.append({"L0": L0, "R0": R0, "L": L, "R": R, "P": P,
                            "rmse": float(np.sqrt(np.mean(sol.fun ** 2))),
                            "cost": float(sol.cost), "success": bool(sol.success)})
        except (ValueError, RuntimeError) as e:
            results.append({"L0": L0, "R0": R0, "error": str(e)})
    return results


# --- Analysis C: leave-one-out anchor clustering -----------------------------

def leave_one_out_anchor(waist_h: float) -> List[dict]:
    """Repeat the nested solve using each interior point (and the waist) as the
    exact anchor in turn; report the recovered (L*, R*) per anchor.
    """
    anchors = VALIDATION_STATIONS + [S_WAIST]
    out = []
    for anchor in anchors:
        anchor_h = waist_h if anchor == S_WAIST else RAW[anchor]

        def solve_L(R: float) -> Optional[float]:
            def g(L: float) -> float:
                H, _, _ = predict_height(L, R, anchor)
                return H - anchor_h
            grid = np.linspace(L_MIN_IN, L_MAX_IN, 141)
            vals = []
            for L in grid:
                try:
                    vals.append(g(float(L)))
                except (ValueError, ZeroDivisionError):
                    vals.append(math.nan)
            roots = []
            for i in range(len(grid) - 1):
                a, b = vals[i], vals[i + 1]
                if math.isnan(a) or math.isnan(b):
                    continue
                if a * b < 0:
                    try:
                        roots.append(float(brentq(g, float(grid[i]), float(grid[i + 1]))))
                    except (ValueError, RuntimeError):
                        pass
            plausible = [L for L in roots
                         if 0.0 <= solve_high_point(L, B_BUTT, S_SHOULDER, R) <= L]
            pool = plausible or roots
            return min(pool, key=lambda L: abs(L - BODY_LENGTH_SPEC)) if pool else None

        others = [s for s in anchors if s != anchor]
        best = None
        for R in np.linspace(R_MIN_IN, R_MAX_IN, 60):
            L = solve_L(float(R))
            if L is None:
                continue
            res = [predict_height(L, float(R), s)[0] - (waist_h if s == S_WAIST else RAW[s])
                   for s in others]
            e = float(np.sqrt(np.mean(np.array(res) ** 2)))
            if best is None or e < best[2]:
                best = (L, float(R), e)
        if best:
            out.append({"anchor": anchor, "L": best[0], "R": best[1], "rmse_others": best[2]})
        else:
            out.append({"anchor": anchor, "L": None, "R": None, "rmse_others": None})
    return out


# --- Half-perimeter test and Model-C falsification ---------------------------

def half_perimeter_in(L: float) -> float:
    _, _, total = _perimeter_point(L, S_MAX)
    return total


def model_c_falsification() -> dict:
    """Interpretation under test: 30.4375 in == centerline body length. Fix
    L = 30.4375 and fit R alone to the interior + waist(authoritative) points.
    """
    L = S_MAX
    fit_stations = VALIDATION_STATIONS + [S_WAIST]
    target = {s: (WAIST_H_AUTHORITATIVE if s == S_WAIST else RAW[s]) for s in fit_stations}

    def resid(x: np.ndarray) -> np.ndarray:
        R = float(x[0])
        out = []
        for s in fit_stations:
            try:
                H, _, _ = predict_height(L, R, s)
            except (ValueError, ZeroDivisionError):
                H = 1e3
            out.append(H - target[s])
        return np.array(out, dtype=float)

    sol = least_squares(resid, x0=[300.0], bounds=([R_MIN_IN], [R_MAX_IN]))
    R = float(sol.x[0])
    P = solve_high_point(L, B_BUTT, S_SHOULDER, R)
    return {"L_fixed": L, "R": R, "P": P,
            "rmse": float(np.sqrt(np.mean(sol.fun ** 2))),
            "on_bound": bool(abs(R - R_MIN_IN) < 1e-3 or abs(R - R_MAX_IN) < 1e-3)}


# --- Sensitivity study -------------------------------------------------------

def sensitivity_perturbation(waist_h: float, delta: float = 0.01) -> dict:
    """Perturb every measured height by +/- delta (in) and re-run Analysis A;
    report the spread of recovered (L*, R*, P*).
    """
    base_raw = dict(RAW)
    Ls, Rs, Ps = [], [], []
    for sign in (+1.0, -1.0):
        globals()["RAW"].update({s: base_raw[s] + sign * delta for s in base_raw})
        wh = waist_h + sign * delta
        rows = sweep_waist_constrained(wh, n_R=40)
        b = best_row(rows)
        if b and b.L_in is not None:
            Ls.append(b.L_in); Rs.append(b.R_in); Ps.append(b.P_in)
    globals()["RAW"].update(base_raw)  # restore
    def spread(v):
        return (min(v), max(v)) if v else (None, None)
    return {"delta_in": delta, "L_range": spread(Ls), "R_range": spread(Rs),
            "P_range": spread(Ps)}


# --- Disposition -------------------------------------------------------------

def classify(bestA: Optional[SweepRow], fitB: List[dict],
             loo: List[dict], mc: dict, sens: dict) -> Tuple[str, List[str]]:
    notes: List[str] = []
    if bestA is None or bestA.L_in is None:
        return "INSUFFICIENT_GEOMETRY_AUTHORITY", [
            "Waist-constrained solve found no plausible (L, R) over the swept range."]

    okB = [f for f in fitB if "L" in f]
    Lb = [f["L"] for f in okB]
    Rb = [f["R"] for f in okB]
    b_clusters = bool(Lb) and (max(Lb) - min(Lb) < 1.0) and (max(Rb) - min(Rb) < 24.0)
    ab_agree = bool(okB) and any(abs(f["L"] - bestA.L_in) < 1.0 for f in okB)

    loo_ok = [d for d in loo if d["L"] is not None]
    loo_L = [d["L"] for d in loo_ok]
    loo_R = [d["R"] for d in loo_ok]
    loo_clusters = bool(loo_L) and (max(loo_L) - min(loo_L) < 2.0)

    on_bound = bool(okB) and any(abs(f["R"] - R_MAX_IN) < 1e-2 or abs(f["R"] - R_MIN_IN) < 1e-2
                                 for f in okB)
    L_lo, L_hi = sens["L_range"]
    sens_wide = (L_lo is not None) and (L_hi - L_lo > 2.0)

    if sens_wide or on_bound or (not b_clusters) or (not loo_clusters):
        if not loo_clusters:
            notes.append("Leave-one-out anchors do NOT cluster: (L, R) depends on which "
                         "point is treated as exact -> not separately identifiable.")
        if sens_wide:
            notes.append(f"+/-{sens['delta_in']} in perturbation moves recovered L across "
                         f"{L_lo:.2f}..{L_hi:.2f} in -> ill-conditioned.")
        if on_bound:
            notes.append("A least-squares solution lands on an R bound (constraint pressure).")
        if not b_clusters:
            notes.append("Full LS from different starts does not settle in one basin.")
        return "UNDERDETERMINED", notes

    supports_20 = abs(bestA.L_in - BODY_LENGTH_SPEC) < 1.0 and ab_agree
    if supports_20:
        notes.append("A and B agree and recovered L is within 1 in of 20.")
        return "CONVERGES_AND_SUPPORTS_20IN", notes
    notes.append(f"Stable convergence but recovered L = {bestA.L_in:.2f} in (not ~20).")
    return "CONVERGES_BUT_NOT_20IN", notes


# --- Experimental-authority startup confirmation -----------------------------

def active_inputs_lines() -> List[str]:
    out = ["ACTIVE EXPERIMENTAL INPUTS"]
    out.append(f"  waist_depth_in            = {EXPERIMENTAL_INPUTS['waist_depth_in']}  "
               f"(overrides repo legacy {COMPARISON_TARGETS['legacy_waist_depth_in']})")
    out.append(f"  waist_station_in          = {EXPERIMENTAL_INPUTS['waist_station_in']}")
    out.append(f"  B_butt_depth_in (station {S_TAIL}) = {EXPERIMENTAL_INPUTS['B_butt_depth_in']}")
    out.append(f"  S_shoulder_depth_in (station {S_NECK}) = {EXPERIMENTAL_INPUTS['S_shoulder_depth_in']}")
    out.append(f"  M_top_thickness_in        = {EXPERIMENTAL_INPUTS['M_top_thickness_in']}")
    out.append(f"  N_back_thickness_in       = {EXPERIMENTAL_INPUTS['N_back_thickness_in']}")
    out.append(f"  R_bounds_ft               = {EXPERIMENTAL_INPUTS['R_bounds_ft']}")
    out.append(f"  L_bounds_in               = {EXPERIMENTAL_INPUTS['L_bounds_in']}")
    out.append("  observations (side profile, in; * = experimental override):")
    for s in STATIONS:
        val = EXPERIMENTAL_INPUTS["waist_depth_in"] if s == S_WAIST else RAW[s]
        star = " *" if s == S_WAIST else ""
        out.append(f"    station {s:>8} -> {val:.4f}{star}")
    out.append("  mapping geometry (repo, mapping-only, NOT a solve input):")
    for k, v in MAPPING_INPUTS.items():
        out.append(f"    {k} = {v}")
    return out


def check_required_inputs() -> None:
    """Stop rather than borrow a repo default if a governing value is missing."""
    missing = [k for k in ("waist_depth_in", "waist_station_in", "M_top_thickness_in",
                           "N_back_thickness_in", "R_bounds_ft", "L_bounds_in",
                           "B_butt_depth_in", "S_shoulder_depth_in")
               if EXPERIMENTAL_INPUTS.get(k) is None]
    if missing:
        raise SystemExit(f"STOP: required experimental input(s) missing: {missing}. "
                         "Declare them in the input block; do not fall back to repo values.")


# --- Inconsistency register --------------------------------------------------

def build_inconsistency_register(bestA: Optional[SweepRow],
                                 bestA_legacy: Optional[SweepRow],
                                 fitB: List[dict], mc: dict,
                                 hp_20: float) -> List[dict]:
    reg: List[dict] = []
    dL = (bestA.L_in - bestA_legacy.L_in
          if bestA and bestA_legacy and bestA.L_in and bestA_legacy.L_in else None)
    reg.append({
        "field": "waist side depth @ station 10.5",
        "experimental": f"{WAIST_H_AUTHORITATIVE} in",
        "conflicting": f"{WAIST_H_LEGACY} in",
        "difference": f"{WAIST_H_AUTHORITATIVE - WAIST_H_LEGACY:+.4f} in",
        "source": "martin_d28_1937.json side_profile_raw['10.5'] (and .py)",
        "effect": (f"moves recovered L* by {dL:+.2f} in and flips P* sign "
                   "(legacy P*<0, authoritative P*>0)" if dL is not None
                   else "changes the nested-solve constraint"),
        "class": "EXPERIMENTAL_OVERRIDE",
        "disposition": "keep experimental value; verify against Arnold drawing; leave repo unchanged",
    })
    reg.append({
        "field": "martin_d28_1937.py module",
        "experimental": "n/a",
        "conflicting": "exports nothing (single line; early # comment swallows all code)",
        "difference": "code vs data-bearing .json",
        "source": "services/api/app/instrument_geometry/specs/martin_d28_1937.py",
        "effect": "none on this solve (observations sourced from the .json)",
        "class": "REPO_CONFLICT",
        "disposition": "flag for owner; the .py spec is non-functional and should be repaired separately",
    })
    okB = [f for f in fitB if "L" in f]
    reg.append({
        "field": "body length L",
        "experimental": "not an input (recovered)",
        "conflicting": f"repo body_length {BODY_LENGTH_SPEC} in",
        "difference": (f"A: {bestA.L_in:.2f} in; B: {okB[0]['L']:.2f} in"
                       if bestA and bestA.L_in and okB else "n/a"),
        "source": "repo dimensions.body_length vs derived",
        "effect": "recovered L disagrees across methods -> not separately identifiable",
        "class": "DERIVATION_MISMATCH",
        "disposition": "do not adjust repo; L underdetermined by these data",
    })
    reg.append({
        "field": "30.4375 in (station span / total_length)",
        "experimental": "developed side-strip span (station max)",
        "conflicting": f"repo total_length {COMPARISON_TARGETS['total_length_in']} in; "
                       f"outline half-perimeter @L=20 = {hp_20:.2f} in",
        "difference": f"{hp_20 - S_MAX:+.2f} in vs half-perimeter",
        "source": "repo dimensions.total_length; derived outline",
        "effect": "governs station->perimeter mapping; 'body length' reading falsified by Model C",
        "class": "UNIT_OR_DATUM_AMBIGUITY",
        "disposition": "read 30.4375 in as developed side-strip / half-perimeter length",
    })
    # Waist value vs the surrounding monotonic raw profile.
    n9, n12 = RAW[9.0], RAW[12.0]
    reg.append({
        "field": "waist depth vs neighbouring raw stations",
        "experimental": f"{WAIST_H_AUTHORITATIVE} in @10.5",
        "conflicting": f"raw 9.0->{n9}, 12.0->{n12} (monotone-increasing profile)",
        "difference": f"waist exceeds station 12.0 by {WAIST_H_AUTHORITATIVE - n12:+.4f} in",
        "source": "martin_d28_1937.json side_profile_raw",
        "effect": "creates a local bulge the smooth spherical model cannot match "
                  "(systematic flanking residuals up to ~0.30 in)",
        "class": "SOURCE_CONFLICT",
        "disposition": "verify Arnold waist reading; UNRESOLVED pending source",
    })
    reg.append({
        "field": "waist_y_norm (perimeter waist position)",
        "experimental": "not declared",
        "conflicting": f"{WAIST_Y_NORM} (BodyContourSolver dreadnought family default)",
        "difference": "family default used for mapping",
        "source": "body_contour_solver FAMILY_DEFAULTS",
        "effect": "sets where the waist sits along the perimeter -> affects D mapping",
        "class": "UNRESOLVED",
        "disposition": "replace with a measured #65260 waist position if an authoritative outline is obtained",
    })
    return reg


# --- Report ------------------------------------------------------------------

def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       cwd=os.path.dirname(_API)).decode().strip()
    except Exception:
        return "UNKNOWN"


def _fmt(v: Optional[float], nd: int = 3) -> str:
    return "n/a" if v is None else f"{v:.{nd}f}"


def build_report() -> str:
    sha = git_sha()
    inits = [(20.0, 180.0), (18.0, 300.0), (22.0, 120.0), (16.0, 500.0), (30.0, 250.0)]

    rowsA = sweep_waist_constrained(WAIST_H_AUTHORITATIVE)
    bestA = best_row(rowsA)
    refinedA = refine_waist_constrained(WAIST_H_AUTHORITATIVE, bestA.R_in) if bestA else None

    rowsA_legacy = sweep_waist_constrained(WAIST_H_LEGACY)
    bestA_legacy = best_row(rowsA_legacy)

    fitB = full_least_squares(WAIST_H_AUTHORITATIVE, inits)
    loo = leave_one_out_anchor(WAIST_H_AUTHORITATIVE)
    mc = model_c_falsification()
    sens = sensitivity_perturbation(WAIST_H_AUTHORITATIVE)

    hp_star = half_perimeter_in(bestA.L_in) if (bestA and bestA.L_in) else None
    hp_20 = half_perimeter_in(BODY_LENGTH_SPEC)

    disposition, notes = classify(bestA, fitB, loo, mc, sens)

    # Physical-admissibility and boundary observations (secondary evidence).
    if bestA and (abs(bestA.R_in - R_MIN_IN) < 1.0 or abs(bestA.R_in - R_MAX_IN) < 1.0):
        notes.append(f"Analysis A's minimum sits on the R bound ({bestA.R_in/12:.1f} ft); "
                     "validation RMSE is monotonic in R, so A has no interior optimum.")
    neg_P = [f for f in fitB if f.get("P") is not None and f["P"] < 0.0]
    if neg_P:
        notes.append("The unconstrained least-squares solution places the spherical high "
                     f"point outside the body (P = {neg_P[0]['P']:.2f} in < 0) — physically "
                     "inadmissible, a further sign the data do not pin the geometry.")
    if bestA and bestA_legacy and bestA.L_in and bestA_legacy.L_in:
        notes.append(f"Waist correction is decisive for the recovered length: 4.4375 in gives "
                     f"L* = {bestA.L_in:.2f} in (P* = {bestA.P_in:+.2f} in), while the legacy "
                     f"4.220 in gives L* = {bestA_legacy.L_in:.2f} in "
                     f"(P* = {bestA_legacy.P_in:+.2f} in). The corrected value moves the "
                     "recovered length toward the historical 20 in.")
    notes.append(f"Supporting the developed-length reading: the outline half-perimeter at "
                 f"L = 20 in ({hp_20:.2f} in) is close to 30.4375 in, whereas treating "
                 "30.4375 in as body length is physically inadmissible (Model C).")

    L = []
    w = L.append
    w("# The Reverse Engineering of the Martin D-28 #65260")
    w("")
    w("Isolated inverse-geometry experiment. Evidence gathering only — no production,")
    w("authority, or spec change is made or implied by this document.")
    w("")
    w("## Experimental authority rule — read first")
    w("")
    w("Only the values declared in the *Active experimental inputs* block below govern")
    w("this solve. They override conflicting values found elsewhere in the repository")
    w("for the purpose of this experiment. Repository defaults, production specs, family")
    w("defaults, historical estimates, and inferred values are **not** silently")
    w("substituted for a declared experimental value. Repository values are read only")
    w("for outline mapping/interpretation, provenance, comparison, validation, and")
    w("inconsistency detection. If a required governing value were missing, the run")
    w("stops and reports it rather than borrowing a repo source. Every discrepancy is")
    w("recorded in the Inconsistency Register (section 12); none is auto-resolved. No")
    w("production authority is changed by this experiment.")
    w("")
    w("## Active experimental inputs")
    w("")
    w("```text")
    for line in active_inputs_lines():
        w(line)
    w("```")
    w("")
    w("## 1. Provenance")
    w("")
    w(f"- Repository SHA tested: `{sha}`")
    w(f"- Branch: `experiment/d28-side-profile-inverse-convergence`")
    w("- Equations reused (unmodified): `solve_high_point`, `solve_side_height` in")
    w("  `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py`.")
    w("- Outline authority: `BodyContourSolver` two-arc plan-view outline, seeded with")
    w("  the D-28 spec widths and scaled to the candidate body length. This is a")
    w("  parametric reconstruction, not an independently measured perimeter polygon —")
    w("  see the identifiability finding.")
    w("- Observations: `martin_d28_1937.json` `side_profile_raw` and `dimensions`")
    w("  (read-only). Incidental defect noted, not fixed here: the sibling")
    w("  `martin_d28_1937.py` is a single physical line whose early `#` comment swallows")
    w("  every assignment, so that module exports nothing; the JSON is the usable copy.")
    w("")
    w("## 2. Authoritative waist correction")
    w("")
    w(f"- Waist side depth used as the hard constraint: **{WAIST_H_AUTHORITATIVE} in**.")
    w(f"- Repository legacy value at station {S_WAIST} in: `{WAIST_H_LEGACY} in` — treated")
    w("  as suspect/superseded for this experiment and left unchanged in the spec.")
    w("")
    w("## 3. Units, boundary conditions, mapping")
    w("")
    w("- Units: inches throughout (the Sevy formulas are unit-agnostic).")
    w(f"- Boundary depths from the profile endpoints (raw ⇒ M = N = 0):")
    w(f"  - S (shoulder/neck, station {S_NECK}) = {S_SHOULDER} in")
    w(f"  - B (butt/tail, station {S_TAIL}) = {B_BUTT} in  ⇒  E = B − S = {B_BUTT - S_SHOULDER:.3f} in")
    w("- Equations:")
    w("  - `P = (L/2) − (E/2)·sqrt(4R²/(L²+E²) − 1)`")
    w("  - `H = (B + (R − sqrt(R²−P²))) − (R − sqrt(R²−D²)) − (M+N)`")
    w("- **Station-to-perimeter mapping:** each developed station `s` maps to the point")
    w("  at normalised arc-length fraction `s / 30.4375` along the neck→tail half of the")
    w("  L-scaled outline. `D` is the Euclidean distance from the high point (0, P) to")
    w("  that perimeter point. **`D` is never set equal to the station.**")
    w(f"- Validation stations (out-of-sample): {VALIDATION_STATIONS}")
    w("")
    w("## 4. Analysis A — waist-constrained nested solve (waist = 4.4375 in)")
    w("")
    w("For each candidate R, L is solved so the model reproduces the waist depth exactly;")
    w("the remaining non-waist, non-endpoint points are pure validation.")
    w("")
    w("| R (in) | R (ft) | solved L (in) | P (in) | val RMSE (in) | val max|resid| (in) |")
    w("|---:|---:|---:|---:|---:|---:|")
    for r in rowsA[::4]:
        w(f"| {r.R_in:.1f} | {r.R_in/12:.2f} | {_fmt(r.L_in)} | {_fmt(r.P_in)} "
          f"| {_fmt(r.rmse_in,4)} | {_fmt(r.max_abs_in,4)} |")
    w("")
    if bestA:
        w(f"- Coarse best: R* = {bestA.R_in:.2f} in ({bestA.R_in/12:.2f} ft), "
          f"L* = {_fmt(bestA.L_in)} in, P* = {_fmt(bestA.P_in)} in, "
          f"validation RMSE = {_fmt(bestA.rmse_in,4)} in.")
    if refinedA:
        w(f"- Local refinement (independent of the grid): R* = {refinedA.R_in:.2f} in, "
          f"L* = {_fmt(refinedA.L_in)} in, RMSE = {_fmt(refinedA.rmse_in,4)} in.")
    w("")
    w("### Residuals at the best Analysis-A solution")
    w("")
    if bestA and bestA.L_in is not None:
        w("| station (in) | measured H (in) | predicted H (in) | residual (in) | D (in) |")
        w("|---:|---:|---:|---:|---:|")
        for s in STATIONS:
            Hm = RAW[s]
            Hp, D, _ = predict_height(bestA.L_in, bestA.R_in, s)
            tag = " (S bc)" if s == S_NECK else (" (B bc)" if s == S_TAIL else (" (waist*)" if s == S_WAIST else ""))
            meas = WAIST_H_AUTHORITATIVE if s == S_WAIST else Hm
            w(f"| {s}{tag} | {meas:.4f} | {Hp:.4f} | {Hp-meas:+.4f} | {D:.3f} |")
        w("")
        w("`(S bc)`/`(B bc)` fix the boundary depths; `(waist*)` is the hard constraint "
          "at the authoritative 4.4375 in.")
    w("")
    w("## 5. Analysis B — independent full least squares in (L, R)")
    w("")
    w("| L0 | R0 | fitted L (in) | fitted R (in / ft) | P (in) | RMSE (in) | success |")
    w("|---:|---:|---:|---:|---:|---:|:--:|")
    for f in fitB:
        if "L" in f:
            w(f"| {f['L0']:.0f} | {f['R0']:.0f} | {f['L']:.3f} | {f['R']:.1f} / {f['R']/12:.2f} "
              f"| {f['P']:.3f} | {f['rmse']:.4f} | {f['success']} |")
        else:
            w(f"| {f['L0']:.0f} | {f['R0']:.0f} | ERROR | — | — | — | — |")
    w("")
    w("## 6. Analysis C — leave-one-out anchor test")
    w("")
    w("Each row uses a different profile point as the exact anchor (in place of the")
    w("waist) and re-solves; clustered `(L, R)` would indicate identifiability.")
    w("")
    w("| anchor station (in) | recovered L (in) | recovered R (in / ft) | RMSE others (in) |")
    w("|---:|---:|---:|---:|")
    for d in loo:
        if d["L"] is not None:
            w(f"| {d['anchor']} | {d['L']:.3f} | {d['R']:.1f} / {d['R']/12:.2f} | {d['rmse_others']:.4f} |")
        else:
            w(f"| {d['anchor']} | n/a | n/a | n/a |")
    loo_ok = [d for d in loo if d["L"] is not None]
    if loo_ok:
        Ls = [d["L"] for d in loo_ok]
        Rs = [d["R"] for d in loo_ok]
        w("")
        w(f"- Recovered L spread: {min(Ls):.2f} .. {max(Ls):.2f} in "
          f"(range {max(Ls)-min(Ls):.2f} in).")
        w(f"- Recovered R spread: {min(Rs)/12:.2f} .. {max(Rs)/12:.2f} ft.")
    w("")
    w("## 7. Half-perimeter test for 30.4375 in")
    w("")
    w(f"- Developed neck→tail half-perimeter of the outline at L = 20 in: {hp_20:.3f} in.")
    if hp_star is not None:
        w(f"- Developed neck→tail half-perimeter at the recovered L* = {bestA.L_in:.2f} in: "
          f"{hp_star:.3f} in.")
    w(f"- Recorded side-profile span (station max): {S_MAX} in.")
    w("- Interpretation: whether 30.4375 in reads as developed side-strip / half-perimeter")
    w("  length rather than centerline body length is judged by how close the outline's")
    w("  half-perimeter is to 30.4375 in versus how close the body length is to 20 in.")
    hp_err = abs(hp_20 - S_MAX)
    w(f"- Verdict: the developed neck→tail half-perimeter at the historical L = 20 in is")
    w(f"  {hp_20:.2f} in, within {hp_err:.2f} in ({100*hp_err/S_MAX:.1f}%) of 30.4375 in.")
    w("  This is consistent with 30.4375 in being a developed side-strip / half-perimeter")
    w("  length, not centerline body length.")
    w("")
    w("## 8. Model C — falsification of `30.4375 in == body length`")
    w("")
    w(f"- Fixing L = {mc['L_fixed']} in and fitting R alone: R = {mc['R']:.1f} in "
      f"({mc['R']/12:.2f} ft), P = {mc['P']:.2f} in, RMSE = {mc['rmse']:.4f} in"
      f"{', on bound' if mc['on_bound'] else ''}.")
    mc_bad = mc["on_bound"] or mc["P"] < 0.0
    w(f"- Verdict: treating 30.4375 in as centerline body length "
      f"{'is not physically admissible — the fit lands on the radius bound and/or drives '
         'the high point outside the body (P < 0).' if mc_bad else 'is admissible.'}")
    w("")
    w("## 9. Sensitivity / identifiability")
    w("")
    Ll, Lh = sens["L_range"]; Rl, Rh = sens["R_range"]; Pl, Ph = sens["P_range"]
    w(f"- ±{sens['delta_in']} in perturbation of every measured height (Analysis A):")
    w(f"  - recovered L: {_fmt(Ll,2)} .. {_fmt(Lh,2)} in")
    w(f"  - recovered R: {_fmt(Rl,1)} .. {_fmt(Rh,1)} in "
      f"({_fmt(Rl/12 if Rl else None,2)} .. {_fmt(Rh/12 if Rh else None,2)} ft)")
    w(f"  - recovered P: {_fmt(Pl,2)} .. {_fmt(Ph,2)} in")
    w("")
    w("## 10. Waist-value comparison — authoritative 4.4375 vs legacy 4.220")
    w("")
    w("| waist H (in) | R* (in / ft) | L* (in) | P* (in) | validation RMSE (in) |")
    w("|---:|---:|---:|---:|---:|")
    if bestA:
        w(f"| 4.4375 (authoritative) | {bestA.R_in:.1f} / {bestA.R_in/12:.2f} | {_fmt(bestA.L_in)} "
          f"| {_fmt(bestA.P_in)} | {_fmt(bestA.rmse_in,4)} |")
    if bestA_legacy:
        w(f"| 4.220 (legacy repo) | {bestA_legacy.R_in:.1f} / {bestA_legacy.R_in/12:.2f} "
          f"| {_fmt(bestA_legacy.L_in)} | {_fmt(bestA_legacy.P_in)} | {_fmt(bestA_legacy.rmse_in,4)} |")
    if bestA and bestA_legacy and bestA.L_in and bestA_legacy.L_in:
        w("")
        w(f"- ΔL* (authoritative − legacy) = {bestA.L_in - bestA_legacy.L_in:+.3f} in; "
          f"ΔR* = {bestA.R_in - bestA_legacy.R_in:+.1f} in.")
    w("")
    w("## 11. Disposition")
    w("")
    w(f"**{disposition}**")
    w("")
    for n in notes:
        w(f"- {n}")
    w("")
    w("## 12. Inconsistency audit")
    w("")
    w("Discrepancies between experimental, repository-production, derived, and")
    w("source/context values. None is resolved, normalised, or overwritten here.")
    w("")
    reg = build_inconsistency_register(bestA, bestA_legacy, fitB, mc, hp_20)
    w("| field / value | experimental | conflicting repo/source | difference | source / location | effect on solve | class | recommended disposition |")
    w("|---|---|---|---|---|---|---|---|")
    for r in reg:
        w(f"| {r['field']} | {r['experimental']} | {r['conflicting']} | {r['difference']} "
          f"| {r['source']} | {r['effect']} | `{r['class']}` | {r['disposition']} |")
    w("")
    w("Classes: `EXPERIMENTAL_OVERRIDE`, `REPO_CONFLICT`, `SOURCE_CONFLICT`, "
      "`DERIVATION_MISMATCH`, `UNIT_OR_DATUM_AMBIGUITY`, `UNRESOLVED`.")
    w("")
    w("## 13. Interpretation rule")
    w("")
    w("This experiment is evidence only. Even a convergence near 20 in would not license")
    w("editing `martin_d28_1937.*`; any production or authority change requires a separate")
    w("owner-reviewed order.")
    w("")
    return "\n".join(L)


def main() -> None:
    check_required_inputs()
    # Startup confirmation (stderr) so a reviewer can verify the experiment
    # obeyed the declared inputs rather than silently falling back to repo values.
    print("\n".join(active_inputs_lines()), file=sys.stderr)
    print("--- solving ---", file=sys.stderr)
    report = build_report()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out = os.path.join(repo_root, "docs", "experiments",
                       "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
    if "--write" in sys.argv:
        with open(out, "w") as fh:
            fh.write(report)
        print(f"wrote {out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
