#!/usr/bin/env python3
"""
D28 RUN 004D — Developed-Side / Plan-Outline Registration
=========================================================

Registers the 004C source-constrained developed-side coordinate s in [0, 30.4375]
onto the verified Arnold/JD plan-view perimeter, producing the first defensible 3D
rim-edge reconstruction for #65260:

    R(s) = ( x(s), y(s), H(s) )

where (x, y) are plan-view rim coordinates obtained by registering the developed
coordinate against the plan outline, and z = H(s) is the UNCHANGED 004C side
height.

This is a REGISTRATION problem, not a radius fit. The governing relation is

    s  ->  p  ->  (x, y)

with s the developed coordinate (004C), p in [0, 1] normalized plan-perimeter
progress, and (x, y) the Arnold/JD plan rim. We solve for a monotonic transform
p = g(u), u = s / 30.4375, anchored at source-supported landmarks:

    hard anchors : neck (0), waist (004C recon station), tail (30.4375)
    prior-only   : upper-bout / lower-bout developed stations (GenOne proportional
                   priors from the committed 004C landmark artifact)

Program principle (carried forward): the registration solution is reported BEFORE
it is judged. The mapping, derivatives, residuals, and anchor behavior are
preserved first; only then is physical admissibility assessed. A local
stretch/compression factor that appears unintuitive is not "corrected" merely
because of expectation. "Physically inadmissible" is a property of the tested
model interpretation, not of the mathematics itself.

No sphere fit governs this run. No Sevy high point. 30.4375 in (developed side)
and ~26.73 in (smoothed plan half-perimeter) / ~24.48 in (raw plan half-perimeter)
are DIFFERENT geometric quantities; none is forced equal to another. 004C side
heights, the Arnold/JD outline, and all prior run artifacts are read-only. No
production/spec/authority edits. No PDF vendored. No PR.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.interpolate import CubicHermiteSpline, PchipInterpolator
from scipy.optimize import brentq
from scipy.signal import find_peaks

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                    "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")

# --- Inputs (all committed, read-only) ---------------------------------------
OUTLINE_CSV = os.path.join(_RESULTS, "D28_65260_ARNOLD_OUTLINE.csv")
EXTRACTION_JSON = os.path.join(_RESULTS, "D28_65260_RERUN_003_EXTRACTION.json")
AUTH_004C_JSON = os.path.join(_RESULTS, "D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json")
PROFILE_004C_CSV = os.path.join(_RESULTS, "D28_65260_CONSTRAINED_SIDE_PROFILE_004C.csv")
LANDMARK_004C_CSV = os.path.join(_RESULTS, "D28_65260_LANDMARK_RECONSTRUCTION_004C.csv")
SUMMARY_004C_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004C_SUMMARY.csv")

# --- Outputs (004D only) -----------------------------------------------------
AUTHORITY_JSON = os.path.join(_RESULTS, "D28_65260_REGISTRATION_AUTHORITY_004D.json")
ANCHORS_CSV = os.path.join(_RESULTS, "D28_65260_REGISTRATION_ANCHORS_004D.csv")
MAPPING_CSV = os.path.join(_RESULTS, "D28_65260_DEVELOPED_PLAN_MAPPING_004D.csv")
RIM_CSV = os.path.join(_RESULTS, "D28_65260_REGISTERED_RIM_004D.csv")
ANALYSIS_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004D_ANALYSIS.csv")
SUMMARY_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004D_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_RESULTS, "D28_65260_RERUN_004D_PROVENANCE.json")

_S, _E = "<!-- RERUN004D_START -->", "<!-- RERUN004D_END -->"

WAIST_H = 4.220          # 004C waist side height (validation target)
RIM_STEP_IN = 0.125      # dense sampling step (plus landmark/source stations)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       cwd=_REPO_ROOT).decode().strip()
    except Exception:
        return "UNKNOWN"


# =============================================================================
# 004C side profile (Z authority) — rebuilt EXACTLY as 004C (PCHIP through the
# same source points) so Z matches 004C at every source station.
# =============================================================================

def validate_source_points(xs: Sequence[float], dev_len: float) -> None:
    """Fail-closed guard for a 004C source-profile station list."""
    xs = list(xs)
    if abs(dev_len - 30.4375) > 1e-9:
        raise ValueError("STOP: 004C developed length != 30.4375")
    if len(xs) < 3:
        raise ValueError("STOP: malformed 004C source profile (too few stations)")
    if xs[0] != 0.0 or abs(xs[-1] - dev_len) > 1e-9:
        raise ValueError("STOP: 004C source endpoints malformed")
    if list(xs) != sorted(set(xs)):
        raise ValueError("STOP: malformed 004C source profile (non-ascending/duplicate)")


def load_004c_side_profile() -> Dict:
    with open(AUTH_004C_JSON) as fh:
        auth = json.load(fh)
    dev_len = float(auth["developed_side_length_in"])
    stationed = {float(d["station_in"]): float(d["height_in"])
                 for d in auth["stationed_side_heights"]}
    bottom = auth["named_landmarks"]["bottom"]
    src = sorted(stationed.items())
    src.append((float(bottom["station_in"]), float(bottom["height_in"])))
    src.sort()
    xs = np.array([p[0] for p in src])
    ys = np.array([p[1] for p in src])
    validate_source_points([float(v) for v in xs], dev_len)
    H = PchipInterpolator(xs, ys, extrapolate=False)
    return {"dev_len": dev_len, "src_points": src, "H": H}


def waist_developed_station(H: Callable, lo: float = 9.0, hi: float = 12.0) -> float:
    def g(s): return float(H(s)) - WAIST_H
    if g(lo) * g(hi) > 0:
        raise SystemExit("STOP: 004C waist height not bracketed in [9, 12]")
    return float(brentq(g, lo, hi, xtol=1e-9))


# =============================================================================
# Arnold/JD plan outline (XY authority). RAW half-profile x=half_width(y).
# =============================================================================

def load_arnold_outline() -> Dict:
    ys: List[float] = []
    hw: List[float] = []
    with open(OUTLINE_CSV) as fh:
        next(fh)
        for line in fh:
            if not line.strip():
                continue
            a, b = line.strip().split(",")
            ys.append(float(a))
            hw.append(float(b))
    y = np.array(ys)
    x = np.array(hw)
    if y[0] != 0.0:
        raise SystemExit("STOP: outline does not start at neck (y=0)")
    if not np.all(np.diff(y) > 0):
        raise SystemExit("STOP: outline y not strictly ascending")
    return {"y": y, "x": x, "L": float(y[-1])}


def compute_outline_arclength(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Cumulative plan-perimeter arc length along the one-side outline from neck."""
    ds = np.hypot(np.diff(x), np.diff(y))
    return np.concatenate([[0.0], np.cumsum(ds)])


