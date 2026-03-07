"""Smoke tests for RMOS safety endpoints (proxied to feasibility engine)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Safety Evaluate Endpoint
# =============================================================================

def test_safety_evaluate_returns_ok(client):
    """POST /api/rmos/safety/evaluate returns ok=True."""
    response = client.post("/api/rmos/safety/evaluate", json={
        "tool_diameter_mm": 6.0,
        "depth_of_cut_mm": 2.0,
        "stepover_percent": 40.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "decision" in data
    assert "risk_level" in data


def test_safety_evaluate_safe_params_green(client):
    """POST /api/rmos/safety/evaluate with safe params returns GREEN."""
    response = client.post("/api/rmos/safety/evaluate", json={
        "tool_diameter_mm": 6.0,
        "depth_of_cut_mm": 2.0,  # Well under 50% of tool diameter
        "stepover_percent": 40.0,
        "material": "softwood",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "GREEN"
    assert data["decision"] == "ALLOW"


def test_safety_evaluate_excessive_doc_yellow(client):
    """POST /api/rmos/safety/evaluate with high DOC triggers YELLOW."""
    response = client.post("/api/rmos/safety/evaluate", json={
        "tool_diameter_mm": 6.0,
        "depth_of_cut_mm": 5.0,  # >50% of tool diameter
        "stepover_percent": 40.0,
        "material_hardness": "hard",
    })
    assert response.status_code == 200
    data = response.json()
    # Should trigger at least one warning
    assert data["risk_level"] in ("YELLOW", "RED")
    assert "rules_triggered" in data


def test_safety_evaluate_dangerous_params_red(client):
    """POST /api/rmos/safety/evaluate with dangerous params returns RED."""
    response = client.post("/api/rmos/safety/evaluate", json={
        "tool_diameter_mm": 6.0,
        "depth_of_cut_mm": 40.0,  # WAY over tool diameter
        "stepover_percent": 100.0,
        "material_hardness": "hard",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "RED"
    assert data["decision"] == "BLOCK"
    assert len(data["blocks"]) > 0


def test_safety_evaluate_returns_rules_triggered(client):
    """POST /api/rmos/safety/evaluate returns rules_triggered list."""
    response = client.post("/api/rmos/safety/evaluate", json={
        "tool_diameter_mm": 6.0,
        "depth_of_cut_mm": 4.0,  # Should trigger at least one rule
        "material_hardness": "hard",
    })
    assert response.status_code == 200
    data = response.json()
    assert "rules_triggered" in data
    assert isinstance(data["rules_triggered"], list)


def test_safety_evaluate_handles_empty_payload(client):
    """POST /api/rmos/safety/evaluate handles empty payload."""
    response = client.post("/api/rmos/safety/evaluate", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "risk_level" in data


# =============================================================================
# Safety Mode Endpoint
# =============================================================================

def test_safety_mode_returns_settings(client):
    """GET /api/rmos/safety/mode returns mode settings."""
    response = client.get("/api/rmos/safety/mode")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "strict_mode" in data
    assert "allow_overrides" in data


def test_safety_mode_default_standard(client):
    """GET /api/rmos/safety/mode defaults to standard mode."""
    response = client.get("/api/rmos/safety/mode")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "standard"


# =============================================================================
# Safety Create Override Endpoint
# =============================================================================

def test_safety_create_override_returns_token(client):
    """POST /api/rmos/safety/create-override returns functional token."""
    response = client.post("/api/rmos/safety/create-override", json={
        "action": "test_action",
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert len(data["token"]) == 8  # 4 bytes hex = 8 chars
    assert "expires_at" in data
