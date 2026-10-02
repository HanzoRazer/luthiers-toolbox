#!/usr/bin/env python3
"""
D28 RUN 004N — Corrected Back Surface Family
============================================

Rebuilds the bounded back-surface family from the CORRECTED rim (004M), with the
interior explicitly classified as CONSTRUCTED (not a recovered historical back),
and REPLACES the 004G forced-zero boundary check with a genuine rim-boundary
residual evaluation.

Family model (unchanged form; corrected rim):
    z(x, y; alpha) = z_TPS(x, y) + alpha * Phi(x, y)
  * z_TPS  = boundary-exact thin-plate-spline on the 004M rim (reused 004E machinery)
  * Phi    = deterministic analytic zero-on-rim bulge, peak-normalized
  * alpha >= 0 scales interior rise over the evidence envelope [1.61, 2.80] mm

Boundary residual (fix for the 004G multiply-by-zero placeholder):
    e_i = z_surface(x_i, y_i) - z_rim(x_i, y_i)   at the ACTUAL rim-boundary samples
    report max|e|, RMSE, n_samples, tolerance, pass/fail — for every member.

Every surface member is labelled CONSTRUCTED_ADMISSIBLE_SURFACE. 004N does NOT
promote any member to "the back", claims no historical radius, and does not modify
004G's artifacts. No production/spec/authority edits; no PDF; experiment branch only.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys
from typing import Dict, List

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))


def _load(name, fname):
    path = os.path.join(_HERE, fname)
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


GA = _load("d28_geometry_authority", "d28_geometry_authority.py")
G04 = _load("d28_004g_for_n", "d28_rerun004g_bounded_back_surface_family.py")
E = G04.E  # the 004E module instance G04 uses internally

_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Inputs (committed, read-only) -------------------------------------------
M_RIM_CSV = os.path.join(_RESULTS, "D28_65260_REGISTERED_RIM_004M.csv")  # corrected rim (004M)
F_POSITIONS_CSV = os.path.join(_RESULTS, "D28_65260_BACK_BRACE_POSITIONS_004F.csv")

# --- Outputs (004N only) -----------------------------------------------------
FAMILY_CSV = os.path.join(_OUTDIR, "D28_65260_BACK_SURFACE_FAMILY_004N.csv")
AUTHORITY_JSON = os.path.join(_OUTDIR, "D28_65260_BACK_SURFACE_AUTHORITY_004N.json")
RESIDUAL_CSV = os.path.join(_OUTDIR, "D28_65260_BACK_BOUNDARY_RESIDUAL_004N.csv")
BRACE_CSV = os.path.join(_OUTDIR, "D28_65260_BACK_BRACE_SAMPLING_004N.csv")
VOLUME_CSV = os.path.join(_OUTDIR, "D28_65260_BODY_VOLUME_ENVELOPE_004N.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004N_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004N_PROVENANCE.json")

_S, _E = "<!-- RERUN004N_START -->", "<!-- RERUN004N_END -->"

MM = 25.4
IN3_TO_CM3 = G04.IN3_TO_CM3
BOUNDARY_TOL_IN = 1.0e-3   # 0.001 in (~0.025 mm): boundary-exact TPS, phi=0 on rim


def _phi_grid_peak(G: Dict) -> float:
    """Reproduce G04.phi_field's normalization peak (raw interior Phi max)."""
    XX, YY, HW, inside, L = G["XX"], G["YY"], G["HW"], G["inside"], G["L"]
    with np.errstate(invalid="ignore", divide="ignore"):
        hw = np.where(HW > 0, HW, np.nan)
        praw = (1.0 - (XX / hw) ** 2) * np.sin(np.pi * YY / L)
    praw = np.where(inside, praw, 0.0)
    praw = np.clip(praw, 0.0, None)
    return float(np.nanmax(praw[inside]))


