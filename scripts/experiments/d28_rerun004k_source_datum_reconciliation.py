#!/usr/bin/env python3
"""
D28 RUN 004K — Source Datum Reconciliation
==========================================

Establishes the CORRECTED meaning, classification, provenance, and independence
of the major Arnold/CAD #65260 dimensions BEFORE any geometry is recalculated.
No reconstructed rim, back surface, or curvature in this run.

Two source dimensions were previously interpreted incorrectly and are now
reconciled:

    20 7/32 in = 20.21875 in   outside longitudinal body-profile length (CAD)
    30 7/16 in = 30.4375  in   internal head-block ↔ tail-block length (NOT the
                               developed rim; it is the Arnold side-height station
                               axis extent — bottom station = 30.4375)
     4 7/16 in = 4.4375   in   waist RADIUS (plan geometry) — NOT assembled depth
     4.220    in            Arnold waist SIDE HEIGHT (side-depth axis)

Superseded (must not propagate into any NEW calculation):

    30.4375 == developed side / rim length
    4.4375  == assembled body depth
    4.4375 - 4.220 == top + back plate thickness

Three lengths are kept strictly distinct (no equality without a geometric
derivation): L_outside (20.21875), L_internal block-to-block (30.4375), and
S_developed rim (derived independently in 004L; NULL here). Waist radius and
waist side height are unrelated geometric axes.

Preserves Runs 001–004J verbatim as historical evidence; records their affected
results as SUPERSEDED_BY_DATUM_RECONCILIATION. No production/spec/authority edits;
no PDF; experiment branch only.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List

# Shared experiment-only utilities (SourceDatum, provenance, writers).
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))


def _load_authority_util():
    path = os.path.join(_HERE, "d28_geometry_authority.py")
    spec = importlib.util.spec_from_file_location("d28_geometry_authority", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d28_geometry_authority"] = m
    spec.loader.exec_module(m)
    return m


GA = _load_authority_util()
SourceDatum = GA.SourceDatum

_RESULTS = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
_DEFAULT_DOC = os.path.join(_REPO_ROOT, "docs", "experiments",
                            "THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md")
_OUTDIR = os.environ.get("D28_EXP_OUTDIR") or _RESULTS
_DOC = os.environ.get("D28_EXP_DOC") or (
    _DEFAULT_DOC if _OUTDIR == _RESULTS else os.path.join(_OUTDIR, "REPORT.md"))

# --- Outputs (004K only) -----------------------------------------------------
AUTHORITY_JSON = os.path.join(_OUTDIR, "D28_65260_SOURCE_DATUM_AUTHORITY_004K.json")
RECONCILIATION_CSV = os.path.join(_OUTDIR, "D28_65260_DIMENSION_RECONCILIATION_004K.csv")
SUPERSEDED_CSV = os.path.join(_OUTDIR, "D28_65260_SUPERSEDED_INTERPRETATIONS_004K.csv")
SUMMARY_CSV = os.path.join(_OUTDIR, "D28_65260_RERUN_004K_SUMMARY.csv")
PROVENANCE_JSON = os.path.join(_OUTDIR, "D28_65260_RERUN_004K_PROVENANCE.json")

_S, _E = "<!-- RERUN004K_START -->", "<!-- RERUN004K_END -->"
_GS, _GE = "<!-- GOVERNING_STATE_004K_START -->", "<!-- GOVERNING_STATE_004K_END -->"

# --- Reconciled source dimensions (fractions resolved to exact decimals) -----
OUTSIDE_BODY_LENGTH_IN = 20.21875      # 20 7/32
INTERNAL_BLOCK_TO_BLOCK_LENGTH_IN = 30.4375   # 30 7/16  (NOT the developed rim)
WAIST_RADIUS_IN = 4.4375               # 4 7/16   (plan radius, NOT depth)
WAIST_SIDE_HEIGHT_IN = 4.220           # Arnold measured side height


def build_datums() -> List["SourceDatum"]:
    """The corrected #65260 source-datum dictionary (004K authority)."""
    return [
        SourceDatum(
            name="outside_body_profile_length",
            value_in=OUTSIDE_BODY_LENGTH_IN, unit="in",
            meaning="Outside longitudinal body-profile length reported by CAD (neck end to tail end).",
            classification="SOURCE_CAD_CONFIRMED",
            source="Arnold #65260 CAD reconstruction (20 7/32 in annotation)",
            participates_in_geometry=True,
            prior_interpretation=None,
            axis="longitudinal_outside",
            notes="Cross-check target for the extracted-outline longitudinal extent (004L).",
        ),
        SourceDatum(
            name="internal_headblock_tailblock_length",
            value_in=INTERNAL_BLOCK_TO_BLOCK_LENGTH_IN, unit="in",
            meaning=("Internal body/cavity length from tail block to head block; also the extent of "
                     "the Arnold side-height station axis (bottom station = 30.4375). NOT the "
                     "developed rim length."),
            classification="SOURCE_PLAN_CORROBORATED",
            source="Arnold #65260 drawing (30 7/16 in) + generic-plan corroboration",
            participates_in_geometry=True,
            prior_interpretation="004C/004D: developed side / rim length (DEV_SIDE_LEN = 30.4375)",
            axis="longitudinal_internal_station",
            notes=("Exact physical endpoints (head-block vs tail-block faces, and whether measured "
                   "along the centerline or the internal cavity) are NOT uniquely fixed by the "
                   "source; endpoint convention is PRESERVED AS UNRESOLVED. The value exceeds the "
                   "outside body length (20.21875 in) and the developed one-side rim (004L), so it "
                   "cannot be a straight neck-to-tail longitudinal span; it is retained as a labelled "
                   "block-to-block / station-axis quantity, never equated to the other two lengths."),
        ),
        SourceDatum(
            name="waist_radius",
            value_in=WAIST_RADIUS_IN, unit="in",
            meaning="Waist radius (plan-view geometry).",
            classification="SOURCE_CAD_CONFIRMED",
            source="Arnold #65260 source annotation (4 7/16 in) + CAD confirmation",
            participates_in_geometry=True,
            prior_interpretation="004C: assembled body depth ('DEEP', 4.4375 in)",
            axis="plan_radius",
            notes=("A plan-geometry radius. NOT used to infer the longitudinal waist position "
                   "(Decision 4); plan-view waist placement comes from outline geometry."),
        ),
        SourceDatum(
            name="waist_side_height",
            value_in=WAIST_SIDE_HEIGHT_IN, unit="in",
            meaning="Arnold measured side height at the waist (side-depth axis).",
            classification="SOURCE_MEASURED",
            source="Arnold #65260 drawing (measured side height 4.220 in)",
            participates_in_geometry=True,
            prior_interpretation=None,
            axis="side_depth",
            notes=("A side-depth measurement. Dimensionally a length but on a different geometric "
                   "axis than the waist radius; the two are unrelated (Decision 4)."),
        ),
        SourceDatum(
            name="developed_rim_length",
            value_in=None, unit="in",
            meaning=("Developed one-side rim distance (the side ribbon unrolled flat = one-side plan "
                     "perimeter arc length). DERIVED INDEPENDENTLY in 004L; intentionally NULL here."),
            classification="DEFERRED_TO_004L",
            source="Independently derived from the extracted Arnold/JD plan contour (004L).",
            participates_in_geometry=True,
            prior_interpretation="004C/004D: proxied by 30.4375 in (the internal block-to-block value)",
            axis="developed_arc",
            notes=("Must NOT be inferred merely because a nearby dimension (30.4375 or 20.21875) "
                   "exists on Arnold/GenOne; it is a distinct quantity requiring a geometric "
                   "derivation (Decision 3)."),
        ),
    ]


