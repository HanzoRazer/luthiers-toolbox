"""
Gate tests for Smart Guitar -> ToolBox Telemetry v1

These tests enforce the telemetry contract boundary:
- Manufacturing-only telemetry (utilization, hardware, environment, lifecycle)
- NO player/pedagogy data
- NO teaching content
- Aggregatable metrics only
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.smart_guitar_telemetry import (
    validate_telemetry,
    validate_telemetry_json,
    TelemetryValidationResult,
    FORBIDDEN_FIELDS,
    TelemetryPayload,
    MetricValue,
    TelemetryCategory,
)
from app.smart_guitar_telemetry.validator import validate_telemetry_file


# =============================================================================
# Fixtures Path
# =============================================================================

FIXTURES_DIR = Path(__file__).parent.parent.parent.parent / "contracts" / "fixtures"


# =============================================================================
# Valid Payload Tests
# =============================================================================


def test_valid_hardware_performance_payload():
    """Valid hardware_performance payload passes validation."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
            "boot_count": {"value": 4, "unit": "count", "aggregation": "sum"},
            "adc_noise_db": {"value": -72.4, "unit": "db", "aggregation": "avg"},
        },
    }
    result = validate_telemetry(payload)
    assert result.valid, f"Errors: {result.errors}"
    assert result.payload is not None
    assert result.payload.telemetry_category == TelemetryCategory.HARDWARE_PERFORMANCE


def test_valid_utilization_payload():
    """Valid utilization payload passes validation."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T18:00:00Z",
        "instrument_id": "sg-0002-beta",
        "manufacturing_batch_id": "tb-batch-2026-01-10-02",
        "telemetry_category": "utilization",
        "metrics": {
            "power_on_hours": {"value": 100.5, "unit": "hours", "aggregation": "sum"},
            "session_count": {"value": 42, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert result.valid, f"Errors: {result.errors}"


def test_valid_environment_payload():
    """Valid environment payload passes validation."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T19:00:00Z",
        "instrument_id": "sg-0003-gamma",
        "manufacturing_batch_id": "tb-batch-2026-01-10-03",
        "telemetry_category": "environment",
        "metrics": {
            "temp_c": {"value": 25.5, "unit": "celsius", "aggregation": "avg"},
            "humidity_bucket": {
                "value": 1,
                "unit": "count",
                "aggregation": "bucket",
                "bucket_label": "40-60 pct",  # Valid pattern (no % allowed)
            },
        },
    }
    result = validate_telemetry(payload)
    assert result.valid, f"Errors: {result.errors}"


def test_valid_lifecycle_payload():
    """Valid lifecycle payload passes validation."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T20:00:00Z",
        "instrument_id": "sg-0004-delta",
        "manufacturing_batch_id": "tb-batch-2026-01-10-04",
        "telemetry_category": "lifecycle",
        "metrics": {
            "fret_wear_events": {"value": 5, "unit": "count", "aggregation": "sum"},
            "string_break_count": {"value": 2, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert result.valid, f"Errors: {result.errors}"


def test_valid_payload_with_optional_fields():
    """Valid payload with optional manufacturing correlation fields."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T21:00:00Z",
        "instrument_id": "sg-0005-epsilon",
        "manufacturing_batch_id": "tb-batch-2026-01-10-05",
        "telemetry_category": "hardware_performance",
        "design_revision_id": "rev-2.1.0",
        "hardware_sku": "SKU-SG-PRO-2026",
        "component_lot_id": "lot-pickup-A1234",
        "metrics": {
            "pickup_noise_floor_db": {"value": -85.2, "unit": "db", "aggregation": "avg"},
        },
    }
    result = validate_telemetry(payload)
    assert result.valid, f"Errors: {result.errors}"
    assert result.payload.design_revision_id == "rev-2.1.0"
    assert result.payload.hardware_sku == "SKU-SG-PRO-2026"


# =============================================================================
# Forbidden Field Tests (Pedagogy Leak Detection)
# =============================================================================


