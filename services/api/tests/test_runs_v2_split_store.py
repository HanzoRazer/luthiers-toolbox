"""
Pytest guard for RMOS runs_v2 split store integrity.

This test ensures:
- Index is created when runs are persisted
- Artifacts exist in date-partitioned directories
- count_runs_filtered() works correctly with workflow_session_id
- Verification CLI passes

Run:
  cd services/api
  pytest tests/test_runs_v2_split_store.py -v
"""

from __future__ import annotations

import importlib
import os
from datetime import datetime, timezone
from typing import Any, Dict

import pytest


def _make_minimal_artifact(RunArtifact, *, run_id: str, workflow_session_id: str):
    """
    Create a RunArtifact with minimal required fields.

    Handles schema evolution by introspecting model_fields.
    """
    fields = getattr(RunArtifact, "model_fields", {})

    def default_for(name: str):
        if name == "run_id":
            return run_id
        if name in ("created_at_utc", "created_at"):
            return datetime.now(timezone.utc)
        if name == "workflow_session_id":
            return workflow_session_id
        if name == "event_type":
            return "TEST"
        if name == "status":
            return "OK"
        if name == "tool_id":
            return "tool_test"
        if name == "mode":
            return "simulation"
        if name == "material_id":
            return "mat_test"
        if name == "machine_id":
            return "machine_test"
        if name == "request_summary":
            return {}
        if name == "feasibility":
            return {}
        if name == "outputs":
            return None
        if name == "hashes":
            return None
        if name == "decision":
            return None
        if name == "advisory_inputs":
            return []
        if name == "explanation_status":
            return "NONE"
        return None

    payload: Dict[str, Any] = {}

    # Fill required fields
    for fname, finfo in fields.items():
        is_required = getattr(finfo, "is_required", lambda: False)
        if callable(is_required):
            is_required = is_required()
        if is_required:
            val = default_for(fname)
            if val is not None:
                payload[fname] = val

    # Always set core fields if they exist in schema
    core_fields = [
        "run_id", "workflow_session_id", "event_type", "status",
        "tool_id", "mode", "created_at_utc"
    ]
    for fname in core_fields:
        if fname in fields and fname not in payload:
            val = default_for(fname)
            if val is not None:
                payload[fname] = val

    return RunArtifact(**payload)


@pytest.fixture
def runs_v2_store(tmp_path, monkeypatch):
    """
    Fixture that sets up a temporary runs_v2 store.

    Returns the reloaded store module.
    """
    store_dir = tmp_path / "rmos_runs"
    store_dir.mkdir(parents=True, exist_ok=True)

    # Set env before importing
    monkeypatch.setenv("RMOS_RUNS_DIR", str(store_dir))

    # Import and reload to pick up new env
    import app.rmos.runs_v2.store as store_module
    importlib.reload(store_module)

    return store_module


def test_split_store_index_created_on_persist(runs_v2_store):
    """Test that persisting a run creates an index entry."""
    from app.rmos.runs_v2.schemas import RunArtifact

    run_id = runs_v2_store.create_run_id()
    wsid = "ws_test_001"

    artifact = _make_minimal_artifact(
        RunArtifact,
        run_id=run_id,
        workflow_session_id=wsid
    )

    # Persist the run
    runs_v2_store.persist_run(artifact)

    # Get the store instance to check index
    store = runs_v2_store._get_default_store()
    index = store._read_index()

    assert run_id in index, "Run should be in index after persist"
    assert index[run_id]["status"] == "OK"


def test_split_store_artifact_in_partition(runs_v2_store):
    """Test that artifacts are stored in date-partitioned directories."""
    from app.rmos.runs_v2.schemas import RunArtifact

    run_id = runs_v2_store.create_run_id()
    wsid = "ws_test_002"

    artifact = _make_minimal_artifact(
        RunArtifact,
        run_id=run_id,
        workflow_session_id=wsid
    )

    runs_v2_store.persist_run(artifact)

    # Check artifact exists in partition directory
    store = runs_v2_store._get_default_store()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    partition_dir = store.root / today

    assert partition_dir.exists(), "Partition directory should exist"

    safe_id = run_id.replace("/", "_").replace("\\", "_")
    artifact_path = partition_dir / f"{safe_id}.json"

    assert artifact_path.exists(), "Artifact file should exist in partition"


