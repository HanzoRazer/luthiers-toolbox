"""
Run Artifacts Index

File-based artifact indexing and querying for RMOS.
Implements RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md.

Security: All paths are validated to prevent traversal attacks.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _artifact_root() -> Path:
    """
    Get the artifact storage root directory.

    Can be configured via RMOS_ARTIFACT_ROOT environment variable.
    Defaults to data/run_artifacts.
    """
    root = os.getenv("RMOS_ARTIFACT_ROOT", "data/run_artifacts")
    return Path(root).resolve()


def _safe_load_json(path: Path) -> Dict[str, Any]:
    """
    Safely load JSON from a path within the artifact root.

    Security: Validates path is within artifact root to prevent traversal.
    """
    root = _artifact_root()
    try:
        rp = path.resolve()
    except Exception:
        raise ValueError("Invalid artifact path")

    # Ensure path is within artifact root
    if root not in rp.parents and rp != root:
        raise ValueError("Path traversal blocked")

    return json.loads(rp.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class RunIndexRow:
    """
    Lightweight index entry for listing runs.

    Contains just enough information for UI list views
    without loading the full artifact payload.
    """
    artifact_id: str
    kind: str              # "feasibility" | "toolpaths" | etc.
    status: str            # "OK" | "BLOCKED" | "ERROR"
    created_utc: str       # ISO 8601 timestamp
    session_id: str
    index_meta: Dict[str, Any]  # tool_id, material_id, machine_id, etc.


def list_artifacts() -> List[RunIndexRow]:
    """
    List all artifacts in the storage directory.

    Returns list sorted by created_utc (newest first).
    Skips malformed artifacts silently.
    """
    root = _artifact_root()
    if not root.exists():
        return []

    rows: List[RunIndexRow] = []
    for p in root.glob("*.json"):
        try:
            obj = _safe_load_json(p)
            rows.append(
                RunIndexRow(
                    artifact_id=obj.get("artifact_id", p.stem),
                    kind=obj.get("kind", "unknown"),
                    status=obj.get("status", "UNKNOWN"),
                    created_utc=obj.get("created_utc", ""),
                    session_id=obj.get("session_id", ""),
                    index_meta=obj.get("index_meta", {}) or {},
                )
            )
        except Exception:
            # Ignore malformed artifacts in index listing (but keep raw file for forensics)
            continue

    # Newest first (string ISO sorts ok for same format)
    rows.sort(key=lambda r: r.created_utc, reverse=True)
    return rows


def get_artifact(artifact_id: str) -> Dict[str, Any]:
    """
    Get a single artifact by ID.

    Raises FileNotFoundError if artifact doesn't exist.
    Raises ValueError on path traversal attempts.
    """
    # Security: Reject suspicious artifact IDs
    if not artifact_id or any(c in artifact_id for c in ("/", "\\", "..")):
        raise ValueError(f"Invalid artifact_id: {artifact_id}")

    root = _artifact_root()
    path = root / f"{artifact_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_id}")
    return _safe_load_json(path)


def _match_filters(row: RunIndexRow, filters: Dict[str, Any]) -> bool:
    """
    Check if a row matches the given filters.

    Supported filters: kind, status, tool_id, material_id, machine_id, session_id,
                      parent_batch_decision_artifact_id, parent_batch_plan_artifact_id,
                      parent_batch_spec_artifact_id
    """
    kind = filters.get("kind")
    if kind and row.kind != kind:
        return False

    status = filters.get("status")
    if status and row.status != status:
        return False

    session_id = filters.get("session_id")
    if session_id and row.session_id != session_id:
        return False

    tool_id = filters.get("tool_id")
    if tool_id and (row.index_meta.get("tool_id") != tool_id):
        return False

    material_id = filters.get("material_id")
    if material_id and (row.index_meta.get("material_id") != material_id):
        return False

    machine_id = filters.get("machine_id")
    if machine_id and (row.index_meta.get("machine_id") != machine_id):
        return False

    # Parent batch artifact filters
    parent_decision = filters.get("parent_batch_decision_artifact_id")
    if parent_decision and (row.index_meta.get("parent_batch_decision_artifact_id") != parent_decision):
        return False

    parent_plan = filters.get("parent_batch_plan_artifact_id")
    if parent_plan and (row.index_meta.get("parent_batch_plan_artifact_id") != parent_plan):
        return False

    parent_spec = filters.get("parent_batch_spec_artifact_id")
    if parent_spec and (row.index_meta.get("parent_batch_spec_artifact_id") != parent_spec):
        return False

    return True


def query_artifacts(
    *,
    cursor: Optional[str],
    limit: int,
    filters: Dict[str, Any],
) -> Tuple[List[RunIndexRow], Optional[str]]:
    """
    Query artifacts with filtering and pagination.

    Cursor is artifact_id of the last item seen.
    Returns (items, next_cursor) where next_cursor is None at end.

    Limit is clamped to 1-200 range per governance contract.
    """
    limit = max(1, min(int(limit), 200))
    rows = [r for r in list_artifacts() if _match_filters(r, filters)]

    if cursor:
        # Find cursor position and skip to next item
        idx = next((i for i, r in enumerate(rows) if r.artifact_id == cursor), None)
        if idx is not None:
            rows = rows[idx + 1:]

    page = rows[:limit]
    next_cursor = page[-1].artifact_id if len(rows) > limit else None

    return page, next_cursor


def save_artifact(artifact: Dict[str, Any]) -> str:
    """
    Save an artifact to storage.

    Returns the artifact_id.
    Creates the storage directory if it doesn't exist.
    """
    root = _artifact_root()
    root.mkdir(parents=True, exist_ok=True)

    artifact_id = artifact.get("artifact_id")
    if not artifact_id:
        raise ValueError("Artifact must have an artifact_id")

    # Security: Validate artifact_id
    if any(c in artifact_id for c in ("/", "\\", "..")):
        raise ValueError(f"Invalid artifact_id: {artifact_id}")

    path = root / f"{artifact_id}.json"
    path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    return artifact_id
