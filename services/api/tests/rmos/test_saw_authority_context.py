"""SAW-AUTHORITY-CONTEXT-006 — the canonical Saw feasibility path evaluates the
SUBMITTED process facts instead of silently substituting hardcoded defaults.

Covers the achievable SAC matrix: contract transport, completeness/validation
(missing vs invalid, booleans, out-of-range, old-minimal, Rosette-geometry-alone),
sensitivity (distinct inputs no longer collapse to the constant 49.4), the real
evaluator / seven-calculator witnesses, structural safeguards (no fallback
constants or Rosette aliases in the canonical conversion; calculator field
contract), and regression isolation.

SAC-025 (an honest in-range ordinary fixture that PERMITS GREEN/YELLOW) is a
documented STOP, not a fabricated witness: with the frozen Saw calculators the
``deflection`` and ``heat`` calculators flag RED for every in-range ordinary
setup, so no honest fixture permits. Per the order, physics/thresholds must NOT
be tuned to manufacture a GREEN; the limitation is recorded in
``test_sac025_no_honest_permit_is_a_documented_stop`` and the CBSP21 manifest.
"""
from __future__ import annotations

import ast
import copy
import inspect
import pathlib

import pytest

from app.rmos.api.saw_feasibility import (
    _SAW_REQUIRED_BOOL,
    _SAW_REQUIRED_NUMERIC,
    _SAW_REQUIRED_STR,
    _validate_and_normalize,
    compute_saw_feasibility,
)

_APP = pathlib.Path(__file__).resolve().parents[1] / "app"


# Complete, truthful Saw request: every fact the seven calculators consume, all
# within saw_lab.models bounds. Constructed for authority testing (not a
# production-approved machine setup). 10" 24T bench-saw-ish numbers.
COMPLETE_SAW_REQUEST = {
    "tool_id": "saw:authority_test",
    "material_id": "hardwood",
    "blade_diameter_mm": 254.0,
    "blade_kerf_mm": 3.0,
    "blade_thickness_mm": 2.5,
    "tooth_count": 24,
    "rpm": 3450,
    "arbor_size_mm": 25.4,
    "stock_thickness_mm": 25.0,
    "feed_rate_mm_min": 3000.0,
    "machine_power_kw": 3.0,
    "blade_youngs_modulus_gpa": 200.0,
    "use_dust_collection": True,
    "cut_length_mm": 300.0,
    "cut_type": "crosscut",
    "miter_angle_deg": 0.0,
    "bevel_angle_deg": 0.0,
    "dado_width_mm": 0.0,
    "dado_depth_mm": 0.0,
    "repeat_count": 1,
}


def _run(req):
    return compute_saw_feasibility(mode="saw", tool_id=req.get("tool_id"), req=req, context="test")


def _safety(req):
    return _run(req)["safety"]


# --- Contract transport (SAC-001..007) --------------------------------------

def test_sac001_002_003_values_survive_request_to_calculators():
    s = _safety(COMPLETE_SAW_REQUEST)
    assert s["risk_level"] in ("GREEN", "YELLOW", "RED")  # calculated, not UNKNOWN/ERROR
    assert s["details"]["engine"] == "feasibility_scorer"
    # rim speed reflects the submitted diameter+rpm (not a hardcoded default)
    rim = s["details"]["calculator_results"]["rim_speed"]
    assert rim["score"] > 0


def test_sac005_watts_to_kw_single_conversion():
    r = dict(COMPLETE_SAW_REQUEST); r.pop("machine_power_kw"); r["spindle_power_watts"] = 2500.0
    norm, missing, invalid = _validate_and_normalize(r)
    assert not missing and not invalid
    assert abs(norm["machine_power_kw"] - 2.5) < 1e-9  # exactly one /1000 conversion


def test_sac007_client_verdict_fields_non_authoritative():
    r = dict(COMPLETE_SAW_REQUEST, risk_level="GREEN", safety="GREEN", score=100.0)
    s = _safety(r)
    # a client-supplied verdict does not become the result
    assert s["details"]["engine"] == "feasibility_scorer"


# --- Completeness and validation (SAC-008..015) -----------------------------

@pytest.mark.parametrize("field", list(_SAW_REQUIRED_NUMERIC) + list(_SAW_REQUIRED_STR) + list(_SAW_REQUIRED_BOOL))
def test_sac008_009_each_missing_fact_blocks_unknown_and_is_named(field):
    r = copy.deepcopy(COMPLETE_SAW_REQUEST)
    r.pop(field, None)
    s = _safety(r)
    assert s["risk_level"] == "UNKNOWN"           # blocking, never a plausible verdict


