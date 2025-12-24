"""
Tests for RMOS runs_v2 delete functionality and audit logging.

H3.6.2: Append-only delete audit log.

Run:
  cd services/api
  pytest tests/test_runs_v2_delete_audit.py -v
"""

from __future__ import annotations

import importlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest


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
            feasibility_sha256="a" * 64,  # 64-char placeholder
        ),
        advisory_inputs=[],
        explanation_status="NONE",
    )


@pytest.fixture
def runs_v2_store(tmp_path, monkeypatch):
    """Fixture that sets up a temporary runs_v2 store."""
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    # Disable rate limiting for tests
    monkeypatch.setenv("RMOS_DELETE_RATE_LIMIT_MAX", "0")

    # Reload store module to pick up new path
    from app.rmos.runs_v2 import store as store_module
    store_module._default_store = None
    importlib.reload(store_module)

    return store_module


@pytest.fixture
def audit_path(tmp_path):
    """Get the expected audit log path."""
    runs_dir = tmp_path / "rmos_runs"
    return runs_dir / "_audit" / "deletes.jsonl"


def test_hard_delete_removes_artifact_and_updates_index(runs_v2_store, audit_path):
    """Hard delete removes artifact file, updates index, and writes audit line."""
    # Create and persist an artifact
    run_id = "run_test_hard_delete"
    artifact = _make_minimal_artifact(run_id=run_id)
    runs_v2_store.persist_run(artifact)

    # Verify it exists
    retrieved = runs_v2_store.get_run(run_id)
    assert retrieved is not None
    assert retrieved.run_id == run_id

    # Perform hard delete
    result = runs_v2_store.delete_run(
        run_id,
        mode="hard",
        reason="Test hard delete",
        actor="test_user",
    )

    # Check result
    assert result["deleted"] is True
    assert result["mode"] == "hard"
    assert result["index_updated"] is True
    assert result["artifact_deleted"] is True

    # Verify artifact is gone
    retrieved = runs_v2_store.get_run(run_id)
    assert retrieved is None

    # Verify audit log was written
    assert audit_path.exists(), "Audit log should be created"
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1

    last_event = json.loads(lines[-1])
    assert last_event["run_id"] == run_id
    assert last_event["mode"] == "hard"
    assert last_event["reason"] == "Test hard delete"
    assert last_event["actor"] == "test_user"
    assert last_event["artifact_deleted"] is True
    assert last_event["errors"] is None


def test_soft_delete_writes_tombstone_and_audit(runs_v2_store, audit_path):
    """Soft delete writes tombstone to index and writes audit line."""
    run_id = "run_test_soft_delete"
    artifact = _make_minimal_artifact(run_id=run_id)
    runs_v2_store.persist_run(artifact)

    # Perform soft delete
    result = runs_v2_store.delete_run(
        run_id,
        mode="soft",
        reason="Test soft delete",
        actor="test_user",
    )

    assert result["deleted"] is True
    assert result["mode"] == "soft"
    assert result["index_updated"] is True
    assert result["artifact_deleted"] is False  # File not removed in soft delete

    # Check index contains tombstone
    store = runs_v2_store._get_default_store()
    index = store._read_index()
    assert run_id in index

    tombstone = index[run_id]
    assert tombstone["deleted"] is True
    assert tombstone["deleted_reason"] == "Test soft delete"
    assert tombstone["deleted_by"] == "test_user"
    assert "deleted_at_utc" in tombstone

    # Verify audit log
    assert audit_path.exists()
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    last_event = json.loads(lines[-1])
    assert last_event["run_id"] == run_id
    assert last_event["mode"] == "soft"


def test_delete_missing_run_raises_keyerror_and_audits(runs_v2_store, audit_path):
    """Deleting a non-existent run raises KeyError and still writes audit."""
    run_id = "run_nonexistent_12345"

    with pytest.raises(KeyError) as exc_info:
        runs_v2_store.delete_run(
            run_id,
            mode="hard",
            reason="Test missing run delete",
            actor="test_user",
        )

    assert run_id in str(exc_info.value)

    # Verify audit log records the failed attempt
    assert audit_path.exists()
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    last_event = json.loads(lines[-1])
    assert last_event["run_id"] == run_id
    assert last_event["errors"] == "Run not found"
    assert last_event["artifact_deleted"] is False


def test_delete_requires_reason(runs_v2_store):
    """Delete without reason raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        runs_v2_store.delete_run(
            "run_any",
            mode="soft",
            reason="",  # Empty reason
        )

    assert "reason" in str(exc_info.value).lower()


def test_rate_limiting(tmp_path, monkeypatch):
    """Rate limiting blocks excessive deletes."""
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    # Enable strict rate limiting: 2 deletes per 60s
    monkeypatch.setenv("RMOS_DELETE_RATE_LIMIT_MAX", "2")
    monkeypatch.setenv("RMOS_DELETE_RATE_LIMIT_WINDOW", "60")

    from app.rmos.runs_v2 import store as store_module
    store_module._default_store = None
    # Clear rate limit state
    store_module._DELETE_RATE_LIMIT.clear()
    importlib.reload(store_module)

    from app.rmos.runs_v2.store import DeleteRateLimitError

    # Create 3 runs
    for i in range(3):
        run_id = f"run_rate_test_{i}"
        artifact = _make_minimal_artifact(run_id=run_id)
        store_module.persist_run(artifact)

    # First two deletes should succeed
    store_module.delete_run("run_rate_test_0", mode="hard", reason="Rate test", actor="test_actor")
    store_module.delete_run("run_rate_test_1", mode="hard", reason="Rate test", actor="test_actor")

    # Third should be rate limited
    with pytest.raises(DeleteRateLimitError):
        store_module.delete_run("run_rate_test_2", mode="hard", reason="Rate test", actor="test_actor")


def test_hard_delete_with_advisory_links(runs_v2_store, audit_path):
    """Hard delete with cascade removes advisory links."""
    run_id = "run_test_with_advisory"
    artifact = _make_minimal_artifact(run_id=run_id)
    runs_v2_store.persist_run(artifact)

    # Attach an advisory
    runs_v2_store.attach_advisory(
        run_id=run_id,
        advisory_id="adv_test_001",
        kind="note",
    )

    # Perform hard delete with cascade
    result = runs_v2_store.delete_run(
        run_id,
        mode="hard",
        reason="Test cascade delete",
        actor="test_user",
        cascade=True,
    )

    assert result["deleted"] is True
    assert result["advisory_links_deleted"] >= 1

    # Verify audit
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    last_event = json.loads(lines[-1])
    assert last_event["attachments_deleted"] >= 1
