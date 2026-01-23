"""
Advisory Artifact Store

Simple file-based storage for advisory artifacts.
Date-partitioned like runs_v2.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .schemas import AdvisoryArtifactV1


def _get_store_dir() -> Path:
    """Get the advisory artifacts storage directory."""
    base = os.getenv("RMOS_ADVISORIES_DIR", "")
    if base:
        return Path(base)
    # Default: alongside runs_v2
    runs_dir = os.getenv("RMOS_RUNS_DIR", "")
    if runs_dir:
        return Path(runs_dir).parent / "advisories"
    return Path("data/rmos/advisories")


def _partition_path(advisory_id: str, created_at: str) -> Path:
    """
    Generate date-partitioned path for artifact.

    Format: {YYYY-MM-DD}/{advisory_id}.json
    """
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    store_dir = _get_store_dir()
    return store_dir / date_str / f"{advisory_id}.json"


def persist_advisory(artifact: AdvisoryArtifactV1) -> Path:
    """
    Persist an advisory artifact to storage.

    Returns the path where artifact was written.
    """
    path = _partition_path(artifact.advisory_id, artifact.created_at_utc)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write via temp file
    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(
            artifact.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(str(tmp_path), str(path))
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    return path


def load_advisory(advisory_id: str) -> Optional[AdvisoryArtifactV1]:
    """
    Load an advisory artifact by ID.

    Scans date partitions to find the artifact.
    Returns None if not found.
    """
    store_dir = _get_store_dir()
    if not store_dir.exists():
        return None

    # Scan all date partitions
    for date_dir in sorted(store_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        artifact_path = date_dir / f"{advisory_id}.json"
        if artifact_path.exists():
            try:
                data = json.loads(artifact_path.read_text(encoding="utf-8"))
                return AdvisoryArtifactV1.model_validate(data)
            except Exception:
                return None

    return None


def list_advisories(
    *,
    limit: int = 50,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[AdvisoryArtifactV1]:
    """
    List advisory artifacts, newest first.

    Args:
        limit: Maximum number to return
        date_from: Optional ISO date string (inclusive)
        date_to: Optional ISO date string (inclusive)
    """
    store_dir = _get_store_dir()
    if not store_dir.exists():
        return []

    results: list[AdvisoryArtifactV1] = []

    for date_dir in sorted(store_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue

        date_str = date_dir.name

        # Filter by date range
        if date_from and date_str < date_from:
            continue
        if date_to and date_str > date_to:
            continue

        for artifact_path in sorted(date_dir.glob("*.json"), reverse=True):
            if len(results) >= limit:
                return results

            try:
                data = json.loads(artifact_path.read_text(encoding="utf-8"))
                artifact = AdvisoryArtifactV1.model_validate(data)
                results.append(artifact)
            except Exception:
                continue

    return results
