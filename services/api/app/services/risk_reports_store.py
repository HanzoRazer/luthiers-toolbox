# services/api/app/services/risk_reports_store.py

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


RISK_REPORTS_PATH = Path("data/cam_risk_reports.json")


@dataclass
class RiskReport:
    """CAM risk report for timeline tracking."""
    id: str
    created_at: float
    lane: str  # "rosette", "adaptive", etc.
    job_id: Optional[str] = None
    preset: Optional[str] = None
    source: str = "pipeline"
    steps: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)


def _load_reports() -> List[Dict[str, Any]]:
    """Load stored reports from disk."""
    if not RISK_REPORTS_PATH.exists():
        RISK_REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        return []

    try:
        raw = RISK_REPORTS_PATH.read_text(encoding="utf-8")
        if not raw.strip():
            return []
        return json.loads(raw)
    except (OSError, json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
        # Corrupted file — reset to empty to keep system healthy
        return []


def _save_reports(reports: List[Dict[str, Any]]) -> None:
    """Save reports to JSON file."""
    RISK_REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RISK_REPORTS_PATH, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)


def create_risk_report(
    *,
    lane: str,
    job_id: Optional[str],
    preset: Optional[str],
    source: str,
    steps: List[Dict[str, Any]],
    summary: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
) -> RiskReport:
    """Create and persist a new risk report entry."""

    timestamp = time.time()
    report_id = f"{lane}_risk_{int(timestamp * 1000)}"

    report = RiskReport(
        id=report_id,
        created_at=timestamp,
        lane=lane,
        job_id=job_id,
        preset=preset,
        source=source,
        steps=steps,
        summary=summary,
        meta=meta or {},
    )

    reports = _load_reports()
    reports.append(asdict(report))
    _save_reports(reports)

    return report


def list_risk_reports(
    lane: Optional[str] = None,
    preset: Optional[str] = None,
    source: Optional[str] = None,
    job_id: Optional[str] = None,
    created_after: Optional[float] = None,
    created_before: Optional[float] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """List risk reports with optional filters."""
    reports = _load_reports()
    
    # Apply filters
    filtered = reports
    if lane:
        filtered = [r for r in filtered if r.get("lane") == lane]
    if preset:
        filtered = [r for r in filtered if r.get("preset") == preset]
    if source:
        filtered = [r for r in filtered if r.get("source") == source]
    if job_id:
        filtered = [r for r in filtered if r.get("job_id") == job_id]
    if created_after is not None:
        filtered = [r for r in filtered if r.get("created_at", 0) >= created_after]
    if created_before is not None:
        filtered = [r for r in filtered if r.get("created_at", 0) <= created_before]
    
    # Sort by newest first
    filtered.sort(key=lambda r: r.get("created_at", 0), reverse=True)
    
    # Apply limit
    return filtered[:limit]


def latest_risk_by_job_ids(job_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Return the latest risk report for each requested job_id."""
    if not job_ids:
        return {}

    reports = _load_reports()
    reports.sort(key=lambda r: r.get("created_at", 0.0), reverse=True)

    wanted = set(job_ids)
    result: Dict[str, Dict[str, Any]] = {}

    for report in reports:
        jid = report.get("job_id")
        if not jid or jid not in wanted or jid in result:
            continue
        result[jid] = report
        if len(result) == len(wanted):
            break

    return result
