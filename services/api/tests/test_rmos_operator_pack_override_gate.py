"""
RMOS Operator Pack Override Gate Tests

Verifies that:
- YELLOW requires override attachment before export
- RED requires override attachment AND feature flag
- Override endpoint creates auditable attachment
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
def test_yellow_requires_override_then_allows_export(tmp_path, monkeypatch):
    """YELLOW feasibility requires override before export is allowed."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    _reset_store_singleton()

    client = _client()
    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists()

    # Force YELLOW: feed_z > feed_xy
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "-3.0",
        "feed_xy": "300",
        "feed_z": "500",   # YELLOW
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

    # operator pack blocked until override exists
    r2 = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r2.status_code == 403
    assert "override required" in (r2.json().get("detail") or "").lower()

    # create override
    r3 = client.post(
        f"/api/rmos/runs_v2/{run_id}/override",
        json={"reason": "Operator verified setup and accepts YELLOW risk", "operator": "test"},
    )
    assert r3.status_code == 200, r3.text
    assert r3.json().get("ok") is True

    # now export should succeed
    r4 = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r4.status_code == 200
    assert r4.headers.get("content-type", "").startswith("application/zip")


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_red_override_is_blocked_without_feature_flag(tmp_path, monkeypatch):
    """RED feasibility is blocked even with override unless feature flag is set."""
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

    # create override (still should not allow export without feature flag)
    r3 = client.post(
        f"/api/rmos/runs_v2/{run_id}/override",
        json={"reason": "test override", "operator": "test"},
    )
    assert r3.status_code == 200, r3.text

    r4 = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r4.status_code == 403
    assert "override disabled" in (r4.json().get("detail") or "").lower()


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_red_override_allows_export_with_feature_flag(tmp_path, monkeypatch):
    """RED feasibility with override AND feature flag allows export."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    monkeypatch.setenv("RMOS_ALLOW_RED_OVERRIDE", "1")
    _reset_store_singleton()

    client = _client()
    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists()

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

    r3 = client.post(
        f"/api/rmos/runs_v2/{run_id}/override",
        json={"reason": "Supervisor approved RED override for test", "operator": "test"},
    )
    assert r3.status_code == 200, r3.text

    r4 = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r4.status_code == 200
    assert r4.headers.get("content-type", "").startswith("application/zip")
