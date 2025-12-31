"""
RMOS Pipeline Metrics Rollup Service

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 5

Service for computing and persisting aggregated execution metrics.
Provides summary statistics for analysis and reporting.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schemas import (
    TimeMetrics,
    YieldMetrics,
    EventCounts,
    MetricsRollup,
    MetricsRollupResponse,
    JobLogStatus,
)
from ..store import write_artifact, read_artifact, query_artifacts
from ..schemas import PipelineStage, PipelineStatus, ArtifactQuery


def _utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class RollupService:
    """
    Service for computing and managing metrics rollups.
    """

    def __init__(self, tool_type: str):
        self.tool_type = tool_type

    def _kind(self, suffix: str) -> str:
        return f"{self.tool_type}_{suffix}"

    def compute_execution_rollup(
        self,
        execution_artifact_id: str,
    ) -> MetricsRollup:
        """
        Compute metrics rollup for an execution.

        Args:
            execution_artifact_id: Execution to compute rollup for

        Returns:
            MetricsRollup with aggregated statistics
        """
        # Query job logs for this execution
        job_logs = self._query_job_logs(execution_artifact_id)

        # Query learning events for this execution
        learning_events = self._query_learning_events(execution_artifact_id)

        # Query learning decisions (accepted only)
        accepted_decisions = self._query_accepted_decisions(execution_artifact_id)

        # Aggregate metrics
        time_metrics = self._aggregate_time(job_logs)
        yield_metrics = self._aggregate_yield(job_logs)
        event_counts = self._aggregate_events(job_logs)
        operators = self._count_operators(job_logs)
        statuses = self._count_statuses(job_logs)

        return MetricsRollup(
            artifact_id="",  # Set on persist
            kind=self._kind("execution_metrics_rollup"),
            created_at_utc=_utc_now_iso(),
            rollup_level="execution",
            parent_artifact_id=execution_artifact_id,
            job_log_count=len(job_logs),
            learning_event_count=len(learning_events),
            learning_accepted_count=len(accepted_decisions),
            operators=operators,
            statuses=statuses,
            time_metrics=time_metrics,
            yield_metrics=yield_metrics,
            event_counts=event_counts,
            learning_applied_count=len(accepted_decisions),
            learning_applied_rate=len(accepted_decisions) / max(len(learning_events), 1),
        )

    def _query_job_logs(self, execution_artifact_id: str) -> List[Dict[str, Any]]:
        """Query job logs for an execution."""
        query = ArtifactQuery(
            kind=self._kind("job_log"),
            parent_decision_artifact_id=execution_artifact_id,
            limit=1000,
        )
        result = query_artifacts(query)
        return result.items

    def _query_learning_events(self, execution_artifact_id: str) -> List[Dict[str, Any]]:
        """Query learning events for an execution."""
        query = ArtifactQuery(
            kind=self._kind("learning_event"),
            parent_decision_artifact_id=execution_artifact_id,
            limit=1000,
        )
        result = query_artifacts(query)
        return result.items

    def _query_accepted_decisions(self, execution_artifact_id: str) -> List[Dict[str, Any]]:
        """Query accepted learning decisions for an execution."""
        query = ArtifactQuery(
            kind=self._kind("learning_decision"),
            status="ACCEPT",
            limit=1000,
        )
        result = query_artifacts(query)

        # Filter to those related to this execution
        # (decisions reference learning events, which reference execution)
        return [d for d in result.items if self._is_for_execution(d, execution_artifact_id)]

    def _is_for_execution(self, decision: Dict[str, Any], execution_artifact_id: str) -> bool:
        """Check if a decision is for a given execution."""
        payload = decision.get("payload", {})
        event_id = payload.get("learning_event_artifact_id")
        if not event_id:
            return False

        event = read_artifact(event_id)
        if not event:
            return False

        event_payload = event.get("payload", {})
        return event_payload.get("execution_artifact_id") == execution_artifact_id

    def _aggregate_time(self, job_logs: List[Dict[str, Any]]) -> TimeMetrics:
        """Aggregate time metrics from job logs."""
        setup_times = []
        cut_times = []
        total_times = []

        for log in job_logs:
            payload = log.get("payload", {})
            metrics = payload.get("metrics", {})

            if metrics.get("setup_time_s"):
                setup_times.append(metrics["setup_time_s"])
            if metrics.get("cut_time_s"):
                cut_times.append(metrics["cut_time_s"])
            if metrics.get("total_time_s"):
                total_times.append(metrics["total_time_s"])

        return TimeMetrics(
            setup_time_s_total=sum(setup_times),
            setup_time_s_avg=sum(setup_times) / len(setup_times) if setup_times else 0,
            cut_time_s_total=sum(cut_times),
            cut_time_s_avg=sum(cut_times) / len(cut_times) if cut_times else 0,
            total_time_s_total=sum(total_times),
            total_time_s_avg=sum(total_times) / len(total_times) if total_times else 0,
        )

    def _aggregate_yield(self, job_logs: List[Dict[str, Any]]) -> YieldMetrics:
        """Aggregate yield metrics from job logs."""
        parts_ok = 0
        parts_scrap = 0

        for log in job_logs:
            payload = log.get("payload", {})
            metrics = payload.get("metrics", {})
            parts_ok += metrics.get("parts_ok", 0)
            parts_scrap += metrics.get("parts_scrap", 0)

        total = parts_ok + parts_scrap
        yield_rate = parts_ok / total if total > 0 else 0

        return YieldMetrics(
            parts_ok_total=parts_ok,
            parts_scrap_total=parts_scrap,
            parts_total=total,
            yield_rate=round(yield_rate, 3),
        )

    def _aggregate_events(self, job_logs: List[Dict[str, Any]]) -> EventCounts:
        """Aggregate event counts from job logs."""
        counts = EventCounts()

        for log in job_logs:
            payload = log.get("payload", {})
            metrics = payload.get("metrics", {})

            if metrics.get("burn"):
                counts.burn_events += 1
            if metrics.get("tearout"):
                counts.tearout_events += 1
            if metrics.get("kickback"):
                counts.kickback_events += 1
            if metrics.get("chatter"):
                counts.chatter_events += 1
            if metrics.get("tool_wear"):
                counts.tool_wear_events += 1

        return counts

    def _count_operators(self, job_logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count job logs by operator."""
        counts: Dict[str, int] = {}
        for log in job_logs:
            payload = log.get("payload", {})
            operator = payload.get("operator", "unknown")
            counts[operator] = counts.get(operator, 0) + 1
        return counts

    def _count_statuses(self, job_logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count job logs by status."""
        counts: Dict[str, int] = {}
        for log in job_logs:
            payload = log.get("payload", {})
            status = payload.get("status", "UNKNOWN")
            counts[status] = counts.get(status, 0) + 1
        return counts

    def persist_rollup(
        self,
        execution_artifact_id: str,
    ) -> MetricsRollupResponse:
        """
        Compute and persist a metrics rollup.

        Args:
            execution_artifact_id: Execution to compute rollup for

        Returns:
            MetricsRollupResponse with artifact ID
        """
        # Compute rollup
        rollup = self.compute_execution_rollup(execution_artifact_id)

        # Read execution for context
        execution = read_artifact(execution_artifact_id)
        execution_meta = execution.get("index_meta", {}) if execution else {}
        batch_label = execution_meta.get("batch_label")
        session_id = execution_meta.get("session_id")

        payload = {
            "created_utc": _utc_now_iso(),
            "parent_artifact_id": execution_artifact_id,
            "rollup_level": "execution",
            "job_log_count": rollup.job_log_count,
            "learning_event_count": rollup.learning_event_count,
            "learning_accepted_count": rollup.learning_accepted_count,
            "operators": rollup.operators,
            "statuses": rollup.statuses,
            "time_metrics": rollup.time_metrics.model_dump(),
            "yield_metrics": rollup.yield_metrics.model_dump(),
            "event_counts": rollup.event_counts.model_dump(),
            "learning_applied_count": rollup.learning_applied_count,
            "learning_applied_rate": rollup.learning_applied_rate,
        }

        index_meta = {
            "tool_type": self.tool_type,
            "tool_kind": self.tool_type,
            "kind_group": "metrics",
            "parent_execution_artifact_id": execution_artifact_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "rollup_level": "execution",
        }

        artifact_id = write_artifact(
            kind=self._kind("execution_metrics_rollup"),
            stage=PipelineStage.EXECUTE,
            status=PipelineStatus.OK,
            index_meta=index_meta,
            payload=payload,
        )

        return MetricsRollupResponse(
            rollup_artifact_id=artifact_id,
            parent_artifact_id=execution_artifact_id,
            rollup_level="execution",
            job_log_count=rollup.job_log_count,
            yield_rate=rollup.yield_metrics.yield_rate,
        )

    def get_latest_rollup(
        self,
        execution_artifact_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest rollup for an execution.

        Args:
            execution_artifact_id: Execution to find rollup for

        Returns:
            Latest rollup artifact, or None
        """
        query = ArtifactQuery(
            kind=self._kind("execution_metrics_rollup"),
            parent_decision_artifact_id=execution_artifact_id,
            limit=1,
        )
        result = query_artifacts(query)

        if result.items:
            # Sort by created_at (newest first)
            items = sorted(
                result.items,
                key=lambda x: str(x.get("created_at_utc", "")),
                reverse=True,
            )
            return items[0]

        return None

    def list_rollup_history(
        self,
        execution_artifact_id: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List rollup history for an execution.

        Args:
            execution_artifact_id: Execution to find rollups for
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of rollup artifacts (newest first)
        """
        query = ArtifactQuery(
            kind=self._kind("execution_metrics_rollup"),
            parent_decision_artifact_id=execution_artifact_id,
            limit=limit + offset,
        )
        result = query_artifacts(query)

        # Sort by created_at (newest first)
        items = sorted(
            result.items,
            key=lambda x: str(x.get("created_at_utc", "")),
            reverse=True,
        )

        return items[offset:offset + limit]


# =============================================================================
# Convenience Functions
# =============================================================================

def compute_execution_rollup(
    tool_type: str,
    execution_artifact_id: str,
) -> MetricsRollup:
    """Compute execution metrics rollup."""
    service = RollupService(tool_type)
    return service.compute_execution_rollup(execution_artifact_id)


def persist_execution_rollup(
    tool_type: str,
    execution_artifact_id: str,
) -> MetricsRollupResponse:
    """Compute and persist execution metrics rollup."""
    service = RollupService(tool_type)
    return service.persist_rollup(execution_artifact_id)


def get_latest_rollup(
    tool_type: str,
    execution_artifact_id: str,
) -> Optional[Dict[str, Any]]:
    """Get latest rollup for an execution."""
    service = RollupService(tool_type)
    return service.get_latest_rollup(execution_artifact_id)


def list_rollup_history(
    tool_type: str,
    execution_artifact_id: str,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """List rollup history for an execution."""
    service = RollupService(tool_type)
    return service.list_rollup_history(execution_artifact_id, **kwargs)
