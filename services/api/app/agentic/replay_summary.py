from __future__ import annotations

from typing import Any, Dict, List, Optional


def summarize_retry_attempts(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute tiny summary metrics from a serialized extraction/replay payload.

    Expected payload shape:
      payload["contour_stage"]["diagnostics"]["retry_attempts"] -> List[dict]

    Returns:
      {
        "retry_count": int,
        "final_score_delta": float,
        "last_retry_profile_used": Optional[str],
        "retry_profiles_used": List[Optional[str]],
      }

    Behavior:
      - If no retry_attempts exist, returns zero/None defaults
      - If score values are malformed, raises ValueError
    """
    retry_attempts = (
        payload.get("contour_stage", {})
        .get("diagnostics", {})
        .get("retry_attempts", [])
    )

    if not retry_attempts:
        return {
            "retry_count": 0,
            "final_score_delta": 0.0,
            "last_retry_profile_used": None,
            "retry_profiles_used": [],
        }

    first = retry_attempts[0]
    last = retry_attempts[-1]
    retry_profiles_used = [attempt.get("retry_profile_used") for attempt in retry_attempts]

    try:
        score_before = float(first["score_before"])
        score_after = float(last["score_after"])
    except KeyError as e:
        raise ValueError(f"Missing retry summary key: {e.args[0]}") from e
    except (TypeError, ValueError) as e:
        raise ValueError("Retry summary score fields must be numeric") from e

    return {
        "retry_count": len(retry_attempts),
        "final_score_delta": score_after - score_before,
        "last_retry_profile_used": last.get("retry_profile_used"),
        "retry_profiles_used": retry_profiles_used,
    }
