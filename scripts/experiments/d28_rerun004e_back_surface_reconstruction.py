#!/usr/bin/env python3
"""
D28 RUN 004E — Back Surface Reconstruction from Registered Rim
==============================================================

Reconstructs a defensible #65260 back surface using the 004D registered 3D rim as
FIXED boundary geometry. The rim is immutable; no side measurement is altered; no
historical radius is assumed. Candidate back surfaces (single sphere, fixed-radius
diagnostic sweep, compound longitudinal/transverse, constrained smooth) are all
built and compared; mathematical results are recorded before physical
interpretation.

Governing principle (carried forward verbatim in substance): a mathematically
valid result must be preserved before judging whether it is physically admissible
for the model being tested. For 004E: do not clamp a fitted radius, move a
curvature center, force a dome apex inside the body, or reject a saddle merely
because it is unexpected. "Physically inadmissible" is a property of the tested
model interpretation, not of the mathematics itself.

Coordinate system (004D plane, unchanged):
  x = transverse plan coordinate (in)   [body symmetric about x=0]
  y = longitudinal body coordinate (in) [neck y=0 .. tail y=L]
  z = vertical body depth (in)          [= 004C side height at the rim]
  rim boundary z = z_rim(s); back rise h(x,y) = z_b(x,y) - z_rim_local(y)

The developed side length (30.4375 in) and the plan half-perimeter are NOT reused
here. GenOne's 4-6 mm arch is REFERENCE-ONLY (never a fit target). Back-brace
longitudinal positions are not numerically available -> brace check is
QUALITATIVE_ONLY (dimensions preserved, no invented positions). No production/spec
edits. No PDF vendored. No PR. Prior runs 001-004D preserved unchanged.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.optimize import least_squares

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                    "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")

# --- Inputs (committed, read-only) -------------------------------------------
RIM_CSV = os.path.join(_RESULTS, "D28_65260_REGISTERED_RIM_004D.csv")
RIM_AUTH_JSON = os.path.join(_RESULTS, "D28_65260_REGISTRATION_AUTHORITY_004D.json")
ANCHORS_CSV = os.path.join(_RESULTS, "D28_65260_REGISTRATION_ANCHORS_004D.csv")
OUTLINE_CSV = os.path.join(_RESULTS, "D28_65260_ARNOLD_OUTLINE.csv")
AUTH_004C_JSON = os.path.join(_RESULTS, "D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json")

# --- Outputs (004E only) -----------------------------------------------------
AUTHORITY_JSON = os.path.join(_RESULTS, "D28_65260_BACK_SURFACE_AUTHORITY_004E.json")
CANDIDATES_CSV = os.path.join(_RESULTS, "D28_65260_BACK_SURFACE_CANDIDATES_004E.csv")
SURFACE_CSV = os.path.join(_RESULTS, "D28_65260_BACK_SURFACE_004E.csv")
CENTERLINE_CSV = os.path.join(_RESULTS, "D28_65260_BACK_CENTERLINE_004E.csv")
SECTIONS_CSV = os.path.join(_RESULTS, "D28_65260_BACK_SECTIONS_004E.csv")
BRACE_CSV = os.path.join(_RESULTS, "D28_65260_BACK_BRACE_COMPATIBILITY_004E.csv")
SUMMARY_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004E_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_RESULTS, "D28_65260_RERUN_004E_PROVENANCE.json")

_S, _E = "<!-- RERUN004E_START -->", "<!-- RERUN004E_END -->"

GRID_STEP_IN = 0.25
RIM_EXACT_TOL_IN = 0.01       # "meets rim exactly" tolerance
RIM_NEARFIT_TOL_IN = 0.05     # "spans rim" approximate tolerance
NONUNIQUE_MM = 1.0            # interior |z| divergence => NONUNIQUE
NONUNIQUE_IN = NONUNIQUE_MM / 25.4

# Back-brace cross-section evidence (Arnold drawing). Positions qualitative only.
BACK_BRACES = [
    {"brace_id": "BB1", "width_in": 0.320, "depth_in": 0.450, "region": "upper bout"},
    {"brace_id": "BB2", "width_in": 0.320, "depth_in": 0.450, "region": "above waist"},
    {"brace_id": "BB3", "width_in": 0.735, "depth_in": 0.385, "region": "below waist"},
    {"brace_id": "BB4", "width_in": 0.760, "depth_in": 0.375, "region": "lower bout"},
]
GENONE_ARCH_MM = (4.0, 6.0)   # reference-only envelope


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
# Loaders
# =============================================================================

def load_registered_rim() -> Dict:
    xs, ys, zs = [], [], []
    with open(RIM_CSV) as fh:
        for r in csv.DictReader(fh):
            xs.append(float(r["x_in"]))
            ys.append(float(r["y_in"]))
            zs.append(float(r["z_in"]))
    x = np.array(xs)
    y = np.array(ys)
    z = np.array(zs)
    if len(x) < 10:
        raise SystemExit("STOP: registered rim too short")
    if y[0] != 0.0 or z[0] <= 0:
        raise SystemExit("STOP: rim neck endpoint malformed")
    return {"x": x, "y": y, "z": z, "L": float(y.max())}


def load_arnold_outline() -> Dict:
    ys, hw = [], []
    with open(OUTLINE_CSV) as fh:
        next(fh)
        for line in fh:
            if not line.strip():
                continue
            a, b = line.strip().split(",")
            ys.append(float(a))
            hw.append(float(b))
    return {"y": np.array(ys), "hw": np.array(hw)}


def half_width_at(outline: Dict, y: float) -> float:
    yy = outline["y"]
    return float(np.interp(np.clip(y, yy[0], yy[-1]), yy, outline["hw"]))


def load_back_brace_evidence() -> List[Dict]:
    return [dict(b) for b in BACK_BRACES]


def load_reference_arch_evidence() -> Dict:
    return {"source": "GenOne dreadnought construction (REFERENCE_GEOMETRY)",
            "arch_mm_range": list(GENONE_ARCH_MM),
            "role": "REFERENCE_ONLY — never a fit target"}


# =============================================================================
# Boundary assembly (full closed back-edge loop)
# =============================================================================

def build_boundary(rim: Dict, outline: Dict) -> Dict:
    """Full closed boundary: both mirrored side curves + neck/tail end segments."""
    sx, sy, sz = rim["x"], rim["y"], rim["z"]
    L = rim["L"]
    # mirrored side points (both sides)
    bx = np.concatenate([sx, -sx])
    by = np.concatenate([sy, sy])
    bz = np.concatenate([sz, sz])
    # neck end segment (y=0, constant z = neck side height)
    hw_neck = float(sx[0])
    z_neck = float(sz[0])
    nx = np.arange(-hw_neck, hw_neck + 1e-9, GRID_STEP_IN)
    ne_x, ne_y, ne_z = nx, np.zeros_like(nx), np.full_like(nx, z_neck)
    # tail end segment (y=L, constant z = tail side height)
    hw_tail = float(sx[-1])
    z_tail = float(sz[-1])
    tx = np.arange(-hw_tail, hw_tail + 1e-9, GRID_STEP_IN)
    te_x, te_y, te_z = tx, np.full_like(tx, L), np.full_like(tx, z_tail)
    X = np.concatenate([bx, ne_x, te_x])
    Y = np.concatenate([by, ne_y, te_y])
    Z = np.concatenate([bz, ne_z, te_z])
    # dedupe identical boundary points deterministically
    key = np.round(np.column_stack([X, Y]), 6)
    _, idx = np.unique(key, axis=0, return_index=True)
    idx = np.sort(idx)
    return {"x": X[idx], "y": Y[idx], "z": Z[idx],
            "side_x": sx, "side_y": sy, "side_z": sz,
            "z_neck": z_neck, "z_tail": z_tail, "L": L}


def rim_z_at_y(rim: Dict, y: np.ndarray) -> np.ndarray:
    """Local rim side-height at longitudinal station y (one-side rim is monotone in y)."""
    return np.interp(y, rim["y"], rim["z"])


# =============================================================================
# Body domain grid + mask
# =============================================================================

def build_grid(rim: Dict, outline: Dict) -> Dict:
    L = rim["L"]
    hw_max = float(outline["hw"].max())
    xs = np.round(np.arange(-hw_max - GRID_STEP_IN, hw_max + GRID_STEP_IN + 1e-9, GRID_STEP_IN), 4)
    ys = np.round(np.arange(0.0, L + 1e-9, GRID_STEP_IN), 4)
    XX, YY = np.meshgrid(xs, ys)
    HW = np.array([half_width_at(outline, float(v)) for v in ys])[:, None]
    inside = np.abs(XX) <= HW + 1e-9
    return {"xs": xs, "ys": ys, "XX": XX, "YY": YY, "inside": inside, "HW": HW,
            "pts": np.column_stack([XX[inside], YY[inside]])}


# =============================================================================
# Candidate surfaces
# =============================================================================

@dataclass
class Candidate:
    name: str
    model_type: str
    zf: Optional[Callable]          # zf(np.ndarray[N,2]) -> z
    params: Dict = field(default_factory=dict)
    radius_ft: Optional[float] = None
    radius_long_ft: Optional[float] = None
    radius_trans_ft: Optional[float] = None
    center: Optional[Tuple[float, float, float]] = None
    apex: Optional[Tuple[float, float, float]] = None
    rim_rmse: Optional[float] = None
    rim_max: Optional[float] = None
    center_rise_in: Optional[float] = None
    curv_min: Optional[float] = None
    curv_max: Optional[float] = None
    admissible: Optional[bool] = None
    note: str = ""


def _sphere_z(cx, cy, cz, R, sign):
    def zf(P):
        v = R * R - (P[:, 0] - cx) ** 2 - (P[:, 1] - cy) ** 2
        v = np.clip(v, 0.0, None)
        return cz + sign * np.sqrt(v)
    return zf


def fit_single_sphere(bnd: Dict) -> Candidate:
    X, Y, Z = bnd["x"], bnd["y"], bnd["z"]

    def res(p):
        cx, cy, cz, R = p
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)
        return d - R
    sol = least_squares(res, [0.0, 10.0, -200.0, 2400.0])
    cx, cy, cz, R = (float(v) for v in sol.x)
    sign = 1.0 if (Z.mean() - cz) > 0 else -1.0
    zf = _sphere_z(cx, cy, cz, R, sign)
    rim_err = zf(np.column_stack([X, Y])) - Z
    apex = (cx, cy, cz + sign * R)
    return Candidate("single_sphere", "sphere", zf,
                     params={"cx": cx, "cy": cy, "cz": cz, "R_in": R, "sign": sign},
                     radius_ft=R / 12, center=(cx, cy, cz), apex=apex,
                     rim_rmse=float(np.sqrt(np.mean(rim_err ** 2))),
                     rim_max=float(np.max(np.abs(rim_err))),
                     note="unconstrained best-fit sphere; center/apex recorded verbatim "
                          "(apex may lie outside the body)")


def sweep_fixed_radii(bnd: Dict, radii_ft=(12, 15, 18, 20, 25, 30)) -> List[Candidate]:
    X, Y, Z = bnd["x"], bnd["y"], bnd["z"]
    out: List[Candidate] = []
    for rft in radii_ft:
        R = rft * 12.0

        def res(p, R=R):
            cy, cz = p
            d = np.sqrt(X ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)  # cx fixed 0 (symmetry)
            return d - R
        sol = least_squares(res, [10.0, Z.mean() - R])
        cy, cz = float(sol.x[0]), float(sol.x[1])
        sign = 1.0 if (Z.mean() - cz) > 0 else -1.0
        zf = _sphere_z(0.0, cy, cz, R, sign)
        rim_err = zf(np.column_stack([X, Y])) - Z
        out.append(Candidate(f"fixed_{rft}ft", "fixed_sphere", zf,
                             params={"cx": 0.0, "cy": cy, "cz": cz, "R_in": R, "sign": sign},
                             radius_ft=float(rft), center=(0.0, cy, cz),
                             apex=(0.0, cy, cz + sign * R),
                             rim_rmse=float(np.sqrt(np.mean(rim_err ** 2))),
                             rim_max=float(np.max(np.abs(rim_err))),
                             note="diagnostic fixed radius (NOT a historical claim)"))
    return out


def fit_compound_surface(bnd: Dict) -> Candidate:
    """Elliptic paraboloid z = z0 + x^2/(2 Rt) + (y-y0)^2/(2 Rl) (cx=0 by symmetry).
    Independent transverse (Rt) and longitudinal (Rl) curvature controls."""
    X, Y, Z = bnd["x"], bnd["y"], bnd["z"]

    def res(p):
        z0, y0, inv_rt, inv_rl = p
        pred = z0 + 0.5 * inv_rt * X ** 2 + 0.5 * inv_rl * (Y - y0) ** 2
        return pred - Z
    sol = least_squares(res, [4.0, 10.0, 1.0 / 400.0, 1.0 / 400.0])
    z0, y0, inv_rt, inv_rl = (float(v) for v in sol.x)
    Rt = (1.0 / inv_rt) if abs(inv_rt) > 1e-12 else float("inf")
    Rl = (1.0 / inv_rl) if abs(inv_rl) > 1e-12 else float("inf")

    def zf(P):
        return z0 + 0.5 * inv_rt * P[:, 0] ** 2 + 0.5 * inv_rl * (P[:, 1] - y0) ** 2
    rim_err = zf(np.column_stack([X, Y])) - Z
    return Candidate("compound_paraboloid", "elliptic_paraboloid", zf,
                     params={"z0": z0, "y0": y0, "inv_Rt_perin": inv_rt, "inv_Rl_perin": inv_rl},
                     radius_long_ft=Rl / 12, radius_trans_ft=Rt / 12,
                     center=(0.0, y0, z0), apex=(0.0, y0, z0),
                     rim_rmse=float(np.sqrt(np.mean(rim_err ** 2))),
                     rim_max=float(np.max(np.abs(rim_err))),
                     note="separable quadratic; independent longitudinal/transverse radii")


def fit_constrained_surface(bnd: Dict) -> Candidate:
    """Thin-plate-spline (biharmonic) interpolation: exact through the full rim
    boundary, deterministic, no smoothing/tuning."""
    P = np.column_stack([bnd["x"], bnd["y"]])
    rbf = RBFInterpolator(P, bnd["z"], kernel="thin_plate_spline")

    def zf(Q):
        return rbf(Q)
    rim_err = zf(P) - bnd["z"]
    return Candidate("constrained_tps", "thin_plate_spline", zf,
                     params={"kernel": "thin_plate_spline", "smoothing": 0.0,
                             "n_boundary_pts": int(P.shape[0])},
                     rim_rmse=float(np.sqrt(np.mean(rim_err ** 2))),
                     rim_max=float(np.max(np.abs(rim_err))),
                     note="boundary-exact minimal-assumption surface (adds no dome)")


# =============================================================================
# Curvature + rise metrics on the body grid
# =============================================================================

def _surface_on_grid(zf: Callable, grid: Dict) -> np.ndarray:
    Z = np.full(grid["XX"].shape, np.nan)
    pts = np.column_stack([grid["XX"][grid["inside"]], grid["YY"][grid["inside"]]])
    Z[grid["inside"]] = zf(pts)
    return Z


def eroded_mask(inside: np.ndarray, iters: int = 2) -> np.ndarray:
    """Body-interior cells whose full curvature stencil stays inside the body.
    Erodes the (non-convex) body mask by `iters` cells (curvature uses two
    successive gradients, so NaN from the boundary propagates ~2 cells)."""
    m = inside.copy()
    for _ in range(iters):
        up = np.zeros_like(m); up[1:, :] = m[:-1, :]
        dn = np.zeros_like(m); dn[:-1, :] = m[1:, :]
        lf = np.zeros_like(m); lf[:, 1:] = m[:, :-1]
        rt = np.zeros_like(m); rt[:, :-1] = m[:, 1:]
        m = m & up & dn & lf & rt
    return m


def curvature_fields(Z: np.ndarray, step: float) -> Dict:
    zy, zx = np.gradient(Z, step, step)
    zyy, zyx = np.gradient(zy, step, step)
    zxy, zxx = np.gradient(zx, step, step)
    denom = (1 + zx ** 2 + zy ** 2)
    H = ((1 + zx ** 2) * zyy - 2 * zx * zy * zxy + (1 + zy ** 2) * zxx) / (2 * denom ** 1.5)
    K = (zxx * zyy - zxy ** 2) / denom ** 2
    return {"mean": H, "gauss": K}


def rise_above_rim(zf: Callable, grid: Dict, rim: Dict) -> np.ndarray:
    pts = np.column_stack([grid["XX"][grid["inside"]], grid["YY"][grid["inside"]]])
    z = zf(pts)
    rz = rim_z_at_y(rim, pts[:, 1])
    return z - rz


def fill_candidate_metrics(c: Candidate, grid: Dict, rim: Dict) -> None:
    Z = _surface_on_grid(c.zf, grid)
    cf = curvature_fields(Z, GRID_STEP_IN)
    interior = grid["inside"]
    inner = eroded_mask(interior, iters=2)
    with np.errstate(invalid="ignore"):
        c.curv_min = float(np.nanmin(cf["gauss"][inner]))
        c.curv_max = float(np.nanmax(cf["gauss"][inner]))
    rr = rise_above_rim(c.zf, grid, rim)
    c.center_rise_in = float(np.nanmax(rr))
    # admissibility
    finite = bool(np.all(np.isfinite(Z[interior])))
    meets_rim = (c.rim_max is not None and c.rim_max <= RIM_NEARFIT_TOL_IN)
    c.admissible = bool(finite and meets_rim)


# =============================================================================
# Centerline + sections
# =============================================================================

def extract_centerline(zf: Callable, rim: Dict, outline: Dict) -> List[Dict]:
    ys = np.round(np.arange(0.0, rim["L"] + 1e-9, GRID_STEP_IN), 4)
    P = np.column_stack([np.zeros_like(ys), ys])
    zc = zf(P)
    rz = rim_z_at_y(rim, ys)
    slope = np.gradient(zc, ys)
    curv = np.gradient(slope, ys)
    rows = []
    for i, y in enumerate(ys):
        rows.append({"y_in": y, "x_center_in": 0.0, "z_back_in": float(zc[i]),
                     "local_rim_reference_in": float(rz[i]),
                     "rise_in": float(zc[i] - rz[i]), "rise_mm": float((zc[i] - rz[i]) * 25.4),
                     "longitudinal_slope": float(slope[i]),
                     "longitudinal_curvature": float(curv[i])})
    return rows


def _fit_circle_section(x: np.ndarray, z: np.ndarray) -> Tuple[float, float]:
    """Fit z(x) ~ arc: minimize residual of a circle through (x,z). Returns (R_in, rmse)."""
    def res(p):
        cx, cz, R = p
        return np.sqrt((x - cx) ** 2 + (z - cz) ** 2) - R
    try:
        sol = least_squares(res, [0.0, z.mean() - 200.0, 200.0])
        R = abs(float(sol.x[2]))
        return R, float(np.sqrt(np.mean(sol.fun ** 2)))
    except Exception:
        return float("nan"), float("nan")


def extract_transverse_sections(zf: Callable, rim: Dict, outline: Dict,
                                 landmarks: Dict) -> List[Dict]:
    rows = []
    for name, y in landmarks.items():
        hw = half_width_at(outline, y)
        xs = np.round(np.arange(-hw, hw + 1e-9, GRID_STEP_IN), 4)
        if len(xs) < 3:
            continue
        P = np.column_stack([xs, np.full_like(xs, y)])
        zz = zf(P)
        rim_z = float(rim_z_at_y(rim, np.array([y]))[0])
        z_center = float(zf(np.array([[0.0, y]]))[0])
        R, rmse = _fit_circle_section(xs, zz)
        # symmetry: compare z(x) to z(-x)
        zz_mirror = zf(np.column_stack([-xs, np.full_like(xs, y)]))
        sym_err = float(np.max(np.abs(zz - zz_mirror)))
        for i, x in enumerate(xs):
            rows.append({"section_name": name, "y_in": y, "x_in": float(x),
                         "z_in": float(zz[i]), "local_rim_z_in": rim_z,
                         "rise_in": float(zz[i] - rim_z),
                         "fitted_local_radius_in": R, "fitted_local_radius_ft": R / 12,
                         "residual_in": rmse,
                         "section_status": (f"symmetric(err={sym_err:.2e});"
                                            f" center_rise={z_center-rim_z:+.4f}in")})
    return rows


def evaluate_brace_compatibility(zf: Callable, rim: Dict) -> List[Dict]:
    rows = []
    for b in BACK_BRACES:
        rows.append({"brace_id": b["brace_id"], "y_in": "", "width_in": f"{b['width_in']:.4f}",
                     "depth_in": f"{b['depth_in']:.4f}", "position_source": "spec_qualitative",
                     "local_surface_curvature": "", "implied_brace_radius_ft": "",
                     "common_radius_compatible": "QUALITATIVE_ONLY",
                     "status": "QUALITATIVE_ONLY",
                     "note": (f"region '{b['region']}'; exact longitudinal position not "
                              "available -> position not invented; brace depth is a "
                              "cross-section dimension, NOT dome rise")})
    return rows


# =============================================================================
# Orchestration
# =============================================================================

def run_all() -> Dict:
    rim = load_registered_rim()
    outline = load_arnold_outline()
    bnd = build_boundary(rim, outline)
    grid = build_grid(rim, outline)

    sphere = fit_single_sphere(bnd)
    sweep = sweep_fixed_radii(bnd)
    compound = fit_compound_surface(bnd)
    tps = fit_constrained_surface(bnd)

    candidates = [sphere] + sweep + [compound, tps]
    for c in candidates:
        fill_candidate_metrics(c, grid, rim)

    primary = tps  # §15: boundary fidelity + minimal assumptions
    primary.name_selected = True  # type: ignore

    # interior divergence sphere vs tps (for disposition)
    Zs = _surface_on_grid(sphere.zf, grid)
    Zt = _surface_on_grid(tps.zf, grid)
    interior = grid["inside"]
    div = np.abs(Zs[interior] - Zt[interior])
    max_div_in = float(np.nanmax(div))
    max_div_mm = max_div_in * 25.4

    # landmark y positions from committed 004D anchors
    landmarks = {}
    with open(ANCHORS_CSV) as fh:
        for r in csv.DictReader(fh):
            if r["anchor_name"] in ("upper_bout", "waist", "lower_bout"):
                landmarks[r["anchor_name"]] = float(r["plan_y_in"])

    centerline = extract_centerline(primary.zf, rim, outline)
    sections = extract_transverse_sections(primary.zf, rim, outline, landmarks)
    braces = evaluate_brace_compatibility(primary.zf, rim)

    # lower-bout center rise vs GenOne reference
    lb_y = landmarks["lower_bout"]
    lb_rise_in = float(primary.zf(np.array([[0.0, lb_y]]))[0] - rim_z_at_y(rim, np.array([lb_y]))[0])
    lb_rise_mm = lb_rise_in * 25.4
    if lb_rise_mm < GENONE_ARCH_MM[0]:
        genone_cmp = "below"
    elif lb_rise_mm > GENONE_ARCH_MM[1]:
        genone_cmp = "above"
    else:
        genone_cmp = "within"

    # curvature tension on primary
    Zt_grid = _surface_on_grid(primary.zf, grid)
    cf = curvature_fields(Zt_grid, GRID_STEP_IN)
    inner = eroded_mask(interior, iters=2)
    with np.errstate(invalid="ignore"):
        gauss_min = float(np.nanmin(cf["gauss"][inner]))
        gauss_max = float(np.nanmax(cf["gauss"][inner]))
        mean_abs_max = float(np.nanmax(np.abs(cf["mean"][inner])))
    saddle = gauss_min < -1e-4
    # curvature "spike" heuristic: mean curvature magnitude far above body-scale 1/R
    tension = mean_abs_max > 0.5  # 1/in; ~ radius < 2 in => implausibly tight

    tps_exact = (primary.rim_max is not None and primary.rim_max <= RIM_EXACT_TOL_IN)

    if not (primary.admissible and tps_exact and np.all(np.isfinite(Zt_grid[interior]))):
        disp = "INSUFFICIENT_BACK_SURFACE_AUTHORITY"
        notes = ["Boundary-exact smooth surface could not be established over the body domain."]
    elif max_div_in > NONUNIQUE_IN:
        disp = "BACK_SURFACE_MODEL_NONUNIQUE"
        notes = [
            f"Materially different surfaces span the same rim: sphere (R≈{sphere.radius_ft:.1f} ft, "
            f"rim max {sphere.rim_max:.4f} in) vs boundary-exact TPS differ by up to "
            f"{max_div_in:.4f} in ({max_div_mm:.2f} mm) in the interior — above the "
            f"{NONUNIQUE_MM:.1f} mm band.",
            "The interior back arch is UNDER-DETERMINED by the rim alone: no measured arch "
            "authority exists (GenOne 4-6 mm is reference-only; brace depths are not dome rise).",
            f"Reported primary = boundary-exact TPS (minimal added assumption); its lower-bout "
            f"center rise is {lb_rise_mm:.2f} mm ({genone_cmp} the GenOne 4-6 mm reference). The "
            f"near-fitting ≈{sphere.radius_ft:.1f} ft sphere is a strong diagnostic, NOT promoted "
            f"to historical authority.",
        ]
    elif tension or saddle:
        disp = "BACK_SURFACE_SUPPORTED_WITH_CURVATURE_TENSION"
        notes = [f"Boundary-exact smooth surface established, but curvature field shows "
                 f"{'a saddle (negative Gaussian)' if saddle else 'localized tight curvature'} "
                 f"(Gaussian ∈ [{gauss_min:.2e}, {gauss_max:.2e}]). Recorded, not corrected."]
    else:
        disp = "BACK_SURFACE_RECONSTRUCTION_SUPPORTED"
        notes = ["Boundary-exact smooth surface spans the rim; candidates agree within the "
                 f"{NONUNIQUE_MM:.1f} mm band; no pathological curvature required."]

    return dict(rim=rim, outline=outline, bnd=bnd, grid=grid, candidates=candidates,
                sphere=sphere, sweep=sweep, compound=compound, tps=tps, primary=primary,
                centerline=centerline, sections=sections, braces=braces,
                landmarks=landmarks, max_div_in=max_div_in, max_div_mm=max_div_mm,
                lb_rise_in=lb_rise_in, lb_rise_mm=lb_rise_mm, genone_cmp=genone_cmp,
                gauss_min=gauss_min, gauss_max=gauss_max, mean_abs_max=mean_abs_max,
                saddle=saddle, disp=disp, notes=notes)


# =============================================================================
# Writers
# =============================================================================

def _wr_csv(path: str, fields: List[str], rows: List[Dict]) -> None:
    os.makedirs(_RESULTS, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _fmt(v, n=4):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return ""
    return f"{v:.{n}f}" if isinstance(v, float) else str(v)


def write_candidates(R: Dict) -> None:
    rows = []
    for c in R["candidates"]:
        selected = (c is R["primary"])
        rows.append({
            "model_name": c.name, "model_type": c.model_type,
            "parameters": json.dumps(c.params, sort_keys=True),
            "radius_ft": _fmt(c.radius_ft, 3),
            "radius_longitudinal_ft": _fmt(c.radius_long_ft, 3),
            "radius_transverse_ft": _fmt(c.radius_trans_ft, 3),
            "center_x": _fmt(c.center[0], 4) if c.center else "",
            "center_y": _fmt(c.center[1], 4) if c.center else "",
            "center_z": _fmt(c.center[2], 4) if c.center else "",
            "apex_x": _fmt(c.apex[0], 4) if c.apex else "",
            "apex_y": _fmt(c.apex[1], 4) if c.apex else "",
            "apex_z": _fmt(c.apex[2], 4) if c.apex else "",
            "rim_rmse_in": _fmt(c.rim_rmse, 5), "rim_max_abs_error_in": _fmt(c.rim_max, 5),
            "center_rise_in": _fmt(c.center_rise_in, 4),
            "center_rise_mm": _fmt((c.center_rise_in * 25.4) if c.center_rise_in is not None else None, 3),
            "curvature_min": _fmt(c.curv_min, 6), "curvature_max": _fmt(c.curv_max, 6),
            "physically_admissible": c.admissible, "selected": selected, "notes": c.note,
        })
    _wr_csv(CANDIDATES_CSV, list(rows[0].keys()), rows)


def write_surface(R: Dict) -> None:
    grid = R["grid"]
    rim = R["rim"]
    primary = R["primary"]
    Z = _surface_on_grid(primary.zf, grid)
    cf = curvature_fields(Z, GRID_STEP_IN)
    rows = []
    XX, YY, inside, HW = grid["XX"], grid["YY"], grid["inside"], grid["HW"]
    ny, nx = XX.shape
    for j in range(ny):
        for i in range(nx):
            if not inside[j, i]:
                continue
            x = float(XX[j, i]); y = float(YY[j, i]); z = float(Z[j, i])
            bdist = float(HW[j, 0] - abs(x))
            k_mean = cf["mean"][j, i]; k_g = cf["gauss"][j, i]
            rows.append({
                "x_in": f"{x:.4f}", "y_in": f"{y:.4f}", "z_in": f"{z:.4f}",
                "x_mm": f"{x*25.4:.3f}", "y_mm": f"{y*25.4:.3f}", "z_mm": f"{z*25.4:.3f}",
                "inside_body": True, "boundary_distance_in": f"{bdist:.4f}",
                "local_mean_curvature": (f"{k_mean:.6f}" if np.isfinite(k_mean) else ""),
                "local_gaussian_curvature": (f"{k_g:.6f}" if np.isfinite(k_g) else ""),
                "source_status": ("RIM_BOUNDARY" if bdist < GRID_STEP_IN / 2 else "RECONSTRUCTED"),
                "model_name": primary.name,
            })
    _wr_csv(SURFACE_CSV, list(rows[0].keys()), rows)


def write_centerline(R: Dict) -> None:
    rows = []
    for r in R["centerline"]:
        rows.append({k: (f"{v:.5f}" if isinstance(v, float) else v) for k, v in r.items()})
    _wr_csv(CENTERLINE_CSV, list(rows[0].keys()), rows)


def write_sections(R: Dict) -> None:
    rows = []
    for r in R["sections"]:
        rows.append({
            "section_name": r["section_name"], "y_in": f"{r['y_in']:.4f}",
            "x_in": f"{r['x_in']:.4f}", "z_in": f"{r['z_in']:.4f}",
            "local_rim_z_in": f"{r['local_rim_z_in']:.4f}", "rise_in": f"{r['rise_in']:.4f}",
            "fitted_local_radius_in": _fmt(r["fitted_local_radius_in"], 3),
            "fitted_local_radius_ft": _fmt(r["fitted_local_radius_ft"], 3),
            "residual_in": _fmt(r["residual_in"], 5), "section_status": r["section_status"],
        })
    _wr_csv(SECTIONS_CSV, list(rows[0].keys()), rows)


def write_braces(R: Dict) -> None:
    _wr_csv(BRACE_CSV, list(R["braces"][0].keys()), R["braces"])


def write_authority(R: Dict) -> None:
    sph = R["sphere"]
    rec = {
        "experiment": "D28_RUN_004E_BACK_SURFACE_RECONSTRUCTION",
        "rim_source": "D28_65260_REGISTERED_RIM_004D.csv (immutable boundary)",
        "coordinate_system": {"x": "transverse (in)", "y": "longitudinal neck->tail (in)",
                              "z": "vertical depth = 004C side height (in)",
                              "rise_definition": "h(x,y) = z_b - z_rim_local(y)"},
        "source_classifications": {
            "registered_rim_004D": "VERIFIED_REGISTERED (004D)",
            "arnold_outline": "VERIFIED_DRAWING_DERIVED",
            "004C_side_heights": "CALCULATED_004C",
            "back_brace_dims": "DRAWING_DERIVED (cross-section only; positions qualitative)",
            "genone_arch_4_6mm": "REFERENCE_GEOMETRY (comparison only; not a fit target)"},
        "brace_evidence": BACK_BRACES,
        "reference_only_genone": load_reference_arch_evidence(),
        "candidate_models": [
            {"name": "single_sphere", "type": "sphere", "role": "diagnostic"},
            {"name": "fixed_radius_sweep", "type": "fixed_sphere",
             "radii_ft": [12, 15, 18, 20, 25, 30], "role": "diagnostic (not historical)"},
            {"name": "compound_paraboloid", "type": "elliptic_paraboloid", "role": "candidate"},
            {"name": "constrained_tps", "type": "thin_plate_spline",
             "role": "selected primary (boundary-exact, minimal assumptions)"}],
        "tolerances": {"rim_exact_in": RIM_EXACT_TOL_IN, "rim_nearfit_in": RIM_NEARFIT_TOL_IN,
                       "nonunique_divergence_mm": NONUNIQUE_MM, "grid_step_in": GRID_STEP_IN},
        "excluded_assumptions": [
            "no historical radius assumed (15/25/30/35 ft not claimed)",
            "no clamped radius / moved center / forced in-body apex",
            "GenOne arch not used as a fit target",
            "brace depth not equated to dome rise",
            "back-brace longitudinal positions not invented (QUALITATIVE_ONLY)"],
        "diagnostic_single_sphere": {"R_ft": sph.radius_ft, "center": sph.center,
                                     "apex": sph.apex, "rim_rmse_in": sph.rim_rmse,
                                     "rim_max_in": sph.rim_max},
        "provenance_sha256": {
            os.path.basename(RIM_CSV): sha256(RIM_CSV),
            os.path.basename(OUTLINE_CSV): sha256(OUTLINE_CSV),
            os.path.basename(AUTH_004C_JSON): sha256(AUTH_004C_JSON)},
        "no_prior_file_modifications": True, "no_production_changes": True,
    }
    with open(AUTHORITY_JSON, "w") as fh:
        json.dump(rec, fh, indent=2, default=str)


def write_summary(R: Dict) -> None:
    sph = R["sphere"]
    primary = R["primary"]
    # best fixed-radius candidate by rim rmse
    best_fixed = min(R["sweep"], key=lambda c: c.rim_rmse)
    cl = R["centerline"]
    max_rise = max(r["rise_in"] for r in cl)
    apex_y = max(cl, key=lambda r: r["rise_in"])["y_in"]
    row = {
        "selected_model": primary.name,
        "selected_rim_rmse_in": f"{primary.rim_rmse:.5f}",
        "selected_rim_max_in": f"{primary.rim_max:.5f}",
        "rim_exact": primary.rim_max <= RIM_EXACT_TOL_IN,
        "max_back_rise_in": f"{max_rise:.4f}", "max_back_rise_mm": f"{max_rise*25.4:.3f}",
        "centerline_apex_y_in": f"{apex_y:.4f}",
        "single_sphere_R_ft": f"{sph.radius_ft:.3f}",
        "single_sphere_center": f"({sph.center[0]:.2f},{sph.center[1]:.2f},{sph.center[2]:.2f})",
        "single_sphere_apex": f"({sph.apex[0]:.2f},{sph.apex[1]:.2f},{sph.apex[2]:.2f})",
        "single_sphere_rim_rmse_in": f"{sph.rim_rmse:.5f}",
        "single_sphere_rim_max_in": f"{sph.rim_max:.5f}",
        "single_sphere_admissible": sph.admissible,
        "best_fixed_radius_ft": f"{best_fixed.radius_ft:.1f}",
        "best_fixed_rim_rmse_in": f"{best_fixed.rim_rmse:.5f}",
        "compound_radius_long_ft": f"{R['compound'].radius_long_ft:.2f}",
        "compound_radius_trans_ft": f"{R['compound'].radius_trans_ft:.2f}",
        "compound_rim_rmse_in": f"{R['compound'].rim_rmse:.5f}",
        "interior_sphere_vs_tps_max_div_in": f"{R['max_div_in']:.5f}",
        "interior_sphere_vs_tps_max_div_mm": f"{R['max_div_mm']:.3f}",
        "gaussian_curv_min": f"{R['gauss_min']:.2e}", "gaussian_curv_max": f"{R['gauss_max']:.2e}",
        "saddle_present": R["saddle"],
        "lower_bout_center_rise_mm": f"{R['lb_rise_mm']:.3f}",
        "genone_4_6mm_comparison": R["genone_cmp"],
        "brace_compatibility": "QUALITATIVE_ONLY (positions not available)",
        "physical_admissibility": ("admissible (boundary-exact, finite, smooth)"
                                   if primary.admissible else "see disposition"),
        "final_disposition": R["disp"],
    }
    _wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004E_BACK_SURFACE_RECONSTRUCTION",
        "parent_commit": git_sha(),
        "script": "scripts/experiments/d28_rerun004e_back_surface_reconstruction.py",
        "command": "python scripts/experiments/d28_rerun004e_back_surface_reconstruction.py --write",
        "source_artifacts": [
            {"path": "docs/experiments/results/D28_65260_REGISTERED_RIM_004D.csv",
             "role": "IMMUTABLE_RIM_BOUNDARY", "sha256": sha256(RIM_CSV)},
            {"path": "docs/experiments/results/D28_65260_REGISTRATION_AUTHORITY_004D.json",
             "role": "RIM_PROVENANCE", "sha256": sha256(RIM_AUTH_JSON)},
            {"path": "docs/experiments/results/D28_65260_ARNOLD_OUTLINE.csv",
             "role": "BODY_DOMAIN_OUTLINE", "sha256": sha256(OUTLINE_CSV)},
            {"path": "docs/experiments/results/D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json",
             "role": "SIDE_HEIGHT_AUTHORITY", "sha256": sha256(AUTH_004C_JSON)},
        ],
        "model_definitions": {
            "single_sphere": "least_squares (cx,cy,cz,R); no clamping",
            "fixed_radius_sweep": "radii [12,15,18,20,25,30] ft; fit (cy,cz), cx=0",
            "compound_paraboloid": "z=z0 + x^2/(2Rt) + (y-y0)^2/(2Rl)",
            "constrained_tps": "RBFInterpolator thin_plate_spline, smoothing=0 (boundary-exact)"},
        "grid_step_in": GRID_STEP_IN,
        "deterministic_seed": "none (no stochastic component)",
        "output_paths": [os.path.basename(p) for p in (
            AUTHORITY_JSON, CANDIDATES_CSV, SURFACE_CSV, CENTERLINE_CSV, SECTIONS_CSV,
            BRACE_CSV, SUMMARY_CSV, PROVENANCE_JSON)],
        "pdf_vendored": False, "no_prior_file_modifications": True,
        "no_production_changes": True, "disposition": R["disp"],
    }
    with open(PROVENANCE_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


# =============================================================================
# Report
# =============================================================================

def build_section(R: Dict) -> str:
    L: List[str] = []
    w = L.append
    sph = R["sphere"]
    comp = R["compound"]
    tps = R["tps"]
    best_fixed = min(R["sweep"], key=lambda c: c.rim_rmse)
    cl = R["centerline"]
    max_rise = max(r["rise_in"] for r in cl)

    w("## Run 004E — Back Surface Reconstruction from Registered Rim")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Reconstructs a #65260 **back surface** `z_b = F(x,y)` spanning the **immutable 004D "
      "registered rim** as fixed boundary geometry. The rim, 004C side heights, and the "
      "Arnold/JD outline are read-only; no historical radius is assumed.")
    w("- Candidate families (all preserved): **single sphere**, **fixed-radius diagnostic "
      "sweep** (12/15/18/20/25/30 ft), **compound elliptic paraboloid**, and **constrained "
      "thin-plate-spline** (boundary-exact). Selected primary = the constrained TPS.")
    w("- Artifacts: `D28_65260_BACK_SURFACE_AUTHORITY_004E.json`, "
      "`D28_65260_BACK_SURFACE_CANDIDATES_004E.csv`, `D28_65260_BACK_SURFACE_004E.csv`, "
      "`D28_65260_BACK_CENTERLINE_004E.csv`, `D28_65260_BACK_SECTIONS_004E.csv`, "
      "`D28_65260_BACK_BRACE_COMPATIBILITY_004E.csv`, `D28_65260_RERUN_004E_SUMMARY.csv`, "
      "`D28_65260_RERUN_004E_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### Why 004E exists")
    w("")
    w("- 004D fixed **where** the rim is in 3D. 004E asks **what back surface can span that rim** "
      "without changing any evidence. A manufacturable back needs a continuous surface meeting "
      "the full rim; the arch between rim edges is the open question.")
    w("")
    w("### Coordinate system & rise definition")
    w("")
    w("- `x` transverse (body symmetric about x=0), `y` longitudinal (neck 0 → tail "
      f"{R['rim']['L']:.3f} in), `z` vertical depth = 004C side height. Rim z ∈ "
      f"[{R['rim']['z'].min():.3f}, {R['rim']['z'].max():.3f}] in (non-planar). Back rise "
      "`h(x,y) = z_b − z_rim_local(y)`; rim-local varies longitudinally and is not treated as "
      "a flat datum.")
    w("")
    w("### Candidate comparison (results recorded before interpretation)")
    w("")
    w("| model | rim RMSE (in) | rim max (in) | key params | center rise (mm) | admissible |")
    w("|---|---:|---:|---|---:|:--:|")
    w(f"| single sphere | {sph.rim_rmse:.4f} | {sph.rim_max:.4f} | R≈{sph.radius_ft:.1f} ft, "
      f"center≈({sph.center[0]:.1f},{sph.center[1]:.1f},{sph.center[2]:.1f}) | "
      f"{(sph.center_rise_in or 0)*25.4:.2f} | {'yes' if sph.admissible else 'no'} |")
    w(f"| best fixed radius ({best_fixed.radius_ft:.0f} ft) | {best_fixed.rim_rmse:.4f} | "
      f"{best_fixed.rim_max:.4f} | diagnostic only | {(best_fixed.center_rise_in or 0)*25.4:.2f} | "
      f"{'yes' if best_fixed.admissible else 'no'} |")
    w(f"| compound paraboloid | {comp.rim_rmse:.4f} | {comp.rim_max:.4f} | "
      f"R_long≈{comp.radius_long_ft:.1f} ft, R_trans≈{comp.radius_trans_ft:.1f} ft | "
      f"{(comp.center_rise_in or 0)*25.4:.2f} | {'yes' if comp.admissible else 'no'} |")
    w(f"| **constrained TPS (selected)** | {tps.rim_rmse:.4f} | {tps.rim_max:.4f} | "
      f"boundary-exact, {tps.params['n_boundary_pts']} rim pts | "
      f"{(tps.center_rise_in or 0)*25.4:.2f} | {'yes' if tps.admissible else 'no'} |")
    w("")
    w(f"- A single **≈{sph.radius_ft:.1f} ft** spherical cap spans the rim to within "
      f"**{sph.rim_max:.4f} in** (RMSE {sph.rim_rmse:.4f}) — a strong diagnostic, but NOT "
      f"promoted to historical authority (no source evidence fixes a radius for #65260).")
    w(f"- Interior divergence between the sphere and the boundary-exact TPS reaches "
      f"**{R['max_div_in']:.4f} in ({R['max_div_mm']:.2f} mm)** — the back **arch magnitude is "
      f"under-determined by the rim alone**.")
    w("")
    w("### Mathematical result vs physical interpretation")
    w("")
    w("> A mathematically valid result is preserved before it is judged physically admissible. "
      "No fitted radius was clamped, no curvature center moved, no apex forced inside the body, "
      "no saddle rejected on sight. The sphere's apex and center are recorded verbatim even "
      "where they lie outside the body. \"Physically inadmissible\" is a property of the tested "
      "model interpretation, not of the mathematics itself. See the program-level **Engineering "
      "Interpretation Principle** at the top of this document.")
    w("")
    w("### Centerline (selected surface)")
    w("")
    w(f"- Max centerline rise above local rim: **{max_rise:.4f} in ({max_rise*25.4:.2f} mm)**.")
    w("")
    w("| landmark | y (in) | z_back (in) | rim z (in) | rise (mm) |")
    w("|---|---:|---:|---:|---:|")
    for nm in ("upper_bout", "waist", "lower_bout"):
        y = R["landmarks"][nm]
        zc = float(tps.zf(np.array([[0.0, y]]))[0])
        rz = float(rim_z_at_y(R["rim"], np.array([y]))[0])
        w(f"| {nm} | {y:.3f} | {zc:.4f} | {rz:.4f} | {(zc-rz)*25.4:.2f} |")
    tail_y = R["rim"]["L"]
    w(f"| tail | {tail_y:.3f} | {float(tps.zf(np.array([[0.0, tail_y]]))[0]):.4f} | "
      f"{float(rim_z_at_y(R['rim'], np.array([tail_y]))[0]):.4f} | "
      f"{(float(tps.zf(np.array([[0.0, tail_y]]))[0])-float(rim_z_at_y(R['rim'], np.array([tail_y]))[0]))*25.4:.2f} |")
    w("")
    w("### Transverse sections & curvature")
    w("")
    w(f"- Sections at upper-bout / waist / lower-bout exported "
      f"(`D28_65260_BACK_SECTIONS_004E.csv`); symmetry reported per section, local circular-arc "
      f"radius fitted (not forced).")
    w(f"- Gaussian curvature over the interior ∈ [{R['gauss_min']:.2e}, {R['gauss_max']:.2e}]; "
      f"saddle (negative Gaussian) present: **{R['saddle']}** — recorded, not auto-rejected.")
    w("")
    w("### Back-brace consistency (QUALITATIVE_ONLY)")
    w("")
    w("- BB1–BB4 cross-section dimensions preserved; exact longitudinal positions are NOT "
      "available in any source, so positions are **not invented** and the check is "
      "`QUALITATIVE_ONLY`. Brace depth is a cross-section dimension and is **not** compared to "
      "dome rise.")
    w("")
    w("### GenOne 4–6 mm (reference-only)")
    w("")
    w(f"- Selected-surface lower-bout center rise: **{R['lb_rise_mm']:.2f} mm** → "
      f"**{R['genone_cmp']}** the GenOne 4–6 mm reference envelope. The reference range was NOT "
      f"used as a fit target.")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Parent dispositions (001–004D) are untouched. 004E alters no rim point, no 004C side "
      "height, and no production/spec file.")
    w("")
    return "\n".join(L)


def splice_doc(section: str) -> None:
    with open(_DOC) as fh:
        text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    else:
        marker = "<!-- RERUN004D_START -->"
        text = text[:text.index(marker)] + block + "\n\n---\n\n" + text[text.index(marker):]
    with open(_DOC, "w") as fh:
        fh.write(text)


def main() -> None:
    R = run_all()
    section = build_section(R)
    if "--write" in sys.argv:
        write_authority(R)
        write_candidates(R)
        write_surface(R)
        write_centerline(R)
        write_sections(R)
        write_braces(R)
        write_summary(R)
        write_provenance(R)
        splice_doc(section)
        print(f"wrote 004E artifacts; disposition={R['disp']}; "
              f"sphere R={R['sphere'].radius_ft:.1f}ft rim_max={R['sphere'].rim_max:.4f}in; "
              f"max_div={R['max_div_mm']:.2f}mm; lb_rise={R['lb_rise_mm']:.2f}mm")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; primary={R['primary'].name}; "
              f"sphere_R={R['sphere'].radius_ft:.2f}ft; max_div={R['max_div_mm']:.2f}mm]")


if __name__ == "__main__":
    main()
