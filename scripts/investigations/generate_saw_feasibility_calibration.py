#!/usr/bin/env python3
"""Regenerate SAW-FEASIBILITY-CALIBRATION-007 evidence from production code.

Read-only. Does not change formulas, thresholds, routes, or inventory.
Writes the committed JSON trace and the one-variable sensitivity CSV.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "services" / "api"
sys.path.insert(0, str(API))

from pydantic import ValidationError  # noqa: E402

from app.rmos.api.saw_feasibility import compute_saw_feasibility  # noqa: E402
from app.saw_lab.calculators import FeasibilityCalculatorBundle  # noqa: E402
from app.saw_lab.models import MaterialProperties, SawContext  # noqa: E402
from tests.rmos.test_rmos_feasibility_authority import SANE_SAW  # noqa: E402
from tests.rmos.test_saw_authority_context import COMPLETE_SAW_REQUEST  # noqa: E402

OUT_DIR = ROOT / "docs" / "investigations" / "saw-feasibility-calibration_2026-10-02"
EVIDENCE_PATH = OUT_DIR / "evidence.json"
CSV_PATH = OUT_DIR / "SENSITIVITY.csv"

BASE_SHA = "ea320c844a5df62954d732602bf4371c4228d3ae"
MERGE_420 = "e06b3075a4e1fa9610f551598ff6cdd025c32802"
MERGE_422 = "9f15a2202ae059a23e744a4fb737e48dc5e5944d"

WEIGHTS = dict(FeasibilityCalculatorBundle.WEIGHTS)
CALC_ORDER = (
    "heat",
    "deflection",
    "rim_speed",
    "bite_load",
    "kickback",
    "cutting_force",
    "blade_dynamics",
)
RED_GATE = 30.0

# Model bounds from saw_lab.models.SawContext / SawDesign. Hypothetical only.
SWEEPS = (
    ("rpm", (2000, 3450, 6000, 10000)),
    ("feed_rate_mm_min", (100.0, 3000.0, 8000.0, 20000.0)),
    ("blade_diameter_mm", (100.0, 254.0, 400.0, 600.0)),
    ("blade_kerf_mm", (1.0, 3.0, 6.0, 10.0)),
    ("tooth_count", (10, 24, 80, 120)),
    ("stock_thickness_mm", (1.0, 25.0, 80.0, 150.0)),
    ("machine_power_kw", (0.5, 3.0, 15.0, 20.0)),
    ("repeat_count", (1, 2, 8, 100)),
)

BOUNDARIES = (
    ("rpm", 1000),
    ("rpm", 10000),
    ("feed_rate_mm_min", 100.0),
    ("feed_rate_mm_min", 20000.0),
    ("blade_diameter_mm", 100.0),
    ("blade_diameter_mm", 600.0),
    ("tooth_count", 10),
    ("tooth_count", 120),
    ("repeat_count", 1),
    ("repeat_count", 100),
)

CASE_B_SOURCE = "services/api/tests/rmos/test_saw_authority_context.py:COMPLETE_SAW_REQUEST"
SANE_SOURCE = "services/api/tests/rmos/test_rmos_feasibility_authority.py:SANE_SAW"
CASE_D_SOURCE = (
    "services/api/tests/rmos/test_saw_authority_context.py:"
    "test_sac026_028_unsafe_fixture_blocks_red_real_evaluator"
)


def _case_d() -> dict:
    """The unsafe control already fixed in the authority test. Not a new job."""
    return dict(
        COMPLETE_SAW_REQUEST,
        feed_rate_mm_min=18000.0,
        stock_thickness_mm=100.0,
        machine_power_kw=0.5,
        rpm=9000,
    )


def _evaluate(req: dict) -> dict:
    return compute_saw_feasibility(
        mode="saw",
        tool_id=req.get("tool_id"),
        req=req,
        context="saw-feasibility-calibration-007",
    )


def _safety(req: dict) -> dict:
    return _evaluate(req)["safety"]


def _calc_rows(safety: dict) -> list:
    results = (safety.get("details") or {}).get("calculator_results") or {}
    rows = []
    forcing = []
    for name in CALC_ORDER:
        raw = results.get(name) or {}
        score = raw.get("score")
        weight = WEIGHTS[name]
        contribution = None if score is None else round(float(score) * weight, 4)
        if score is not None and float(score) < RED_GATE:
            forcing.append(name)
        meta = {k: v for k, v in raw.items() if k != "warning"}
        rows.append(
            {
                "calculator": name,
                "score": score,
                "weight": weight,
                "weighted_contribution": contribution,
                "forces_red": bool(score is not None and float(score) < RED_GATE),
                "warning": raw.get("warning"),
                "metadata": meta,
            }
        )
    return rows


def _trace(req: dict, case_id: str, classification: str, source: str) -> dict:
    safety = _safety(req)
    rows = _calc_rows(safety)
    weighted = round(
        sum(r["weighted_contribution"] or 0.0 for r in rows),
        1,
    )
    return {
        "case_id": case_id,
        "classification": classification,
        "source": source,
        "approved_operating_point": False,
        "risk_level": safety.get("risk_level"),
        "score": safety.get("score"),
        "block_reason": safety.get("block_reason"),
        "engine": (safety.get("details") or {}).get("engine"),
        "estimated_cut_time_seconds": (safety.get("details") or {}).get(
            "estimated_cut_time_seconds"
        ),
        "weighted_sum_rounded": weighted,
        "score_matches_weighted_sum": safety.get("score") == weighted,
        "red_gate": "any calculator score < 30 forces RED before the 80/50 bands",
        "first_red_gate_in_evaluation_order": next(
            (r["calculator"] for r in rows if r["forces_red"]),
            None,
        ),
        "calculators_forcing_red": [r["calculator"] for r in rows if r["forces_red"]],
        "calculators": rows,
        "request": req,
    }


def _species_sce() -> dict:
    path = API / "app" / "data_registry" / "system" / "materials" / "wood_species.json"
    doc = json.loads(path.read_text())
    values = []
    for species in doc["species"].values():
        thermal = species.get("thermal") or {}
        sce = thermal.get("specific_cutting_energy_j_per_mm3")
        if isinstance(sce, (int, float)):
            values.append(float(sce))
    rejected = None
    try:
        MaterialProperties(
            id="alder",
            name="Red Alder",
            specific_cutting_energy_j_per_mm3=min(values),
        )
    except ValidationError as exc:
        rejected = str(exc.errors()[0]["type"])
    return {
        "source": str(path.relative_to(ROOT)),
        "unit_label": doc["_meta"]["units"]["specific_cutting_energy_j_per_mm3"],
        "provenance": doc["_meta"]["sources"]["estimation_methods"],
        "min": min(values),
        "max": max(values),
        "count": len(values),
        "material_properties_ge": 5.0,
        "material_properties_le": 200.0,
        "species_minimum_rejected_by_material_properties": rejected,
        "canonical_path_loads_species": False,
    }


def _material_bound() -> dict:
    field = MaterialProperties.model_fields["specific_cutting_energy_j_per_mm3"]
    return {
        "default": field.default,
        "ge": 5.0,
        "le": 200.0,
        "description": field.description,
    }


def _compare_defaults() -> dict:
    ctx = SawContext()
    design_defaults_note = (
        "compare_saw_candidates builds SawDesign(**design) and SawContext(**context). "
        "Omitted fields take the model defaults below. The canonical path rejects "
        "those omissions as UNKNOWN and does not construct SawContext until validation "
        "passes. Both paths then call SawLabService.check_feasibility, which calls "
        "FeasibilityCalculatorBundle.evaluate(design, ctx) with no MaterialProperties."
    )
    return {
        "same_calculator_bundle": True,
        "richer_physics_model": False,
        "note": design_defaults_note,
        "saw_context_defaults_if_omitted": {
            "blade_diameter_mm": ctx.blade_diameter_mm,
            "blade_kerf_mm": ctx.blade_kerf_mm,
            "blade_thickness_mm": ctx.blade_thickness_mm,
            "tooth_count": ctx.tooth_count,
            "max_rpm": ctx.max_rpm,
            "arbor_size_mm": ctx.arbor_size_mm,
            "stock_thickness_mm": ctx.stock_thickness_mm,
            "feed_rate_mm_per_min": ctx.feed_rate_mm_per_min,
            "machine_power_kw": ctx.machine_power_kw,
            "blade_youngs_modulus_gpa": ctx.blade_youngs_modulus_gpa,
            "use_dust_collection": ctx.use_dust_collection,
        },
    }


def _csv_row(trace: dict, variable: str, value, classification: str) -> dict:
    by_name = {row["calculator"]: row for row in trace["calculators"]}

    def meta(name: str, key: str):
        return (by_name.get(name) or {}).get("metadata", {}).get(key)

    def score(name: str):
        return (by_name.get(name) or {}).get("score")

    warnings = [row["warning"] for row in trace["calculators"] if row.get("warning")]
    return {
        "case_id": trace["case_id"],
        "changed_variable": variable,
        "value": value,
        "source_classification": classification,
        "approved_operating_point": False,
        "score": trace["score"],
        "risk": trace["risk_level"],
        "estimated_cut_time_seconds": trace["estimated_cut_time_seconds"],
        "heat_score": score("heat"),
        "heat_temp_rise_c": meta("heat", "temp_rise_c"),
        "deflection_score": score("deflection"),
        "deflection_mm": meta("deflection", "deflection_mm"),
        "rim_speed_score": score("rim_speed"),
        "rim_speed_m_s": meta("rim_speed", "rim_speed_m_s"),
        "bite_load_score": score("bite_load"),
        "bite_load_mm": meta("bite_load", "bite_load_mm"),
        "kickback_score": score("kickback"),
        "cutting_force_score": score("cutting_force"),
        "cutting_power_w": meta("cutting_force", "cutting_power_w"),
        "power_ratio": meta("cutting_force", "power_ratio"),
        "kc_j_per_mm3": meta("cutting_force", "specific_cutting_energy_j_per_mm3"),
        "blade_dynamics_score": score("blade_dynamics"),
        "warnings": " | ".join(warnings),
    }


def _sweep_rows(baseline: dict) -> list:
    rows = [
        _csv_row(baseline, "none", "", "repository_fixture"),
    ]
    base_req = dict(COMPLETE_SAW_REQUEST)
    for variable, values in SWEEPS:
        for value in values:
            if base_req.get(variable) == value:
                continue
            req = dict(base_req, **{variable: value})
            trace = _trace(
                req,
                f"CASE-C-{variable}-{value}",
                "hypothetical_sweep",
                "saw_lab.models bounds; not an approved operating point",
            )
            rows.append(_csv_row(trace, variable, value, "hypothetical_sweep"))
    rows.append(
        _csv_row(
            _trace(_case_d(), "CASE-D", "known_invalid_control", CASE_D_SOURCE),
            "feed_rate_mm_min,stock_thickness_mm,machine_power_kw,rpm",
            "18000,100,0.5,9000",
            "known_invalid_control",
        )
    )
    return rows


def _write_csv(rows: list) -> None:
    fieldnames = list(rows[0].keys())
    with CSV_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_evidence() -> dict:
    case_b = _trace(
        dict(COMPLETE_SAW_REQUEST),
        "CASE-B",
        "repository_fixture",
        CASE_B_SOURCE,
    )
    sane = _trace(
        dict(SANE_SAW, tool_id="saw:default"),
        "CASE-B-SANE",
        "repository_fixture",
        SANE_SOURCE,
    )
    case_d = _trace(_case_d(), "CASE-D", "known_invalid_control", CASE_D_SOURCE)
    boundaries = []
    for variable, value in BOUNDARIES:
        req = dict(COMPLETE_SAW_REQUEST, **{variable: value})
        trace = _trace(
            req,
            f"BOUND-{variable}-{value}",
            "hypothetical_sweep",
            "exact SawContext/SawDesign bound; not an approved operating point",
        )
        echoed = None
        if variable == "rpm":
            echoed = trace["calculators"][2]["metadata"].get("current_rpm")
        elif variable == "feed_rate_mm_min":
            echoed = trace["calculators"][3]["metadata"].get("current_feed_mm_per_min")
        elif variable == "blade_diameter_mm":
            echoed = trace["calculators"][2]["metadata"].get("blade_diameter_mm")
        elif variable == "tooth_count":
            echoed = trace["calculators"][3]["metadata"].get("tooth_count")
        elif variable == "repeat_count":
            echoed = "time_only"
        boundaries.append(
            {
                "variable": variable,
                "submitted": value,
                "echoed_by_calculator": echoed,
                "risk_level": trace["risk_level"],
                "score": trace["score"],
                "hidden_default_5000_or_3000": echoed in (5000, 3000.0) and value not in (5000, 3000, 3000.0),
            }
        )
    repeat_scores = []
    for repeats in (1, 8):
        trace = _trace(
            dict(COMPLETE_SAW_REQUEST, repeat_count=repeats),
            f"REPEAT-{repeats}",
            "hypothetical_sweep",
            "repeat_count is consumed by cut-time estimation only",
        )
        repeat_scores.append(
            {
                "repeat_count": repeats,
                "score": trace["score"],
                "risk_level": trace["risk_level"],
                "calculator_scores": {
                    row["calculator"]: row["score"] for row in trace["calculators"]
                },
                "estimated_cut_time_seconds": trace["estimated_cut_time_seconds"],
            }
        )
    return {
        "order": "SAW-FEASIBILITY-CALIBRATION-007",
        "production_formulas_changed": False,
        "base_sha": BASE_SHA,
        "merge_420": MERGE_420,
        "merge_422": MERGE_422,
        "case_a": {
            "status": "not_assembled",
            "reason": (
                "No repository machine, blade, and job record together supply "
                "blade thickness, arbor, RPM, feed, stock, power, and cut geometry. "
                "sample_saw_blades.json has diameter, kerf, and tooth count only. "
                "MACHINE_PRESETS have no spindle power. wood_species machining clamps "
                "are router RPM bands, and their specific_cutting_energy values are "
                "estimated and rejected by MaterialProperties ge=5."
            ),
        },
        "case_b": case_b,
        "case_b_sane_saw_same_verdict": {
            "source": SANE_SOURCE,
            "score": sane["score"],
            "risk_level": sane["risk_level"],
            "same_score_as_case_b": sane["score"] == case_b["score"],
            "same_risk_as_case_b": sane["risk_level"] == case_b["risk_level"],
            "difference": "SANE_SAW supplies spindle_power_watts=3000 instead of machine_power_kw=3",
        },
        "case_c_label": "hypothetical_sweep",
        "case_d": case_d,
        "boundaries": boundaries,
        "repeat_count_scope": repeat_scores,
        "species_specific_cutting_energy": _species_sce(),
        "material_properties_kc": _material_bound(),
        "compare_route": _compare_defaults(),
        "aggregation": {
            "weights": WEIGHTS,
            "weight_sum": round(sum(WEIGHTS.values()), 10),
            "individual_red_below": RED_GATE,
            "green_at_or_above": 80,
            "yellow_at_or_above": 50,
            "source": "services/api/app/saw_lab/calculators/__init__.py:FeasibilityCalculatorBundle",
        },
        "next_increment": "SAW-ENERGY-IDENTITY-008",
        "containment_ready": "NO",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    first = build_evidence()
    second = build_evidence()
    if first != second:
        raise SystemExit("evidence generation is not deterministic")
    text = json.dumps(first, indent=2, sort_keys=True) + "\n"
    EVIDENCE_PATH.write_text(text)
    _write_csv(_sweep_rows(first["case_b"]))
    print(f"wrote {EVIDENCE_PATH.relative_to(ROOT)}")
    print(f"wrote {CSV_PATH.relative_to(ROOT)}")
    print(
        "CASE-B",
        first["case_b"]["risk_level"],
        first["case_b"]["score"],
        "first_red",
        first["case_b"]["first_red_gate_in_evaluation_order"],
    )


if __name__ == "__main__":
    main()
