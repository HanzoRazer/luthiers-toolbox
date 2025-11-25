# File: services/api/app/services/job_int_log.py
# NEW – JSONL-backed job intelligence logging for CAM pipeline runs

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

DEFAULT_LOG_PATH = os.path.join("data", "cam_job_log.jsonl")


def _ensure_dir(path: str) -> None:
    """Ensure parent directory exists for the given file path."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def append_job_log_entry(
    run_id: str,
    *,
    job_id: Optional[str] = None,
    job_name: Optional[str] = None,
    machine_id: Optional[str] = None,
    post_id: Optional[str] = None,
    material: Optional[str] = None,
    gcode_key: Optional[str] = None,
    use_helical: bool = False,
    sim_time_s: Optional[float] = None,
    sim_energy_j: Optional[float] = None,
    sim_move_count: Optional[int] = None,
    sim_issue_count: Optional[int] = None,
    sim_max_dev_pct: Optional[float] = None,
    sim_stats: Optional[Dict[str, Any]] = None,
    sim_issues: Optional[Dict[str, Any]] = None,
    geometry_loops: Optional[List[Dict[str, Any]]] = None,
    plan_request: Optional[Dict[str, Any]] = None,
    moves: Optional[List[Dict[str, Any]]] = None,
    moves_path: Optional[str] = None,
    baseline_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    favorite: Optional[bool] = None,
    notes: Optional[str] = None,
    created_at: Optional[str] = None,
    source: str = "pipeline_run",
    path: str = DEFAULT_LOG_PATH,
) -> None:
    """
    Append a job run entry to the JSONL log file.
    
    Each line in the log is a JSON object representing one pipeline run.
    B20 extends this schema with optional artifacts (geometry, plan, moves, baseline).
    """
    _ensure_dir(path)
    
    # Import here to avoid circular dependencies
    from datetime import datetime, timezone
    
    if created_at is None:
        created_at = datetime.now(timezone.utc).isoformat()
    
    entry: Dict[str, Any] = {
        "run_id": run_id,
        "job_id": job_id,
        "job_name": job_name,
        "machine_id": machine_id,
        "post_id": post_id,
        "material": material,
        "gcode_key": gcode_key,
        "use_helical": bool(use_helical),
        "sim_time_s": sim_time_s,
        "sim_energy_j": sim_energy_j,
        "sim_move_count": sim_move_count,
        "sim_issue_count": sim_issue_count,
        "sim_max_dev_pct": sim_max_dev_pct,
        "sim_stats": sim_stats or {},
        "sim_issues": sim_issues or {},
        "created_at": created_at,
        "source": source,
        "baseline_id": baseline_id,
        "notes": notes or "",
        "tags": tags or [],
        "favorite": bool(favorite) if favorite is not None else False,
    }

    if geometry_loops is not None:
        entry["geometry_loops"] = geometry_loops
    if plan_request is not None:
        entry["plan_request"] = plan_request
    if moves is not None:
        entry["moves"] = moves
    if moves_path is not None:
        entry["moves_path"] = moves_path
    
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_all_job_logs(path: str = DEFAULT_LOG_PATH) -> List[Dict[str, Any]]:
    """
    Load all job log entries from the JSONL file.
    
    Returns:
        List of dictionaries, one per log entry. Returns empty list if file doesn't exist.
    """
    if not os.path.exists(path):
        return []
    
    entries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict):
                    entries.append(entry)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
    
    return entries


def find_job_log_by_run_id(
    run_id: str,
    path: str = DEFAULT_LOG_PATH,
) -> Optional[Dict[str, Any]]:
    """
    Find a specific job log entry by run_id.
    
    Returns:
        Dictionary with entry data, or None if not found.
    """
    entries = load_all_job_logs(path=path)
    for entry in entries:
        if entry.get("run_id") == run_id:
            return entry
    return None


def update_job_baseline(
    run_id: str,
    baseline_id: Optional[str],
    path: str = DEFAULT_LOG_PATH,
) -> bool:
    """
    Update the baseline_id field for an existing job log entry.
    
    Args:
        run_id: Job run identifier
        baseline_id: Baseline ID to set (or None to clear)
        path: Path to JSONL log file
    
    Returns:
        True if job found and updated, False otherwise.
    """
    if not os.path.exists(path):
        return False
    
    # Read all entries
    entries = load_all_job_logs(path=path)
    found = False
    
    # Update matching entry
    for entry in entries:
        if entry.get("run_id") == run_id:
            entry["baseline_id"] = baseline_id
            found = True
            break
    
    if not found:
        return False
    
    # Rewrite entire file (JSONL doesn't support in-place updates)
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return True