def build_superseded() -> List[Dict]:
    """Explicit supersession records (prior interpretations retained as history)."""
    return [
        {"locus": "interpretation", "prior": "30.4375 in == developed side / rim length",
         "corrected": "30.4375 in == internal head-block/tail-block length (station-axis extent)",
         "superseded_in": "004K", "evidence": "SOURCE_PLAN_CORROBORATED",
         "why": "Developed rim derived independently in 004L; the two are different quantities."},
        {"locus": "interpretation", "prior": "4.4375 in == assembled body depth (DEEP)",
         "corrected": "4.4375 in == waist radius (plan geometry)",
         "superseded_in": "004K", "evidence": "SOURCE_CAD_CONFIRMED",
         "why": "Source annotation + CAD confirm a plan radius, not a side depth."},
        {"locus": "interpretation", "prior": "4.4375 - 4.220 == top + back plate thickness",
         "corrected": "DELETED — 4.4375 (plan radius) and 4.220 (side height) are unrelated axes",
         "superseded_in": "004K", "evidence": "GEOMETRIC_INDEPENDENCE",
         "why": "Subtracting a plan radius from a side depth has no geometric meaning."},
        {"locus": "004C", "prior": "30.4375 classified as developed-side boundary",
         "corrected": "internal block-to-block / side-height station axis extent",
         "superseded_in": "004K", "evidence": "SOURCE_PLAN_CORROBORATED",
         "why": "Datum reconciliation; 004C artifact preserved verbatim as evidence."},
        {"locus": "004C", "prior": "4.4375 classified as assembled DEEP (depth)",
         "corrected": "waist radius (plan geometry)",
         "superseded_in": "004K", "evidence": "SOURCE_CAD_CONFIRMED",
         "why": "Datum reconciliation; 004C artifact preserved verbatim as evidence."},
        {"locus": "004C", "prior": "0.2175 in (4.4375 - 4.220) interpreted as plate contribution",
         "corrected": "no such quantity — the subtraction is between unrelated axes",
         "superseded_in": "004K", "evidence": "GEOMETRIC_INDEPENDENCE",
         "why": "Plate-thickness inference deleted (Decision 4)."},
        {"locus": "004D", "prior": "u = s / 30.4375 developed-fraction normalization",
         "corrected": "normalized station fraction on the internal block-to-block axis; the developed "
                      "rim arc length is a separate quantity (004L)",
         "superseded_in": "004K", "evidence": "SOURCE_PLAN_CORROBORATED",
         "why": "30.4375 is not the developed arc length; relabelled for the corrected chain (004M)."},
        {"locus": "004D", "prior": "30.4375-to-plan registration treated as developed-to-plan with an "
                                   "A/S 'local stretch ratio' distortion narrative",
         "corrected": "landmark-anchored (neck/waist/tail) station→plan registration; the A/S ratio is "
                      "not a developed-to-plan stretch and the distortion narrative is withdrawn (004M)",
         "superseded_in": "004K", "evidence": "SOURCE_PLAN_CORROBORATED",
         "why": "The stretch ratio was an artifact of equating the station axis with the developed rim."},
    ]


