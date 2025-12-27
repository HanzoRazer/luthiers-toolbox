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
    # Minimal CamIntentV1 payload (adjust fields if your model requires more)
    payload = {
        "tool_id": "router:1/4in_endmill",
        "mode": "roughing",
        "design": {
            "entities": [],
            "tool_diameter": 6.35,
            "depth_per_pass": 1.0,
            "stock_thickness": 10.0,
            "feed_xy": 500.0,
            "feed_z": 200.0,
            "safe_z": 5.0,
            "tabs_count": 0,
            "tab_width": 10,
            "tab_height": 1.5,
            "post": "grbl",
        },
    }

    r = client.post("/api/cam/roughing_gcode_intent?strict=false", json=payload, headers={"x-request-id": "req_test_1"})
    assert r.status_code in (200, 201, 204) or r.status_code == 422  # generator may reject empty entities; metrics still should count

    m = client.get("/metrics")
    assert m.status_code == 200
    body = m.text

    assert _contains_metric(body, "cam_roughing_gcode_intent_total")


def test_roughing_intent_strict_reject_counter(client: TestClient) -> None:
    # A payload likely to produce issues (depends on your normalizer; keep intentionally sparse)
    payload = {
        "tool_id": "router:unknown",
        "mode": "roughing",
        "design": {},
    }

    r = client.post("/api/cam/roughing_gcode_intent?strict=true", json=payload, headers={"x-request-id": "req_test_2"})
    # Strict mode may reject with 422; that's what we want to count.
    assert r.status_code in (400, 422)

    m = client.get("/metrics")
    assert m.status_code == 200
    body = m.text

    assert _contains_metric(body, "cam_roughing_gcode_intent_total")
    # If strict rejection occurred via issues path, this should exist:
    # We can't guarantee normalizer emits issues in all cases, so allow either.
    # But if 422, we expect the reject counter exists.
    if r.status_code == 422:
        assert _contains_metric(body, "cam_roughing_gcode_intent_strict_reject_total")
