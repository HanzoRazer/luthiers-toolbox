# services/api/app/services/job_risk_store.py
"""
Job Risk Store - Phase 18.0

JSONL-based storage for CAM risk reports.
Simple append-only log with in-memory caching.
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..schemas.cam_risk import RiskReportIn, RiskReportOut, RiskReportSummary


class JobRiskStore:
    """
    Simple JSONL store for risk reports.
    Each report is appended as a single line.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            # Default to data/risk_reports.jsonl in API directory
            storage_path = Path(__file__).parent.parent / "data" / "risk_reports.jsonl"
        
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure file exists
        if not self.storage_path.exists():
            self.storage_path.touch()

    def save(self, report_in: RiskReportIn) -> RiskReportOut:
        """
        Save a new risk report.
        Returns the saved report with ID and timestamp.
        """
        report_id = str(uuid.uuid4())
        created_at = datetime.utcnow()

        report_out = RiskReportOut(
            id=report_id,
            created_at=created_at,
            job_id=report_in.job_id,
            pipeline_id=report_in.pipeline_id,
            op_id=report_in.op_id,
            machine_profile_id=report_in.machine_profile_id,
            post_preset=report_in.post_preset,
            design_source=report_in.design_source,
            design_path=report_in.design_path,
            issues=report_in.issues,
            analytics=report_in.analytics,
        )

        # Append to JSONL file
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(report_out.model_dump(), default=str) + "\n")

        return report_out

    def get_timeline(self, job_id: str, limit: int = 50) -> List[RiskReportOut]:
        """
        Get risk timeline for a specific job_id.
        Returns reports sorted by created_at (newest first).
        """
        reports = []
        
        if not self.storage_path.exists():
            return reports

        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("job_id") == job_id:
                        # Parse datetime string back to datetime object
                        if isinstance(data.get("created_at"), str):
                            data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                        reports.append(RiskReportOut(**data))
                except Exception as e:
                    print(f"Warning: Failed to parse line: {e}")
                    continue

        # Sort by created_at descending (newest first)
        reports.sort(key=lambda r: r.created_at, reverse=True)
        
        return reports[:limit]

    def get_recent(self, limit: int = 100) -> List[RiskReportSummary]:
        """
        Get recent risk reports (all jobs).
        Returns lightweight summaries sorted by created_at (newest first).
        """
        reports = []
        
        if not self.storage_path.exists():
            return reports

        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    
                    # Parse datetime
                    if isinstance(data.get("created_at"), str):
                        created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                    else:
                        created_at = data.get("created_at", datetime.utcnow())
                    
                    # Extract analytics
                    analytics = data.get("analytics", {})
                    severity_counts = analytics.get("severity_counts", {})
                    
                    summary = RiskReportSummary(
                        id=data.get("id"),
                        created_at=created_at,
                        job_id=data.get("job_id"),
                        pipeline_id=data.get("pipeline_id"),
                        op_id=data.get("op_id"),
                        machine_profile_id=data.get("machine_profile_id"),
                        post_preset=data.get("post_preset"),
                        total_issues=analytics.get("total_issues", 0),
                        critical_count=severity_counts.get("critical", 0),
                        high_count=severity_counts.get("high", 0),
                        medium_count=severity_counts.get("medium", 0),
                        low_count=severity_counts.get("low", 0),
                        info_count=severity_counts.get("info", 0),
                        risk_score=analytics.get("risk_score", 0.0),
                        total_extra_time_s=analytics.get("total_extra_time_s", 0.0),
                    )
                    
                    reports.append(summary)
                except Exception as e:
                    print(f"Warning: Failed to parse line: {e}")
                    continue

        # Sort by created_at descending (newest first)
        reports.sort(key=lambda r: r.created_at, reverse=True)
        
        return reports[:limit]


# Singleton instance
_store: Optional[JobRiskStore] = None


def get_risk_store() -> JobRiskStore:
    """Get or create the singleton risk store."""
    global _store
    if _store is None:
        _store = JobRiskStore()
    return _store