def compute_invariants(datums: List["SourceDatum"]) -> Dict:
    """Semantic + numeric independence invariants (004K required checks)."""
    d = {x.name: x for x in datums}
    outside = d["outside_body_profile_length"].value_in
    internal = d["internal_headblock_tailblock_length"].value_in
    radius = d["waist_radius"].value_in
    side_h = d["waist_side_height"].value_in
    developed_axis = d["developed_rim_length"].axis
    internal_axis = d["internal_headblock_tailblock_length"].axis
    return {
        # outside body length != internal block-to-block length (numeric + axis)
        "outside_ne_internal": outside != internal,
        "outside_axis": d["outside_body_profile_length"].axis,
        "internal_axis": internal_axis,
        # internal block-to-block length != developed rim length (semantic: distinct
        # axes/quantities; developed value is deferred to 004L so numeric inequality
        # is asserted there, independence is asserted here)
        "internal_ne_developed_semantic": internal_axis != developed_axis,
        "developed_value_deferred": d["developed_rim_length"].value_in is None,
        # waist radius != waist side height (semantic independence, not mere numeric)
        "radius_ne_sideheight_numeric": radius != side_h,
        "radius_axis": d["waist_radius"].axis,
        "sideheight_axis": d["waist_side_height"].axis,
        "radius_ne_sideheight_semantic": d["waist_radius"].axis != d["waist_side_height"].axis,
        # no new artifact may classify 4.4375 as DEEP/depth
        "waist_radius_not_depth": "depth" not in d["waist_radius"].meaning.lower()
        and d["waist_radius"].axis == "plan_radius",
    }