def _smoothed_half_width(x: np.ndarray) -> np.ndarray:
    """Replicate the 003/004C boxcar smoothing used for landmark detection and
    the legacy 'plan half-perimeter' value (26.73 in). Boundary mode='same'
    introduces endpoint artifacts (hence raw is used for working geometry)."""
    k = max(3, int(0.02 * len(x)) | 1)
    return np.convolve(x, np.ones(k) / k, mode="same")


def identify_outline_landmarks(y: np.ndarray, x_raw: np.ndarray) -> Dict:
    """Detect waist / upper-bout / lower-bout longitudinal (y) positions on the
    SMOOTHED half-width (consistent with Runs 003/004C), then report both the raw
    and smoothed plan-arc fractions. XY are taken from the RAW outline."""
    x_s = _smoothed_half_width(x_raw)
    s_raw = compute_outline_arclength(y, x_raw)
    s_sm = compute_outline_arclength(y, x_s)
    A_raw = float(s_raw[-1])
    A_sm = float(s_sm[-1])

    lb_i = int(np.argmax(x_s))
    peaks, _ = find_peaks(x_s[:lb_i + 1], prominence=0.03)
    peaks = [p for p in peaks if 0.05 * y.max() < y[p] < 0.5 * y.max()]
    ub_i = int(peaks[int(np.argmax(x_s[peaks]))]) if peaks else int(
        np.argmax(np.where(y < 0.28 * y.max(), x_s, -1)))
    wi = ub_i + int(np.argmin(x_s[ub_i:lb_i + 1]))

    def pack(i: int) -> Dict:
        return {"y_in": float(y[i]), "half_width_in": float(x_raw[i]),
                "plan_arc_raw_in": float(s_raw[i]), "plan_frac_raw": float(s_raw[i] / A_raw),
                "plan_arc_sm_in": float(s_sm[i]), "plan_frac_sm": float(s_sm[i] / A_sm)}

    return {"upper_bout": pack(ub_i), "waist": pack(wi), "lower_bout": pack(lb_i),
            "A_raw": A_raw, "A_sm": A_sm, "s_raw": s_raw}


def load_genone_landmark_priors() -> Dict[str, float]:
    """Developed-side bout stations as committed GenOne proportional priors
    (from the 004C landmark artifact). Longitudinal priors ONLY; no depth."""
    out: Dict[str, float] = {}
    with open(LANDMARK_004C_CSV) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            out[row["landmark"]] = float(row["prior_s65260_in"])
    for k in ("head", "upper_bout", "waist", "lower_bout", "tail"):
        if k not in out:
            raise SystemExit(f"STOP: GenOne prior '{k}' missing from 004C landmark artifact")
    return out


# =============================================================================
# Anchor set
# =============================================================================

@dataclass
class Anchor:
    name: str
    dev_s: float
    dev_u: float
    plan_frac: float          # raw plan fraction (working)
    plan_arc_in: float        # raw plan arc
    plan_x_in: float
    plan_y_in: float
    anchor_class: str
    source: str
    hard: bool
    uncertainty_note: str
    plan_frac_sm: float       # smoothed-diagnostic plan fraction


def _xy_at_frac(frac: float, s_raw: np.ndarray, y: np.ndarray, x: np.ndarray,
                A_raw: float) -> Tuple[float, float]:
    a = frac * A_raw
    return float(np.interp(a, s_raw, x)), float(np.interp(a, s_raw, y))


