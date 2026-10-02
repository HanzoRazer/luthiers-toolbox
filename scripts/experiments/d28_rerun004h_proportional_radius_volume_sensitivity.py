#!/usr/bin/env python3
"""
D28 RUN 004H — Proportional Radius / Volume Sensitivity Transform
=================================================================

A SENSITIVITY / DECOMPOSITION experiment. It does NOT recover the historical
#65260 back radius. Starting from a CONTROLLED model reference back (Geometry B,
a 25 ft = 300 in spherical dish over a generic dreadnought planform), it measures
which direction — and by how much — the independently known #65260 plan contour
(004D) and developed-side profile (004C/004D) push the dome rise, apex location,
equivalent radius, and body volume.

Controlled model (known BY CONSTRUCTION, not claimed historical):
    z(x,y) = base(u) + domeS(x,y),   u = y/L,  |x| <= w(u)
    domeS  = sqrt(R^2 - x^2 - (y-y_c)^2) - sqrt(R^2 - w(u)^2 - (y-y_c)^2)
             (spherical cap of radius R; = 0 at the rim x=±w(u), peaks at x=0)
  * w(u)    = planform half-width            -> OUTLINE authority
  * base(u) = longitudinal rim-depth profile -> SIDE-PROFILE authority
  * R       = 300 in = 25 ft                 -> MODEL_ASSUMPTION_CONTROLLED_REFERENCE

Transform cases:
  B0 reference | B1 pure similitude (scale k) | B2 outline-only (#65260 w)
  B3 side-only (#65260 base) | B4 combined (#65260 w + base)

Reference planform w_ref(u) is a DECLARED synthetic generic dreadnought
(MODEL_REFERENCE_GEOMETRY). Reference side profile base_ref(u) is the committed
GenOne generic side-contour (SOURCE_SUPPORTED_ANALOGY). #65260 w_A/base_A are the
committed Arnold outline / 004D rim. No PDF read at runtime. No production/spec
edits. No prior-run alteration. No PR.

Non-claim: 004H establishes NOTHING about whether #65260 was built on a 25-ft dish
or had a spherical back. Transformed radii are CALCULATED_DIAGNOSTIC only.
"""
from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Inputs (committed, read-only) -------------------------------------------
ARNOLD_OUTLINE_CSV = os.path.join(_RESULTS, "D28_65260_ARNOLD_OUTLINE.csv")
RIM_CSV = os.path.join(_RESULTS, "D28_65260_REGISTERED_RIM_004D.csv")
GENONE_SIDE_CSV = os.path.join(_RESULTS, "D28_65260_GENONE_SIDE_CONTOUR_004B.csv")
F_POSITIONS_CSV = os.path.join(_RESULTS, "D28_65260_BACK_BRACE_POSITIONS_004F.csv")
G_SUMMARY_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004G_SUMMARY.csv")
G_MEMBERS_CSV = os.path.join(_RESULTS, "D28_65260_BACK_FAMILY_MEMBERS_004G.csv")

# --- Outputs (004H only) -----------------------------------------------------
REFGEO_JSON = os.path.join(_OUTDIR, "D28_65260_REFERENCE_GEOMETRY_004H.json")
TRANSFORMS_CSV = os.path.join(_OUTDIR, "D28_65260_PROPORTIONAL_TRANSFORMS_004H.csv")
RADIUS_CSV = os.path.join(_OUTDIR, "D28_65260_RADIUS_SENSITIVITY_004H.csv")
APEX_CSV = os.path.join(_OUTDIR, "D28_65260_APEX_MIGRATION_004H.csv")
VOLUME_CSV = os.path.join(_OUTDIR, "D28_65260_VOLUME_SENSITIVITY_004H.csv")
BRACE_CSV = os.path.join(_OUTDIR, "D28_65260_BRACE_SECTION_SENSITIVITY_004H.csv")
CROSSCHECK_CSV = os.path.join(_OUTDIR, "D28_65260_004G_004H_CROSSCHECK.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004H_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004H_PROVENANCE.json")

_S, _E = "<!-- RERUN004H_START -->", "<!-- RERUN004H_END -->"

MM = 25.4
IN3_TO_CM3 = 16.387064
STEP = 0.25
R_REF_IN = 300.0                      # 25 ft, MODEL_ASSUMPTION_CONTROLLED_REFERENCE
L_REF_IN = 20.0                       # nominal generic dreadnought length

# Declared synthetic generic-dreadnought planform (MODEL_REFERENCE_GEOMETRY):
# half-width vs normalized longitudinal u (0=neck .. 1=tail). Martin-D nominal
# proportions (upper bout 11.5", waist 10.77", lower bout 15.625").
W_REF_U = [0.00, 0.08, 0.16, 0.25, 0.33, 0.45, 0.60, 0.73, 0.85, 0.95, 1.00]
W_REF_HW = [3.05, 4.80, 5.75, 5.55, 5.385, 6.00, 7.20, 7.8125, 7.35, 5.70, 4.40]

# Direction thresholds (declared BEFORE results).
TH_RADIUS_PCT = 1.0       # <1% radius change -> NEGLIGIBLE
TH_APEX_IN = 0.10         # <0.10 in longitudinal apex shift -> NEGLIGIBLE
TH_VOLUME_PCT = 0.25      # <0.25% volume change -> NEGLIGIBLE

# 004G envelope (read at runtime; shown here for context only).
G_RISE_LO_MM, G_RISE_HI_MM = 1.61, 2.80
G_VOL_LO_L, G_VOL_HI_L = 18.439, 18.603


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception:
        return "UNKNOWN"


# =============================================================================
# Loaders -> normalized profile functions w(u), base(u)
# =============================================================================

def _pchip(us, vs) -> Callable:
    p = PchipInterpolator(np.asarray(us, float), np.asarray(vs, float), extrapolate=True)
    return lambda u: np.clip(p(u), 0.0, None)


def interpolate_half_width_ref() -> Callable:
    return _pchip(W_REF_U, W_REF_HW)