def test_split_store_count_by_workflow_session(runs_v2_store):
    """Test that count_runs_filtered works with workflow_session_id."""
    from app.rmos.runs_v2.schemas import RunArtifact

    wsid = "ws_test_003"

    # Create two runs in the same workflow session
    for i in range(2):
        run_id = runs_v2_store.create_run_id()
        artifact = _make_minimal_artifact(
            RunArtifact,
            run_id=run_id,
            workflow_session_id=wsid
        )
        runs_v2_store.persist_run(artifact)

    # Count should be 2
    count = runs_v2_store.count_runs_filtered(workflow_session_id=wsid)
    assert count == 2, f"Expected 2 runs for session, got {count}"

    # Count for different session should be 0
    count_other = runs_v2_store.count_runs_filtered(workflow_session_id="ws_other")
    assert count_other == 0, f"Expected 0 runs for other session, got {count_other}"


def test_split_store_list_filtered_pagination(runs_v2_store):
    """Test that list_runs_filtered supports pagination."""
    from app.rmos.runs_v2.schemas import RunArtifact

    wsid = "ws_test_004"

    # Create 5 runs
    for i in range(5):
        run_id = runs_v2_store.create_run_id()
        artifact = _make_minimal_artifact(
            RunArtifact,
            run_id=run_id,
            workflow_session_id=wsid
        )
        runs_v2_store.persist_run(artifact)

    # Get first 2
    page1 = runs_v2_store.list_runs_filtered(
        workflow_session_id=wsid,
        limit=2,
        offset=0
    )
    assert len(page1) == 2, f"Expected 2 runs in page 1, got {len(page1)}"

    # Get next 2
    page2 = runs_v2_store.list_runs_filtered(
        workflow_session_id=wsid,
        limit=2,
        offset=2
    )
    assert len(page2) == 2, f"Expected 2 runs in page 2, got {len(page2)}"

    # Ensure no overlap
    page1_ids = {r.run_id for r in page1}
    page2_ids = {r.run_id for r in page2}
    assert page1_ids.isdisjoint(page2_ids), "Pages should not overlap"


def test_split_store_rebuild_index(runs_v2_store):
    """Test that rebuild_index correctly indexes all artifacts."""
    from app.rmos.runs_v2.schemas import RunArtifact

    wsid = "ws_test_005"

    # Create 3 runs
    run_ids = []
    for i in range(3):
        run_id = runs_v2_store.create_run_id()
        run_ids.append(run_id)
        artifact = _make_minimal_artifact(
            RunArtifact,
            run_id=run_id,
            workflow_session_id=wsid
        )
        runs_v2_store.persist_run(artifact)

    # Delete the index file
    store = runs_v2_store._get_default_store()
    if store._index_path.exists():
        store._index_path.unlink()

    # Rebuild
    count = runs_v2_store.rebuild_index()
    assert count == 3, f"Expected 3 runs indexed, got {count}"

    # Verify all runs are in index
    index = store._read_index()
    for run_id in run_ids:
        assert run_id in index, f"Run {run_id} should be in rebuilt index"


def test_split_store_verify_passes(runs_v2_store):
    """Test that verification CLI logic passes for valid store."""
    from app.rmos.runs_v2.schemas import RunArtifact
    from app.rmos.runs_v2.verify_store import verify

    wsid = "ws_test_006"

    # Create a run
    run_id = runs_v2_store.create_run_id()
    artifact = _make_minimal_artifact(
        RunArtifact,
        run_id=run_id,
        workflow_session_id=wsid
    )
    runs_v2_store.persist_run(artifact)

    # Get store root for verification
    store = runs_v2_store._get_default_store()

    # Verify should pass
    ok, report = verify(store_root=str(store.root), strict_deserialize=True)

    assert ok, f"Verification should pass: {report}"
    assert report["indexed_runs"] >= 1
    assert len(report["missing_artifacts"]) == 0
    assert len(report["deserialize_failures"]) == 0
