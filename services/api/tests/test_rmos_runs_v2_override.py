"""
RMOS Override Router Tests - YELLOW unlock primitive.

Tests verify that:
- YELLOW runs can be overridden to unlock downstream actions
- RED override creates attachment (but export blocked without feature flag)
- Override creates auditable attachment and updates run status
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _client():
    from app.main import app
    return TestClient(app)


def _reset_store_singleton():
    import app.rmos.runs_v2.store as runs_store
    if hasattr(runs_store, "_default_store"):
        runs_store._default_store = None


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_override_yellow_creates_attachment_and_unlocks(tmp_path, monkeypatch):
    """YELLOW override creates attachment and unlocks downstream actions."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    _reset_store_singleton()

    client = _client()
    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists(), "Missing MVP DXF fixture"

    # Force YELLOW: feed_z > feed_xy (F011 rule)
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "-3.0",
        "feed_xy": "300",
        "feed_z": "500",  # YELLOW: plunge feed > XY feed
        "rapid": "3000",
        "safe_z": "5.0",
        "strategy": "Spiral",
        "layer_name": "GEOMETRY",
        "climb": "true",
        "smoothing": "0.1",
        "margin": "0.0",
    }

    with dxf_path.open("rb") as f:
        files = {"file": ("mvp_rect_with_island.dxf", f, "application/dxf")}
        r = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", data=data, files=files)
    assert r.status_code == 200, r.text
    run_data = r.json()
    assert run_data.get("ok") is True
    run_id = run_data["run_id"]

    # Apply override - should succeed for YELLOW
    r_override = client.post(
        f"/api/rmos/runs_v2/{run_id}/override",
        json={"reason": "Operator reviewed warnings and approved for production"},
    )
    assert r_override.status_code == 200, r_override.text
    override_resp = r_override.json()
    assert override_resp.get("ok") is True
    assert override_resp["run_id"] == run_id
    # Check attachment was created
    assert "attachment" in override_resp
    assert override_resp["attachment"]["kind"] == "override"
    assert "sha256" in override_resp["attachment"]

    # Operator pack should now be accessible
    r_pack = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r_pack.status_code == 200
    assert r_pack.headers.get("content-type", "").startswith("application/zip")


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_override_creates_attachment_for_any_risk_level(tmp_path, monkeypatch):
    """Override creates attachment regardless of risk level."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    _reset_store_singleton()

    client = _client()
    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists()

    # Force RED: z_rough >= 0
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "0.0",  # RED: cutting above zero
        "feed_xy": "1200",
        "feed_z": "300",
        "rapid": "3000",
        "safe_z": "5.0",
        "strategy": "Spiral",
        "layer_name": "GEOMETRY",
        "climb": "true",
        "smoothing": "0.1",
        "margin": "0.0",
    }

    with dxf_path.open("rb") as f:
        files = {"file": ("mvp_rect_with_island.dxf", f, "application/dxf")}
        r = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", data=data, files=files)
    assert r.status_code == 200, r.text
    run_data = r.json()
    run_id = run_data["run_id"]

    # Override should succeed (creates attachment)
    r_override = client.post(
        f"/api/rmos/runs_v2/{run_id}/override",
        json={"reason": "Override for testing purposes"},
    )
    assert r_override.status_code == 200, r_override.text
    override_resp = r_override.json()
    assert override_resp.get("ok") is True
    assert "attachment" in override_resp
    assert override_resp["attachment"]["kind"] == "override"
    assert "sha256" in override_resp["attachment"]


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_red_override_export_blocked_without_feature_flag(tmp_path, monkeypatch):
    """RED runs with override still blocked from export without RMOS_ALLOW_RED_OVERRIDE."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    monkeypatch.delenv("RMOS_ALLOW_RED_OVERRIDE", raising=False)
    _reset_store_singleton()

    client = _client()
    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists()

    # Force RED: z_rough >= 0
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "0.0",  # RED
        "feed_xy": "1200",
        "feed_z": "300",
        "rapid": "3000",
        "safe_z": "5.0",
        "strategy": "Spiral",
        "layer_name": "GEOMETRY",
        "climb": "true",
        "smoothing": "0.1",
        "margin": "0.0",
    }

    with dxf_path.open("rb") as f:
        files = {"file": ("mvp_rect_with_island.dxf", f, "application/dxf")}
        r = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", data=data, files=files)
    assert r.status_code == 200, r.text
    run_id = r.json()["run_id"]

    # Override succeeds
    r_override = client.post(
        f"/api/rmos/runs_v2/{run_id}/override",
        json={"reason": "Testing RED override without feature flag"},
    )
    assert r_override.status_code == 200, r_override.text
    assert r_override.json().get("ok") is True

    # But operator-pack export should still be blocked
    r_pack = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r_pack.status_code == 403
    assert "override disabled" in (r_pack.json().get("detail") or "").lower()


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_red_override_export_allowed_with_feature_flag(tmp_path, monkeypatch):
    """RED runs with override can export when RMOS_ALLOW_RED_OVERRIDE=1."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    monkeypatch.setenv("RMOS_ALLOW_RED_OVERRIDE", "1")
    _reset_store_singleton()

    client = _client()
    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists()

    # Force RED
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "0.0",  # RED
        "feed_xy": "1200",
        "feed_z": "300",
        "rapid": "3000",
        "safe_z": "5.0",
        "strategy": "Spiral",
        "layer_name": "GEOMETRY",
        "climb": "true",
        "smoothing": "0.1",
        "margin": "0.0",
    }

    with dxf_path.open("rb") as f:
        files = {"file": ("mvp_rect_with_island.dxf", f, "application/dxf")}
        r = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", data=data, files=files)
    assert r.status_code == 200, r.text
    run_id = r.json()["run_id"]

    # Override succeeds
    r_override = client.post(
        f"/api/rmos/runs_v2/{run_id}/override",
        json={"reason": "Supervisor approved RED override for testing"},
    )
    assert r_override.status_code == 200, r_override.text
    assert r_override.json().get("ok") is True

    # Operator-pack export should succeed with feature flag
    r_pack = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r_pack.status_code == 200
    assert r_pack.headers.get("content-type", "").startswith("application/zip")
