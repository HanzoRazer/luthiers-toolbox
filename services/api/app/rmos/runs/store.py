"""
RMOS Run Artifact Store

JSON-file based store for run artifacts.
Thread-safe, deterministic, easily replaceable with SQLite/Postgres.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .schemas import RunArtifact, RunAttachment, RunDecision, AdvisoryInputRef

STORE_PATH_DEFAULT = "services/api/app/data/runs.json"
_LOCK = threading.Lock()


def _now_utc_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _store_path() -> str:
    """Get the store file path from env or default."""
    return os.getenv("RMOS_RUN_STORE_PATH", STORE_PATH_DEFAULT)


def _read_all() -> Dict[str, Dict[str, Any]]:
    """Read all runs from store."""
    path = _store_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_all(data: Dict[str, Dict[str, Any]]) -> None:
    """Write all runs to store."""
    path = _store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _serialize_artifact(artifact: RunArtifact) -> Dict[str, Any]:
    """Serialize RunArtifact to dict, handling nested dataclasses."""
    d = asdict(artifact)
    # Handle attachments list
    if d.get("attachments"):
        d["attachments"] = [
            asdict(a) if hasattr(a, "__dataclass_fields__") else a
            for a in artifact.attachments or []
        ]
    # Handle decision dataclass
    if artifact.decision is not None:
        d["decision"] = asdict(artifact.decision)
    # Handle advisory_inputs list
    if d.get("advisory_inputs"):
        d["advisory_inputs"] = [
            asdict(a) if hasattr(a, "__dataclass_fields__") else a
            for a in artifact.advisory_inputs or []
        ]
    return d


def _deserialize_artifact(data: Dict[str, Any]) -> RunArtifact:
    """Deserialize dict to RunArtifact."""
    # Handle attachments
    if data.get("attachments"):
        data["attachments"] = [
            RunAttachment(**a) if isinstance(a, dict) else a
            for a in data["attachments"]
        ]
    # Handle decision dataclass
    if data.get("decision") and isinstance(data["decision"], dict):
        data["decision"] = RunDecision(**data["decision"])
    # Handle advisory_inputs list
    if data.get("advisory_inputs"):
        data["advisory_inputs"] = [
            AdvisoryInputRef(**a) if isinstance(a, dict) else a
            for a in data["advisory_inputs"]
        ]
    return RunArtifact(**data)


def create_run_id() -> str:
    """Generate a new run ID."""
    return f"run_{uuid4().hex[:16]}"


def persist_run(artifact: RunArtifact) -> RunArtifact:
    """
    Persist a run artifact to storage.
    
    This is an AUTHORITATIVE operation - only called from RMOS core.
    """
    with _LOCK:
        data = _read_all()
        data[artifact.run_id] = _serialize_artifact(artifact)
        _write_all(data)
    return artifact


def get_run(run_id: str) -> RunArtifact:
    """Retrieve a run artifact by ID."""
    with _LOCK:
        data = _read_all()
    raw = data.get(run_id)
    if raw is None:
        raise KeyError(f"Run {run_id} not found")
    return _deserialize_artifact(raw)


def list_runs(limit: int = 50) -> List[RunArtifact]:
    """List recent runs."""
    with _LOCK:
        data = _read_all()
    items = [_deserialize_artifact(v) for v in data.values()]
    items.sort(key=lambda r: r.created_at_utc, reverse=True)
    return items[:limit]


def list_runs_filtered(
    *,
    limit: int = 50,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    workflow_session_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    machine_id: Optional[str] = None,
) -> List[RunArtifact]:
    """List runs with optional filtering."""
    with _LOCK:
        data = _read_all()

    items = [_deserialize_artifact(v) for v in data.values()]

    def match(r: RunArtifact) -> bool:
        if event_type and r.event_type != event_type:
            return False
        if status and r.status != status:
            return False
        if workflow_session_id and r.workflow_session_id != workflow_session_id:
            return False
        if tool_id and r.tool_id != tool_id:
            return False
        if material_id and r.material_id != material_id:
            return False
        if machine_id and r.machine_id != machine_id:
            return False
        return True

    items = [r for r in items if match(r)]
    items.sort(key=lambda r: r.created_at_utc, reverse=True)
    return items[:limit]


# --- NEW FUNCTIONS FROM GAP ANALYSIS ---

def patch_run_meta(run_id: str, meta_updates: Dict[str, Any]) -> RunArtifact:
    """
    Update the meta field of a run artifact.

    Thread-safe patch operation that preserves existing meta keys
    while adding/updating specified keys.

    Args:
        run_id: The run ID to patch
        meta_updates: Dict of key-value pairs to merge into meta

    Returns:
        Updated RunArtifact

    Raises:
        KeyError: If run_id not found
    """
    with _LOCK:
        data = _read_all()
        if run_id not in data:
            raise KeyError(f"Run {run_id} not found")

        raw = data[run_id]
        if raw.get("meta") is None:
            raw["meta"] = {}
        raw["meta"].update(meta_updates)

        _write_all(data)

    return _deserialize_artifact(raw)