def run_all() -> Dict:
    datums = build_datums()
    superseded = build_superseded()
    invariants = compute_invariants(datums)
    all_invariants_hold = all(bool(v) for k, v in invariants.items()
                              if isinstance(v, bool))
    disp = ("SOURCE_DATUM_RECONCILED" if all_invariants_hold
            else "SOURCE_DATUM_RECONCILIATION_INCOMPLETE")
    notes = [
        "Three longitudinal/arc lengths kept strictly distinct: outside body profile "
        f"({OUTSIDE_BODY_LENGTH_IN} in), internal block-to-block ({INTERNAL_BLOCK_TO_BLOCK_LENGTH_IN} in), "
        "and developed one-side rim (derived independently in 004L; NULL here).",
        "Waist radius (4.4375 in, plan geometry) and waist side height (4.220 in, side depth) are "
        "UNRELATED axes; the former plate-thickness inference (4.4375 - 4.220) is deleted.",
        "30.4375 in is relabelled from 'developed side length' to the internal head-block/tail-block "
        "dimension; its exact physical endpoints are preserved as UNRESOLVED.",
        "Runs 001–004J are preserved verbatim; their dependent downstream geometry is marked "
        "SUPERSEDED_BY_DATUM_RECONCILIATION, not rewritten.",
    ]
    return dict(datums=datums, superseded=superseded, invariants=invariants,
                all_invariants_hold=all_invariants_hold, disp=disp, notes=notes)


# =============================================================================
# Writers
# =============================================================================

def write_authority(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004K_SOURCE_DATUM_RECONCILIATION",
        "disposition": R["disp"],
        "outside_body_profile_length_in": OUTSIDE_BODY_LENGTH_IN,
        "internal_headblock_tailblock_length_in": INTERNAL_BLOCK_TO_BLOCK_LENGTH_IN,
        "waist_radius_in": WAIST_RADIUS_IN,
        "waist_side_height_in": WAIST_SIDE_HEIGHT_IN,
        "developed_rim_length_in": None,
        "datums": [x.as_record() for x in R["datums"]],
        "independence_invariants": R["invariants"],
        "endpoints_unresolved": {
            "internal_headblock_tailblock_length": (
                "Head-block/tail-block face endpoints and the measurement path for 30.4375 in are not "
                "uniquely fixed by the source; preserved as UNRESOLVED (stop condition if a downstream "
                "run requires them)."),
        },
        "preserved_prior_runs": "001-004J retained verbatim; dependent geometry = SUPERSEDED_BY_DATUM_RECONCILIATION",
        "no_production_changes": True,
        "no_prior_run_alteration": True,
        "pdf_vendored": False,
    }
    GA.write_provenance_json(AUTHORITY_JSON, rec)


def write_reconciliation(R: Dict) -> None:
    rows = []
    for x in R["datums"]:
        rows.append({
            "name": x.name,
            "value_in": ("" if x.value_in is None else f"{x.value_in:.5f}"),
            "unit": x.unit,
            "axis": x.axis,
            "meaning": x.meaning,
            "classification": x.classification,
            "source": x.source,
            "participates_in_geometry": x.participates_in_geometry,
            "prior_interpretation": (x.prior_interpretation or ""),
            "notes": x.notes,
        })
    GA.wr_csv(RECONCILIATION_CSV, list(rows[0].keys()), rows)


def write_superseded(R: Dict) -> None:
    rows = [{
        "locus": s["locus"], "prior_interpretation": s["prior"],
        "corrected_interpretation": s["corrected"], "superseded_in_run": s["superseded_in"],
        "evidence_class": s["evidence"], "why": s["why"],
        "disposition": "SUPERSEDED_BY_DATUM_RECONCILIATION",
    } for s in R["superseded"]]
    GA.wr_csv(SUPERSEDED_CSV, list(rows[0].keys()), rows)


