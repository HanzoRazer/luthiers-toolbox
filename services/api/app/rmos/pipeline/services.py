"""RMOS Pipeline Services - Business Logic for Multi-Stage Execution"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from .schemas import (
    PipelineStage,
    PipelineStatus,
    RiskBucket,
    PlanOperation,
    SpecResponse,
    PlanResponse,
    ApproveResponse,
    ExecuteResponse,
)
from .store import (
    write_artifact,
    read_artifact,
    get_pipeline_store,
)
from ..runs import sha256_of_obj


def _utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _aggregate_risk(operations: List[PlanOperation]) -> RiskBucket:
    """Determine aggregate risk from list of operations."""
    has_red = any(op.risk_bucket == RiskBucket.RED for op in operations)
    has_unknown = any(op.risk_bucket == RiskBucket.UNKNOWN for op in operations)
    has_yellow = any(op.risk_bucket == RiskBucket.YELLOW for op in operations)

    if has_red:
        return RiskBucket.RED
    if has_unknown:
        return RiskBucket.UNKNOWN
    if has_yellow:
        return RiskBucket.YELLOW
    return RiskBucket.GREEN


def _aggregate_score(operations: List[PlanOperation]) -> float:
    """Calculate average feasibility score across operations."""
    if not operations:
        return 0.0
    total = sum(op.feasibility_score for op in operations)
    return round(total / len(operations), 2)


# =============================================================================
# Pipeline Service Protocol
# =============================================================================

class FeasibilityChecker(Protocol):
    """Protocol for feasibility checking."""

    def check(self, design: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check feasibility for a design/context."""
        ...


