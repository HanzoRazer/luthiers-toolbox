"""Workflow Runs Bridge — rejection & snapshot event handlers.

Extracted from workflow_runs_bridge.py (WP-3).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..rmos.runs_v2.schemas import (
    RunArtifact,
    RunDecision,
    Hashes,
)
from ..rmos.runs_v2.store import RunStoreV2, create_run_id

from .state_machine import (
    WorkflowSession,
    RunArtifactRef,
    RiskBucket,
    RunStatus,
)

logger = logging.getLogger(__name__)


def _sha256(data: Any) -> str:
    """Compute SHA256 hash of data."""
    import hashlib
    import json

    if isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload = data
    else:
        payload = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _risk_bucket_to_level(bucket: RiskBucket) -> str:
    """Convert RiskBucket enum to risk level string."""
    return bucket.value.upper()


def handle_rejected(
    store: RunStoreV2,
    session: WorkflowSession,
    *,
    reason: str,
    request_id: Optional[str] = None,
    build_request_summary: Any,
    build_feasibility_dict: Any,
) -> Optional[RunArtifactRef]:
    """
    Create RunArtifact when session is rejected.

    Called after reject() transition.
    """
    feas_hash = "0" * 64  # Placeholder if no feasibility
    feas_dict: Dict[str, Any] = {}

    if session.feasibility:
        feas = session.feasibility
        feas_dict = build_feasibility_dict(feas)
        feas_hash = _sha256(feas_dict)
        risk_level = _risk_bucket_to_level(feas.risk_bucket)
        score = feas.score
    else:
        risk_level = "UNKNOWN"
        score = None

    # Build decision
    decision = RunDecision(
        risk_level=risk_level,
        score=score,
        block_reason=reason,
        warnings=[],
        details={"rejected": True, "reason": reason},
    )

    # Create artifact
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        mode=session.mode.value,
        tool_id=session.index_meta.get("tool_id", "unknown"),
        status="BLOCKED",
        request_summary=build_request_summary(session),
        feasibility=feas_dict,
        decision=decision,
        hashes=Hashes(feasibility_sha256=feas_hash),
        event_type="rejection",
        workflow_session_id=session.session_id,
        material_id=session.index_meta.get("material_id"),
        machine_id=session.index_meta.get("machine_id"),
        workflow_mode=session.mode.value,
        meta={
            "request_id": request_id,
            "workflow_state": session.state.value,
            "rejection_reason": reason,
        },
    )

    # Persist
    try:
        store.put(artifact)
        logger.info(
            "workflow_runs_bridge.rejection_persisted",
            extra={
                "run_id": run_id,
                "session_id": session.session_id,
                "reason": reason,
            },
        )
    except ValueError as e:
        logger.error(f"Failed to persist rejection artifact: {e}")
        return None

    return RunArtifactRef(
        artifact_id=run_id,
        kind="rejection",
        status=RunStatus.BLOCKED,
        meta={"reason": reason},
    )


def handle_snapshot_saved(
    store: RunStoreV2,
    session: WorkflowSession,
    *,
    snapshot_id: str,
    snapshot_name: str,
    snapshot_data: Dict[str, Any],
    tags: Optional[list[str]] = None,
    request_id: Optional[str] = None,
    build_request_summary: Any,
    build_feasibility_dict: Any,
) -> Optional[RunArtifactRef]:
    """
    Create RunArtifact when a session snapshot is saved.

    Called from save-snapshot endpoint.
    """
    # Hash the snapshot data
    snapshot_hash = _sha256(snapshot_data)

    # Build feasibility info if available
    feas_dict: Dict[str, Any] = {}
    feas_hash = "0" * 64
    risk_level = "UNKNOWN"
    score = None

    if session.feasibility:
        feas = session.feasibility
        feas_dict = build_feasibility_dict(feas)
        feas_hash = _sha256(feas_dict)
        risk_level = _risk_bucket_to_level(feas.risk_bucket)
        score = feas.score

    # Build decision
    decision = RunDecision(
        risk_level=risk_level,
        score=score,
        warnings=[],
        details={
            "snapshot_id": snapshot_id,
            "snapshot_name": snapshot_name,
            "tags": tags or [],
        },
    )

    # Create artifact
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        mode=session.mode.value,
        tool_id=session.index_meta.get("tool_id", "unknown"),
        status="OK",
        request_summary=build_request_summary(session),
        feasibility=feas_dict,
        decision=decision,
        hashes=Hashes(
            feasibility_sha256=feas_hash,
            snapshot_sha256=snapshot_hash,
        ),
        event_type="snapshot",
        workflow_session_id=session.session_id,
        material_id=session.index_meta.get("material_id"),
        machine_id=session.index_meta.get("machine_id"),
        workflow_mode=session.mode.value,
        meta={
            "request_id": request_id,
            "workflow_state": session.state.value,
            "snapshot_id": snapshot_id,
            "snapshot_name": snapshot_name,
            "tags": tags or [],
        },
    )

    # Persist
    try:
        store.put(artifact)
        logger.info(
            "workflow_runs_bridge.snapshot_persisted",
            extra={
                "run_id": run_id,
                "session_id": session.session_id,
                "snapshot_id": snapshot_id,
                "snapshot_name": snapshot_name,
            },
        )
    except ValueError as e:
        logger.error(f"Failed to persist snapshot artifact: {e}")
        return None

    return RunArtifactRef(
        artifact_id=run_id,
        kind="snapshot",
        status=RunStatus.OK,
        meta={
            "snapshot_id": snapshot_id,
            "snapshot_name": snapshot_name,
            "snapshot_hash": snapshot_hash,
        },
    )
