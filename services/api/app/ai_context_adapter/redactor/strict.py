# services/api/app/ai_context_adapter/redactor/strict.py
"""
Strict redaction for AI context envelope.

Removes all forbidden fields (manufacturing secrets, PII, pedagogy)
and ensures the envelope conforms to v1 redaction rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


# Forbidden keys - these MUST NOT appear in AI context
FORBIDDEN_KEYS = frozenset({
    # Manufacturing / CAM secrets
    "gcode",
    "toolpaths",
    "toolpath",
    "toolpath_data",
    "path_data",
    "trajectory",
    "post_processor",
    "feeds_and_speeds",
    "feed_rate",
    "spindle_speed",
    "machine_profile",
    "fixture_offsets",
    "nc_code",
    "ngc",
    # Obvious PII / pedagogy identifiers
    "player_id",
    "account_id",
    "lesson_id",
    "practice_session_id",
    "coach_feedback",
    "email",
    "phone",
    "ssn",
    "password",
    "api_key",
    "token",
    "secret",
    "credential",
    "private_key",
})


def _walk_and_scrub(obj: Any, warnings: List[str], path: str = "") -> Any:
    """
    Recursively walk object and remove forbidden keys.

    Returns a new object with forbidden keys removed.
    Appends warnings for each removed key.
    """
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            key = str(k).lower()
            p = f"{path}.{k}" if path else k

            # Check if key matches forbidden patterns
            if key in FORBIDDEN_KEYS:
                warnings.append(f"Removed forbidden field: {p}")
                continue

            # Check for partial matches (e.g., "toolpath_data")
            forbidden_match = False
            for forbidden in FORBIDDEN_KEYS:
                if forbidden in key:
                    warnings.append(f"Removed forbidden field (partial match): {p}")
                    forbidden_match = True
                    break

            if forbidden_match:
                continue

            out[k] = _walk_and_scrub(v, warnings, p)
        return out

    if isinstance(obj, list):
        return [_walk_and_scrub(x, warnings, f"{path}[]") for x in obj]

    return obj


@dataclass
class RedactionResult:
    """Result of strict redaction."""

    redacted: Dict[str, Any]
    warnings: List[str]


def redact_strict(envelope: Dict[str, Any]) -> RedactionResult:
    """
    Apply strict redaction to an envelope.

    - Removes all forbidden keys recursively
    - Hard-pins redaction metadata
    - Returns warnings for each removed field

    Args:
        envelope: Raw envelope dict

    Returns:
        RedactionResult with redacted envelope and warnings
    """
    warnings: List[str] = []
    redacted = _walk_and_scrub(envelope, warnings)

    # Hard-pin redaction metadata (belt + suspenders)
    redacted.setdefault("redaction", {})
    redacted["redaction"]["mode"] = "strict"
    redacted["redaction"]["ruleset"] = "toolbox_ai_redaction_strict_v1"
    redacted["redaction"]["warnings"] = warnings[:200]  # Cap warnings

    return RedactionResult(redacted=redacted, warnings=warnings)
