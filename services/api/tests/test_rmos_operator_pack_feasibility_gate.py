"""
RMOS Operator Pack Feasibility Gate Tests

Verifies that operator pack export respects feasibility risk levels:
- RED: Blocked (403)
- YELLOW: Requires override
- GREEN: Allowed
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _client():
    from app.main import app
    return TestClient(app)


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_operator_pack_blocked_when_risk_red(tmp_path, monkeypatch):
    """RED feasibility blocks operator pack export with 403."""
    # Isolate runs/attachments so test is hermetic
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))

    # Reset singleton store so env vars are respected in this process
    import app.rmos.runs_v2.store as runs_store
    if hasattr(runs_store, "_default_store"):
        runs_store._default_store = None

    client = _client()

    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists(), f"Test fixture not found: {dxf_path}"

    # Force RED feasibility (z_rough must be negative, 0.0 triggers RED)
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "0.0",  # RED: z_rough >= 0 is invalid
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
    run_id = r.json().get("run_id")
    assert run_id, "No run_id in response"

    # Verify run has RED feasibility
    decision = r.json().get("decision", {})
    assert decision.get("risk_level") == "RED", f"Expected RED, got {decision}"

    # Operator pack export must be blocked for RED
    r2 = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r2.status_code == 403, f"Expected 403, got {r2.status_code}: {r2.text}"
    detail = r2.json().get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("error") == "FEASIBILITY_RED_BLOCKED"
    else:
        assert "blocked" in str(detail).lower()


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_operator_pack_requires_override_when_yellow(tmp_path, monkeypatch):
    """YELLOW feasibility requires override params for operator pack export."""
    # Isolate runs/attachments
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))

    import app.rmos.runs_v2.store as runs_store
    if hasattr(runs_store, "_default_store"):
        runs_store._default_store = None

    client = _client()

    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists()

    # Force YELLOW feasibility (feed_z > feed_xy triggers warning)
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "-3.0",  # Valid
        "feed_xy": "1200",
        "feed_z": "1500",  # YELLOW: feed_z > feed_xy
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
    run_id = r.json().get("run_id")
    assert run_id

    decision = r.json().get("decision", {})
    assert decision.get("risk_level") == "YELLOW", f"Expected YELLOW, got {decision}"

    # Without override params, should get 400
    r2 = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r2.status_code == 400, f"Expected 400, got {r2.status_code}"
    detail = r2.json().get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("error") == "OVERRIDE_REQUIRED"


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_operator_pack_allowed_when_green(tmp_path, monkeypatch):
    """GREEN feasibility allows operator pack export without override."""
    # Isolate runs/attachments
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))

    import app.rmos.runs_v2.store as runs_store
    if hasattr(runs_store, "_default_store"):
        runs_store._default_store = None

    client = _client()

    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists()

    # Valid params should yield GREEN
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "-3.0",
        "feed_xy": "1200",
        "feed_z": "300",  # Valid: feed_z < feed_xy
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
    run_id = r.json().get("run_id")
    assert run_id

    decision = r.json().get("decision", {})
    assert decision.get("risk_level") == "GREEN", f"Expected GREEN, got {decision}"

    # GREEN should allow export without override
    r2 = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.text}"
    assert r2.headers.get("content-type") == "application/zip"


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_operator_pack_yellow_with_override_succeeds(tmp_path, monkeypatch):
    """YELLOW feasibility with override params allows export and creates override attachment."""
    # Isolate runs/attachments
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "attachments"))

    import app.rmos.runs_v2.store as runs_store
    if hasattr(runs_store, "_default_store"):
        runs_store._default_store = None

    client = _client()

    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    assert dxf_path.exists()

    # Force YELLOW
    data = {
        "tool_d": "6.0",
        "stepover": "0.45",
        "stepdown": "1.5",
        "z_rough": "-3.0",
        "feed_xy": "1200",
        "feed_z": "1500",  # YELLOW
        "rapid": "3000",
        "safe_z": "5.0",
    }

    with dxf_path.open("rb") as f:
        files = {"file": ("mvp_rect_with_island.dxf", f, "application/dxf")}
        r = client.post("/api/rmos/wrap/mvp/dxf-to-grbl", data=data, files=files)

    assert r.status_code == 200
    run_id = r.json().get("run_id")

    # With override params, should succeed
    r2 = client.get(
        f"/api/rmos/runs_v2/{run_id}/operator-pack",
        params={"override_by": "test_operator", "override_reason": "Approved for testing"},
    )
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.text}"
    assert r2.headers.get("content-type") == "application/zip"

    # Verify override attachment was created (check attachments dir)
    attachments_dir = tmp_path / "attachments"
    override_files = list(attachments_dir.glob("**/*.json"))
    # Should have multiple JSON files including override
    assert len(override_files) > 0, "Override attachment should be stored"
