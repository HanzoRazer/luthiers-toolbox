from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
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
    DRAFT = "draft"
    CONTEXT_READY = "context_ready"

    FEASIBILITY_REQUESTED = "feasibility_requested"
    FEASIBILITY_READY = "feasibility_ready"

    DESIGN_REVISION_REQUIRED = "design_revision_required"
    APPROVED = "approved"

    TOOLPATHS_REQUESTED = "toolpaths_requested"
    TOOLPATHS_READY = "toolpaths_ready"

    REJECTED = "rejected"
    ARCHIVED = "archived"


class RiskBucket(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"


class ActorRole(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    OPERATOR = "operator"


class RunStatus(str, Enum):
    OK = "OK"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Run Artifact Contracts (maps to RUN_ARTIFACT_* docs)
# ---------------------------------------------------------------------------

class RunArtifactRef(BaseModel):
    """
    Minimal reference to a persisted run artifact.
    The artifact storage layer decides filesystem/db layout.
    """
    artifact_id: str
    kind: str  # "feasibility" | "toolpaths" | "bom" | ...
    status: RunStatus
    created_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    meta: Dict[str, Any] = Field(default_factory=dict)


class FeasibilityResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    risk_bucket: RiskBucket
    warnings: List[str] = Field(default_factory=list)

    # Required for diff viewer + audit
    meta: Dict[str, Any] = Field(default_factory=dict)
    # EXPECTED meta keys (enforced by guardrails later):
    # - feasibility_hash
    # - policy_version
    # - calculator_versions (dict)
    # - design_hash
    # - context_hash
    # - tool_id/material_id/machine_id
    # - source: "server_recompute" | "server_direct" | "client_ignored"


class ToolpathPlanRef(BaseModel):
    plan_id: str
    meta: Dict[str, Any] = Field(default_factory=dict)
    # EXPECTED meta keys:
    # - toolpath_hash
    # - plan_summary
    # - design_hash/context_hash
    # - policy_version/calculator_versions


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

    After repo-wide requirements:
      - Every feasibility/toolpaths attempt MUST yield an artifact
      - Toolpaths MUST enforce server-side feasibility recompute
      - Hashes/versions MUST be captured for diffing and indexing
    """
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: WorkflowMode
    state: WorkflowState = WorkflowState.DRAFT

    # Canonical inputs (swap Any to RosetteParamSpec / RmosContext later)
    design: Optional[Any] = None
    context: Optional[Any] = None

    # Latest deterministic results
    feasibility: Optional[FeasibilityResult] = None
    toolpaths: Optional[ToolpathPlanRef] = None
    approval: Optional[WorkflowApproval] = None

    # Run artifact refs (required for UI + Index API + Diff)
    last_feasibility_artifact: Optional[RunArtifactRef] = None
    last_toolpaths_artifact: Optional[RunArtifactRef] = None

    # Governance knobs
    allow_red_override: bool = False
    treat_unknown_as_red: bool = True
    require_explicit_approval: bool = True
    min_score_to_approve: float = 70.0

    # Server-side enforcement toggles (should be True in production)
    require_server_side_feasibility_for_toolpaths: bool = True

    # Candidate loops (AI/constraint-first)
    max_candidate_attempts: int = 50
    candidate_attempt_count: int = 0

    # Audit log
    events: List[WorkflowEvent] = Field(default_factory=list)

    # Index metadata (required for artifact indexing/query)
    # Populate from context builder: tool_id/material_id/machine_id/etc.
    index_meta: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class WorkflowTransitionError(RuntimeError):
    pass


class GovernanceError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Transition table
# ---------------------------------------------------------------------------

TransitionKey = Tuple[WorkflowState, str]

_ALLOWED: Dict[TransitionKey, WorkflowState] = {
    (WorkflowState.DRAFT, "set_design"): WorkflowState.DRAFT,
    (WorkflowState.DRAFT, "set_context"): WorkflowState.CONTEXT_READY,

    (WorkflowState.CONTEXT_READY, "request_feasibility"): WorkflowState.FEASIBILITY_REQUESTED,
    (WorkflowState.FEASIBILITY_REQUESTED, "store_feasibility"): WorkflowState.FEASIBILITY_READY,

    (WorkflowState.FEASIBILITY_READY, "require_revision"): WorkflowState.DESIGN_REVISION_REQUIRED,
    (WorkflowState.FEASIBILITY_READY, "approve"): WorkflowState.APPROVED,
    (WorkflowState.FEASIBILITY_READY, "reject"): WorkflowState.REJECTED,

    (WorkflowState.DESIGN_REVISION_REQUIRED, "set_design"): WorkflowState.CONTEXT_READY,

    (WorkflowState.APPROVED, "request_toolpaths"): WorkflowState.TOOLPATHS_REQUESTED,
    (WorkflowState.TOOLPATHS_REQUESTED, "store_toolpaths"): WorkflowState.TOOLPATHS_READY,

    (WorkflowState.TOOLPATHS_READY, "archive"): WorkflowState.ARCHIVED,
    (WorkflowState.REJECTED, "archive"): WorkflowState.ARCHIVED,
}


def _assert_can(session: WorkflowSession, action: str) -> WorkflowState:
    key = (session.state, action)
    if key not in _ALLOWED:
        raise WorkflowTransitionError(f"Illegal transition: {session.state} --{action}--> ?")
    return _ALLOWED[key]


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


# ---------------------------------------------------------------------------
# Artifact hooks (call out to persistence layer from routers/services)
# ---------------------------------------------------------------------------

def attach_feasibility_artifact(session: WorkflowSession, artifact: RunArtifactRef) -> None:
    session.last_feasibility_artifact = artifact


def attach_toolpaths_artifact(session: WorkflowSession, artifact: RunArtifactRef) -> None:
    session.last_toolpaths_artifact = artifact


# ---------------------------------------------------------------------------
# Public API (state changes)
# ---------------------------------------------------------------------------

def new_session(mode: WorkflowMode, *, index_meta: Optional[Dict[str, Any]] = None) -> WorkflowSession:
    s = WorkflowSession(mode=mode, index_meta=index_meta or {})
    _emit(
        s,
        actor=ActorRole.SYSTEM,
        action="create",
        from_state=WorkflowState.DRAFT,
        to_state=WorkflowState.DRAFT,
        summary=f"Workflow session created (mode={mode.value})",
        details={"mode": mode.value},
    )
    return s


def set_design(session: WorkflowSession, design: Any, *, actor: ActorRole) -> WorkflowSession:
    _assert_can(session, "set_design")
    prev = session.state

    session.design = design
    # Clear downstream
    session.feasibility = None
    session.toolpaths = None
    session.approval = None
    session.last_feasibility_artifact = None
    session.last_toolpaths_artifact = None

    to_state = WorkflowState.CONTEXT_READY if prev == WorkflowState.DESIGN_REVISION_REQUIRED else prev
    _emit(session, actor=actor, action="set_design", from_state=prev, to_state=to_state, summary="Design updated")
    return session


def set_context(session: WorkflowSession, context: Any, *, actor: ActorRole) -> WorkflowSession:
    to_state = _assert_can(session, "set_context")
    prev = session.state

    session.context = context
    # Clear downstream
    session.feasibility = None
    session.toolpaths = None
    session.approval = None
    session.last_feasibility_artifact = None
    session.last_toolpaths_artifact = None

    _emit(session, actor=actor, action="set_context", from_state=prev, to_state=to_state, summary="Context set/normalized")
    return session


def request_feasibility(session: WorkflowSession, *, actor: ActorRole) -> WorkflowSession:
    if session.design is None:
        raise WorkflowTransitionError("Cannot request feasibility: design is missing")
    if session.context is None:
        raise WorkflowTransitionError("Cannot request feasibility: context is missing")

    to_state = _assert_can(session, "request_feasibility")
    prev = session.state
    _emit(session, actor=actor, action="request_feasibility", from_state=prev, to_state=to_state, summary="Feasibility requested")
    return session


def store_feasibility(session: WorkflowSession, result: FeasibilityResult, *, actor: ActorRole) -> WorkflowSession:
    to_state = _assert_can(session, "store_feasibility")
    prev = session.state

    session.feasibility = result

    # Governance: UNKNOWN treated as RED if configured
    rb = result.risk_bucket
    if rb == RiskBucket.UNKNOWN and session.treat_unknown_as_red:
        rb = RiskBucket.RED
        session.feasibility.risk_bucket = RiskBucket.RED
        session.feasibility.warnings.append("Risk bucket UNKNOWN treated as RED by policy.")

    # Governance: hard stop on RED unless override allowed
    if rb == RiskBucket.RED and not session.allow_red_override:
        _emit(
            session,
            actor=actor,
            action="store_feasibility",
            from_state=prev,
            to_state=WorkflowState.REJECTED,
            summary="Feasibility stored (RED) — hard stop",
            details={"risk_bucket": rb.value, "score": result.score, "warnings": result.warnings},
        )
        return session

    _emit(
        session,
        actor=actor,
        action="store_feasibility",
        from_state=prev,
        to_state=to_state,
        summary="Feasibility stored",
        details={"risk_bucket": rb.value, "score": result.score, "warnings": result.warnings},
    )
    return session


def approve(session: WorkflowSession, *, actor: ActorRole, note: Optional[str] = None) -> WorkflowSession:
    if session.feasibility is None:
        raise WorkflowTransitionError("Cannot approve: feasibility is missing")

    rb = session.feasibility.risk_bucket
    score = session.feasibility.score

    if rb == RiskBucket.RED and not session.allow_red_override:
        raise GovernanceError("Approval blocked: RED and overrides disabled")

    if score < session.min_score_to_approve and rb != RiskBucket.GREEN:
        raise GovernanceError(f"Approval blocked: score {score} below min {session.min_score_to_approve} (risk={rb.value})")

    to_state = _assert_can(session, "approve")
    prev = session.state

    session.approval = WorkflowApproval(approved=True, approved_by=actor, note=note)
    _emit(
        session,
        actor=actor,
        action="approve",
        from_state=prev,
        to_state=to_state,
        summary="Approved for toolpath generation",
        details={"risk_bucket": rb.value, "score": score, "note": note or ""},
    )
    return session


def reject(session: WorkflowSession, *, actor: ActorRole, reason: str) -> WorkflowSession:
    to_state = _assert_can(session, "reject")
    prev = session.state
    session.approval = WorkflowApproval(approved=False, approved_by=actor, note=reason)
    _emit(session, actor=actor, action="reject", from_state=prev, to_state=to_state, summary="Rejected", details={"reason": reason})
    return session


def request_toolpaths(session: WorkflowSession, *, actor: ActorRole) -> WorkflowSession:
    """
    Repo-wide requirement mapping:
      - Toolpaths MUST be gated by feasibility
      - Toolpaths MUST require SERVER-SIDE feasibility recompute (production)
      - Any block MUST still emit an artifact (done in router/service layer via attach_toolpaths_artifact)
    """
    if session.feasibility is None:
        raise WorkflowTransitionError("Cannot request toolpaths: feasibility is missing")

    if session.require_explicit_approval and session.state != WorkflowState.APPROVED:
        raise GovernanceError("Toolpaths blocked: explicit approval required")

    # Hard block: RED unless override enabled
    if session.feasibility.risk_bucket == RiskBucket.RED and not session.allow_red_override:
        raise GovernanceError("Toolpaths blocked: feasibility RED and overrides disabled")

    # Server-side enforcement: require feasibility meta to indicate server recompute
    if session.require_server_side_feasibility_for_toolpaths:
        src = (session.feasibility.meta or {}).get("source")
        if src not in ("server_recompute", "server_direct"):
            raise GovernanceError(
                "Toolpaths blocked: server-side feasibility enforcement enabled; "
                "feasibility source is not server_*"
            )

    to_state = _assert_can(session, "request_toolpaths")
    prev = session.state
    _emit(
        session,
        actor=actor,
        action="request_toolpaths",
        from_state=prev,
        to_state=to_state,
        summary="Toolpaths requested",
        details={"risk_bucket": session.feasibility.risk_bucket.value, "score": session.feasibility.score},
    )
    return session


def store_toolpaths(session: WorkflowSession, plan_ref: ToolpathPlanRef, *, actor: ActorRole) -> WorkflowSession:
    to_state = _assert_can(session, "store_toolpaths")
    prev = session.state

    session.toolpaths = plan_ref
    _emit(
        session,
        actor=actor,
        action="store_toolpaths",
        from_state=prev,
        to_state=to_state,
        summary="Toolpaths stored/linked",
        details={"plan_id": plan_ref.plan_id, "toolpath_hash": plan_ref.meta.get("toolpath_hash")},
    )
    return session


def require_revision(session: WorkflowSession, *, actor: ActorRole, reason: str) -> WorkflowSession:
    if session.feasibility is None:
        raise WorkflowTransitionError("Cannot require revision: feasibility missing")

    to_state = _assert_can(session, "require_revision")
    prev = session.state
    _emit(
        session,
        actor=actor,
        action="require_revision",
        from_state=prev,
        to_state=to_state,
        summary="Design revision required",
        details={"reason": reason, "risk_bucket": session.feasibility.risk_bucket.value, "score": session.feasibility.score},
    )
    return session


def archive(session: WorkflowSession, *, actor: ActorRole, note: Optional[str] = None) -> WorkflowSession:
    to_state = _assert_can(session, "archive")
    prev = session.state
    _emit(session, actor=actor, action="archive", from_state=prev, to_state=to_state, summary="Archived", details={"note": note or ""})
    return session


# ---------------------------------------------------------------------------
# Diff-viewer friendly snapshot (maps to RUN_DIFF_VIEWER.md)
# ---------------------------------------------------------------------------

class RunComparableSnapshot(BaseModel):
    """
    Stable, minimal snapshot used by diff tooling.
    Prefer hashes + versions rather than huge payloads.
    """
    session_id: str
    mode: WorkflowMode
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None

    design_hash: Optional[str] = None
    context_hash: Optional[str] = None

    feasibility_hash: Optional[str] = None
    risk_bucket: Optional[RiskBucket] = None
    score: Optional[float] = None
    policy_version: Optional[str] = None
    calculator_versions: Dict[str, str] = Field(default_factory=dict)

    toolpath_hash: Optional[str] = None

    feasibility_artifact_id: Optional[str] = None
    toolpaths_artifact_id: Optional[str] = None


def to_comparable_snapshot(session: WorkflowSession) -> RunComparableSnapshot:
    tool_id = session.index_meta.get("tool_id")
    material_id = session.index_meta.get("material_id")
    machine_id = session.index_meta.get("machine_id")

    fmeta = (session.feasibility.meta if session.feasibility else {}) or {}
    tmeta = (session.toolpaths.meta if session.toolpaths else {}) or {}

    return RunComparableSnapshot(
        session_id=session.session_id,
        mode=session.mode,
        tool_id=tool_id,
        material_id=material_id,
        machine_id=machine_id,
        design_hash=fmeta.get("design_hash") or session.index_meta.get("design_hash"),
        context_hash=fmeta.get("context_hash") or session.index_meta.get("context_hash"),
        feasibility_hash=fmeta.get("feasibility_hash"),
        risk_bucket=session.feasibility.risk_bucket if session.feasibility else None,
        score=session.feasibility.score if session.feasibility else None,
        policy_version=fmeta.get("policy_version"),
        calculator_versions=fmeta.get("calculator_versions") or {},
        toolpath_hash=tmeta.get("toolpath_hash"),
        feasibility_artifact_id=(session.last_feasibility_artifact.artifact_id if session.last_feasibility_artifact else None),
        toolpaths_artifact_id=(session.last_toolpaths_artifact.artifact_id if session.last_toolpaths_artifact else None),
    )