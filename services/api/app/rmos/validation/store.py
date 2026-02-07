"""
Validation Log Store

Persists validation run results with timestamps for audit trail.

Storage structure:
    {RMOS_RUNS_DIR}/validation_logs/
        sessions/
            {session_id}.json      # Full session (summary + all results)
        runs/
            {YYYY-MM-DD}/
                {run_id}.json      # Individual scenario run result
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _get_validation_root() -> Path:
    """Get validation logs root directory."""
    from ..runs_v2.store import _get_store_root
    runs_root = Path(_get_store_root()).expanduser().resolve()
    return runs_root / "validation_logs"


class ValidationRunRecord(BaseModel):
    """A single scenario validation run record."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    scenario_name: str
    tier: str
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    expected_decision: List[str]
    actual_decision: str
    expected_rules_any: List[str] = Field(default_factory=list)
    actual_rules: List[str] = Field(default_factory=list)
    expected_export_allowed: bool
    actual_export_allowed: bool

    decision_match: bool
    rules_match: bool
    export_match: bool
    passed: bool

    feasibility_input: Dict[str, Any] = Field(default_factory=dict)
    feasibility_result: Dict[str, Any] = Field(default_factory=dict)
    notes: str = ""

    # Session linkage
    session_id: Optional[str] = None


class ValidationSessionRecord(BaseModel):
    """A validation session containing multiple scenario runs."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at_utc: Optional[str] = None

    # Filters applied
    tier_filter: Optional[str] = None
    scenario_filter: Optional[str] = None

    # Summary
    total: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: str = "0%"
    by_tier: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    red_leaks: int = 0
    red_leak_scenarios: List[str] = Field(default_factory=list)
    release_authorized: bool = False

    # Run IDs in this session
    run_ids: List[str] = Field(default_factory=list)

    # Operator info
    operator: Optional[str] = None
    notes: str = ""


def write_validation_run(record: ValidationRunRecord) -> str:
    """
    Write a single validation run record.

    Returns the run_id.
    """
    root = _get_validation_root()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    runs_dir = root / "runs" / date_str
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_path = runs_dir / f"{record.run_id}.json"
    tmp_path = run_path.with_suffix(".tmp")

    data = record.model_dump()
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    os.replace(tmp_path, run_path)
    return record.run_id


def write_validation_session(record: ValidationSessionRecord) -> str:
    """
    Write a validation session record.

    Returns the session_id.
    """
    root = _get_validation_root()
    sessions_dir = root / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    session_path = sessions_dir / f"{record.session_id}.json"
    tmp_path = session_path.with_suffix(".tmp")

    data = record.model_dump()
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    os.replace(tmp_path, session_path)
    return record.session_id


def get_validation_run(run_id: str) -> Optional[ValidationRunRecord]:
    """Retrieve a validation run by ID (searches all date directories)."""
    root = _get_validation_root()
    runs_dir = root / "runs"

    if not runs_dir.exists():
        return None

    # Search all date directories
    for date_dir in sorted(runs_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        run_path = date_dir / f"{run_id}.json"
        if run_path.exists():
            with open(run_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ValidationRunRecord(**data)

    return None


def get_validation_session(session_id: str) -> Optional[ValidationSessionRecord]:
    """Retrieve a validation session by ID."""
    root = _get_validation_root()
    session_path = root / "sessions" / f"{session_id}.json"

    if not session_path.exists():
        return None

    with open(session_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return ValidationSessionRecord(**data)


def list_validation_sessions(
    limit: int = 50,
    offset: int = 0,
) -> List[ValidationSessionRecord]:
    """List validation sessions, most recent first."""
    root = _get_validation_root()
    sessions_dir = root / "sessions"

    if not sessions_dir.exists():
        return []

    # Get all session files sorted by mtime descending
    files = sorted(
        sessions_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    results: List[ValidationSessionRecord] = []
    for f in files[offset:offset + limit]:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            results.append(ValidationSessionRecord(**data))
        except (OSError, json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
            continue

    return results


def list_validation_runs(
    date: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[ValidationRunRecord]:
    """
    List validation runs.

    Args:
        date: Filter by date (YYYY-MM-DD)
        session_id: Filter by session ID
        limit: Max results
        offset: Pagination offset

    Returns:
        List of validation run records.
    """
    root = _get_validation_root()
    runs_dir = root / "runs"

    if not runs_dir.exists():
        return []

    # Collect all run files
    files: List[Path] = []

    if date:
        date_dir = runs_dir / date
        if date_dir.exists():
            files = list(date_dir.glob("*.json"))
    else:
        for date_dir in runs_dir.iterdir():
            if date_dir.is_dir():
                files.extend(date_dir.glob("*.json"))

    # Sort by mtime descending
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    results: List[ValidationRunRecord] = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            record = ValidationRunRecord(**data)

            # Apply session filter
            if session_id and record.session_id != session_id:
                continue

            results.append(record)

            if len(results) >= offset + limit:
                break
        except (OSError, json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
            continue

    return results[offset:offset + limit]


def get_latest_session_summary() -> Optional[Dict[str, Any]]:
    """Get the summary of the most recent validation session."""
    sessions = list_validation_sessions(limit=1)
    if not sessions:
        return None

    session = sessions[0]
    return {
        "session_id": session.session_id,
        "started_at_utc": session.started_at_utc,
        "completed_at_utc": session.completed_at_utc,
        "total": session.total,
        "passed": session.passed,
        "failed": session.failed,
        "pass_rate": session.pass_rate,
        "red_leaks": session.red_leaks,
        "release_authorized": session.release_authorized,
    }
