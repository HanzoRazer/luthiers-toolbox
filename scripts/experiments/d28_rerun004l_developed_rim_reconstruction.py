#!/usr/bin/env python3
"""
D28 RUN 004L — Developed Rim Reconstruction
===========================================

Determines the actual developed ONE-SIDE rim distance for #65260 from the
source-derived plan outline, rather than using 30.4375 in (the internal
block-to-block dimension, 004K) as a proxy.

Method (Decision 3 — independent derivation):
    ds_i = sqrt((x_{i+1}-x_i)^2 + (y_{i+1}-y_i)^2)      (Euclidean polyline step)
    S_j  = sum_{i<j} ds_i                                (cumulative arc length)
    S_developed_rim = S[-1]   on the RAW committed Arnold/JD one-side outline.

The raw polyline arc length is the working developed-rim authority. The legacy
boxcar-smoothed value (~26.73 in) is reproduced ONLY to flag it as an endpoint
artifact (NOT authority). 30.4375 in (internal block-to-block) is NOT used.

Gate: the extracted-outline longitudinal extent must reconcile with the CAD
outside body-profile length (20.21875 in, 004K) within an explicitly stated
tolerance. If it cannot, STOP (do not rescale silently).

Input authority: the already committed D28_65260_ARNOLD_OUTLINE.csv (1,993
points). The PDF is not retraced. No production/spec/authority edits; no PDF;
experiment branch only.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from typing import Dict, List

import numpy as np
from scipy.signal import find_peaks

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
K04 = _load("d28_004k_for_l", "d28_rerun004k_source_datum_reconciliation.py")

_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Input (committed, read-only) --------------------------------------------
OUTLINE_CSV = GA.ARNOLD_OUTLINE_CSV

# --- Outputs (004L only) -----------------------------------------------------
RIM_CSV = os.path.join(_OUTDIR, "D28_65260_DEVELOPED_RIM_004L.csv")
ARCLEN_CSV = os.path.join(_OUTDIR, "D28_65260_RIM_ARCLENGTH_004L.csv")
LANDMARKS_CSV = os.path.join(_OUTDIR, "D28_65260_RIM_LANDMARKS_004L.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004L_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004L_PROVENANCE.json")

_S, _E = "<!-- RERUN004L_START -->", "<!-- RERUN004L_END -->"

# Datum values from 004K (single source of truth; not re-derived here).
CAD_OUTSIDE_BODY_LENGTH_IN = K04.OUTSIDE_BODY_LENGTH_IN          # 20.21875
INTERNAL_BLOCK_TO_BLOCK_IN = K04.INTERNAL_BLOCK_TO_BLOCK_LENGTH_IN  # 30.4375

# Explicit reconciliation tolerance for the CAD body-length cross-check.
BODY_LENGTH_TOL_PCT = 2.5


def identify_landmarks(y: np.ndarray, x_raw: np.ndarray, s_raw: np.ndarray,
                       s_sm: np.ndarray) -> Dict:
    """Detect waist / upper-bout / lower-bout longitudinal positions on the smoothed
    half-width (consistent with Runs 003/004C/004D); XY/arc taken from the RAW outline.
    Pure plan geometry — the waist radius (4.4375 in) is NOT used (Decision 4)."""
    x_s = GA.boxcar_half_width(x_raw)
    A_raw, A_sm = float(s_raw[-1]), float(s_sm[-1])
    lb_i = int(np.argmax(x_s))
    peaks, _ = find_peaks(x_s[:lb_i + 1], prominence=0.03)
    peaks = [p for p in peaks if 0.05 * y.max() < y[p] < 0.5 * y.max()]
    ub_i = int(peaks[int(np.argmax(x_s[peaks]))]) if peaks else int(
        np.argmax(np.where(y < 0.28 * y.max(), x_s, -1)))
    wi = ub_i + int(np.argmin(x_s[ub_i:lb_i + 1]))

    def pack(name, i):
        return {"landmark": name, "y_in": float(y[i]), "half_width_in": float(x_raw[i]),
                "plan_arc_raw_in": float(s_raw[i]), "plan_frac_raw": float(s_raw[i] / A_raw),
                "plan_arc_sm_in": float(s_sm[i]), "plan_frac_sm": float(s_sm[i] / A_sm)}

    return {"neck": pack("neck", 0), "upper_bout": pack("upper_bout", ub_i),
            "waist": pack("waist", wi), "lower_bout": pack("lower_bout", lb_i),
            "tail": pack("tail", len(y) - 1)}


def run_all() -> Dict:
    outline = GA.load_arnold_outline(OUTLINE_CSV)
    y, x = outline["y"], outline["x"]
    s_raw = GA.compute_polyline_arclength(y, x)
    x_s = GA.boxcar_half_width(x)
    s_sm = GA.compute_polyline_arclength(y, x_s)

    developed_rim_raw = float(s_raw[-1])
    developed_rim_sm = float(s_sm[-1])
    smoothing_inflation = developed_rim_sm - developed_rim_raw
    smoothing_inflation_pct = 100.0 * smoothing_inflation / developed_rim_raw

    outline_long_extent = float(outline["L"])     # y[-1]: traced longitudinal body length
    body_abs_err = abs(outline_long_extent - CAD_OUTSIDE_BODY_LENGTH_IN)
    body_pct_err = 100.0 * body_abs_err / CAD_OUTSIDE_BODY_LENGTH_IN
    reconciled = body_pct_err <= BODY_LENGTH_TOL_PCT

    landmarks = identify_landmarks(y, x, s_raw, s_sm)

    developed_ne_internal = abs(developed_rim_raw - INTERNAL_BLOCK_TO_BLOCK_IN) > 1e-6
    developed_ne_outside = abs(developed_rim_raw - CAD_OUTSIDE_BODY_LENGTH_IN) > 1e-6

    if not reconciled:
        disp = "DEVELOPED_RIM_SCALE_UNRECONCILED"
        notes = [f"STOP: outline longitudinal extent {outline_long_extent:.4f} in vs CAD "
                 f"{CAD_OUTSIDE_BODY_LENGTH_IN} in differs by {body_pct_err:.2f}% "
                 f"(> {BODY_LENGTH_TOL_PCT}% tolerance). Not rescaled silently."]
    else:
        disp = "DEVELOPED_RIM_RECONSTRUCTED"
        notes = [
            f"Developed one-side rim length = raw polyline arc length "
            f"**{developed_rim_raw:.4f} in**, derived independently from the committed "
            f"Arnold/JD outline ({len(y)} points) — NOT 30.4375 in.",
            f"Legacy boxcar-smoothed value {developed_rim_sm:.4f} in is inflated by "
            f"{smoothing_inflation:.4f} in ({smoothing_inflation_pct:.2f}%) via a mode='same' "
            f"endpoint artifact; retained as DIAGNOSTIC_ONLY, never authority.",
            f"CAD body-length cross-check PASSED: traced extent {outline_long_extent:.4f} in vs "
            f"CAD {CAD_OUTSIDE_BODY_LENGTH_IN} in = {body_pct_err:.2f}% (<= {BODY_LENGTH_TOL_PCT}%).",
            f"Three lengths remain distinct: developed rim {developed_rim_raw:.4f} != internal "
            f"block-to-block {INTERNAL_BLOCK_TO_BLOCK_IN} != CAD outside {CAD_OUTSIDE_BODY_LENGTH_IN}.",
        ]
    return dict(outline=outline, s_raw=s_raw, s_sm=s_sm, x_s=x_s,
                developed_rim_raw=developed_rim_raw, developed_rim_sm=developed_rim_sm,
                smoothing_inflation=smoothing_inflation,
                smoothing_inflation_pct=smoothing_inflation_pct,
                outline_long_extent=outline_long_extent, body_abs_err=body_abs_err,
                body_pct_err=body_pct_err, reconciled=reconciled, landmarks=landmarks,
                developed_ne_internal=developed_ne_internal,
                developed_ne_outside=developed_ne_outside, disp=disp, notes=notes)


# =============================================================================
# Writers
# =============================================================================

def write_rim(R: Dict) -> None:
    rows = [
        {"quantity": "developed_rim_length_raw", "value_in": f"{R['developed_rim_raw']:.5f}",
         "method": "raw polyline Euclidean arc length of the one-side plan outline",
         "classification": "DEVELOPED_RIM_AUTHORITY (working)",
         "note": "the side ribbon unrolled flat = one-side plan perimeter; independent of 30.4375"},
        {"quantity": "developed_rim_length_smoothed_diag", "value_in": f"{R['developed_rim_sm']:.5f}",
         "method": "arc length of boxcar(mode='same')-smoothed half-width (003/004C legacy)",
         "classification": "DIAGNOSTIC_ONLY (endpoint-artifact inflated)",
         "note": f"inflated by {R['smoothing_inflation']:.4f} in vs raw; NOT authority"},
        {"quantity": "outline_longitudinal_extent", "value_in": f"{R['outline_long_extent']:.5f}",
         "method": "y[-1] of the committed Arnold/JD outline (neck y=0 to tail)",
         "classification": "DRAWING_DERIVED",
         "note": "traced body length; cross-checked against CAD outside body length"},
        {"quantity": "cad_outside_body_length", "value_in": f"{CAD_OUTSIDE_BODY_LENGTH_IN:.5f}",
         "method": "004K source datum (20 7/32 in)", "classification": "SOURCE_CAD_CONFIRMED",
         "note": "cross-check target for the traced extent"},
        {"quantity": "internal_block_to_block", "value_in": f"{INTERNAL_BLOCK_TO_BLOCK_IN:.5f}",
         "method": "004K source datum (30 7/16 in)", "classification": "SOURCE_PLAN_CORROBORATED",
         "note": "REFERENCE ONLY — NOT the developed rim; never equated to it"},
    ]
    GA.wr_csv(RIM_CSV, list(rows[0].keys()), rows)


def write_arclength(R: Dict) -> None:
    y, x = R["outline"]["y"], R["outline"]["x"]
    s_raw, s_sm, x_s = R["s_raw"], R["s_sm"], R["x_s"]
    A_raw = R["developed_rim_raw"]
    ds = np.concatenate([[0.0], np.hypot(np.diff(x), np.diff(y))])
    rows = []
    for i in range(len(y)):
        rows.append({
            "index": i, "y_in": f"{y[i]:.5f}", "half_width_in": f"{x[i]:.5f}",
            "half_width_smoothed_in": f"{x_s[i]:.5f}", "ds_in": f"{ds[i]:.6f}",
            "cumulative_arc_raw_in": f"{s_raw[i]:.5f}", "cumulative_arc_sm_in": f"{s_sm[i]:.5f}",
            "developed_fraction": f"{s_raw[i] / A_raw:.6f}",
        })
    GA.wr_csv(ARCLEN_CSV, list(rows[0].keys()), rows)


def write_landmarks(R: Dict) -> None:
    rows = []
    for key in ("neck", "upper_bout", "waist", "lower_bout", "tail"):
        lm = R["landmarks"][key]
        rows.append({
            "landmark": lm["landmark"], "y_in": f"{lm['y_in']:.5f}",
            "half_width_in": f"{lm['half_width_in']:.5f}",
            "plan_arc_raw_in": f"{lm['plan_arc_raw_in']:.5f}",
            "developed_fraction_raw": f"{lm['plan_frac_raw']:.6f}",
            "plan_arc_smoothed_diag_in": f"{lm['plan_arc_sm_in']:.5f}",
            "developed_fraction_smoothed_diag": f"{lm['plan_frac_sm']:.6f}",
            "basis": "plan outline geometry (waist = half-width minimum); waist RADIUS not used",
        })
    GA.wr_csv(LANDMARKS_CSV, list(rows[0].keys()), rows)


def write_summary(R: Dict) -> None:
    row = {
        "disposition": R["disp"],
        "developed_rim_length_raw_in": f"{R['developed_rim_raw']:.5f}",
        "developed_rim_length_smoothed_diag_in": f"{R['developed_rim_sm']:.5f}",
        "smoothing_inflation_in": f"{R['smoothing_inflation']:.5f}",
        "smoothing_inflation_pct": f"{R['smoothing_inflation_pct']:.3f}",
        "outline_longitudinal_extent_in": f"{R['outline_long_extent']:.5f}",
        "cad_outside_body_length_in": f"{CAD_OUTSIDE_BODY_LENGTH_IN:.5f}",
        "body_length_abs_err_in": f"{R['body_abs_err']:.5f}",
        "body_length_pct_err": f"{R['body_pct_err']:.3f}",
        "body_length_tolerance_pct": f"{BODY_LENGTH_TOL_PCT:.2f}",
        "body_length_reconciled": R["reconciled"],
        "internal_block_to_block_in": f"{INTERNAL_BLOCK_TO_BLOCK_IN:.5f}",
        "developed_rim_ne_internal": R["developed_ne_internal"],
        "developed_rim_ne_cad_outside": R["developed_ne_outside"],
        "n_outline_points": len(R["outline"]["y"]),
        "final_disposition": R["disp"],
    }
    GA.wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004L_DEVELOPED_RIM_RECONSTRUCTION",
        "parent_commit": GA.git_sha(),
        "script": "scripts/experiments/d28_rerun004l_developed_rim_reconstruction.py",
        "command": "python scripts/experiments/d28_rerun004l_developed_rim_reconstruction.py --write",
        "source_artifacts": [
            {"path": "docs/experiments/results/D28_65260_ARNOLD_OUTLINE.csv",
             "role": "PLAN_OUTLINE_XY_AUTHORITY (not retraced)",
             "classification": "VERIFIED_DRAWING_DERIVED", "sha256": GA.sha256(OUTLINE_CSV)},
        ],
        "reuses_004k_datums": "developed rim derived independently; 30.4375 used only as a labelled "
                              "reference, never as the developed length",
        "arclength_method": "raw Euclidean polyline cumulative arc length; smoothed value is diagnostic only",
        "cad_body_length_tolerance_pct": BODY_LENGTH_TOL_PCT,
        "output_paths": [os.path.basename(p) for p in (
            RIM_CSV, ARCLEN_CSV, LANDMARKS_CSV, SUMMARY_CSV, PROVENANCE_JSON)],
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
    w("## Run 004L — Developed Rim Reconstruction")
    w("")
    w(f"- Repository SHA tested: `{GA.git_sha()}`")
    w("- Determines the actual developed **one-side rim** distance for #65260 from the committed "
      "source-derived plan outline, **not** from 30.4375 in (the internal block-to-block dimension, "
      "004K). The developed rim is the side ribbon unrolled flat = the one-side plan-perimeter arc "
      "length.")
    w("- Artifacts: `D28_65260_DEVELOPED_RIM_004L.csv`, `D28_65260_RIM_ARCLENGTH_004L.csv`, "
      "`D28_65260_RIM_LANDMARKS_004L.csv`, `D28_65260_RERUN_004L_SUMMARY.csv`, "
      "`D28_65260_RERUN_004L_PROVENANCE.json`. Input: `D28_65260_ARNOLD_OUTLINE.csv` (not retraced). "
      "No PDF vendored.")
    w("")
    w("### Independent developed-rim derivation")
    w("")
    w(f"- **Raw polyline arc length `S = {R['developed_rim_raw']:.4f} in`** (working developed-rim "
      f"authority), from `ds_i = √((Δx)²+(Δy)²)`, `S = Σ ds_i` over {len(R['outline']['y'])} outline "
      "points.")
    w(f"- Smoothed diagnostic `{R['developed_rim_sm']:.4f} in` (boxcar `mode='same'`) is inflated by "
      f"**{R['smoothing_inflation']:.4f} in ({R['smoothing_inflation_pct']:.2f}%)** by an endpoint "
      "artifact — `DIAGNOSTIC_ONLY`, never authority. (This is the legacy ≈26.73 in value.)")
    w("")
    w("### CAD body-length cross-check (gate)")
    w("")
    w(f"- Traced outline longitudinal extent **{R['outline_long_extent']:.4f} in** vs CAD outside "
      f"body length **{CAD_OUTSIDE_BODY_LENGTH_IN} in**: Δ = {R['body_abs_err']:.4f} in "
      f"(**{R['body_pct_err']:.2f}%**), tolerance **{BODY_LENGTH_TOL_PCT}%** → "
      f"**{'RECONCILED' if R['reconciled'] else 'UNRECONCILED (STOP)'}**. No silent rescaling.")
    w("")
    w("### Three distinct lengths")
    w("")
    w(f"- developed rim `{R['developed_rim_raw']:.4f} in` ≠ internal block-to-block "
      f"`{INTERNAL_BLOCK_TO_BLOCK_IN} in` ≠ CAD outside `{CAD_OUTSIDE_BODY_LENGTH_IN} in` — no "
      "equality asserted (Decision 3).")
    w("")
    w("### Outline landmarks (plan geometry; waist radius not used)")
    w("")
    w("| landmark | y (in) | half-width (in) | plan arc raw (in) | developed fraction |")
    w("|---|---:|---:|---:|---:|")
    for key in ("neck", "upper_bout", "waist", "lower_bout", "tail"):
        lm = R["landmarks"][key]
        w(f"| {lm['landmark']} | {lm['y_in']:.3f} | {lm['half_width_in']:.3f} | "
          f"{lm['plan_arc_raw_in']:.3f} | {lm['plan_frac_raw']:.4f} |")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Runs 001–004J are untouched. 004L retraces no PDF, derives the rim independently of 30.4375, "
      "and changes no prior artifact or production file.")
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
    elif "<!-- RERUN004K_START -->" in text:
        marker = "<!-- RERUN004K_START -->"
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
        write_rim(R)
        write_arclength(R)
        write_landmarks(R)
        write_summary(R)
        write_provenance(R)
        splice_doc(section)
        print(f"wrote 004L artifacts; disposition={R['disp']}; "
              f"developed_rim_raw={R['developed_rim_raw']:.4f} in; "
              f"body_length_err={R['body_pct_err']:.2f}%")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; developed_rim_raw={R['developed_rim_raw']:.4f}; "
              f"smoothed_diag={R['developed_rim_sm']:.4f}; body_err={R['body_pct_err']:.2f}%]")


if __name__ == "__main__":
    main()