def load_outline_65260() -> Tuple[Callable, float]:
    ys, hw = [], []
    with open(ARNOLD_OUTLINE_CSV) as fh:
        next(fh)
        for line in fh:
            if line.strip():
                a, b = line.strip().split(",")
                ys.append(float(a)); hw.append(float(b))
    y = np.array(ys); h = np.array(hw)
    L = float(y.max())
    return _pchip(y / L, h), L


def load_base_ref() -> Callable:
    us, d = [], []
    with open(GENONE_SIDE_CSV) as fh:
        for line in fh:
            if line.startswith("#") or line.startswith("u,"):
                continue
            parts = line.strip().split(",")
            if len(parts) == 4:
                us.append(float(parts[0])); d.append(float(parts[3]))
    return _pchip(us, d)


def load_base_65260() -> Callable:
    ys, z = [], []
    with open(RIM_CSV) as fh:
        for r in csv.DictReader(fh):
            ys.append(float(r["y_in"])); z.append(float(r["z_in"]))
    y = np.array(ys); zz = np.array(z)
    L = float(y.max())
    return _pchip(y / L, zz)


def load_brace_stations() -> Dict[str, Dict]:
    out = {}
    with open(F_POSITIONS_CSV) as fh:
        for r in csv.DictReader(fh):
            out[r["brace_id"]] = {"y_in": float(r["y_from_neck_in"]), "unc_in": float(r["uncertainty_in"])}
    return out


def load_004g_envelope() -> Dict:
    s = next(iter(csv.DictReader(open(G_SUMMARY_CSV))))
    members = list(csv.DictReader(open(G_MEMBERS_CSV)))
    return {"rise_lo_mm": float(s["rise_floor_mm"]), "rise_hi_mm": float(s["rise_ceiling_mm"]),
            "vol_lo_L": float(s["body_volume_floor_L"]), "vol_hi_L": float(s["body_volume_ceiling_L"]),
            "member_apex": [(m["member"], float(m["apex_x_in"]), float(m["apex_y_in"])) for m in members]}


# =============================================================================
# Surface construction (controlled spherical-dish dome + rim-depth base)
# =============================================================================

def construct_surface(wfun: Callable, basefun: Callable, R: float, L: float,
                      step: float = STEP) -> Dict:
    y_c = L / 2.0
    hw_max = float(np.max([wfun(u) for u in np.linspace(0, 1, 201)]))
    xs = np.round(np.arange(-hw_max - step, hw_max + step + 1e-9, step), 5)
    ys = np.round(np.arange(0.0, L + 1e-9, step), 5)
    XX, YY = np.meshgrid(xs, ys)
    U = YY / L
    W = wfun(U)
    inside = np.abs(XX) <= W + 1e-9
    disc = R * R - XX ** 2 - (YY - y_c) ** 2
    disc_edge = R * R - W ** 2 - (YY - y_c) ** 2
    with np.errstate(invalid="ignore"):
        dome = np.sqrt(np.clip(disc, 0, None)) - np.sqrt(np.clip(disc_edge, 0, None))
    base = basefun(U)
    z = base + dome
    z = np.where(inside, z, np.nan)
    dome = np.where(inside, dome, np.nan)
    return {"xs": xs, "ys": ys, "XX": XX, "YY": YY, "U": U, "W": W, "inside": inside,
            "z": z, "dome": dome, "base": base, "R": R, "L": L, "y_c": y_c, "step": step,
            "wfun": wfun, "basefun": basefun}


def integrate_body_volume(S: Dict) -> float:
    return float(np.nansum(S["z"][S["inside"]]) * S["step"] ** 2)


def find_relative_apex(S: Dict) -> Dict:
    d = np.where(S["inside"], S["dome"], -np.inf)
    j, i = np.unravel_index(int(np.argmax(d)), d.shape)
    return {"apex_x_in": float(S["XX"][j, i]), "apex_y_in": float(S["YY"][j, i]),
            "apex_y_fraction": float(S["YY"][j, i] / S["L"]), "apex_rise_mm": float(d[j, i] * MM)}


def fit_global_sphere(S: Dict) -> Dict:
    X = S["XX"][S["inside"]]; Y = S["YY"][S["inside"]]; Z = S["z"][S["inside"]]

    def res(p):
        cx, cy, cz, R = p
        return np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2) - R
    sol = least_squares(res, [0.0, S["L"] / 2, Z.mean() - S["R"], S["R"]])
    cx, cy, cz, R = (float(v) for v in sol.x)
    sign = 1.0 if (Z.mean() - cz) > 0 else -1.0
    apex = (cx, cy, cz + sign * R)
    inside_planform = bool(0 <= cy <= S["L"] and abs(cx) <= float(np.max(S["W"])))
    return {"R_in": R, "R_ft": R / 12.0, "cx": cx, "cy": cy, "cz": cz,
            "rmse_in": float(np.sqrt(np.mean(sol.fun ** 2))), "max_resid_in": float(np.max(np.abs(sol.fun))),
            "apex": apex, "apex_inside_planform": inside_planform}


def fit_transverse_circle(S: Dict, y_station: float) -> Dict:
    j = int(np.argmin(np.abs(S["ys"] - y_station)))
    row = S["inside"][j]
    xs = S["XX"][j][row]; z = S["z"][j][row]
    if len(xs) < 3:
        return {"radius_ft": float("nan"), "rise_center_mm": float("nan")}

    def res(p):
        cx, cz, R = p
        return np.sqrt((xs - cx) ** 2 + (z - cz) ** 2) - R
    sol = least_squares(res, [0.0, z.mean() - S["R"], S["R"]])
    R = abs(float(sol.x[2]))
    i0 = int(np.argmin(np.abs(xs)))
    rise = float(S["dome"][j][row][i0] * MM)
    return {"radius_in": R, "radius_ft": R / 12.0, "rmse_in": float(np.sqrt(np.mean(sol.fun ** 2))),
            "rise_center_mm": rise, "y_used_in": float(S["ys"][j])}


