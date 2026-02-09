"""WP-3: Execution-stage logic for PipelineService.

Extracted from services.py to reduce god-object size.
Contains create_execution() and retry_execution() logic.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .schemas import (
    PipelineStage,
    PipelineStatus,
    RiskBucket,
    ExecutionResult,
    ExecuteResponse,
)
from .store import write_artifact, read_artifact
from ..runs import sha256_of_obj

if TYPE_CHECKING:
    from .services import PipelineService


def _utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def execute_pipeline(
    svc: PipelineService,
    decision_artifact_id: str,
    *,
    op_ids: Optional[List[str]] = None,
    is_retry: bool = False,
    retry_of_execution_id: Optional[str] = None,
    retry_reason: Optional[str] = None,
) -> ExecuteResponse:
    """Create an EXECUTION artifact (generate toolpaths).

    This is the core execution logic, extracted from PipelineService.create_execution().
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
        _execute_single_op(
            svc=svc,
            op_id=op_id,
            plan_operations=plan_operations,
            decision_artifact_id=decision_artifact_id,
            plan_artifact_id=plan_artifact_id,
            spec_artifact_id=spec_artifact_id,
            results=results,
            children=children,
            counters={"ok": ok_count, "blocked": blocked_count, "error": error_count},
        )
        ok_count = sum(1 for r in results if r.status == PipelineStatus.OK)
        blocked_count = sum(1 for r in results if r.status == PipelineStatus.BLOCKED)
        error_count = sum(1 for r in results if r.status == PipelineStatus.ERROR)

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
        "tool_type": svc.tool_type,
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
        kind=svc._kind("execution"),
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


def _execute_single_op(
    *,
    svc: PipelineService,
    op_id: str,
    plan_operations: Dict[str, Any],
    decision_artifact_id: str,
    plan_artifact_id: Optional[str],
    spec_artifact_id: Optional[str],
    results: List[ExecutionResult],
    children: List[Dict[str, str]],
    counters: Dict[str, int],
) -> None:
    """Execute a single operation within the pipeline.

    Mutates results and children lists in place.
    """
    op_data = plan_operations.get(op_id, {})
    design = op_data.get("design", {})
    context = op_data.get("context", {})

    # Server-side feasibility recompute (mandatory)
    feas_result = {"score": 50.0, "risk_bucket": "UNKNOWN", "warnings": []}
    if svc.feasibility_checker:
        try:
            feas_result = svc.feasibility_checker.check(design, context)
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
        child_id = write_artifact(
            kind=svc._kind("op_toolpaths"),
            stage=PipelineStage.EXECUTE,
            status=PipelineStatus.BLOCKED,
            index_meta={
                "tool_type": svc.tool_type,
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
            status=PipelineStatus.BLOCKED,
            risk_bucket=risk_bucket,
            feasibility_score=score,
            toolpaths_artifact_id=child_id,
            warnings=warnings,
        ))
        children.append({"artifact_id": child_id, "kind": svc._kind("op_toolpaths")})
        return

    # Generate toolpaths
    toolpaths_result: Dict[str, Any] = {}
    gcode = ""
    gcode_hash = None
    op_status = PipelineStatus.OK
    errors: List[str] = []

    if svc.toolpath_generator:
        try:
            toolpaths_result = svc.toolpath_generator.generate(design, context)
            gcode = toolpaths_result.get("gcode", "")
            if gcode:
                gcode_hash = sha256_of_obj(gcode)
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as e:  # WP-1: narrowed from except Exception (GOVERNANCE: fail-closed)
            op_status = PipelineStatus.ERROR
            errors = [f"{type(e).__name__}: {str(e)}"]

    # Create op_toolpaths artifact
    child_id = write_artifact(
        kind=svc._kind("op_toolpaths"),
        stage=PipelineStage.EXECUTE,
        status=op_status,
        index_meta={
            "tool_type": svc.tool_type,
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
    children.append({"artifact_id": child_id, "kind": svc._kind("op_toolpaths")})


def retry_pipeline_execution(
    svc: PipelineService,
    execution_artifact_id: str,
    *,
    op_ids: Optional[List[str]] = None,
    reason: str = "retry",
) -> ExecuteResponse:
    """Retry a previous execution (immutable - creates new artifacts)."""
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

    return execute_pipeline(
        svc,
        decision_artifact_id=decision_artifact_id,
        op_ids=op_ids,
        is_retry=True,
        retry_of_execution_id=execution_artifact_id,
        retry_reason=reason,
    )
