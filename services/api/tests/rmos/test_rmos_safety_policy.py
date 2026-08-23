"""
RMOS-CONVERGE-001A - SafetyPolicy remains the gate, and remains fail-closed.

Acceptance witnesses TC-10 .. TC-13.

The audit found the gate itself sound; the defect was the authority handed
to it. Nothing in ``safety_policy.py`` is changed by this increment, so
these are regression witnesses: they pin the fail-closed posture against the
two new non-authorizing results (``UNKNOWN`` from an unavailable engine,
``ERROR`` from a failing one) that the cutover now routes through it.

Note: a broader ``SafetyPolicy`` unit suite exists at
``app/tests/rmos/test_safety_policy.py``, but ``pytest.ini`` sets
``testpaths = tests`` so it is never collected. That collection gap is
recorded in the audit addendum; this file covers the gate behaviour this
increment depends on, in a location that actually runs.
"""

from __future__ import annotations

import pytest

from app.rmos.feasibility_authority import error_feasibility, unavailable_feasibility
from app.rmos.policies import SafetyPolicy
from app.rmos.policies.safety_policy import RiskLevel


# ---------------------------------------------------------------------------
# TC-10 .. TC-13
# ---------------------------------------------------------------------------

def test_tc10_green_is_allowed():
    """TC-10: GREEN allows the operation."""
    decision = SafetyPolicy.extract_safety_decision({"safety": {"risk_level": "GREEN"}})
    assert decision.risk_level is RiskLevel.GREEN
    assert SafetyPolicy.should_block(decision.risk_level) is False


def test_yellow_is_allowed_but_carries_its_warnings():
    """YELLOW proceeds under the review policy; it is not silently GREEN."""
    decision = SafetyPolicy.extract_safety_decision(
        {"safety": {"risk_level": "YELLOW", "warnings": ["heat risk"]}}
    )
    assert decision.risk_level is RiskLevel.YELLOW
    assert SafetyPolicy.should_block(decision.risk_level) is False
    assert decision.warnings == ["heat risk"]


def test_tc11_red_is_blocked():
    """TC-11: RED blocks."""
    decision = SafetyPolicy.extract_safety_decision({"safety": {"risk_level": "RED"}})
    assert decision.risk_level is RiskLevel.RED
    assert SafetyPolicy.should_block(decision.risk_level) is True


def test_tc12_unknown_is_blocked():
    """TC-12: UNKNOWN blocks."""
    decision = SafetyPolicy.extract_safety_decision({"safety": {"risk_level": "UNKNOWN"}})
    assert decision.risk_level is RiskLevel.UNKNOWN
    assert SafetyPolicy.should_block(decision.risk_level) is True


@pytest.mark.parametrize(
    "payload, label",
    [
        (None, "missing payload"),
        ("RED", "non-dict payload"),
        ({}, "empty payload"),
        ({"safety": {}}, "safety bag with no risk_level"),
        ({"safety": {"risk_level": ""}}, "blank risk_level"),
        ({"safety": {"risk_level": "DEFINITELY_FINE"}}, "unrecognised risk_level"),
        ({"safety": {"risk_level": None}}, "null risk_level"),
        ({"risk_level": 200}, "non-string risk_level"),
    ],
)
def test_tc13_malformed_safety_result_blocks(payload, label):
    """
    TC-13: an invalid or unparseable safety result blocks.

    The extractor never raises - it degrades to UNKNOWN, which the gate
    treats as blocking. An unreadable verdict is not an authorization.
    """
    decision = SafetyPolicy.extract_safety_decision(payload)
    assert decision.risk_level is RiskLevel.UNKNOWN, label
    assert SafetyPolicy.should_block(decision.risk_level) is True, label


# ---------------------------------------------------------------------------
# The gate against the cutover's new non-authorizing results
# ---------------------------------------------------------------------------

def test_engine_unavailable_result_blocks_at_the_gate():
    """An UNAVAILABLE engine result must be blocking end to end."""
    result = unavailable_feasibility(mode="vcarve", tool_id="vcarve:default", context="test")
    decision = SafetyPolicy.extract_safety_decision(result)

    assert decision.risk_level is RiskLevel.UNKNOWN
    assert SafetyPolicy.should_block(decision.risk_level) is True
    assert decision.block_reason


def test_engine_error_result_blocks_at_the_gate():
    """An ERROR engine result must be blocking end to end - never YELLOW."""
    result = error_feasibility(
        mode="saw", tool_id="saw:default", context="test", error=ValueError("boom")
    )
    decision = SafetyPolicy.extract_safety_decision(result)

    assert decision.risk_level is RiskLevel.ERROR
    assert SafetyPolicy.should_block(decision.risk_level) is True
    assert decision.block_reason


def test_error_level_is_never_treated_as_a_softer_yellow():
    """
    Regression guard for F3: the pre-cutover engines answered an evaluation
    failure with YELLOW so manufacturing would not be blocked. ERROR and
    YELLOW must not be interchangeable at the gate.
    """
    assert SafetyPolicy.should_block(RiskLevel.YELLOW) is False
    assert SafetyPolicy.should_block(RiskLevel.ERROR) is True
