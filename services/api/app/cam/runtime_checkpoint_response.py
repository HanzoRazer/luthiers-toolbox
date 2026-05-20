"""
Runtime Checkpoint Response Helpers

CAM Dev Order 7Q: Shared response helpers for runtime governance checkpoints.

This module provides:
  - RuntimeCheckpointSummary model for checkpoint results
  - Pathway construction helpers
  - RED blocking helpers
  - Response enrichment helpers

7Q invariants (always enforced):
  - execution_authorized = False
  - machine_output_allowed = False
  - serializer_execution_allowed = False

Guardrail:
  7Q wires governance checkpoints into selected live router boundaries.
  It blocks RED only for runtime-adjacent validation/authorization actions.
  It does not block read-only discovery, auto-infer governance lineage,
  invoke serializers, or authorize execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.cam.runtime_governance_enforcement import (
    RuntimeEnforcementRequest,
    RuntimeGovernanceEnforcementEvaluation,
)
from app.cam.runtime_enforcement_policy import evaluate_runtime_enforcement


# -----------------------------------------------------------------------------
# Checkpoint Summary Model
# -----------------------------------------------------------------------------

class RuntimeCheckpointSummary(BaseModel):
    """
    Lightweight checkpoint summary for router responses.

    Provides essential checkpoint state without full evaluation detail.
    """

    checkpoint_gate: Literal["green", "yellow", "red"] = Field(
        ..., description="Checkpoint gate status"
    )
    checkpoint_passed: bool = Field(
        ..., description="Whether checkpoint allows proceeding"
    )
    blocking_issues: List[str] = Field(
        default_factory=list, description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list, description="YELLOW warnings"
    )
    enforcement_hash: str = Field(
        default="", description="Deterministic enforcement hash"
    )
    pathway: str = Field(
        default="", description="Evaluated runtime pathway"
    )

    # 7Q invariants
    execution_authorized: bool = Field(
        default=False, description="Always False — 7Q does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False, description="Always False — 7Q does not allow machine output"
    )


class RuntimeCheckpointBlockedResponse(BaseModel):
    """
    Response body for HTTP 409 when checkpoint blocks a route.

    Used when RED checkpoint prevents route execution.
    """

    error: str = Field(
        default="runtime_governance_checkpoint_blocked",
        description="Error code"
    )
    message: str = Field(
        ..., description="Human-readable explanation"
    )
    checkpoint_summary: RuntimeCheckpointSummary = Field(
        ..., description="Checkpoint details"
    )
    route: str = Field(
        default="", description="Blocked route path"
    )


# -----------------------------------------------------------------------------
# Pathway Construction Helpers
# -----------------------------------------------------------------------------

def build_export_route_pathway(route: str) -> str:
    """
    Build pathway for export route checkpoint.

    Example: build_export_route_pathway("/api/cam/export/lifecycle/validate")
             -> "export_route:/api/cam/export/lifecycle/validate"
    """
    return f"export_route:{route}"


def build_translator_dispatch_pathway(translator_id: str) -> str:
    """
    Build pathway for translator dispatch checkpoint.

    Example: build_translator_dispatch_pathway("dxf_r12")
             -> "translator_dispatch:dxf_r12"
    """
    return f"translator_dispatch:{translator_id}"


def build_serializer_boundary_pathway(boundary_id: str) -> str:
    """
    Build pathway for serializer boundary checkpoint.

    Example: build_serializer_boundary_pathway("dxf_compat")
             -> "serializer_boundary:dxf_compat"
    """
    return f"serializer_boundary:{boundary_id}"


def build_postprocessor_boundary_pathway(postprocessor_id: str) -> str:
    """
    Build pathway for postprocessor boundary checkpoint.

    Example: build_postprocessor_boundary_pathway("grbl_placeholder")
             -> "postprocessor_boundary:grbl_placeholder"
    """
    return f"postprocessor_boundary:{postprocessor_id}"


def build_geometry_consumption_pathway(consumption_id: str) -> str:
    """
    Build pathway for geometry consumption checkpoint.

    Example: build_geometry_consumption_pathway("body_grid_to_export")
             -> "geometry_consumption:body_grid_to_export"
    """
    return f"geometry_consumption:{consumption_id}"


# -----------------------------------------------------------------------------
# Checkpoint Evaluation Helper
# -----------------------------------------------------------------------------

def evaluate_runtime_pathway_checkpoint(
    runtime_pathway: str,
    translator_id: Optional[str] = None,
    export_route: Optional[str] = None,
    consumer_id: Optional[str] = None,
    ledger_entry_id: Optional[str] = None,
    quarantine_id: Optional[str] = None,
    request_context: Optional[Dict[str, Any]] = None,
) -> RuntimeGovernanceEnforcementEvaluation:
    """
    Evaluate runtime governance checkpoint for a pathway.

    Wrapper around 7P evaluate_runtime_enforcement for router use.

    Args:
        runtime_pathway: Pathway declaration (format: type:target)
        translator_id: Optional translator identifier
        export_route: Optional export route path
        consumer_id: Optional 7N consumer reference
        ledger_entry_id: Optional 7O ledger entry reference
        quarantine_id: Optional 7H quarantine reference
        request_context: Optional additional context

    Returns:
        RuntimeGovernanceEnforcementEvaluation from 7P

    Note:
        This does NOT auto-discover governance references.
        Pass None unless explicitly provided by the request.
    """
    request = RuntimeEnforcementRequest(
        runtime_pathway=runtime_pathway,
        translator_id=translator_id,
        export_route=export_route,
        consumer_id=consumer_id,
        ledger_entry_id=ledger_entry_id,
        quarantine_id=quarantine_id,
        request_context=request_context or {},
    )

    return evaluate_runtime_enforcement(request)


# -----------------------------------------------------------------------------
# Summary Conversion
# -----------------------------------------------------------------------------

def to_checkpoint_summary(
    evaluation: RuntimeGovernanceEnforcementEvaluation,
) -> RuntimeCheckpointSummary:
    """
    Convert full evaluation to lightweight summary.

    Args:
        evaluation: Full 7P enforcement evaluation

    Returns:
        RuntimeCheckpointSummary suitable for response embedding
    """
    return RuntimeCheckpointSummary(
        checkpoint_gate=evaluation.severity,
        checkpoint_passed=evaluation.governance_checkpoint_passed,
        blocking_issues=evaluation.blocking_issues,
        warnings=evaluation.warnings,
        enforcement_hash=evaluation.deterministic_enforcement_hash,
        pathway=evaluation.runtime_pathway,
        execution_authorized=False,
        machine_output_allowed=False,
    )


# -----------------------------------------------------------------------------
# RED Blocking Helpers
# -----------------------------------------------------------------------------

def is_red_checkpoint(evaluation: RuntimeGovernanceEnforcementEvaluation) -> bool:
    """Check if evaluation is RED (blocking)."""
    return evaluation.severity == "red"


def is_yellow_checkpoint(evaluation: RuntimeGovernanceEnforcementEvaluation) -> bool:
    """Check if evaluation is YELLOW (warning)."""
    return evaluation.severity == "yellow"


def is_green_checkpoint(evaluation: RuntimeGovernanceEnforcementEvaluation) -> bool:
    """Check if evaluation is GREEN (pass)."""
    return evaluation.severity == "green"


def raise_on_red_checkpoint(
    evaluation: RuntimeGovernanceEnforcementEvaluation,
    route: str,
) -> None:
    """
    Raise HTTP 409 Conflict if checkpoint is RED.

    Use this for runtime-adjacent validation/authorization routes
    that should be blocked on RED.

    Args:
        evaluation: 7P enforcement evaluation
        route: Route path being blocked (for error message)

    Raises:
        HTTPException: 409 Conflict with RuntimeCheckpointBlockedResponse body
    """
    if not is_red_checkpoint(evaluation):
        return

    summary = to_checkpoint_summary(evaluation)

    blocked_response = RuntimeCheckpointBlockedResponse(
        error="runtime_governance_checkpoint_blocked",
        message=(
            f"Runtime governance checkpoint blocked route: {route}. "
            f"Blocking issues: {', '.join(summary.blocking_issues)}"
        ),
        checkpoint_summary=summary,
        route=route,
    )

    raise HTTPException(
        status_code=409,
        detail=blocked_response.model_dump(),
    )


# -----------------------------------------------------------------------------
# Response Enrichment (Optional Summary Field)
# -----------------------------------------------------------------------------

def maybe_add_checkpoint_to_dict(
    response_dict: Dict[str, Any],
    evaluation: RuntimeGovernanceEnforcementEvaluation,
    field_name: str = "runtime_checkpoint_summary",
) -> Dict[str, Any]:
    """
    Add checkpoint summary to response dict if checkpoint was evaluated.

    For use with responses that support optional summary fields.

    Args:
        response_dict: Response data as dict
        evaluation: 7P enforcement evaluation
        field_name: Name of summary field to add

    Returns:
        Response dict with checkpoint summary added
    """
    summary = to_checkpoint_summary(evaluation)
    response_dict[field_name] = summary.model_dump()
    return response_dict
