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


def query_job_logs_by_execution(batch_execution_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query job log artifacts by parent execution ID.

    Returns list of job logs sorted by created_utc descending (newest first).
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "batch_job_log":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_execution_artifact_id") == batch_execution_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_executions_by_label(batch_label: str, session_id: Optional[str] = None) -> list[Dict[str, Any]]:
    """
    Query execution artifacts by batch_label (and optionally session_id).

    Returns list of execution artifacts sorted by created_utc descending (newest first).
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_execution":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_label") != batch_label:
            continue
        if session_id is not None and payload.get("session_id") != session_id:
            continue
        results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_decisions_by_plan(batch_plan_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query decision artifacts by parent plan ID.

    Returns list of decision artifacts sorted by created_utc descending (newest first).
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_decision":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_plan_artifact_id") == batch_plan_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_decisions_by_spec(batch_spec_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query decision artifacts by spec ID (via plan -> spec chain).

    Returns list of decision artifacts sorted by created_utc descending (newest first).
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_decision":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_spec_artifact_id") == batch_spec_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_executions_by_plan(batch_plan_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query execution artifacts by plan ID (via decision -> plan chain).

    Returns list of execution artifacts sorted by created_utc descending (newest first).
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_execution":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_plan_artifact_id") == batch_plan_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_executions_by_spec(batch_spec_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query execution artifacts by spec ID.

    Returns list of execution artifacts sorted by created_utc descending (newest first).
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_execution":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_spec_artifact_id") == batch_spec_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_op_toolpaths_by_decision(batch_decision_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query op_toolpaths artifacts by parent decision ID.

    Returns list of op_toolpaths artifacts sorted by created_utc descending.
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_op_toolpaths":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_decision_artifact_id") == batch_decision_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_op_toolpaths_by_execution(batch_execution_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query op_toolpaths artifacts by parent execution ID.

    Uses execution's children list to find referenced op_toolpaths.
    Returns list of op_toolpaths artifacts.
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        return []

    payload = execution.get("payload", {})
    children = payload.get("children", [])

    results = []
    for child_ref in children:
        child_id = child_ref.get("artifact_id") if isinstance(child_ref, dict) else child_ref
        art = get_artifact(child_id)
        if art and art.get("kind") == "saw_batch_op_toolpaths":
            results.append(art)

    return results


def query_metrics_rollups_by_execution(batch_execution_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query metrics rollup artifacts by parent execution ID.

    Returns list of rollup artifacts sorted by created_utc descending.
    Matches both saw_batch_execution_metrics_rollup and saw_batch_execution_rollup kinds.
    """
    results = []
    valid_kinds = {"saw_batch_execution_metrics_rollup", "saw_batch_execution_rollup"}
    for art in _batch_artifacts.values():
        if art.get("kind") not in valid_kinds:
            continue
        payload = art.get("payload", {})
        if payload.get("batch_execution_artifact_id") == batch_execution_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_learning_events_by_decision(batch_decision_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query learning event artifacts by parent decision ID.

    Returns list of learning events sorted by created_utc descending.
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_learning_event":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_decision_artifact_id") == batch_decision_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_accepted_learning_events(batch_decision_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query ACCEPTED learning events for a decision.

    Returns list of learning events with policy_decision="ACCEPT".
    """
    all_events = query_learning_events_by_decision(batch_decision_artifact_id)
    return [e for e in all_events if e.get("payload", {}).get("policy_decision") == "ACCEPT"]


def query_all_accepted_learning_events(limit: int = 200) -> list[Dict[str, Any]]:
    """
    Query all ACCEPTED learning events globally.

    Returns list of learning events with policy_decision="ACCEPT", sorted by created_utc descending.
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_learning_event":
            continue
        payload = art.get("payload", {})
        if payload.get("policy_decision") == "ACCEPT":
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results[:limit]


def query_executions_with_learning(batch_label: Optional[str] = None, only_applied: bool = False) -> list[Dict[str, Any]]:
    """
    Query execution artifacts that have learning applied.

    If only_applied=True, only returns executions where learning was actually applied.
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_execution":
            continue
        payload = art.get("payload", {})

        # Filter by batch_label if specified
        if batch_label and payload.get("batch_label") != batch_label:
            continue

        # Check if learning was applied
        learning = payload.get("learning", {})
        tuning_stamp = learning.get("tuning_stamp", {}) if isinstance(learning, dict) else {}
        applied = tuning_stamp.get("applied", False) if isinstance(tuning_stamp, dict) else False

        if only_applied and not applied:
            continue

        results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_learning_events_by_execution(batch_execution_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query learning event artifacts by execution ID.

    Returns list of learning events sorted by created_utc descending.
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_learning_event":
            continue
        payload = art.get("payload", {})
        if payload.get("batch_execution_artifact_id") == batch_execution_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results


def query_execution_rollups_by_decision(batch_decision_artifact_id: str) -> list[Dict[str, Any]]:
    """
    Query execution rollup artifacts by decision ID.

    Returns list of rollup artifacts sorted by created_utc descending.
    """
    results = []
    for art in _batch_artifacts.values():
        if art.get("kind") != "saw_batch_execution_metrics_rollup":
            continue
        payload = art.get("payload", {})
        if payload.get("parent_batch_decision_artifact_id") == batch_decision_artifact_id:
            results.append(art)

    results.sort(key=lambda a: a.get("created_utc", ""), reverse=True)
    return results