def _phi_norm_at_boundary(G: Dict, bx: np.ndarray, by: np.ndarray, peak: float) -> np.ndarray:
    """Analytic normalized Phi at arbitrary (x, y) boundary points (expected ~0 on
    the rim, but COMPUTED, never forced)."""
    outline, L = G["outline"], G["L"]
    out = np.zeros_like(bx, dtype=float)
    for i, (x, y) in enumerate(zip(bx, by)):
        hw = E.half_width_at(outline, float(y))
        if hw <= 0:
            out[i] = 0.0
            continue
        v = (1.0 - (float(x) / hw) ** 2) * math.sin(math.pi * float(y) / L)
        out[i] = max(v, 0.0) / peak
    return out


def real_boundary_residual(G: Dict, alpha: float, peak: float) -> Dict:
    """REAL residual e_i = z_member(x_i,y_i) - z_rim(x_i,y_i) at the rim boundary."""
    bnd = G["bnd"]
    P = np.column_stack([bnd["x"], bnd["y"]])
    z_tps_bnd = G["tps"].zf(P)
    phi_bnd = _phi_norm_at_boundary(G, bnd["x"], bnd["y"], peak)
    z_member_bnd = z_tps_bnd + alpha * phi_bnd
    res = GA.boundary_residuals(z_member_bnd, bnd["z"])
    res["phi_boundary_max"] = float(np.max(np.abs(phi_bnd)))
    res["tolerance_in"] = BOUNDARY_TOL_IN
    res["pass"] = bool(res["max_abs"] <= BOUNDARY_TOL_IN)
    return res


def run_all() -> Dict:
    # Drive the 004E/004G machinery from the CORRECTED 004M rim.
    if not os.path.exists(M_RIM_CSV):
        raise SystemExit("STOP: corrected 004M rim not found (run 004M first)")
    E.RIM_CSV = M_RIM_CSV
    G = G04.build_geometry()
    peak = _phi_grid_peak(G)
    stations = G04.load_brace_stations()

    members = []
    for name, frac in G04.FAMILY_FRACTIONS:
        target = G04.RISE_FLOOR_MM + frac * (G04.RISE_CEIL_MM - G04.RISE_FLOOR_MM)
        alpha = G04.solve_alpha_for_rise(G, target)
        hmax = G04.h_max_mm(G, alpha)
        ax, ay, _ = G04.apex_of(G, alpha)
        vol = G04.body_volume_in3(G, alpha)
        arch = G04.arch_volume_in3(G, alpha)
        cur = G04.curvature_stats(G, alpha)
        resid = real_boundary_residual(G, alpha, peak)
        members.append({"name": name, "frac": frac, "alpha": alpha, "h_max_mm": hmax,
                        "apex_x": ax, "apex_y": ay, "volume_in3": vol, "arch_in3": arch,
                        "curv": cur, "resid": resid,
                        "classification": "CONSTRUCTED_ADMISSIBLE_SURFACE"})

    # Brace sampling across the family.
    brace_rows = []
    for bb in ("BB1", "BB2", "BB3", "BB4"):
        y = stations[bb]["y_in"]
        per = []
        for m in members:
            t = G04.brace_transverse(G, m["alpha"], y)
            per.append((m["name"], t["rise_center_mm"], t.get("radius_ft", float("nan"))))
        rises = [p[1] for p in per]
        radii = [p[2] for p in per if np.isfinite(p[2])]
        brace_rows.append({"brace_id": bb, "y_in": y, "unc_in": stations[bb]["unc_in"],
                           "rise_min_mm": min(rises), "rise_max_mm": max(rises),
                           "radius_min_ft": (min(radii) if radii else float("nan")),
                           "radius_max_ft": (max(radii) if radii else float("nan")),
                           "per_member": per})

    refine = G04.refinement_check(G)

    boundary_all_pass = all(m["resid"]["pass"] for m in members)
    max_boundary_abs = max(m["resid"]["max_abs"] for m in members)
    saddle_any = any(m["curv"]["saddle"] for m in members)

    if not boundary_all_pass:
        disp = "CORRECTED_BACK_SURFACE_BOUNDARY_FAILED"
        notes = [f"STOP: a constructed member violates the rim boundary "
                 f"(max |e| = {max_boundary_abs:.2e} in > {BOUNDARY_TOL_IN} in)."]
    else:
        disp = "CORRECTED_BOUNDED_BACK_SURFACE_FAMILY_CONSTRUCTED"
        notes = [
            f"Bounded CONSTRUCTED back-surface family on the CORRECTED 004M rim: "
            f"z = z_TPS + alpha*Phi over interior rise "
            f"[{members[0]['h_max_mm']:.2f}, {members[-1]['h_max_mm']:.2f}] mm (5 members).",
            f"GENUINE rim-boundary residual (replaces the 004G forced zero): max |e| = "
            f"{max_boundary_abs:.2e} in across all members (tol {BOUNDARY_TOL_IN} in) — the "
            "boundary-exact TPS and the zero-on-rim Phi are confirmed by evaluation, not asserted.",
            f"Geometric body-volume envelope (flat-top reference, GEOMETRIC_REFERENCE_ONLY): "
            f"[{min(m['volume_in3'] for m in members)*IN3_TO_CM3/1000:.3f}, "
            f"{max(m['volume_in3'] for m in members)*IN3_TO_CM3/1000:.3f}] L.",
            "Every member is CONSTRUCTED_ADMISSIBLE_SURFACE — NOT a measured/recovered historical "
            "back. No member promoted; no historical radius claimed; family intentionally non-unique.",
        ]
    return dict(G=G, members=members, brace_rows=brace_rows, stations=stations, refine=refine,
                peak=peak, boundary_all_pass=boundary_all_pass, max_boundary_abs=max_boundary_abs,
                saddle_any=saddle_any, disp=disp, notes=notes)


