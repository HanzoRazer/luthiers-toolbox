"""SAW-FEASIBILITY-CALIBRATION-007 — evidence integrity.

Proves the diagnostic harness and the committed trace. Does not change
formulas, thresholds, routes, or inventory, and does not monkeypatch
calculators.
"""
from __future__ import annotations

import ast
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

from app.rmos.api.saw_feasibility import compute_saw_feasibility
from app.saw_lab.calculators import FeasibilityCalculatorBundle
from tests.rmos.test_rmos_feasibility_authority import SANE_SAW
from tests.rmos.test_saw_authority_context import COMPLETE_SAW_REQUEST

MERGE_420 = "e06b3075a4e1fa9610f551598ff6cdd025c32802"
MERGE_422 = "9f15a2202ae059a23e744a4fb737e48dc5e5944d"

CALC_ORDER = (
    "heat",
    "deflection",
    "rim_speed",
    "bite_load",
    "kickback",
    "cutting_force",
    "blade_dynamics",
)
CALC_MODULES = {
    "heat": "app.saw_lab.calculators.saw_heat",
    "deflection": "app.saw_lab.calculators.saw_deflection",
    "rim_speed": "app.saw_lab.calculators.saw_rimspeed",
    "bite_load": "app.saw_lab.calculators.saw_bite_load",
    "kickback": "app.saw_lab.calculators.saw_kickback",
    "cutting_force": "app.saw_lab.calculators.saw_cutting_force",
    "blade_dynamics": "app.saw_lab.calculators.saw_blade_dynamics",
}
CONSUMED_FACTS = (
    "blade_diameter_mm",
    "blade_kerf_mm",
    "blade_thickness_mm",
    "tooth_count",
    "rpm",
    "arbor_size_mm",
    "stock_thickness_mm",
    "feed_rate_mm_min",
    "machine_power_kw",
    "blade_youngs_modulus_gpa",
    "cut_length_mm",
    "miter_angle_deg",
    "bevel_angle_deg",
    "dado_width_mm",
    "dado_depth_mm",
    "repeat_count",
    "material_id",
    "use_dust_collection",
    "specific_cutting_energy",
)
FORBIDDEN_PREFIXES = (
    "services/api/app/saw_lab/",
    "services/api/app/rmos/",
    "services/api/app/toolpath/saw_engine.py",
    "services/api/app/services/saw_lab_compare_service.py",
    "governance/manufacturing_output_inventory.json",
)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists() and (parent / "AGENTS.md").is_file():
            return parent
    raise RuntimeError("repository root not found")


def _evidence_dir() -> Path:
    return _repo_root() / "docs" / "investigations" / "saw-feasibility-calibration_2026-10-02"


def _evidence() -> dict:
    return json.loads((_evidence_dir() / "evidence.json").read_text())


def _csv_rows() -> list[dict]:
    with (_evidence_dir() / "SENSITIVITY.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=_repo_root(),
        text=True,
    ).strip()


def _safety(req: dict) -> dict:
    return compute_saw_feasibility(
        mode="saw",
        tool_id=req.get("tool_id"),
        req=req,
        context="saw-feasibility-calibration-007",
    )["safety"]


def _parse_sweep_value(variable: str, raw: str):
    current = COMPLETE_SAW_REQUEST[variable]
    if isinstance(current, bool):
        return raw == "True"
    if isinstance(current, int):
        return int(float(raw))
    return float(raw)


def _close(left, right) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-6)


def _changed_paths() -> set[str]:
    diff = _git("diff", "--name-only", "origin/main...HEAD").splitlines()
    status = _git("status", "--porcelain", "-uall").splitlines()
    paths = {line.strip() for line in diff if line.strip()}
    for line in status:
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.add(path.strip('"'))
    return paths


def test_sfc001_main_contains_420_and_422():
    evidence = _evidence()
    assert evidence["merge_420"] == MERGE_420
    assert evidence["merge_422"] == MERGE_422
    assert evidence["base_sha"] == _git("rev-parse", "origin/main")
    for sha in (MERGE_420, MERGE_422):
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
            cwd=_repo_root(),
        )