def write_summary(R: Dict) -> None:
    inv = R["invariants"]
    row = {
        "disposition": R["disp"],
        "outside_body_profile_length_in": f"{OUTSIDE_BODY_LENGTH_IN:.5f}",
        "internal_headblock_tailblock_length_in": f"{INTERNAL_BLOCK_TO_BLOCK_LENGTH_IN:.5f}",
        "waist_radius_in": f"{WAIST_RADIUS_IN:.5f}",
        "waist_side_height_in": f"{WAIST_SIDE_HEIGHT_IN:.5f}",
        "developed_rim_length_in": "NULL (derived in 004L)",
        "outside_ne_internal": inv["outside_ne_internal"],
        "internal_ne_developed_semantic": inv["internal_ne_developed_semantic"],
        "radius_ne_sideheight_semantic": inv["radius_ne_sideheight_semantic"],
        "waist_radius_not_depth": inv["waist_radius_not_depth"],
        "all_invariants_hold": R["all_invariants_hold"],
        "n_superseded_records": len(R["superseded"]),
        "prior_runs_preserved": "001-004J (verbatim)",
        "final_disposition": R["disp"],
    }
    GA.wr_csv(SUMMARY_CSV, list(row.keys()), [row])


def write_provenance(R: Dict) -> None:
    rec = {
        "experiment": "D28_RUN_004K_SOURCE_DATUM_RECONCILIATION",
        "parent_commit": GA.git_sha(),
        "script": "scripts/experiments/d28_rerun004k_source_datum_reconciliation.py",
        "command": "python scripts/experiments/d28_rerun004k_source_datum_reconciliation.py --write",
        "inputs": "none (datum authority is established from reconciled source dimensions; no "
                  "geometry recomputed, no committed artifact consumed)",
        "output_paths": [os.path.basename(p) for p in (
            AUTHORITY_JSON, RECONCILIATION_CSV, SUPERSEDED_CSV, SUMMARY_CSV, PROVENANCE_JSON)],
        "distinguishes_extracted_from_constructed": True,
        "runtime_pdf_access": False,
        "no_production_changes": True,
        "no_prior_run_alteration": True,
        "pdf_vendored": False,
        "disposition": R["disp"],
    }
    GA.write_provenance_json(PROVENANCE_JSON, rec)


# =============================================================================
# Report (section + governing-state banner)
# =============================================================================

def build_section(R: Dict) -> str:
    L: List[str] = []
    w = L.append
    w("## Run 004K — Source Datum Reconciliation")
    w("")
    w(f"- Repository SHA tested: `{GA.git_sha()}`")
    w("- Establishes the **corrected meaning, classification, provenance, and independence** of the "
      "major Arnold/CAD #65260 dimensions **before** any geometry is recalculated. No rim, back "
      "surface, or curvature is reconstructed in this run.")
    w("- Artifacts: `D28_65260_SOURCE_DATUM_AUTHORITY_004K.json`, "
      "`D28_65260_DIMENSION_RECONCILIATION_004K.csv`, `D28_65260_SUPERSEDED_INTERPRETATIONS_004K.csv`, "
      "`D28_65260_RERUN_004K_SUMMARY.csv`, `D28_65260_RERUN_004K_PROVENANCE.json`. No PDF vendored.")
    w("")
    w("### Corrected source dimensions")
    w("")
    w("| dimension | value | corrected meaning | axis | class | prior (superseded) |")
    w("|---|---:|---|---|---|---|")
    for x in R["datums"]:
        val = "— (004L)" if x.value_in is None else f"{x.value_in:.5f} in"
        w(f"| `{x.name}` | {val} | {x.meaning.split('.')[0]}. | `{x.axis}` | `{x.classification}` | "
          f"{(x.prior_interpretation or '—')} |")
    w("")
    w("### Independence invariants (required)")
    w("")
    inv = R["invariants"]
    w(f"- outside body length (`{OUTSIDE_BODY_LENGTH_IN}`) ≠ internal block-to-block "
      f"(`{INTERNAL_BLOCK_TO_BLOCK_LENGTH_IN}`): **{inv['outside_ne_internal']}**.")
    w(f"- internal block-to-block ≠ developed rim length (distinct axes `{inv['internal_axis']}` vs "
      f"`internal_axis→developed_arc`; developed value deferred to 004L): "
      f"**{inv['internal_ne_developed_semantic']}**.")
    w(f"- waist radius (`{WAIST_RADIUS_IN}`, `{inv['radius_axis']}`) ≠ waist side height "
      f"(`{WAIST_SIDE_HEIGHT_IN}`, `{inv['sideheight_axis']}`) — semantic independence: "
      f"**{inv['radius_ne_sideheight_semantic']}**.")
    w("")
    w("### Superseded interpretations (preserved as history, not rewritten)")
    w("")
    w("| locus | prior interpretation | corrected | superseded in |")
    w("|---|---|---|---|")
    for s in R["superseded"]:
        w(f"| {s['locus']} | {s['prior']} | {s['corrected']} | {s['superseded_in']} |")
    w("")
    w("### Disposition")
    w("")
    w(f"**`{R['disp']}`**")
    w("")
    for n in R["notes"]:
        w(f"- {n}")
    w("")
    w("Runs 001–004J are untouched. 004K reconstructs no geometry, reads no PDF, and changes no "
      "prior artifact or production file.")
    w("")
    return "\n".join(L)


