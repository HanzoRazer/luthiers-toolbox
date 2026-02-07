"""
Phase 27.1 + 27.2: Rosette Compare Mode
Compare risk log service for job-tagged diff history tracking
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.compare_baseline import CompareDiffStats

LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "compare_risk_log.json"


def _load_log() -> Dict[str, Any]:
    """Load compare risk log from disk."""
    if not LOG_PATH.exists():
        return {"entries": []}
    try:
        with LOG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
        return {"entries": []}


def _save_log(data: Dict[str, Any]) -> None:
    """Save compare risk log to disk."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def log_compare_diff(
    job_id: str | None,
    lane: str,
    baseline_id: str,
    stats: CompareDiffStats,
    preset: str | None = None,
) -> None:
    """Log a compare diff entry for risk/job analytics.
    
    Phase 27.1: Track geometry changes over time for job-based analysis.
    Phase 27.4: Include optional preset label (Safe/Aggressive/etc.).
    """
    data = _load_log()
    entries = data.get("entries") or []

    entry = {
        "ts": datetime.utcnow().isoformat(),
        "job_id": job_id,
        "lane": lane,
        "baseline_id": baseline_id,
        "baseline_path_count": stats.baseline_path_count,
        "current_path_count": stats.current_path_count,
        "added_paths": stats.added_paths,
        "removed_paths": stats.removed_paths,
        "unchanged_paths": stats.unchanged_paths,
        "preset": preset,
    }
    entries.append(entry)
    data["entries"] = entries
    _save_log(data)


def list_compare_history(
    lane: Optional[str] = None,
    job_id: Optional[str] = None,
) -> List[dict]:
    """Return filtered compare history entries from compare_risk_log.json.
    
    Phase 27.2: Query history for Compare History pane.
    Filter by lane and/or job_id if provided.
    """
    data = _load_log()
    entries = data.get("entries") or []
    out: List[dict] = []

    for entry in entries:
        if lane and entry.get("lane") != lane:
            continue
        if job_id and entry.get("job_id") != job_id:
            continue
        out.append(entry)

    # newest first
    out.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return out