def build_anchor_set(side: Dict, outline: Dict, land: Dict,
                     priors: Dict[str, float], waist_dev: float) -> List[Anchor]:
    dev_len = side["dev_len"]
    y, x = outline["y"], outline["x"]
    s_raw = land["s_raw"]
    A_raw = land["A_raw"]
    neck_xy = (float(x[0]), float(y[0]))
    tail_xy = (float(x[-1]), float(y[-1]))

    anchors = [
        Anchor("neck", 0.0, 0.0, 0.0, 0.0, neck_xy[0], neck_xy[1],
               "SOURCE_MEASURED", "developed endpoint (004C) ↔ outline neck endpoint",
               True, "exact endpoint", 0.0),
        Anchor("upper_bout", priors["upper_bout"], priors["upper_bout"] / dev_len,
               land["upper_bout"]["plan_frac_raw"], land["upper_bout"]["plan_arc_raw_in"],
               land["upper_bout"]["half_width_in"], land["upper_bout"]["y_in"],
               "PROPORTIONAL_PRIOR",
               "developed station = GenOne proportional prior (004C); plan position VERIFIED_DRAWING_DERIVED",
               False, "developed coordinate is GenOne prior, not Arnold-measured",
               land["upper_bout"]["plan_frac_sm"]),
        Anchor("waist", waist_dev, waist_dev / dev_len,
               land["waist"]["plan_frac_raw"], land["waist"]["plan_arc_raw_in"],
               land["waist"]["half_width_in"], land["waist"]["y_in"],
               "CALCULATED_004C",
               "developed station = 004C reconstructed (H=4.220); plan waist VERIFIED_DRAWING_DERIVED",
               True, "004C-reconstructed developed waist; outline waist is a single minimum",
               land["waist"]["plan_frac_sm"]),
        Anchor("lower_bout", priors["lower_bout"], priors["lower_bout"] / dev_len,
               land["lower_bout"]["plan_frac_raw"], land["lower_bout"]["plan_arc_raw_in"],
               land["lower_bout"]["half_width_in"], land["lower_bout"]["y_in"],
               "PROPORTIONAL_PRIOR",
               "developed station = GenOne proportional prior (004C); plan position VERIFIED_DRAWING_DERIVED",
               False, "developed coordinate is GenOne prior, not Arnold-measured",
               land["lower_bout"]["plan_frac_sm"]),
        Anchor("tail", dev_len, 1.0, 1.0, A_raw, tail_xy[0], tail_xy[1],
               "SOURCE_MEASURED", "developed endpoint (004C) ↔ outline tail endpoint",
               True, "exact endpoint", 1.0),
    ]
    return anchors


# =============================================================================
# Registration mapping candidates (fail-closed, monotone)
# =============================================================================

def _validate_anchors(u: Sequence[float], p: Sequence[float]) -> None:
    u = list(u)
    p = list(p)
    if len(u) != len(p) or len(u) < 2:
        raise ValueError("registration anchors malformed (need >=2 paired)")
    if u[0] != 0.0 or abs(u[-1] - 1.0) > 1e-12:
        raise ValueError("missing neck/tail endpoint anchor (u must span [0,1])")
    if p[0] != 0.0 or abs(p[-1] - 1.0) > 1e-12:
        raise ValueError("plan endpoints must be 0 and 1")
    if any(b <= a for a, b in zip(u, u[1:])):
        raise ValueError("developed anchor stations not strictly increasing (duplicate/non-monotone)")
    if any(b <= a for a, b in zip(p, p[1:])):
        raise ValueError("plan anchor fractions not strictly increasing (duplicate/non-monotone)")
    if any(not (0.0 <= v <= 1.0) for v in p):
        raise ValueError("plan fraction anchor outside [0,1] (anchor outside outline range)")


@dataclass
class Mapping:
    method: str
    g: Optional[Callable]
    dg: Optional[Callable]
    u_anchors: List[float]
    p_anchors: List[float]
    monotonic: bool
    admissible: bool
    note: str


def _dense_u(n: int = 2001) -> np.ndarray:
    return np.linspace(0.0, 1.0, n)


def fit_registration_mapping(u: Sequence[float], p: Sequence[float], method: str) -> Mapping:
    """Build a monotone p=g(u). Fail-closed: unconstrained Hermite that cannot be
    shown monotone is marked inadmissible (its g is still returned for reporting)."""
    _validate_anchors(u, p)
    u = np.array(u, float)
    p = np.array(p, float)
    uu = _dense_u()

    if method == "linear":
        def g(x): return np.interp(x, u, p)
        # piecewise-constant derivative
        slopes = np.diff(p) / np.diff(u)

        def dg(x):
            idx = np.clip(np.searchsorted(u, x, side="right") - 1, 0, len(slopes) - 1)
            return slopes[idx]
        mono = bool(np.all(np.diff(g(uu)) >= -1e-12))
        return Mapping("piecewise_linear", g, dg, list(u), list(p), mono, mono,
                       "exact anchors; derivative discontinuous at anchors")

    if method == "pchip":
        pch = PchipInterpolator(u, p, extrapolate=False)
        dpch = pch.derivative(1)
        vals = pch(uu)
        mono = bool(np.all(np.diff(vals) >= -1e-12))
        overshoot = bool(vals.min() < -1e-9 or vals.max() > 1.0 + 1e-9)
        return Mapping("monotone_pchip", lambda x: pch(x), lambda x: dpch(x),
                       list(u), list(p), mono, mono and not overshoot,
                       "shape-preserving; no overshoot beyond [0,1]"
                       if not overshoot else "OVERSHOOT beyond [0,1] (inadmissible)")

    if method == "hermite":
        # finite-difference slopes (NOT guaranteed monotone) -> fail closed.
        m = np.gradient(p, u)
        her = CubicHermiteSpline(u, p, m, extrapolate=False)
        dher = her.derivative(1)
        vals = her(uu)
        mono = bool(np.all(np.diff(vals) >= -1e-12)) and bool(np.all(dher(uu) >= -1e-9))
        overshoot = bool(vals.min() < -1e-9 or vals.max() > 1.0 + 1e-9)
        adm = mono and not overshoot
        return Mapping("constrained_cubic_hermite", lambda x: her(x), lambda x: dher(x),
                       list(u), list(p), mono, adm,
                       "FD-slope Hermite; monotonicity verified on dense grid"
                       if adm else "FAIL-CLOSED: monotonicity/overshoot not guaranteed")

    raise ValueError(f"unknown mapping method {method!r}")


# =============================================================================
# Evaluation
# =============================================================================