def test_sfc002_branch_contains_current_main():
    assert _git("merge-base", "HEAD", "origin/main") == _git("rev-parse", "origin/main")


def test_sfc005_seven_calculators_match_the_bundle():
    bundle = FeasibilityCalculatorBundle()
    assert tuple(bundle._calculators) == CALC_ORDER
    evidence_names = [row["calculator"] for row in _evidence()["case_b"]["calculators"]]
    assert evidence_names == list(CALC_ORDER)
    for name, calculator in bundle._calculators.items():
        assert type(calculator).calculate.__module__ == CALC_MODULES[name]
        assert not hasattr(type(calculator).calculate, "mock")


def test_sfc006_case_a_is_not_assembled():
    case_a = _evidence()["case_a"]
    assert case_a["status"] == "not_assembled"
    assert "request" not in case_a


def test_sfc007_case_b_is_the_authority_fixture():
    case_b = _evidence()["case_b"]
    assert case_b["classification"] == "repository_fixture"
    assert case_b["request"] == COMPLETE_SAW_REQUEST
    assert case_b["approved_operating_point"] is False
    sane = _evidence()["case_b_sane_saw_same_verdict"]
    assert sane["same_score_as_case_b"] is True
    assert sane["same_risk_as_case_b"] is True


def test_sfc008_sweeps_are_hypothetical():
    assert _evidence()["case_c_label"] == "hypothetical_sweep"
    rows = _csv_rows()
    hypothetical = [row for row in rows if row["case_id"].startswith("CASE-C-")]
    assert hypothetical
    for row in hypothetical:
        assert row["source_classification"] == "hypothetical_sweep"
        assert row["approved_operating_point"] == "False"
        assert row["risk"] == "RED"


def test_sfc009_case_d_stays_blocking():
    case_d = _evidence()["case_d"]
    assert case_d["classification"] == "known_invalid_control"
    assert case_d["risk_level"] == "RED"
    assert case_d["score"] == 34.3
    safety = _safety(
        dict(
            COMPLETE_SAW_REQUEST,
            feed_rate_mm_min=18000.0,
            stock_thickness_mm=100.0,
            machine_power_kw=0.5,
            rpm=9000,
        )
    )
    assert safety["risk_level"] == "RED"
    assert safety["score"] == case_d["score"]
    assert safety["details"]["engine"] == "feasibility_scorer"


def test_sfc010_canonical_verdict_is_reproduced_without_monkeypatch():
    source = (_repo_root() / "scripts" / "investigations" / "generate_saw_feasibility_calibration.py").read_text()
    assert "monkeypatch" not in source
    assert "unittest.mock" not in source
    tree = ast.parse(source)
    imported = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert any(node.module == "app.rmos.api.saw_feasibility" for node in imported)
    safety = _safety(dict(COMPLETE_SAW_REQUEST))
    case_b = _evidence()["case_b"]
    assert safety["risk_level"] == case_b["risk_level"] == "RED"
    assert safety["score"] == case_b["score"] == 56.2
    assert safety["details"]["engine"] == "feasibility_scorer"
    results = safety["details"]["calculator_results"]
    for row in case_b["calculators"]:
        assert results[row["calculator"]]["score"] == row["score"]
    sane = _safety(dict(SANE_SAW, tool_id="saw:default"))
    assert sane["score"] == 56.2
    assert sane["risk_level"] == "RED"


