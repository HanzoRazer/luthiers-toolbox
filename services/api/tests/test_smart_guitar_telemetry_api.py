"""
API tests for Smart Guitar -> ToolBox Telemetry Ingestion endpoint.

Tests the HTTP endpoints:
- POST /api/telemetry/ingest
- POST /api/telemetry/validate
- GET /api/telemetry/contract
- GET /api/telemetry/health
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# =============================================================================
# Health & Contract Info Tests
# =============================================================================


def test_telemetry_health_endpoint():
    """GET /api/telemetry/health returns healthy status."""
    response = client.get("/api/telemetry/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["contract_version"] == "v1"
    assert "timestamp_utc" in data


def test_telemetry_contract_info():
    """GET /api/telemetry/contract returns contract info."""
    response = client.get("/api/telemetry/contract")
    assert response.status_code == 200
    data = response.json()
    assert data["contract_version"] == "v1"
    assert "utilization" in data["allowed_categories"]
    assert "hardware_performance" in data["allowed_categories"]
    assert "environment" in data["allowed_categories"]
    assert "lifecycle" in data["allowed_categories"]
    assert "player_id" in data["forbidden_fields"]
    assert "lesson_id" in data["forbidden_fields"]
    assert "accuracy" in data["forbidden_fields"]


# =============================================================================
# Ingest Endpoint Tests - Valid Payloads
# =============================================================================


def test_ingest_valid_hardware_performance():
    """POST /api/telemetry/ingest accepts valid hardware_performance payload."""
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
        },
    }
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 200, f"Response: {response.json()}"
    data = response.json()
    assert data["accepted"] is True
    assert data["telemetry_id"] is not None
    assert data["instrument_id"] == "sg-0001-alpha"
    assert data["category"] == "hardware_performance"
    assert data["metric_count"] == 2


def test_ingest_valid_utilization():
    """POST /api/telemetry/ingest accepts valid utilization payload."""
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
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_ingest_valid_environment():
    """POST /api/telemetry/ingest accepts valid environment payload."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T19:00:00Z",
        "instrument_id": "sg-0003-gamma",
        "manufacturing_batch_id": "tb-batch-2026-01-10-03",
        "telemetry_category": "environment",
        "metrics": {
            "temp_c": {"value": 25.5, "unit": "celsius", "aggregation": "avg"},
        },
    }
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_ingest_valid_lifecycle():
    """POST /api/telemetry/ingest accepts valid lifecycle payload."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T20:00:00Z",
        "instrument_id": "sg-0004-delta",
        "manufacturing_batch_id": "tb-batch-2026-01-10-04",
        "telemetry_category": "lifecycle",
        "metrics": {
            "fret_wear_events": {"value": 5, "unit": "count", "aggregation": "sum"},
        },
    }
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is True


# =============================================================================
# Ingest Endpoint Tests - Rejected Payloads (Forbidden Fields)
# =============================================================================


def test_ingest_rejects_player_id():
    """POST /api/telemetry/ingest rejects payload with player_id."""
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
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["accepted"] is False
    assert any("player_id" in e.lower() for e in detail["errors"])


def test_ingest_rejects_lesson_id():
    """POST /api/telemetry/ingest rejects payload with lesson_id."""
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
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["accepted"] is False


def test_ingest_rejects_accuracy():
    """POST /api/telemetry/ingest rejects payload with accuracy field."""
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
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 422


def test_ingest_rejects_midi():
    """POST /api/telemetry/ingest rejects payload with midi field."""
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
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 422


# =============================================================================
# Ingest Endpoint Tests - Rejected Payloads (Invalid Schema)
# =============================================================================


def test_ingest_rejects_invalid_category():
    """POST /api/telemetry/ingest rejects invalid telemetry_category."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "practice_usage",  # INVALID
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 422


def test_ingest_rejects_empty_metrics():
    """POST /api/telemetry/ingest rejects empty metrics."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {},  # Empty
    }
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 422


def test_ingest_rejects_missing_required_fields():
    """POST /api/telemetry/ingest rejects missing required fields."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        # Missing: schema_version, emitted_at_utc, etc.
    }
    response = client.post("/api/telemetry/ingest", json=payload)
    assert response.status_code == 422


# =============================================================================
# Validate Endpoint Tests
# =============================================================================


def test_validate_valid_payload():
    """POST /api/telemetry/validate returns valid=true for valid payload."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "hardware_performance",
        "metrics": {
            "uptime_hours": {"value": 12.5, "unit": "hours", "aggregation": "sum"},
        },
    }
    response = client.post("/api/telemetry/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["errors"] == []


def test_validate_invalid_payload():
    """POST /api/telemetry/validate returns valid=false for invalid payload."""
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
    response = client.post("/api/telemetry/validate", json=payload)
    assert response.status_code == 200  # Validate endpoint always returns 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0


def test_validate_warns_on_suspicious_metrics():
    """POST /api/telemetry/validate returns warnings for suspicious metric names."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-10T17:06:00Z",
        "instrument_id": "sg-0001-alpha",
        "manufacturing_batch_id": "tb-batch-2026-01-10-01",
        "telemetry_category": "utilization",
        "metrics": {
            "practice_mode_hours": {"value": 5.0, "unit": "hours", "aggregation": "sum"},
        },
    }
    response = client.post("/api/telemetry/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True  # Still valid, but with warnings
    assert len(data["warnings"]) > 0
    assert any("suspicious" in w.lower() for w in data["warnings"])


# =============================================================================
# Integration Tests
# =============================================================================


def test_full_telemetry_workflow():
    """End-to-end test: validate, then ingest."""
    payload = {
        "schema_id": "smart_guitar_toolbox_telemetry",
        "schema_version": "v1",
        "emitted_at_utc": "2026-01-11T00:00:00Z",
        "instrument_id": "sg-integration-test",
        "manufacturing_batch_id": "tb-integration-batch",
        "telemetry_category": "hardware_performance",
        "design_revision_id": "rev-2.0",
        "hardware_sku": "SKU-SG-PRO",
        "metrics": {
            "adc_noise_db": {"value": -75.5, "unit": "db", "aggregation": "avg"},
            "battery_voltage_v": {"value": 3.85, "unit": "volts", "aggregation": "avg"},
            "temp_c": {"value": 28.5, "unit": "celsius", "aggregation": "max"},
        },
    }

    # 1. Validate first
    validate_response = client.post("/api/telemetry/validate", json=payload)
    assert validate_response.status_code == 200
    assert validate_response.json()["valid"] is True

    # 2. Then ingest
    ingest_response = client.post("/api/telemetry/ingest", json=payload)
    assert ingest_response.status_code == 200
    data = ingest_response.json()
    assert data["accepted"] is True
    assert data["metric_count"] == 3
    assert "telemetry_id" in data