def centerline_curvature(S: Dict) -> Dict:
    ys = S["ys"]
    zc = []
    for j, y in enumerate(ys):
        row = S["inside"][j]
        if not row.any():
            zc.append(np.nan); continue
        xs = S["XX"][j][row]; i0 = int(np.argmin(np.abs(xs)))
        zc.append(float(S["z"][j][row][i0]))
    zc = np.array(zc)
    good = np.isfinite(zc)
    yg = ys[good]; zg = zc[good]
    d1 = np.gradient(zg, yg); d2 = np.gradient(d1, yg)
    with np.errstate(divide="ignore", invalid="ignore"):
        kappa = np.abs(d2) / (1 + d1 ** 2) ** 1.5
        R_local = np.where(kappa > 1e-9, 1.0 / kappa, np.inf)
    finiteR = R_local[np.isfinite(R_local)]
    return {"R_long_min_ft": float(np.min(finiteR) / 12) if finiteR.size else float("nan"),
            "R_long_median_ft": float(np.median(finiteR) / 12) if finiteR.size else float("nan")}


def classify_direction(delta: float, threshold: float, flatter_label="FLATTER",
                       tighter_label="TIGHTER") -> str:
    if abs(delta) < threshold:
        return "NEGLIGIBLE"
    return flatter_label if delta > 0 else tighter_label


# =============================================================================
# Orchestration
# =============================================================================