def test_sfc011_trace_has_units_and_outputs():
    required = {
        "heat": ("temp_rise_c", "cutting_power_w", "thermal_conductivity"),
        "deflection": ("deflection_mm", "mrr_mm3_per_s", "youngs_modulus_gpa"),
        "rim_speed": ("rim_speed_m_s", "current_rpm", "blade_diameter_mm"),
        "bite_load": ("bite_load_mm", "current_feed_mm_per_min", "tooth_count"),
        "kickback": ("blade_exposure_mm", "feed_per_tooth_mm"),
        "cutting_force": (
            "cutting_power_w",
            "available_power_w",
            "power_ratio",
            "specific_cutting_energy_j_per_mm3",
            "mrr_mm3_per_s",
        ),
        "blade_dynamics": ("nearest_critical_rpm", "margin_to_critical", "operating_rpm"),
    }
    for row in _evidence()["case_b"]["calculators"]:
        for key in required[row["calculator"]]:
            assert key in row["metadata"], key
        assert row["weight"] is not None
        assert row["score"] is not None


def test_sfc012_aggregation_is_explained():
    case_b = _evidence()["case_b"]
    weights = _evidence()["aggregation"]["weights"]
    assert math.isclose(sum(weights.values()), 1.0)
    total = round(sum(row["score"] * weights[row["calculator"]] for row in case_b["calculators"]), 1)
    assert total == case_b["score"] == case_b["weighted_sum_rounded"]
    assert case_b["score_matches_weighted_sum"] is True
    assert case_b["first_red_gate_in_evaluation_order"] == "heat"
    assert case_b["calculators_forcing_red"] == ["heat", "deflection", "cutting_force"]
    assert _evidence()["aggregation"]["individual_red_below"] == 30.0


def test_sfc013_sweeps_change_only_the_named_fact():
    for row in _csv_rows():
        if not row["case_id"].startswith("CASE-C-"):
            continue
        variable = row["changed_variable"]
        req = dict(COMPLETE_SAW_REQUEST)
        req[variable] = _parse_sweep_value(variable, row["value"])
        assert sum(1 for key, value in req.items() if COMPLETE_SAW_REQUEST[key] != value) == 1


def _assert_variable_deterministic(variable: str) -> None:
    matched = [row for row in _csv_rows() if row["changed_variable"] == variable]
    assert len(matched) >= 3
    for row in matched:
        req = dict(COMPLETE_SAW_REQUEST)
        req[variable] = _parse_sweep_value(variable, row["value"])
        first = _safety(req)
        second = _safety(req)
        assert first == second
        assert first["risk_level"] == row["risk"] == "RED"
        assert _close(first["score"], row["score"])
        results = first["details"]["calculator_results"]
        assert _close(results["heat"]["temp_rise_c"], row["heat_temp_rise_c"])
        assert _close(results["cutting_force"]["cutting_power_w"], row["cutting_power_w"])
        assert _close(results["cutting_force"]["power_ratio"], row["power_ratio"])
        assert results["cutting_force"]["specific_cutting_energy_j_per_mm3"] == 30.0


def test_sfc014_rpm_sensitivity_is_deterministic():
    _assert_variable_deterministic("rpm")


def test_sfc015_feed_sensitivity_is_deterministic():
    _assert_variable_deterministic("feed_rate_mm_min")


def test_sfc016_diameter_sensitivity_is_deterministic():
    _assert_variable_deterministic("blade_diameter_mm")


def test_sfc017_kerf_sensitivity_is_deterministic():
    _assert_variable_deterministic("blade_kerf_mm")


def test_sfc018_tooth_count_sensitivity_is_deterministic():
    _assert_variable_deterministic("tooth_count")


def test_sfc019_stock_thickness_sensitivity_is_deterministic():
    _assert_variable_deterministic("stock_thickness_mm")


def test_sfc020_machine_power_sensitivity_is_deterministic():
    _assert_variable_deterministic("machine_power_kw")


def test_sfc021_repeat_count_changes_time_only():
    scope = _evidence()["repeat_count_scope"]
    assert scope[0]["repeat_count"] == 1
    assert scope[1]["repeat_count"] == 8
    assert scope[0]["calculator_scores"] == scope[1]["calculator_scores"]
    assert scope[0]["estimated_cut_time_seconds"] == 11.0
    assert scope[1]["estimated_cut_time_seconds"] == 88.0
    once = _safety(dict(COMPLETE_SAW_REQUEST, repeat_count=1))
    many = _safety(dict(COMPLETE_SAW_REQUEST, repeat_count=8))
    assert once["details"]["calculator_results"] == many["details"]["calculator_results"]
    assert once["details"]["estimated_cut_time_seconds"] == 11.0
    assert many["details"]["estimated_cut_time_seconds"] == 88.0


