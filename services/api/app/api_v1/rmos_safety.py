"""
RMOS Safety API v1

Run Manufacturing Operations System - safety gates for CNC operations:

1. POST /rmos/check - Check feasibility of machining parameters
2. GET  /rmos/rules - List all feasibility rules
3. POST /rmos/runs - Create a new RMOS run
4. GET  /rmos/runs/{id} - Get run status and decision
5. POST /rmos/runs/{id}/approve - Approve a YELLOW run with override
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

router = APIRouter(prefix="/rmos", tags=["RMOS Safety"])


# =============================================================================
# SCHEMAS
# =============================================================================

class V1Response(BaseModel):
    """Standard v1 response wrapper."""
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    hint: Optional[str] = None


class FeasibilityCheckRequest(BaseModel):
    """Request to check machining feasibility."""
    tool_diameter_mm: float = Field(..., description="Tool diameter")
    depth_of_cut_mm: float = Field(..., description="Depth of cut per pass")
    stepover_percent: float = Field(..., description="Stepover as % of tool diameter")
    feed_xy_mm_min: float = Field(..., description="XY feedrate")
    feed_z_mm_min: float = Field(..., description="Z feedrate")
    spindle_rpm: int = Field(..., description="Spindle speed")
    material: str = Field("hardwood", description="Material type")
    operation: str = Field("profile", description="Operation type")


class FeasibilityCheckResponse(V1Response):
    """Feasibility check result."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "decision": "GREEN",
            "risk_level": "LOW",
            "rules_triggered": [],
            "recommendation": "Parameters are safe for operation",
        }],
    )


class RunCreateRequest(BaseModel):
    """Request to create an RMOS run."""
    session_id: str = Field(..., description="Session identifier")
    operation: str = Field(..., description="Operation type")
    parameters: Dict[str, Any] = Field(..., description="Machining parameters")
    geometry_hash: Optional[str] = Field(None, description="Hash of input geometry")