class ToolpathGenerator(Protocol):
    """Protocol for toolpath generation."""

    def generate(
        self,
        design: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate toolpaths for a design/context."""
        ...


class PipelineService:
    """Service for managing pipeline operations."""

    def __init__(
        self,
        tool_type: str,
        feasibility_checker: Optional[FeasibilityChecker] = None,
        toolpath_generator: Optional[ToolpathGenerator] = None,
    ):
        """Initialize pipeline service."""
        self.tool_type = tool_type
        self.feasibility_checker = feasibility_checker
        self.toolpath_generator = toolpath_generator

    def _kind(self, stage: str) -> str:
        """Generate artifact kind from tool type and stage."""
        return f"{self.tool_type}_{stage}"

    def create_spec(
        self,
        design: Dict[str, Any],
        context: Dict[str, Any],
        *,
        batch_label: Optional[str] = None,
        session_id: Optional[str] = None,
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> SpecResponse:
        """Create a SPEC artifact."""
        item_count = len(items) if items else 1

        # Generate op_ids for each item
        if items:
            for item in items:
                if "op_id" not in item:
                    item["op_id"] = f"op_{sha256_of_obj(item)[:8]}"

        payload = {
            "created_utc": _utc_now_iso(),
            "design": design,
            "context": context,
            "batch_label": batch_label,
            "session_id": session_id,
            "items": items or [{"op_id": f"op_{sha256_of_obj(design)[:8]}", **design}],
            "item_count": item_count,
        }

        index_meta = {
            "tool_type": self.tool_type,
            "batch_label": batch_label,
            "session_id": session_id,
            "workflow_mode": "pipeline",
        }

        artifact_id = write_artifact(
            kind=self._kind("spec"),
            stage=PipelineStage.SPEC,
            status=PipelineStatus.CREATED,
            index_meta=index_meta,
            payload=payload,
            request_hash=sha256_of_obj(payload),
        )

        return SpecResponse(
            spec_artifact_id=artifact_id,
            batch_label=batch_label,
            session_id=session_id,
            status="CREATED",
            item_count=item_count,
        )

    def create_plan(
        self,
        spec_artifact_id: str,
        *,
        operations: Optional[List[PlanOperation]] = None,
    ) -> PlanResponse:
        """Create a PLAN artifact from a spec."""
        # Read spec artifact
        spec = read_artifact(spec_artifact_id)
        if not spec:
            raise ValueError(f"Spec artifact not found: {spec_artifact_id}")

        spec_payload = spec.get("payload", {})
        spec_meta = spec.get("index_meta", {})

        batch_label = spec_payload.get("batch_label") or spec_meta.get("batch_label")
        session_id = spec_payload.get("session_id") or spec_meta.get("session_id")

        # Generate operations from spec items if not provided
        if operations is None:
            operations = []
            items = spec_payload.get("items", [])
            design = spec_payload.get("design", {})
            context = spec_payload.get("context", {})

            for item in items:
                op_id = item.get("op_id", f"op_{len(operations)}")

                # Merge item design with base design
                op_design = {**design, **item}
                op_design.pop("op_id", None)

                # Check feasibility if checker available
                feas_result = {"score": 50.0, "risk_bucket": "UNKNOWN", "warnings": []}
                if self.feasibility_checker:
                    try:
                        feas_result = self.feasibility_checker.check(op_design, context)
                    except (ZeroDivisionError, ValueError, TypeError, KeyError, AttributeError) as e:  # WP-1: narrowed from except Exception
                        feas_result = {
                            "score": 0.0,
                            "risk_bucket": "ERROR",
                            "warnings": [str(e)],
                        }

                operations.append(PlanOperation(
                    op_id=op_id,
                    design=op_design,
                    context=context,
                    feasibility_score=feas_result.get("score", 50.0),
                    risk_bucket=RiskBucket(feas_result.get("risk_bucket", "UNKNOWN")),
                    warnings=feas_result.get("warnings", []),
                    feasibility_details=feas_result,
                ))

        # Calculate aggregates
        aggregate_score = _aggregate_score(operations)
        aggregate_risk = _aggregate_risk(operations)

        # Count by risk bucket
        green_count = sum(1 for op in operations if op.risk_bucket == RiskBucket.GREEN)
        yellow_count = sum(1 for op in operations if op.risk_bucket == RiskBucket.YELLOW)
        red_count = sum(1 for op in operations if op.risk_bucket == RiskBucket.RED)

        payload = {
            "created_utc": _utc_now_iso(),
            "spec_artifact_id": spec_artifact_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "operations": [op.model_dump() for op in operations],
            "aggregate_score": aggregate_score,
            "aggregate_risk": aggregate_risk.value,
            "op_count": len(operations),
            "green_count": green_count,
            "yellow_count": yellow_count,
            "red_count": red_count,
        }

        index_meta = {
            "tool_type": self.tool_type,
            "parent_spec_artifact_id": spec_artifact_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "workflow_mode": "pipeline",
            "op_count": len(operations),
        }

        artifact_id = write_artifact(
            kind=self._kind("plan"),
            stage=PipelineStage.PLAN,
            status=PipelineStatus.OK,
            index_meta=index_meta,
            payload=payload,
        )

        return PlanResponse(
            plan_artifact_id=artifact_id,
            spec_artifact_id=spec_artifact_id,
            batch_label=batch_label,
            status="OK",
            op_count=len(operations),
            aggregate_score=aggregate_score,
            aggregate_risk=aggregate_risk.value,
            operations=operations,
        )

    def create_decision(
        self,
        plan_artifact_id: str,
        approved_by: str,
        *,
        reason: Optional[str] = None,
        setup_order: Optional[List[str]] = None,
        op_order: Optional[List[str]] = None,
    ) -> ApproveResponse:
        """Create a DECISION artifact (approval checkpoint)."""
        # Read plan artifact
        plan = read_artifact(plan_artifact_id)
        if not plan:
            raise ValueError(f"Plan artifact not found: {plan_artifact_id}")

        plan_payload = plan.get("payload", {})
        plan_meta = plan.get("index_meta", {})

        spec_artifact_id = plan_payload.get("spec_artifact_id") or plan_meta.get("parent_spec_artifact_id")
        batch_label = plan_payload.get("batch_label") or plan_meta.get("batch_label")
        session_id = plan_payload.get("session_id") or plan_meta.get("session_id")

        # Default op_order from plan operations
        if op_order is None:
            operations = plan_payload.get("operations", [])
            op_order = [op.get("op_id") for op in operations if op.get("op_id")]

        payload = {
            "created_utc": _utc_now_iso(),
            "plan_artifact_id": plan_artifact_id,
            "spec_artifact_id": spec_artifact_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "approved_by": approved_by,
            "reason": reason,
            "chosen_order": {
                "setup_order": setup_order or [],
                "op_order": op_order or [],
            },
        }

        index_meta = {
            "tool_type": self.tool_type,
            "parent_plan_artifact_id": plan_artifact_id,
            "parent_spec_artifact_id": spec_artifact_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "approved_by": approved_by,
            "workflow_mode": "pipeline",
        }

        artifact_id = write_artifact(
            kind=self._kind("decision"),
            stage=PipelineStage.DECISION,
            status=PipelineStatus.APPROVED,
            index_meta=index_meta,
            payload=payload,
        )

        return ApproveResponse(
            decision_artifact_id=artifact_id,
            plan_artifact_id=plan_artifact_id,
            spec_artifact_id=spec_artifact_id,
            batch_label=batch_label,
            status="APPROVED",
            approved_by=approved_by,
        )

    def create_execution(
        self,
        decision_artifact_id: str,
        *,
        op_ids: Optional[List[str]] = None,
        is_retry: bool = False,
        retry_of_execution_id: Optional[str] = None,
        retry_reason: Optional[str] = None,
    ) -> ExecuteResponse:
        """Create an EXECUTION artifact (generate toolpaths).

        WP-3: Core logic extracted to services_execution.execute_pipeline().
        """
        from .services_execution import execute_pipeline

        return execute_pipeline(
            self,
            decision_artifact_id,
            op_ids=op_ids,
            is_retry=is_retry,
            retry_of_execution_id=retry_of_execution_id,
            retry_reason=retry_reason,
        )

    def retry_execution(
        self,
        execution_artifact_id: str,
        *,
        op_ids: Optional[List[str]] = None,
        reason: str = "retry",
    ) -> ExecuteResponse:
        """Retry a previous execution (immutable - creates new artifacts).

        WP-3: Core logic extracted to services_execution.retry_pipeline_execution().
        """
        from .services_execution import retry_pipeline_execution

        return retry_pipeline_execution(
            self,
            execution_artifact_id,
            op_ids=op_ids,
            reason=reason,
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def create_spec_artifact(
    tool_type: str,
    design: Dict[str, Any],
    context: Dict[str, Any],
    **kwargs: Any,
) -> SpecResponse:
    """Create a spec artifact."""
    service = PipelineService(tool_type)
    return service.create_spec(design, context, **kwargs)


def create_plan_artifact(
    tool_type: str,
    spec_artifact_id: str,
    **kwargs: Any,
) -> PlanResponse:
    """Create a plan artifact from a spec."""
    service = PipelineService(tool_type)
    return service.create_plan(spec_artifact_id, **kwargs)


def create_decision_artifact(
    tool_type: str,
    plan_artifact_id: str,
    approved_by: str,
    **kwargs: Any,
) -> ApproveResponse:
    """Create a decision artifact (approval checkpoint)."""
    service = PipelineService(tool_type)
    return service.create_decision(plan_artifact_id, approved_by, **kwargs)


def create_execution_artifact(
    tool_type: str,
    decision_artifact_id: str,
    **kwargs: Any,
) -> ExecuteResponse:
    """Create an execution artifact (generate toolpaths)."""
    service = PipelineService(tool_type)
    return service.create_execution(decision_artifact_id, **kwargs)
