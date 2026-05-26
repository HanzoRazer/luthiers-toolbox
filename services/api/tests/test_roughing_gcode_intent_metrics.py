# services/api/tests/test_roughing_gcode_intent_metrics.py
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app

METRICS_URL = "/api/_meta/metrics"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _metric_sum(body: str, metric_name: str) -> float:
    """Sum numeric values for a Prometheus counter (handles label suffixes)."""
    total = 0.0
    pattern = re.compile(rf"^{re.escape(metric_name)}(?:\{{[^}}]*\}})?\s+(\S+)")
    for line in body.splitlines():
        m = pattern.match(line)
        if m:
            total += float(m.group(1))
    return total


def test_roughing_intent_increments_metrics(client: TestClient) -> None:
    before = _metric_sum(client.get(METRICS_URL).text, "cam_roughing_gcode_intent_total")

    payload = {
        "mode": "router_3axis",
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

    r = client.post(
        "/api/cam/roughing/gcode_intent?strict=false",
        json=payload,
        headers={"x-request-id": "req_test_1"},
    )
    assert r.status_code in (200, 422)

    after = _metric_sum(client.get(METRICS_URL).text, "cam_roughing_gcode_intent_total")
    assert after == before + 1.0


def test_roughing_intent_strict_reject_counter(client: TestClient) -> None:
    before_total = _metric_sum(
        client.get(METRICS_URL).text, "cam_roughing_gcode_intent_total"
    )
    before_reject = _metric_sum(
        client.get(METRICS_URL).text, "cam_roughing_gcode_intent_strict_reject_total"
    )

    payload = {
        "mode": "router_3axis",
        "design": {},
        "units": "mm",
    }

    r = client.post(
        "/api/cam/roughing/gcode_intent?strict=true",
        json=payload,
        headers={"x-request-id": "req_test_2"},
    )
    assert r.status_code in (200, 400, 422)

    after_total = _metric_sum(
        client.get(METRICS_URL).text, "cam_roughing_gcode_intent_total"
    )
    assert after_total == before_total + 1.0

    if r.status_code == 422:
        after_reject = _metric_sum(
            client.get(METRICS_URL).text, "cam_roughing_gcode_intent_strict_reject_total"
        )
        assert after_reject == before_reject + 1.0