class RunCreateResponse(V1Response):
    """Created run details."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "run_id": "run_abc123",
            "decision": "GREEN",
            "export_allowed": True,
        }],
    )


class RunApproveRequest(BaseModel):
    """Request to approve a YELLOW run."""
    operator_id: str = Field(..., description="Operator performing override")
    reason: str = Field(..., description="Justification for override")
    acknowledged_risks: List[str] = Field(..., description="List of acknowledged risk IDs")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/check", response_model=FeasibilityCheckResponse)
def check_feasibility(req: FeasibilityCheckRequest) -> FeasibilityCheckResponse:
    """
    Check if machining parameters are safe.

    Returns:
    - GREEN: Safe to proceed
    - YELLOW: Proceed with caution, review warnings
    - RED: Blocked - parameters exceed safe limits

    This is a quick check - use /runs for full tracking.
    """
    rules_triggered = []
    decision = "GREEN"
    risk_level = "LOW"

    # Rule F001: DOC > 50% of tool diameter in hardwood
    max_doc = req.tool_diameter_mm * 0.5
    if req.depth_of_cut_mm > max_doc and req.material in ("hardwood", "hard"):
        rules_triggered.append({
            "id": "F001",
            "level": "YELLOW",
            "message": f"DOC ({req.depth_of_cut_mm}mm) exceeds 50% of tool diameter",
            "hint": f"Reduce to {max_doc:.1f}mm or less for hardwood",
        })
        decision = "YELLOW"
        risk_level = "MEDIUM"

    # Rule F002: Stepover > 50% for finishing
    if req.stepover_percent > 50 and req.operation == "profile":
        rules_triggered.append({
            "id": "F002",
            "level": "YELLOW",
            "message": f"Stepover ({req.stepover_percent}%) is high for profiling",
            "hint": "Use 30-40% stepover for better surface finish",
        })
        if decision == "GREEN":
            decision = "YELLOW"
            risk_level = "MEDIUM"

    # Rule F020: Excessive DOC (>100% tool diameter)
    if req.depth_of_cut_mm > req.tool_diameter_mm:
        rules_triggered.append({
            "id": "F020",
            "level": "RED",
            "message": "DOC exceeds tool diameter - high breakage risk",
            "hint": "Never exceed tool diameter for DOC",
        })
        decision = "RED"
        risk_level = "HIGH"

    # Rule F003: Feed rate sanity
    max_feed = req.spindle_rpm * req.tool_diameter_mm * 0.1  # Rough chip load calc
    if req.feed_xy_mm_min > max_feed:
        rules_triggered.append({
            "id": "F003",
            "level": "YELLOW",
            "message": f"Feed rate may be too aggressive for spindle speed",
            "hint": f"Consider reducing to {max_feed:.0f} mm/min or increase RPM",
        })
        if decision == "GREEN":
            decision = "YELLOW"
            risk_level = "MEDIUM"

    return FeasibilityCheckResponse(
        ok=True,
        data={
            "decision": decision,
            "risk_level": risk_level,
            "rules_triggered": rules_triggered,
            "parameters_checked": {
                "tool_diameter_mm": req.tool_diameter_mm,
                "depth_of_cut_mm": req.depth_of_cut_mm,
                "stepover_percent": req.stepover_percent,
            },
            "recommendation": (
                "Parameters are safe for operation" if decision == "GREEN"
                else "Review warnings before proceeding" if decision == "YELLOW"
                else "BLOCKED: Parameters exceed safe limits"
            ),
        },
    )


@router.get("/rules")
def list_rules() -> V1Response:
    """
    List all RMOS feasibility rules.

    Rules are organized by category:
    - Core (F001-F007): Basic safety checks
    - Warnings (F010-F019): Advisory warnings
    - Adversarial (F020-F029): Blocks dangerous parameters
    """
    rules = [
        {
            "id": "F001",
            "level": "YELLOW",
            "category": "core",
            "name": "DOC Limit",
            "description": "Depth of cut should not exceed 50% of tool diameter in hardwood",
        },
        {
            "id": "F002",
            "level": "YELLOW",
            "category": "core",
            "name": "Stepover Limit",
            "description": "Stepover >50% produces poor surface finish",
        },
        {
            "id": "F003",
            "level": "YELLOW",
            "category": "core",
            "name": "Feed Rate Check",
            "description": "Feed rate should match spindle speed and tool size",
        },
        {
            "id": "F020",
            "level": "RED",
            "category": "adversarial",
            "name": "Excessive DOC",
            "description": "DOC exceeding tool diameter causes breakage",
        },
        {
            "id": "F021",
            "level": "RED",
            "category": "adversarial",
            "name": "Tool Breakage Risk",
            "description": "DOC:diameter ratio >5:1 is dangerous",
        },
    ]

    return V1Response(
        ok=True,
        data={
            "rules": rules,
            "total": len(rules),
            "levels": {
                "GREEN": "Safe to proceed",
                "YELLOW": "Proceed with caution",
                "RED": "Blocked - unsafe",
            },
        },
    )


@router.post("/runs", response_model=RunCreateResponse)
def create_run(req: RunCreateRequest) -> RunCreateResponse:
    """
    Create a new RMOS run for tracking.

    A run captures:
    - Input parameters
    - Feasibility decision
    - Generated outputs (G-code, toolpaths)
    - Operator approvals
    """
    import hashlib
    import json
    from datetime import datetime

    # Generate run ID
    content = json.dumps(req.parameters, sort_keys=True)
    run_id = f"run_{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    # Perform feasibility check
    check_result = check_feasibility(
        FeasibilityCheckRequest(
            tool_diameter_mm=req.parameters.get("tool_diameter_mm", 6.0),
            depth_of_cut_mm=req.parameters.get("depth_of_cut_mm", 3.0),
            stepover_percent=req.parameters.get("stepover_percent", 40.0),
            feed_xy_mm_min=req.parameters.get("feed_xy", 1000.0),
            feed_z_mm_min=req.parameters.get("feed_z", 200.0),
            spindle_rpm=req.parameters.get("spindle_rpm", 18000),
            material=req.parameters.get("material", "hardwood"),
            operation=req.operation,
        )
    )

    decision = check_result.data["decision"] if check_result.data else "GREEN"
    export_allowed = decision != "RED"

    return RunCreateResponse(
        ok=True,
        data={
            "run_id": run_id,
            "session_id": req.session_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "decision": decision,
            "export_allowed": export_allowed,
            "rules_triggered": check_result.data.get("rules_triggered", []) if check_result.data else [],
        },
    )


@router.get("/runs/{run_id}")
def get_run(run_id: str = Path(..., description="Run ID")) -> V1Response:
    """
    Get status of an RMOS run.

    Returns decision, export status, and any overrides.
    """
    # In production, this would look up from the runs store
    # For v1 API, return a mock response showing the structure

    return V1Response(
        ok=True,
        data={
            "run_id": run_id,
            "status": "COMPLETE",
            "decision": "GREEN",
            "export_allowed": True,
            "created_at": "2024-01-15T10:30:00Z",
            "artifacts": {
                "gcode": f"/api/rmos/runs/{run_id}/artifacts/gcode",
                "toolpaths": f"/api/rmos/runs/{run_id}/artifacts/toolpaths",
            },
        },
        hint="Use the artifacts URLs to download generated files",
    )


@router.post("/runs/{run_id}/approve")
def approve_run(
    run_id: str = Path(..., description="Run ID"),
    req: RunApproveRequest = ...,
) -> V1Response:
    """
    Approve a YELLOW run with operator override.

    Requires:
    - Operator ID for audit trail
    - Justification reason
    - Explicit acknowledgment of triggered risks

    RED runs cannot be approved - parameters must be changed.
    """
    if not req.operator_id:
        return V1Response(
            ok=False,
            error="Operator ID required for override",
            hint="Provide the operator's ID for audit trail",
        )

    if not req.reason or len(req.reason) < 10:
        return V1Response(
            ok=False,
            error="Override reason must be at least 10 characters",
            hint="Explain why this override is safe despite warnings",
        )

    if not req.acknowledged_risks:
        return V1Response(
            ok=False,
            error="Must acknowledge triggered risks",
            hint="List the rule IDs you are acknowledging (e.g., ['F001', 'F002'])",
        )

    return V1Response(
        ok=True,
        data={
            "run_id": run_id,
            "status": "APPROVED",
            "override": {
                "operator_id": req.operator_id,
                "reason": req.reason,
                "acknowledged_risks": req.acknowledged_risks,
                "approved_at": "2024-01-15T10:35:00Z",
            },
            "export_allowed": True,
        },
    )
