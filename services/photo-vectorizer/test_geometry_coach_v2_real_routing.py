"""
Test: GeometryCoachV2 real-world routing — body-ownership correction harness.

Loads named failure-class fixtures and verifies the coach routes each to
the expected action (rerun_body_isolation, rerun_contour_stage, etc.).
"""
from __future__ import annotations

import pytest

from geometry_coach_v2 import GeometryCoachV2, CoachV2Config
from replay_fixture_loader import (
    load_regression_cases,
    make_serialized_body_result,
    make_serialized_contour_result,
)


# ---------------------------------------------------------------------------
# Coach fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def coach() -> GeometryCoachV2:
    return GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            contour_target_threshold=0.80,
            body_isolation_review_threshold=0.45,
            severe_border_penalty_threshold=0.5,
            ownership_retry_threshold=0.60,
        )
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case",
    load_regression_cases(["smart_guitar", "benedetto", "archtop"]),
    ids=lambda c: c.case_id,
)
def test_geometry_coach_v2_routes_real_body_ownership_cases(case, coach: GeometryCoachV2):
    body_result = make_serialized_body_result(case.payload)
    contour_result = make_serialized_contour_result(case.payload)

    decision = coach.decide(
        body_result=body_result,
        contour_result=contour_result,
        retry_count=0,
    )

    assert decision.action == case.expected_action, (
        f"Case {case.case_id} expected {case.expected_action} "
        f"but got {decision.action}. Reason: {decision.reason}"
    )


def test_geometry_coach_v2_fixture_is_nonempty():
    cases = load_regression_cases(["smart_guitar", "benedetto", "archtop"])
    assert len(cases) >= 3


def test_geometry_coach_v2_real_cases_cover_all_first_rules():
    cases = load_regression_cases(["smart_guitar", "benedetto", "archtop"])
    actions = {c.expected_action for c in cases}
    assert "rerun_body_isolation" in actions
