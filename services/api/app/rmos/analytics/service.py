"""RMOS Analytics Service - Compute metrics from run store."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..runs_v2.store import RunStoreV2
from ..runs_v2.schemas import RunArtifact


class AnalyticsService:
    """Compute analytics from RMOS run store."""

    def __init__(self, store: Optional[RunStoreV2] = None):
        self._store = store or RunStoreV2()

    def get_summary(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get aggregate summary statistics."""
        runs = self._store.list_runs(
            limit=10000,
            date_from=date_from,
            date_to=date_to,
        )

        total = len(runs)
        by_status = defaultdict(int)
        by_risk = defaultdict(int)
        by_mode = defaultdict(int)

        for run in runs:
            by_status[run.status] += 1
            if run.decision:
                by_risk[run.decision.risk_level] += 1
            if run.mode:
                by_mode[run.mode] += 1

        return {
            "total_runs": total,
            "by_status": dict(by_status),
            "by_risk_level": dict(by_risk),
            "by_mode": dict(by_mode),
            "period_start": date_from.isoformat() if date_from else None,
            "period_end": date_to.isoformat() if date_to else None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_lane_analytics(
        self,
        limit_recent: int = 100,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get analytics by operation lane (mode)."""
        runs = self._store.list_runs(
            limit=limit_recent,
            date_from=date_from,
            date_to=date_to,
        )

        lanes: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total": 0,
            "ok": 0,
            "blocked": 0,
            "error": 0,
            "green": 0,
            "yellow": 0,
            "red": 0,
        })

        for run in runs:
            lane_key = run.mode or "unknown"
            lanes[lane_key]["total"] += 1

            status_lower = (run.status or "").lower()
            if status_lower in lanes[lane_key]:
                lanes[lane_key][status_lower] += 1

            if run.decision:
                risk_lower = (run.decision.risk_level or "").lower()
                if risk_lower in lanes[lane_key]:
                    lanes[lane_key][risk_lower] += 1

        # Convert to list format
        lane_list = [
            {"lane": k, **v}
            for k, v in sorted(lanes.items(), key=lambda x: x[1]["total"], reverse=True)
        ]

        return {
            "lanes": lane_list,
            "total_runs": len(runs),
            "period_start": (date_from or datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
            "period_end": (date_to or datetime.now(timezone.utc)).isoformat(),
        }

    def get_risk_timeline(
        self,
        preset_id: Optional[str] = None,
        limit: int = 50,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get risk decision timeline."""
        runs = self._store.list_runs(
            limit=limit * 2,  # Over-fetch to account for filtering
            date_from=date_from,
            date_to=date_to,
        )

        events = []
        for run in runs:
            if not run.decision:
                continue

            # Filter by preset_id if specified
            if preset_id:
                run_preset = (run.meta or {}).get("preset_id")
                if run_preset != preset_id:
                    continue

            events.append({
                "run_id": run.run_id,
                "timestamp": run.created_at_utc.isoformat() if run.created_at_utc else None,
                "risk_level": run.decision.risk_level,
                "status": run.status,
                "mode": run.mode,
                "block_reason": run.decision.block_reason,
                "warnings_count": len(run.decision.warnings or []),
            })

            if len(events) >= limit:
                break

        return {
            "preset_id": preset_id or "all",
            "events": events,
            "total": len(events),
        }

    def get_trends(
        self,
        days: int = 30,
        bucket_size: str = "day",
    ) -> Dict[str, Any]:
        """Get trends over time."""
        date_to = datetime.now(timezone.utc)
        date_from = date_to - timedelta(days=days)

        runs = self._store.list_runs(
            limit=10000,
            date_from=date_from,
            date_to=date_to,
        )

        # Bucket by day
        buckets: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "total": 0,
            "green": 0,
            "yellow": 0,
            "red": 0,
        })

        for run in runs:
            if not run.created_at_utc:
                continue

            bucket_key = run.created_at_utc.strftime("%Y-%m-%d")
            buckets[bucket_key]["total"] += 1

            if run.decision:
                risk = run.decision.risk_level.lower()
                if risk in buckets[bucket_key]:
                    buckets[bucket_key][risk] += 1

        # Convert to sorted list
        trends = [
            {"date": k, **v}
            for k, v in sorted(buckets.items())
        ]

        return {
            "trends": trends,
            "period_days": days,
            "bucket_size": bucket_size,
        }

    def export_analytics(
        self,
        format: str = "json",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Export analytics data."""
        summary = self.get_summary(date_from=date_from, date_to=date_to)
        lanes = self.get_lane_analytics(date_from=date_from, date_to=date_to)
        trends = self.get_trends()

        return {
            "export_format": format,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "lanes": lanes,
            "trends": trends,
        }
