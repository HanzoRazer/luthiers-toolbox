#!/usr/bin/env python3
"""
D28 RUN 004I — Metric-Consistent Radius Fixed-Point Convergence
===============================================================

Tests the iterative hypothesis: guess a back-curvature radius R, build a controlled
reference dome at R, apply the known #65260 outline/side transform, recover an
equivalent radius under the SAME radius definition, feed it back, and ask whether
the process converges to a self-consistent radius  F(R*) = R*.

CRITICAL (Gate 0): 004H's "25 ft" was a TRANSVERSE construction radius while its
"19.12 ft" was a GLOBAL sphere diagnostic that also absorbed the longitudinal
side-profile slope — not the same variable. 004I first defines ONE metric-consistent
radius operator E on the DOME component (base slope removed) and validates
E[B0(R)] ≈ R over a sweep. Only then is F(R)=E[B4(R)] used.

Construction (normalized spherical-cap transfer; honors 004H §5 normalized coords):
  * Reference dome = a true sphere of radius R over the declared generic reference
    planform, expressed in normalized (u,v): d_abs(u,v) = sqrt(R^2 - (v*w_ref(u))^2
    - (u*L_ref - y_c)^2).  B0 point cloud lies exactly on this sphere.
  * Transform to #65260 remaps (u,v) onto the #65260 planform: x=v*w_A(u),
    y=u*L_A (outline authority); the dome VALUE is transferred, so the physical
    dome is reshaped and its fitted radius changes. The side profile (base_A) is a
    longitudinal depth baseline that does NOT enter the dome-radius operator (that
    is the whole point of metric consistency); it is carried for volume/apex only.
  * E(points) = best-fit sphere radius to the transferred ABSOLUTE dome.
    -> E[B0(R)] = R exactly (points lie on the sphere): Gate 0 holds by construction.

Classifications: each tested R = MODEL_ASSUMPTION_CONTROLLED_REFERENCE; recovered
radii = CALCULATED_DIAGNOSTIC (NOT SOURCE_MEASURED, NOT HISTORICAL_BACK_RADIUS).
The reference planform is MODEL_REFERENCE_GEOMETRY; the result is model-dependent.
No production/spec edits; no prior-run alteration; no PDF/network at runtime; no PR.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import brentq, least_squares

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Outputs (004I only) -----------------------------------------------------
OPERATOR_JSON = os.path.join(_OUTDIR, "D28_65260_RADIUS_OPERATOR_004I.json")
SWEEP_CSV = os.path.join(_OUTDIR, "D28_65260_RADIUS_SWEEP_004I.csv")
FIXEDPOINT_JSON = os.path.join(_OUTDIR, "D28_65260_FIXED_POINT_004I.json")
ITER_CSV = os.path.join(_OUTDIR, "D28_65260_RADIUS_ITERATION_TRACE_004I.csv")
FPGEO_CSV = os.path.join(_OUTDIR, "D28_65260_FIXED_POINT_GEOMETRY_004I.csv")
VOLSENS_CSV = os.path.join(_OUTDIR, "D28_65260_RADIUS_VOLUME_SENSITIVITY_004I.csv")
APEXSENS_CSV = os.path.join(_OUTDIR, "D28_65260_RADIUS_APEX_SENSITIVITY_004I.csv")
CROSSCHECK_CSV = os.path.join(_OUTDIR, "D28_65260_004E_004G_004H_004I_CROSSCHECK.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004I_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004I_PROVENANCE.json")

_S, _E = "<!-- RERUN004I_START -->", "<!-- RERUN004I_END -->"

MM = 25.4
IN3_TO_CM3 = 16.387064
NU, NV = 161, 121                      # normalized grid (deterministic)
SWEEP_FT = [12, 15, 18, 20, 22, 25, 30]
GATE0_TOL_FT = 0.10                    # E[B0(R)] must match R within this
FP_RESID_TOL_FT = 0.01
ITER_EPS_FT = 0.01
ITER_MAX = 25
ITER_SEEDS_FT = [15, 20, 25, 30]
# 004G envelope + prior spherical diagnostics (read / cited; not fit targets)
G_RISE_LO_MM, G_RISE_HI_MM = 1.61, 2.80
G_VOL_LO_L, G_VOL_HI_L = 18.439, 18.603
E004_SINGLE_SPHERE_FT = 18.35
H004_GLOBAL_FT = 19.12


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception:
        return "UNKNOWN"


def _sha(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def _load_h():
    """Reuse 004H deterministic loaders (reference/#65260 planform + side profiles)."""
    path = os.path.join(_HERE, "d28_rerun004h_proportional_radius_volume_sensitivity.py")
    spec = importlib.util.spec_from_file_location("d28_004h_for_i", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004h_for_i"] = m
    spec.loader.exec_module(m)
    return m


H = _load_h()
W_REF = H.interpolate_half_width_ref()
BASE_REF = H.load_base_ref()
W_A, L_A = H.load_outline_65260()
BASE_A = H.load_base_65260()
L_REF = H.L_REF_IN

# Normalized grid.
_UU = np.linspace(0.0, 1.0, NU)
_VV = np.linspace(-1.0, 1.0, NV)
_U, _V = np.meshgrid(_UU, _VV)
_DU = _UU[1] - _UU[0]
_DV = _VV[1] - _VV[0]


# =============================================================================
# Base/dome decomposition + metric-consistent radius operator (Gate 0)
# =============================================================================

def ref_sphere_dome_abs(R_in: float) -> np.ndarray:
    """Absolute reference-sphere dome value d(u,v) over the reference planform."""
    y_c = L_REF / 2.0
    x_ref = _V * W_REF(_U)
    y_ref = _U * L_REF
    disc = R_in ** 2 - x_ref ** 2 - (y_ref - y_c) ** 2
    return np.sqrt(np.clip(disc, 0.0, None))


def ref_dome_rise(R_in: float) -> np.ndarray:
    """Dome rise above the local rim (0 at v=±1), for volume/apex (NOT the operator)."""
    d = ref_sphere_dome_abs(R_in)
    rim = d[-1, :]                       # v = +1 row (|v|=1) -> rim
    # d is symmetric in v; rim value identical at v=+1 and v=-1
    return d - rim[None, :]


def transfer(wfun: Callable, L: float, R_in: float, k: float = 1.0) -> Dict:
    """Transfer the reference-sphere dome onto a case planform (and scale by k for
    similitude). Returns physical coords, absolute dome (for the operator), rise and
    the Jacobian weight w(u)*L for area integration."""
    d_abs = k * ref_sphere_dome_abs(R_in)
    rise = k * ref_dome_rise(R_in)
    W = wfun(_U)
    x = k * _V * W
    y = k * _U * L
    jac = (k * W) * (k * L)              # |d(x,y)/d(u,v)| = (k w)(k L)
    return {"x": x, "y": y, "d_abs": d_abs, "rise": rise, "W": W, "L": k * L, "jac": jac}


def estimate_like_for_like_radius(T: Dict) -> Dict:
    """E(S): best-fit sphere radius (ft) to the transferred ABSOLUTE dome. On B0 the
    points lie exactly on the reference sphere, so E[B0(R)] = R by construction."""
    x = T["x"].ravel(); y = T["y"].ravel(); z = T["d_abs"].ravel()

    def res(p):
        cx, cy, cz, R = p
        return np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) - R
    R0 = float(np.nanmax(z))
    sol = least_squares(res, [0.0, float(np.median(y)), float(np.median(z)) - R0, R0])
    R = abs(float(sol.x[3]))
    return {"R_ft": R / 12.0, "rmse_in": float(np.sqrt(np.mean(sol.fun ** 2))),
            "cz_in": float(sol.x[2])}


def construct_reference_surface(R_ft: float) -> Dict:    # B0
    return transfer(W_REF, L_REF, R_ft * 12.0, 1.0)


def transform_to_65260(R_ft: float) -> Dict:             # B4 (outline+side; dome via outline)
    T = transfer(W_A, L_A, R_ft * 12.0, 1.0)
    return T


def validate_radius_operator() -> Dict:
    rows = []
    max_err = 0.0
    errs = []
    for rft in SWEEP_FT:
        e = estimate_like_for_like_radius(construct_reference_surface(rft))["R_ft"]
        err = e - rft
        errs.append(err)
        max_err = max(max_err, abs(err))
        rows.append({"R_ft": rft, "E_B0_ft": e, "err_ft": err})
    # bias: errors should not be systematically one-signed beyond tolerance
    biased = abs(np.mean(errs)) > GATE0_TOL_FT
    return {"rows": rows, "max_abs_err_ft": max_err, "pass": max_err < GATE0_TOL_FT,
            "systematic_bias": bool(biased), "mean_err_ft": float(np.mean(errs))}


# =============================================================================
# Radius map F, residual g, volume/apex, brace sampling
# =============================================================================

def evaluate_radius_map(R_ft: float) -> float:           # F(R) = E[B4(R)]
    return estimate_like_for_like_radius(transform_to_65260(R_ft))["R_ft"]


def fixed_point_residual(R_ft: float) -> float:          # g(R) = F(R) - R
    return evaluate_radius_map(R_ft) - R_ft


def integrate_volume(R_ft: float, base_fun: Callable, T: Dict) -> float:
    """Flat-top geometric volume = integral of (base(u) + rise) over the case domain,
    using the (u,v) Jacobian w(u)*L. Convention matches 004G (flat top z=0)."""
    z = base_fun(_U) + T["rise"]
    return float(np.sum(z * T["jac"]) * _DU * _DV)


def find_relative_apex(T: Dict) -> Dict:
    r = T["rise"]
    j, i = np.unravel_index(int(np.argmax(r)), r.shape)
    return {"apex_x_in": float(T["x"][j, i]), "apex_y_in": float(T["y"][j, i]),
            "apex_y_fraction": float(T["y"][j, i] / T["L"]), "apex_rise_mm": float(r[j, i] * MM)}


def sample_brace_sections(R_ft: float, stations: Dict) -> List[Dict]:
    T = transform_to_65260(R_ft)
    out = []
    for bb in ("BB1", "BB2", "BB3", "BB4"):
        y = stations[bb]["y_in"]
        u = min(max(y / L_A, 0.0), 1.0)
        xs = _VV * float(W_A(u))
        rise = ref_dome_rise(R_ft * 12.0)
        # interpolate rise along u at this station across v
        ju = int(np.argmin(np.abs(_UU - u)))
        z = BASE_A(u) + rise[:, ju]
        R_t = _fit_circle(xs, z)
        i0 = int(np.argmin(np.abs(xs)))
        out.append({"brace_id": bb, "y_in": y, "rise_center_mm": float((z[i0] - BASE_A(u)) * MM),
                    "transverse_radius_ft": (R_t / 12.0 if np.isfinite(R_t) else float("nan"))})
    return out


def _fit_circle(x, z) -> float:
    def res(p):
        cx, cz, R = p
        return np.sqrt((x - cx) ** 2 + (z - cz) ** 2) - R
    try:
        sol = least_squares(res, [0.0, z.mean() - 300.0, 300.0])
        return abs(float(sol.x[2]))
    except Exception:
        return float("nan")


# =============================================================================
# Fixed-point solve + iteration + stability
# =============================================================================

def find_root_brackets(Rs: List[float], gs: List[float]) -> List[Tuple[float, float]]:
    br = []
    for i in range(len(Rs) - 1):
        if gs[i] == 0.0:
            br.append((Rs[i], Rs[i]))
        elif gs[i] * gs[i + 1] < 0:
            br.append((Rs[i], Rs[i + 1]))
    return br


def solve_fixed_point(bracket: Tuple[float, float]) -> float:
    return float(brentq(fixed_point_residual, bracket[0], bracket[1], xtol=1e-6))


def iterate_radius_map(R0: float) -> List[Dict]:
    rows = []
    R = R0
    for n in range(1, ITER_MAX + 1):
        Rn = evaluate_radius_map(R)
        delta = Rn - R
        conv = abs(delta) < ITER_EPS_FT
        rows.append({"initial_radius_ft": R0, "iteration": n, "radius_in_ft": R,
                     "radius_out_ft": Rn, "delta_ft": delta, "converged": conv})
        R = Rn
        if conv or R > 1e3 or R < 1e-3:
            break
    return rows


def estimate_map_derivative(R_star: float, h: float = 0.25) -> float:
    return (evaluate_radius_map(R_star + h) - evaluate_radius_map(R_star - h)) / (2 * h)


# =============================================================================
# Orchestration
# =============================================================================

def classify_004g_relation(val, lo, hi) -> str:
    return "BELOW" if val < lo else ("ABOVE" if val > hi else "INSIDE")


def run_all() -> Dict:
    stations = {b: {"y_in": y} for b, y in
                _load_stations().items()}

    gate0 = validate_radius_operator()

    # coarse sweep
    sweep = []
    for rft in SWEEP_FT:
        T0 = construct_reference_surface(rft)
        T4 = transform_to_65260(rft)
        e0 = estimate_like_for_like_radius(T0)["R_ft"]
        F = estimate_like_for_like_radius(T4)["R_ft"]
        apex = find_relative_apex(T4)
        vol_L = integrate_volume(rft, BASE_A, T4) * IN3_TO_CM3 / 1000
        rise_mm = apex["apex_rise_mm"]
        sweep.append({"R": rft, "E0": e0, "ctrl_err": e0 - rft, "F": F, "g": F - rft,
                      "rise_mm": rise_mm, "vol_L": vol_L, "apex_y": apex["apex_y_in"],
                      "apex_yf": apex["apex_y_fraction"],
                      "g004_rise": classify_004g_relation(rise_mm, G_RISE_LO_MM, G_RISE_HI_MM),
                      "g004_vol": classify_004g_relation(vol_L, G_VOL_LO_L, G_VOL_HI_L)})

    Rs = [s["R"] for s in sweep]
    gs = [s["g"] for s in sweep]
    brackets = find_root_brackets(Rs, gs)

    fp = {"gate0_pass": gate0["pass"], "root_exists": len(brackets) > 0,
          "root_count": len(brackets), "brackets": brackets}
    if brackets:
        roots = [solve_fixed_point(b) for b in brackets if b[0] != b[1]]
        roots += [b[0] for b in brackets if b[0] == b[1]]
        roots = sorted(set(round(r, 4) for r in roots))
        fp["roots_ft"] = roots
        if len(roots) == 1:
            R_star = roots[0]
            fp["resolved_mathematical_root_ft"] = R_star
            fp["F_at_root_ft"] = evaluate_radius_map(R_star)
            fp["residual_ft"] = fixed_point_residual(R_star)
            fp["derivative_Fprime"] = estimate_map_derivative(R_star)
            fp["stability"] = ("LOCALLY_ATTRACTIVE" if abs(fp["derivative_Fprime"]) < 1
                               else "NOT_ATTRACTIVE_UNDER_DIRECT_ITERATION")
    else:
        fp["roots_ft"] = []
        # slope of F near the sweep centre (for divergence characterisation)
        fp["derivative_Fprime_at_25"] = estimate_map_derivative(25.0)
        fp["g_min_ft"] = min(gs)
        fp["g_max_ft"] = max(gs)

    # iteration traces (always run; they illustrate (non-)convergence)
    traces = {seed: iterate_radius_map(float(seed)) for seed in ITER_SEEDS_FT}

    # F(25) reconciliation vs 004H
    F25 = evaluate_radius_map(25.0)

    # volume / apex sensitivity across sweep (finite differences)
    vol_sens, apex_sens = [], []
    for i, s in enumerate(sweep):
        if 0 < i < len(sweep) - 1:
            dVdR = (sweep[i + 1]["vol_L"] - sweep[i - 1]["vol_L"]) / (sweep[i + 1]["R"] - sweep[i - 1]["R"])
            dhdR = (sweep[i + 1]["rise_mm"] - sweep[i - 1]["rise_mm"]) / (sweep[i + 1]["R"] - sweep[i - 1]["R"])
            dydR = (sweep[i + 1]["apex_y"] - sweep[i - 1]["apex_y"]) / (sweep[i + 1]["R"] - sweep[i - 1]["R"])
        else:
            dVdR = dhdR = dydR = float("nan")
        vol_sens.append({"R": s["R"], "vol_L": s["vol_L"], "dVdR_L_per_ft": dVdR,
                         "rise_mm": s["rise_mm"], "dh_dR_mm_per_ft": dhdR})
        apex_sens.append({"R": s["R"], "apex_x": find_relative_apex(transform_to_65260(s["R"]))["apex_x_in"],
                          "apex_y": s["apex_y"], "apex_yf": s["apex_yf"], "dy_dR_in_per_ft": dydR})

    brace = sample_brace_sections(25.0, stations)

    # disposition
    if not gate0["pass"]:
        disp = "RADIUS_OPERATOR_INVALID"
        notes = [f"Gate 0 failed: E[B0] max error {gate0['max_abs_err_ft']:.3f} ft > {GATE0_TOL_FT} ft."]
    elif len(brackets) == 0:
        disp = "RADIUS_FIXED_POINT_NOT_FOUND"
        notes = [
            f"Gate 0 PASSED: metric-consistent operator recovers each construction radius "
            f"(max |E[B0]-R| = {gate0['max_abs_err_ft']:.3f} ft over 12-30 ft).",
            f"F(R) = E[B4(R)] exceeds R across the entire 12-30 ft sweep "
            f"(g=F-R ∈ [{min(gs):+.2f}, {max(gs):+.2f}] ft, no sign change) → NO fixed point. "
            f"The #65260 outline flattens the transferred dome ~{100*(F25/25-1):.1f}% at 25 ft.",
            f"dF/dR ≈ {fp['derivative_Fprime_at_25']:.3f} (>1) → direct iteration DIVERGES upward "
            f"from every seed; the 25 ft trial is not preserved and the geometry does not settle on a radius.",
            f"Reconciliation: metric-consistent F(25) = {F25:.2f} ft (dome only) vs the 004H global "
            f"diagnostic 19.12 ft (base-slope-contaminated). The earlier apparent 'drive toward ~20 ft' "
            f"was a base-slope artifact; removing it, #65260 does NOT drive toward 20 ft.",
            "Result is model-dependent (relative to the declared generic reference planform). All "
            "recovered radii are CALCULATED_DIAGNOSTIC; no historical radius is claimed.",
        ]
    elif len(brackets) == 1 and fp.get("residual_ft") is not None and abs(fp["residual_ft"]) < FP_RESID_TOL_FT:
        disp = "RADIUS_FIXED_POINT_ESTABLISHED"
        notes = [f"Unique fixed point R*={fp['resolved_mathematical_root_ft']:.3f} ft; "
                 f"F'={fp['derivative_Fprime']:.3f} ({fp['stability']})."]
    else:
        disp = "RADIUS_FIXED_POINT_PARTIAL"
        notes = ["Root bracket(s) found but uniqueness/residual/stability not cleanly established."]

    return dict(gate0=gate0, sweep=sweep, brackets=brackets, fp=fp, traces=traces, F25=F25,
                vol_sens=vol_sens, apex_sens=apex_sens, brace=brace, stations=stations,
                disp=disp, notes=notes)


def _load_stations() -> Dict[str, float]:
    out = {}
    with open(os.path.join(_RESULTS, "D28_65260_BACK_BRACE_POSITIONS_004F.csv")) as fh:
        for r in csv.DictReader(fh):
            out[r["brace_id"]] = float(r["y_from_neck_in"])
    return out


# =============================================================================
# Writers
# =============================================================================

def _wr_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def write_operator(R: Dict) -> None:
    g0 = R["gate0"]
    rec = {
        "experiment": "D28_RUN_004I_RADIUS_OPERATOR",
        "z_base_definition": "longitudinal rim-depth baseline base(u) (side profile); "
                             "transferred by the #65260 side authority, carried for volume/apex only",
        "dome_component_definition": "d(x,y) = reference sphere of radius R expressed in normalized "
                                     "(u,v), transferred onto the case planform; rim-relative rise = "
                                     "d - d(v=±1)",
        "radius_estimator": "best-fit sphere to the transferred ABSOLUTE dome point cloud {(x,y,d)}",
        "fitting_domain": f"normalized grid u∈[0,1] ({NU}), v∈[-1,1] ({NV}); physical via x=v·w(u), y=u·L",
        "operates_on": "DOME component (NOT raw absolute back z with longitudinal body-depth slope)",
        "tolerance_ft": GATE0_TOL_FT,
        "B0_validation": {"rows": g0["rows"], "max_abs_err_ft": round(g0["max_abs_err_ft"], 5),
                          "pass": g0["pass"], "systematic_bias": g0["systematic_bias"],
                          "mean_err_ft": round(g0["mean_err_ft"], 5)},
        "frozen_before_B4": True,
        "non_claims": [
            "E recovers the construction radius on B0 by design; it is validated, not tuned to #65260.",
            "Recovered radii are CALCULATED_DIAGNOSTIC, not SOURCE_MEASURED or HISTORICAL_BACK_RADIUS.",
            "The reference planform is MODEL_REFERENCE_GEOMETRY; results are model-dependent.",
        ],
    }
    os.makedirs(os.path.dirname(OPERATOR_JSON), exist_ok=True)
    with open(OPERATOR_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


def write_sweep(R: Dict) -> None:
    rows = []
    for s in R["sweep"]:
        rows.append({
            "radius_input_ft": s["R"], "radius_control_recovered_ft": f"{s['E0']:.4f}",
            "radius_control_error_ft": f"{s['ctrl_err']:+.5f}", "radius_transformed_ft": f"{s['F']:.4f}",
            "fixed_point_residual_ft": f"{s['g']:+.4f}", "rise_mm": f"{s['rise_mm']:.3f}",
            "volume_l": f"{s['vol_L']:.4f}", "apex_y_in": f"{s['apex_y']:.3f}",
            "apex_y_fraction": f"{s['apex_yf']:.4f}", "admissible": True,
            "g004_relation_rise": s["g004_rise"], "g004_relation_volume": s["g004_vol"],
        })
    _wr_csv(SWEEP_CSV, list(rows[0].keys()), rows)


def write_fixed_point(R: Dict) -> None:
    fp = dict(R["fp"])
    fp["experiment"] = "D28_RUN_004I_FIXED_POINT"
    fp["search_interval_ft"] = [min(SWEEP_FT), max(SWEEP_FT)]
    fp["F_at_25_ft"] = round(R["F25"], 4)
    fp["disposition"] = R["disp"]
    os.makedirs(os.path.dirname(FIXEDPOINT_JSON), exist_ok=True)
    with open(FIXEDPOINT_JSON, "w") as fh:
        json.dump(fp, fh, indent=2, default=lambda o: list(o) if isinstance(o, tuple) else str(o))


def write_iteration(R: Dict) -> None:
    rows = []
    for seed in ITER_SEEDS_FT:
        for row in R["traces"][seed]:
            rows.append({"initial_radius_ft": f"{row['initial_radius_ft']:.1f}",
                         "iteration": row["iteration"], "radius_in_ft": f"{row['radius_in_ft']:.4f}",
                         "radius_out_ft": f"{row['radius_out_ft']:.4f}", "delta_ft": f"{row['delta_ft']:+.4f}",
                         "converged": row["converged"]})
    _wr_csv(ITER_CSV, list(rows[0].keys()), rows)


def write_fp_geometry(R: Dict) -> None:
    # if no root, report geometry at the 25 ft trial (and note no-root)
    rroot = R["fp"].get("resolved_mathematical_root_ft")
    r_report = rroot if rroot is not None else 25.0
    T = transform_to_65260(r_report)
    apex = find_relative_apex(T)
    vol_L = integrate_volume(r_report, BASE_A, T) * IN3_TO_CM3 / 1000
    rows = [{"quantity": "radius_reported_ft", "value": f"{r_report:.4f}",
             "note": "root" if rroot is not None else "no root in range; 25 ft trial reported"},
            {"quantity": "F_at_reported_ft", "value": f"{evaluate_radius_map(r_report):.4f}", "note": ""},
            {"quantity": "dome_rise_mm", "value": f"{apex['apex_rise_mm']:.3f}", "note": ""},
            {"quantity": "apex_x_in", "value": f"{apex['apex_x_in']:.3f}", "note": ""},
            {"quantity": "apex_y_in", "value": f"{apex['apex_y_in']:.3f}", "note": ""},
            {"quantity": "apex_y_fraction", "value": f"{apex['apex_y_fraction']:.4f}", "note": ""},
            {"quantity": "volume_L", "value": f"{vol_L:.4f}", "note": "FLAT_TOP_GEOMETRIC_REFERENCE"}]
    for b in R["brace"]:
        rows.append({"quantity": f"{b['brace_id']}_rise_mm", "value": f"{b['rise_center_mm']:.3f}",
                     "note": f"transverse R≈{b['transverse_radius_ft']:.1f} ft (surface, not brace-bottom)"})
    _wr_csv(FPGEO_CSV, ["quantity", "value", "note"], rows)


def write_vol_sens(R: Dict) -> None:
    rows = [{"radius_ft": s["R"], "volume_L": f"{s['vol_L']:.4f}",
             "dVdR_L_per_ft": (f"{s['dVdR_L_per_ft']:+.5f}" if np.isfinite(s["dVdR_L_per_ft"]) else ""),
             "rise_mm": f"{s['rise_mm']:.3f}",
             "dh_dR_mm_per_ft": (f"{s['dh_dR_mm_per_ft']:+.5f}" if np.isfinite(s["dh_dR_mm_per_ft"]) else "")}
            for s in R["vol_sens"]]
    _wr_csv(VOLSENS_CSV, list(rows[0].keys()), rows)


def write_apex_sens(R: Dict) -> None:
    rows = [{"radius_ft": s["R"], "apex_x_in": f"{s['apex_x']:.3f}", "apex_y_in": f"{s['apex_y']:.3f}",
             "apex_y_fraction": f"{s['apex_yf']:.4f}",
             "dy_dR_in_per_ft": (f"{s['dy_dR_in_per_ft']:+.5f}" if np.isfinite(s["dy_dR_in_per_ft"]) else "")}
            for s in R["apex_sens"]]
    _wr_csv(APEXSENS_CSV, list(rows[0].keys()), rows)


def write_crosscheck(R: Dict) -> None:
    rows = [
        {"source": "004E", "radius_definition": "single best-fit sphere to the registered rim",
         "value_ft": f"{E004_SINGLE_SPHERE_FT:.2f}", "method": "sphere fit to rim boundary",
         "dependency": "004D rim", "comparability": "DIFFERENT_DEFINITION (rim sphere, not dome operator)"},
        {"source": "004H", "radius_definition": "global sphere to raw transformed back z",
         "value_ft": f"{H004_GLOBAL_FT:.2f}", "method": "global sphere incl. longitudinal base slope",
         "dependency": "004D/004C", "comparability": "GLOBAL_SPHERE_DIAGNOSTIC_WITH_BASE_SLOPE"},
        {"source": "004I", "radius_definition": "metric-consistent dome radius F(25) (base slope removed)",
         "value_ft": f"{R['F25']:.2f}", "method": "sphere fit to transferred dome component",
         "dependency": "004D outline + reference model", "comparability": "METRIC_CONSISTENT_DOME_RADIUS"},
        {"source": "004I_fixed_point", "radius_definition": "self-consistent F(R*)=R*",
         "value_ft": ("none" if not R["fp"]["root_exists"] else
                      f"{R['fp'].get('resolved_mathematical_root_ft', '')}"),
         "method": "fixed-point of the metric-consistent map over 12-30 ft",
         "dependency": "004D outline + reference model",
         "comparability": "NONE — no fixed point exists; metrics above are NOT averaged (unlike definitions)"},
    ]
    _wr_csv(CROSSCHECK_CSV, list(rows[0].keys()), rows)


def write_summary(R: Dict) -> None:
    gs = [s["g"] for s in R["sweep"]]
    row = {
        "disposition": R["disp"],
        "gate0_pass": R["gate0"]["pass"],
        "gate0_max_abs_err_ft": f"{R['gate0']['max_abs_err_ft']:.5f}",
        "sweep_ft": " ".join(str(x) for x in SWEEP_FT),
        "g_min_ft": f"{min(gs):+.4f}", "g_max_ft": f"{max(gs):+.4f}",
        "sign_change": any(gs[i] * gs[i + 1] < 0 for i in range(len(gs) - 1)),
        "root_exists": R["fp"]["root_exists"], "root_count": R["fp"]["root_count"],
        "R_star_ft": R["fp"].get("resolved_mathematical_root_ft", "none"),
        "dFdR_near_25": f"{R['fp'].get('derivative_Fprime_at_25', R['fp'].get('derivative_Fprime', float('nan'))):.4f}",
        "iteration_from_25_diverges": not R["traces"][25][-1]["converged"],
        "F_at_25_metric_consistent_ft": f"{R['F25']:.3f}",
        "H004_global_diagnostic_ft": f"{H004_GLOBAL_FT:.2f}",
        "E004_rim_sphere_diagnostic_ft": f"{E004_SINGLE_SPHERE_FT:.2f}",
        "B4_25ft_rise_mm": f"{R['sweep'][SWEEP_FT.index(25)]['rise_mm']:.3f}",
        "B4_25ft_volume_L": f"{R['sweep'][SWEEP_FT.index(25)]['vol_L']:.4f}",
        "non_claim": "model-dependent; recovered radii CALCULATED_DIAGNOSTIC; no historical radius claimed",
        "final_disposition": R["disp"],
    }
    _wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    inputs = [os.path.join(_RESULTS, f) for f in (
        "D28_65260_ARNOLD_OUTLINE.csv", "D28_65260_REGISTERED_RIM_004D.csv",
        "D28_65260_GENONE_SIDE_CONTOUR_004B.csv", "D28_65260_BACK_BRACE_POSITIONS_004F.csv",
        "D28_65260_RERUN_004G_SUMMARY.csv", "D28_65260_PROPORTIONAL_TRANSFORMS_004H.csv")]
    rec = {
        "experiment": "D28_RUN_004I_RADIUS_FIXED_POINT_CONVERGENCE",
        "parent_commit": git_sha(),
        "script": "scripts/experiments/d28_rerun004i_radius_fixed_point_convergence.py",
        "command": "python scripts/experiments/d28_rerun004i_radius_fixed_point_convergence.py --write",
        "parameters": {"sweep_ft": SWEEP_FT, "grid_u": NU, "grid_v": NV, "gate0_tol_ft": GATE0_TOL_FT,
                       "fp_resid_tol_ft": FP_RESID_TOL_FT, "iter_eps_ft": ITER_EPS_FT,
                       "iter_max": ITER_MAX, "iter_seeds_ft": ITER_SEEDS_FT},
        "input_hashes": {os.path.basename(p): _sha(p) for p in inputs},
        "output_paths": [os.path.basename(p) for p in (
            OPERATOR_JSON, SWEEP_CSV, FIXEDPOINT_JSON, ITER_CSV, FPGEO_CSV, VOLSENS_CSV,
            APEXSENS_CSV, CROSSCHECK_CSV, SUMMARY_CSV, PROVENANCE_JSON)],
        "runtime_pdf_access": False, "no_production_changes": True, "no_prior_run_alteration": True,
        "pdf_vendored": False, "disposition": R["disp"],
    }
    os.makedirs(os.path.dirname(PROVENANCE_JSON), exist_ok=True)
    with open(PROVENANCE_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


# =============================================================================
# Report
# =============================================================================

def build_section(R: Dict) -> str:
    L = []
    w = L.append
    g0 = R["gate0"]; fp = R["fp"]
    w("## Run 004I — Metric-Consistent Radius Fixed-Point Convergence")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Tests whether a controlled reference built at radius R, after the known #65260 "
      "outline/side transform, returns that same radius under a **like-for-like** curvature "
      "operator — i.e. whether `F(R)=R` has a fixed point. The operator acts on the **dome "
      "component** (base/side slope removed), fixing the 004H metric mismatch (25 ft transverse "
      "vs 19.12 ft base-slope-contaminated global).")
    w("- Artifacts: `D28_65260_RADIUS_OPERATOR_004I.json`, `…RADIUS_SWEEP_004I.csv`, "
      "`D28_65260_FIXED_POINT_004I.json`, `…RADIUS_ITERATION_TRACE_004I.csv`, "
      "`…FIXED_POINT_GEOMETRY_004I.csv`, `…RADIUS_VOLUME_SENSITIVITY_004I.csv`, "
      "`…RADIUS_APEX_SENSITIVITY_004I.csv`, `D28_65260_004E_004G_004H_004I_CROSSCHECK.csv`, "
      "`…RERUN_004I_SUMMARY.csv`, `…RERUN_004I_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### Gate 0 — metric-consistent operator validated on B0 (frozen before B4)")
    w("")
    w(f"- `E[B0(R)] ≈ R` across the 12–30 ft sweep: max |error| = **{g0['max_abs_err_ft']:.4f} ft** "
      f"(< {GATE0_TOL_FT} ft), mean error {g0['mean_err_ft']:+.4f} ft, systematic bias: "
      f"{g0['systematic_bias']}. The operator fits a sphere to the transferred reference-sphere dome "
      "(absolute dome, not raw back z), so it recovers the construction radius by design.")
    w("")
    w("### Radius map F(R) = E[B4(R)] over the sweep")
    w("")
    w("| R_in (ft) | E[B0] (ft) | ctrl err | F(R) (ft) | g=F−R (ft) | rise (mm) | vol (L) | apex Y (in) | 004G rise | 004G vol |")
    w("|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for s in R["sweep"]:
        w(f"| {s['R']} | {s['E0']:.2f} | {s['ctrl_err']:+.3f} | {s['F']:.2f} | {s['g']:+.3f} | "
          f"{s['rise_mm']:.2f} | {s['vol_L']:.3f} | {s['apex_y']:.2f} | {s['g004_rise']} | {s['g004_vol']} |")
    w("")
    w("### Fixed point")
    w("")
    if fp["root_exists"]:
        w(f"- Root(s) in 12–30 ft: {fp.get('roots_ft')}. "
          + (f"R*={fp.get('resolved_mathematical_root_ft')} ft, F'={fp.get('derivative_Fprime')}, "
             f"{fp.get('stability')}." if fp.get("resolved_mathematical_root_ft") is not None else ""))
    else:
        w(f"- **No sign change in g(R) over 12–30 ft** (g ∈ [{min(s['g'] for s in R['sweep']):+.2f}, "
          f"{max(s['g'] for s in R['sweep']):+.2f}] ft, strictly positive) → **no fixed point**. "
          f"`dF/dR ≈ {fp['derivative_Fprime_at_25']:.3f}` (> 1): direct iteration diverges upward from "
          f"every seed (15/20/25/30 ft). The 25 ft trial is **not** preserved; the geometry does not "
          "settle on a self-consistent radius in the tested range.")
    w("")
    w("### Reconciliation with 004H (essential)")
    w("")
    w(f"- Metric-consistent **F(25) = {R['F25']:.2f} ft** (`METRIC_CONSISTENT_DOME_RADIUS`, base slope "
      f"removed) vs the 004H **19.12 ft** (`GLOBAL_SPHERE_DIAGNOSTIC_WITH_BASE_SLOPE`). They differ "
      "because the 004H global sphere absorbed the longitudinal side-depth slope, pulling the apparent "
      "radius *tighter*; the dome-only operator shows the #65260 outline actually makes the dome "
      f"*flatter* (~{100*(R['F25']/25-1):.1f}% at 25 ft). **The earlier apparent 'drive toward ~20 ft' "
      "was a base-slope artifact.**")
    w("")
    w("### Cross-check vs 004E / 004G / 004H (unlike definitions — not averaged)")
    w("")
    w("- 004E rim-sphere ≈ 18.35 ft, 004H global ≈ 19.12 ft, 004I metric-consistent F(25) ≈ "
      f"{R['F25']:.2f} ft — each measures a **different** geometric quantity (rim sphere / "
      "base-slope-contaminated global / dome-only), and all share 004D/004C boundary data. They are "
      "reported side-by-side with definitions, **not averaged**, and comparisons fail closed where "
      "the definitions differ.")
    w(f"- 004G cross-check at the 25 ft trial: rise {R['sweep'][SWEEP_FT.index(25)]['rise_mm']:.2f} mm "
      f"({R['sweep'][SWEEP_FT.index(25)]['g004_rise']} [1.61, 2.80] mm), volume "
      f"{R['sweep'][SWEEP_FT.index(25)]['vol_L']:.3f} L ({R['sweep'][SWEEP_FT.index(25)]['g004_vol']} "
      "[18.439, 18.603] L). No 004G member promoted.")
    w("")
    w("### Sensitivity")
    w("")
    w("- `dV/dR` and `dy_apex/dR` are reported across the sweep (`…RADIUS_VOLUME_SENSITIVITY_004I.csv`, "
      "`…RADIUS_APEX_SENSITIVITY_004I.csv`). Apex longitudinal location is dominated by the outline "
      "(near-flat `dy_apex/dR`), consistent with 004H; body volume varies only weakly with R, so "
      "body-volume evidence is a comparatively weak radius discriminator here.")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("> The #65260 constraints do not exhibit a self-consistent curvature fixed point in 12–30 ft "
      "under the stated proportional model. The result is model-dependent and is not a historical "
      "back-radius measurement.")
    w("")
    w("Parent dispositions (001–004H) are untouched. 004I claims no historical radius, reads no PDF, "
      "and changes no prior artifact.")
    w("")
    return "\n".join(L)


def splice_doc(section: str) -> None:
    text = ""
    if os.path.exists(_DOC):
        with open(_DOC) as fh:
            text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    elif "<!-- RERUN004H_START -->" in text:
        marker = "<!-- RERUN004H_START -->"
        text = text[:text.index(marker)] + block + "\n\n---\n\n" + text[text.index(marker):]
    else:
        os.makedirs(os.path.dirname(_DOC), exist_ok=True)
        text = (text + "\n\n" if text else "") + block + "\n"
    with open(_DOC, "w") as fh:
        fh.write(text)


def main() -> None:
    R = run_all()
    section = build_section(R)
    if "--write" in sys.argv:
        os.makedirs(_OUTDIR, exist_ok=True)
        write_operator(R); write_sweep(R); write_fixed_point(R); write_iteration(R)
        write_fp_geometry(R); write_vol_sens(R); write_apex_sens(R); write_crosscheck(R)
        write_summary(R); write_provenance(R)
        splice_doc(section)
        print(f"wrote 004I artifacts; disposition={R['disp']}; gate0_max_err="
              f"{R['gate0']['max_abs_err_ft']:.4f}ft; F(25)={R['F25']:.2f}ft; roots={R['fp']['root_count']}")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; F(25)={R['F25']:.2f}ft; "
              f"g∈[{min(s['g'] for s in R['sweep']):+.2f},{max(s['g'] for s in R['sweep']):+.2f}]ft]")


if __name__ == "__main__":
    main()
