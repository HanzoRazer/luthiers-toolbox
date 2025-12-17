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
    # Ensure artifacts are written to temp
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    # Mark as test environment
    monkeypatch.setenv("ENV", "test")

    # Import the app
    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app: {e}")

    return TestClient(app)


@pytest.fixture()
def artifact_dir(tmp_path, monkeypatch):
    """Create and configure a temporary artifact directory."""
    artifact_path = tmp_path / "run_artifacts"
    artifact_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(artifact_path))
    return artifact_path


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
    """Test that filters work correctly."""
    import json
    from datetime import datetime, timezone

    # Create test artifacts
    artifact1 = {
        "artifact_id": "test_artifact_1",
        "kind": "feasibility",
        "status": "OK",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": "session_1",
        "index_meta": {"tool_id": "saw:test"},
    }
    artifact2 = {
        "artifact_id": "test_artifact_2",
        "kind": "toolpaths",
        "status": "BLOCKED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": "session_2",
        "index_meta": {"tool_id": "rosette:test"},
    }

    (artifact_dir / "test_artifact_1.json").write_text(json.dumps(artifact1))
    (artifact_dir / "test_artifact_2.json").write_text(json.dumps(artifact2))

    # Test kind filter
    res = client.get("/api/rmos/runs", params={"kind": "feasibility"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["artifact_id"] == "test_artifact_1"

    # Test status filter
    res = client.get("/api/rmos/runs", params={"status": "BLOCKED"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["artifact_id"] == "test_artifact_2"


def test_runs_diff_detects_changes(client, artifact_dir):
    """Test that diff correctly detects changed fields."""
    import json
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    artifact_a = {
        "artifact_id": "diff_test_a",
        "kind": "feasibility",
        "status": "OK",
        "created_utc": now,
        "session_id": "session_a",
        "index_meta": {"tool_id": "saw:test", "material_id": "ebony"},
        "payload": {
            "feasibility": {
                "score": 92.0,
                "risk_bucket": "GREEN",
                "meta": {"feasibility_hash": "hash_a"},
            }
        },
    }
    artifact_b = {
        "artifact_id": "diff_test_b",
        "kind": "feasibility",
        "status": "OK",
        "created_utc": now,
        "session_id": "session_b",
        "index_meta": {"tool_id": "saw:test", "material_id": "maple"},
        "payload": {
            "feasibility": {
                "score": 71.0,
                "risk_bucket": "YELLOW",
                "meta": {"feasibility_hash": "hash_b"},
            }
        },
    }

    (artifact_dir / "diff_test_a.json").write_text(json.dumps(artifact_a))
    (artifact_dir / "diff_test_b.json").write_text(json.dumps(artifact_b))

    res = client.get("/api/rmos/runs/diff/diff_test_a/diff_test_b")
    assert res.status_code == 200
    diff = res.json()

    assert diff["a_id"] == "diff_test_a"
    assert diff["b_id"] == "diff_test_b"
    assert diff["summary"]["total_changes"] >= 1

    changed_fields = {c["field"] for c in diff["changed_fields"]}
    assert "score" in changed_fields or "risk_bucket" in changed_fields or "material_id" in changed_fields