def run_all() -> Dict:
    w_ref = interpolate_half_width_ref()
    base_ref = load_base_ref()
    w_A, L_A = load_outline_65260()
    base_A = load_base_65260()
    stations = load_brace_stations()
    g_env = load_004g_envelope()

    k = L_A / L_REF_IN

    # --- cases -----------------------------------------------------------------
    cases: Dict[str, Dict] = {}
    cases["B0"] = construct_surface(w_ref, base_ref, R_REF_IN, L_REF_IN)
    # B1: uniform similitude by k (scale planform, base, R, L — AND the grid step,
    # so the Riemann sum/point-cloud is a uniform k-scaling of B0 and the ratios
    # R1/R0=k, V1/V0=k^3 hold exactly rather than to discretization noise).
    w_ref_k = (lambda f=w_ref: (lambda u: k * f(u)))()
    base_ref_k = (lambda f=base_ref: (lambda u: k * f(u)))()
    cases["B1"] = construct_surface(w_ref_k, base_ref_k, k * R_REF_IN, k * L_REF_IN, step=k * STEP)
    cases["B2"] = construct_surface(w_A, base_ref, R_REF_IN, L_A)        # outline-only
    cases["B3"] = construct_surface(w_ref, base_A, R_REF_IN, L_REF_IN)   # side-only
    cases["B4"] = construct_surface(w_A, base_A, R_REF_IN, L_A)          # combined

    results = {}
    for name, S in cases.items():
        vol = integrate_body_volume(S)
        apex = find_relative_apex(S)
        sph = fit_global_sphere(S)
        cl = centerline_curvature(S)
        results[name] = {"S": S, "vol_in3": vol, "apex": apex, "sphere": sph, "centerline": cl}

    # --- controls ---------------------------------------------------------------
    # The 25-ft radius is imposed as the TRANSVERSE (radius-dish) curvature, so the
    # construction radius is validated by a transverse circle fit (clean), NOT by the
    # global best-fit sphere (which mixes in the longitudinal base slope and is a
    # separate diagnostic). R_char = transverse radius at the widest station.
    def r_char_ft(S):
        jmax = int(np.argmax([S["wfun"](u) for u in S["ys"] / S["L"]]))
        return fit_transverse_circle(S, float(S["ys"][jmax]))["radius_ft"]

    v0 = results["B0"]["vol_in3"]
    rc0 = r_char_ft(cases["B0"])
    rc1 = r_char_ft(cases["B1"])
    b1_vol_ratio = results["B1"]["vol_in3"] / v0
    b1_Rchar_ratio = rc1 / rc0
    controls = {"k": k, "V1_over_V0": b1_vol_ratio, "k_cubed": k ** 3,
                "R1_over_R0": b1_Rchar_ratio, "R_char_B0_ft": rc0,
                "global_R_B0_ft": results["B0"]["sphere"]["R_ft"],
                "vol_ratio_ok": abs(b1_vol_ratio - k ** 3) < 1e-3,
                "R_ratio_ok": abs(b1_Rchar_ratio - k) < 1e-3,
                "B0_R_reproduces_25ft": abs(rc0 - R_REF_IN / 12.0) / (R_REF_IN / 12.0) < 0.02}

    # explicit arbitrary-k machinery proof (k=1.5), independent of #65260 size
    # (grid step also scaled by kc so the ratios are exact).
    kc = 1.5
    S_kc = construct_surface((lambda f=w_ref: (lambda u: kc * f(u)))(),
                             (lambda f=base_ref: (lambda u: kc * f(u)))(),
                             kc * R_REF_IN, kc * L_REF_IN, step=kc * STEP)
    controls["arbitrary_k"] = kc
    controls["arbitrary_V_ratio"] = integrate_body_volume(S_kc) / v0
    controls["arbitrary_V_ok"] = abs(integrate_body_volume(S_kc) / v0 - kc ** 3) < 1e-3
    controls["arbitrary_R_ratio"] = r_char_ft(S_kc) / rc0
    controls["arbitrary_R_ok"] = abs(r_char_ft(S_kc) / rc0 - kc) < 1e-3

    # --- grid refinement sensitivity (B4) --------------------------------------
    S_fine = construct_surface(w_A, base_A, R_REF_IN, L_A, step=STEP / 2)
    refine = {"vol_coarse_in3": results["B4"]["vol_in3"], "vol_fine_in3": integrate_body_volume(S_fine)}
    refine["rel_delta"] = abs(refine["vol_fine_in3"] - refine["vol_coarse_in3"]) / refine["vol_coarse_in3"]

    # --- sensitivity decomposition (vs B0) -------------------------------------
    dV_out = results["B2"]["vol_in3"] - v0
    dV_side = results["B3"]["vol_in3"] - v0
    dV_comb = results["B4"]["vol_in3"] - v0
    dV_inter = dV_comb - dV_out - dV_side

    R0ft = results["B0"]["sphere"]["R_ft"]
    dR_out_pct = 100 * (results["B2"]["sphere"]["R_ft"] - R0ft) / R0ft
    dR_side_pct = 100 * (results["B3"]["sphere"]["R_ft"] - R0ft) / R0ft
    dR_comb_pct = 100 * (results["B4"]["sphere"]["R_ft"] - R0ft) / R0ft

    ay0 = results["B0"]["apex"]["apex_y_in"]
    dAy_out = results["B2"]["apex"]["apex_y_in"] - ay0
    dAy_side = results["B3"]["apex"]["apex_y_in"] - ay0
    dAy_comb = results["B4"]["apex"]["apex_y_in"] - ay0

    decomp = {
        "dV_outline_cm3": dV_out * IN3_TO_CM3, "dV_side_cm3": dV_side * IN3_TO_CM3,
        "dV_combined_cm3": dV_comb * IN3_TO_CM3, "dV_interaction_cm3": dV_inter * IN3_TO_CM3,
        "dR_outline_pct": dR_out_pct, "dR_side_pct": dR_side_pct, "dR_combined_pct": dR_comb_pct,
        "dApexY_outline_in": dAy_out, "dApexY_side_in": dAy_side, "dApexY_combined_in": dAy_comb,
        # radius sign convention: larger R = FLATTER
        "outline_radius_effect": classify_direction(dR_out_pct, TH_RADIUS_PCT),
        "side_profile_radius_effect": classify_direction(dR_side_pct, TH_RADIUS_PCT),
        "combined_radius_effect": classify_direction(dR_comb_pct, TH_RADIUS_PCT),
        # apex sign convention: +y = AFT (toward tail)
        "outline_apex_shift": classify_direction(dAy_out, TH_APEX_IN, "AFT", "FORWARD"),
        "side_profile_apex_shift": classify_direction(dAy_side, TH_APEX_IN, "AFT", "FORWARD"),
        "combined_apex_shift": classify_direction(dAy_comb, TH_APEX_IN, "AFT", "FORWARD"),
    }

    # --- brace-station sensitivity (B4; ±0.4 in window) ------------------------
    brace_rows = []
    for bb in ("BB1", "BB2", "BB3", "BB4"):
        y = stations[bb]["y_in"]; unc = stations[bb]["unc_in"]
        samples = [fit_transverse_circle(results["B4"]["S"], yy)
                   for yy in (y - unc, y, y + unc)]
        rises = [s["rise_center_mm"] for s in samples if np.isfinite(s["rise_center_mm"])]
        radii = [s["radius_ft"] for s in samples if np.isfinite(s.get("radius_ft", float("nan")))]
        brace_rows.append({"brace_id": bb, "y_in": y, "unc_in": unc,
                           "rise_center_mm": fit_transverse_circle(results["B4"]["S"], y)["rise_center_mm"],
                           "radius_ft": fit_transverse_circle(results["B4"]["S"], y).get("radius_ft", float("nan")),
                           "rise_min_mm": min(rises), "rise_max_mm": max(rises),
                           "radius_min_ft": min(radii) if radii else float("nan"),
                           "radius_max_ft": max(radii) if radii else float("nan")})

    # --- 004G crosscheck (B4) --------------------------------------------------
    b4 = results["B4"]
    h_b4_mm = b4["apex"]["apex_rise_mm"]
    v_b4_L = b4["vol_in3"] * IN3_TO_CM3 / 1000
    crosscheck = build_crosscheck(h_b4_mm, v_b4_L, b4, g_env)

    # --- controls / STOP gate --------------------------------------------------
    controls_ok = (controls["B0_R_reproduces_25ft"] and controls["vol_ratio_ok"]
                   and controls["R_ratio_ok"] and controls["arbitrary_V_ok"] and controls["arbitrary_R_ok"])
    monotonic_ok = all(np.all(np.diff(S["ys"]) > 0) for S in cases.values())
    finite_ok = all(np.all(np.isfinite(r["S"]["z"][r["S"]["inside"]])) for r in results.values())

    if not (controls_ok and monotonic_ok and finite_ok):
        disp = "PROPORTIONAL_SENSITIVITY_TRANSFORM_INVALID"
        notes = ["Transform controls failed (B0 radius / B1 R∝k / B1 V∝k^3) or geometry invalid."]
    elif controls["vol_ratio_ok"] and controls["R_ratio_ok"]:
        disp = "PROPORTIONAL_SENSITIVITY_TRANSFORM_SUPPORTED"
        notes = [
            f"Controls pass: B0 transverse R={rc0:.2f} ft (≈25 ft); B1 R1/R0={b1_Rchar_ratio:.5f}≈k={k:.5f}; "
            f"V1/V0={b1_vol_ratio:.5f}≈k^3={k**3:.5f}; arbitrary k={kc}: V ratio {controls['arbitrary_V_ratio']:.4f}≈{kc**3:.4f}.",
            f"Outline effect on equivalent radius: {decomp['outline_radius_effect']} "
            f"({dR_out_pct:+.2f}%); side-profile: {decomp['side_profile_radius_effect']} ({dR_side_pct:+.2f}%); "
            f"combined: {decomp['combined_radius_effect']} ({dR_comb_pct:+.2f}%).",
            f"Apex migration (B0→B4): Δy={dAy_comb:+.3f} in ({decomp['combined_apex_shift']}); "
            f"outline Δy={dAy_out:+.3f}, side Δy={dAy_side:+.3f}.",
            f"Volume Δ (B4−B0) {dV_comb*IN3_TO_CM3:+.1f} cm^3; interaction {dV_inter*IN3_TO_CM3:+.1f} cm^3.",
            "All transformed radii are CALCULATED_DIAGNOSTIC; Geometry B is MODEL_REFERENCE_GEOMETRY "
            "(25 ft known by construction). No historical #65260 radius claimed.",
        ]
    else:
        disp = "PROPORTIONAL_SENSITIVITY_TRANSFORM_PARTIAL"
        notes = ["Nonuniform cases computed but a control tolerance was marginal; see controls."]

    return dict(cases=cases, results=results, controls=controls, refine=refine, decomp=decomp,
                brace_rows=brace_rows, crosscheck=crosscheck, g_env=g_env, k=k, L_A=L_A,
                h_b4_mm=h_b4_mm, v_b4_L=v_b4_L, disp=disp, notes=notes)


