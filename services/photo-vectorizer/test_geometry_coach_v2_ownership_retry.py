from types import SimpleNamespace

from body_isolation_stage import BodyIsolationParams
from geometry_coach_v2 import CoachV2Config, GeometryCoachV2


def _body(profile="default", completeness_score=0.50):
    return SimpleNamespace(
        profile=profile,
        completeness_score=completeness_score,
        body_region=None,
        lower_bout_missing_likely=False,
        border_contact_likely=False,
        score_breakdown=SimpleNamespace(border_contact_penalty=0.0),
    )


def _contour(best_score=0.75, ownership_score=0.40):
    return SimpleNamespace(
        best_score=best_score,
        ownership_score=ownership_score,
        diagnostics={"ownership_score": ownership_score},
        elected_source="pre_merge",
    )


def test_decide_forces_body_region_expansion_when_ownership_fails():
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            ownership_retry_threshold=0.60,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
                BodyIsolationParams(profile="body_region_expansion"),
            ],
            contour_retry_profiles=[],
        )
    )

    decision = coach.decide(
        body_result=_body(profile="default"),
        contour_result=_contour(ownership_score=0.41),
        retry_count=0,
    )

    assert decision.action == "rerun_body_isolation"
    assert decision.body_retry_params.profile == "body_region_expansion"
    assert "ownership gate" in decision.reason.lower()


def test_decide_requires_manual_review_when_ownership_fails_and_budget_exhausted():
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=1,
            ownership_retry_threshold=0.60,
            body_retry_profiles=[BodyIsolationParams(profile="body_region_expansion")],
            contour_retry_profiles=[],
        )
    )

    decision = coach.decide(
        body_result=_body(profile="body_region_expansion"),
        contour_result=_contour(ownership_score=0.32),
        retry_count=1,
    )

    assert decision.action == "manual_review_required"
    assert "ownership gate" in decision.reason.lower()
