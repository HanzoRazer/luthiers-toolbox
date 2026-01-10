"""
RMOS Run Artifacts E2E Tests

Tests the run artifacts index, query, and diff endpoints
per RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md.
"""

from __future__ import annotations

import os
import pytest
from pathlib import Path


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Uses the real FastAPI app but redirects artifact storage to a temp folder.
    """
    # Ensure artifacts are written to temp (legacy)
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    # runs_v2 store uses RMOS_RUNS_DIR
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    # Seed empty index
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")
    # Mark as test environment
    monkeypatch.setenv("ENV", "test")

    # Reset the store singleton to pick up new path
    try:
        from app.rmos.runs_v2 import store as runs_v2_store

        runs_v2_store._default_store = None
    except ImportError:
        pass

    # Import the app
    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app: {e}")

    return TestClient(app)


@pytest.fixture()
def artifact_dir(tmp_path, monkeypatch):
    """Create and configure a temporary artifact directory for runs_v2."""
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    # Seed empty index
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    # Reset the store singleton
    try:
        from app.rmos.runs_v2 import store as runs_v2_store

        runs_v2_store._default_store = None
    except ImportError:
        pass

    return runs_dir


def test_runs_list_empty(client):
    """Test that empty index returns empty list."""
    res = client.get("/api/rmos/runs")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["next_cursor"] is None


def test_runs_404_for_missing_artifact(client):
    """Test that missing artifact returns 404."""
    res = client.get("/api/rmos/runs/nonexistent_artifact_id")
    assert res.status_code == 404
    data = res.json()
    assert data["detail"]["error"] == "RUN_NOT_FOUND"


def test_runs_rejects_path_traversal(client):
    """Test that path traversal attempts are rejected."""
    res = client.get("/api/rmos/runs/../../etc/passwd")
    assert res.status_code in (400, 404)


def test_runs_diff_404_for_missing(client):
    """Test that diff with missing artifacts returns 404."""
    res = client.get("/api/rmos/runs/diff/missing_a/missing_b")
    assert res.status_code == 404


def test_runs_index_with_filters(client, artifact_dir):
    """Test that filters work correctly using the runs_v2 API."""
    # Create test runs via API (runs_v2 uses event_type, not kind)
    run1 = client.post(
        "/api/rmos/runs",
        json={
            "mode": "cam",
            "tool_id": "saw:test",
            "status": "OK",
            "event_type": "feasibility",
            "request_summary": {},
            "feasibility": {"score": 0.9},
        },
    )
    assert run1.status_code == 200, f"Create run1 failed: {run1.text}"

    run2 = client.post(
        "/api/rmos/runs",
        json={
            "mode": "cam",
            "tool_id": "rosette:test",
            "status": "BLOCKED",
            "event_type": "toolpaths",
            "request_summary": {},
            "feasibility": {"score": 0.5},
        },
    )
    assert run2.status_code == 200, f"Create run2 failed: {run2.text}"

    # Test event_type filter (runs_v2 uses event_type, not kind)
    res = client.get("/api/rmos/runs", params={"event_type": "feasibility"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["event_type"] == "feasibility"

    # Test status filter
    res = client.get("/api/rmos/runs", params={"status": "BLOCKED"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "BLOCKED"


def test_runs_diff_detects_changes(client, artifact_dir):
    """Test that diff correctly detects changed fields using runs_v2 API."""
    # Create two runs via API with differing feasibility data
    run_a_resp = client.post(
        "/api/rmos/runs",
        json={
            "mode": "cam",
            "tool_id": "saw:test",
            "status": "OK",
            "event_type": "feasibility",
            "request_summary": {"material_id": "ebony"},
            "feasibility": {"score": 92.0, "risk_bucket": "GREEN"},
            "meta": {"material_id": "ebony"},
        },
    )
    assert run_a_resp.status_code == 200, f"Create run_a failed: {run_a_resp.text}"
    run_a_id = run_a_resp.json()["run_id"]

    run_b_resp = client.post(
        "/api/rmos/runs",
        json={
            "mode": "cam",
            "tool_id": "saw:test",
            "status": "OK",
            "event_type": "feasibility",
            "request_summary": {"material_id": "maple"},
            "feasibility": {"score": 71.0, "risk_bucket": "YELLOW"},
            "meta": {"material_id": "maple"},
        },
    )
    assert run_b_resp.status_code == 200, f"Create run_b failed: {run_b_resp.text}"
    run_b_id = run_b_resp.json()["run_id"]

    # Use the query-param diff endpoint
    res = client.get("/api/rmos/runs/diff", params={"left_id": run_a_id, "right_id": run_b_id})
    assert res.status_code == 200
    diff = res.json()

    # Diff response uses "a" and "b" keys containing run snapshots
    assert diff["a"]["run_id"] == run_a_id
    assert diff["b"]["run_id"] == run_b_id
    # Should detect severity and changed fields
    assert "diff_severity" in diff
    assert "changed_paths" in diff or "diff" in diff
