from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from body_isolation_result import BodyIsolationResult
from body_isolation_stage import BodyIsolationParams
from geometry_coach_v2 import CoachV2Config, GeometryCoachV2
from replay_fixture_loader import (
    ReplayRegressionCase,
    load_regression_case,
    make_serialized_body_result,
    make_serialized_contour_result,
)
from replay_objects import advance_contour_stage_result
from replay_summary import summarize_retry_attempts


@dataclass
class ReplayExecutionResult:
    case: ReplayRegressionCase
    final_body_result: BodyIsolationResult
    final_contour_result: Any
    final_decision: Any
    summary: Dict[str, Any]


class _BodyStageReplayRunner:
    def __init__(self, case: ReplayRegressionCase, cursor: Dict[str, int]):
        self.case = case
        self.cursor = cursor

    def run(self, *args, **kwargs) -> BodyIsolationResult:
        payload = self.case.payload
        base = make_serialized_body_result(payload)
        idx = min(
            self.cursor["idx"],
            max(0, len(payload.get("diagnostics", {}).get("retry_attempts", [])) - 1),
        )
        attempts = payload.get("diagnostics", {}).get("retry_attempts", [])
        if attempts:
            attempt = attempts[idx]
            score_after = attempt.get("score_after")
            try:
                # Keep body score monotonic enough that contour improvement remains
                # the main acceptance signal while still reflecting a "better retry".
                base.completeness_score = max(
                    float(base.completeness_score),
                    min(float(score_after), 0.95),
                )
            except (TypeError, ValueError):
                pass
            profile = attempt.get("retry_profile_used")
            if isinstance(profile, str):
                base.recommended_next_action = profile
            base.diagnostics = {
                **(getattr(base, "diagnostics", {}) or {}),
                "replay_retry_iteration": idx + 1,
                "replay_retry_profile_used": profile,
            }
        return base


class _ContourStageReplayRunner:
    def __init__(self, case: ReplayRegressionCase, cursor: Dict[str, int]):
        self.case = case
        self.cursor = cursor

    def run(self, *args, **kwargs):
        payload = self.case.payload
        attempts = payload.get("diagnostics", {}).get("retry_attempts", [])
        idx = self.cursor["idx"]
        if idx >= len(attempts):
            # Defensive fallback: return the concrete serialized terminal contour.
            # Bump score just enough to pass accept_candidate so the loop can
            # reach the next decide() call (budget-exhaustion path).
            contour = make_serialized_contour_result(payload)
            last = attempts[-1] if attempts else {}
            base_score = float(
                last.get("score_after", payload["contour_result"]["best_score"])
            )
            contour.best_score = base_score + 0.04
            contour.ownership_score = last.get("ownership_score_after")
            contour.ownership_ok = last.get("ownership_ok_after")
            if contour.ownership_ok is False and contour.ownership_score is not None:
                contour.export_block_issues = [
                    f"body ownership weak ({float(contour.ownership_score):.2f})"
                ]
            self.cursor["idx"] += 1
            return contour

        attempt = attempts[idx]
        contour = make_serialized_contour_result(payload)
        contour = advance_contour_stage_result(
            contour,
            score_after=attempt.get("score_after", payload["contour_result"]["best_score"]),
            ownership_score_after=attempt.get("ownership_score_after"),
            ownership_ok_after=attempt.get("ownership_ok_after"),
            retry_profile_used=attempt.get("retry_profile_used"),
            retry_iteration=idx + 1,
        )
        self.cursor["idx"] += 1
        return contour


def build_replay_coach() -> GeometryCoachV2:
    return GeometryCoachV2(
        CoachV2Config(
            max_retries=3,
            epsilon=0.03,
            contour_target_threshold=0.80,
            body_isolation_review_threshold=0.45,
            severe_border_penalty_threshold=0.5,
            ownership_retry_threshold=0.60,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
                BodyIsolationParams(profile="border_suppression"),
                BodyIsolationParams(profile="body_region_expansion"),
            ],
            contour_retry_profiles=[],
        )
    )


def execute_regression_case(
    case_id: str,
    *,
    coach: Optional[GeometryCoachV2] = None,
) -> ReplayExecutionResult:
    case = load_regression_case(case_id)
    body_result = make_serialized_body_result(case.payload)
    contour_result = make_serialized_contour_result(case.payload)
    cursor = {"idx": 0}

    body_stage_runner = _BodyStageReplayRunner(case, cursor)
    contour_stage_runner = _ContourStageReplayRunner(case, cursor)
    coach = coach or build_replay_coach()

    final_body, final_contour, final_decision = coach.evaluate(
        body_stage_runner=body_stage_runner,
        contour_stage_runner=contour_stage_runner,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family=case.family,
        geometry_authority=None,
        contour_inputs={
            "edges": None,
            "alpha_mask": None,
            "calibration": type("_Cal", (), {"mm_per_pixel": 1.0})(),
            "family": case.family,
            "image_shape": (400, 300),
            "params": type("_Params", (), {})(),
        },
        body_result=body_result,
        contour_result=contour_result,
    )

    summary = summarize_retry_attempts(case.payload)

    return ReplayExecutionResult(
        case=case,
        final_body_result=final_body,
        final_contour_result=final_contour,
        final_decision=final_decision,
        summary=summary,
    )