# =============================================================================
# Writers
# =============================================================================

def write_family(R: Dict) -> None:
    rows = []
    for m in R["members"]:
        c = m["curv"]
        rows.append({
            "member": m["name"], "frac": f"{m['frac']:.2f}", "alpha_in": f"{m['alpha']:.5f}",
            "max_rise_mm": f"{m['h_max_mm']:.3f}", "apex_x_in": f"{m['apex_x']:.3f}",
            "apex_y_in": f"{m['apex_y']:.3f}", "volume_in3": f"{m['volume_in3']:.3f}",
            "volume_L": f"{m['volume_in3']*IN3_TO_CM3/1000:.4f}",
            "arch_contribution_cm3": f"{m['arch_in3']*IN3_TO_CM3:.3f}",
            "gauss_curv_min": f"{c['gauss_min']:.6f}", "gauss_curv_max": f"{c['gauss_max']:.6f}",
            "saddle_present": c["saddle"],
            "boundary_max_abs_in": f"{m['resid']['max_abs']:.3e}",
            "boundary_rmse_in": f"{m['resid']['rmse']:.3e}",
            "boundary_pass": m["resid"]["pass"],
            "classification": m["classification"],
        })
    GA.wr_csv(FAMILY_CSV, list(rows[0].keys()), rows)


def write_residual(R: Dict) -> None:
    rows = []
    for m in R["members"]:
        r = m["resid"]
        rows.append({
            "member": m["name"], "alpha_in": f"{m['alpha']:.5f}",
            "max_abs_boundary_error_in": f"{r['max_abs']:.3e}",
            "boundary_rmse_in": f"{r['rmse']:.3e}",
            "number_of_boundary_samples": r["n_samples"],
            "phi_on_boundary_max": f"{r['phi_boundary_max']:.3e}",
            "tolerance_in": f"{r['tolerance_in']:.1e}",
            "pass": r["pass"],
            "method": "e_i = z_member(x_i,y_i) - z_rim(x_i,y_i) at the actual rim boundary "
                      "(replaces the 004G forced-zero placeholder)",
        })
    GA.wr_csv(RESIDUAL_CSV, list(rows[0].keys()), rows)


