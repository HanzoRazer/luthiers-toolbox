from __future__ import annotations

from typing import Any, Dict, List, Optional


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> Optional[bool]:
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


def _retry_attempts(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    diagnostics = payload.get("diagnostics", {}) or {}
    attempts = diagnostics.get("retry_attempts", [])
    if not isinstance(attempts, list):
        return []
    return [a for a in attempts if isinstance(a, dict)]


def summarize_retry_attempts(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarize retry trajectory from a serialized contour-stage payload.

    Preserves legacy summary keys and adds ownership trajectory fields so
    replay analysis can distinguish "score changed" from "body ownership fixed".
    """
    attempts = _retry_attempts(payload)

    retry_profiles_used: List[Optional[str]] = []
    final_score_delta = 0.0
    last_retry_profile_used: Optional[str] = None

    ownership_scores_before: List[Optional[float]] = []
    ownership_scores_after: List[Optional[float]] = []
    ownership_ok_before: List[Optional[bool]] = []
    ownership_ok_after: List[Optional[bool]] = []

    for attempt in attempts:
        profile = attempt.get("retry_profile_used")
        profile = profile if profile is None or isinstance(profile, str) else None
        retry_profiles_used.append(profile)
        if profile is not None:
            last_retry_profile_used = profile

        score_delta = _safe_float(attempt.get("score_delta"))
        if score_delta is not None:
            final_score_delta += score_delta

        ownership_scores_before.append(_safe_float(attempt.get("ownership_score_before")))
        ownership_scores_after.append(_safe_float(attempt.get("ownership_score_after")))
        ownership_ok_before.append(_safe_bool(attempt.get("ownership_ok_before")))
        ownership_ok_after.append(_safe_bool(attempt.get("ownership_ok_after")))

    first_ownership_score_before = next((v for v in ownership_scores_before if v is not None), None)
    final_ownership_score = next((v for v in reversed(ownership_scores_after) if v is not None), None)
    final_ownership_ok = next((v for v in reversed(ownership_ok_after) if v is not None), None)
    # Count retries whose *result* still failed ownership. This lets replay
    # review distinguish "initial failure that got fixed" from "persistent
    # failure that never cleared."
    ownership_failures = sum(1 for v in ownership_ok_after if v is False)

    ownership_score_delta = None
    if first_ownership_score_before is not None and final_ownership_score is not None:
        ownership_score_delta = final_ownership_score - first_ownership_score_before

    return {
        "retry_count": len(attempts),
        "final_score_delta": final_score_delta,
        "last_retry_profile_used": last_retry_profile_used,
        "retry_profiles_used": retry_profiles_used,
        "first_ownership_score_before": first_ownership_score_before,
        "final_ownership_score": final_ownership_score,
        "final_ownership_ok": final_ownership_ok,
        "ownership_score_delta": ownership_score_delta,
        "ownership_failures": ownership_failures,
    }
