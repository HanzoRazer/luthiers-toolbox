from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_apply_flag_status_default_off(client: TestClient, monkeypatch):
    """
    By default (via conftest), SAW_LAB_APPLY_ACCEPTED_OVERRIDES is false.
    """
    monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "false")

    res = client.get("/api/saw/batch/learning-overrides/apply/status")
    assert res.status_code == 200, res.text
    body = res.json()

    assert "SAW_LAB_APPLY_ACCEPTED_OVERRIDES" in body
    assert body["SAW_LAB_APPLY_ACCEPTED_OVERRIDES"] is False


def test_apply_flag_status_when_enabled(client: TestClient, monkeypatch):
    """
    When SAW_LAB_APPLY_ACCEPTED_OVERRIDES=true, endpoint should report True.
    """
    monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "true")

    res = client.get("/api/saw/batch/learning-overrides/apply/status")
    assert res.status_code == 200, res.text
    body = res.json()

    assert "SAW_LAB_APPLY_ACCEPTED_OVERRIDES" in body
    assert body["SAW_LAB_APPLY_ACCEPTED_OVERRIDES"] is True


def test_apply_flag_status_accepts_various_truthy_values(client: TestClient, monkeypatch):
    """
    The flag should accept various truthy values: 1, true, yes, y, on
    """
    truthy_values = ["1", "true", "TRUE", "yes", "YES", "y", "Y", "on", "ON"]

    for val in truthy_values:
        monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", val)
        res = client.get("/api/saw/batch/learning-overrides/apply/status")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["SAW_LAB_APPLY_ACCEPTED_OVERRIDES"] is True, f"Expected True for value '{val}'"


def test_apply_flag_status_accepts_various_falsy_values(client: TestClient, monkeypatch):
    """
    The flag should treat any non-truthy value as false.
    """
    falsy_values = ["0", "false", "FALSE", "no", "NO", "n", "N", "off", "OFF", "", "anything"]

    for val in falsy_values:
        monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", val)
        res = client.get("/api/saw/batch/learning-overrides/apply/status")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["SAW_LAB_APPLY_ACCEPTED_OVERRIDES"] is False, f"Expected False for value '{val}'"