def evaluate_registration(mp: Mapping, A_raw: float, dev_len: float,
                          waist_u: float) -> Dict:
    uu = _dense_u()
    if mp.g is None:
        return {}
    g = mp.g(uu)
    dg = mp.dg(uu)
    # anchor residuals
    anc_res = max(abs(float(mp.g(ua)) - pa) for ua, pa in zip(mp.u_anchors, mp.p_anchors))
    endpoint_exact = abs(float(mp.g(0.0))) < 1e-9 and abs(float(mp.g(1.0)) - 1.0) < 1e-9
    waist_exact = abs(float(mp.g(waist_u)) - np.interp(waist_u, mp.u_anchors, mp.p_anchors)) < 1e-9
    # derivatives: dp/du == local stretch ratio r (see report). da/ds = (A/S)*dp/du.
    ratio_global = A_raw / dev_len
    stretch = dg                      # r = dp/du
    da_ds = ratio_global * dg
    smooth = float(np.max(np.abs(np.gradient(dg, uu))))  # max |g''| proxy
    return {
        "method": mp.method,
        "anchor_count": len(mp.u_anchors),
        "monotonic": mp.monotonic,
        "endpoint_exact": bool(endpoint_exact),
        "waist_exact": bool(waist_exact),
        "max_anchor_residual": float(anc_res),
        "min_dp_du": float(np.min(dg)),
        "max_dp_du": float(np.max(dg)),
        "min_da_ds": float(np.min(da_ds)),
        "max_da_ds": float(np.max(da_ds)),
        "max_stretch_ratio": float(np.max(stretch)),
        "max_compression_ratio": float(1.0 / np.min(stretch)) if np.min(stretch) > 0 else float("inf"),
        "smoothness_metric": smooth,
        "admissible": bool(mp.admissible and np.min(dg) > 0),
        "notes": mp.note,
    }


def build_registered_rim(mp: Mapping, side: Dict, outline: Dict, land: Dict,
                         stations: np.ndarray) -> List[Dict]:
    dev_len = side["dev_len"]
    H = side["H"]
    y, x = outline["y"], outline["x"]
    s_raw = land["s_raw"]
    A_raw = land["A_raw"]
    src_s = {round(p[0], 6) for p in side["src_points"]}
    rows: List[Dict] = []
    for s in stations:
        u = s / dev_len
        p = float(mp.g(u))
        a = p * A_raw
        xi = float(np.interp(a, s_raw, x))
        yi = float(np.interp(a, s_raw, y))
        zi = float(H(s))
        is_src = round(float(s), 6) in src_s
        rows.append({
            "s_in": s, "u": u, "p": p, "plan_arc_in": a,
            "x_in": xi, "y_in": yi, "z_in": zi,
            "x_mm": xi * 25.4, "y_mm": yi * 25.4, "z_mm": zi * 25.4,
            "source_height_status": ("SOURCE_MEASURED" if is_src else "INTERPOLATED_004C"),
        })
    return rows


def analyze_stretch_ratio(mp: Mapping, side: Dict, land: Dict,
                          stations: np.ndarray, anchors: List[Anchor]) -> List[Dict]:
    dev_len = side["dev_len"]
    A_raw = land["A_raw"]
    s_raw = land["s_raw"]
    y, x = side.get("_y"), side.get("_x")  # unused; kept for clarity
    ratio_global = A_raw / dev_len
    anc_u = np.array([a.dev_u for a in anchors])
    anc_names = [a.name for a in anchors]
    rows: List[Dict] = []
    seg_bounds = sorted({a.dev_u for a in anchors})
    for s in stations:
        u = s / dev_len
        p = float(mp.g(u))
        a = p * A_raw
        dp = float(mp.dg(u))
        da_ds = ratio_global * dp
        r = dp  # local stretch ratio
        ni = int(np.argmin(np.abs(anc_u - u)))
        seg = int(np.searchsorted(seg_bounds, u, side="right"))
        rows.append({
            "s_in": s, "u_developed": u, "p_plan": p, "plan_arc_in": a,
            "ds_plan_ds_developed": da_ds,
            "local_stretch_ratio": r,
            "local_compression_ratio": (1.0 / r if r > 0 else float("inf")),
            "nearest_anchor": anc_names[ni],
            "anchor_distance_in": abs(s - anchors[ni].dev_s),
            "mapping_segment": seg,
        })
    return rows


# =============================================================================
# Orchestration
# =============================================================================

def _station_grid(side: Dict, anchors: List[Anchor]) -> np.ndarray:
    dev_len = side["dev_len"]
    base = list(np.round(np.arange(0.0, dev_len, RIM_STEP_IN), 4))
    extra = [p[0] for p in side["src_points"]] + [a.dev_s for a in anchors] + [dev_len]
    grid = sorted({round(float(v), 4) for v in base + extra})
    return np.array(grid)


