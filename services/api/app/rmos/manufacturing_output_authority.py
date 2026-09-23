"""Pre-generation authority for governed manufacturing output.

The feasibility dispatcher is not a qualified evaluator for these tool ids.
An unresolved id yields unavailable feasibility, SafetyPolicy reads that as
UNKNOWN, and this module refuses before any program is built. It does not
register engines, mint a risk level, or read the audit registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from fastapi import HTTPException

from .api.rmos_feasibility_router import compute_feasibility_internal
from .policies import SafetyDecision, SafetyPolicy
from .runs_v2 import create_run_id, sha256_of_obj, sha256_of_text
from .runs_v2.store_completeness import validate_and_persist

REFUSAL_ERROR = "SAFETY_BLOCKED"
REFUSAL_MESSAGE = "Manufacturing output blocked by server-side safety policy."
GOVERNED_LANE = "governed"


@dataclass(frozen=True)
class ManufacturingAuthorityContext:
    """The decision that authorized one run. Not a qualification."""

    run_id: str
    feasibility: Dict[str, Any]
    feasibility_sha256: str
    decision: SafetyDecision
    risk_level: str
    warnings: tuple[str, ...]
    tool_id: str
    mode: str
    event_type: str
    request_summary: Dict[str, Any]


def _headers(run_id: str, *, gcode_sha256: Optional[str] = None) -> Dict[str, str]:
    headers = {"X-Run-ID": run_id, "X-ToolBox-Lane": GOVERNED_LANE}
    if gcode_sha256 is not None:
        headers["X-GCode-SHA256"] = gcode_sha256
    return headers


def require_manufacturing_output_authority(
    *,
    tool_id: str,
    mode: str,
    event_type: str,
    request_summary: Mapping[str, Any],
) -> ManufacturingAuthorityContext:
    """Resolve authority. Raise HTTP 409 before the caller builds output."""
    summary = dict(request_summary)
    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req={"tool_id": tool_id, **summary},
        context=event_type,
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feasibility_sha256 = sha256_of_obj(feasibility)
    run_id = create_run_id()
    warnings = tuple(decision.warnings)

    if SafetyPolicy.should_block(decision.risk_level):
        validate_and_persist(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            event_type=f"{event_type}_blocked",
            status="BLOCKED",
            request_summary=summary,
            feasibility=feasibility,
            feasibility_sha256=feasibility_sha256,
            risk_level=risk_level,
            block_reason=f"Blocked by safety policy: {risk_level}",
            decision_warnings=list(warnings),
            decision_score=decision.score,
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": REFUSAL_ERROR,
                "message": REFUSAL_MESSAGE,
                "run_id": run_id,
                "tool_id": tool_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
            headers=_headers(run_id),
        )

    return ManufacturingAuthorityContext(
        run_id=run_id,
        feasibility=feasibility,
        feasibility_sha256=feasibility_sha256,
        decision=decision,
        risk_level=risk_level,
        warnings=warnings,
        tool_id=tool_id,
        mode=mode,
        event_type=event_type,
        request_summary=summary,
    )


def persist_authorized_manufacturing_output(
    *,
    context: ManufacturingAuthorityContext,
    gcode_text: str,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """Record the program under the decision that already authorized it.

    The risk level is taken from ``context``. This function does not evaluate
    feasibility again and does not construct a fresh GREEN decision.
    """
    gcode_hash = sha256_of_text(gcode_text)
    validate_and_persist(
        run_id=context.run_id,
        mode=context.mode,
        tool_id=context.tool_id,
        event_type=f"{context.event_type}_execution",
        status="OK",
        request_summary=context.request_summary,
        feasibility=context.feasibility,
        feasibility_sha256=context.feasibility_sha256,
        risk_level=context.risk_level,
        decision_warnings=list(context.warnings),
        decision_score=context.decision.score,
        block_reason=context.decision.block_reason,
        gcode_sha256=gcode_hash,
        meta=meta,
    )
    return gcode_hash
