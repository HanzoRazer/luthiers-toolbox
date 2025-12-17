from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _artifact_root() -> Path:
    root = os.getenv("RMOS_ARTIFACT_ROOT", "data/run_artifacts")
    return Path(root).resolve()


def _safe_load_json(path: Path) -> Dict[str, Any]:
    # Hard safety: only load if it’s inside artifact root
    root = _artifact_root()
    try:
        rp = path.resolve()
    except Exception:
        raise ValueError("Invalid artifact path")

    if root not in rp.parents and rp != root:
        raise ValueError("Path traversal blocked")

    return json.loads(rp.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class RunIndexRow:
    artifact_id: str
    kind: str
    status: str
    created_utc: str
    session_id: str
    index_meta: Dict[str, Any]


def list_artifacts() -> List[RunIndexRow]:
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
    root = _artifact_root()
    path = root / f"{artifact_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_id}")
    return _safe_load_json(path)


def _match_filters(row: RunIndexRow, filters: Dict[str, Any]) -> bool:
    # Supported filters: kind, status, tool_id, material_id, machine_id, session_id
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

    return True


def query_artifacts(
    *,
    cursor: Optional[str],
    limit: int,
    filters: Dict[str, Any],
) -> Tuple[List[RunIndexRow], Optional[str]]:
    """
    Cursor is artifact_id of the last item seen (stable enough for filesystem listing).
    Returns next_cursor as the last artifact_id in returned page.
    """
    limit = max(1, min(int(limit), 200))
    rows = [r for r in list_artifacts() if _match_filters(r, filters)]

    if cursor: