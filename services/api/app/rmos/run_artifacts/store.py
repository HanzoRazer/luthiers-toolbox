"""
Run Artifacts Store

Wrapper module providing write/read/query operations for run artifacts.
Implements the interface expected by batch services.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .index import list_artifacts, get_artifact, save_artifact, RunIndexRow


def _generate_artifact_id() -> str:
    """Generate a unique artifact ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"art_{ts}_{short_uuid}"


def write_run_artifact(
    *,
    kind: str,
    status: str,
    session_id: Optional[str] = None,
    index_meta: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Write a new run artifact to storage.

    Args:
        kind: Artifact kind (e.g., "saw_batch_execution", "saw_batch_op_toolpaths")
        status: Status code ("OK", "BLOCKED", "ERROR")
        session_id: Optional session identifier
        index_meta: Metadata for indexing and filtering
        payload: Full artifact payload data

    Returns:
        Dict with artifact_id and other metadata
    """
    artifact_id = _generate_artifact_id()
    created_utc = datetime.now(timezone.utc).isoformat()

    artifact = {
        "artifact_id": artifact_id,
        "kind": kind,
        "status": status,
        "created_utc": created_utc,
        "session_id": session_id or "",
        "index_meta": index_meta or {},
        "payload": payload or {},
    }

    save_artifact(artifact)

    return artifact


def read_run_artifact(artifact_id: str) -> Dict[str, Any]:
    """
    Read a run artifact by ID.

    Args:
        artifact_id: The artifact ID to retrieve

    Returns:
        Full artifact dict including payload

    Raises:
        FileNotFoundError: If artifact doesn't exist
    """
    return get_artifact(artifact_id)


def query_run_artifacts(
    *,
    kind: Optional[str] = None,
    status: Optional[str] = None,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    parent_batch_decision_artifact_id: Optional[str] = None,
    parent_batch_plan_artifact_id: Optional[str] = None,
    parent_batch_spec_artifact_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    **extra_filters: Any,
) -> List[Dict[str, Any]]:
    """
    Query run artifacts with filtering.

    Args:
        kind: Filter by artifact kind
        status: Filter by status
        session_id: Filter by session_id
        batch_label: Filter by batch_label in index_meta
        parent_batch_decision_artifact_id: Filter by parent decision artifact
        parent_batch_plan_artifact_id: Filter by parent plan artifact
        parent_batch_spec_artifact_id: Filter by parent spec artifact
        limit: Max results to return
        offset: Number of results to skip
        **extra_filters: Additional index_meta filters

    Returns:
        List of matching artifact dicts (index data only, not full payload)
    """
    all_rows = list_artifacts()

    # Apply filters
    filtered: List[RunIndexRow] = []
    for row in all_rows:
        if kind and row.kind != kind:
            continue
        if status and row.status != status:
            continue
        if session_id and row.session_id != session_id:
            continue
        if batch_label and row.index_meta.get("batch_label") != batch_label:
            continue

        # Parent batch artifact filters
        if parent_batch_decision_artifact_id and row.index_meta.get("parent_batch_decision_artifact_id") != parent_batch_decision_artifact_id:
            continue
        if parent_batch_plan_artifact_id and row.index_meta.get("parent_batch_plan_artifact_id") != parent_batch_plan_artifact_id:
            continue
        if parent_batch_spec_artifact_id and row.index_meta.get("parent_batch_spec_artifact_id") != parent_batch_spec_artifact_id:
            continue

        # Check extra filters against index_meta
        skip = False
        for key, value in extra_filters.items():
            if value is not None and row.index_meta.get(key) != value:
                skip = True
                break
        if skip:
            continue

        filtered.append(row)

    # Apply pagination
    paginated = filtered[offset : offset + limit]

    # Convert to dicts
    return [
        {
            "artifact_id": row.artifact_id,
            "id": row.artifact_id,  # Alias for compatibility
            "kind": row.kind,
            "status": row.status,
            "created_utc": row.created_utc,
            "session_id": row.session_id,
            "index_meta": row.index_meta,
        }
        for row in paginated
    ]