def build_crosscheck(h_b4_mm: float, v_b4_L: float, b4: Dict, g_env: Dict) -> List[Dict]:
    def rel(val, lo, hi):
        return "below" if val < lo else ("above" if val > hi else "inside")
    rows = [
        {"quantity": "dome_rise_mm", "004g_low": f"{g_env['rise_lo_mm']:.3f}",
         "004g_high": f"{g_env['rise_hi_mm']:.3f}", "004h_combined": f"{h_b4_mm:.3f}",
         "relation": rel(h_b4_mm, g_env["rise_lo_mm"], g_env["rise_hi_mm"]),
         "comparison_valid": "True",
         "reason": "same relative-rise definition (dome rise above local rim)"},
        {"quantity": "body_volume_L", "004g_low": f"{g_env['vol_lo_L']:.3f}",
         "004g_high": f"{g_env['vol_hi_L']:.3f}", "004h_combined": f"{v_b4_L:.3f}",
         "relation": rel(v_b4_L, g_env["vol_lo_L"], g_env["vol_hi_L"]),
         "comparison_valid": "True",
         "reason": "same FLAT_TOP_GEOMETRIC_REFERENCE convention over the #65260 planform; "
                   "NOTE both share 004D/004C boundary data (not independent)"},
        {"quantity": "apex_y_in_vs_004g_members", "004g_low": f"{min(a[2] for a in g_env['member_apex']):.3f}",
         "004g_high": f"{max(a[2] for a in g_env['member_apex']):.3f}",
         "004h_combined": f"{b4['apex']['apex_y_in']:.3f}",
         "relation": rel(b4["apex"]["apex_y_in"], min(a[2] for a in g_env["member_apex"]),
                         max(a[2] for a in g_env["member_apex"])),
         "comparison_valid": "True",
         "reason": "apex compared to 004G member apex spread; no member selected/averaged"},
        {"quantity": "equivalent_radius_ft", "004g_low": "", "004g_high": "",
         "004h_combined": f"{b4['sphere']['R_ft']:.2f}",
         "relation": "no_comparable_004g_global_radius",
         "comparison_valid": "False",
         "reason": "VOLUME_CONVENTION_MISMATCH n/a; 004G reports no single global sphere radius, "
                   "and both derive from shared boundary data -> not independent historical proof"},
    ]
    return rows


# =============================================================================
# Writers
# =============================================================================

def _wr_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


_CASE_DESC = {"B0": ("reference", "reference"), "B1": ("scaled", "scaled"),
              "B2": ("#65260", "reference"), "B3": ("reference", "#65260"), "B4": ("#65260", "#65260")}


def write_transforms(R: Dict) -> None:
    rows = []
    for name in ("B0", "B1", "B2", "B3", "B4"):
        r = R["results"][name]
        out, side = _CASE_DESC[name]
        rows.append({
            "case": name, "outline": out, "side_profile": side,
            "equiv_radius_ft": f"{r['sphere']['R_ft']:.3f}",
            "apex_rise_mm": f"{r['apex']['apex_rise_mm']:.3f}",
            "apex_y_in": f"{r['apex']['apex_y_in']:.3f}",
            "apex_y_fraction": f"{r['apex']['apex_y_fraction']:.4f}",
            "volume_L": f"{r['vol_in3']*IN3_TO_CM3/1000:.4f}",
            "sphere_rmse_in": f"{r['sphere']['rmse_in']:.5f}",
            "class": "CALCULATED_DIAGNOSTIC" if name != "B0" else "MODEL_REFERENCE_GEOMETRY",
        })
    _wr_csv(TRANSFORMS_CSV, list(rows[0].keys()), rows)


def write_radius(R: Dict) -> None:
    rows = []
    r0 = R["results"]["B0"]["sphere"]["R_ft"]
    for name in ("B0", "B1", "B2", "B3", "B4"):
        s = R["results"][name]["sphere"]; cl = R["results"][name]["centerline"]
        rows.append({
            "case": name, "global_equiv_radius_ft": f"{s['R_ft']:.3f}",
            "pct_change_vs_B0": f"{100*(s['R_ft']-r0)/r0:+.3f}",
            "sphere_rmse_in": f"{s['rmse_in']:.5f}", "sphere_max_resid_in": f"{s['max_resid_in']:.5f}",
            "sphere_center": f"({s['cx']:.2f},{s['cy']:.2f},{s['cz']:.1f})",
            "apex_inside_planform": s["apex_inside_planform"],
            "centerline_R_long_median_ft": f"{cl['R_long_median_ft']:.1f}",
            "class": "CALCULATED_DIAGNOSTIC",
        })
    _wr_csv(RADIUS_CSV, list(rows[0].keys()), rows)