def test_rejects_player_id():
    """Payload with player_id is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "player_id": "user-12345",  # FORBIDDEN
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid
    assert any("player_id" in e.lower() for e in result.errors)


def test_rejects_lesson_id():
    """Payload with lesson_id is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "lesson_id": "lesson_fretting_101",  # FORBIDDEN
        "metrics": {
            "session_count": {"value": 5, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid
    assert any("lesson_id" in e.lower() for e in result.errors)


def test_rejects_accuracy():
    """Payload with accuracy field is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "accuracy": 0.82,  # FORBIDDEN - pedagogy data
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid
    assert any("accuracy" in e.lower() for e in result.errors)


def test_rejects_midi():
    """Payload with midi field is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "midi": [60, 64, 67],  # FORBIDDEN - musical content
        "metrics": {
            "latency_ms": {"value": 5.2, "unit": "milliseconds", "aggregation": "avg"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid
    assert any("midi" in e.lower() for e in result.errors)


def test_rejects_audio():
    """Payload with audio field is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "audio": "base64-encoded-audio",  # FORBIDDEN
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid
    assert any("audio" in e.lower() for e in result.errors)


def test_rejects_coach_feedback():
    """Payload with coach_feedback is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "coach_feedback": "Good progress!",  # FORBIDDEN
        "metrics": {
            "session_count": {"value": 1, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid
    assert any("coach_feedback" in e.lower() for e in result.errors)


@pytest.mark.parametrize("field_name", list(FORBIDDEN_FIELDS)[:10])
def test_forbidden_fields_rejected(field_name):
    """All forbidden fields are rejected at top level."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        field_name: "forbidden_value",  # Injected forbidden field
        "metrics": {
            "uptime_hours": {"value": 1.0, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid, f"Field '{field_name}' should be forbidden"


# =============================================================================
# Invalid Telemetry Category Tests
# =============================================================================


def test_rejects_invalid_category():
    """Invalid telemetry_category is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "practice_usage",  # INVALID - pedagogy-like
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


def test_rejects_pedagogy_category():
    """Pedagogy-sounding category is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "learning_metrics",  # INVALID
        "metrics": {
            "session_count": {"value": 5, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


# =============================================================================
# Schema Validation Tests
# =============================================================================


def test_rejects_missing_required_fields():
    """Missing required fields are REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        # Missing: schema_version, emitted_at_utc, instrument_id, etc.
    }
    result = validate_telemetry(payload)
    assert not result.valid
    assert len(result.errors) > 0


def test_rejects_wrong_schema_id():
    """Wrong schema_id is REJECTED."""
    payload = {
        "schema_id": "wrong_schema_id",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


def test_rejects_wrong_schema_version():
    """Wrong schema_version is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v2",  # Wrong version
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


def test_rejects_invalid_instrument_id_pattern():
    """Invalid instrument_id pattern is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "x",  # Too short
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


def test_rejects_empty_metrics():
    """Empty metrics object is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {},  # Empty - not allowed
    }
    result = validate_telemetry(payload)
    assert not result.valid


def test_rejects_invalid_metric_name():
    """Invalid metric name pattern is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "InvalidMetricName": {  # Must be lowercase with underscores
                "value": 12.5,
                "unit": "hours",
                "aggregation": "sum",
            },
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


def test_rejects_invalid_unit():
    """Invalid metric unit is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "uptime": {
                "value": 12.5,
                "unit": "invalid_unit",  # Not in allowed units
                "aggregation": "sum",
            },
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


def test_rejects_bucket_without_label():
    """Bucket aggregation without bucket_label is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "environment",
        "metrics": {
            "humidity_bucket": {
                "value": 1,
                "unit": "count",
                "aggregation": "bucket",
                # Missing bucket_label!
            },
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


def test_rejects_bucket_label_on_non_bucket():
    """bucket_label on non-bucket aggregation is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "uptime_hours": {
                "value": 12.5,
                "unit": "hours",
                "aggregation": "sum",
                "bucket_label": "0-10 hours",  # Not allowed on non-bucket!
            },
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid


# =============================================================================
# Fixture File Tests
# =============================================================================


def test_valid_fixture_file_passes():
    """Valid fixture file passes validation."""
    fixture_path = FIXTURES_DIR / "telemetry_valid_hardware_performance.json"
    if fixture_path.exists():
        result = validate_telemetry_file(fixture_path)
        assert result.valid, f"Errors: {result.errors}"
    else:
        pytest.skip(f"Fixture not found: {fixture_path}")


def test_invalid_fixture_file_rejected():
    """Invalid fixture with pedagogy leak is REJECTED."""
    fixture_path = FIXTURES_DIR / "telemetry_invalid_pedagogy_leak.json"
    if fixture_path.exists():
        result = validate_telemetry_file(fixture_path)
        assert not result.valid, "Invalid fixture should be rejected"
        # Should catch player_id, lesson_id, and/or accuracy
        assert len(result.errors) > 0
    else:
        pytest.skip(f"Fixture not found: {fixture_path}")


def test_metric_key_smuggle_fixture_rejected():
    """Fixture with forbidden terms smuggled in metric keys is REJECTED."""
    fixture_path = FIXTURES_DIR / "telemetry_invalid_metric_key_smuggle.json"
    if fixture_path.exists():
        result = validate_telemetry_file(fixture_path)
        assert not result.valid, "Metric key smuggling should be rejected"
        # Should catch player_id_hash, lesson_progress_pct, accuracy_score_avg
        assert len(result.errors) >= 3
        assert any("player_id" in e.lower() for e in result.errors)
        assert any("lesson" in e.lower() for e in result.errors)
        assert any("accuracy" in e.lower() for e in result.errors)
    else:
        pytest.skip(f"Fixture not found: {fixture_path}")


# =============================================================================
# Metric Key Smuggling Tests (Boundary Enforcement)
# =============================================================================


def test_rejects_player_id_in_metric_key():
    """Metric key containing 'player_id' is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "metrics": {
            "player_id_hash": {"value": 1, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid, "Metric key 'player_id_hash' should be blocked"
    assert any("player_id" in e.lower() and "metric key" in e.lower() for e in result.errors)


def test_rejects_lesson_id_in_metric_key():
    """Metric key containing 'lesson_id' is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "metrics": {
            "lesson_id_count": {"value": 5, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid, "Metric key 'lesson_id_count' should be blocked"
    assert any("lesson_id" in e.lower() for e in result.errors)


def test_rejects_accuracy_in_metric_key():
    """Metric key containing 'accuracy' is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "metrics": {
            "accuracy_score_avg": {"value": 0.85, "unit": "ratio", "aggregation": "avg"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid, "Metric key 'accuracy_score_avg' should be blocked"
    assert any("accuracy" in e.lower() for e in result.errors)


def test_rejects_timing_in_metric_key():
    """Metric key containing 'timing' is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "timing_offset_ms": {"value": 5.2, "unit": "milliseconds", "aggregation": "avg"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid, "Metric key 'timing_offset_ms' should be blocked"
    assert any("timing" in e.lower() for e in result.errors)


def test_rejects_score_in_metric_key():
    """Metric key containing 'score' is REJECTED."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "metrics": {
            "score_total": {"value": 100, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid, "Metric key 'score_total' should be blocked"
    assert any("score" in e.lower() for e in result.errors)


def test_rejects_multiple_forbidden_metric_keys():
    """Multiple forbidden metric keys all generate errors."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "metrics": {
            "player_id_hash": {"value": 1, "unit": "count", "aggregation": "sum"},
            "lesson_progress_pct": {"value": 75.0, "unit": "percent", "aggregation": "avg"},
            "accuracy_avg": {"value": 0.92, "unit": "ratio", "aggregation": "avg"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid
    # Should have at least 3 errors (one per forbidden metric key)
    assert len(result.errors) >= 3


@pytest.mark.parametrize("forbidden_term", [
    "player_id", "user_id", "account_id", "lesson_id", "accuracy", "timing",
    "midi", "audio", "score", "grade", "evaluation", "coach_feedback",
])
def test_forbidden_terms_blocked_in_metric_keys(forbidden_term):
    """All forbidden terms are blocked when used in metric keys."""
    metric_key = f"{forbidden_term}_count"
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "metrics": {
            metric_key: {"value": 1, "unit": "count", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert not result.valid, f"Metric key '{metric_key}' should be blocked"
    assert any(forbidden_term in e.lower() for e in result.errors)


def test_accepts_valid_metric_key_without_forbidden_terms():
    """Valid metric keys without forbidden terms are accepted."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "cpu_temp_c": {"value": 45.2, "unit": "celsius", "aggregation": "avg"},
            "battery_voltage_v": {"value": 3.85, "unit": "volts", "aggregation": "avg"},
            "uptime_hours": {"value": 100.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    assert result.valid, f"Valid metrics should pass: {result.errors}"


# =============================================================================
# JSON String Validation Tests
# =============================================================================


def test_validate_json_string():
    """validate_telemetry_json works with JSON string."""
    json_str = json.dumps({
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    })
    result = validate_telemetry_json(json_str)
    assert result.valid, f"Errors: {result.errors}"


def test_validate_json_string_invalid():
    """validate_telemetry_json rejects invalid JSON."""
    result = validate_telemetry_json("not valid json")
    assert not result.valid
    assert any("invalid json" in e.lower() for e in result.errors)


# =============================================================================
# Warning Tests
# =============================================================================


def test_warns_on_suspicious_metric_names():
    """Suspicious metric names trigger warnings."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "metrics": {
            # These metric names contain suspicious patterns
            "practice_mode_hours": {"value": 5.0, "unit": "hours", "aggregation": "sum"},
        },
    }
    result = validate_telemetry(payload)
    # Should still be valid (not a hard block) but have warnings
    assert result.valid
    assert len(result.warnings) > 0
    assert any("suspicious" in w.lower() for w in result.warnings)
