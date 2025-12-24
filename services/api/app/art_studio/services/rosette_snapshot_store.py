"""
Rosette Snapshot Store - Bundle 31.0.27 + H1 Hardening

File-based persistence for rosette design snapshots.

H1 Hardening:
- Path traversal / unsafe filenames (snapshot_id validation)
- Partial writes / race corruption (atomic write via temp + os.replace + fsync)
- Custom SnapshotIdError for clean error handling
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from ..schemas.rosette_snapshot import RosetteDesignSnapshot
from ..schemas.rosette_params import RosetteParamSpec


# Default storage location
SNAPSHOT_DIR_DEFAULT = "services/api/data/art_studio/snapshots"

# Strict, filename-safe IDs only
_SNAPSHOT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

# Keep it bounded to avoid weird filesystem edge cases
_MAX_SNAPSHOT_ID_LEN = 64


class SnapshotIdError(ValueError):
    """Raised when snapshot_id is invalid or unsafe."""


def _snapshot_dir() -> Path:
    """Get snapshot storage directory from environment or default."""
    path = Path(os.getenv("ART_STUDIO_SNAPSHOTS_DIR", SNAPSHOT_DIR_DEFAULT))
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_snapshot_id(snapshot_id: str) -> str:
    """
    Validate snapshot_id is safe for filesystem usage.

    - ASCII alnum + _ -
    - bounded length (max 64)
    - no path separators

    Returns:
        The validated snapshot_id (stripped)

    Raises:
        SnapshotIdError: If snapshot_id is invalid or unsafe
    """
    if snapshot_id is None:
        raise SnapshotIdError("snapshot_id is required")

    sid = str(snapshot_id).strip()
    if not sid:
        raise SnapshotIdError("snapshot_id is required")

    if len(sid) > _MAX_SNAPSHOT_ID_LEN:
        raise SnapshotIdError(f"snapshot_id too long (max {_MAX_SNAPSHOT_ID_LEN})")

    if "/" in sid or "\\" in sid:
        raise SnapshotIdError("invalid snapshot_id")

    if not _SNAPSHOT_ID_RE.match(sid):
        raise SnapshotIdError("invalid snapshot_id (allowed: a-z A-Z 0-9 _ -)")

    return sid


def _validate_snapshot_id(snapshot_id: str) -> bool:
    """
    Legacy validation function for backward compatibility.

    Prefer using validate_snapshot_id() which raises SnapshotIdError.
    """
    try:
        validate_snapshot_id(snapshot_id)
        return True
    except SnapshotIdError:
        return False


def _safe_snapshot_path(snapshot_id: str) -> Path:
    """
    Construct a safe path for a snapshot file and ensure it stays within snapshot_dir.

    Raises:
        SnapshotIdError: If snapshot_id is invalid or would escape the snapshot directory
    """
    sid = validate_snapshot_id(snapshot_id)
    base = _snapshot_dir().resolve()
    path = (base / f"{sid}.json").resolve()

    # Ensure no traversal: path must be inside base
    if base not in path.parents and path.parent != base:
        raise SnapshotIdError("invalid snapshot_id")

    return path


def _atomic_write_text(target_path: Path, text: str, encoding: str = "utf-8") -> None:
    """
    Atomic write:
    - write to temp file in same directory
    - fsync
    - os.replace into place (atomic on Windows/Linux for same filesystem)
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    dir_path = str(target_path.parent)

    fd, tmp_path = tempfile.mkstemp(prefix=target_path.name + ".", suffix=".tmp", dir=dir_path)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target_path)
    finally:
        # If replace failed, cleanup tmp file
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def compute_design_fingerprint(design: RosetteParamSpec) -> str:
    """
    Compute a deterministic fingerprint for a design.

    Used for deduplication and change detection.
    """
    # Serialize design to JSON with sorted keys for determinism
    design_json = design.model_dump_json(exclude_none=True)
    return hashlib.sha256(design_json.encode()).hexdigest()[:16]


def create_snapshot_id() -> str:
    """Generate a unique snapshot ID."""
    return f"snap_{uuid4().hex[:12]}"


def save_snapshot(snapshot: RosetteDesignSnapshot) -> RosetteDesignSnapshot:
    """
    Save a snapshot to disk.

    Args:
        snapshot: The snapshot to save

    Returns:
        The saved snapshot (with updated timestamp if needed)

    Raises:
        SnapshotIdError: If snapshot_id is invalid or unsafe
    """
    # Validate and get safe path (raises SnapshotIdError if invalid)
    path = _safe_snapshot_path(snapshot.snapshot_id)

    # Atomic write with fsync
    payload = snapshot.model_dump_json(indent=2)
    _atomic_write_text(path, payload, encoding="utf-8")

    return snapshot


def load_snapshot(snapshot_id: str) -> Optional[RosetteDesignSnapshot]:
    """
    Load a snapshot from disk.

    Args:
        snapshot_id: The snapshot ID to load

    Returns:
        The snapshot if found, None otherwise

    Raises:
        SnapshotIdError: If snapshot_id is invalid or unsafe
    """
    # Validate and get safe path (raises SnapshotIdError if invalid)
    path = _safe_snapshot_path(snapshot_id)

    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return RosetteDesignSnapshot.model_validate(data)
    except Exception:
        return None


def delete_snapshot(snapshot_id: str) -> bool:
    """
    Delete a snapshot from disk.

    Args:
        snapshot_id: The snapshot ID to delete

    Returns:
        True if deleted, False if not found

    Raises:
        SnapshotIdError: If snapshot_id is invalid or unsafe
    """
    # Validate and get safe path (raises SnapshotIdError if invalid)
    path = _safe_snapshot_path(snapshot_id)

    if not path.exists():
        return False

    path.unlink()
    return True


def list_snapshots(
    *,
    limit: int = 50,
    offset: int = 0,
    tag: Optional[str] = None,
) -> List[RosetteDesignSnapshot]:
    """
    List snapshots with optional filtering.

    Args:
        limit: Maximum number of snapshots to return
        offset: Number of snapshots to skip
        tag: Filter by tag (optional)

    Returns:
        List of snapshots sorted by creation time (newest first)
    """
    snapshots: List[RosetteDesignSnapshot] = []

    snapshot_dir = _snapshot_dir()
    paths = sorted(
        snapshot_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for path in paths:
        if path.name.endswith(".tmp"):
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            snapshot = RosetteDesignSnapshot.model_validate(data)

            # Apply tag filter
            if tag and tag not in (snapshot.metadata.tags or []):
                continue

            snapshots.append(snapshot)
        except Exception:
            continue

    # Apply pagination
    return snapshots[offset:offset + limit]


def count_snapshots(*, tag: Optional[str] = None) -> int:
    """
    Count snapshots with optional filtering.

    Args:
        tag: Filter by tag (optional)

    Returns:
        Total count of matching snapshots
    """
    if tag is None:
        # Fast path: just count files
        return len(list(_snapshot_dir().glob("*.json")))

    # Slow path: need to load and filter
    return len(list_snapshots(limit=10000, tag=tag))


def find_by_fingerprint(fingerprint: str) -> Optional[RosetteDesignSnapshot]:
    """
    Find a snapshot by its design fingerprint.

    Args:
        fingerprint: The design fingerprint to search for

    Returns:
        The first matching snapshot, or None if not found
    """
    for path in _snapshot_dir().glob("*.json"):
        if path.name.endswith(".tmp"):
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("design_fingerprint") == fingerprint:
                return RosetteDesignSnapshot.model_validate(data)
        except Exception:
            continue

    return None