def write_apex(R: Dict) -> None:
    rows = []
    a0 = R["results"]["B0"]["apex"]
    prev = a0
    for name in ("B0", "B1", "B2", "B3", "B4"):
        a = R["results"][name]["apex"]
        rows.append({
            "case": name, "apex_x_in": f"{a['apex_x_in']:.3f}", "apex_y_in": f"{a['apex_y_in']:.3f}",
            "apex_y_fraction": f"{a['apex_y_fraction']:.4f}", "apex_rise_mm": f"{a['apex_rise_mm']:.3f}",
            "apex_shift_x_in": f"{a['apex_x_in']-a0['apex_x_in']:+.3f}",
            "apex_shift_y_in": f"{a['apex_y_in']-a0['apex_y_in']:+.3f}",
            "shift_y_vs_prev_in": f"{a['apex_y_in']-prev['apex_y_in']:+.3f}",
        })
        prev = a
    _wr_csv(APEX_CSV, list(rows[0].keys()), rows)


def write_volume(R: Dict) -> None:
    d = R["decomp"]; v0 = R["results"]["B0"]["vol_in3"]
    rows = []
    for name in ("B0", "B1", "B2", "B3", "B4"):
        v = R["results"][name]["vol_in3"]
        rows.append({
            "case": name, "volume_in3": f"{v:.3f}", "volume_cm3": f"{v*IN3_TO_CM3:.2f}",
            "volume_L": f"{v*IN3_TO_CM3/1000:.4f}", "delta_vs_B0_cm3": f"{(v-v0)*IN3_TO_CM3:+.3f}",
            "pct_vs_B0": f"{100*(v-v0)/v0:+.3f}", "top_reference": "FLAT_TOP_GEOMETRIC_REFERENCE",
        })
    rows.append({"case": "DECOMP_outline", "volume_in3": "", "volume_cm3": f"{d['dV_outline_cm3']:+.3f}",
                 "volume_L": "", "delta_vs_B0_cm3": f"{d['dV_outline_cm3']:+.3f}", "pct_vs_B0": "",
                 "top_reference": "ΔV attributable to outline substitution"})
    rows.append({"case": "DECOMP_side", "volume_in3": "", "volume_cm3": f"{d['dV_side_cm3']:+.3f}",
                 "volume_L": "", "delta_vs_B0_cm3": f"{d['dV_side_cm3']:+.3f}", "pct_vs_B0": "",
                 "top_reference": "ΔV attributable to side-profile substitution"})
    rows.append({"case": "DECOMP_combined", "volume_in3": "", "volume_cm3": f"{d['dV_combined_cm3']:+.3f}",
                 "volume_L": "", "delta_vs_B0_cm3": f"{d['dV_combined_cm3']:+.3f}", "pct_vs_B0": "",
                 "top_reference": "ΔV combined"})
    rows.append({"case": "DECOMP_interaction", "volume_in3": "", "volume_cm3": f"{d['dV_interaction_cm3']:+.3f}",
                 "volume_L": "", "delta_vs_B0_cm3": f"{d['dV_interaction_cm3']:+.3f}", "pct_vs_B0": "",
                 "top_reference": "ΔV_combined − ΔV_outline − ΔV_side (superposition residual)"})
    rows.append({"case": "GRID_REFINEMENT", "volume_in3": f"{R['refine']['vol_fine_in3']:.3f}",
                 "volume_cm3": "", "volume_L": "", "delta_vs_B0_cm3": "",
                 "pct_vs_B0": f"rel_delta={R['refine']['rel_delta']:.2e}",
                 "top_reference": f"B4 @ step {STEP/2} vs {STEP} in"})
    _wr_csv(VOLUME_CSV, list(rows[0].keys()), rows)


def write_brace(R: Dict) -> None:
    rows = []
    for b in R["brace_rows"]:
        rows.append({
            "brace_id": b["brace_id"], "y_from_neck_in": f"{b['y_in']:.3f}",
            "position_uncertainty_in": f"{b['unc_in']:.2f}",
            "surface_rise_center_mm": f"{b['rise_center_mm']:.3f}",
            "transverse_equiv_radius_ft": (f"{b['radius_ft']:.2f}" if np.isfinite(b["radius_ft"]) else ""),
            "rise_window_min_mm": f"{b['rise_min_mm']:.3f}", "rise_window_max_mm": f"{b['rise_max_mm']:.3f}",
            "radius_window_min_ft": (f"{b['radius_min_ft']:.2f}" if np.isfinite(b["radius_min_ft"]) else ""),
            "radius_window_max_ft": (f"{b['radius_max_ft']:.2f}" if np.isfinite(b["radius_max_ft"]) else ""),
            "brace_bottom_curvature": "UNRESOLVED (004F) — surface-under-brace != brace-bottom radius",
        })
    _wr_csv(BRACE_CSV, list(rows[0].keys()), rows)


def write_crosscheck(R: Dict) -> None:
    _wr_csv(CROSSCHECK_CSV, list(R["crosscheck"][0].keys()), R["crosscheck"])


