"""
RMOS Run Orchestration Service

Cross-domain orchestration for RMOS run artifact workflows.
Lives in services/ because it coordinates multiple domains.

Architecture Layer: ORCHESTRATION (Layer 5)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

This service:
- Provides high-level workflows for run artifact management
- Coordinates feasibility evaluation across domains
- Bridges routers to RMOS storage layer
- Does NOT contain math (delegates to domain modules)

Usage:
    from app.services.rmos_run_service import (
        create_run_from_feasibility,
        get_run_with_attachments,
        list_runs_by_session,
    )
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# RMOS domain imports
from ..rmos.runs_v2 import (
    RunArtifact,
    RunStoreV2,
    create_run_id,
    validate_and_persist,
    get_run,
    list_runs_filtered,
    attach_advisory,
    check_completeness,
)
from ..rmos.runs_v2.hashing import sha256_of_obj, compute_feasibility_hash
from ..rmos.runs_v2.attachments import (
    put_json_attachment,
    get_attachment_path,
    verify_attachment,
)


# =============================================================================
# Run Creation Workflows
# =============================================================================

def create_run_from_feasibility(
    *,
    mode: str,
    tool_id: str,
    request_summary: Dict[str, Any],
    feasibility: Dict[str, Any],
    status: Optional[str] = None,
    block_reason: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """
    Create a run artifact from a feasibility evaluation.

    This is the primary entry point for creating run artifacts.
    Automatically:
    - Computes feasibility hash
    - Extracts risk level
    - Determines status from risk if not provided
    - Enforces completeness guard

    Args:
        mode: Operation mode (saw, router, cam, etc.)
        tool_id: Tool identifier
        request_summary: Sanitized request parameters
        feasibility: Server-computed feasibility result
        status: Override status (auto-determined from risk if None)
        block_reason: Why blocked (required if status=BLOCKED)
        meta: Additional metadata

    Returns:
        Persisted RunArtifact
    """
    # Compute feasibility hash
    feasibility_sha256 = sha256_of_obj(feasibility)

    # Extract risk level
    risk_level = feasibility.get("risk_level", "UNKNOWN")
    if not risk_level:
        risk_level = feasibility.get("decision", {}).get("risk_level", "UNKNOWN")

    # Auto-determine status from risk if not provided
    if status is None:
        if risk_level == "RED":
            status = "BLOCKED"
            block_reason = block_reason or "Risk level RED - operation blocked"
        elif risk_level == "ERROR":
            status = "ERROR"
            block_reason = block_reason or "Feasibility evaluation error"
        else:
            status = "OK"

    # Extract additional decision fields
    score = feasibility.get("score")
    warnings = feasibility.get("warnings", [])
    details = feasibility.get("details", {})

    # Delegate to validate_and_persist with completeness guard
    return validate_and_persist(
        run_id=create_run_id(),
        mode=mode,
        tool_id=tool_id,
        status=status,
        request_summary=request_summary,
        feasibility=feasibility,
        feasibility_sha256=feasibility_sha256,
        risk_level=risk_level,
        decision_score=score,
        decision_warnings=warnings,
        decision_details=details,
        block_reason=block_reason,
        meta=meta or {},
    )


def create_blocked_run(
    *,
    mode: str,
    tool_id: str,
    request_summary: Dict[str, Any],
    block_reason: str,
    feasibility: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """
    Create a BLOCKED run artifact.

    Use this when an operation is blocked before feasibility evaluation
    (e.g., validation failure, permission denied).

    Args:
        mode: Operation mode
        tool_id: Tool identifier
        request_summary: Request that was blocked
        block_reason: Why the operation was blocked
        feasibility: Partial feasibility if available
        meta: Additional metadata

    Returns:
        Persisted BLOCKED RunArtifact
    """
    # Create minimal feasibility if not provided
    if feasibility is None:
        feasibility = {
            "risk_level": "ERROR",
            "score": 0,
            "warnings": [block_reason],
            "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    return create_run_from_feasibility(
        mode=mode,
        tool_id=tool_id,
        request_summary=request_summary,
        feasibility=feasibility,
        status="BLOCKED",
        block_reason=block_reason,
        meta=meta,
    )


# =============================================================================
# Run Retrieval Workflows
# =============================================================================

def get_run_with_attachments(
    run_id: str,
    *,
    verify_integrity: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Get a run artifact with all attachments.

    Args:
        run_id: Run identifier
        verify_integrity: If True, verify attachment checksums

    Returns:
        Dict with run artifact and attachment metadata, or None if not found
    """
    artifact = get_run(run_id)
    if artifact is None:
        return None

    result = {
        "artifact": artifact.model_dump(),
        "attachments": [],
        "integrity_verified": False,
    }

    # Load attachment metadata
    if artifact.attachments:
        for att in artifact.attachments:
            att_info = {
                "sha256": att.sha256,
                "kind": att.kind,
                "filename": att.filename,
                "size_bytes": att.size_bytes,
                "path": get_attachment_path(att.sha256),
            }

            if verify_integrity:
                try:
                    att_info["verified"] = verify_attachment(att.sha256)
                except OSError as e:  # WP-1: narrowed from except Exception
                    att_info["verified"] = False
                    att_info["error"] = str(e)

            result["attachments"].append(att_info)

        result["integrity_verified"] = verify_integrity

    return result


def list_runs_by_session(
    workflow_session_id: str,
    *,
    limit: int = 100,
) -> List[RunArtifact]:
    """
    List all runs for a workflow session.

    Args:
        workflow_session_id: Session identifier
        limit: Maximum results

    Returns:
        List of RunArtifact objects for the session
    """
    return list_runs_filtered(
        workflow_session_id=workflow_session_id,
        limit=limit,
    )


def list_blocked_runs(
    *,
    mode: Optional[str] = None,
    limit: int = 50,
) -> List[RunArtifact]:
    """
    List all blocked runs, optionally filtered by mode.

    Args:
        mode: Filter by operation mode
        limit: Maximum results

    Returns:
        List of BLOCKED RunArtifact objects
    """
    return list_runs_filtered(
        status="BLOCKED",
        mode=mode,
        limit=limit,
    )


# =============================================================================
# Advisory Management
# =============================================================================

def attach_explanation(
    run_id: str,
    *,
    explanation_id: str,
    engine_id: str = "claude",
    engine_version: Optional[str] = None,
    request_id: Optional[str] = None,
) -> bool:
    """
    Attach an AI-generated explanation to a run.

    Args:
        run_id: Run to attach to
        explanation_id: Explanation asset ID
        engine_id: AI engine that generated it
        engine_version: Engine version
        request_id: Correlation ID

    Returns:
        True if attached, False if run not found
    """
    ref = attach_advisory(
        run_id=run_id,
        advisory_id=explanation_id,
        kind="explanation",
        engine_id=engine_id,
        engine_version=engine_version,
        request_id=request_id,
    )
    return ref is not None


# =============================================================================
# Validation Helpers
# =============================================================================

def validate_run_request(
    *,
    mode: str,
    tool_id: str,
    request_summary: Dict[str, Any],
) -> List[str]:
    """
    Validate a run request before processing.

    Returns list of validation errors (empty if valid).

    Args:
        mode: Operation mode
        tool_id: Tool identifier
        request_summary: Request to validate

    Returns:
        List of validation error messages
    """
    errors = []

    if not mode or not mode.strip():
        errors.append("mode is required")

    if not tool_id or not tool_id.strip():
        errors.append("tool_id is required")

    if not request_summary:
        errors.append("request_summary is required")

    return errors
