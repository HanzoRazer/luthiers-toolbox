# File: services/api/app/services/risk_reports_store.py
"""
JSONL-backed risk reports storage for CAM pipeline simulation results.

Provides persistent storage for CAM risk reports instead of in-memory storage.
Each line in the JSONL file is a complete risk report with issues and analytics.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


DEFAULT_RISK_LOG_PATH = os.path.join("data", "cam_risk_reports.jsonl")


def _ensure_dir(path: str) -> None:
    """Ensure parent directory exists for the given file path."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def append_risk_report(
    *,
    job_id: str,
    pipeline_id: Optional[str] = None,
    op_id: Optional[str] = None,
    machine_profile_id: Optional[str] = None,
    post_preset: Optional[str] = None,
    design_source: Optional[str] = None,
    design_path: Optional[str] = None,
    issues: List[Dict[str, Any]] = None,
    analytics: Dict[str, Any] = None,
    path: str = DEFAULT_RISK_LOG_PATH,
) -> Dict[str, Any]:
    """
    Append a risk report to the JSONL log file.

    Returns the stored report with generated id and created_at.
    """
    _ensure_dir(path)

    report_id = uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()

    report: Dict[str, Any] = {
        "id": report_id,
        "created_at": created_at,
        "job_id": job_id,
        "pipeline_id": pipeline_id,
        "op_id": op_id,
        "machine_profile_id": machine_profile_id,
        "post_preset": post_preset,
        "design_source": design_source,
        "design_path": design_path,
        "issues": issues or [],
        "analytics": analytics or {},
    }

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False) + "\n")

    return report


def load_all_risk_reports(path: str = DEFAULT_RISK_LOG_PATH) -> List[Dict[str, Any]]:
    """
    Load all risk reports from the JSONL file.

    Returns:
        List of risk report dictionaries. Returns empty list if file doesn't exist.
    """
    if not os.path.exists(path):
        return []

    reports: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                report = json.loads(line)
                if isinstance(report, dict):
                    reports.append(report)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue

    return reports


def get_recent_reports(
    limit: int = 100,
    path: str = DEFAULT_RISK_LOG_PATH,
) -> List[Dict[str, Any]]:
    """
    Get the most recent risk reports with summary fields.

    Returns:
        List of report summaries, most recent first.
    """
    reports = load_all_risk_reports(path=path)

    summaries = []
    for r in reports[-limit:]:
        analytics = r.get("analytics", {})
        severity_counts = analytics.get("severity_counts", {})
        summaries.append({
            "id": r.get("id"),
            "created_at": r.get("created_at"),
            "job_id": r.get("job_id"),
            "pipeline_id": r.get("pipeline_id"),
            "op_id": r.get("op_id"),
            "machine_profile_id": r.get("machine_profile_id"),
            "post_preset": r.get("post_preset"),
            "total_issues": analytics.get("total_issues", 0),
            "critical_count": severity_counts.get("critical", 0),
            "high_count": severity_counts.get("high", 0),
            "medium_count": severity_counts.get("medium", 0),
            "low_count": severity_counts.get("low", 0),
            "info_count": severity_counts.get("info", 0),
            "risk_score": analytics.get("risk_score", 0),
            "total_extra_time_s": analytics.get("total_extra_time_s", 0),
        })

    return list(reversed(summaries))


def get_reports_by_job_id(
    job_id: str,
    limit: int = 50,
    path: str = DEFAULT_RISK_LOG_PATH,
) -> List[Dict[str, Any]]:
    """
    Get risk reports for a specific job.

    Returns:
        List of full risk reports for the job, most recent first.
    """
    reports = load_all_risk_reports(path=path)
    job_reports = [r for r in reports if r.get("job_id") == job_id]
    return list(reversed(job_reports[-limit:]))


def browse_reports(
    *,
    lane: Optional[str] = None,
    preset: Optional[str] = None,
    start_ts: Optional[float] = None,
    end_ts: Optional[float] = None,
    limit: int = 100,
    path: str = DEFAULT_RISK_LOG_PATH,
) -> List[Dict[str, Any]]:
    """
    Browse risk reports with optional filters.

    Returns:
        List of filtered reports in timeline format, most recent first.
    """
    reports = load_all_risk_reports(path=path)

    results = []
    for r in reports:
        # Apply preset filter
        if preset and r.get("post_preset") != preset:
            continue

        # Parse timestamp for time range filtering
        try:
            created_str = r.get("created_at", "")
            if created_str:
                # Handle ISO format with or without timezone
                if created_str.endswith("Z"):
                    created_str = created_str[:-1] + "+00:00"
                created_ts = datetime.fromisoformat(created_str).timestamp()
            else:
                created_ts = 0
        except (ValueError, AttributeError):
            created_ts = 0

        # Apply time range filters
        if start_ts and created_ts < start_ts:
            continue
        if end_ts and created_ts > end_ts:
            continue

        results.append({
            "id": r.get("id"),
            "created_at": created_ts,
            "lane": lane or "default",
            "job_id": r.get("job_id"),
            "preset": r.get("post_preset"),
            "source": r.get("design_source"),
            "summary": r.get("analytics", {}),
        })

    return list(reversed(results[-limit:]))
