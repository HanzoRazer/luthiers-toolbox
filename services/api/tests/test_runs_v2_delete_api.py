"""
Tests for RMOS runs_v2 DELETE API endpoint and cursor pagination.

H3.4: Cursor pagination
H3.5/H3.6: DELETE endpoint with policy enforcement
H3.6.1: Rate limiting
H3.6.2: Audit logging

Run:
    cd services/api
    pytest tests/test_runs_v2_delete_api.py -v
"""
from __future__ import annotations

import importlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient


def _make_minimal_artifact(run_id: str, workflow_session_id: str = "sess_test"):
    """Create a RunArtifact with minimal required fields."""
    from app.rmos.runs_v2.schemas import RunArtifact, RunDecision, Hashes

    return RunArtifact(
        run_id=run_id,
        created_at_utc=datetime.now(timezone.utc),
        workflow_session_id=workflow_session_id,
        event_type="TEST",
        status="OK",
        tool_id="tool_test",
        mode="simulation",
        material_id="mat_test",
        machine_id="machine_test",
        request_summary={},
        feasibility={},
        decision=RunDecision(
            risk_level="GREEN",
            score=0.95,
            warnings=[],
            details={},
        ),
        hashes=Hashes(
            feasibility_sha256="a" * 64,
        ),
        advisory_inputs=[],
        explanation_status="NONE",
    )


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Set up isolated test environment."""
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")
    (runs_dir / "_audit").mkdir(exist_ok=True)

    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    # Disable rate limiting for most tests
    monkeypatch.setenv("RMOS_DELETE_RATE_LIMIT_MAX", "0")
    # Safe defaults
    monkeypatch.setenv("RMOS_DELETE_DEFAULT_MODE", "soft")
    monkeypatch.setenv("RMOS_DELETE_ALLOW_HARD", "false")

    # Clear store_api singleton BEFORE reload (the actual singleton lives there)
    from app.rmos.runs_v2 import store_api
    store_api._default_store = None

    # Reload store module to pick up new path
    from app.rmos.runs_v2 import store as store_module
    importlib.reload(store_module)

    return {
        "runs_dir": runs_dir,
        "audit_path": runs_dir / "_audit" / "deletes.jsonl",
    }


@pytest.fixture
def client(test_env):
    """Create FastAPI test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def seeded_run(test_env, request):
    """Create and return a seeded run for testing with unique ID per test."""
    from app.rmos.runs_v2.store import persist_run
    from uuid import uuid4

    # Use unique run_id per test to avoid "already exists" conflicts
    run_id = f"run_test_api_delete_{uuid4().hex[:8]}"
    artifact = _make_minimal_artifact(run_id=run_id)
    persist_run(artifact)
    return run_id


# =============================================================================
# DELETE Endpoint Tests
# =============================================================================