def run_all() -> Dict:
    side = load_004c_side_profile()
    outline = load_arnold_outline()
    s_raw = compute_outline_arclength(outline["y"], outline["x"])
    land = identify_outline_landmarks(outline["y"], outline["x"])
    priors = load_genone_landmark_priors()
    waist_dev = waist_developed_station(side["H"])
    anchors = build_anchor_set(side, outline, land, priors, waist_dev)

    hard = [a for a in anchors if a.hard]
    hu = [a.dev_u for a in hard]
    hp = [a.plan_frac for a in hard]
    au = [a.dev_u for a in anchors]
    ap = [a.plan_frac for a in anchors]

    # Candidate mappings on the HARD anchor set (drive the selected rim).
    cand_hard = {m: fit_registration_mapping(hu, hp, m)
                 for m in ("linear", "pchip", "hermite")}
    # Prior-informed candidates (all five anchors) — reported, not selected.
    cand_prior = {m: fit_registration_mapping(au, ap, m)
                  for m in ("linear", "pchip")}

    waist_u = waist_dev / side["dev_len"]
    evals = {}
    for tag, mp in list(cand_hard.items()):
        evals[f"hard_{tag}"] = evaluate_registration(mp, land["A_raw"], side["dev_len"], waist_u)
    for tag, mp in list(cand_prior.items()):
        evals[f"prior_{tag}"] = evaluate_registration(mp, land["A_raw"], side["dev_len"], waist_u)

    # Primary selection: monotone PCHIP on hard anchors unless inadmissible.
    primary = cand_hard["pchip"]
    primary_tag = "hard_monotone_pchip"
    if not evals["hard_pchip"]["admissible"]:
        primary = cand_hard["linear"]
        primary_tag = "hard_piecewise_linear"

    stations = _station_grid(side, anchors)
    rim = build_registered_rim(primary, side, outline, land, stations)
    stretch_rows = analyze_stretch_ratio(primary, side, land, stations, anchors)

    # Primary admissibility / disposition
    pe = evals[primary_tag.replace("hard_monotone_pchip", "hard_pchip").replace(
        "hard_piecewise_linear", "hard_linear")]
    # material difference between hard-pchip and prior-pchip (non-uniqueness check)
    uu = _dense_u()
    diff_hard_prior = float(np.max(np.abs(cand_hard["pchip"].g(uu) - cand_prior["pchip"].g(uu))))

    continuous = all(np.isfinite([r["x_in"], r["y_in"], r["z_in"]]).all() for r in rim)
    monotone_p = bool(np.all(np.diff([r["p"] for r in rim]) >= -1e-9))
    stretch_vals = [r["local_stretch_ratio"] for r in stretch_rows]
    max_stretch = max(stretch_vals)
    max_compression = max(r["local_compression_ratio"] for r in stretch_rows)

    # Local-tension heuristic: stretch spike well outside the global-average band.
    tension = (max_stretch > 1.6) or (max_compression > 1.6)
    if not (pe["admissible"] and continuous and monotone_p):
        disp = "INSUFFICIENT_REGISTRATION_AUTHORITY"
        notes = ["Primary mapping is not admissible/continuous/monotonic."]
    elif tension:
        disp = "DEVELOPED_PLAN_REGISTRATION_WITH_LOCAL_TENSION"
        notes = [f"Mapping valid & continuous but localized stretch "
                 f"(max {max_stretch:.3f}) / compression (max {max_compression:.3f}) "
                 f"exceeds the 1.6× reporting band."]
    else:
        disp = "DEVELOPED_PLAN_REGISTRATION_SUPPORTED"
        notes = [
            f"Monotone registration through hard anchors (neck/waist/tail); "
            f"anchor residual {pe['max_anchor_residual']:.2e}.",
            f"Registered rim continuous ({len(rim)} points); XY from Arnold/JD raw "
            f"outline, Z from 004C (unchanged).",
            f"Local stretch ∈ [{min(stretch_vals):.3f}, {max_stretch:.3f}] about the "
            f"global average A/S = {land['A_raw']/side['dev_len']:.3f}; no reversal, "
            f"finite positive derivative.",
        ]

    return dict(side=side, outline=outline, land=land, priors=priors,
                waist_dev=waist_dev, waist_u=waist_u, anchors=anchors,
                cand_hard=cand_hard, cand_prior=cand_prior, evals=evals,
                primary=primary, primary_tag=primary_tag, rim=rim,
                stretch_rows=stretch_rows, disp=disp, notes=notes,
                diff_hard_prior=diff_hard_prior, max_stretch=max_stretch,
                max_compression=max_compression, stations=stations)


# =============================================================================
# Writers
# =============================================================================

