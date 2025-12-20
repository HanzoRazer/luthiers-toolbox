"""
Saw Lab Orchestration Service

Cross-domain orchestration between Saw Lab and other modules.
Lives in services/ because it crosses domain boundaries.

Architecture Layer: ORCHESTRATION (Layer 5)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

This service:
- Coordinates Saw Lab calculations with RMOS feasibility
- Bridges Saw Lab risk evaluation to run artifacts
- Does NOT contain math (delegates to saw_lab/ modules)

Usage:
    from app.services.saw_lab_service import (
        evaluate_saw_operation,
        create_saw_run_artifact,
    )
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone

# Domain imports - Saw Lab owns the calculations
from ..saw_lab.risk_evaluator import SawRiskEvaluator
from ..saw_lab.models import SawContext, SawDesign

# Domain imports - RMOS owns the run artifacts
from ..rmos.runs_v2 import (
    validate_and_persist,
    create_run_id,
    RunArtifact,
)
from ..rmos.runs_v2.hashing import sha256_of_obj


def evaluate_saw_operation(
    *,
    blade_diameter_mm: float,
    rpm: float,
    feed_rate_mm_min: float,
    cut_depth_mm: float,
    material_id: str,
    tool_id: str,
) -> Dict[str, Any]:
    """
    Evaluate a saw operation for feasibility.

    Orchestrates calls to Saw Lab risk and heat calculations,
    returning a unified feasibility result.

    Args:
        blade_diameter_mm: Blade diameter in mm
        rpm: Spindle speed
        feed_rate_mm_min: Feed rate in mm/min
        cut_depth_mm: Depth of cut in mm
        material_id: Material identifier
        tool_id: Tool identifier

    Returns:
        Feasibility dict with risk_level, score, warnings, details
    """
    # Build Saw Lab domain objects
    ctx = SawContext(
        blade_diameter_mm=blade_diameter_mm,
        rpm=rpm,
        material_id=material_id,
    )
    design = SawDesign(
        cut_depth_mm=cut_depth_mm,
        feed_rate_mm_min=feed_rate_mm_min,
    )

    # Delegate to Saw Lab domain modules (no math here)
    evaluator = SawRiskEvaluator()
    risk_level = evaluator.evaluate(design, ctx)

    # Build warnings from risk level
    warnings = []
    if risk_level.value == "RED":
        warnings.append("High risk operation - review parameters")
    elif risk_level.value == "YELLOW":
        warnings.append("Moderate risk - proceed with caution")

    return {
        "risk_level": risk_level.value if hasattr(risk_level, 'value') else str(risk_level),
        "score": 100.0 if risk_level.value == "GREEN" else (50.0 if risk_level.value == "YELLOW" else 0.0),
        "warnings": warnings,
        "details": {
            "blade_diameter_mm": blade_diameter_mm,
            "rpm": rpm,
            "cut_depth_mm": cut_depth_mm,
            "feed_rate_mm_min": feed_rate_mm_min,
            "material_id": material_id,
        },
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def create_saw_run_artifact(
    *,
    request_summary: Dict[str, Any],
    feasibility: Dict[str, Any],
    tool_id: str,
    status: str = "OK",
    block_reason: Optional[str] = None,
    outputs: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """
    Create and persist a Saw Lab run artifact.

    Bridges Saw Lab operations to RMOS run artifact storage.
    Uses validate_and_persist() to enforce completeness guard.

    Args:
        request_summary: Sanitized request parameters
        feasibility: Result from evaluate_saw_operation()
        tool_id: Tool identifier
        status: Run status (OK, BLOCKED, ERROR)
        block_reason: Why blocked (if status=BLOCKED)
        outputs: Generated outputs (G-code, toolpath, etc.)
        meta: Additional metadata

    Returns:
        Persisted RunArtifact (check status for completeness violations)
    """
    # Compute feasibility hash for audit trail
    feasibility_sha256 = sha256_of_obj(feasibility)

    # Extract risk level from feasibility
    risk_level = feasibility.get("risk_level", "UNKNOWN")

    # Delegate to RMOS for artifact creation with completeness guard
    artifact = validate_and_persist(
        run_id=create_run_id(),
        mode="saw",
        tool_id=tool_id,
        status=status,
        request_summary=request_summary,
        feasibility=feasibility,
        feasibility_sha256=feasibility_sha256,
        risk_level=risk_level,
        decision_score=feasibility.get("score"),
        decision_warnings=feasibility.get("warnings", []),
        decision_details=feasibility.get("details", {}),
        block_reason=block_reason,
        meta=meta or {},
    )

    return artifact


# =============================================================================
# Higher-level workflows
# =============================================================================

def execute_saw_workflow(
    *,
    blade_diameter_mm: float,
    rpm: float,
    feed_rate_mm_min: float,
    cut_depth_mm: float,
    material_id: str,
    tool_id: str,
    generate_gcode: bool = True,
) -> RunArtifact:
    """
    Execute complete saw workflow: evaluate -> decide -> persist.

    This is the main entry point for saw operations that need
    full RMOS integration with feasibility evaluation.

    Args:
        blade_diameter_mm: Blade diameter
        rpm: Spindle speed
        feed_rate_mm_min: Feed rate
        cut_depth_mm: Cut depth
        material_id: Material ID
        tool_id: Tool ID
        generate_gcode: Whether to generate G-code (if feasible)

    Returns:
        RunArtifact with status OK, BLOCKED, or ERROR
    """
    # Step 1: Evaluate feasibility
    feasibility = evaluate_saw_operation(
        blade_diameter_mm=blade_diameter_mm,
        rpm=rpm,
        feed_rate_mm_min=feed_rate_mm_min,
        cut_depth_mm=cut_depth_mm,
        material_id=material_id,
        tool_id=tool_id,
    )

    # Step 2: Decide status based on risk
    risk_level = feasibility.get("risk_level", "UNKNOWN")
    if risk_level == "RED":
        status = "BLOCKED"
        block_reason = "Risk level RED - operation not permitted"
    elif risk_level == "ERROR":
        status = "ERROR"
        block_reason = "Feasibility evaluation failed"
    else:
        status = "OK"
        block_reason = None

    # Step 3: Build request summary
    request_summary = {
        "blade_diameter_mm": blade_diameter_mm,
        "rpm": rpm,
        "feed_rate_mm_min": feed_rate_mm_min,
        "cut_depth_mm": cut_depth_mm,
        "material_id": material_id,
        "tool_id": tool_id,
    }

    # Step 4: Create and persist artifact
    return create_saw_run_artifact(
        request_summary=request_summary,
        feasibility=feasibility,
        tool_id=tool_id,
        status=status,
        block_reason=block_reason,
        meta={"workflow": "execute_saw_workflow"},
    )
