"""
RMOS Pipeline Services - Business Logic for Multi-Stage Execution

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 4

This module provides the service layer for the 4-stage pipeline:
SPEC → PLAN → DECISION → EXECUTE

Each function creates an immutable artifact and links it to its parent,
forming an auditable chain for deterministic replay.

Usage:
    # 1. Create spec from user request
    spec_id = create_spec_artifact(
        tool_type="roughing",
        design={"width": 100, "height": 50, ...},
        context={"tool_id": "endmill_6mm", ...},
        batch_label="Job-001",
    )

    # 2. Generate plan with feasibility scoring
    plan_id = create_plan_artifact(
        spec_artifact_id=spec_id,
        operations=[
            PlanOperation(op_id="op_1", feasibility_score=85, risk_bucket="GREEN"),
        ],
    )

    # 3. Operator approves plan
    decision_id = create_decision_artifact(
        plan_artifact_id=plan_id,
        approved_by="operator:john",
        reason="Looks good",
        op_order=["op_1"],
    )

    # 4. Execute approved decision
    execution_id = create_execution_artifact(
        decision_artifact_id=decision_id,
        results=[
            ExecutionResult(op_id="op_1", status="OK", ...),
        ],
    )
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar

from .schemas import (
    PipelineStage,
    PipelineStatus,
    RiskBucket,
    IndexMeta,
    SpecArtifact,
    PlanArtifact,
    DecisionArtifact,
    ExecutionArtifact,
    OpToolpathsArtifact,
    PlanOperation,
    ExecutionResult,
    ChosenOrder,
    SpecRequest,
    SpecResponse,
    PlanRequest,
    PlanResponse,
    ApproveRequest,
    ApproveResponse,
    ExecuteRequest,
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
    """
    Determine aggregate risk from list of operations.

    Rules:
    - Any RED → aggregate RED
    - Any UNKNOWN → aggregate UNKNOWN (if no RED)
    - Any YELLOW → aggregate YELLOW (if no RED/UNKNOWN)
    - All GREEN → aggregate GREEN
    """
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
        """
        Check feasibility for a design/context.

        Returns dict with:
        - score: float (0-100)
        - risk_bucket: str (GREEN, YELLOW, RED, UNKNOWN)
        - warnings: List[str]
        - details: Dict[str, Any] (calculator results, etc.)
        """
        ...


class ToolpathGenerator(Protocol):
    """Protocol for toolpath generation."""

    def generate(
        self,
        design: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate toolpaths for a design/context.

        Returns dict with:
        - moves: List[Dict] (canonical GCodeMoves)
        - gcode: str (generated G-code)
        - stats: Dict[str, Any] (path length, time, etc.)
        """
        ...


