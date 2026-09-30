"""
RMOS-CONVERGE-001A - Saw evaluator plumbing repair (order 006).

Witnesses that the truthful saw process facts a caller supplies actually reach
the Saw calculators, instead of being dropped so that the evaluator scores on
hardcoded conversion defaults.

The defect these tests are born from
------------------------------------
``_score_via_scorer`` already forwarded ``rpm`` / ``feed_rate_mm_min`` /
``spindle_power_watts`` / ``tool_diameter_mm`` into ``RmosContext``, but those
fields were undeclared on the model. Under pydantic v2's default
``extra='ignore'`` they were silently dropped, and ``_convert_to_saw_context``
then hardcoded ``max_rpm=5000`` / ``feed_rate=3000`` and read blade geometry
only from the tool_id string. So the Saw evaluator produced the same verdict
regardless of the request - a manufacturing-authority defect, because a lane
that cannot see its own process facts is not evaluating the cut it was asked
about.

Scope note (availability regression is a *formula* defect, not plumbing)
------------------------------------------------------------------------
This increment repairs plumbing only. It does not touch calculator formulas,
thresholds or defaults. With the facts now delivered, no ordinary in-range job
yet earns a permitting verdict: the ``app.saw_lab.calculators`` bundle uses a
specific-cutting-energy default of 30 J/mm^3 - roughly three orders of
magnitude above the physical value for wood (~0.02-0.05 J/mm^3) - which drives
the heat and deflection calculators into RED for every realistic cut. A
9,600-point sweep across the full in-range parameter space produced zero
GREEN/YELLOW verdicts. That is a separate formula/units defect, out of scope
here and reported for a follow-up increment. These witnesses therefore assert
the in-scope guarantees:

* truthful facts reach the calculators (metadata reflects the request);
* a safety-critical fact that changes shifts the calculator that consumes it;
* an omitted safety-critical fact fails closed to UNKNOWN (no default scoring);
* an out-of-range fact fails closed to ERROR (no silent clamp to a default);
* a genuinely unsafe, input-driven cut blocks.
"""

from __future__ import annotations

import pytest

from app.rmos.api.rmos_feasibility_router import compute_saw_feasibility
from app.rmos.api.saw_feasibility import _SAW_REQUIRED_KEYS
from app.rmos.feasibility_authority import ENGINE_ERROR, ENGINE_UNAVAILABLE


# An ordinary bench-saw cut: 10" (254 mm) 24-tooth blade at 3450 RPM, 3 m/min
# feed, 25 mm hardwood, on a 3 kW spindle. Every value is inside the calculator
# bundle's own declared ranges.
ORDINARY_SAW = {
    "tool_id": "saw:default",
    "material_id": "hardwood",
    "rpm": 3450,
    "feed_rate_mm_min": 3000.0,
    "tool_diameter_mm": 254.0,
    "tooth_count": 24,
    "stock_thickness_mm": 25.0,
    "spindle_power_watts": 3000.0,
}


def _saw(**overrides) -> dict:
    req = dict(ORDINARY_SAW)
    req.update(overrides)
    return compute_saw_feasibility(req=req, context="test")


def _calc(result: dict, name: str) -> dict:
    # SawEngine flattens each calculator's metadata alongside ``score`` and
    # ``warning`` into one dict, so metadata keys are read directly.
    return result["safety"]["details"]["calculator_results"][name]


# ---------------------------------------------------------------------------
# Facts reach the calculators
# ---------------------------------------------------------------------------

def test_ordinary_saw_request_reaches_the_saw_calculators():
    """The saw lane runs the saw calculator bundle on the supplied facts."""
    result = _saw()
    safety = result["safety"]

    assert result["mode"] == "saw"
    assert safety["details"]["engine"] == "feasibility_scorer"

    calc = safety["details"]["calculator_results"]
    # The seven saw calculators, not the router calculator set.
    assert {
        "heat",
        "deflection",
        "rim_speed",
        "bite_load",
        "kickback",
        "cutting_force",
        "blade_dynamics",
    } <= set(calc)


def test_supplied_facts_are_the_values_the_calculators_use():
    """
    Calculator metadata echoes the request facts verbatim - proof the values
    are consumed, not dropped in favour of the old 5000 RPM / 3000 mm-min
    conversion defaults.
    """
    result = _saw(rpm=4200, feed_rate_mm_min=2400.0, tool_diameter_mm=300.0,
                  tooth_count=40, spindle_power_watts=5000.0)

    rim = _calc(result, "rim_speed")
    assert rim["current_rpm"] == 4200
    assert rim["blade_diameter_mm"] == 300.0

    bite = _calc(result, "bite_load")
    assert bite["rpm"] == 4200
    assert bite["tooth_count"] == 40
    assert bite["current_feed_mm_per_min"] == 2400.0

    # Available power is machine power * motor efficiency (0.85): 5000 * 0.85.
    force = _calc(result, "cutting_force")
    assert force["available_power_w"] == pytest.approx(4250.0, rel=1e-6)


# ---------------------------------------------------------------------------
# A fact that changes moves the calculator that consumes it (sensitivity)
# ---------------------------------------------------------------------------

def test_rpm_and_diameter_change_rim_speed_score():
    """
    Rim speed is pi*D*RPM. A modest 254 mm blade at 3450 RPM sits in the safe
    band (score 100); a 600 mm blade at 9000 RPM is a rim-overspeed hazard
    (score collapses). If the facts were still dropped, both would be identical.
    """
    safe = _calc(_saw(tool_diameter_mm=254.0, rpm=3450), "rim_speed")
    fast = _calc(_saw(tool_diameter_mm=600.0, rpm=9000), "rim_speed")

    assert safe["score"] == 100.0
    assert fast["score"] < safe["score"]
    assert fast["rim_speed_m_s"] > safe["rim_speed_m_s"]