def build_governing_state() -> str:
    return (
        "> **Current governing state (004K source-datum reconciliation).** Source-datum "
        "reconciliation has superseded the previous interpretation of `30 7/16 in` (30.4375) as the "
        "developed-side length and `4 7/16 in` (4.4375) as the assembled body depth. `30.4375 in` is "
        "the internal head-block/tail-block dimension (and the side-height station-axis extent); "
        "`4.4375 in` is the waist radius; `4.220 in` is the Arnold waist side height; `20.21875 in` is "
        "the CAD outside body-profile length; the developed one-side rim length is derived "
        "independently in 004L. The corrected geometry chain begins at **004K** and continues "
        "004L→004M→004N→004O. Runs **004C–004J remain preserved as historical experiment evidence** "
        "but their downstream geometry is **not current authority**. A unique historical back "
        "surface/radius remains **unresolved**."
    )


def splice_section(section: str) -> None:
    text = ""
    if os.path.exists(_DOC):
        with open(_DOC) as fh:
            text = fh.read()
    block = f"{_S}\n{section}\n{_E}"
    if _S in text and _E in text:
        text = text[:text.index(_S)] + block + text[text.index(_E) + len(_E):]
    elif "<!-- RERUN004J_START -->" in text:
        marker = "<!-- RERUN004J_START -->"
        text = text[:text.index(marker)] + block + "\n\n---\n\n" + text[text.index(marker):]
    else:
        os.makedirs(os.path.dirname(_DOC), exist_ok=True)
        text = (text + "\n\n" if text else "") + block + "\n"
    with open(_DOC, "w") as fh:
        fh.write(text)


def splice_governing_state() -> None:
    """Insert/refresh the corrected governing-state banner (idempotent, durable marker)."""
    text = ""
    if os.path.exists(_DOC):
        with open(_DOC) as fh:
            text = fh.read()
    block = f"{_GS}\n{build_governing_state()}\n{_GE}"
    if _GS in text and _GE in text:
        text = text[:text.index(_GS)] + block + text[text.index(_GE) + len(_GE):]
    else:
        lines = text.split("\n")
        # insert right after the H1 title (first line starting with '# ')
        insert_at = 1 if lines and lines[0].startswith("# ") else 0
        new = lines[:insert_at] + ["", block, ""] + lines[insert_at:]
        text = "\n".join(new)
    with open(_DOC, "w") as fh:
        fh.write(text)


def main() -> None:
    R = run_all()
    section = build_section(R)
    if "--write" in sys.argv:
        os.makedirs(_OUTDIR, exist_ok=True)
        write_authority(R)
        write_reconciliation(R)
        write_superseded(R)
        write_summary(R)
        write_provenance(R)
        splice_governing_state()
        splice_section(section)
        print(f"wrote 004K artifacts; disposition={R['disp']}; "
              f"invariants_hold={R['all_invariants_hold']}; superseded={len(R['superseded'])}")
    else:
        print(section)
        print(f"\n[disposition={R['disp']}; invariants_hold={R['all_invariants_hold']}]")


if __name__ == "__main__":
    main()