class PipelineService:
    """
    Service for managing pipeline operations.

    This class provides the core pipeline logic, allowing customization
    of feasibility checking and toolpath generation via protocols.
    """

    def __init__(
        self,
        tool_type: str,
        feasibility_checker: Optional[FeasibilityChecker] = None,
        toolpath_generator: Optional[ToolpathGenerator] = None,
    ):
        """
        Initialize pipeline service.

        Args:
            tool_type: Tool type prefix (e.g., "roughing", "drilling")
            feasibility_checker: Custom feasibility checker
            toolpath_generator: Custom toolpath generator
        """
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
        """
        Create a SPEC artifact.

        Args:
            design: Design parameters
            context: Machining context
            batch_label: User-provided batch label
            session_id: Session correlation ID
            items: Optional list of batch items

        Returns:
            SpecResponse with artifact ID
        """
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
        """
        Create a PLAN artifact from a spec.

        If operations are not provided, they are generated from the spec
        using the feasibility checker.

        Args:
            spec_artifact_id: Parent spec artifact ID
            operations: Pre-computed operations (optional)

        Returns:
            PlanResponse with artifact ID and operations
        """
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
        """
        Create a DECISION artifact (approval checkpoint).

        Args:
            plan_artifact_id: Plan to approve
            approved_by: Operator name/ID
            reason: Approval reason
            setup_order: Chosen setup order (optional)
            op_order: Chosen operation order (optional)

        Returns:
            ApproveResponse with artifact ID
        """
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
        """
        Create an EXECUTION artifact (generate toolpaths).

        This is where the actual toolpath generation happens.
        Feasibility is recomputed server-side for each operation.

        Args:
            decision_artifact_id: Approved decision to execute
            op_ids: Specific ops to execute (None = all)
            is_retry: Whether this is a retry execution
            retry_of_execution_id: Original execution being retried
            retry_reason: Reason for retry

        Returns:
            ExecuteResponse with results
        """
        # Read decision artifact
        decision = read_artifact(decision_artifact_id)
        if not decision:
            raise ValueError(f"Decision artifact not found: {decision_artifact_id}")

        decision_payload = decision.get("payload", {})
        decision_meta = decision.get("index_meta", {})

        plan_artifact_id = decision_payload.get("plan_artifact_id") or decision_meta.get("parent_plan_artifact_id")
        spec_artifact_id = decision_payload.get("spec_artifact_id") or decision_meta.get("parent_spec_artifact_id")
        batch_label = decision_payload.get("batch_label") or decision_meta.get("batch_label")
        session_id = decision_payload.get("session_id") or decision_meta.get("session_id")

        # Get execution order from decision
        chosen_order = decision_payload.get("chosen_order", {})
        all_op_order = chosen_order.get("op_order", [])

        # Filter to requested ops if specified
        if op_ids is not None:
            op_order = [op_id for op_id in all_op_order if op_id in op_ids]
        else:
            op_order = all_op_order

        # Read plan for operation details
        plan = read_artifact(plan_artifact_id) if plan_artifact_id else None
        plan_payload = plan.get("payload", {}) if plan else {}
        plan_operations = {
            op.get("op_id"): op
            for op in plan_payload.get("operations", [])
        }

        # Execute each operation
        results: List[ExecutionResult] = []
        children: List[Dict[str, str]] = []
        ok_count = 0
        blocked_count = 0
        error_count = 0

        for op_id in op_order:
            op_data = plan_operations.get(op_id, {})
            design = op_data.get("design", {})
            context = op_data.get("context", {})

            # Server-side feasibility recompute (mandatory)
            feas_result = {"score": 50.0, "risk_bucket": "UNKNOWN", "warnings": []}
            if self.feasibility_checker:
                try:
                    feas_result = self.feasibility_checker.check(design, context)
                except (ZeroDivisionError, ValueError, TypeError, KeyError, AttributeError) as e:  # WP-1: narrowed from except Exception (GOVERNANCE: fail-closed)
                    feas_result = {
                        "score": 0.0,
                        "risk_bucket": "ERROR",
                        "warnings": [str(e)],
                    }

            risk_bucket = RiskBucket(feas_result.get("risk_bucket", "UNKNOWN"))
            score = feas_result.get("score", 0.0)
            warnings = feas_result.get("warnings", [])

            # Block if RED or UNKNOWN
            if risk_bucket in (RiskBucket.RED, RiskBucket.UNKNOWN):
                blocked_count += 1
                status = PipelineStatus.BLOCKED

                # Create blocked op_toolpaths artifact
                child_id = write_artifact(
                    kind=self._kind("op_toolpaths"),
                    stage=PipelineStage.EXECUTE,
                    status=PipelineStatus.BLOCKED,
                    index_meta={
                        "tool_type": self.tool_type,
                        "parent_decision_artifact_id": decision_artifact_id,
                        "parent_plan_artifact_id": plan_artifact_id,
                        "parent_spec_artifact_id": spec_artifact_id,
                        "op_id": op_id,
                    },
                    payload={
                        "op_id": op_id,
                        "design": design,
                        "context": context,
                        "feasibility_recomputed": feas_result,
                        "blocked_reason": f"Server-side feasibility: {risk_bucket.value}",
                    },
                )

                results.append(ExecutionResult(
                    op_id=op_id,
                    status=status,
                    risk_bucket=risk_bucket,
                    feasibility_score=score,
                    toolpaths_artifact_id=child_id,
                    warnings=warnings,
                ))
                children.append({"artifact_id": child_id, "kind": self._kind("op_toolpaths")})
                continue

            # Generate toolpaths
            toolpaths_result: Dict[str, Any] = {}
            gcode = ""
            gcode_hash = None
            op_status = PipelineStatus.OK
            errors: List[str] = []

            if self.toolpath_generator:
                try:
                    toolpaths_result = self.toolpath_generator.generate(design, context)
                    gcode = toolpaths_result.get("gcode", "")
                    if gcode:
                        gcode_hash = sha256_of_obj(gcode)
                    ok_count += 1
                except (ValueError, TypeError, KeyError, AttributeError, OSError) as e:  # WP-1: narrowed from except Exception (GOVERNANCE: fail-closed)
                    op_status = PipelineStatus.ERROR
                    errors = [f"{type(e).__name__}: {str(e)}"]
                    error_count += 1
            else:
                # No generator, just mark as OK with empty toolpaths
                ok_count += 1

            # Create op_toolpaths artifact
            child_id = write_artifact(
                kind=self._kind("op_toolpaths"),
                stage=PipelineStage.EXECUTE,
                status=op_status,
                index_meta={
                    "tool_type": self.tool_type,
                    "parent_decision_artifact_id": decision_artifact_id,
                    "parent_plan_artifact_id": plan_artifact_id,
                    "parent_spec_artifact_id": spec_artifact_id,
                    "op_id": op_id,
                },
                payload={
                    "op_id": op_id,
                    "design": design,
                    "context": context,
                    "feasibility_recomputed": feas_result,
                    "toolpaths": toolpaths_result,
                    "gcode": gcode,
                },
                output_hash=gcode_hash,
            )

            results.append(ExecutionResult(
                op_id=op_id,
                status=op_status,
                risk_bucket=risk_bucket,
                feasibility_score=score,
                toolpaths_artifact_id=child_id,
                errors=errors,
                warnings=warnings,
            ))
            children.append({"artifact_id": child_id, "kind": self._kind("op_toolpaths")})

        # Create parent execution artifact
        overall_status = PipelineStatus.OK
        if error_count > 0:
            overall_status = PipelineStatus.ERROR
        elif blocked_count > 0 and ok_count == 0:
            overall_status = PipelineStatus.BLOCKED

        payload = {
            "created_utc": _utc_now_iso(),
            "decision_artifact_id": decision_artifact_id,
            "plan_artifact_id": plan_artifact_id,
            "spec_artifact_id": spec_artifact_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "op_count": len(op_order),
            "ok_count": ok_count,
            "blocked_count": blocked_count,
            "error_count": error_count,
            "results": [r.model_dump() for r in results],
            "children": children,
            "is_retry": is_retry,
            "retry_of_execution_id": retry_of_execution_id,
            "retry_reason": retry_reason,
        }

        index_meta = {
            "tool_type": self.tool_type,
            "parent_decision_artifact_id": decision_artifact_id,
            "parent_plan_artifact_id": plan_artifact_id,
            "parent_spec_artifact_id": spec_artifact_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "workflow_mode": "pipeline",
            "op_count": len(op_order),
            "ok_count": ok_count,
            "blocked_count": blocked_count,
            "error_count": error_count,
        }

        artifact_id = write_artifact(
            kind=self._kind("execution"),
            stage=PipelineStage.EXECUTE,
            status=overall_status,
            index_meta=index_meta,
            payload=payload,
        )

        return ExecuteResponse(
            execution_artifact_id=artifact_id,
            decision_artifact_id=decision_artifact_id,
            plan_artifact_id=plan_artifact_id,
            spec_artifact_id=spec_artifact_id,
            batch_label=batch_label,
            status=overall_status.value,
            op_count=len(op_order),
            ok_count=ok_count,
            blocked_count=blocked_count,
            error_count=error_count,
            results=results,
        )

    def retry_execution(
        self,
        execution_artifact_id: str,
        *,
        op_ids: Optional[List[str]] = None,
        reason: str = "retry",
    ) -> ExecuteResponse:
        """
        Retry a previous execution (immutable - creates new artifacts).

        Args:
            execution_artifact_id: Execution to retry
            op_ids: Specific ops to retry (None = all blocked/error)
            reason: Reason for retry

        Returns:
            ExecuteResponse with new execution
        """
        # Read original execution
        execution = read_artifact(execution_artifact_id)
        if not execution:
            raise ValueError(f"Execution artifact not found: {execution_artifact_id}")

        execution_payload = execution.get("payload", {})
        decision_artifact_id = execution_payload.get("decision_artifact_id")

        # Determine ops to retry
        if op_ids is None:
            # Retry all blocked/error ops
            results = execution_payload.get("results", [])
            op_ids = [
                r.get("op_id")
                for r in results
                if r.get("status") in ("BLOCKED", "ERROR")
            ]

        return self.create_execution(
            decision_artifact_id=decision_artifact_id,
            op_ids=op_ids,
            is_retry=True,
            retry_of_execution_id=execution_artifact_id,
            retry_reason=reason,
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