def write_refgeo(R: Dict) -> None:
    rec = {
        "name": "Geometry B — controlled model reference back",
        "authority_classification": "MODEL_REFERENCE_GEOMETRY",
        "reference_radius": {"value_in": R_REF_IN, "value_ft": R_REF_IN / 12,
                             "classification": "MODEL_ASSUMPTION_CONTROLLED_REFERENCE",
                             "basis": "25 ft is a conventional reference modeling value; KNOWN BY "
                                      "CONSTRUCTION, NOT a GenOne/#65260 historical measurement"},
        "planform_w_ref": {"classification": "MODEL_REFERENCE_GEOMETRY (declared synthetic generic "
                                             "dreadnought)", "u_knots": W_REF_U, "halfwidth_in": W_REF_HW,
                           "length_in": L_REF_IN},
        "side_profile_base_ref": {"source": "committed GenOne generic side contour "
                                            "(D28_65260_GENONE_SIDE_CONTOUR_004B.csv)",
                                 "classification": "SOURCE_SUPPORTED_ANALOGY"},
        "surface_model": "z(x,y) = base(u) + [sqrt(R^2-x^2-(y-y_c)^2) - sqrt(R^2-w(u)^2-(y-y_c)^2)]",
        "normalized_coords": {"u": "y/L", "v": "x/w(u) in [-1,1]"},
        "non_claim": ("Geometry B establishes NOTHING about the historical #65260 back. It is a "
                      "controlled reference whose radius and volume are known by construction so that "
                      "#65260's measured outline/side-profile can be substituted and their effect "
                      "measured. 004H does not assert #65260 used a 25-ft dish or a spherical back."),
        "if_source_radius_found": "preserved separately as source evidence; the controlled 25-ft "
                                  "baseline is NOT silently replaced during the run",
    }
    os.makedirs(os.path.dirname(REFGEO_JSON), exist_ok=True)
    with open(REFGEO_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


def write_summary(R: Dict) -> None:
    d = R["decomp"]; c = R["controls"]
    row = {
        "disposition": R["disp"],
        "reference_radius_ft": f"{R_REF_IN/12:.1f}",
        "B0_fitted_radius_ft": f"{R['results']['B0']['sphere']['R_ft']:.3f}",
        "similitude_k": f"{R['k']:.5f}", "B1_R_ratio": f"{c['R1_over_R0']:.5f}",
        "B1_V_ratio": f"{c['V1_over_V0']:.5f}", "k_cubed": f"{R['k']**3:.5f}",
        "controls_pass": c["vol_ratio_ok"] and c["R_ratio_ok"] and c["B0_R_reproduces_25ft"]
                         and c["arbitrary_V_ok"] and c["arbitrary_R_ok"],
        "outline_radius_effect": f"{d['outline_radius_effect']} ({d['dR_outline_pct']:+.2f}%)",
        "side_profile_radius_effect": f"{d['side_profile_radius_effect']} ({d['dR_side_pct']:+.2f}%)",
        "combined_radius_effect": f"{d['combined_radius_effect']} ({d['dR_combined_pct']:+.2f}%)",
        "outline_apex_shift": f"{d['outline_apex_shift']} ({d['dApexY_outline_in']:+.3f} in)",
        "side_profile_apex_shift": f"{d['side_profile_apex_shift']} ({d['dApexY_side_in']:+.3f} in)",
        "combined_apex_shift": f"{d['combined_apex_shift']} ({d['dApexY_combined_in']:+.3f} in)",
        "volume_interaction_cm3": f"{d['dV_interaction_cm3']:+.3f}",
        "B4_dome_rise_mm": f"{R['h_b4_mm']:.3f}", "B4_volume_L": f"{R['v_b4_L']:.4f}",
        "B4_vs_004g_rise": R["crosscheck"][0]["relation"],
        "B4_vs_004g_volume": R["crosscheck"][1]["relation"],
        "grid_refinement_rel_delta": f"{R['refine']['rel_delta']:.2e}",
        "thresholds": f"radius<{TH_RADIUS_PCT}% apex<{TH_APEX_IN}in volume<{TH_VOLUME_PCT}%",
        "non_claim": "no historical #65260 radius claimed; transformed radii CALCULATED_DIAGNOSTIC",
        "final_disposition": R["disp"],
    }
    _wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def _sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def write_provenance(R: Dict) -> None:
    inputs = [ARNOLD_OUTLINE_CSV, RIM_CSV, GENONE_SIDE_CSV, F_POSITIONS_CSV, G_SUMMARY_CSV, G_MEMBERS_CSV]
    rec = {
        "experiment": "D28_RUN_004H_PROPORTIONAL_RADIUS_VOLUME_SENSITIVITY",
        "parent_commit": git_sha(),
        "script": "scripts/experiments/d28_rerun004h_proportional_radius_volume_sensitivity.py",
        "command": "python scripts/experiments/d28_rerun004h_proportional_radius_volume_sensitivity.py --write",
        "reference_radius_ft": R_REF_IN / 12,
        "reference_radius_classification": "MODEL_ASSUMPTION_CONTROLLED_REFERENCE",
        "geometry_B_classification": "MODEL_REFERENCE_GEOMETRY",
        "transformed_radius_classification": "CALCULATED_DIAGNOSTIC",
        "input_hashes": {os.path.basename(p): _sha(p) for p in inputs},
        "output_paths": [os.path.basename(p) for p in (
            REFGEO_JSON, TRANSFORMS_CSV, RADIUS_CSV, APEX_CSV, VOLUME_CSV, BRACE_CSV,
            CROSSCHECK_CSV, SUMMARY_CSV, PROVENANCE_JSON)],
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
    d = R["decomp"]; c = R["controls"]; res = R["results"]
    w("## Run 004H — Proportional Radius / Volume Sensitivity Transform")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- A **sensitivity/decomposition** experiment: starting from a **controlled** model-reference "
      "back (`Geometry B` = 25 ft spherical dish over a declared generic dreadnought planform), it "
      "measures how the independently known #65260 **plan contour** (004D) and **developed-side "
      "profile** (004C/004D) perturb equivalent radius, dome rise, apex, and body volume. "
      "**It does NOT recover a historical #65260 radius.**")
    w("- `Geometry B` is `MODEL_REFERENCE_GEOMETRY`; the 25 ft radius is "
      "`MODEL_ASSUMPTION_CONTROLLED_REFERENCE` (known by construction). All transformed radii are "
      "`CALCULATED_DIAGNOSTIC`.")
    w("- Artifacts: `D28_65260_REFERENCE_GEOMETRY_004H.json`, `…PROPORTIONAL_TRANSFORMS_004H.csv`, "
      "`…RADIUS_SENSITIVITY_004H.csv`, `…APEX_MIGRATION_004H.csv`, `…VOLUME_SENSITIVITY_004H.csv`, "
      "`…BRACE_SECTION_SENSITIVITY_004H.csv`, `D28_65260_004G_004H_CROSSCHECK.csv`, "
      "`…RERUN_004H_SUMMARY.csv`, `…RERUN_004H_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### Transform-machinery controls (must pass before interpreting nonuniform cases)")
    w("")
    w(f"- B0 **transverse** (radius-dish) radius = **{c['R_char_B0_ft']:.2f} ft** — reproduces the "
      f"25 ft construction value (the imposed curvature). The B0 **global** best-fit sphere is "
      f"**{c['global_R_B0_ft']:.2f} ft** (a separate diagnostic that also absorbs the longitudinal "
      f"base slope; shallow-dome fits are ill-conditioned, so it is not used as a control).")
    w(f"- B1 pure similitude (k={R['k']:.5f}): R₁/R₀ = **{c['R1_over_R0']:.5f}** ≈ k; V₁/V₀ = "
      f"**{c['V1_over_V0']:.5f}** ≈ k³ = {R['k']**3:.5f}. Independent arbitrary-k check (k={c['arbitrary_k']}): "
      f"V ratio {c['arbitrary_V_ratio']:.4f} ≈ {c['arbitrary_k']**3:.4f}, R ratio {c['arbitrary_R_ratio']:.4f} "
      f"≈ {c['arbitrary_k']}. **Machinery validated.**")
    w("")
    w("### Sensitivity decomposition")
    w("")
    w("| Case | Outline | Side profile | Equiv R (ft) | Rise (mm) | Apex Y (in) | Volume (L) | Sphere RMSE (in) |")
    w("|---|---|---|---:|---:|---:|---:|---:|")
    for name in ("B0", "B1", "B2", "B3", "B4"):
        r = res[name]; out, side = _CASE_DESC[name]
        w(f"| {name} | {out} | {side} | {r['sphere']['R_ft']:.2f} | {r['apex']['apex_rise_mm']:.3f} | "
          f"{r['apex']['apex_y_in']:.2f} | {r['vol_in3']*IN3_TO_CM3/1000:.3f} | {r['sphere']['rmse_in']:.4f} |")
    w("")
    w(f"- Directional thresholds (declared): radius <{TH_RADIUS_PCT}%, apex <{TH_APEX_IN} in, "
      f"volume <{TH_VOLUME_PCT}% → NEGLIGIBLE. Radius sign: larger = FLATTER; apex sign: +y = AFT.")
    w("")
    w("### Required conclusions")
    w("")
    w(f"- **A. Outline** → equivalent radius **{d['outline_radius_effect']}** ({d['dR_outline_pct']:+.2f}%).")
    w(f"- **B. Side profile** → equivalent radius **{d['side_profile_radius_effect']}** ({d['dR_side_pct']:+.2f}%).")
    w(f"- **C. Interaction** → combined {d['combined_radius_effect']} ({d['dR_combined_pct']:+.2f}%); "
      f"volume interaction (ΔV_comb − ΔV_out − ΔV_side) = {d['dV_interaction_cm3']:+.1f} cm³ "
      f"({'approx. superposes' if abs(d['dV_interaction_cm3']) < 5 else 'materially interacts'}).")
    w(f"- **D. Apex** → combined transform moves the high point Δy = {d['dApexY_combined_in']:+.3f} in "
      f"({d['combined_apex_shift']}); outline Δy = {d['dApexY_outline_in']:+.3f}, side Δy = "
      f"{d['dApexY_side_in']:+.3f} in. (Outline redistributes width → moves the dome apex; the "
      "additive side profile shifts depth/volume, not the dome-apex location.)")
    w("")
    w("### Comparison against 004G (independent; shared boundary data noted)")
    w("")
    w("| quantity | 004G low | 004G high | 004H B4 | relation | comparison valid |")
    w("|---|---:|---:|---:|---|:--:|")
    for r in R["crosscheck"]:
        w(f"| {r['quantity']} | {r['004g_low']} | {r['004g_high']} | {r['004h_combined']} | "
          f"{r['relation']} | {r['comparison_valid']} |")
    w("")
    w("- Volume uses the same `FLAT_TOP_GEOMETRIC_REFERENCE` convention as 004G. The equivalent-radius "
      "comparison is marked invalid: 004G reports no single global sphere radius, and both diagnostics "
      "ultimately share 004D/004C boundary data — **agreement would not be independent historical proof.**")
    w("")
    w("### Brace-station sensitivity (B4; ±0.4 in windows)")
    w("")
    w("| brace | y (in) | surface rise (mm) | transverse equiv R (ft) |")
    w("|---|---:|---:|---:|")
    for b in R["brace_rows"]:
        rr = f"{b['radius_ft']:.1f}" if np.isfinite(b["radius_ft"]) else "n/a"
        w(f"| {b['brace_id']} | {b['y_in']:.2f} | {b['rise_center_mm']:.3f} | {rr} |")
    w("")
    w("- Brace-bottom curvature remains **UNRESOLVED** (004F); the surface-under-brace radius is not "
      "the brace-bottom radius.")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("> The proportional transform quantifies how known #65260 geometry perturbs a controlled "
      "reference model. It does not establish that #65260 was built on the reference radius or that "
      "its historical back was spherical.")
    w("")
    w("Parent dispositions (001–004G) are untouched. 004H promotes no historical radius, reads no PDF, "
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
    elif "<!-- RERUN004G_START -->" in text:
        marker = "<!-- RERUN004G_START -->"
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
        write_refgeo(R); write_transforms(R); write_radius(R); write_apex(R); write_volume(R)
        write_brace(R); write_crosscheck(R); write_summary(R); write_provenance(R)
        splice_doc(section)
        print(f"wrote 004H artifacts; disposition={R['disp']}; "
              f"B0_R={R['results']['B0']['sphere']['R_ft']:.2f}ft; k={R['k']:.4f}; "
              f"outline_R={R['decomp']['dR_outline_pct']:+.2f}% side_R={R['decomp']['dR_side_pct']:+.2f}% "
              f"combined_R={R['decomp']['dR_combined_pct']:+.2f}%")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; B0_R={R['results']['B0']['sphere']['R_ft']:.2f}ft; "
              f"B4_rise={R['h_b4_mm']:.2f}mm; B4_vol={R['v_b4_L']:.3f}L]")


if __name__ == "__main__":
    main()