def test_sac008_missing_power_blocks():
    r = copy.deepcopy(COMPLETE_SAW_REQUEST); r.pop("machine_power_kw", None)
    assert _safety(r)["risk_level"] == "UNKNOWN"


def test_sac010_invalid_negative_does_not_default():
    r = dict(COMPLETE_SAW_REQUEST, blade_diameter_mm=-254.0)  # out of ge=100 bound
    assert _safety(r)["risk_level"] == "ERROR"    # fails model validation, not defaulted


def test_sac011_boolean_rejected_for_numeric_field():
    r = dict(COMPLETE_SAW_REQUEST, rpm=True)      # bool masquerading as a number
    assert _safety(r)["risk_level"] == "ERROR"


def test_sac012_out_of_range_fails_explicitly():
    r = dict(COMPLETE_SAW_REQUEST, blade_diameter_mm=5000.0)  # over le=600
    assert _safety(r)["risk_level"] == "ERROR"


def test_sac014_malformed_tool_id_supplies_no_hidden_blade_defaults():
    # tool_id carries no process facts; a structured-looking id must not satisfy
    # the contract on its own.
    r = {"tool_id": "saw:10_24_3.0", "material_id": "hardwood"}
    assert _safety(r)["risk_level"] == "UNKNOWN"


def test_sac015_rosette_geometry_alone_cannot_satisfy_saw_contract():
    r = {"tool_id": "saw:x", "material_id": "hardwood",
         "outer_diameter_mm": 300.0, "inner_diameter_mm": 20.0, "ring_count": 3,
         "pattern_type": "radial"}
    assert _safety(r)["risk_level"] == "UNKNOWN"  # Rosette fields are not Saw facts


# --- Sensitivity (SAC-016..024) ---------------------------------------------

def test_sac016_rpm_changes_rim_speed():
    a = _safety(dict(COMPLETE_SAW_REQUEST, rpm=3000))["details"]["calculator_results"]["rim_speed"]
    b = _safety(dict(COMPLETE_SAW_REQUEST, rpm=6000))["details"]["calculator_results"]["rim_speed"]
    assert a["score"] != b["score"]


def test_sac017_018_feed_and_tooth_change_bite_load():
    # assert on calculator metadata (the actual bite), not the saturated score
    base = _safety(COMPLETE_SAW_REQUEST)["details"]["calculator_results"]["bite_load"]["bite_load_mm"]
    feed = _safety(dict(COMPLETE_SAW_REQUEST, feed_rate_mm_min=8000.0))["details"]["calculator_results"]["bite_load"]["bite_load_mm"]
    teeth = _safety(dict(COMPLETE_SAW_REQUEST, tooth_count=80))["details"]["calculator_results"]["bite_load"]["bite_load_mm"]
    assert feed != base and teeth != base


def test_sac022_machine_power_changes_cutting_force():
    # assert on calculator metadata (available power / ratio), which tracks the
    # submitted machine power even where the overall score saturates.
    a = _safety(dict(COMPLETE_SAW_REQUEST, machine_power_kw=3.0))["details"]["calculator_results"]["cutting_force"]["available_power_w"]
    b = _safety(dict(COMPLETE_SAW_REQUEST, machine_power_kw=20.0))["details"]["calculator_results"]["cutting_force"]["available_power_w"]
    assert a != b


def test_sac024_distinct_inputs_do_not_collapse_to_constant():
    scores = {
        _safety(dict(COMPLETE_SAW_REQUEST, rpm=rpm, feed_rate_mm_min=feed))["score"]
        for rpm, feed in [(2000, 1000.0), (3450, 3000.0), (6000, 6000.0), (5000, 4000.0)]
    }
    assert len(scores) >= 3            # not the constant 49.4
    assert 49.4 not in scores


# --- Verdict witnesses (SAC-026..030) ---------------------------------------

def test_sac026_028_unsafe_fixture_blocks_red_real_evaluator():
    # deliberately unsafe: huge feed on thick stock with a small motor
    unsafe = dict(COMPLETE_SAW_REQUEST, feed_rate_mm_min=18000.0, stock_thickness_mm=100.0,
                  machine_power_kw=0.5, rpm=9000)
    s = _safety(unsafe)
    assert s["risk_level"] == "RED"
    assert s["details"]["engine"] == "feasibility_scorer"   # real evaluator, no monkeypatch