def _wr_csv(path: str, fields: List[str], rows: List[Dict]) -> None:
    os.makedirs(_RESULTS, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_authority(R: Dict) -> None:
    land = R["land"]
    side = R["side"]
    anchors = R["anchors"]
    rec = {
        "experiment": "D28_RUN_004D_DEVELOPED_PLAN_REGISTRATION",
        "developed_side_length_in": side["dev_len"],
        "outline_source_artifact": "D28_65260_ARNOLD_OUTLINE.csv",
        "plan_half_perimeter_raw_in": round(land["A_raw"], 4),
        "plan_half_perimeter_smoothed_in": round(land["A_sm"], 4),
        "plan_half_perimeter_note": (
            "Raw one-side outline arc length is the working plan coordinate. The "
            "smoothed value (~26.73 in, documented in Runs 003/004C) is inflated by "
            "a boxcar mode='same' endpoint artifact and is retained as a diagnostic "
            "only. 30.4375 in (developed) and the plan half-perimeter are DIFFERENT "
            "geometric quantities; none is forced equal."),
        "mapping_method_primary": R["primary"].method,
        "mapping_candidates": ["piecewise_linear", "monotone_pchip",
                               "constrained_cubic_hermite(fail-closed)"],
        "interpolation_method_z": "PCHIP through 004C source points (unchanged)",
        "interpolation_method_xy": "linear interpolation on raw outline arc length",
        "tolerances": {"anchor_residual_in": 1e-9, "overshoot": 1e-9,
                       "waist_bracket_in": [9.0, 12.0]},
        "hard_anchors": [a.name for a in anchors if a.hard],
        "prior_only_anchors": [a.name for a in anchors if not a.hard],
        "rejected_anchors": [],
        "landmark_classifications": {a.name: a.anchor_class for a in anchors},
        "waist_developed_station_in": round(R["waist_dev"], 4),
        "provenance_sha256": {
            "D28_65260_ARNOLD_OUTLINE.csv": sha256(OUTLINE_CSV),
            "D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json": sha256(AUTH_004C_JSON),
            "D28_65260_CONSTRAINED_SIDE_PROFILE_004C.csv": sha256(PROFILE_004C_CSV),
            "D28_65260_LANDMARK_RECONSTRUCTION_004C.csv": sha256(LANDMARK_004C_CSV),
        },
        "no_prior_file_modifications": True,
        "no_production_changes": True,
        "no_sphere_fit": True,
        "no_sevy_high_point": True,
    }
    with open(AUTHORITY_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


def write_anchors(R: Dict) -> None:
    rows = []
    for a in R["anchors"]:
        rows.append({
            "anchor_name": a.name,
            "developed_station_in": f"{a.dev_s:.4f}",
            "developed_fraction": f"{a.dev_u:.5f}",
            "plan_x_in": f"{a.plan_x_in:.4f}",
            "plan_y_in": f"{a.plan_y_in:.4f}",
            "plan_arc_in": f"{a.plan_arc_in:.4f}",
            "plan_fraction": f"{a.plan_frac:.5f}",
            "plan_fraction_smoothed_diag": f"{a.plan_frac_sm:.5f}",
            "anchor_class": a.anchor_class,
            "source": a.source,
            "hard_constraint": a.hard,
            "uncertainty_note": a.uncertainty_note,
            "included_in_fit": a.hard,
        })
    _wr_csv(ANCHORS_CSV, list(rows[0].keys()), rows)


def write_mapping(R: Dict) -> None:
    rows = []
    for r in R["stretch_rows"]:
        rim = next(x for x in R["rim"] if abs(x["s_in"] - r["s_in"]) < 1e-9)
        rows.append({
            "s_in": f"{r['s_in']:.4f}",
            "u_developed": f"{r['u_developed']:.5f}",
            "p_plan": f"{r['p_plan']:.5f}",
            "plan_arc_in": f"{r['plan_arc_in']:.4f}",
            "x_in": f"{rim['x_in']:.4f}",
            "y_in": f"{rim['y_in']:.4f}",
            "z_in": f"{rim['z_in']:.4f}",
            "ds_plan_ds_developed": f"{r['ds_plan_ds_developed']:.5f}",
            "local_stretch_ratio": f"{r['local_stretch_ratio']:.5f}",
            "local_compression_ratio": f"{r['local_compression_ratio']:.5f}",
            "nearest_anchor": r["nearest_anchor"],
            "anchor_distance_in": f"{r['anchor_distance_in']:.4f}",
            "mapping_segment": r["mapping_segment"],
            "registration_status": "REGISTERED",
        })
    _wr_csv(MAPPING_CSV, list(rows[0].keys()), rows)


def write_rim(R: Dict) -> None:
    dev_len = R["side"]["dev_len"]
    A_raw = R["land"]["A_raw"]
    rows = []
    for r in R["rim"]:
        rows.append({
            "s_in": f"{r['s_in']:.4f}",
            "x_in": f"{r['x_in']:.4f}",
            "y_in": f"{r['y_in']:.4f}",
            "z_in": f"{r['z_in']:.4f}",
            "x_mm": f"{r['x_mm']:.4f}",
            "y_mm": f"{r['y_mm']:.4f}",
            "z_mm": f"{r['z_mm']:.4f}",
            "plan_fraction": f"{r['p']:.5f}",
            "developed_fraction": f"{r['u']:.5f}",
            "source_height_status": r["source_height_status"],
            "registration_status": "REGISTERED",
        })
    _wr_csv(RIM_CSV, list(rows[0].keys()), rows)


def write_analysis(R: Dict) -> None:
    order = ["hard_linear", "hard_pchip", "hard_hermite", "prior_linear", "prior_pchip"]
    rows = []
    for tag in order:
        e = R["evals"][tag]
        rows.append({
            "method": tag,
            "anchor_count": e["anchor_count"],
            "monotonic": e["monotonic"],
            "endpoint_exact": e["endpoint_exact"],
            "waist_exact": e["waist_exact"],
            "max_anchor_residual": f"{e['max_anchor_residual']:.2e}",
            "min_dp_ds": f"{e['min_da_ds']:.5f}",
            "max_dp_ds": f"{e['max_da_ds']:.5f}",
            "max_stretch_ratio": f"{e['max_stretch_ratio']:.5f}",
            "max_compression_ratio": f"{e['max_compression_ratio']:.5f}",
            "smoothness_metric": f"{e['smoothness_metric']:.5f}",
            "admissible": e["admissible"],
            "notes": e["notes"],
        })
    _wr_csv(ANALYSIS_CSV, list(rows[0].keys()), rows)


def write_summary(R: Dict) -> None:
    land = R["land"]
    side = R["side"]
    a = {x.name: x for x in R["anchors"]}
    pe_tag = "hard_pchip" if R["primary"].method == "monotone_pchip" else "hard_linear"
    e = R["evals"][pe_tag]
    row = {
        "developed_side_length_in": f"{side['dev_len']:.4f}",
        "plan_half_perimeter_raw_in": f"{land['A_raw']:.4f}",
        "plan_half_perimeter_smoothed_diag_in": f"{land['A_sm']:.4f}",
        "hard_anchors": " ".join(x.name for x in R["anchors"] if x.hard),
        "prior_only_anchors": " ".join(x.name for x in R["anchors"] if not x.hard),
        "selected_mapping_method": R["primary"].method,
        "waist_developed_station_in": f"{R['waist_dev']:.4f}",
        "waist_plan_arc_in": f"{a['waist'].plan_arc_in:.4f}",
        "waist_plan_fraction": f"{a['waist'].plan_frac:.5f}",
        "upper_bout_developed_station_in": f"{a['upper_bout'].dev_s:.4f}",
        "lower_bout_developed_station_in": f"{a['lower_bout'].dev_s:.4f}",
        "min_mapping_derivative_dp_du": f"{e['min_dp_du']:.5f}",
        "max_mapping_derivative_dp_du": f"{e['max_dp_du']:.5f}",
        "global_registration_ratio_A_over_S": f"{land['A_raw']/side['dev_len']:.5f}",
        "max_local_stretch_ratio": f"{R['max_stretch']:.5f}",
        "max_local_compression_ratio": f"{R['max_compression']:.5f}",
        "mapping_monotonic": e["monotonic"],
        "registered_rim_point_count": len(R["rim"]),
        "endpoint_closure_neck_xy": f"({a['neck'].plan_x_in:.4f},{a['neck'].plan_y_in:.4f})",
        "endpoint_closure_tail_xy": f"({a['tail'].plan_x_in:.4f},{a['tail'].plan_y_in:.4f})",
        "hard_vs_prior_pchip_max_abs_frac_diff": f"{R['diff_hard_prior']:.5f}",
        "physical_admissibility": ("admissible (monotonic, continuous, exact anchors, "
                                   "finite positive derivative)" if e["admissible"] else "inadmissible"),
        "final_disposition": R["disp"],
    }
    _wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004D_DEVELOPED_PLAN_REGISTRATION",
        "parent_commit": git_sha(),
        "script": "scripts/experiments/d28_rerun004d_developed_plan_registration.py",
        "command": "python scripts/experiments/d28_rerun004d_developed_plan_registration.py --write",
        "source_artifacts": [
            {"path": "docs/experiments/results/D28_65260_ARNOLD_OUTLINE.csv",
             "role": "PLAN_OUTLINE_XY_AUTHORITY", "classification": "VERIFIED_DRAWING_DERIVED",
             "sha256": sha256(OUTLINE_CSV)},
            {"path": "docs/experiments/results/D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json",
             "role": "DEVELOPED_SIDE_HEIGHT_AUTHORITY", "classification": "CALCULATED_004C",
             "sha256": sha256(AUTH_004C_JSON)},
            {"path": "docs/experiments/results/D28_65260_CONSTRAINED_SIDE_PROFILE_004C.csv",
             "role": "DEVELOPED_SIDE_PROFILE_REFERENCE", "classification": "CALCULATED_004C",
             "sha256": sha256(PROFILE_004C_CSV)},
            {"path": "docs/experiments/results/D28_65260_LANDMARK_RECONSTRUCTION_004C.csv",
             "role": "GENONE_LONGITUDINAL_LANDMARK_PRIOR", "classification": "PROPORTIONAL_PRIOR",
             "sha256": sha256(LANDMARK_004C_CSV)},
            {"path": "docs/experiments/results/D28_65260_RERUN_003_EXTRACTION.json",
             "role": "OUTLINE_EXTRACTION_METADATA", "classification": "VERIFIED_DRAWING_DERIVED",
             "sha256": sha256(EXTRACTION_JSON)},
        ],
        "output_paths": [os.path.basename(p) for p in (
            AUTHORITY_JSON, ANCHORS_CSV, MAPPING_CSV, RIM_CSV, ANALYSIS_CSV,
            SUMMARY_CSV, PROVENANCE_JSON)],
        "pdf_vendored": False,
        "no_prior_file_modifications": True,
        "no_production_changes": True,
        "no_sphere_fit_governs_registration": True,
        "disposition": R["disp"],
    }
    with open(PROVENANCE_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


# =============================================================================
# Report section
# =============================================================================

def build_section(R: Dict) -> str:
    L: List[str] = []
    w = L.append
    land = R["land"]
    side = R["side"]
    a = {x.name: x for x in R["anchors"]}
    A_raw, A_sm, S = land["A_raw"], land["A_sm"], side["dev_len"]
    ratio = A_raw / S

    w("## Run 004D — Developed-Side / Plan-Outline Registration")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Registers the **004C source-constrained developed-side coordinate** "
      "`s ∈ [0, 30.4375 in]` onto the **verified Arnold/JD plan outline**, producing the "
      "first defensible 3D rim edge `R(s) = (x(s), y(s), H(s))` for #65260. XY comes from "
      "the Arnold/JD outline; Z = H(s) is the **unchanged** 004C side height.")
    w("- This is a **registration** problem (`s → p → (x,y)`), not a radius fit. No sphere "
      "fit, no Sevy high point governs it.")
    w("- Artifacts: `D28_65260_REGISTRATION_AUTHORITY_004D.json`, "
      "`D28_65260_REGISTRATION_ANCHORS_004D.csv`, `D28_65260_DEVELOPED_PLAN_MAPPING_004D.csv`, "
      "`D28_65260_REGISTERED_RIM_004D.csv`, `D28_65260_RERUN_004D_ANALYSIS.csv`, "
      "`D28_65260_RERUN_004D_SUMMARY.csv`, `D28_65260_RERUN_004D_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### Why 004D exists")
    w("")
    w("- 004C established a source-constrained side-height function `H(s)` but did not "
      "determine **where** each developed station lies around the plan-view perimeter.")
    w("- A manufacturable rim needs both the position around the body **and** the side height "
      "at that position. 004D combines those two independently established datasets.")
    w("")
    w("### Two lengths are retained, never forced equal")
    w("")
    w(f"- Developed side length **S = 30.4375 in** (004C authority).")
    w(f"- Plan one-side perimeter (**raw** outline, working): **A = {A_raw:.4f} in**.")
    w(f"- Plan one-side perimeter (**smoothed**, legacy diagnostic ≈ 26.73 in): "
      f"**{A_sm:.4f} in** — inflated by a boxcar `mode='same'` endpoint artifact in the "
      "003/004C helper (neck half-width 3.086→2.064 in); retained as a diagnostic only.")
    w(f"- These are **different geometric quantities**. No solver path forces `S = A`. The "
      f"registration is a normalized monotone transform `p = g(u)`, `u = s/S`, `p = a/A`, "
      f"with `g(0)=0`, `g(1)=1`; the global average `A/S = {ratio:.4f}`.")
    w("")
    w("### What GenOne contributes (and does not)")
    w("")
    w("- Contributes **only** proportional longitudinal landmark priors for the upper/lower "
      "bout developed stations (not directly recoverable from Arnold's numeric side-height "
      "series). Reused from the committed 004C landmark artifact.")
    w("- Does **not** contribute side-height authority, outline authority, brace authority, or "
      "any forced developed-length scaling.")
    w("")
    w("### Anchors")
    w("")
    w("| anchor | dev station s (in) | dev u | plan frac (raw) | plan XY (in) | class | hard |")
    w("|---|---:|---:|---:|---|---|:--:|")
    for nm in ("neck", "upper_bout", "waist", "lower_bout", "tail"):
        an = a[nm]
        w(f"| {nm} | {an.dev_s:.4f} | {an.dev_u:.4f} | {an.plan_frac:.4f} | "
          f"({an.plan_x_in:.3f}, {an.plan_y_in:.3f}) | `{an.anchor_class}` | "
          f"{'yes' if an.hard else 'prior'} |")
    w("")
    w(f"- Hard anchors drive the selected mapping: **neck, waist "
      f"(s={R['waist_dev']:.3f} in, 004C-reconstructed), tail**. Upper/lower bout developed "
      f"stations are **GenOne proportional priors** — reported and used only in an alternate "
      f"prior-informed candidate; removing them cannot move the hard anchors.")
    w("")
    w("### Candidate mappings (all evaluated; results preserved before judging)")
    w("")
    w("| candidate | anchors | monotonic | endpoint exact | max anchor resid | "
      "min dp/du | max dp/du | max stretch | admissible |")
    w("|---|---:|:--:|:--:|---:|---:|---:|---:|:--:|")
    label = {"hard_linear": "piecewise-linear (hard)", "hard_pchip": "monotone PCHIP (hard)",
             "hard_hermite": "cubic Hermite (hard, fail-closed)",
             "prior_linear": "piecewise-linear (+priors)", "prior_pchip": "monotone PCHIP (+priors)"}
    for tag in ("hard_linear", "hard_pchip", "hard_hermite", "prior_linear", "prior_pchip"):
        e = R["evals"][tag]
        w(f"| {label[tag]} | {e['anchor_count']} | {'yes' if e['monotonic'] else 'NO'} | "
          f"{'yes' if e['endpoint_exact'] else 'no'} | {e['max_anchor_residual']:.1e} | "
          f"{e['min_dp_du']:.3f} | {e['max_dp_du']:.3f} | {e['max_stretch_ratio']:.3f} | "
          f"{'yes' if e['admissible'] else 'NO'} |")
    w("")
    w(f"- **Selected primary mapping: `{R['primary'].method}`** on the hard anchors.")
    w(f"- Max |fraction| difference between the hard-only and prior-informed PCHIP mappings: "
      f"**{R['diff_hard_prior']:.4f}** (the GenOne priors nudge the bout regions but do not "
      f"redefine the hard-anchor skeleton).")
    w("")
    w("### Registration distortion (local stretch ratio r = dp/du)")
    w("")
    w(f"- `r = 1` means the local plan-perimeter rate matches the global average "
      f"`A/S = {ratio:.4f}`; `r > 1` locally more plan distance per developed inch, `r < 1` "
      f"less. Neither is an error by itself.")
    w(f"- Observed over the selected mapping: max local stretch **{R['max_stretch']:.3f}**, "
      f"max local compression **{R['max_compression']:.3f}**.")
    w("")
    w("### Mathematical result vs physical interpretation")
    w("")
    w("> The registration solution is reported before it is judged. The mapping, derivatives, "
      "residuals, and anchor behavior are preserved first; only then is physical admissibility "
      "assessed. A local stretch or compression factor that appears unintuitive is not corrected "
      "merely because of expectation. \"Physically inadmissible\" is a property of the tested "
      "model interpretation, not of the mathematics itself.")
    w("")
    w("- All candidate mapping behavior (including any rejected candidate) is retained in "
      "`D28_65260_RERUN_004D_ANALYSIS.csv`. See the program-level **Engineering Interpretation "
      "Principle** at the top of this document.")
    w("")
    w("### Registered rim")
    w("")
    w(f"- `{len(R['rim'])}` deterministic rim points over `s ∈ [0, {S:.4f}]`; XY interpolated on "
      f"the raw Arnold/JD outline, Z = 004C H(s) (exact at every source station).")
    w(f"- Endpoint closure: neck XY = ({a['neck'].plan_x_in:.3f}, {a['neck'].plan_y_in:.3f}) in, "
      f"tail XY = ({a['tail'].plan_x_in:.3f}, {a['tail'].plan_y_in:.3f}) in — the real outline "
      f"endpoints.")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Parent dispositions (001–004C) are untouched. 004D introduces no sphere fit, no Sevy "
      "high point, and transfers no GenOne side-height curve.")
    w("")
    return "\n".join(L)


def splice_doc(section: str) -> None:
    with open(_DOC) as fh:
        text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    else:
        marker = "<!-- RERUN004C_START -->"
        text = text[:text.index(marker)] + block + "\n\n---\n\n" + text[text.index(marker):]
    with open(_DOC, "w") as fh:
        fh.write(text)


def main() -> None:
    R = run_all()
    section = build_section(R)
    if "--write" in sys.argv:
        write_authority(R)
        write_anchors(R)
        write_mapping(R)
        write_rim(R)
        write_analysis(R)
        write_summary(R)
        write_provenance(R)
        splice_doc(section)
        print(f"wrote 004D artifacts; disposition={R['disp']}; "
              f"rim_points={len(R['rim'])}; A_raw={R['land']['A_raw']:.4f}")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; primary={R['primary'].method}; "
              f"rim_points={len(R['rim'])}; A_raw={R['land']['A_raw']:.4f}; "
              f"waist_dev={R['waist_dev']:.4f}]")


if __name__ == "__main__":
    main()
