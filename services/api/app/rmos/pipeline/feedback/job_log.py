"""
RMOS Pipeline Job Log Service

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 5

Service for recording operator feedback on executed jobs.
Auto-triggers learning event and metrics rollup hooks if enabled.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schemas import (
    JobLog,
    JobLogRequest,
    JobLogResponse,
    JobLogStatus,
    JobLogMetrics,
)
from .config import (
    is_learning_hook_enabled,
    is_metrics_rollup_hook_enabled,
)
from ..store import write_artifact, read_artifact, query_artifacts
from ..schemas import PipelineStage, PipelineStatus, ArtifactQuery
from ...runs import create_run_id, sha256_of_obj


def _utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class JobLogService:
    """
    Service for managing job logs.

    Job logs capture operator feedback after job execution.
    They auto-trigger learning and metrics hooks if enabled.
    """

    def __init__(self, tool_type: str):
        """
        Initialize job log service.

        Args:
            tool_type: Tool type prefix (e.g., "roughing", "drilling")
        """
        self.tool_type = tool_type

    def _kind(self, suffix: str) -> str:
        """Generate artifact kind."""
        return f"{self.tool_type}_{suffix}"

    def write_log(
        self,
        execution_artifact_id: str,
        operator: str,
        status: JobLogStatus,
        *,
        op_id: Optional[str] = None,
        station: Optional[str] = None,
        notes: Optional[str] = None,
        metrics: Optional[JobLogMetrics] = None,
    ) -> JobLogResponse:
        """
        Write a job log.

        Args:
            execution_artifact_id: Parent execution artifact
            operator: Operator name/ID
            status: Job completion status
            op_id: Specific operation (optional)
            station: Workstation ID (optional)
            notes: Operator notes (optional)
            metrics: Job metrics (optional)

        Returns:
            JobLogResponse with artifact ID and hook status
        """
        # Read execution for context
        execution = read_artifact(execution_artifact_id)
        execution_payload = execution.get("payload", {}) if execution else {}
        execution_meta = execution.get("index_meta", {}) if execution else {}

        batch_label = execution_payload.get("batch_label") or execution_meta.get("batch_label")
        session_id = execution_payload.get("session_id") or execution_meta.get("session_id")

        # Build job log payload
        if metrics is None:
            metrics = JobLogMetrics()

        payload = {
            "created_utc": _utc_now_iso(),
            "execution_artifact_id": execution_artifact_id,
            "op_id": op_id,
            "operator": operator,
            "station": station,
            "status": status.value,
            "notes": notes,
            "metrics": metrics.model_dump(),
            "tool_type": self.tool_type,
            "batch_label": batch_label,
            "session_id": session_id,
        }

        index_meta = {
            "tool_type": self.tool_type,
            "tool_kind": self.tool_type,
            "kind_group": "batch",
            "parent_execution_artifact_id": execution_artifact_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "operator": operator,
            "status": status.value,
            # Signal flags for querying
            "signal_burn": metrics.burn,
            "signal_tearout": metrics.tearout,
            "signal_kickback": metrics.kickback,
        }

        # Write artifact
        artifact_id = write_artifact(
            kind=self._kind("job_log"),
            stage=PipelineStage.EXECUTE,
            status=PipelineStatus.OK,
            index_meta=index_meta,
            payload=payload,
            request_hash=sha256_of_obj(payload),
        )

        # Auto-trigger hooks
        learning_emitted = False
        rollup_updated = False

        if is_learning_hook_enabled(self.tool_type):
            try:
                from .learning import emit_learning_event
                emit_learning_event(
                    tool_type=self.tool_type,
                    job_log_artifact_id=artifact_id,
                    execution_artifact_id=execution_artifact_id,
                    metrics=metrics,
                    notes=notes,
                )
                learning_emitted = True
            except (OSError, ValueError, TypeError):  # WP-1: narrowed from except Exception
                pass  # Hook failure shouldn't fail the job log

        if is_metrics_rollup_hook_enabled(self.tool_type):
            try:
                from .rollups import persist_execution_rollup
                persist_execution_rollup(
                    tool_type=self.tool_type,
                    execution_artifact_id=execution_artifact_id,
                )
                rollup_updated = True
            except (OSError, ValueError, TypeError):  # WP-1: narrowed from except Exception
                pass  # Hook failure shouldn't fail the job log

        return JobLogResponse(
            job_log_artifact_id=artifact_id,
            execution_artifact_id=execution_artifact_id,
            status=status.value,
            learning_event_emitted=learning_emitted,
            metrics_rollup_updated=rollup_updated,
        )

    def list_for_execution(
        self,
        execution_artifact_id: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List job logs for an execution.

        Args:
            execution_artifact_id: Execution to find logs for
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of job log artifacts
        """
        query = ArtifactQuery(
            kind=self._kind("job_log"),
            parent_decision_artifact_id=execution_artifact_id,
            limit=limit,
            offset=offset,
        )
        result = query_artifacts(query)

        # Sort by created_at (newest first)
        items = sorted(
            result.items,
            key=lambda x: str(x.get("created_at_utc", "")),
            reverse=True,
        )

        return items


# =============================================================================
# Convenience Functions
# =============================================================================

def write_job_log(
    tool_type: str,
    execution_artifact_id: str,
    operator: str,
    status: JobLogStatus,
    **kwargs: Any,
) -> JobLogResponse:
    """Write a job log."""
    service = JobLogService(tool_type)
    return service.write_log(execution_artifact_id, operator, status, **kwargs)


def list_job_logs_for_execution(
    tool_type: str,
    execution_artifact_id: str,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """List job logs for an execution."""
    service = JobLogService(tool_type)
    return service.list_for_execution(execution_artifact_id, **kwargs)