def write_brace(R: Dict) -> None:
    rows = []
    for b in R["brace_rows"]:
        for (name, rise, rad_ft) in b["per_member"]:
            rows.append({
                "brace_id": b["brace_id"], "y_from_neck_in": f"{b['y_in']:.3f}",
                "position_uncertainty_in": f"{b['unc_in']:.2f}", "member": name,
                "surface_rise_center_mm": f"{rise:.3f}",
                "transverse_fitted_radius_ft": (f"{rad_ft:.2f}" if np.isfinite(rad_ft) else ""),
                "classification": "CONSTRUCTED_ADMISSIBLE_SURFACE",
                "note": "back-SURFACE curvature under brace; brace-bottom curvature UNKNOWN (004F)",
            })
    GA.wr_csv(BRACE_CSV, list(rows[0].keys()), rows)


def write_volume(R: Dict) -> None:
    rows = []
    vf = R["members"][0]["volume_in3"]
    for m in R["members"]:
        rows.append({
            "member": m["name"], "alpha_in": f"{m['alpha']:.5f}", "max_rise_mm": f"{m['h_max_mm']:.3f}",
            "body_volume_in3": f"{m['volume_in3']:.3f}",
            "body_volume_L": f"{m['volume_in3']*IN3_TO_CM3/1000:.4f}",
            "delta_vs_floor_cm3": f"{(m['volume_in3']-vf)*IN3_TO_CM3:.3f}",
            "back_arch_contribution_cm3": f"{m['arch_in3']*IN3_TO_CM3:.3f}",
            "top_assumption": "flat-top plane z=0 (GEOMETRIC_REFERENCE_ONLY)",
            "case_B_top_dome": "UNRESOLVED (no #65260 top radius; not invented)",
            "classification": "CONSTRUCTED_ADMISSIBLE_SURFACE",
        })
    rows.append({"member": "GRID_REFINEMENT_CHECK", "alpha_in": "", "max_rise_mm": "",
                 "body_volume_in3": f"{R['refine']['vol_fine_in3']:.3f}", "body_volume_L": "",
                 "delta_vs_floor_cm3": "", "back_arch_contribution_cm3": "",
                 "top_assumption": f"floor @ step/2 rel_delta={R['refine']['rel_delta']:.2e}",
                 "case_B_top_dome": "", "classification": "integration convergence diagnostic"})
    GA.wr_csv(VOLUME_CSV, list(rows[0].keys()), rows)


def write_authority(R: Dict) -> None:
    ms = R["members"]
    rec = {
        "experiment": "D28_RUN_004N_CORRECTED_BACK_SURFACE_FAMILY",
        "disposition": R["disp"],
        "rim_source": "D28_65260_REGISTERED_RIM_004M.csv (corrected developed-arc rim, 004M)",
        "family_model": "z(x,y;alpha) = z_TPS(x,y) + alpha*Phi(x,y)",
        "interior_classification": "CONSTRUCTED_ADMISSIBLE_SURFACE (NOT a measured/recovered back)",
        "boundary_residual": {
            "method": "e_i = z_member(x_i,y_i) - z_rim(x_i,y_i) at actual rim boundary samples",
            "replaces": "004G forced-zero placeholder (interior Phi multiplied by zero)",
            "tolerance_in": BOUNDARY_TOL_IN,
            "max_abs_in_across_family": R["max_boundary_abs"],
            "all_members_pass": R["boundary_all_pass"],
            "n_boundary_samples": ms[0]["resid"]["n_samples"],
        },
        "interior_rise_envelope_mm": {"floor": G04.RISE_FLOOR_MM, "ceiling": G04.RISE_CEIL_MM},
        "members": [{"name": m["name"], "alpha_in": round(m["alpha"], 5),
                     "max_rise_mm": round(m["h_max_mm"], 3),
                     "volume_L": round(m["volume_in3"] * IN3_TO_CM3 / 1000, 4),
                     "saddle": m["curv"]["saddle"],
                     "boundary_max_abs_in": m["resid"]["max_abs"],
                     "classification": m["classification"]} for m in ms],
        "no_member_promoted_to_the_back": True,
        "no_historical_radius_claimed": True,
        "body_volume_top_assumption": {"case_A": "flat-top plane z=0 (GEOMETRIC_REFERENCE_ONLY)",
                                       "case_B": "top dome UNRESOLVED (not invented)"},
        "no_production_changes": True, "no_prior_run_alteration": True, "pdf_vendored": False,
    }
    GA.write_provenance_json(AUTHORITY_JSON, rec)