def test_delete_soft_with_reason_succeeds(client, seeded_run):
    """Soft delete with valid reason succeeds."""
    response = client.delete(
        f"/api/rmos/runs/{seeded_run}",
        params={"reason": "cleanup test data"}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["run_id"] == seeded_run
    assert body["mode"] == "soft"
    assert body["deleted"] is True
    assert body["tombstoned"] is True
    assert body["reason"] == "cleanup test data"


def test_delete_without_reason_fails_400(client, seeded_run):
    """Delete without reason returns 400."""
    response = client.delete(f"/api/rmos/runs/{seeded_run}")
    assert response.status_code == 422  # FastAPI validation error


def test_delete_short_reason_fails_400(client, seeded_run):
    """Delete with too-short reason returns 422."""
    response = client.delete(
        f"/api/rmos/runs/{seeded_run}",
        params={"reason": "short"}  # Less than 6 chars
    )
    assert response.status_code == 422


def test_delete_not_found_returns_404(client):
    """Delete non-existent run returns 404."""
    response = client.delete(
        "/api/rmos/runs/run_nonexistent_12345",
        params={"reason": "cleanup test data"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_hard_blocked_without_admin_header(client, seeded_run, monkeypatch):
    """Hard delete without admin header returns 403."""
    # Enable hard delete in policy so we can test the admin header check
    monkeypatch.setenv("RMOS_DELETE_ALLOW_HARD", "true")

    response = client.delete(
        f"/api/rmos/runs/{seeded_run}",
        params={"mode": "hard", "reason": "cleanup test data"}
    )
    assert response.status_code == 403
    assert "header" in response.json()["detail"].lower()


def test_delete_hard_blocked_without_env_allow(client, seeded_run, monkeypatch):
    """Hard delete with admin header but without env allow returns 403."""
    # RMOS_DELETE_ALLOW_HARD is false by default from fixture
    response = client.delete(
        f"/api/rmos/runs/{seeded_run}",
        params={"mode": "hard", "reason": "cleanup test data"},
        headers={"X-RMOS-Admin": "true"}
    )
    assert response.status_code == 403
    assert "policy" in response.json()["detail"].lower()


def test_delete_hard_allowed_with_admin_and_env(client, seeded_run, monkeypatch):
    """Hard delete succeeds with admin header and env allow."""
    monkeypatch.setenv("RMOS_DELETE_ALLOW_HARD", "true")

    response = client.delete(
        f"/api/rmos/runs/{seeded_run}",
        params={"mode": "hard", "reason": "cleanup test data"},
        headers={"X-RMOS-Admin": "true"}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["mode"] == "hard"
    assert body["deleted"] is True
    assert body["artifact_deleted"] is True


def test_delete_audit_log_written(client, seeded_run, test_env):
    """Delete writes to audit log."""
    response = client.delete(
        f"/api/rmos/runs/{seeded_run}",
        params={"reason": "audit test cleanup"}
    )
    assert response.status_code == 200

    # Check audit log
    audit_path = test_env["audit_path"]
    assert audit_path.exists()

    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1

    last_event = json.loads(lines[-1])
    assert last_event["run_id"] == seeded_run
    assert last_event["mode"] == "soft"
    assert last_event["reason"] == "audit test cleanup"
    assert last_event["outcome"] == "ok"


# =============================================================================
# Cursor Pagination Tests
# =============================================================================

def test_query_cursor_pagination(client, test_env):
    """Cursor pagination works correctly."""
    from app.rmos.runs_v2 import store as store_module

    # Create multiple runs with different timestamps
    for i in range(5):
        artifact = _make_minimal_artifact(run_id=f"run_page_test_{i}")
        store_module.persist_run(artifact)

    # First page
    r1 = client.get("/api/rmos/runs/query/recent", params={"limit": 2})
    assert r1.status_code == 200

    body1 = r1.json()
    assert len(body1["items"]) == 2
    assert body1["next_cursor"] is not None

    # Second page
    r2 = client.get(
        "/api/rmos/runs/query/recent",
        params={"limit": 2, "cursor": body1["next_cursor"]}
    )
    assert r2.status_code == 200

    body2 = r2.json()
    assert len(body2["items"]) >= 1

    # Items should be different
    ids1 = {item["run_id"] for item in body1["items"]}
    ids2 = {item["run_id"] for item in body2["items"]}
    assert ids1.isdisjoint(ids2)


def test_query_with_filters(client, test_env):
    """Query with filters works."""
    from app.rmos.runs_v2 import store as store_module

    # Create runs with different statuses
    art1 = _make_minimal_artifact(run_id="run_filter_ok")
    art1 = art1.model_copy(update={"status": "OK"})
    store_module.persist_run(art1)

    art2 = _make_minimal_artifact(run_id="run_filter_blocked")
    art2 = art2.model_copy(update={"status": "BLOCKED"})
    store_module.persist_run(art2)

    # Filter by status
    response = client.get(
        "/api/rmos/runs/query/recent",
        params={"status": "OK"}
    )
    assert response.status_code == 200

    body = response.json()
    # All returned items should have status OK
    for item in body["items"]:
        assert item.get("status") == "OK"


# =============================================================================
# Policy Module Tests
# =============================================================================

def test_delete_policy_defaults():
    """Policy has safe defaults."""
    from app.rmos.runs_v2.delete_policy import get_delete_policy

    policy = get_delete_policy()
    assert policy.default_mode == "soft"
    assert policy.allow_hard is False
    assert policy.admin_header_name == "X-RMOS-Admin"


def test_delete_policy_env_override(monkeypatch):
    """Policy respects environment variables."""
    monkeypatch.setenv("RMOS_DELETE_DEFAULT_MODE", "hard")
    monkeypatch.setenv("RMOS_DELETE_ALLOW_HARD", "true")
    monkeypatch.setenv("RMOS_DELETE_ADMIN_HEADER", "X-Custom-Admin")

    from app.rmos.runs_v2.delete_policy import get_delete_policy

    policy = get_delete_policy()
    assert policy.default_mode == "hard"
    assert policy.allow_hard is True
    assert policy.admin_header_name == "X-Custom-Admin"


def test_is_admin_request():
    """Admin header detection works."""
    from app.rmos.runs_v2.delete_policy import is_admin_request

    assert is_admin_request("true") is True
    assert is_admin_request("TRUE") is True
    assert is_admin_request("1") is True
    assert is_admin_request("yes") is True
    assert is_admin_request("admin") is True
    assert is_admin_request("false") is False
    assert is_admin_request(None) is False
    assert is_admin_request("") is False


def test_check_delete_allowed():
    """Policy check works correctly."""
    from app.rmos.runs_v2.delete_policy import (
        DeletePolicy,
        check_delete_allowed,
    )

    # Soft delete always allowed
    policy = DeletePolicy(default_mode="soft", allow_hard=False, admin_header_name="X-Admin")
    allowed, reason = check_delete_allowed("soft", False, policy)
    assert allowed is True

    # Hard delete blocked without allow_hard
    allowed, reason = check_delete_allowed("hard", True, policy)
    assert allowed is False
    assert "policy" in reason.lower()

    # Hard delete blocked without admin
    policy = DeletePolicy(default_mode="soft", allow_hard=True, admin_header_name="X-Admin")
    allowed, reason = check_delete_allowed("hard", False, policy)
    assert allowed is False
    assert "header" in reason.lower()

    # Hard delete allowed with both
    allowed, reason = check_delete_allowed("hard", True, policy)
    assert allowed is True
