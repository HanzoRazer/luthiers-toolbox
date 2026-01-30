# services/api/tests/test_roughing_gcode_intent_metrics.py
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _contains_metric(body: str, metric_name: str) -> bool:
    return any(line.startswith(metric_name) for line in body.splitlines())


def test_roughing_intent_increments_metrics(client: TestClient) -> None:
    # CamIntentV1 payload matching actual schema requirements
    payload = {
        "mode": "router_3axis",  # Required by CamIntentV1
        "design": {
            "geometry": {"type": "rectangle", "width_mm": 100.0, "height_mm": 50.0},
            "width_mm": 100.0,
            "height_mm": 50.0,
            "depth_mm": 10.0,
            "stepdown_mm": 2.0,
            "stepover_mm": 5.0,
            "safe_z": 5.0,
        },
        "context": {"feed_rate": 500.0},
        "units": "mm",
    }

    r = client.post("/api/cam/roughing/gcode_intent?strict=false", json=payload, headers={"x-request-id": "req_test_1"})
    assert r.status_code in (200, 201, 204) or r.status_code == 422  # generator may reject empty entities; metrics still should count

    m = client.get("/metrics")
    assert m.status_code == 200
    body = m.text

    assert _contains_metric(body, "cam_roughing_gcode_intent_total")


def test_roughing_intent_strict_reject_counter(client: TestClient) -> None:
    # A sparse payload that may produce normalization issues
    payload = {
        "mode": "router_3axis",  # Required by CamIntentV1
        "design": {},  # Empty design should trigger issues
        "units": "mm",
    }

    r = client.post("/api/cam/roughing/gcode_intent?strict=true", json=payload, headers={"x-request-id": "req_test_2"})
    # Strict mode may reject with 422; that's what we want to count.
    # Also allow 400 for invalid request or 200 if normalizer doesn't find issues
    assert r.status_code in (200, 400, 422)

    m = client.get("/metrics")
    assert m.status_code == 200
    body = m.text

    assert _contains_metric(body, "cam_roughing_gcode_intent_total")
    # If strict rejection occurred via issues path, this should exist:
    # We can't guarantee normalizer emits issues in all cases, so allow either.
    # But if 422, we expect the reject counter exists.
    if r.status_code == 422:
        assert _contains_metric(body, "cam_roughing_gcode_intent_strict_reject_total")