def write_summary(R: Dict) -> None:
    ms = R["members"]
    vols_L = [m["volume_in3"] * IN3_TO_CM3 / 1000 for m in ms]
    row = {
        "disposition": R["disp"],
        "rim_source": "D28_65260_REGISTERED_RIM_004M.csv (corrected 004M)",
        "n_members": len(ms),
        "rise_floor_mm": f"{ms[0]['h_max_mm']:.3f}", "rise_ceiling_mm": f"{ms[-1]['h_max_mm']:.3f}",
        "body_volume_floor_L": f"{vols_L[0]:.4f}", "body_volume_ceiling_L": f"{vols_L[-1]:.4f}",
        "boundary_residual_method": "real e_i = z_surface - z_rim (NOT forced zero)",
        "boundary_max_abs_in": f"{R['max_boundary_abs']:.3e}",
        "boundary_tolerance_in": f"{BOUNDARY_TOL_IN:.1e}",
        "boundary_all_members_pass": R["boundary_all_pass"],
        "interior_classification": "CONSTRUCTED_ADMISSIBLE_SURFACE",
        "member_promoted": "none (family intentionally non-unique)",
        "saddle_present_any_member": R["saddle_any"],
        "grid_refinement_rel_delta": f"{R['refine']['rel_delta']:.2e}",
        "final_disposition": R["disp"],
    }
    GA.wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004N_CORRECTED_BACK_SURFACE_FAMILY",
        "parent_commit": GA.git_sha(),
        "script": "scripts/experiments/d28_rerun004n_corrected_back_surface_family.py",
        "command": "python scripts/experiments/d28_rerun004n_corrected_back_surface_family.py --write",
        "committed_inputs": [
            {"path": "docs/experiments/results/D28_65260_REGISTERED_RIM_004M.csv",
             "role": "CORRECTED_RIM_BOUNDARY", "sha256": GA.sha256(M_RIM_CSV)},
            {"path": "docs/experiments/results/D28_65260_BACK_BRACE_POSITIONS_004F.csv",
             "role": "BRACE_POSITIONS", "sha256": GA.sha256(F_POSITIONS_CSV)},
        ],
        "reuses_004eg_modules": "004E (z_TPS, grid, curvature) + 004G (family/Phi/volume) driven "
                                "from the corrected 004M rim",
        "boundary_residual": "GENUINE (e_i = z_surface - z_rim); replaces the 004G forced-zero",
        "output_paths": [os.path.basename(p) for p in (
            FAMILY_CSV, AUTHORITY_JSON, RESIDUAL_CSV, BRACE_CSV, VOLUME_CSV, SUMMARY_CSV,
            PROVENANCE_JSON)],
        "no_new_single_surface_promoted": True,
        "distinguishes_extracted_from_constructed": True,
        "runtime_pdf_access": False,
        "no_production_changes": True,
        "no_prior_run_alteration": True,
        "pdf_vendored": False,
        "disposition": R["disp"],
    }
    GA.write_provenance_json(PROVENANCE_JSON, rec)


