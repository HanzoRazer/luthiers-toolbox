#!/usr/bin/env python3
"""
D28 RUN 004F — Back-Arch Authority Recovery
===========================================

Purpose: NOT to generate another back surface, but to determine whether the
historical/source record contains enough additional #65260-specific INTERIOR
evidence to reduce the back-arch non-uniqueness established by Run 004E
(a ~2.6 mm interior divergence between admissible surfaces spanning the same rim).

Governing question:
    Is there enough #65260-specific interior authority to distinguish among the
    admissible back-surface families from 004E?

Primary #65260 source audited: the John Arnold construction drawing
`1937 D-28 #65260` (raster scan `1937_D-28_fb03.pdf`, NOT vendored; SHA-256
recorded). The JD `ACOUSTIC BODY` reconstruction is a TOP-plan trace only (no
back-arch authority). GenOne / A003 are generic (non-#65260) references.

What the Arnold drawing yields (recovered interior authority):
  * Back-brace cross-section dimensions (explicit table)      -> SOURCE_MEASURED
  * Back-brace LONGITUDINAL positions (bars drawn on the body) -> DRAWING_DERIVED
        (pixel-calibrated from the raster scan, with stated uncertainty)
  * Back-brace scallop/peak annotations (profile values)       -> SOURCE_MEASURED
        (preserved as source values; NOT reinterpreted as back-arch rise)

What is explicitly ABSENT (the missing interior-arch magnitude):
  * No explicit back radius / dome-rise notation
  * No back-brace side cross-section (brace-bottom curvature NOT dimensioned)
  * No centerline / back-depth arch datum

Conclusion (expected): BACK_ARCH_AUTHORITY_PARTIAL. The recovered brace authority
INCREASES interior structural authority but does NOT directly constrain the arch
magnitude unless brace-bottom curvature or another interior geometric datum is
available. The 004E admissible arch family is therefore preserved (bounded), not
collapsed. No new back surface is generated. No production/spec edit; prior runs
001-004E preserved unchanged. No PDF vendored.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

# Input dir is always the real committed results (read-only). Output dir and the
# report doc are overridable (env) so the test suite can run --write hermetically
# into a tmp dir without dirtying committed artifacts (see 004-series harness).
_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Inputs (committed, read-only; the 004E envelope is sourced from here) ----
E_SUMMARY_CSV = os.path.join(_RESULTS, "D28_65260_RERUN_004E_SUMMARY.csv")
E_CANDIDATES_CSV = os.path.join(_RESULTS, "D28_65260_BACK_SURFACE_CANDIDATES_004E.csv")

# --- Outputs (004F only; _OUTDIR == _RESULTS unless overridden for tests) -----
AUTHORITY_JSON = os.path.join(_OUTDIR, "D28_65260_BACK_ARCH_AUTHORITY_004F.json")
POSITIONS_CSV = os.path.join(_OUTDIR, "D28_65260_BACK_BRACE_POSITIONS_004F.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004F_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004F_PROVENANCE.json")

_S, _E = "<!-- RERUN004F_START -->", "<!-- RERUN004F_END -->"

# =============================================================================
# Source provenance (PDFs NOT vendored; SHA-256 recorded). SHAs are hardcoded so
# 004F is reproducible WITHOUT the external uploads (CI-safe).
# =============================================================================
ARNOLD_PDF_NAME = "1937_D-28_fb03.pdf"
ARNOLD_PDF_SHA256 = "d6e7a994b19b5590b6706541e5ff35f8a574361e42a578812da2b0b689d4d75d"
JD_TRACE_NAME = "ACOUSTIC_BODY (A0001)"
JD_TRACE_SHA256 = "de56210225695e645f3a1e3a61c3e490fd80967ebe301079e78f14d44bf46647"

# =============================================================================
# Raster-scan calibration (deterministic; committed pixel reads).
# Arnold scan rendered to grayscale at Z=4 (4 px/pt). The soundhole (Ø4.0 in) is
# the scale+origin anchor; its center is placed at the datum-A longitudinal
# position recovered in Run 003 (y_from_neck = 5.896 in). y increases toward the
# tail. Scale cross-validated: BB3/BB4 drawn bar widths match the table (.755/.760).
# =============================================================================
RENDER_Z = 4
SOUNDHOLE_CENTER_PX = 4900.0          # x of soundhole center (longitudinal axis)
SOUNDHOLE_RADIUS_PX = 573.0           # => Ø4.0 in
PX_PER_IN = SOUNDHOLE_RADIUS_PX / 2.0  # 286.5 px/in
SOUNDHOLE_Y_FROM_NECK_IN = 5.896      # Run 003 datum-A soundhole center (cross-source anchor)
BODY_LENGTH_IN = 19.99                # Run 003 extracted body length (context only)
POSITION_UNCERTAINTY_IN = 0.4         # calibration + reading + scan distortion (conservative)

# Manually read brace-bar CENTER x (dark-mask px at Z=4). Edge-pair reads for the
# wide braces (BB3/BB4) matched the table widths, validating scale.
BRACE_CENTER_PX = {"BB1": 5405.0, "BB2": 4480.0, "BB3": 3503.0, "BB4": 2361.0}

# Back-brace cross-section dimensions, read directly from the Arnold drawing's
# "BACK BRACE DIMENSIONS" table (SOURCE_MEASURED). width_in x depth_in.
BRACE_DIMS = {
    "BB1": {"width_in": 0.320, "depth_in": 0.615},
    "BB2": {"width_in": 0.320, "depth_in": 0.615},
    "BB3": {"width_in": 0.755, "depth_in": 0.385},
    "BB4": {"width_in": 0.760, "depth_in": 0.375},
}
# Qualitative region label on the production spec, for cross-check ONLY.
SPEC_REGION = {"BB1": "upper bout", "BB2": "above waist",
               "BB3": "below waist", "BB4": "lower bout"}
# Legacy production-spec values (martin_d28_1937.json) that the Arnold drawing
# CORRECTS. Recorded as findings; production is NOT edited (read-only), and 004E
# (which used the legacy values) is NOT retroactively altered.
SPEC_LEGACY_DIMS = {
    "BB1": {"width_in": 0.320, "depth_in": 0.450},
    "BB2": {"width_in": 0.320, "depth_in": 0.450},
    "BB3": {"width_in": 0.735, "depth_in": 0.385},
    "BB4": {"width_in": 0.760, "depth_in": 0.375},
}

# Scallop/"MAX"/"PEAK" profile annotations OBSERVED near the braces on the Arnold
# drawing. Preserved as source-observed values; NOT reinterpreted as back-arch
# rise, and NOT force-assigned per brace (the raster scan does not unambiguously
# resolve which annotation belongs to which brace, or scallop-peak vs full-height).
OBSERVED_PROFILE_ANNOTATIONS_IN = [0.255, 0.515, 0.545, 0.550, 0.625, 0.630]

# Interior arch datums searched for and NOT found on any #65260 source.
ABSENT_INTERIOR_DATUMS = [
    "explicit back radius / spherical-dish notation",
    "back dome-rise / arch-height dimension",
    "back-brace side cross-section (brace-bottom curvature)",
    "centerline back-depth / arch datum",
]


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       cwd=_REPO_ROOT).decode().strip()
    except Exception:
        return "UNKNOWN"


# =============================================================================
# Calibration + loaders
# =============================================================================

def y_from_neck_in(center_px: float) -> float:
    """Longitudinal position (in) from the neck, from a dark-mask x (px).
    y increases toward the tail (decreasing x)."""
    return SOUNDHOLE_Y_FROM_NECK_IN + (SOUNDHOLE_CENTER_PX - center_px) / PX_PER_IN


def recover_brace_positions() -> List[Dict]:
    out = []
    for bb in ("BB1", "BB2", "BB3", "BB4"):
        y = y_from_neck_in(BRACE_CENTER_PX[bb])
        out.append({
            "brace_id": bb,
            "center_px": BRACE_CENTER_PX[bb],
            "y_from_neck_in": y,
            "uncertainty_in": POSITION_UNCERTAINTY_IN,
            "width_in": BRACE_DIMS[bb]["width_in"],
            "depth_in": BRACE_DIMS[bb]["depth_in"],
            "spec_region": SPEC_REGION[bb],
            "position_class": "DRAWING_DERIVED",
            "dims_class": "SOURCE_MEASURED",
        })
    return out


def spec_discrepancies() -> List[Dict]:
    out = []
    for bb in ("BB1", "BB2", "BB3", "BB4"):
        drawing = BRACE_DIMS[bb]
        legacy = SPEC_LEGACY_DIMS[bb]
        for field in ("width_in", "depth_in"):
            if abs(drawing[field] - legacy[field]) > 1e-9:
                out.append({
                    "brace_id": bb, "field": field,
                    "arnold_drawing_in": drawing[field], "legacy_repo_in": legacy[field],
                    "delta_in": round(drawing[field] - legacy[field], 4),
                    "authority": "SOURCE_MEASURED (Arnold drawing) corrects LEGACY_REPO_ASSIGNMENT",
                    "action": "recorded only; production spec NOT edited; 004E NOT altered",
                })
    return out


def load_004e_envelope() -> Dict:
    """Read the admissible back-arch family envelope from committed 004E artifacts."""
    cand = {}
    with open(E_CANDIDATES_CSV) as fh:
        for r in csv.DictReader(fh):
            cand[r["model_name"]] = r
    summ = next(csv.DictReader(open(E_SUMMARY_CSV)))

    def f(x):
        return float(x) if x not in ("", None) else None
    tps = f(cand["constrained_tps"]["center_rise_mm"])
    sph = f(cand["single_sphere"]["center_rise_mm"])
    lo, hi = sorted([tps, sph])
    return {
        "tps_center_rise_mm": tps,
        "sphere_center_rise_mm": sph,
        "sphere_R_ft": f(cand["single_sphere"]["radius_ft"]),
        "interior_divergence_mm": f(summ["interior_sphere_vs_tps_max_div_mm"]),
        "lower_bout_rise_mm": f(summ["lower_bout_center_rise_mm"]),
        "family_center_rise_mm_range": [lo, hi],
        "parent_disposition": summ["final_disposition"],
    }


# =============================================================================
# Orchestration
# =============================================================================

def run_all() -> Dict:
    positions = recover_brace_positions()
    discreps = spec_discrepancies()
    env = load_004e_envelope()

    recovered = {
        "back_brace_cross_sections": "SOURCE_MEASURED (Arnold table)",
        "back_brace_longitudinal_positions": "DRAWING_DERIVED (raster-calibrated, ±%.1f in)" % POSITION_UNCERTAINTY_IN,
        "back_brace_scallop_annotations": "SOURCE_MEASURED (profile values; NOT arch rise)",
    }

    # Governing question: a DIRECT interior-arch datum is required to collapse the
    # 004E family. None exists. Brace positions/dims increase structural authority
    # but do not directly constrain arch magnitude.
    has_direct_arch_datum = False
    has_new_interior_authority = True  # positions + corrected cross-sections

    if has_direct_arch_datum:
        disp = "BACK_ARCH_AUTHORITY_RECOVERED"
    elif has_new_interior_authority:
        disp = "BACK_ARCH_AUTHORITY_PARTIAL"
    else:
        disp = "BACK_ARCH_AUTHORITY_ABSENT"

    notes = [
        "Recovered #65260-specific back authority: BB1-BB4 cross-section dimensions "
        "(SOURCE_MEASURED) and longitudinal positions (DRAWING_DERIVED, ±%.1f in)." % POSITION_UNCERTAINTY_IN,
        "No direct interior-arch datum found on any #65260 source: " + "; ".join(ABSENT_INTERIOR_DATUMS) + ".",
        "The recovered brace positions INCREASE interior structural authority but do NOT "
        "directly constrain arch magnitude unless brace-bottom curvature or another interior "
        "geometric datum is available.",
        "The 004E admissible back-arch family is preserved (bounded), not collapsed: center-rise "
        "envelope ~[%.2f, %.2f] mm across candidates; interior divergence ~%.2f mm. No new back "
        "surface generated." % (env["family_center_rise_mm_range"][0],
                                env["family_center_rise_mm_range"][1],
                                env["interior_divergence_mm"]),
    ]
    return dict(positions=positions, discreps=discreps, env=env, recovered=recovered,
                disp=disp, notes=notes)


# =============================================================================
# Writers
# =============================================================================

def _wr_csv(path: str, fields: List[str], rows: List[Dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_positions(R: Dict) -> None:
    rows = []
    for p in R["positions"]:
        rows.append({
            "brace_id": p["brace_id"],
            "y_from_neck_in": f"{p['y_from_neck_in']:.3f}",
            "uncertainty_in": f"{p['uncertainty_in']:.2f}",
            "center_px_z4": f"{p['center_px']:.0f}",
            "width_in": f"{p['width_in']:.3f}",
            "depth_in": f"{p['depth_in']:.3f}",
            "spec_region_crosscheck": p["spec_region"],
            "position_class": p["position_class"],
            "dims_class": p["dims_class"],
        })
    _wr_csv(POSITIONS_CSV, list(rows[0].keys()), rows)


def write_authority(R: Dict) -> None:
    env = R["env"]
    rec = {
        "experiment": "D28_RUN_004F_BACK_ARCH_AUTHORITY_RECOVERY",
        "governing_question": ("Is there enough #65260-specific interior authority to "
                               "distinguish among the admissible back-surface families from 004E?"),
        "answer": R["disp"],
        "sources": {
            "arnold_drawing": {"name": ARNOLD_PDF_NAME, "sha256": ARNOLD_PDF_SHA256,
                               "role": "PRIMARY #65260 interior source", "vendored": False},
            "jd_acoustic_body_reconstruction": {"name": JD_TRACE_NAME, "sha256": JD_TRACE_SHA256,
                                                "role": "TOP-PLAN authority only; NO back-arch authority",
                                                "vendored": False},
            "genone_a003": {"role": "generic (non-#65260) reference only; not used as authority"},
        },
        "recovered_authority": R["recovered"],
        "back_brace_cross_sections_in": {k: BRACE_DIMS[k] for k in ("BB1", "BB2", "BB3", "BB4")},
        "back_brace_cross_sections_class": "SOURCE_MEASURED",
        "back_brace_longitudinal_positions": [
            {"brace_id": p["brace_id"], "y_from_neck_in": round(p["y_from_neck_in"], 3),
             "uncertainty_in": p["uncertainty_in"], "class": "DRAWING_DERIVED"}
            for p in R["positions"]],
        "scallop_profile_annotations_in": OBSERVED_PROFILE_ANNOTATIONS_IN,
        "scallop_profile_note": ("preserved as source-observed brace-profile values; NOT "
                                 "reinterpreted as back-arch rise; per-brace assignment not "
                                 "resolved from the raster scan"),
        "absent_interior_arch_datums": ABSENT_INTERIOR_DATUMS,
        "calibration": {
            "method": "soundhole Ø4.0 in = scale+origin anchor on the raster scan",
            "px_per_in": PX_PER_IN, "render_zoom": RENDER_Z,
            "soundhole_center_px": SOUNDHOLE_CENTER_PX,
            "soundhole_y_from_neck_in": SOUNDHOLE_Y_FROM_NECK_IN,
            "cross_source_assumption": ("soundhole longitudinal position taken from the Run 003 "
                                        "datum-A extraction (JD trace); absorbed in the stated uncertainty"),
            "scale_validation": "BB3/BB4 drawn bar widths match table widths (.755/.760) within ~3%",
            "position_uncertainty_in": POSITION_UNCERTAINTY_IN,
        },
        "spec_discrepancies": R["discreps"],
        "e004_admissible_family": env,
        "constraints": [
            "no new back surface generated (004F is authority recovery only)",
            "production spec NOT edited (read-only); 004E NOT retroactively altered",
            "no PDF vendored (geometry/measurements + SHA-256 + provenance only)",
        ],
        "disposition": R["disp"],
    }
    os.makedirs(os.path.dirname(AUTHORITY_JSON), exist_ok=True)
    with open(AUTHORITY_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


def write_summary(R: Dict) -> None:
    env = R["env"]
    p = {x["brace_id"]: x for x in R["positions"]}
    row = {
        "governing_answer": R["disp"],
        "recovered_back_brace_positions": "yes (DRAWING_DERIVED, +/-%.1f in)" % POSITION_UNCERTAINTY_IN,
        "recovered_cross_sections": "yes (SOURCE_MEASURED)",
        "BB1_y_from_neck_in": f"{p['BB1']['y_from_neck_in']:.3f}",
        "BB2_y_from_neck_in": f"{p['BB2']['y_from_neck_in']:.3f}",
        "BB3_y_from_neck_in": f"{p['BB3']['y_from_neck_in']:.3f}",
        "BB4_y_from_neck_in": f"{p['BB4']['y_from_neck_in']:.3f}",
        "position_uncertainty_in": f"{POSITION_UNCERTAINTY_IN:.2f}",
        "direct_arch_datum_found": "no",
        "absent_datums": "; ".join(ABSENT_INTERIOR_DATUMS),
        "spec_corrections": "; ".join(f"{d['brace_id']}.{d['field']} {d['legacy_repo_in']}->{d['arnold_drawing_in']}"
                                      for d in R["discreps"]),
        "e004_family_center_rise_mm": f"[{env['family_center_rise_mm_range'][0]:.2f}, {env['family_center_rise_mm_range'][1]:.2f}]",
        "e004_interior_divergence_mm": f"{env['interior_divergence_mm']:.2f}",
        "new_surface_generated": "no",
        "final_disposition": R["disp"],
    }
    _wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004F_BACK_ARCH_AUTHORITY_RECOVERY",
        "parent_commit": git_sha(),
        "script": "scripts/experiments/d28_rerun004f_back_arch_authority_recovery.py",
        "command": "python scripts/experiments/d28_rerun004f_back_arch_authority_recovery.py --write",
        "sources_not_vendored": [
            {"name": ARNOLD_PDF_NAME, "sha256": ARNOLD_PDF_SHA256,
             "role": "PRIMARY #65260 interior source (raster scan)"},
            {"name": JD_TRACE_NAME, "sha256": JD_TRACE_SHA256,
             "role": "TOP-PLAN reconstruction (no back authority)"},
        ],
        "committed_inputs": [
            {"path": "docs/experiments/results/D28_65260_RERUN_004E_SUMMARY.csv"},
            {"path": "docs/experiments/results/D28_65260_BACK_SURFACE_CANDIDATES_004E.csv"},
        ],
        "output_paths": [os.path.basename(p) for p in (
            AUTHORITY_JSON, POSITIONS_CSV, SUMMARY_CSV, PROVENANCE_JSON)],
        "pdf_vendored": False,
        "runtime_pdf_access": False,
        "no_new_surface_generated": True,
        "no_production_changes": True,
        "no_prior_run_alteration": True,
        "disposition": R["disp"],
    }
    os.makedirs(os.path.dirname(PROVENANCE_JSON), exist_ok=True)
    with open(PROVENANCE_JSON, "w") as fh:
        json.dump(rec, fh, indent=2)


# =============================================================================
# Report
# =============================================================================

def build_section(R: Dict) -> str:
    L: List[str] = []
    w = L.append
    env = R["env"]
    p = {x["brace_id"]: x for x in R["positions"]}

    w("## Run 004F — Back-Arch Authority Recovery")
    w("")
    w(f"- Repository SHA tested: `{git_sha()}`")
    w("- Purpose: **not** to generate another back surface, but to determine whether the "
      "source record holds enough #65260-specific **interior** evidence to reduce the 004E "
      "back-arch non-uniqueness (~2.6 mm interior divergence among admissible surfaces).")
    w("- Primary source audited: the **John Arnold** construction drawing `1937 D-28 #65260` "
      f"(raster scan, SHA-256 `{ARNOLD_PDF_SHA256[:16]}…`, **not vendored**). The JD "
      "`ACOUSTIC BODY` reconstruction is a **top-plan trace only** (no back-arch authority); "
      "GenOne/A003 are generic (non-#65260) references.")
    w("- Artifacts: `D28_65260_BACK_ARCH_AUTHORITY_004F.json`, "
      "`D28_65260_BACK_BRACE_POSITIONS_004F.csv`, `D28_65260_RERUN_004F_SUMMARY.csv`, "
      "`D28_65260_RERUN_004F_PROVENANCE.json`. No PDF vendored; no new surface generated.")
    w("")
    w("### Recovered #65260-specific interior authority")
    w("")
    w("- **Back-brace cross-section dimensions** (`SOURCE_MEASURED`, Arnold table): "
      "BB1 0.320×0.615, BB2 0.320×0.615, BB3 0.755×0.385, BB4 0.760×0.375 in (width×depth).")
    w("- **Back-brace longitudinal positions** (`DRAWING_DERIVED`, raster-calibrated via the "
      f"Ø4.0 in soundhole at {PX_PER_IN:.1f} px/in, ±{POSITION_UNCERTAINTY_IN:.1f} in; scale "
      "cross-validated by BB3/BB4 drawn widths matching the table):")
    w("")
    w("| brace | y from neck (in) | ± (in) | width×depth (in) | spec region (cross-check) |")
    w("|---|---:|---:|---|---|")
    for bb in ("BB1", "BB2", "BB3", "BB4"):
        w(f"| {bb} | {p[bb]['y_from_neck_in']:.2f} | {POSITION_UNCERTAINTY_IN:.1f} | "
          f"{BRACE_DIMS[bb]['width_in']:.3f}×{BRACE_DIMS[bb]['depth_in']:.3f} | {SPEC_REGION[bb]} |")
    w("")
    w("- **Scallop/profile annotations** observed near the braces are preserved as source "
      "values and are **not** reinterpreted as back-arch rise (per-brace assignment is not "
      "resolved from the raster scan).")
    w("")
    w("### Legacy-spec corrections (recorded, not applied)")
    w("")
    w("- The Arnold drawing corrects the production-spec back-brace values: "
      + "; ".join(f"**{d['brace_id']} {d['field'].replace('_in','')}** "
                 f"{d['legacy_repo_in']}→{d['arnold_drawing_in']} in" for d in R["discreps"])
      + ". Recorded as `SOURCE_MEASURED` correcting `LEGACY_REPO_ASSIGNMENT`; the production "
        "spec is **not** edited and Run 004E is **not** retroactively altered.")
    w("")
    w("### Interior-arch datums searched for and NOT found")
    w("")
    for d in ABSENT_INTERIOR_DATUMS:
        w(f"- {d}: **absent** on all #65260 sources.")
    w("")
    w("### Effect on the 004E non-uniqueness")
    w("")
    w(f"- 004E admissible back-arch family (center-rise envelope): "
      f"**~[{env['family_center_rise_mm_range'][0]:.2f}, {env['family_center_rise_mm_range'][1]:.2f}] mm** "
      f"(TPS {env['tps_center_rise_mm']:.2f} mm … {env['sphere_R_ft']:.1f} ft sphere "
      f"{env['sphere_center_rise_mm']:.2f} mm); interior divergence ~{env['interior_divergence_mm']:.2f} mm. "
      f"This family is **preserved (bounded), not collapsed**.")
    w("")
    w("### Mathematical result vs physical interpretation")
    w("")
    w("> The recovered back-brace positions and cross-sections **increase interior structural "
      "authority but do not directly constrain the back-arch magnitude** unless brace-bottom "
      "curvature or another interior geometric datum is available. The brace positions do **not** "
      "\"solve\" or \"determine\" the back arch. Absent a direct interior-arch datum, the admissible "
      "arch remains a bounded family rather than a unique historical reconstruction. See the "
      "program-level **Engineering Interpretation Principle** at the top of this document.")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Parent dispositions (001–004E) are untouched. 004F generates no back surface, edits no "
      "production/spec file, and alters no prior run.")
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
    elif "<!-- RERUN004E_START -->" in text:
        marker = "<!-- RERUN004E_START -->"
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
        write_authority(R)
        write_positions(R)
        write_summary(R)
        write_provenance(R)
        splice_doc(section)
        print(f"wrote 004F artifacts; disposition={R['disp']}")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; positions="
              + ", ".join(f"{x['brace_id']}={x['y_from_neck_in']:.2f}" for x in R["positions"]) + "]")


if __name__ == "__main__":
    main()
