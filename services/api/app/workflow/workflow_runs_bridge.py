"""
Workflow → Runs V2 Bridge

Connects WorkflowSession state transitions to RunArtifact persistence.
On significant state changes, creates immutable run artifacts for:
- Audit trail
- Diff viewer support
- Index API queries

Governance Compliance:
- Every feasibility result → RunArtifact (event_type="feasibility")
- Every approval → RunArtifact (event_type="approval")
- Every toolpath generation → RunArtifact (event_type="toolpaths")
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from ..rmos.runs_v2.schemas import (
    RunArtifact,
    RunDecision,
    Hashes,
    RunOutputs,
    AdvisoryInputRef,
)
from ..rmos.runs_v2.store import RunStoreV2, create_run_id

from .state_machine import (
    WorkflowSession,
    WorkflowState,
    WorkflowEvent,
    FeasibilityResult,
    ToolpathPlanRef,
    RunArtifactRef,
    RiskBucket,
    RunStatus,
)

logger = logging.getLogger(__name__)


def _sha256(data: Any) -> str:
    """Compute SHA256 hash of data."""
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


def _workflow_status_to_run_status(
    bucket: Optional[RiskBucket],
    blocked: bool = False,
) -> str:
    """Convert workflow risk to RunArtifact status."""
    if blocked:
        return "BLOCKED"
    if bucket is None:
        return "ERROR"
    if bucket == RiskBucket.RED:
        return "BLOCKED"
    return "OK"


def _get_default_store() -> RunStoreV2:
    """Get or create the default RunStoreV2 instance."""
    return RunStoreV2()


class WorkflowRunsBridge:
    """
    Bridge between WorkflowSession and RunArtifact persistence.
    
    Usage:
        bridge = WorkflowRunsBridge()
        
        # After storing feasibility
        artifact_ref = bridge.on_feasibility_stored(session)
        
        # After approval
        artifact_ref = bridge.on_approved(session)
        
        # After toolpaths
        artifact_ref = bridge.on_toolpaths_stored(session)
    """
    
    def __init__(self, store: Optional[RunStoreV2] = None):
        self.store = store or _get_default_store()
    
    def _build_request_summary(self, session: WorkflowSession) -> Dict[str, Any]:
        """Build sanitized request summary from session."""
        summary = {
            "session_id": session.session_id,
            "mode": session.mode.value,
            "state": session.state.value,
        }
        
        # Add index metadata
        if session.index_meta:
            summary.update({
                "tool_id": session.index_meta.get("tool_id"),
                "material_id": session.index_meta.get("material_id"),
                "machine_id": session.index_meta.get("machine_id"),
            })
        
        # Add design hash if available
        if session.design:
            summary["design_hash"] = _sha256(session.design)
        
        # Add context hash if available
        if session.context:
            summary["context_hash"] = _sha256(session.context)
        
        return summary
    
    def _build_feasibility_dict(self, result: FeasibilityResult) -> Dict[str, Any]:
        """Build feasibility dict from FeasibilityResult."""
        return {
            "score": result.score,
            "risk_bucket": result.risk_bucket.value,
            "warnings": result.warnings,
            "meta": result.meta,
        }
    
    def on_feasibility_stored(
        self,
        session: WorkflowSession,
        *,
        request_id: Optional[str] = None,
    ) -> Optional[RunArtifactRef]:
        """
        Create RunArtifact when feasibility is stored.
        
        Called after store_feasibility() transition.
        """
        if session.feasibility is None:
            logger.warning("on_feasibility_stored called but no feasibility in session")
            return None
        
        feas = session.feasibility
        
        # Build hashes
        feas_hash = _sha256(self._build_feasibility_dict(feas))
        
        # Build decision
        decision = RunDecision(
            risk_level=_risk_bucket_to_level(feas.risk_bucket),
            score=feas.score,
            warnings=feas.warnings,
            details=feas.meta or {},
        )
        
        # Determine status
        status = _workflow_status_to_run_status(feas.risk_bucket)
        
        # Create artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            mode=session.mode.value,
            tool_id=session.index_meta.get("tool_id", "unknown"),
            status=status,
            request_summary=self._build_request_summary(session),
            feasibility=self._build_feasibility_dict(feas),
            decision=decision,
            hashes=Hashes(feasibility_sha256=feas_hash),
            event_type="feasibility",
            workflow_session_id=session.session_id,
            material_id=session.index_meta.get("material_id"),
            machine_id=session.index_meta.get("machine_id"),
            workflow_mode=session.mode.value,
            meta={
                "request_id": request_id,
                "workflow_state": session.state.value,
                "events_count": len(session.events),
            },
        )
        
        # Persist
        try:
            self.store.put(artifact)
            logger.info(
                "workflow_runs_bridge.feasibility_persisted",
                extra={
                    "run_id": run_id,
                    "session_id": session.session_id,
                    "risk_level": decision.risk_level,
                    "score": feas.score,
                }
            )
        except ValueError as e:
            # Already exists (shouldn't happen with UUID)
            logger.error(f"Failed to persist feasibility artifact: {e}")
            return None
        
        # Return ref for session to store
        return RunArtifactRef(
            artifact_id=run_id,
            kind="feasibility",
            status=RunStatus(status),
            meta={
                "feasibility_hash": feas_hash,
                "risk_level": decision.risk_level,
                "score": feas.score,
            },
        )
    
    def on_approved(
        self,
        session: WorkflowSession,
        *,
        request_id: Optional[str] = None,
    ) -> Optional[RunArtifactRef]:
        """
        Create RunArtifact when session is approved.
        
        Called after approve() transition.
        """
        if session.approval is None:
            logger.warning("on_approved called but no approval in session")
            return None
        
        if session.feasibility is None:
            logger.warning("on_approved called but no feasibility in session")
            return None
        
        feas = session.feasibility
        feas_hash = _sha256(self._build_feasibility_dict(feas))
        
        # Build decision
        decision = RunDecision(
            risk_level=_risk_bucket_to_level(feas.risk_bucket),
            score=feas.score,
            warnings=feas.warnings,
            details={
                "approved": session.approval.approved,
                "approved_by": session.approval.approved_by.value,
                "note": session.approval.note,
            },
        )
        
        # Create artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            mode=session.mode.value,
            tool_id=session.index_meta.get("tool_id", "unknown"),
            status="OK",  # Approval means OK to proceed
            request_summary=self._build_request_summary(session),
            feasibility=self._build_feasibility_dict(feas),
            decision=decision,
            hashes=Hashes(feasibility_sha256=feas_hash),
            event_type="approval",
            workflow_session_id=session.session_id,
            material_id=session.index_meta.get("material_id"),
            machine_id=session.index_meta.get("machine_id"),
            workflow_mode=session.mode.value,
            meta={
                "request_id": request_id,
                "workflow_state": session.state.value,
                "approval_ts": session.approval.ts_utc.isoformat(),
                "parent_feasibility_artifact": (
                    session.last_feasibility_artifact.artifact_id
                    if session.last_feasibility_artifact else None
                ),
            },
        )
        
        # Persist
        try:
            self.store.put(artifact)
            logger.info(
                "workflow_runs_bridge.approval_persisted",
                extra={
                    "run_id": run_id,
                    "session_id": session.session_id,
                    "approved_by": session.approval.approved_by.value,
                }
            )
        except ValueError as e:
            logger.error(f"Failed to persist approval artifact: {e}")
            return None
        
        return RunArtifactRef(
            artifact_id=run_id,
            kind="approval",
            status=RunStatus.OK,
            meta={
                "approved_by": session.approval.approved_by.value,
                "feasibility_hash": feas_hash,
            },
        )
    
    def on_toolpaths_stored(
        self,
        session: WorkflowSession,
        *,
        toolpaths_data: Optional[Dict[str, Any]] = None,
        gcode_text: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[RunArtifactRef]:
        """
        Create RunArtifact when toolpaths are stored.
        
        Called after store_toolpaths() transition.
        
        Args:
            session: The workflow session
            toolpaths_data: Raw toolpath data for hashing
            gcode_text: Generated G-code (inline if <= 200KB)
            request_id: Correlation ID
        """
        if session.toolpaths is None:
            logger.warning("on_toolpaths_stored called but no toolpaths in session")
            return None
        
        if session.feasibility is None:
            logger.warning("on_toolpaths_stored called but no feasibility in session")
            return None
        
        feas = session.feasibility
        feas_hash = _sha256(self._build_feasibility_dict(feas))
        
        # Compute toolpath hash
        toolpaths_hash = None
        if toolpaths_data:
            toolpaths_hash = _sha256(toolpaths_data)
        elif session.toolpaths.meta.get("toolpath_hash"):
            toolpaths_hash = session.toolpaths.meta["toolpath_hash"]
        
        # Compute gcode hash
        gcode_hash = None
        if gcode_text:
            gcode_hash = _sha256(gcode_text)
        
        # Build decision
        decision = RunDecision(
            risk_level=_risk_bucket_to_level(feas.risk_bucket),
            score=feas.score,
            warnings=feas.warnings,
            details=session.toolpaths.meta,
        )
        
        # Build outputs
        outputs = RunOutputs()
        if gcode_text and len(gcode_text) <= 200 * 1024:  # Inline if <= 200KB
            outputs.gcode_text = gcode_text
        
        # Create artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            mode=session.mode.value,
            tool_id=session.index_meta.get("tool_id", "unknown"),
            status="OK",
            request_summary=self._build_request_summary(session),
            feasibility=self._build_feasibility_dict(feas),
            decision=decision,
            hashes=Hashes(
                feasibility_sha256=feas_hash,
                toolpaths_sha256=toolpaths_hash,
                gcode_sha256=gcode_hash,
            ),
            outputs=outputs,
            event_type="toolpaths",
            workflow_session_id=session.session_id,
            material_id=session.index_meta.get("material_id"),
            machine_id=session.index_meta.get("machine_id"),
            workflow_mode=session.mode.value,
            meta={
                "request_id": request_id,
                "workflow_state": session.state.value,
                "plan_id": session.toolpaths.plan_id,
                "parent_approval_artifact": (
                    session.last_toolpaths_artifact.artifact_id
                    if session.last_toolpaths_artifact else None
                ),
            },
        )
        
        # Persist
        try:
            self.store.put(artifact)
            logger.info(
                "workflow_runs_bridge.toolpaths_persisted",
                extra={
                    "run_id": run_id,
                    "session_id": session.session_id,
                    "plan_id": session.toolpaths.plan_id,
                }
            )
        except ValueError as e:
            logger.error(f"Failed to persist toolpaths artifact: {e}")
            return None
        
        return RunArtifactRef(
            artifact_id=run_id,
            kind="toolpaths",
            status=RunStatus.OK,
            meta={
                "toolpaths_hash": toolpaths_hash,
                "gcode_hash": gcode_hash,
                "plan_id": session.toolpaths.plan_id,
            },
        )
    
    def on_rejected(
        self,
        session: WorkflowSession,
        *,
        reason: str,
        request_id: Optional[str] = None,
    ) -> Optional[RunArtifactRef]:
        """
        Create RunArtifact when session is rejected.
        
        Called after reject() transition.
        """
        feas_hash = "0" * 64  # Placeholder if no feasibility
        feas_dict: Dict[str, Any] = {}
        
        if session.feasibility:
            feas = session.feasibility
            feas_dict = self._build_feasibility_dict(feas)
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
            request_summary=self._build_request_summary(session),
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
            self.store.put(artifact)
            logger.info(
                "workflow_runs_bridge.rejection_persisted",
                extra={
                    "run_id": run_id,
                    "session_id": session.session_id,
                    "reason": reason,
                }
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


# Module singleton
_bridge: Optional[WorkflowRunsBridge] = None


def get_workflow_runs_bridge() -> WorkflowRunsBridge:
    """Get or create the workflow runs bridge singleton."""
    global _bridge
    if _bridge is None:
        _bridge = WorkflowRunsBridge()
    return _bridge


def reset_bridge() -> None:
    """Reset singleton (for testing)."""
    global _bridge
    _bridge = None