# =============================================================================
# Report
# =============================================================================

def build_section(R: Dict) -> str:
    L: List[str] = []
    w = L.append
    ms = R["members"]
    vols_L = [m["volume_in3"] * IN3_TO_CM3 / 1000 for m in ms]
    w("## Run 004N — Corrected Back Surface Family")
    w("")
    w(f"- Repository SHA tested: `{GA.git_sha()}`")
    w("- Rebuilds the bounded back-surface family from the **corrected 004M rim**, classifies the "
      "interior as **CONSTRUCTED** (not a recovered historical back), and replaces the 004G "
      "forced-zero boundary check with a **genuine rim-boundary residual**.")
    w("- Artifacts: `D28_65260_BACK_SURFACE_FAMILY_004N.csv`, `D28_65260_BACK_SURFACE_AUTHORITY_004N.json`, "
      "`D28_65260_BACK_BOUNDARY_RESIDUAL_004N.csv`, `D28_65260_BACK_BRACE_SAMPLING_004N.csv`, "
      "`D28_65260_BODY_VOLUME_ENVELOPE_004N.csv`, `D28_65260_RERUN_004N_SUMMARY.csv`, "
      "`D28_65260_RERUN_004N_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### Genuine rim-boundary residual (replaces the 004G forced zero)")
    w("")
    w(f"- `e_i = z_surface(x_i, y_i) - z_rim(x_i, y_i)` evaluated at "
      f"{ms[0]['resid']['n_samples']} actual rim-boundary samples, for **every** member.")
    w(f"- Max |e| across the family = **{R['max_boundary_abs']:.2e} in** (tolerance "
      f"{BOUNDARY_TOL_IN} in) → **{'PASS' if R['boundary_all_pass'] else 'FAIL'}**. The boundary-exact "
      "TPS and the zero-on-rim Φ are confirmed by evaluation, not asserted by multiplying by zero.")
    w("")
    w("### Constructed back-surface family (5 members)")
    w("")
    w("| member | α (in) | max rise (mm) | body volume (L) | saddle | boundary max|e| (in) | class |")
    w("|---|---:|---:|---:|:--:|---:|---|")
    for m, vL in zip(ms, vols_L):
        w(f"| {m['name']} | {m['alpha']:.4f} | {m['h_max_mm']:.2f} | {vL:.3f} | "
          f"{'yes' if m['curv']['saddle'] else 'no'} | {m['resid']['max_abs']:.1e} | "
          f"`{m['classification']}` |")
    w("")
    w(f"- Interior-rise envelope **[{ms[0]['h_max_mm']:.2f}, {ms[-1]['h_max_mm']:.2f}] mm**; body "
      f"volume **[{vols_L[0]:.3f}, {vols_L[-1]:.3f}] L** (flat-top reference, "
      "`GEOMETRIC_REFERENCE_ONLY`; top dome UNRESOLVED).")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Runs 001–004J (incl. 004G) are untouched. 004N promotes no single surface, claims no "
      "historical radius, and labels every member CONSTRUCTED_ADMISSIBLE_SURFACE.")
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
    elif "<!-- RERUN004M_START -->" in text:
        marker = "<!-- RERUN004M_START -->"
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
        write_family(R); write_residual(R); write_brace(R); write_volume(R)
        write_authority(R); write_summary(R); write_provenance(R)
        splice_doc(section)
        print(f"wrote 004N artifacts; disposition={R['disp']}; "
              f"boundary_max_abs={R['max_boundary_abs']:.2e} in; "
              f"vol=[{R['members'][0]['volume_in3']*IN3_TO_CM3/1000:.3f},"
              f"{R['members'][-1]['volume_in3']*IN3_TO_CM3/1000:.3f}]L")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; boundary_max_abs={R['max_boundary_abs']:.2e}; "
              f"members={[m['name'] for m in R['members']]}]")


if __name__ == "__main__":
    main()