def test_feed_rate_changes_bite_load():
    """Bite per tooth = feed / (rpm * teeth); raising feed raises the bite."""
    low = _calc(_saw(feed_rate_mm_min=1000.0), "bite_load")
    high = _calc(_saw(feed_rate_mm_min=8000.0), "bite_load")

    assert high["bite_load_mm"] > low["bite_load_mm"]


def test_spindle_power_changes_cutting_force_power_ratio():
    """A bigger spindle lowers the required-vs-available power ratio."""
    small = _calc(_saw(spindle_power_watts=2000.0), "cutting_force")
    big = _calc(_saw(spindle_power_watts=12000.0), "cutting_force")

    assert big["power_ratio"] < small["power_ratio"]


# ---------------------------------------------------------------------------
# Missing safety-critical facts fail closed to UNKNOWN (no default scoring)
# ---------------------------------------------------------------------------

def test_each_missing_safety_critical_fact_yields_unknown_not_a_default_score():
    """
    Dropping any one required fact must produce a blocking UNKNOWN naming the
    absent fact - never a score computed on a substituted default.
    """
    for key in _SAW_REQUIRED_KEYS:
        req = dict(ORDINARY_SAW)
        req.pop(key)
        result = compute_saw_feasibility(req=req, context="test")
        safety = result["safety"]

        assert safety["risk_level"] == "UNKNOWN", key
        assert safety["score"] is None, key
        assert safety["details"]["code"] == ENGINE_UNAVAILABLE, key
        assert key in safety["block_reason"], key


def test_no_facts_at_all_is_unknown_not_scored():
    """The bare saw request (tool_id only) is UNKNOWN, not a default verdict."""
    result = compute_saw_feasibility(
        req={"tool_id": "saw:default", "material_id": "hardwood"}, context="test"
    )
    assert result["safety"]["risk_level"] == "UNKNOWN"
    assert result["safety"]["score"] is None
    assert result["safety"]["details"]["code"] == ENGINE_UNAVAILABLE


# ---------------------------------------------------------------------------
# An out-of-range fact fails closed to ERROR (no silent clamp to a default)
# ---------------------------------------------------------------------------

def test_out_of_range_rpm_fails_closed_to_error():
    """
    An RPM the SawContext rejects (> 10000) means the evaluator could not run
    on the requested value. It blocks as ERROR rather than being clamped to a
    default or escaping as an unhandled 500.
    """
    result = _saw(rpm=50000)
    safety = result["safety"]

    assert safety["risk_level"] == "ERROR"
    assert safety["details"]["code"] == ENGINE_ERROR


# ---------------------------------------------------------------------------
# A genuinely unsafe, input-driven cut blocks
# ---------------------------------------------------------------------------

def test_rim_overspeed_cut_blocks_red():
    """
    A 600 mm blade spun at 9000 RPM is a rim-overspeed hazard. The verdict is
    RED and it is reached *through* the supplied facts - the rim-speed
    calculator names the excessive speed.
    """
    result = _saw(tool_diameter_mm=600.0, rpm=9000)
    assert result["safety"]["risk_level"] == "RED"

    rim = _calc(result, "rim_speed")
    assert rim["score"] < 30
    assert "rim speed" in (rim["warning"] or "").lower()


# ---------------------------------------------------------------------------
# Availability boundary (documented; out-of-scope formula defect)
# ---------------------------------------------------------------------------

def test_ordinary_job_still_blocks_pending_out_of_scope_formula_fix():
    """
    Documents the availability boundary this increment deliberately does NOT
    cross. With the facts now correctly delivered, an ordinary cut still blocks
    RED, and the cause is two calculator-model defects that live in the formula
    layer this plumbing increment is not allowed to change:

    1. Specific cutting energy. The heat/deflection/cutting_force calculators
       use a hardcoded 30 J/mm^3 (MaterialProperties defaults to 30, "hardwood
       ~40") and the bundle never passes material. The repository's own
       governed material DB - app/data_registry/system/materials/
       wood_species.json - lists specific_cutting_energy_j_per_mm3 at
       0.22-0.87 J/mm^3 per species, ~35-140x lower. Worse,
       MaterialProperties.specific_cutting_energy_j_per_mm3 is bounded ge=5.0,
       so the model rejects the repo's own truthful values outright: the fact
       cannot even be wired in without recalibrating the model's bounds,
       default, and the formulas tuned around them.
    2. Deflection. Even with a truthful ~0.35 J/mm^3 forced in (physics only),
       deflection still scores ~20 (<30) because its effective-width term
       collapses the blade's second moment of area - an independent defect.

    Both are out of scope for a plumbing repair. This test pins the current
    behaviour and its cause; when the formula/units defects are fixed in a
    later increment it will fail here and flag the change for re-baselining.
    """
    result = _saw()
    calc = result["safety"]["details"]["calculator_results"]

    # The block is driven by heat/deflection, not by a missing/dropped fact.
    assert result["safety"]["risk_level"] == "RED"
    assert calc["heat"]["score"] < 30
    assert calc["deflection"]["score"] < 30

    # And the in-range facts that are NOT dominated by the kc default score fine,
    # confirming the plumbing itself is sound.
    assert calc["rim_speed"]["score"] == 100.0
    assert calc["bite_load"]["score"] >= 50.0
