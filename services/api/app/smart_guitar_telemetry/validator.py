"""
Validator for Smart Guitar -> ToolBox Telemetry v1

Gate enforcement:
1. Validates payload against schema
2. Hard-blocks forbidden player/pedagogy fields
3. Validates telemetry category is manufacturing-only
4. Validates metric structure
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .schemas import TelemetryPayload


# =============================================================================
# Forbidden Fields (Player/Pedagogy Data - Hard Block)
# =============================================================================

FORBIDDEN_FIELDS: Set[str] = frozenset({
    # Player identity
    "player_id",
    "account_id",
    "user_id",
    "email",
    "username",
    # Pedagogy / Teaching
    "lesson_id",
    "curriculum_id",
    "practice_session_id",
    "skill_level",
    "accuracy",
    "timing",
    # Musical content
    "midi",
    "audio",
    "recording_url",
    # Coaching
    "coach_feedback",
    "prompt_trace",
    "lesson_progress",
    "score",
    "grade",
    "evaluation",
})


# =============================================================================
# Validation Result
# =============================================================================


@dataclass
class TelemetryValidationResult:
    """Result of validating a telemetry payload."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    payload: Optional[TelemetryPayload] = None

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# =============================================================================
# Validation Functions
# =============================================================================


def _check_forbidden_fields(data: Dict[str, Any], path: str = "") -> List[str]:
    """
    Recursively check for forbidden fields in the payload.

    Returns list of error messages for any forbidden fields found.
    """
    errors = []

    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key

        # Check if this key is forbidden
        if key.lower() in FORBIDDEN_FIELDS:
            errors.append(
                f"Forbidden field '{key}' at '{current_path}': "
                "Player/pedagogy data must not cross the boundary"
            )

        # Recurse into nested objects
        if isinstance(value, dict):
            errors.extend(_check_forbidden_fields(value, current_path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    errors.extend(_check_forbidden_fields(item, f"{current_path}[{i}]"))

    return errors


def validate_telemetry(payload_dict: Dict[str, Any]) -> TelemetryValidationResult:
    """
    Validate a telemetry payload dictionary against the schema.

    Checks:
    1. No forbidden player/pedagogy fields (hard block)
    2. Valid schema structure (Pydantic validation)
    3. Valid telemetry category
    4. Valid metric structure
    """
    result = TelemetryValidationResult(valid=True)

    # 1) Check for forbidden fields FIRST (hard block)
    forbidden_errors = _check_forbidden_fields(payload_dict)
    for err in forbidden_errors:
        result.add_error(err)

    if forbidden_errors:
        # Don't bother with further validation if forbidden fields present
        return result

    # 2) Parse with Pydantic (validates schema)
    try:
        payload = TelemetryPayload.model_validate(payload_dict)
        result.payload = payload
    except Exception as e:
        result.add_error(f"Schema validation failed: {e}")
        return result

    # 3) Validate telemetry category (already enforced by enum, but log for audit)
    valid_categories = {"utilization", "hardware_performance", "environment", "lifecycle"}
    if payload.telemetry_category.value not in valid_categories:
        result.add_error(
            f"Invalid telemetry_category '{payload.telemetry_category}': "
            f"must be one of {valid_categories}"
        )

    # 4) Validate metrics have at least one entry
    if not payload.metrics:
        result.add_error("Payload must contain at least one metric")

    # 5) Hard-block forbidden terms in metric keys (prevents smuggling)
    # This catches attempts to hide pedagogy data in metric names like
    # "player_id_hash", "lesson_progress_count", "accuracy_pct", etc.
    # We check if the forbidden term appears as a complete segment (word boundary aware)
    for metric_key in payload.metrics.keys():
        metric_key_lower = metric_key.lower()
        # Split into segments to avoid false positives like "humidity" matching "midi"
        segments = metric_key_lower.split("_")
        for forbidden in FORBIDDEN_FIELDS:
            # Check if forbidden term matches as complete segment(s)
            forbidden_parts = forbidden.split("_")
            # Check for exact segment match or segment prefix/suffix
            for i in range(len(segments)):
                # Check if forbidden_parts match starting at position i
                if i + len(forbidden_parts) <= len(segments):
                    if segments[i:i + len(forbidden_parts)] == forbidden_parts:
                        result.add_error(
                            f"Forbidden metric key '{metric_key}': "
                            f"contains blocked term '{forbidden}' (pedagogy data boundary violation)"
                        )
                        break
            else:
                continue
            break  # Already found a match for this metric key

    # 6) Warning for suspiciously teaching-like metric names
    # (softer patterns that might indicate pedagogy data but aren't hard-blocked)
    suspicious_patterns = ["practice", "skill", "progress", "performance_score"]
    for metric_name in payload.metrics.keys():
        for pattern in suspicious_patterns:
            if pattern in metric_name.lower():
                # Don't warn if already hard-blocked
                already_blocked = any(f in metric_name.lower() for f in FORBIDDEN_FIELDS)
                if not already_blocked:
                    result.add_warning(
                        f"Suspicious metric name '{metric_name}': "
                        "review for potential pedagogy data"
                    )

    return result


def validate_telemetry_json(json_str: str) -> TelemetryValidationResult:
    """Validate telemetry from JSON string."""
    try:
        payload_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        result = TelemetryValidationResult(valid=False)
        result.add_error(f"Invalid JSON: {e}")
        return result
    return validate_telemetry(payload_dict)


def validate_telemetry_file(file_path: Path) -> TelemetryValidationResult:
    """Validate telemetry from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload_dict = json.load(f)
    except FileNotFoundError:
        result = TelemetryValidationResult(valid=False)
        result.add_error(f"File not found: {file_path}")
        return result
    except json.JSONDecodeError as e:
        result = TelemetryValidationResult(valid=False)
        result.add_error(f"Invalid JSON in {file_path}: {e}")
        return result

    return validate_telemetry(payload_dict)