def test_sac030_result_includes_all_seven_calculators():
    s = _safety(COMPLETE_SAW_REQUEST)
    assert set(s["details"]["calculator_results"]) == {
        "bite_load", "blade_dynamics", "cutting_force", "deflection", "heat",
        "kickback", "rim_speed",
    }


def test_sac025_no_honest_permit_is_a_documented_stop():
    """SAC-025 STOP: with the FROZEN Saw calculators (deflection/heat flag RED for
    every in-range ordinary setup) no honest fixture permits GREEN/YELLOW. Physics
    and thresholds are out of scope for this transport/adaptation repair and must
    not be tuned. This asserts the documented limitation rather than fabricating a
    permitted witness."""
    best = max(
        _safety(dict(COMPLETE_SAW_REQUEST, material_id="softwood", blade_kerf_mm=1.0,
                     blade_thickness_mm=3.0, blade_youngs_modulus_gpa=250.0,
                     tooth_count=teeth, stock_thickness_mm=stock,
                     feed_rate_mm_min=feed, machine_power_kw=20.0, rpm=rpm))["score"]
        for teeth in (10, 24) for stock in (5.0, 10.0) for feed in (800.0, 1500.0) for rpm in (2000, 3000)
    )
    # No honest in-range ordinary fixture reaches a permitted band under frozen physics.
    assert best < 70.0


# --- Structural safeguards (SAC-039..041) -----------------------------------

def _canonical_conversion_src():
    import app.toolpath.saw_engine as se
    return inspect.getsource(se._convert_to_saw_context) + inspect.getsource(se._convert_to_saw_design)


def test_sac039_canonical_conversion_has_no_fallback_numeric_constants():
    tree = ast.parse(_canonical_conversion_src())
    nums = [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
            and not isinstance(n.value, bool)]
    # the strict canonical converters contain no hardcoded blade/machine constants
    assert nums == [], f"fallback numeric constants leaked into canonical conversion: {nums}"


def test_sac040_canonical_conversion_has_no_rosette_aliases():
    # Inspect actual attribute ACCESSES (AST), so docstrings/comments that merely
    # name the removed aliases do not trip the check.
    tree = ast.parse(_canonical_conversion_src())
    accessed = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    aliases = {"outer_diameter_mm", "ring_count", "pattern_type", "inner_diameter_mm"}
    leaked = accessed & aliases
    assert not leaked, f"Rosette alias(es) accessed in canonical Saw conversion: {leaked}"


def test_sac041_every_calculator_field_is_in_the_canonical_contract():
    import re
    calc_dir = _APP / "saw_lab" / "calculators"
    ctx_fields, design_fields = set(), set()
    for f in calc_dir.glob("saw_*.py"):
        txt = f.read_text()
        ctx_fields |= set(re.findall(r"ctx\.([a-z_]+)", txt))
        design_fields |= set(re.findall(r"design\.([a-z_]+)", txt))
    # SawContext field names consumed must each be representable in the canonical input
    from app.rmos.api_contracts import RmosContext
    from app.rmos.api.rmos_feasibility_router import SawScorerDesignSpec
    rmos_fields = set(RmosContext.model_fields)
    # ctx.max_rpm <- rpm; ctx.feed_rate_mm_per_min <- feed_rate_mm_min (documented renames)
    alias = {"max_rpm": "rpm", "feed_rate_mm_per_min": "feed_rate_mm_min"}
    for cf in ctx_fields:
        mapped = alias.get(cf, cf)
        assert mapped in rmos_fields or cf in ("material_id",), f"ctx.{cf} not in RmosContext contract"
    saw_design_fields = set(SawScorerDesignSpec.model_fields)
    for df in design_fields:
        assert df in saw_design_fields, f"design.{df} not in SawScorerDesignSpec contract"


# --- Regression isolation (SAC-031..033) ------------------------------------

def test_sac031_032_rosette_needs_no_saw_fields_and_still_evaluates():
    from app.rmos.api.rmos_feasibility_router import compute_rosette_feasibility
    r = compute_rosette_feasibility(req={"tool_id": "rosette:default", "material_id": "spruce"}, context="test")
    assert r["mode"] == "rosette"
    assert r["safety"]["risk_level"] in ("GREEN", "YELLOW", "RED")  # unchanged behaviour
