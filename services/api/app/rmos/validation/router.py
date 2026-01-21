"""
Validation Log Router

API endpoints for:
- Running validation scenarios
- Logging validation results
- Browsing validation history
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .store import (
    ValidationRunRecord,
    ValidationSessionRecord,
    write_validation_run,
    write_validation_session,
    get_validation_run,
    get_validation_session,
    list_validation_sessions,
    list_validation_runs,
    get_latest_session_summary,
)
from .harness import (
    load_scenarios,
    evaluate_scenario,
    run_validation,
    SCENARIOS_FILE,
)


router = APIRouter(prefix="/api/rmos/validation", tags=["validation"])


# =============================================================================
# Request/Response Models
# =============================================================================

class RunScenarioRequest(BaseModel):
    """Request to run a single scenario."""
    scenario_id: str
    session_id: Optional[str] = None
    operator: Optional[str] = None
    notes: str = ""


class RunBatchRequest(BaseModel):
    """Request to run a batch of scenarios."""
    tier: Optional[str] = Field(None, description="Filter by tier: baseline, edge_pressure, adversarial")
    scenario_ids: Optional[List[str]] = Field(None, description="Specific scenario IDs to run")
    operator: Optional[str] = None
    notes: str = ""


class LogResultRequest(BaseModel):
    """Request to log a manual validation result."""
    scenario_id: str
    scenario_name: str
    tier: str

    expected_decision: List[str]
    actual_decision: str
    expected_rules_any: List[str] = Field(default_factory=list)
    actual_rules: List[str] = Field(default_factory=list)
    expected_export_allowed: bool
    actual_export_allowed: bool

    decision_match: bool
    rules_match: bool
    export_match: bool
    passed: bool

    session_id: Optional[str] = None
    notes: str = ""


class ValidationSummaryResponse(BaseModel):
    """Summary of validation status."""
    latest_session_id: Optional[str] = None
    latest_timestamp: Optional[str] = None
    total: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: str = "N/A"
    red_leaks: int = 0
    release_authorized: bool = False


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/scenarios")
async def get_scenarios(
    tier: Optional[str] = Query(None, description="Filter by tier"),
) -> Dict[str, Any]:
    """
    Get available validation scenarios.
    """
    scenarios = load_scenarios()

    if tier:
        scenarios = [s for s in scenarios if s.get("tier") == tier]

    return {
        "total": len(scenarios),
        "scenarios": scenarios,
    }


@router.post("/run")
async def run_scenario(req: RunScenarioRequest) -> Dict[str, Any]:
    """
    Run a single validation scenario and log the result.
    """
    scenarios = load_scenarios()

    # Find the scenario
    scenario = next((s for s in scenarios if s.get("id") == req.scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {req.scenario_id}")

    # Evaluate
    result = evaluate_scenario(scenario)

    # Create record
    record = ValidationRunRecord(
        scenario_id=result.scenario_id,
        scenario_name=result.scenario_name,
        tier=result.tier,
        timestamp_utc=result.timestamp_utc,
        expected_decision=result.expected_decision,
        actual_decision=result.actual_decision,
        expected_rules_any=result.expected_rules_any,
        actual_rules=result.actual_rules,
        expected_export_allowed=result.expected_export_allowed,
        actual_export_allowed=result.actual_export_allowed,
        decision_match=result.decision_match,
        rules_match=result.rules_match,
        export_match=result.export_match,
        passed=result.passed,
        feasibility_input=result.feasibility_input,
        feasibility_result=result.feasibility_result,
        notes=req.notes or result.notes,
        session_id=req.session_id,
    )

    # Persist
    run_id = write_validation_run(record)

    return {
        "run_id": run_id,
        "scenario_id": req.scenario_id,
        "passed": result.passed,
        "actual_decision": result.actual_decision,
        "expected_decision": result.expected_decision,
        "rules_triggered": result.actual_rules,
        "notes": record.notes,
    }


@router.post("/run-batch")
async def run_batch(req: RunBatchRequest) -> Dict[str, Any]:
    """
    Run a batch of validation scenarios and create a session.
    """
    scenarios = load_scenarios()

    # Apply filters
    if req.scenario_ids:
        scenarios = [s for s in scenarios if s.get("id") in req.scenario_ids]
    elif req.tier:
        scenarios = [s for s in scenarios if s.get("tier") == req.tier]

    if not scenarios:
        raise HTTPException(status_code=400, detail="No scenarios match the filter criteria")

    # Create session
    session = ValidationSessionRecord(
        tier_filter=req.tier,
        operator=req.operator,
        notes=req.notes,
    )

    # Run all scenarios
    results, summary = run_validation(scenarios)

    # Persist individual runs
    for r in results:
        record = ValidationRunRecord(
            scenario_id=r.scenario_id,
            scenario_name=r.scenario_name,
            tier=r.tier,
            timestamp_utc=r.timestamp_utc,
            expected_decision=r.expected_decision,
            actual_decision=r.actual_decision,
            expected_rules_any=r.expected_rules_any,
            actual_rules=r.actual_rules,
            expected_export_allowed=r.expected_export_allowed,
            actual_export_allowed=r.actual_export_allowed,
            decision_match=r.decision_match,
            rules_match=r.rules_match,
            export_match=r.export_match,
            passed=r.passed,
            feasibility_input=r.feasibility_input,
            feasibility_result=r.feasibility_result,
            notes=r.notes,
            session_id=session.session_id,
        )
        run_id = write_validation_run(record)
        session.run_ids.append(run_id)

    # Update session with summary
    session.completed_at_utc = datetime.now(timezone.utc).isoformat()
    session.total = summary["total"]
    session.passed = summary["passed"]
    session.failed = summary["failed"]
    session.pass_rate = summary["pass_rate"]
    session.by_tier = summary.get("by_tier", {})
    session.red_leaks = summary.get("red_leaks", 0)
    session.red_leak_scenarios = summary.get("red_leak_scenarios", [])
    session.release_authorized = summary.get("release_authorized", False)

    # Persist session
    write_validation_session(session)

    return {
        "session_id": session.session_id,
        "total": session.total,
        "passed": session.passed,
        "failed": session.failed,
        "pass_rate": session.pass_rate,
        "by_tier": session.by_tier,
        "red_leaks": session.red_leaks,
        "red_leak_scenarios": session.red_leak_scenarios,
        "release_authorized": session.release_authorized,
        "run_ids": session.run_ids,
    }


@router.post("/log")
async def log_result(req: LogResultRequest) -> Dict[str, Any]:
    """
    Log a manual validation result (for UI-driven testing).
    """
    record = ValidationRunRecord(
        scenario_id=req.scenario_id,
        scenario_name=req.scenario_name,
        tier=req.tier,
        expected_decision=req.expected_decision,
        actual_decision=req.actual_decision,
        expected_rules_any=req.expected_rules_any,
        actual_rules=req.actual_rules,
        expected_export_allowed=req.expected_export_allowed,
        actual_export_allowed=req.actual_export_allowed,
        decision_match=req.decision_match,
        rules_match=req.rules_match,
        export_match=req.export_match,
        passed=req.passed,
        notes=req.notes,
        session_id=req.session_id,
    )

    run_id = write_validation_run(record)

    return {
        "run_id": run_id,
        "logged": True,
    }


@router.get("/summary")
async def get_summary() -> ValidationSummaryResponse:
    """
    Get summary of latest validation status.
    """
    latest = get_latest_session_summary()

    if not latest:
        return ValidationSummaryResponse()

    return ValidationSummaryResponse(
        latest_session_id=latest.get("session_id"),
        latest_timestamp=latest.get("completed_at_utc") or latest.get("started_at_utc"),
        total=latest.get("total", 0),
        passed=latest.get("passed", 0),
        failed=latest.get("failed", 0),
        pass_rate=latest.get("pass_rate", "N/A"),
        red_leaks=latest.get("red_leaks", 0),
        release_authorized=latest.get("release_authorized", False),
    )


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """
    List validation sessions.
    """
    sessions = list_validation_sessions(limit=limit, offset=offset)

    return {
        "total": len(sessions),
        "sessions": [s.model_dump() for s in sessions],
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get a validation session by ID.
    """
    session = get_validation_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return session.model_dump()


@router.get("/runs")
async def list_runs_endpoint(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """
    List validation runs.
    """
    runs = list_validation_runs(
        date=date,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )

    return {
        "total": len(runs),
        "runs": [r.model_dump() for r in runs],
    }


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> Dict[str, Any]:
    """
    Get a validation run by ID.
    """
    run = get_validation_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    return run.model_dump()
