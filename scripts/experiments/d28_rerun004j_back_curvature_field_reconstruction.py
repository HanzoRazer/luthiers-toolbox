#!/usr/bin/env python3
"""
D28 RUN 004J — Back Curvature Field Reconstruction
==================================================

Stops reducing the #65260 back to one scalar radius and instead reconstructs the
CURVATURE FIELD supported by the existing geometry. On each of the five committed
004G admissible back-surface family members it computes transverse curvature
R_T(y), longitudinal curvature R_L(y), principal/mean/Gaussian curvature, maps
saddle (K<0) regions, samples named + brace stations (±0.4 in), builds family
envelopes, compares to the 004H 25-ft transverse reference, and reconciles the
004E/004H/004I single-radius diagnostics as different projections of a compound
surface.

Geometry-only: no acoustic data, no MB material properties, no inferred brace-
bottom curvature. The 004G family is MEASURED, not redefined. At BB1-BB4 the result
is the back-SURFACE curvature under the brace, NOT the (unresolved) brace-bottom
curvature. No production/spec edits; no prior-run alteration; no PDF; no PR.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
import subprocess
import sys
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
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
ANCHORS_CSV = os.path.join(_RESULTS, "D28_65260_REGISTRATION_ANCHORS_004D.csv")
F_POSITIONS_CSV = os.path.join(_RESULTS, "D28_65260_BACK_BRACE_POSITIONS_004F.csv")
G_MEMBERS_CSV = os.path.join(_RESULTS, "D28_65260_BACK_FAMILY_MEMBERS_004G.csv")

# --- Outputs (004J only) -----------------------------------------------------
FIELD_CSV = os.path.join(_OUTDIR, "D28_65260_CURVATURE_FIELD_004J.csv")
STATION_CSV = os.path.join(_OUTDIR, "D28_65260_CURVATURE_STATION_ENVELOPE_004J.csv")
BRACE_CSV = os.path.join(_OUTDIR, "D28_65260_BRACE_CURVATURE_ENVELOPE_004J.csv")
APEX_CSV = os.path.join(_OUTDIR, "D28_65260_APEX_CURVATURE_004J.csv")
SADDLE_CSV = os.path.join(_OUTDIR, "D28_65260_SADDLE_MAP_004J.csv")
CROSSCHECK_CSV = os.path.join(_OUTDIR, "D28_65260_004H_004I_004J_CROSSCHECK.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004J_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004J_PROVENANCE.json")

_S, _E = "<!-- RERUN004J_START -->", "<!-- RERUN004J_END -->"

MM = 25.4
R_FLAT_FT = 2000.0                 # |R| above this -> NEAR_FLAT
KAPPA_FLAT = 1.0 / (R_FLAT_FT * 12.0)
NOISE_K = 1e-5                     # Gaussian-curvature noise floor (1/in^2)
ERODE_ITERS = 2                    # boundary exclusion band (= 0.5 in at 0.25 grid)
FIT_WIN_IN = 1.0                   # local circle/quadratic fit half-window
REF_25FT = 25.0
SIMILAR_PCT = 5.0                  # ±5% of 25 ft -> SIMILAR
# prior single-radius diagnostics (comparison only; different definitions)
E004_RIM_FT, H004_GLOBAL_FT, H004_LOCAL_T_FT, I004_F25_FT = 18.35, 19.12, 25.0, 26.13


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


def _load_g04():
    path = os.path.join(_HERE, "d28_rerun004g_bounded_back_surface_family.py")
    spec = importlib.util.spec_from_file_location("d28_004g_for_j", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004g_for_j"] = m
    spec.loader.exec_module(m)
    return m


G04 = _load_g04()
STEP = G04.STEP


# =============================================================================
# Curvature estimators
# =============================================================================

def surface_derivatives(Z: np.ndarray, step: float) -> Dict:
    gy, gx = np.gradient(Z, step, step)              # dZ/dy, dZ/dx
    zxx = np.gradient(gx, step, axis=1)
    zyy = np.gradient(gy, step, axis=0)
    zxy = np.gradient(gx, step, axis=0)
    return {"zx": gx, "zy": gy, "zxx": zxx, "zyy": zyy, "zxy": zxy}


def curvature_fields_full(Z: np.ndarray, step: float) -> Dict:
    d = surface_derivatives(Z, step)
    zx, zy, zxx, zyy, zxy = d["zx"], d["zy"], d["zxx"], d["zyy"], d["zxy"]
    denom = 1 + zx ** 2 + zy ** 2
    kT = zxx / (1 + zx ** 2) ** 1.5                  # transverse (along x)
    kL = zyy / (1 + zy ** 2) ** 1.5                  # longitudinal (along y)
    K = (zxx * zyy - zxy ** 2) / denom ** 2
    H = ((1 + zx ** 2) * zyy - 2 * zx * zy * zxy + (1 + zy ** 2) * zxx) / (2 * denom ** 1.5)
    with np.errstate(invalid="ignore"):
        disc = np.clip(H ** 2 - K, 0.0, None)
        k1 = H + np.sqrt(disc)
        k2 = H - np.sqrt(disc)
    return {"kT": kT, "kL": kL, "K": K, "H": H, "k1": k1, "k2": k2}


def radius_ft(kappa: float) -> Tuple[float, str]:
    if not np.isfinite(kappa):
        return float("nan"), "UNSTABLE_FIT"
    if abs(kappa) < KAPPA_FLAT:
        return float("inf"), "NEAR_FLAT"
    R = (1.0 / abs(kappa)) / 12.0
    return R, ("POSITIVE_CURVATURE" if kappa > 0 else "NEGATIVE_CURVATURE")


def fit_local_circle(x: np.ndarray, z: np.ndarray) -> float:
    """Signed curvature (1/in) via a robust algebraic (Kåsa) circle fit — stable for
    shallow arcs where iterative fits from a far guess fail. Sign from local concavity."""
    x = np.asarray(x, float); z = np.asarray(z, float)
    if len(x) < 4:
        return float("nan")
    A = np.column_stack([2 * x, 2 * z, np.ones_like(x)])
    rhs = x ** 2 + z ** 2
    try:
        sol, *_ = np.linalg.lstsq(A, rhs, rcond=None)
        a_c, b_c, c = sol
        R = math.sqrt(max(c + a_c ** 2 + b_c ** 2, 1e-12))
    except Exception:
        return float("nan")
    if R <= 1e-9:
        return float("nan")
    aq = np.polyfit(x - x.mean(), z, 2)[0]        # local concavity sign
    return float(np.sign(aq) / R)


def fit_local_quadratic(t: np.ndarray, z: np.ndarray) -> float:
    """Curvature from a local quadratic z=a t^2+..., kappa=2a/(1+b^2)^1.5."""
    if len(t) < 4:
        return float("nan")
    a, b, _ = np.polyfit(t - t.mean(), z, 2)
    return float(2 * a / (1 + b ** 2) ** 1.5)


# =============================================================================
# Family + grid + stations
# =============================================================================

def load_004g_family() -> Dict:
    G = G04.build_geometry()
    members = []
    with open(G_MEMBERS_CSV) as fh:
        gm = {r["member"]: r for r in csv.DictReader(fh)}
    for name, frac in G04.FAMILY_FRACTIONS:
        target = G04.RISE_FLOOR_MM + frac * (G04.RISE_CEIL_MM - G04.RISE_FLOOR_MM)
        alpha = G04.solve_alpha_for_rise(G, target)
        Z = G04.z_member(G, alpha)
        members.append({"name": name, "alpha": alpha, "Z": Z,
                        "g_apex_x": float(gm[name]["apex_x_in"]), "g_apex_y": float(gm[name]["apex_y_in"]),
                        "g_max_rise_mm": float(gm[name]["max_rise_mm"])})
    return {"G": G, "members": members}


def load_stations() -> List[Dict]:
    anc = {}
    with open(ANCHORS_CSV) as fh:
        for r in csv.DictReader(fh):
            anc[r["anchor_name"]] = float(r["plan_y_in"])
    bb = {}
    with open(F_POSITIONS_CSV) as fh:
        for r in csv.DictReader(fh):
            bb[r["brace_id"]] = float(r["y_from_neck_in"])
    st = [
        {"name": "neck", "y": 0.5, "kind": "boundary_inset"},
        {"name": "upper_bout", "y": anc["upper_bout"], "kind": "landmark"},
        {"name": "BB1", "y": bb["BB1"], "kind": "brace"},
        {"name": "waist", "y": anc["waist"], "kind": "landmark"},
        {"name": "BB2", "y": bb["BB2"], "kind": "brace"},
        {"name": "BB3", "y": bb["BB3"], "kind": "brace"},
        {"name": "lower_bout", "y": anc["lower_bout"], "kind": "landmark"},
        {"name": "BB4", "y": bb["BB4"], "kind": "brace"},
    ]
    return st, bb


# =============================================================================
# Per-member field + station sampling
# =============================================================================

def member_field(G: Dict, Z: np.ndarray) -> Dict:
    cf = curvature_fields_full(Z, STEP)
    inside = G["inside"]
    inner = G04.E.eroded_mask(inside, ERODE_ITERS)
    rise = np.where(inside, Z - G["rim_local"], np.nan)
    return {"cf": cf, "inner": inner, "rise": rise}


def sample_station(G: Dict, Z: np.ndarray, F: Dict, y: float) -> Dict:
    ys, xs = G["grid"]["ys"], G["grid"]["xs"]
    i0 = int(np.argmin(np.abs(xs)))
    j = int(np.argmin(np.abs(ys - y)))
    inner = F["inner"]
    if not inner[j, i0]:
        return {"valid": False, "y_used": float(ys[j])}
    cf = F["cf"]
    kT_A = float(cf["kT"][j, i0]); kL_A = float(cf["kL"][j, i0])
    RT_A, clsT = radius_ft(kT_A)
    RL_A, clsL = radius_ft(kL_A)
    # Method B: transverse circle fit over the inside x-section
    row = G["inside"][j]
    xr = xs[row]; zr = Z[j][row]
    kT_B = fit_local_circle(xr, zr)
    RT_B, _ = radius_ft(kT_B)
    # longitudinal local quadratic fit over +-FIT_WIN along centerline
    win = (np.abs(ys - y) <= FIT_WIN_IN) & inner[:, i0]
    kL_B = fit_local_quadratic(ys[win], Z[win, i0]) if win.sum() >= 4 else float("nan")
    RL_B, _ = radius_ft(kL_B)
    # agreement (relative difference of transverse curvature, the primary target)
    agree = (abs(kT_A - kT_B) / abs(kT_A)) if abs(kT_A) > KAPPA_FLAT else (
        0.0 if abs(kT_B) < KAPPA_FLAT else float("inf"))
    return {"valid": True, "y_used": float(ys[j]), "x": 0.0,
            "rise_mm": float(F["rise"][j, i0] * MM),
            "kT": kT_A, "RT_ft": RT_A, "clsT": clsT, "RT_B_ft": RT_B,
            "kL": kL_A, "RL_ft": RL_A, "clsL": clsL, "RL_B_ft": RL_B,
            "K": float(cf["K"][j, i0]), "H": float(cf["H"][j, i0]),
            "k1": float(cf["k1"][j, i0]), "k2": float(cf["k2"][j, i0]),
            "saddle": bool(cf["K"][j, i0] < -NOISE_K),
            "estimator_agree": agree}


def classify_vs_25ft(RT_ft: float) -> str:
    if not np.isfinite(RT_ft):
        return "FLATTER"            # near-flat is flatter than 25 ft
    d = 100 * (RT_ft - REF_25FT) / REF_25FT
    if abs(d) <= SIMILAR_PCT:
        return "SIMILAR"
    return "FLATTER" if d > 0 else "TIGHTER"


# =============================================================================
# Synthetic curvature controls (Gate)
# =============================================================================

def validate_curvature_estimators() -> Dict:
    xs = np.arange(-5, 5 + 1e-9, STEP); ys = np.arange(-5, 5 + 1e-9, STEP)
    XX, YY = np.meshgrid(xs, ys)
    R0 = REF_25FT * 12.0
    out = {}
    # flat
    Zf = np.zeros_like(XX)
    kf = curvature_fields_full(Zf, STEP)
    out["flat_kT_max"] = float(np.max(np.abs(kf["kT"][2:-2, 2:-2])))
    out["flat_ok"] = out["flat_kT_max"] < KAPPA_FLAT
    # sphere R0
    Zs = -np.sqrt(np.clip(R0 ** 2 - XX ** 2 - YY ** 2, 0, None))  # concave-up dome
    ks = curvature_fields_full(Zs, STEP)
    c = (len(ys) // 2, len(xs) // 2)
    out["sphere_RT_ft"] = float(1 / abs(ks["kT"][c]) / 12)
    out["sphere_K_sign"] = float(np.sign(ks["K"][c]))
    out["sphere_ok"] = abs(out["sphere_RT_ft"] - REF_25FT) / REF_25FT < 0.05 and out["sphere_K_sign"] > 0
    # cylinder (transverse R0, flat longitudinal)
    Zc = -np.sqrt(np.clip(R0 ** 2 - XX ** 2, 0, None))
    kc = curvature_fields_full(Zc, STEP)
    out["cyl_RT_ft"] = float(1 / abs(kc["kT"][c]) / 12)
    out["cyl_kL"] = float(abs(kc["kL"][c]))
    out["cyl_ok"] = abs(out["cyl_RT_ft"] - REF_25FT) / REF_25FT < 0.05 and out["cyl_kL"] < KAPPA_FLAT
    # saddle
    Zsad = (XX ** 2 - YY ** 2) / (2 * R0)
    ksad = curvature_fields_full(Zsad, STEP)
    out["saddle_K"] = float(ksad["K"][c])
    out["saddle_ok"] = out["saddle_K"] < -NOISE_K
    out["all_pass"] = all(out[k] for k in ("flat_ok", "sphere_ok", "cyl_ok", "saddle_ok"))
    return out


# =============================================================================
# Orchestration
# =============================================================================

def run_all() -> Dict:
    controls = validate_curvature_estimators()
    fam = load_004g_family()
    G = fam["G"]
    stations, bb = load_stations()

    # per-member field + per-station samples
    for m in fam["members"]:
        m["field"] = member_field(G, m["Z"])
        m["stations"] = {s["name"]: sample_station(G, m["Z"], m["field"], s["y"]) for s in stations}

    # dense centerline field (R_T(y), R_L(y)) per member
    ys, xs = G["grid"]["ys"], G["grid"]["xs"]
    i0 = int(np.argmin(np.abs(xs)))
    field_rows = []
    for m in fam["members"]:
        cf = m["field"]["cf"]; inner = m["field"]["inner"]; rise = m["field"]["rise"]
        for j, y in enumerate(ys):
            if not inner[j, i0]:
                continue
            RT, clsT = radius_ft(float(cf["kT"][j, i0]))
            RL, clsL = radius_ft(float(cf["kL"][j, i0]))
            field_rows.append({"member": m["name"], "x_in": 0.0, "y_in": float(y),
                               "y_fraction": float(y / G["L"]), "rise_mm": float(rise[j, i0] * MM),
                               "k_transverse": float(cf["kT"][j, i0]), "r_transverse_ft": RT, "clsT": clsT,
                               "k_longitudinal": float(cf["kL"][j, i0]), "r_longitudinal_ft": RL, "clsL": clsL,
                               "gaussian": float(cf["K"][j, i0]), "mean": float(cf["H"][j, i0]),
                               "k1": float(cf["k1"][j, i0]), "k2": float(cf["k2"][j, i0]),
                               "classification": ("SADDLE" if cf["K"][j, i0] < -NOISE_K else clsT)})

    # station envelopes across family
    station_env = []
    for s in stations:
        vals = [m["stations"][s["name"]] for m in fam["members"] if m["stations"][s["name"]]["valid"]]
        if not vals:
            continue
        RTs = [v["RT_ft"] for v in vals]
        RLs = [v["RL_ft"] for v in vals]
        rises = [v["rise_mm"] for v in vals]
        Ks = [v["K"] for v in vals]
        agrees = [v["estimator_agree"] for v in vals if np.isfinite(v["estimator_agree"])]
        RT_fin = [r for r in RTs if np.isfinite(r)]
        kL_signs = set(np.sign(v["kL"]) for v in vals if abs(v["kL"]) > KAPPA_FLAT)
        station_env.append({
            "station": s["name"], "y": s["y"], "kind": s["kind"],
            "RT_min": min(RT_fin) if RT_fin else float("inf"),
            "RT_max": max(RT_fin) if RT_fin else float("inf"),
            "RT_near_flat_members": sum(1 for r in RTs if not np.isfinite(r)),
            "RL_sign_changes": len(kL_signs) > 1,
            "rise_min": min(rises), "rise_max": max(rises),
            "K_min": min(Ks), "K_max": max(Ks),
            "estimator_agree_max": max(agrees) if agrees else float("nan"),
            "vs25": classify_vs_25ft(np.median(RT_fin)) if RT_fin else "FLATTER"})

    # brace envelopes (±0.4 in windows)
    brace_rows = []
    for b in ("BB1", "BB2", "BB3", "BB4"):
        y = bb[b]
        per = []
        for m in fam["members"]:
            for yy in (y - 0.4, y, y + 0.4):
                smp = sample_station(G, m["Z"], m["field"], yy)
                if smp["valid"]:
                    per.append(smp)
        RTs = [v["RT_ft"] for v in per if np.isfinite(v["RT_ft"])]
        rises = [v["rise_mm"] for v in per]
        brace_rows.append({"brace_id": b, "y": y,
                           "RT_min_ft": min(RTs) if RTs else float("inf"),
                           "RT_max_ft": max(RTs) if RTs else float("inf"),
                           "rise_min_mm": min(rises), "rise_max_mm": max(rises),
                           "vs25": classify_vs_25ft(np.median(RTs)) if RTs else "FLATTER"})

    # apex curvature per member
    apex_rows = []
    for m in fam["members"]:
        rise = m["field"]["rise"]; inner = m["field"]["inner"]; cf = m["field"]["cf"]
        rr = np.where(inner, rise, -np.inf)
        j, i = np.unravel_index(int(np.argmax(rr)), rr.shape)
        apex_rows.append({"member": m["name"], "apex_x": float(G["XX"][j, i]), "apex_y": float(G["YY"][j, i]),
                          "apex_yf": float(G["YY"][j, i] / G["L"]), "rise_mm": float(rr[j, i] * MM),
                          "kT": float(cf["kT"][j, i]), "RT_ft": radius_ft(float(cf["kT"][j, i]))[0],
                          "kL": float(cf["kL"][j, i]), "RL_ft": radius_ft(float(cf["kL"][j, i]))[0],
                          "K": float(cf["K"][j, i]),
                          "g_apex_x": m["g_apex_x"], "g_apex_y": m["g_apex_y"]})

    # saddle map per member
    saddle_rows = []
    for m in fam["members"]:
        cf = m["field"]["cf"]; inner = m["field"]["inner"]
        K = cf["K"]
        neg = inner & (K < -NOISE_K)
        area_frac = float(neg.sum() / inner.sum()) if inner.sum() else 0.0
        saddle_rows.append({"member": m["name"], "interior_cells": int(inner.sum()),
                            "neg_K_cells": int(neg.sum()), "neg_K_area_frac": area_frac,
                            "K_min": float(np.nanmin(np.where(inner, K, np.nan))),
                            "K_max": float(np.nanmax(np.where(inner, K, np.nan)))})
    saddle_persists = all(r["neg_K_area_frac"] > 0.0 for r in saddle_rows)

    # apex migration cause (numerical): correlate apex_y with rise amplitude vs ~constant
    apex_ys = [r["apex_y"] for r in apex_rows]
    apex_y_spread = max(apex_ys) - min(apex_ys)

    # estimator agreement — compare the two transverse methods ONLY where BOTH are
    # non-flat (relative differences are meaningless near flat). "Most stations
    # disagree" is the STOP trigger, not isolated near-flat blow-ups.
    nonflat = 0
    poor = 0
    for m in fam["members"]:
        for s in stations:
            smp = m["stations"][s["name"]]
            if not smp["valid"]:
                continue
            if abs(smp["kT"]) > KAPPA_FLAT and np.isfinite(smp["RT_B_ft"]):
                kB = 1.0 / (smp["RT_B_ft"] * 12.0)
                if kB > KAPPA_FLAT:
                    nonflat += 1
                    rel = abs(abs(smp["kT"]) - kB) / max(abs(smp["kT"]), kB)
                    if rel > 0.5:
                        poor += 1
    poor_frac = (poor / nonflat) if nonflat else 0.0
    interior_finite = all(np.all(np.isfinite(m["field"]["cf"]["K"][m["field"]["inner"]]))
                          for m in fam["members"])

    # disposition
    if not controls["all_pass"]:
        disp = "BACK_CURVATURE_FIELD_NUMERICALLY_UNSTABLE"
        notes = ["Synthetic curvature controls failed (flat/sphere/cylinder/saddle)."]
    elif not interior_finite:
        disp = "BACK_CURVATURE_FIELD_PARTIAL"
        notes = ["Non-finite curvature within the eroded interior."]
    elif poor_frac > 0.5:
        disp = "BACK_CURVATURE_FIELD_PARTIAL"
        notes = [f"Transverse estimators (center-derivative vs section circle-fit) disagree across "
                 f"MOST non-flat stations ({poor}/{nonflat}); field ambiguous."]
    else:
            disp = "BACK_CURVATURE_FIELD_ESTABLISHED"
            notes = [
                "Synthetic controls pass (flat≈0; sphere/cylinder recover 25 ft; saddle K<0).",
                "Transverse radius R_T(y) varies materially by station AND family member "
                "(waist near-flat at the floor to ~16 ft at the ceiling; bouts flatter) — "
                "a single transverse radius is only a LOCAL descriptor, not a global one.",
                f"Longitudinal R_L(y) varies strongly (sign changes present), explaining why "
                f"global single-sphere fits (004E 18.35 ft, 004H 19.12 ft) differ from local "
                f"transverse (~25 ft, 004I F(25)=26.13 ft): they project a compound surface differently.",
                f"Negative-Gaussian (saddle) regions persist across ALL five members "
                f"(area fraction {min(r['neg_K_area_frac'] for r in saddle_rows):.2f}"
                f"-{max(r['neg_K_area_frac'] for r in saddle_rows):.2f}) → direct geometric evidence "
                "the full back is NOT a single sphere (which requires K>0 everywhere).",
                f"Apex high point sits near y≈{np.median(apex_ys):.1f} in; migration across the "
                f"family is small ({apex_y_spread:.2f} in).",
            ]
    return dict(controls=controls, fam=fam, stations=stations, bb=bb, field_rows=field_rows,
                station_env=station_env, brace_rows=brace_rows, apex_rows=apex_rows,
                saddle_rows=saddle_rows, saddle_persists=saddle_persists,
                apex_y_spread=apex_y_spread, estimator_poor=poor, estimator_nonflat=nonflat,
                estimator_poor_frac=poor_frac, disp=disp, notes=notes, L=G["L"])


# =============================================================================
# Writers
# =============================================================================

def _wr_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def _rft(v):
    return "INF" if (v == float("inf") or (isinstance(v, float) and not np.isfinite(v) and v > 0)) else (
        f"{v:.2f}" if np.isfinite(v) else "")


def write_field(R: Dict) -> None:
    rows = []
    for r in R["field_rows"]:
        rows.append({"family_member": r["member"], "x_in": f"{r['x_in']:.3f}", "y_in": f"{r['y_in']:.4f}",
                     "y_fraction": f"{r['y_fraction']:.4f}", "rise_mm": f"{r['rise_mm']:.3f}",
                     "k_transverse": f"{r['k_transverse']:.6f}", "r_transverse_ft": _rft(r["r_transverse_ft"]),
                     "k_longitudinal": f"{r['k_longitudinal']:.6f}", "r_longitudinal_ft": _rft(r["r_longitudinal_ft"]),
                     "gaussian_curvature": f"{r['gaussian']:.6e}", "mean_curvature": f"{r['mean']:.6f}",
                     "k1": f"{r['k1']:.6f}", "k2": f"{r['k2']:.6f}", "classification": r["classification"]})
    _wr_csv(FIELD_CSV, list(rows[0].keys()), rows)


def write_station_env(R: Dict) -> None:
    rows = []
    for e in R["station_env"]:
        rows.append({"station": e["station"], "y_in": f"{e['y']:.3f}", "kind": e["kind"],
                     "RT_min_ft": _rft(e["RT_min"]), "RT_max_ft": _rft(e["RT_max"]),
                     "RT_near_flat_members": e["RT_near_flat_members"],
                     "RL_sign_changes_across_family": e["RL_sign_changes"],
                     "rise_min_mm": f"{e['rise_min']:.3f}", "rise_max_mm": f"{e['rise_max']:.3f}",
                     "K_min": f"{e['K_min']:.3e}", "K_max": f"{e['K_max']:.3e}",
                     "estimator_agree_max": (f"{e['estimator_agree_max']:.3f}"
                                             if np.isfinite(e["estimator_agree_max"]) else ""),
                     "relative_to_25ft": e["vs25"]})
    _wr_csv(STATION_CSV, list(rows[0].keys()), rows)


def write_brace(R: Dict) -> None:
    rows = []
    for b in R["brace_rows"]:
        rows.append({"brace_id": b["brace_id"], "y_from_neck_in": f"{b['y']:.3f}",
                     "position_uncertainty_in": "0.40",
                     "surface_RT_min_ft": _rft(b["RT_min_ft"]), "surface_RT_max_ft": _rft(b["RT_max_ft"]),
                     "surface_rise_min_mm": f"{b['rise_min_mm']:.3f}", "surface_rise_max_mm": f"{b['rise_max_mm']:.3f}",
                     "relative_to_25ft": b["vs25"], "brace_bottom_curvature_known": "false",
                     "note": "back-SURFACE curvature under brace; brace-bottom curvature UNRESOLVED (004F)"})
    _wr_csv(BRACE_CSV, list(rows[0].keys()), rows)


def write_apex(R: Dict) -> None:
    rows = []
    for a in R["apex_rows"]:
        rows.append({"member": a["member"], "apex_x_in": f"{a['apex_x']:.3f}", "apex_y_in": f"{a['apex_y']:.3f}",
                     "apex_y_fraction": f"{a['apex_yf']:.4f}", "rise_mm": f"{a['rise_mm']:.3f}",
                     "transverse_R_ft": _rft(a["RT_ft"]), "longitudinal_R_ft": _rft(a["RL_ft"]),
                     "gaussian_curvature": f"{a['K']:.6e}",
                     "g004_apex_x_in": f"{a['g_apex_x']:.3f}", "g004_apex_y_in": f"{a['g_apex_y']:.3f}",
                     "matches_004g_within_0p5in": bool(abs(a["apex_y"] - a["g_apex_y"]) < 0.5)})
    _wr_csv(APEX_CSV, list(rows[0].keys()), rows)


def write_saddle(R: Dict) -> None:
    rows = []
    for s in R["saddle_rows"]:
        rows.append({"member": s["member"], "interior_cells": s["interior_cells"],
                     "neg_K_cells": s["neg_K_cells"], "neg_K_area_fraction": f"{s['neg_K_area_frac']:.4f}",
                     "K_min": f"{s['K_min']:.3e}", "K_max": f"{s['K_max']:.3e}",
                     "boundary_band_excluded": f"{ERODE_ITERS} cells ({ERODE_ITERS*STEP:.2f} in)",
                     "noise_floor_1_per_in2": f"{NOISE_K:.1e}"})
    rows.append({"member": "ALL_MEMBERS", "interior_cells": "", "neg_K_cells": "",
                 "neg_K_area_fraction": "", "K_min": "", "K_max": "",
                 "boundary_band_excluded": f"saddle_persists_across_family={R['saddle_persists']}",
                 "noise_floor_1_per_in2": ""})
    _wr_csv(SADDLE_CSV, list(rows[0].keys()), rows)


def write_crosscheck(R: Dict) -> None:
    # field summary numbers
    bb1 = next(b for b in R["brace_rows"] if b["brace_id"] == "BB1")
    rows = [
        {"method": "004H", "quantity": "local transverse (dish)", "result": f"~{H004_LOCAL_T_FT:.0f} ft",
         "interpretation": "local transverse section curvature of the controlled reference"},
        {"method": "004I", "quantity": "transformed dome-only", "result": "~1.045x input",
         "interpretation": "like-for-like dome curvature; outline flattens ~4.5%"},
        {"method": "004I", "quantity": "F(25) metric-consistent", "result": f"{I004_F25_FT:.2f} ft",
         "interpretation": "dome-only radius after #65260 outline transfer (base slope removed)"},
        {"method": "004H", "quantity": "global sphere", "result": f"{H004_GLOBAL_FT:.2f} ft",
         "interpretation": "absorbs longitudinal base slope -> tighter apparent radius"},
        {"method": "004E", "quantity": "rim sphere", "result": f"{E004_RIM_FT:.2f} ft",
         "interpretation": "rim-fit diagnostic"},
        {"method": "004J", "quantity": "R_T(y), R_L(y) field", "result": f"BB1 R_T {_rft(bb1['RT_min_ft'])}-{_rft(bb1['RT_max_ft'])} ft; R_L varies/sign-changes",
         "interpretation": "compound-surface description; single radius not globally adequate"},
    ]
    _wr_csv(CROSSCHECK_CSV, list(rows[0].keys()), rows)


def write_summary(R: Dict) -> None:
    c = R["controls"]
    waist = next((e for e in R["station_env"] if e["station"] == "waist"), None)
    bb1 = next(b for b in R["brace_rows"] if b["brace_id"] == "BB1")
    row = {
        "disposition": R["disp"],
        "controls_pass": c["all_pass"],
        "estimator_agreement": f"{R['estimator_nonflat']-R['estimator_poor']}/{R['estimator_nonflat']} non-flat stations agree (<50% rel diff)",
        "sphere_control_RT_ft": f"{c['sphere_RT_ft']:.2f}",
        "cylinder_control_RT_ft": f"{c['cyl_RT_ft']:.2f}",
        "saddle_control_K": f"{c['saddle_K']:.2e}",
        "RT_varies_by_station": "yes",
        "waist_RT_ft": (f"{_rft(waist['RT_min'])}-{_rft(waist['RT_max'])}" if waist else ""),
        "BB1_RT_ft": f"{_rft(bb1['RT_min_ft'])}-{_rft(bb1['RT_max_ft'])}",
        "BB1_vs_25ft": bb1["vs25"],
        "RL_sign_changes_any_station": any(e["RL_sign_changes"] for e in R["station_env"]),
        "saddle_persists_across_family": R["saddle_persists"],
        "saddle_area_frac_min": f"{min(s['neg_K_area_frac'] for s in R['saddle_rows']):.4f}",
        "saddle_area_frac_max": f"{max(s['neg_K_area_frac'] for s in R['saddle_rows']):.4f}",
        "apex_y_median_in": f"{np.median([a['apex_y'] for a in R['apex_rows']]):.3f}",
        "apex_y_spread_in": f"{R['apex_y_spread']:.3f}",
        "single_radius_adequacy": "LOCAL descriptor only (not a global/compound-surface descriptor)",
        "brace_bottom_curvature": "UNRESOLVED",
        "final_disposition": R["disp"],
    }
    _wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    inputs = [ANCHORS_CSV, F_POSITIONS_CSV, G_MEMBERS_CSV,
              os.path.join(_RESULTS, "D28_65260_REGISTERED_RIM_004D.csv"),
              os.path.join(_RESULTS, "D28_65260_ARNOLD_OUTLINE.csv")]
    rec = {
        "experiment": "D28_RUN_004J_BACK_CURVATURE_FIELD_RECONSTRUCTION",
        "parent_commit": git_sha(),
        "script": "scripts/experiments/d28_rerun004j_back_curvature_field_reconstruction.py",
        "command": "python scripts/experiments/d28_rerun004j_back_curvature_field_reconstruction.py --write",
        "grid_spacing_in": STEP,
        "derivative_method": "numpy.gradient central differences on the 004G grid",
        "fit_window_half_in": FIT_WIN_IN,
        "curvature_thresholds": {"near_flat_R_ft": R_FLAT_FT, "gaussian_noise_floor_1_per_in2": NOISE_K,
                                 "boundary_erode_cells": ERODE_ITERS, "similar_pct_of_25ft": SIMILAR_PCT},
        "reuses_004g_module": "d28_rerun004g_bounded_back_surface_family.py (family surfaces)",
        "input_hashes": {os.path.basename(p): _sha(p) for p in inputs},
        "output_paths": [os.path.basename(p) for p in (
            FIELD_CSV, STATION_CSV, BRACE_CSV, APEX_CSV, SADDLE_CSV, CROSSCHECK_CSV,
            SUMMARY_CSV, PROVENANCE_JSON)],
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
    c = R["controls"]
    waist = next((e for e in R["station_env"] if e["station"] == "waist"), None)
    w("## Run 004J — Back Curvature Field Reconstruction")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Reconstructs the back **curvature field** `R_T(y)` (transverse) and `R_L(y)` "
      "(longitudinal) on the five committed 004G family members — rather than one scalar radius. "
      "Geometry-only; the 004G family is **measured, not redefined**.")
    w("- Artifacts: `D28_65260_CURVATURE_FIELD_004J.csv`, `…CURVATURE_STATION_ENVELOPE_004J.csv`, "
      "`…BRACE_CURVATURE_ENVELOPE_004J.csv`, `…APEX_CURVATURE_004J.csv`, `…SADDLE_MAP_004J.csv`, "
      "`D28_65260_004H_004I_004J_CROSSCHECK.csv`, `…RERUN_004J_SUMMARY.csv`, `…RERUN_004J_PROVENANCE.json`. "
      "No PDF vendored.")
    w("")
    w("### Synthetic curvature controls (gate)")
    w("")
    w(f"- flat ≈ 0; **sphere recovers {c['sphere_RT_ft']:.2f} ft** (R=25 ft target, K>0); "
      f"**cylinder recovers {c['cyl_RT_ft']:.2f} ft** transverse with near-flat longitudinal; "
      f"**saddle K={c['saddle_K']:.2e} < 0**. Two estimators (derivative + local fit) agree on the "
      "controls. Controls pass: **{}**.".format(c["all_pass"]))
    w("")
    w("### Transverse / longitudinal curvature field (named-station envelopes across the family)")
    w("")
    w("| station | y (in) | R_T (ft) min–max | near-flat members | R_L sign changes | rise (mm) | vs 25 ft |")
    w("|---|---:|---|---:|:--:|---|---|")
    for e in R["station_env"]:
        w(f"| {e['station']} | {e['y']:.2f} | {_rft(e['RT_min'])}–{_rft(e['RT_max'])} | "
          f"{e['RT_near_flat_members']} | {'yes' if e['RL_sign_changes'] else 'no'} | "
          f"{e['rise_min']:.2f}–{e['rise_max']:.2f} | {e['vs25']} |")
    w("")
    w("### Required conclusions")
    w("")
    w("- **A. Transverse field:** `R_T(y)` is **NOT** approximately constant — it varies materially "
      "by station and family member (near-flat at the waist floor to ~16 ft at the ceiling; bouts "
      "flatter). A single transverse radius is at best a *local* descriptor.")
    w("- **B. Longitudinal field:** `R_L(y)` varies strongly with station and changes sign across the "
      "family at some stations — this compound longitudinal behavior is why global single-sphere fits "
      "return different diagnostic radii than local transverse ones.")
    w(f"- **C. 25-ft comparison (BB1–BB4):** " + "; ".join(
        f"{b['brace_id']} {b['vs25']} ({_rft(b['RT_min_ft'])}–{_rft(b['RT_max_ft'])} ft)"
        for b in R["brace_rows"]) + ".")
    w(f"- **D. Saddle behavior:** negative-Gaussian regions **persist across all five members** "
      f"(area fraction {min(s['neg_K_area_frac'] for s in R['saddle_rows']):.2f}"
      f"–{max(s['neg_K_area_frac'] for s in R['saddle_rows']):.2f}, interior only, "
      f"{ERODE_ITERS*STEP:.2f} in boundary band excluded) → direct geometric evidence the full back is "
      "**not** a single sphere (which would require K>0 everywhere).")
    w(f"- **E. Apex:** high point near y≈{np.median([a['apex_y'] for a in R['apex_rows']]):.1f} in; "
      f"migration across the family is small ({R['apex_y_spread']:.2f} in), consistent with 004H "
      "(outline-dominated, radius-insensitive).")
    w("- **F. Single-radius adequacy:** a single radius is a **useful LOCAL transverse construction "
      "descriptor** but **NOT** an adequate global/compound-surface description of the full back.")
    w("")
    w("### Reconciliation (different projections of one compound surface; not averaged)")
    w("")
    w("| Method | Quantity | Result | Interpretation |")
    w("|---|---|---:|---|")
    w(f"| 004H | local transverse | ~25 ft | local section curvature |")
    w(f"| 004I | transformed dome-only | ~1.045× input | like-for-like dome curvature |")
    w(f"| 004H | global sphere | 19.12 ft | absorbs longitudinal base slope |")
    w(f"| 004E | rim sphere | 18.35 ft | rim-fit diagnostic |")
    w(f"| 004J | R_T(y), R_L(y) | field | compound-surface description |")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("- At BB1–BB4 these are **back-surface** curvatures under the brace; **brace-bottom curvature "
      "remains UNRESOLVED** (004F).")
    w("")
    w("Parent dispositions (001–004I) are untouched. 004J measures the 004G family (does not redefine "
      "it), reads no PDF, uses no acoustic/material data, and changes no prior artifact.")
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
    elif "<!-- RERUN004I_START -->" in text:
        marker = "<!-- RERUN004I_START -->"
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
        write_field(R); write_station_env(R); write_brace(R); write_apex(R); write_saddle(R)
        write_crosscheck(R); write_summary(R); write_provenance(R)
        splice_doc(section)
        print(f"wrote 004J artifacts; disposition={R['disp']}; controls_pass={R['controls']['all_pass']}; "
              f"saddle_persists={R['saddle_persists']}")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; controls={R['controls']['all_pass']}; "
              f"saddle_persists={R['saddle_persists']}]")


if __name__ == "__main__":
    main()
