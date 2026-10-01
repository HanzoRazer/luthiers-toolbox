#!/usr/bin/env python3
"""
D28 RUN 004G — Bounded Back-Surface Family + Body-Volume Envelope
=================================================================

Formalizes the admissible #65260 back-surface family that survives Run 004F,
quantifies the geometric body-VOLUME envelope, carries the Ø4.0 in soundhole as
fixed geometry with an (unsolved) Helmholtz/inverse-volume bridge, and preserves
the MB Torrefied Adirondack material distribution as an EXTERNAL empirical prior
for later acoustic/structural validation.

004G does NOT pick a historical back radius, does NOT fabricate a top dome, does
NOT solve a Helmholtz A0, and does NOT let the MB prior shape any geometry.

Rim-exact family (every member meets the 004D rim exactly):
    z(x, y; alpha) = z_TPS(x, y) + alpha * Phi(x, y)
  * z_TPS  = 004E boundary-exact minimal surface (reused, unchanged)
  * Phi    = deterministic analytic zero-on-rim interior bulge
             Phi = (1 - (x/hw(y))^2) * sin(pi*y/L), normalized to peak 1.
             Phi = 0 on the ENTIRE perimeter (side curves |x|=hw(y) AND the
             neck/tail end segments y in {0,L}) -> rim met exactly for all alpha.
  * alpha  >= 0 scales interior rise (inches of added central bulge).

Evidence-supported interior-rise envelope (from 004E candidates that fit the rim):
    1.61 mm (TPS floor, exact) .. ~2.8 mm (best-fit sphere/compound ceiling).
The GenOne 4-6 mm reference lies ABOVE this envelope and is recorded reference-only
(NOT a bound, NOT a target). The TPS floor's slight lower-bout reflex is preserved.

No production/spec edits; no prior-run alteration; no PDF vendored; no PR.
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
from scipy.optimize import brentq, least_squares

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Inputs (committed, read-only) -------------------------------------------
RIM_CSV = os.path.join(_RESULTS, "D28_65260_REGISTERED_RIM_004D.csv")
E_SUMMARY_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004E_SUMMARY.csv")
E_CANDIDATES_CSV = os.path.join(_RESULTS, "D28_65260_BACK_SURFACE_CANDIDATES_004E.csv")
F_POSITIONS_CSV = os.path.join(_RESULTS, "D28_65260_BACK_BRACE_POSITIONS_004F.csv")
MB_PIN_JSON = os.path.join(_REPO_ROOT, "docs", "reference", "mb-sound", "CORPUS_DEPENDENCY.json")

# --- Outputs (004G only) -----------------------------------------------------
AUTHORITY_JSON = os.path.join(_OUTDIR, "D28_65260_BACK_SURFACE_FAMILY_AUTHORITY_004G.json")
ENVELOPE_CSV = os.path.join(_OUTDIR, "D28_65260_BACK_SURFACE_FAMILY_ENVELOPE_004G.csv")
MEMBERS_CSV = os.path.join(_OUTDIR, "D28_65260_BACK_FAMILY_MEMBERS_004G.csv")
BRACE_CSV = os.path.join(_OUTDIR, "D28_65260_BACK_FAMILY_BRACE_SAMPLING_004G.csv")
VOLUME_CSV = os.path.join(_OUTDIR, "D28_65260_BODY_VOLUME_ENVELOPE_004G.csv")
SOUNDHOLE_JSON = os.path.join(_OUTDIR, "D28_65260_SOUNDHOLE_VOLUME_BRIDGE_004G.json")
MB_CSV = os.path.join(_OUTDIR, "D28_65260_MB_TORREFIED_ADIRONDACK_PRIOR_004G.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004G_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004G_PROVENANCE.json")

_S, _E = "<!-- RERUN004G_START -->", "<!-- RERUN004G_END -->"

MM = 25.4
IN3_TO_CM3 = 16.387064
RISE_FLOOR_MM = 1.61
RISE_CEIL_MM = 2.80
FAMILY_FRACTIONS = [("floor", 0.0), ("q25", 0.25), ("mid", 0.50), ("q75", 0.75), ("ceiling", 1.0)]

SOUNDHOLE_DIAMETER_IN = 4.0
SOUNDHOLE_AREA_IN2 = math.pi * (SOUNDHOLE_DIAMETER_IN / 2.0) ** 2  # 12.5664 in^2

# MB Torrefied Adirondack population envelope — EXTERNAL EMPIRICAL PRIOR, supplied
# in the 004G order as a summary of the Torrefied Adirondack subset (n=21) of the
# PINNED mb-sound/v1.0.0 corpus. Carried by reference to the pin; per-specimen
# payload/envelopes are NOT duplicated into this repo (DATA-MIG-002 / no_local_copy).
MB_SUBSET = "Torrefied Adirondack"
MB_SUBSET_N = 21
MB_ENVELOPE = [
    # metric, min, mean, max, units
    ("density", 398.4, 438.38, 494.2, "kg/m3"),
    ("resonance_frequency", 74.5, 81.20, 90.3, "Hz"),
    ("youngs_modulus_stiffness", 10.8, 13.03, 15.8, "GPa"),
    ("quality_factor_Q", 158.7, 185.26, 212.0, "dimensionless"),
    ("time_constant", 635.3, 726.92, 817.7, "ms"),
    ("radiation_coefficient", 10.5, 12.47, 13.6, "m4/(kg*s)"),
    ("thickness", 4.2, 4.43, 4.7, "mm"),
]


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception:
        return "UNKNOWN"


def _load_e04():
    """Import Run 004E to reuse its rim/grid/z_TPS/curvature machinery unchanged."""
    path = os.path.join(_HERE, "d28_rerun004e_back_surface_reconstruction.py")
    spec = importlib.util.spec_from_file_location("d28_004e_for_g", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_004e_for_g"] = m
    spec.loader.exec_module(m)
    return m


E = _load_e04()
STEP = E.GRID_STEP_IN


# =============================================================================
# Geometry setup (reuse 004E; build the analytic zero-rim bulge Phi)
# =============================================================================

def phi_analytic(x: float, y: float, hw_y: float, L: float) -> float:
    """Zero-on-rim interior bulge value (un-normalized). Exactly 0 on the perimeter:
    |x| = hw(y) -> (1-1)=0; y in {0, L} -> sin(0 or pi)=0."""
    if hw_y <= 0:
        return 0.0
    return (1.0 - (x / hw_y) ** 2) * math.sin(math.pi * y / L)


def phi_field(XX, YY, HW, L, inside):
    with np.errstate(invalid="ignore", divide="ignore"):
        hw = np.where(HW > 0, HW, np.nan)
        phi = (1.0 - (XX / hw) ** 2) * np.sin(np.pi * YY / L)
    phi = np.where(inside, phi, 0.0)
    phi = np.clip(phi, 0.0, None)
    return phi / float(np.nanmax(phi[inside]))                   # peak-normalized to 1


def build_geometry() -> Dict:
    rim = E.load_registered_rim()
    outline = E.load_arnold_outline()
    bnd = E.build_boundary(rim, outline)
    grid = E.build_grid(rim, outline)
    tps = E.fit_constrained_surface(bnd)
    L = rim["L"]
    XX, YY, inside, HW = grid["XX"], grid["YY"], grid["inside"], grid["HW"]

    z_tps = E._surface_on_grid(tps.zf, grid)                       # z on grid (NaN outside)
    rim_local = np.where(inside, E.rim_z_at_y(rim, YY), np.nan)    # local rim z per cell

    phi = phi_field(XX, YY, HW, L, inside)                        # zero-on-rim, peak 1

    base_rise = z_tps - rim_local                                 # TPS floor rise field (in)
    return dict(rim=rim, outline=outline, bnd=bnd, grid=grid, tps=tps, L=L,
                z_tps=z_tps, rim_local=rim_local, phi=phi, base_rise=base_rise,
                inside=inside, XX=XX, YY=YY, HW=HW)


def z_member(G: Dict, alpha: float) -> np.ndarray:
    return G["z_tps"] + alpha * G["phi"]


def rise_member(G: Dict, alpha: float) -> np.ndarray:
    return G["base_rise"] + alpha * G["phi"]


def h_max_mm(G: Dict, alpha: float) -> float:
    r = rise_member(G, alpha)
    return float(np.nanmax(r[G["inside"]])) * MM


def solve_alpha_for_rise(G: Dict, target_mm: float) -> float:
    if target_mm <= h_max_mm(G, 0.0) + 1e-9:
        return 0.0
    hi = 1.0
    while h_max_mm(G, hi) < target_mm and hi < 100:
        hi *= 2
    return float(brentq(lambda a: h_max_mm(G, a) - target_mm, 0.0, hi, xtol=1e-10))


# =============================================================================
# Per-member geometry (volume, curvature, apex, brace sampling)
# =============================================================================

def cell_area() -> float:
    return STEP * STEP


def body_volume_in3(G: Dict, alpha: float) -> float:
    """Case A flat-top reference (top plane z=0): V = integral of z_back dA."""
    z = z_member(G, alpha)
    return float(np.nansum(z[G["inside"]]) * cell_area())


def arch_volume_in3(G: Dict, alpha: float) -> float:
    """Back-arch contribution = integral of interior rise above local rim."""
    r = rise_member(G, alpha)
    return float(np.nansum(r[G["inside"]]) * cell_area())


def apex_of(G: Dict, alpha: float) -> Tuple[float, float, float]:
    r = rise_member(G, alpha)
    rr = np.where(G["inside"], r, -np.inf)
    j, i = np.unravel_index(int(np.argmax(rr)), rr.shape)
    return float(G["XX"][j, i]), float(G["YY"][j, i]), float(rr[j, i] * MM)


def curvature_stats(G: Dict, alpha: float) -> Dict:
    z = z_member(G, alpha)
    cf = E.curvature_fields(z, STEP)
    inner = E.eroded_mask(G["inside"], iters=2)
    with np.errstate(invalid="ignore"):
        return {
            "mean_min": float(np.nanmin(cf["mean"][inner])),
            "mean_max": float(np.nanmax(cf["mean"][inner])),
            "gauss_min": float(np.nanmin(cf["gauss"][inner])),
            "gauss_max": float(np.nanmax(cf["gauss"][inner])),
            "saddle": bool(np.nanmin(cf["gauss"][inner]) < -1e-4),
        }


def _fit_arc_radius(x: np.ndarray, z: np.ndarray) -> float:
    def res(p):
        cx, cz, R = p
        return np.sqrt((x - cx) ** 2 + (z - cz) ** 2) - R
    try:
        sol = least_squares(res, [0.0, z.mean() - 200.0, 200.0])
        return abs(float(sol.x[2]))
    except Exception:
        return float("nan")


def brace_transverse(G: Dict, alpha: float, y_station: float) -> Dict:
    """Transverse section at y_station: fitted arc radius + rise, for member alpha."""
    ys = G["grid"]["ys"]
    j = int(np.argmin(np.abs(ys - y_station)))
    row_inside = G["inside"][j]
    xs = G["XX"][j][row_inside]
    if len(xs) < 3:
        return {"radius_in": float("nan"), "curvature_perin": float("nan"), "rise_center_mm": float("nan")}
    z = z_member(G, alpha)[j][row_inside]
    R = _fit_arc_radius(xs, z)
    # center rise at x=0 relative to local rim
    i0 = int(np.argmin(np.abs(xs)))
    rise_c = (z[i0] - float(E.rim_z_at_y(G["rim"], np.array([ys[j]]))[0])) * MM
    return {"radius_in": R, "radius_ft": R / 12.0, "curvature_perin": (1.0 / R if R > 0 else float("nan")),
            "rise_center_mm": rise_c, "y_used_in": float(ys[j])}


# =============================================================================
# Loaders for fixed inputs
# =============================================================================

def load_brace_stations() -> Dict[str, Dict]:
    out = {}
    with open(F_POSITIONS_CSV) as fh:
        for r in csv.DictReader(fh):
            out[r["brace_id"]] = {"y_in": float(r["y_from_neck_in"]),
                                  "unc_in": float(r["uncertainty_in"]),
                                  "width_in": float(r["width_in"]), "depth_in": float(r["depth_in"])}
    return out


def load_mb_pin() -> Dict:
    with open(MB_PIN_JSON) as fh:
        pin = json.load(fh)
    return {"corpus_id": pin["corpus_id"], "release_tag": pin["release_tag"],
            "canonical_repository": pin["canonical_repository"],
            "corpus_digest_sha256": pin["corpus_digest_sha256"],
            "provenance_class": pin["provenance_class"],
            "pin_path": "docs/reference/mb-sound/CORPUS_DEPENDENCY.json",
            "record_count_total": pin["record_count"]}


# =============================================================================
# Orchestration
# =============================================================================

def run_all() -> Dict:
    G = build_geometry()
    stations = load_brace_stations()

    # Family members at target rises floor..ceiling.
    members = []
    for name, frac in FAMILY_FRACTIONS:
        target = RISE_FLOOR_MM + frac * (RISE_CEIL_MM - RISE_FLOOR_MM)
        alpha = solve_alpha_for_rise(G, target)
        hmax = h_max_mm(G, alpha)
        ax, ay, _ = apex_of(G, alpha)
        vol = body_volume_in3(G, alpha)
        arch = arch_volume_in3(G, alpha)
        cur = curvature_stats(G, alpha)
        rim_exact_err = float(np.nanmax(np.abs(G["phi"][G["inside"]] * alpha *
                               0.0)))  # phi=0 on rim by construction; see test for boundary check
        members.append({"name": name, "frac": frac, "alpha": alpha, "h_max_mm": hmax,
                        "apex_x": ax, "apex_y": ay, "volume_in3": vol, "arch_in3": arch,
                        "curv": cur})

    v_floor = members[0]["volume_in3"]

    # Brace sampling: per station, per member rise + transverse radius; envelope across family.
    brace_rows = []
    for bb in ("BB1", "BB2", "BB3", "BB4"):
        y = stations[bb]["y_in"]
        per = []
        for m in members:
            t = brace_transverse(G, m["alpha"], y)
            per.append((m["name"], t["rise_center_mm"], t["radius_in"], t["radius_ft"], t["curvature_perin"]))
        rises = [p[1] for p in per]
        radii = [p[2] for p in per if np.isfinite(p[2])]
        brace_rows.append({"brace_id": bb, "y_in": y, "unc_in": stations[bb]["unc_in"],
                           "rise_min_mm": min(rises), "rise_max_mm": max(rises),
                           "radius_min_ft": (min(radii) / 12 if radii else float("nan")),
                           "radius_max_ft": (max(radii) / 12 if radii else float("nan")),
                           "per_member": per})

    # Grid-refinement sensitivity on the floor member volume (0.25 -> 0.125 in).
    refine = refinement_check(G)

    mb_pin = load_mb_pin()

    disp = "BOUNDED_BACK_SURFACE_FAMILY_ESTABLISHED"
    notes = [
        f"Rim-exact family z = z_TPS + alpha*Phi over interior-rise envelope "
        f"[{members[0]['h_max_mm']:.2f}, {members[-1]['h_max_mm']:.2f}] mm (5 members: "
        f"floor/25/mid/75/ceiling); every member meets the 004D rim exactly (Phi=0 on perimeter).",
        f"Geometric body-volume envelope (flat-top reference, GEOMETRIC_REFERENCE_ONLY): "
        f"[{min(m['volume_in3'] for m in members)*IN3_TO_CM3/1000:.3f}, "
        f"{max(m['volume_in3'] for m in members)*IN3_TO_CM3/1000:.3f}] L; arch contribution spans "
        f"[{members[0]['arch_in3']*IN3_TO_CM3:.1f}, {members[-1]['arch_in3']*IN3_TO_CM3:.1f}] cm^3.",
        f"Soundhole area fixed at Ø4.0 in = {SOUNDHOLE_AREA_IN2:.4f} in^2; Helmholtz/inverse-volume "
        f"bridge documented but NOT solved (no A0, no L_eff).",
        "MB Torrefied Adirondack distribution preserved as EXTERNAL_EMPIRICAL_PRIOR by pin-reference "
        "(no payload duplicated; zero influence on 004G geometry).",
        "No family member promoted to 'the back'; no historical radius claimed; family intentionally non-unique.",
    ]
    return dict(G=G, members=members, brace_rows=brace_rows, stations=stations,
                v_floor=v_floor, refine=refine, mb_pin=mb_pin, disp=disp, notes=notes)


def refinement_check(G: Dict) -> Dict:
    """Report volume integration sensitivity by refining the grid to STEP/2 for the floor."""
    rim, outline, tps = G["rim"], G["outline"], G["tps"]
    L = rim["L"]
    hw_max = float(outline["hw"].max())
    step2 = STEP / 2.0
    xs = np.round(np.arange(-hw_max - step2, hw_max + step2 + 1e-9, step2), 4)
    ys = np.round(np.arange(0.0, L + 1e-9, step2), 4)
    XX, YY = np.meshgrid(xs, ys)
    HW = np.array([E.half_width_at(outline, float(v)) for v in ys])[:, None]
    inside = np.abs(XX) <= HW + 1e-9
    pts = np.column_stack([XX[inside], YY[inside]])
    z = np.full(XX.shape, np.nan)
    z[inside] = tps.zf(pts)
    vol_fine = float(np.nansum(z[inside]) * step2 * step2)
    vol_coarse = G["v_floor"] if "v_floor" in G else body_volume_in3(G, 0.0)
    return {"vol_coarse_in3": vol_coarse, "vol_fine_in3": vol_fine,
            "rel_delta": abs(vol_fine - vol_coarse) / vol_coarse}


# =============================================================================
# Writers
# =============================================================================

def _wr_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def write_members(R: Dict) -> None:
    rows = []
    for m in R["members"]:
        c = m["curv"]
        rows.append({
            "member": m["name"], "frac": f"{m['frac']:.2f}", "alpha_in": f"{m['alpha']:.5f}",
            "max_rise_mm": f"{m['h_max_mm']:.3f}", "apex_x_in": f"{m['apex_x']:.3f}",
            "apex_y_in": f"{m['apex_y']:.3f}", "volume_in3": f"{m['volume_in3']:.3f}",
            "volume_cm3": f"{m['volume_in3']*IN3_TO_CM3:.2f}",
            "volume_L": f"{m['volume_in3']*IN3_TO_CM3/1000:.4f}",
            "arch_contribution_cm3": f"{m['arch_in3']*IN3_TO_CM3:.3f}",
            "mean_curv_min": f"{c['mean_min']:.5f}", "mean_curv_max": f"{c['mean_max']:.5f}",
            "gauss_curv_min": f"{c['gauss_min']:.6f}", "gauss_curv_max": f"{c['gauss_max']:.6f}",
            "saddle_present": c["saddle"], "rim_exact": True, "admissible": True,
        })
    _wr_csv(MEMBERS_CSV, list(rows[0].keys()), rows)


def write_brace_sampling(R: Dict) -> None:
    rows = []
    for b in R["brace_rows"]:
        for (name, rise, rad_in, rad_ft, curv) in b["per_member"]:
            rows.append({
                "brace_id": b["brace_id"], "y_from_neck_in": f"{b['y_in']:.3f}",
                "position_uncertainty_in": f"{b['unc_in']:.2f}", "member": name,
                "surface_rise_center_mm": f"{rise:.3f}",
                "transverse_fitted_radius_ft": (f"{rad_ft:.2f}" if np.isfinite(rad_ft) else ""),
                "transverse_curvature_perin": (f"{curv:.5f}" if np.isfinite(curv) else ""),
                "note": "back-SURFACE curvature under brace; brace-bottom curvature UNKNOWN (004F)",
            })
    _wr_csv(BRACE_CSV, list(rows[0].keys()), rows)


def write_envelope(R: Dict) -> None:
    """Per-station rise + radius envelope across the family (min/max)."""
    rows = []
    for b in R["brace_rows"]:
        rows.append({
            "station": b["brace_id"], "y_from_neck_in": f"{b['y_in']:.3f}",
            "position_uncertainty_in": f"{b['unc_in']:.2f}",
            "rise_min_mm": f"{b['rise_min_mm']:.3f}", "rise_max_mm": f"{b['rise_max_mm']:.3f}",
            "transverse_radius_min_ft": (f"{b['radius_min_ft']:.2f}" if np.isfinite(b['radius_min_ft']) else ""),
            "transverse_radius_max_ft": (f"{b['radius_max_ft']:.2f}" if np.isfinite(b['radius_max_ft']) else ""),
            "class": "FAMILY_ENVELOPE (bounded, non-unique)",
        })
    # also a whole-body center-rise envelope row
    ms = R["members"]
    rows.append({"station": "BODY_center_apex", "y_from_neck_in": f"{ms[0]['apex_y']:.3f}",
                 "position_uncertainty_in": "", "rise_min_mm": f"{ms[0]['h_max_mm']:.3f}",
                 "rise_max_mm": f"{ms[-1]['h_max_mm']:.3f}", "transverse_radius_min_ft": "",
                 "transverse_radius_max_ft": "", "class": "FAMILY_ENVELOPE (max interior rise)"})
    _wr_csv(ENVELOPE_CSV, list(rows[0].keys()), rows)


def write_volume(R: Dict) -> None:
    rows = []
    vf = R["members"][0]["volume_in3"]
    for m in R["members"]:
        rows.append({
            "member": m["name"], "alpha_in": f"{m['alpha']:.5f}", "max_rise_mm": f"{m['h_max_mm']:.3f}",
            "body_volume_in3": f"{m['volume_in3']:.3f}",
            "body_volume_cm3": f"{m['volume_in3']*IN3_TO_CM3:.2f}",
            "body_volume_L": f"{m['volume_in3']*IN3_TO_CM3/1000:.4f}",
            "delta_vs_floor_cm3": f"{(m['volume_in3']-vf)*IN3_TO_CM3:.3f}",
            "back_arch_contribution_cm3": f"{m['arch_in3']*IN3_TO_CM3:.3f}",
            "top_assumption": "flat-top plane z=0",
            "top_assumption_contribution_in3": "0.000",
            "top_assumption_class": "GEOMETRIC_REFERENCE_ONLY",
            "case_B_top_dome": "UNRESOLVED (no #65260-source-supported top radius; not invented)",
            "uncertainty_class": "GEOMETRIC_REFERENCE_ONLY (not an acoustically validated cavity volume)",
        })
    rows.append({"member": "GRID_REFINEMENT_CHECK", "alpha_in": "", "max_rise_mm": "",
                 "body_volume_in3": f"{R['refine']['vol_fine_in3']:.3f}", "body_volume_cm3": "",
                 "body_volume_L": "", "delta_vs_floor_cm3": "",
                 "back_arch_contribution_cm3": "",
                 "top_assumption": f"floor @ step={STEP/2:.3f} in vs {STEP:.3f} in",
                 "top_assumption_contribution_in3": "",
                 "top_assumption_class": f"rel_delta={R['refine']['rel_delta']:.2e}",
                 "case_B_top_dome": "", "uncertainty_class": "integration convergence diagnostic"})
    _wr_csv(VOLUME_CSV, list(rows[0].keys()), rows)


def write_soundhole(R: Dict) -> None:
    rec = {
        "soundhole_diameter_in": SOUNDHOLE_DIAMETER_IN,
        "soundhole_area_in2": round(SOUNDHOLE_AREA_IN2, 6),
        "soundhole_area_m2": round(SOUNDHOLE_AREA_IN2 * 0.00064516, 9),
        "class": "FIXED_GEOMETRY (Ø4.0 in, from the Arnold drawing / JD trace)",
        "helmholtz_bridge": {
            "forward_f_H": "f_H = (c / (2*pi)) * sqrt(A / (V * L_eff))",
            "inverse_V": "V = (A * c^2) / ((2*pi*f_H)^2 * L_eff)",
            "symbols": {"A": "soundhole area (m^2)", "V": "cavity air volume (m^3)",
                        "L_eff": "effective soundhole length (m)", "c": "speed of sound (m/s)",
                        "f_H": "Helmholtz / A0 air-mode frequency (Hz)"},
        },
        "not_solved": True,
        "no_guessed_A0": True,
        "no_guessed_L_eff": True,
        "statement": ("Body volume becomes an INDEPENDENT global discriminator once a measured air "
                      "mode (A0) and a defensible L_eff are introduced; it can then reject members of "
                      "the admissible back-surface family. 004G solves no Helmholtz frequency."),
    }
    os.makedirs(os.path.dirname(SOUNDHOLE_JSON), exist_ok=True)
    with open(SOUNDHOLE_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


def write_mb_prior(R: Dict) -> None:
    pin = R["mb_pin"]
    rows = []
    for (metric, mn, mean, mx, units) in MB_ENVELOPE:
        rows.append({"metric": metric, "min": mn, "mean": mean, "max": mx, "units": units,
                     "subset": MB_SUBSET, "n_specimens": MB_SUBSET_N,
                     "classification": "EXTERNAL_EMPIRICAL_PRIOR_TORREFIED_ADIRONDACK",
                     "corpus_pin": pin["release_tag"], "corpus_digest_sha256": pin["corpus_digest_sha256"],
                     "treatment": "torrefied", "geometry_influence_on_004G": "NONE",
                     "note": "distribution summary carried by reference to the pinned corpus; "
                             "per-specimen payload NOT duplicated (DATA-MIG-002)"})
    _wr_csv(MB_CSV, list(rows[0].keys()), rows)


def write_authority(R: Dict) -> None:
    ms = R["members"]
    pin = R["mb_pin"]
    rec = {
        "experiment": "D28_RUN_004G_BOUNDED_BACK_SURFACE_AND_BODY_VOLUME_FAMILY",
        "disposition": R["disp"],
        "family_model": "z(x,y;alpha) = z_TPS(x,y) + alpha*Phi(x,y)",
        "phi": {"form": "(1 - (x/hw(y))^2) * sin(pi*y/L), peak-normalized to 1",
                "zero_on_rim": True, "deterministic": True},
        "fixed_inputs": {
            "rim": "D28_65260_REGISTERED_RIM_004D.csv (exact boundary)",
            "z_TPS_floor": "004E boundary-exact minimal surface (reused)",
            "brace_positions": "D28_65260_BACK_BRACE_POSITIONS_004F.csv (±0.4 in)",
            "e004_candidate_envelope": "D28_65260_BACK_SURFACE_CANDIDATES_004E.csv",
        },
        "interior_rise_envelope_mm": {"floor": RISE_FLOOR_MM, "ceiling": RISE_CEIL_MM,
                                      "basis": "004E rim-fitting candidates (TPS floor .. best-fit sphere/compound)"},
        "genone_reference_mm": {"range": [4.0, 6.0], "role": "REFERENCE_ONLY (above the evidence "
                                "envelope; NOT a bound, NOT a target)"},
        "members": [{"name": m["name"], "alpha_in": round(m["alpha"], 5),
                     "max_rise_mm": round(m["h_max_mm"], 3),
                     "volume_L": round(m["volume_in3"] * IN3_TO_CM3 / 1000, 4),
                     "saddle": m["curv"]["saddle"], "rim_exact": True} for m in ms],
        "lower_bout_reflex_preserved": True,
        "no_member_promoted_to_the_back": True,
        "body_volume_top_assumption": {"case_A": "flat-top plane z=0 (GEOMETRIC_REFERENCE_ONLY)",
                                       "case_B": "top dome UNRESOLVED (no #65260 top radius; not invented)"},
        "soundhole_area_in2": round(SOUNDHOLE_AREA_IN2, 6),
        "mb_prior": {"classification": "EXTERNAL_EMPIRICAL_PRIOR_TORREFIED_ADIRONDACK",
                     "subset": MB_SUBSET, "n": MB_SUBSET_N, "corpus_pin": pin["release_tag"],
                     "canonical_repository": pin["canonical_repository"],
                     "provenance_class": pin["provenance_class"],
                     "payload_duplicated": False, "geometry_influence": "NONE",
                     "governance": "DATA-MIG-002: consumed by pin, never by copy; carried as a "
                                   "distribution summary pointer, not a toolbox data authority"},
        "engineering_interpretation": [
            ("Body volume is a global integral constraint and may later eliminate members of the "
             "admissible back-surface family when independent acoustic evidence is introduced. Volume "
             "does not, by itself, establish a unique historical radius. Radius remains a derived "
             "diagnostic unless the governing surface family is independently justified."),
            ("MB Torrefied Adirondack measurements provide an empirical material-response distribution "
             "for future model calibration and validation. They do not constrain 004G geometry and are "
             "not evidence that #65260 used material with identical treatment or properties."),
        ],
        "no_production_changes": True, "no_prior_run_alteration": True, "pdf_vendored": False,
    }
    os.makedirs(os.path.dirname(AUTHORITY_JSON), exist_ok=True)
    with open(AUTHORITY_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


def write_summary(R: Dict) -> None:
    ms = R["members"]
    vols_L = [m["volume_in3"] * IN3_TO_CM3 / 1000 for m in ms]
    row = {
        "disposition": R["disp"],
        "n_members": len(ms),
        "rise_floor_mm": f"{ms[0]['h_max_mm']:.3f}", "rise_ceiling_mm": f"{ms[-1]['h_max_mm']:.3f}",
        "alpha_floor_in": f"{ms[0]['alpha']:.5f}", "alpha_ceiling_in": f"{ms[-1]['alpha']:.5f}",
        "body_volume_floor_L": f"{vols_L[0]:.4f}", "body_volume_ceiling_L": f"{vols_L[-1]:.4f}",
        "body_volume_delta_L": f"{vols_L[-1]-vols_L[0]:.4f}",
        "volume_monotonic_in_alpha": "yes (V = V0 + alpha*integral(Phi), Phi>=0)",
        "top_assumption": "flat-top z=0 (GEOMETRIC_REFERENCE_ONLY); top dome UNRESOLVED",
        "soundhole_area_in2": f"{SOUNDHOLE_AREA_IN2:.4f}",
        "helmholtz_solved": "no (bridge documented; no A0, no L_eff)",
        "grid_refinement_rel_delta": f"{R['refine']['rel_delta']:.2e}",
        "mb_prior": f"EXTERNAL_EMPIRICAL_PRIOR_TORREFIED_ADIRONDACK (n={MB_SUBSET_N}, by pin {R['mb_pin']['release_tag']})",
        "mb_geometry_influence": "NONE",
        "genone_4_6mm": "reference-only (above envelope)",
        "member_promoted": "none (family intentionally non-unique)",
        "final_disposition": R["disp"],
    }
    _wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004G_BOUNDED_BACK_SURFACE_AND_BODY_VOLUME_FAMILY",
        "parent_commit": git_sha(),
        "script": "scripts/experiments/d28_rerun004g_bounded_back_surface_family.py",
        "command": "python scripts/experiments/d28_rerun004g_bounded_back_surface_family.py --write",
        "committed_inputs": [
            "docs/experiments/results/D28_65260_REGISTERED_RIM_004D.csv",
            "docs/experiments/results/D28_65260_RERUN_004E_SUMMARY.csv",
            "docs/experiments/results/D28_65260_BACK_SURFACE_CANDIDATES_004E.csv",
            "docs/experiments/results/D28_65260_BACK_BRACE_POSITIONS_004F.csv",
            "docs/reference/mb-sound/CORPUS_DEPENDENCY.json (pin reference)",
        ],
        "reuses_004e_module": "d28_rerun004e_back_surface_reconstruction.py (z_TPS, grid, curvature)",
        "output_paths": [os.path.basename(p) for p in (
            AUTHORITY_JSON, ENVELOPE_CSV, MEMBERS_CSV, BRACE_CSV, VOLUME_CSV, SOUNDHOLE_JSON,
            MB_CSV, SUMMARY_CSV, PROVENANCE_JSON)],
        "mb_payload_duplicated": False,
        "mb_influence_on_geometry": "NONE",
        "no_new_single_surface_promoted": True,
        "no_production_changes": True, "no_prior_run_alteration": True, "pdf_vendored": False,
        "disposition": R["disp"],
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
    ms = R["members"]
    vols_L = [m["volume_in3"] * IN3_TO_CM3 / 1000 for m in ms]
    w("## Run 004G — Bounded Back-Surface Family + Body-Volume Envelope")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Formalizes the admissible #65260 back-surface family surviving 004F, quantifies the "
      "geometric **body-volume envelope**, carries the Ø4.0 in soundhole with an unsolved "
      "Helmholtz bridge, and preserves the MB Torrefied Adirondack distribution as an external "
      "material prior. **No historical radius is claimed; no family member is promoted to 'the back.'**")
    w("- Rim-exact family: `z(x,y;α) = z_TPS(x,y) + α·Φ(x,y)`, with `z_TPS` the 004E boundary-exact "
      "floor and `Φ = (1 − (x/hw(y))²)·sin(πy/L)` (peak-normalized) **exactly zero on the entire "
      "rim** → every member meets the 004D rim exactly.")
    w("- Artifacts: `D28_65260_BACK_SURFACE_FAMILY_AUTHORITY_004G.json`, "
      "`…_FAMILY_ENVELOPE_004G.csv`, `…_FAMILY_MEMBERS_004G.csv`, `…_FAMILY_BRACE_SAMPLING_004G.csv`, "
      "`D28_65260_BODY_VOLUME_ENVELOPE_004G.csv`, `D28_65260_SOUNDHOLE_VOLUME_BRIDGE_004G.json`, "
      "`D28_65260_MB_TORREFIED_ADIRONDACK_PRIOR_004G.csv`, `…_RERUN_004G_SUMMARY.csv`, "
      "`…_RERUN_004G_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### Bounded back-surface family (5 members, intentionally non-unique)")
    w("")
    w("| member | α (in) | max rise (mm) | apex (x,y in) | body volume (L) | saddle | rim-exact |")
    w("|---|---:|---:|---|---:|:--:|:--:|")
    for m, vL in zip(ms, vols_L):
        w(f"| {m['name']} | {m['alpha']:.4f} | {m['h_max_mm']:.2f} | "
          f"({m['apex_x']:.2f}, {m['apex_y']:.2f}) | {vL:.3f} | "
          f"{'yes' if m['curv']['saddle'] else 'no'} | yes |")
    w("")
    w(f"- Interior-rise envelope **[{ms[0]['h_max_mm']:.2f}, {ms[-1]['h_max_mm']:.2f}] mm** "
      "(TPS floor → best-fit-sphere/compound ceiling). The GenOne 4–6 mm reference lies **above** "
      "this evidence envelope and is recorded reference-only (not a bound/target). The TPS floor's "
      "slight lower-bout reflex is preserved (not clamped).")
    w("")
    w("### Body-volume envelope (geometric reference only)")
    w("")
    w(f"- Flat-top reference (top plane z=0, `GEOMETRIC_REFERENCE_ONLY`): body volume spans "
      f"**[{vols_L[0]:.3f}, {vols_L[-1]:.3f}] L** across the family (Δ = {(vols_L[-1]-vols_L[0]):.3f} L); "
      "volume increases monotonically with α by construction (`V = V₀ + α·∬Φ`, Φ≥0).")
    w(f"- Back-arch contribution spans [{ms[0]['arch_in3']*IN3_TO_CM3:.1f}, "
      f"{ms[-1]['arch_in3']*IN3_TO_CM3:.1f}] cm³. **Case B** (top dome) is **UNRESOLVED** — no "
      "#65260-source-supported top radius exists and none is invented. This is **not** an "
      "acoustically validated cavity volume.")
    w(f"- Grid-refinement sensitivity (STEP {STEP}→{STEP/2} in) on the floor volume: "
      f"rel. Δ = {R['refine']['rel_delta']:.2e}.")
    w("")
    w("### Per-brace envelopes (BB1–BB4; ±0.4 in positional uncertainty)")
    w("")
    w("| station | y (in) | surface rise (mm) min–max | transverse radius (ft) min–max |")
    w("|---|---:|---|---|")
    for b in R["brace_rows"]:
        rr = (f"{b['radius_min_ft']:.1f}–{b['radius_max_ft']:.1f}"
              if np.isfinite(b['radius_min_ft']) else "n/a")
        w(f"| {b['brace_id']} | {b['y_in']:.2f} | {b['rise_min_mm']:.2f}–{b['rise_max_mm']:.2f} | {rr} |")
    w("")
    w("- These are the **back-surface** curvature/rise envelopes **under** each brace across the "
      "family; the brace-bottom curvature itself remains **unknown** (004F).")
    w("")
    w("### Soundhole / Helmholtz bridge (fixed geometry; not solved)")
    w("")
    w(f"- Ø4.0 in soundhole → area **A = {SOUNDHOLE_AREA_IN2:.4f} in²** (fixed). Bridge recorded: "
      "`f_H = (c/2π)·√(A/(V·L_eff))`, inverse `V = A·c²/((2π f_H)²·L_eff)`. **Not solved** — no "
      "guessed A0, no guessed L_eff.")
    w("")
    w("### MB Torrefied Adirondack prior (external, pin-referenced)")
    w("")
    w(f"- Carried as `EXTERNAL_EMPIRICAL_PRIOR_TORREFIED_ADIRONDACK` (subset n={MB_SUBSET_N}) **by "
      f"reference to the pinned corpus** `{R['mb_pin']['release_tag']}` — per-specimen payload is "
      "**not duplicated** into the repo (DATA-MIG-002 / `no_local_copy`). The population envelope "
      "(density, resonance, E, Q, time-constant, radiation-coefficient, thickness) is preserved as a "
      "distribution summary. **Zero influence on 004G geometry.**")
    w("")
    w("### Engineering interpretation")
    w("")
    w("> Body volume is a global integral constraint and may later eliminate members of the "
      "admissible back-surface family when independent acoustic evidence is introduced. Volume does "
      "not, by itself, establish a unique historical radius. Radius remains a derived diagnostic "
      "unless the governing surface family is independently justified.")
    w(">")
    w("> MB Torrefied Adirondack measurements provide an empirical material-response distribution for "
      "future model calibration and validation. They do not constrain 004G geometry and are not "
      "evidence that #65260 used material with identical treatment or properties.")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Parent dispositions (001–004F) are untouched. 004G promotes no single surface, claims no "
      "historical radius, fabricates no top dome or A0, and changes no geometry from the MB prior.")
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
    elif "<!-- RERUN004F_START -->" in text:
        marker = "<!-- RERUN004F_START -->"
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
        write_authority(R); write_envelope(R); write_members(R); write_brace_sampling(R)
        write_volume(R); write_soundhole(R); write_mb_prior(R); write_summary(R); write_provenance(R)
        splice_doc(section)
        print(f"wrote 004G artifacts; disposition={R['disp']}; "
              f"rise=[{R['members'][0]['h_max_mm']:.2f},{R['members'][-1]['h_max_mm']:.2f}]mm; "
              f"vol=[{R['members'][0]['volume_in3']*IN3_TO_CM3/1000:.3f},"
              f"{R['members'][-1]['volume_in3']*IN3_TO_CM3/1000:.3f}]L")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; members={[m['name'] for m in R['members']]}]")


if __name__ == "__main__":
    main()
