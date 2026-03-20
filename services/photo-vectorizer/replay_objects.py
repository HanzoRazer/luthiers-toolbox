from __future__ import annotations

from typing import Any, Dict, Optional

from body_isolation_result import BodyIsolationResult
from photo_vectorizer_v2 import ContourStageResult


def as_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def hydrate_body_result(
    base: BodyIsolationResult,
    payload: Dict[str, Any],
) -> BodyIsolationResult:
    """
    Enrich a concrete BodyIsolationResult with serialized replay diagnostics.
    """
    base.diagnostics = {
        **(getattr(base, "diagnostics", {}) or {}),
        **dict(payload.get("body_result", {}).get("diagnostics", {}) or {}),
    }
    return base


def make_contour_stage_result(payload: Dict[str, Any]) -> ContourStageResult:
    """
    Build a concrete ContourStageResult from serialized replay payload.
    """
    contour_payload = dict(payload["contour_result"] or {})
    contour_payload["diagnostics"] = {
        "retry_attempts": list(payload.get("diagnostics", {}).get("retry_attempts", []) or []),
        **dict(contour_payload.get("diagnostics", {}) or {}),
    }
    result = ContourStageResult.from_payload(contour_payload)
    return result


def advance_contour_stage_result(
    result: ContourStageResult,
    *,
    score_after: Any,
    ownership_score_after: Any,
    ownership_ok_after: Any,
    retry_profile_used: Any,
    retry_iteration: int,
) -> ContourStageResult:
    """
    Mutate a concrete replay contour object to the next serialized retry state.
    """
    result.best_score = float(score_after)
    result.ownership_score = ownership_score_after
    result.ownership_ok = as_bool(ownership_ok_after)
    result.export_block_issues = []
    result.export_blocked = False
    result.block_reason = None
    result.recommended_next_action = None
    result.elected_source = "pre_merge_guarded"
    result.diagnostics = {
        **(getattr(result, "diagnostics", {}) or {}),
        "ownership_score": result.ownership_score,
        "ownership_ok": result.ownership_ok,
        "replay_retry_iteration": retry_iteration,
        "replay_retry_profile_used": retry_profile_used,
    }
    if result.ownership_ok is False and result.ownership_score is not None:
        result.export_block_issues.append(
            f"body ownership weak ({float(result.ownership_score):.2f})"
        )
    return result
