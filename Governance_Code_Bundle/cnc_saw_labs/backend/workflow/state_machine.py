from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums / Types
# ---------------------------------------------------------------------------

class WorkflowMode(str, Enum):
    DESIGN_FIRST = "design_first"
    CONSTRAINT_FIRST = "constraint_first"
    AI_ASSISTED = "ai_assisted"


class WorkflowState(str, Enum):
    DRAFT = "draft"                           # Design exists, not yet scored
    CONTEXT_READY = "context_ready"           # Context validated/normalized
    FEASIBILITY_REQUESTED = "feasibility_requested"
    FEASIBILITY_READY = "feasibility_ready"   # Result stored
    DESIGN_REVISION_REQUIRED = "design_revision_required"
    APPROVED = "approved"                     # Explicit approval gate
    TOOLPATHS_REQUESTED = "toolpaths_requested"
    TOOLPATHS_READY = "toolpaths_ready"
    REJECTED = "rejected"                     # Hard stop (RED or explicit reject)
    ARCHIVED = "archived"


class RiskBucket(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class ActorRole(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    OPERATOR = "operator"


# ---------------------------------------------------------------------------
# Core Data Contracts (minimal, keep RMOS canonical clean)
# These are intentionally "thin" so this module can live without importing RMOS.
# You can replace Any with real RosetteParamSpec / RmosContext later.
# ---------------------------------------------------------------------------

class FeasibilityResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    risk_bucket: RiskBucket
    warnings: List[str] = Field(default_factory=list)
    efficiency: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    estimated_cut_time_s: Optional[float] = Field(default=None, ge=0.0)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ToolpathPlanRef(BaseModel):
    """Reference to a generated toolpath plan (in-memory, db id, or artifact id)."""
    plan_id: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class WorkflowApproval(BaseModel):
    approved: bool
    approved_by: ActorRole
    note: Optional[str] = None
    ts_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowEvent(BaseModel):
    ts_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: ActorRole
    action: str
    from_state: WorkflowState
    to_state: WorkflowState
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkflowSession(BaseModel):
    """
    Authoritative workflow session record.
    Store this in DB later; for now it's a serializable state object.
    """
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: WorkflowMode

    state: WorkflowState = WorkflowState.DRAFT

    # Canonical inputs (keep as Any here; swap to RosetteParamSpec/RmosContext later)
    design: Optional[Any] = None
    context: Optional[Any] = None

    # Latest feasibility/toolpath artifacts
    feasibility: Optional[FeasibilityResult] = None
    toolpaths: Optional[ToolpathPlanRef] = None

    # Governance knobs (can be per-session)
    allow_red_override: bool = False  # default hard-stop
    require_explicit_approval: bool = True  # recommended for safety
    min_score_to_approve: float = 70.0  # tune as needed

    # AI / constraint-first loop controls
    max_candidate_attempts: int = 50
    candidate_attempt_count: int = 0

    # Audit log
    events: List[WorkflowEvent] = Field(default_factory=list)

    # Free-form metadata
    meta: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class WorkflowTransitionError(RuntimeError):
    pass


class GovernanceError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# State Machine
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TransitionRule:
    """A simple rule for transitions; use guards for governance checks."""
    from_state: WorkflowState
    action: str
    to_state: WorkflowState


# Allowed transitions (minimal but complete for A/B/C workflows)
TRANSITIONS: Tuple[TransitionRule, ...] = (
    TransitionRule(WorkflowState.DRAFT, "set_design", WorkflowState.DRAFT),
    TransitionRule(WorkflowState.DRAFT, "set_context", WorkflowState.CONTEXT_READY),

    TransitionRule(WorkflowState.CONTEXT_READY, "request_feasibility", WorkflowState.FEASIBILITY_REQUESTED),
    TransitionRule(WorkflowState.FEASIBILITY_REQUESTED, "store_feasibility", WorkflowState.FEASIBILITY_READY),

    TransitionRule(WorkflowState.FEASIBILITY_READY, "require_revision", WorkflowState.DESIGN_REVISION_REQUIRED),
    TransitionRule(WorkflowState.FEASIBILITY_READY, "approve", WorkflowState.APPROVED),
    TransitionRule(WorkflowState.FEASIBILITY_READY, "reject", WorkflowState.REJECTED),

    TransitionRule(WorkflowState.DESIGN_REVISION_REQUIRED, "set_design", WorkflowState.CONTEXT_READY),

    TransitionRule(WorkflowState.APPROVED, "request_toolpaths", WorkflowState.TOOLPATHS_REQUESTED),
    TransitionRule(WorkflowState.TOOLPATHS_REQUESTED, "store_toolpaths", WorkflowState.TOOLPATHS_READY),

    TransitionRule(WorkflowState.TOOLPATHS_READY, "archive", WorkflowState.ARCHIVED),
    TransitionRule(WorkflowState.REJECTED, "archive", WorkflowState.ARCHIVED),
)

# Quick lookup
_ALLOWED = {(t.from_state, t.action): t.to_state for t in TRANSITIONS}


def _emit(session: WorkflowSession, *, actor: ActorRole, action: str,
          from_state: WorkflowState, to_state: WorkflowState,
          summary: str, details: Optional[Dict[str, Any]] = None) -> None:
    session.events.append(
        WorkflowEvent(
            actor=actor,
            action=action,
            from_state=from_state,
            to_state=to_state,
            summary=summary,
            details=details or {},
        )
    )
    session.state = to_state


def _assert_can(session: WorkflowSession, action: str) -> WorkflowState:
    key = (session.state, action)
    if key not in _ALLOWED:
        raise WorkflowTransitionError(f"Illegal transition: {session.state} --{action}--> ?")
    return _ALLOWED[key]


# ---------------------------------------------------------------------------
# Public API (the only way the app should move workflow forward)
# ---------------------------------------------------------------------------

def new_session(mode: WorkflowMode, *, require_explicit_approval: bool = True,
                min_score_to_approve: float = 70.0,
                allow_red_override: bool = False,
                meta: Optional[Dict[str, Any]] = None) -> WorkflowSession:
    s = WorkflowSession(
        mode=mode,
        require_explicit_approval=require_explicit_approval,
        min_score_to_approve=min_score_to_approve,
        allow_red_override=allow_red_override,
        meta=meta or {},
    )
    _emit(
        s,
        actor=ActorRole.SYSTEM,
        action="create",
        from_state=WorkflowState.DRAFT,
        to_state=WorkflowState.DRAFT,
        summary=f"Workflow session created in mode={mode.value}",
        details={"mode": mode.value},
    )
    return s


def set_design(session: WorkflowSession, design: Any, *, actor: ActorRole) -> WorkflowSession:
    to_state = _assert_can(session, "set_design")
    session.design = design
    # If we were in revision-required, rule routes to CONTEXT_READY; otherwise stays DRAFT.
    if session.state == WorkflowState.DESIGN_REVISION_REQUIRED:
        # Force back to CONTEXT_READY to re-run feasibility with same context
        to_state = WorkflowState.CONTEXT_READY
    _emit(
        session,
        actor=actor,
        action="set_design",
        from_state=session.state,
        to_state=to_state,
        summary="Design updated",
    )
    # Clear downstream artifacts
    session.feasibility = None
    session.toolpaths = None
    return session


def set_context(session: WorkflowSession, context: Any, *, actor: ActorRole) -> WorkflowSession:
    to_state = _assert_can(session, "set_context")
    session.context = context
    _emit(
        session,
        actor=actor,
        action="set_context",
        from_state=session.state,
        to_state=to_state,
        summary="Context set/normalized",
    )
    # Clear downstream artifacts
    session.feasibility = None
    session.toolpaths = None
    return session


def request_feasibility(session: WorkflowSession, *, actor: ActorRole) -> WorkflowSession:
    if session.design is None:
        raise WorkflowTransitionError("Cannot request feasibility: design is missing")
    if session.context is None:
        raise WorkflowTransitionError("Cannot request feasibility: context is missing")

    to_state = _assert_can(session, "request_feasibility")
    _emit(
        session,
        actor=actor,
        action="request_feasibility",
        from_state=session.state,
        to_state=to_state,
        summary="Feasibility requested",
    )
    return session


def store_feasibility(session: WorkflowSession, result: FeasibilityResult, *, actor: ActorRole) -> WorkflowSession:
    to_state = _assert_can(session, "store_feasibility")
    session.feasibility = result

    # Governance: hard stop on RED unless override allowed
    if result.risk_bucket == RiskBucket.RED and not session.allow_red_override:
        # Force REJECTED regardless of nominal transition target
        _emit(
            session,
            actor=actor,
            action="store_feasibility",
            from_state=session.state,
            to_state=WorkflowState.REJECTED,
            summary="Feasibility stored (RED) — hard stop",
            details={"risk_bucket": result.risk_bucket.value, "score": result.score, "warnings": result.warnings},
        )
        return session

    _emit(
        session,
        actor=actor,
        action="store_feasibility",
        from_state=session.state,
        to_state=to_state,
        summary="Feasibility stored",
        details={"risk_bucket": result.risk_bucket.value, "score": result.score, "warnings": result.warnings},
    )

    # Automatic next-step suggestion (state stays FEASIBILITY_READY; caller can decide)
    return session


def require_revision(session: WorkflowSession, *, actor: ActorRole, reason: str) -> WorkflowSession:
    if session.feasibility is None:
        raise WorkflowTransitionError("Cannot require revision: feasibility is missing")

    to_state = _assert_can(session, "require_revision")
    _emit(
        session,
        actor=actor,
        action="require_revision",
        from_state=session.state,
        to_state=to_state,
        summary="Design revision required",
        details={"reason": reason, "risk_bucket": session.feasibility.risk_bucket.value, "score": session.feasibility.score},
    )
    return session


def approve(session: WorkflowSession, *, actor: ActorRole, note: Optional[str] = None) -> WorkflowSession:
    if session.feasibility is None:
        raise WorkflowTransitionError("Cannot approve: feasibility is missing")

    # Governance checks
    fb = session.feasibility.risk_bucket
    score = session.feasibility.score

    if fb == RiskBucket.RED and not session.allow_red_override:
        raise GovernanceError("Approval blocked: RED and overrides are disabled")

    if score < session.min_score_to_approve and fb != RiskBucket.GREEN:
        # You can tune this policy; current stance: low score + not-green should not approve.
        raise GovernanceError(
            f"Approval blocked: score {score} below min {session.min_score_to_approve} (risk={fb.value})"
        )

    to_state = _assert_can(session, "approve")
    _emit(
        session,
        actor=actor,
        action="approve",
        from_state=session.state,
        to_state=to_state,
        summary="Session approved for toolpath generation",
        details={"note": note or "", "risk_bucket": fb.value, "score": score},
    )
    return session


def reject(session: WorkflowSession, *, actor: ActorRole, reason: str) -> WorkflowSession:
    to_state = _assert_can(session, "reject")
    _emit(
        session,
        actor=actor,
        action="reject",
        from_state=session.state,
        to_state=to_state,
        summary="Session rejected",
        details={"reason": reason},
    )
    return session


def request_toolpaths(session: WorkflowSession, *, actor: ActorRole) -> WorkflowSession:
    if session.feasibility is None:
        raise WorkflowTransitionError("Cannot request toolpaths: feasibility is missing")

    # Require approval unless explicitly disabled
    if session.require_explicit_approval and session.state != WorkflowState.APPROVED:
        raise GovernanceError("Toolpaths blocked: explicit approval required")

    # Extra governance: even with approval disabled, block RED unless override enabled
    if session.feasibility.risk_bucket == RiskBucket.RED and not session.allow_red_override:
        raise GovernanceError("Toolpaths blocked: feasibility is RED and overrides disabled")

    to_state = _assert_can(session, "request_toolpaths")
    _emit(
        session,
        actor=actor,
        action="request_toolpaths",
        from_state=session.state,
        to_state=to_state,
        summary="Toolpaths requested",
        details={"risk_bucket": session.feasibility.risk_bucket.value, "score": session.feasibility.score},
    )
    return session


def store_toolpaths(session: WorkflowSession, plan_ref: ToolpathPlanRef, *, actor: ActorRole) -> WorkflowSession:
    to_state = _assert_can(session, "store_toolpaths")
    session.toolpaths = plan_ref
    _emit(
        session,
        actor=actor,
        action="store_toolpaths",
        from_state=session.state,
        to_state=to_state,
        summary="Toolpaths stored/linked",
        details={"plan_id": plan_ref.plan_id},
    )
    return session


def archive(session: WorkflowSession, *, actor: ActorRole, note: Optional[str] = None) -> WorkflowSession:
    to_state = _assert_can(session, "archive")
    _emit(
        session,
        actor=actor,
        action="archive",
        from_state=session.state,
        to_state=to_state,
        summary="Session archived",
        details={"note": note or ""},
    )
    return session


# ---------------------------------------------------------------------------
# Convenience helpers for bidirectional workflows
# ---------------------------------------------------------------------------

def next_step_hint(session: WorkflowSession) -> str:
    """
    Small helper for UIs/clients: tells them what action is expected next.
    Not authoritative; state machine still enforces.
    """
    st = session.state
    if st == WorkflowState.DRAFT:
        return "Set context (and ensure design exists) to proceed."
    if st == WorkflowState.CONTEXT_READY:
        return "Request feasibility."
    if st == WorkflowState.FEASIBILITY_REQUESTED:
        return "Await feasibility result."
    if st == WorkflowState.FEASIBILITY_READY:
        if session.feasibility and session.feasibility.risk_bucket == RiskBucket.RED and not session.allow_red_override:
            return "Rejected (RED). Revise design or change constraints; then start a new session or require revision flow."
        return "Approve (or require revision) based on feasibility."
    if st == WorkflowState.DESIGN_REVISION_REQUIRED:
        return "Update design parameters and re-run feasibility."
    if st == WorkflowState.APPROVED:
        return "Request toolpaths."
    if st == WorkflowState.TOOLPATHS_REQUESTED:
        return "Await toolpath generation."
    if st == WorkflowState.TOOLPATHS_READY:
        return "Archive when complete."
    if st == WorkflowState.REJECTED:
        return "Archive or start a new session."
    if st == WorkflowState.ARCHIVED:
        return "Archived."
    return "Unknown."


def bump_candidate_attempt(session: WorkflowSession, *, actor: ActorRole) -> WorkflowSession:
    """
    For Constraint-First / AI-Assisted loops: count candidate attempts.
    If max exceeded, reject session (prevents runaway searches).
    """
    session.candidate_attempt_count += 1
    if session.candidate_attempt_count > session.max_candidate_attempts:
        # Hard stop (search budget exceeded)
        session.state = WorkflowState.REJECTED
        _emit(
            session,
            actor=actor,
            action="candidate_budget_exceeded",
            from_state=WorkflowState.FEASIBILITY_READY,
            to_state=WorkflowState.REJECTED,
            summary="Candidate search budget exceeded — rejected",
            details={"attempts": session.candidate_attempt_count, "max": session.max_candidate_attempts},
        )
    return session