def test_sfc022_bounds_are_not_coerced_to_defaults():
    for row in _evidence()["boundaries"]:
        assert row["hidden_default_5000_or_3000"] is False
        assert row["risk_level"] == "RED"
        if row["variable"] == "repeat_count":
            assert row["echoed_by_calculator"] == "time_only"
        else:
            assert row["echoed_by_calculator"] == row["submitted"]


def test_sfc023_unit_audit_names_every_consumed_fact():
    text = (_evidence_dir() / "UNIT_AUDIT.md").read_text()
    for fact in CONSUMED_FACTS:
        assert fact in text
    force = next(
        row for row in _evidence()["case_b"]["calculators"] if row["calculator"] == "cutting_force"
    )
    meta = force["metadata"]
    mrr = 3.0 * 25.0 * (3000.0 / 60.0)
    assert _close(meta["mrr_mm3_per_s"], mrr)
    assert _close(meta["cutting_power_w"], 30.0 * mrr)
    assert _close(meta["available_power_w"], 3.0 * 1000.0 * 0.85)
    assert meta["power_ratio"] == round(meta["cutting_power_w"] / meta["available_power_w"], 3)
    rim = next(row for row in _evidence()["case_b"]["calculators"] if row["calculator"] == "rim_speed")
    assert rim["metadata"]["rim_speed_m_s"] == round(math.pi * 254.0 * 3450.0 / 60000.0, 2)
    bite = next(row for row in _evidence()["case_b"]["calculators"] if row["calculator"] == "bite_load")
    assert bite["metadata"]["bite_load_mm"] == round(3000.0 / (3450.0 * 24.0), 5)


def test_sfc024_compare_route_is_the_same_bundle():
    compare = _evidence()["compare_route"]
    assert compare["same_calculator_bundle"] is True
    assert compare["richer_physics_model"] is False
    source = (_repo_root() / "scripts" / "investigations" / "generate_saw_feasibility_calibration.py").read_text()
    tree = ast.parse(source)
    called = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            called.append(func.id if isinstance(func, ast.Name) else getattr(func, "attr", None))
    assert "compare_saw_candidates" not in called
    assert "saw_lab_compare_service" not in source


def test_sfc025_026_diff_does_not_touch_production_or_inventory():
    for path in _changed_paths():
        for prefix in FORBIDDEN_PREFIXES:
            assert not path.startswith(prefix), path
    assert _evidence()["production_formulas_changed"] is False


def test_sfc027_regeneration_is_byte_identical():
    evidence_path = _evidence_dir() / "evidence.json"
    csv_path = _evidence_dir() / "SENSITIVITY.csv"
    before_evidence = evidence_path.read_bytes()
    before_csv = csv_path.read_bytes()
    subprocess.check_call(
        [sys.executable, str(_repo_root() / "scripts" / "investigations" / "generate_saw_feasibility_calibration.py")],
        cwd=_repo_root(),
    )
    assert evidence_path.read_bytes() == before_evidence
    assert csv_path.read_bytes() == before_csv


def test_sfc030_one_next_increment():
    evidence = _evidence()
    assert evidence["next_increment"] == "SAW-ENERGY-IDENTITY-008"
    assert evidence["containment_ready"] == "NO"
    text = (_evidence_dir() / "ADJUDICATION.md").read_text()
    marker = "## Recommended next increment\n\nSAW-ENERGY-IDENTITY-008\n"
    assert marker in text
    assert text.count("## Recommended next increment") == 1
    assert "## Containment readiness\n\n`NO`\n" in text
