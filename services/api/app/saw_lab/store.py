"""
Saw Lab Artifact Store

In-memory artifact storage for the SawLab batch workflow.
Provides a clean seam for repo-backed storage later.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_batch_artifacts: Dict[str, Dict[str, Any]] = {}


def store_artifact(
    *,
    kind: str,
    payload: Dict[str, Any],
    parent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    index_meta: Optional[Dict[str, Any]] = None,
    status: str = "OK",
) -> str:
    """Store an artifact and return its ID."""
    artifact_id = f"{kind}_{uuid.uuid4().hex[:12]}"
    _batch_artifacts[artifact_id] = {
        "artifact_id": artifact_id,
        "kind": kind,
        "status": status,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "parent_id": parent_id,
        "session_id": session_id,
        "index_meta": index_meta or {},
        "payload": payload,
    }
    return artifact_id


def get_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Get artifact by ID, returns None if not found."""
    return _batch_artifacts.get(artifact_id)


def read_artifact(artifact_id: str) -> Dict[str, Any]:
    """
    Read artifact by ID, raises FileNotFoundError if not found.

    Matches RMOS read_run_artifact semantics for use as a pluggable reader.
    """
    art = get_artifact(artifact_id)
    if art is None:
        raise FileNotFoundError(f"SawLab artifact not found: {artifact_id}")
    return art


def clear_artifacts() -> None:
    """Clear all artifacts (for testing)."""
    _batch_artifacts.clear()


def query_executions_by_decision(batch_decision_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query execution artifacts by parent decision ID.

    Returns list of execution artifacts sorted by created_utc descending (newest first).
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_execution":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_decision_artifact_id") == batch_decision_artifact_id:
            results.append(art)

    # Sort by created_utc descending (newest first)
    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_latest_by_label_and_session(batch_label: str, session_id: str) -> Dict[str, Optional[str]]:
    """
    Query latest artifact IDs for each kind by batch_label and session_id.

    Returns dict with latest_spec_artifact_id, latest_plan_artifact_id,
    latest_decision_artifact_id, latest_execution_artifact_id.
    """
    latest: Dict[str, Optional[str]] = {
        "latest_spec_artifact_id": None,
        "latest_plan_artifact_id": None,
        "latest_decision_artifact_id": None,
        "latest_execution_artifact_id": None,
    }

    kind_to_key = {
        "saw_batch_spec": "latest_spec_artifact_id",
        "saw_batch_plan": "latest_plan_artifact_id",
        "saw_batch_decision": "latest_decision_artifact_id",
        "saw_batch_execution": "latest_execution_artifact_id",
    }

    # Group artifacts by kind, filter by label/session
    by_kind: Dict[str, list[Dict[str, Any]]] = {k: [] for k in kind_to_key}

    for art in _batch_artifacts.values():
        kind = art.get("kind", "")
        if kind not in kind_to_key:
            continue

        payload = art.get("payload", {})
        art_label = payload.get("batch_label", "")
        art_session = payload.get("session_id", "") or art.get("session_id", "")

        if art_label == batch_label and art_session == session_id:
            by_kind[kind].append(art)

    # Get latest (by created_utc) for each kind
    for kind, key in kind_to_key.items():
        arts = by_kind[kind]
        if arts:
            arts.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
            latest[key] = arts[0].get("artifact_id")

    return latest
