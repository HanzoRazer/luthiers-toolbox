"""
AI Context Adapter - Read-Only API Routes

All endpoints are GET only. No POST, PUT, PATCH, DELETE.
These endpoints provide read-only context snapshots for AI consumption.

Prefix: /api/ai/context
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .schemas import (
    Actor,
    ActorKind,
    ActorRole,
    ContextRequest,
    ForbiddenCategory,
    RedactionLevel,
    RedactionPolicy,
    Scope,
    generate_request_id,
)
from .assembler import default_assembler


router = APIRouter(prefix="/api/ai/context", tags=["AI Context"])


# -------------------------
# Request/Response Models
# -------------------------

class ContextEnvelopeResponse(BaseModel):
    """Response containing the full context envelope."""
    envelope: Dict[str, Any] = Field(..., description="The context envelope")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Any warnings generated")


class RunSummaryResponse(BaseModel):
    """Response containing run summary context."""
    source_id: str
    kind: str = "run_summary"
    content_type: str = "application/json"
    payload: Dict[str, Any]


class DesignIntentResponse(BaseModel):
    """Response containing design intent context."""
    source_id: str
    kind: str = "design_intent"
    content_type: str = "application/json"
    payload: Dict[str, Any]


class GovernanceNotesResponse(BaseModel):
    """Response containing governance notes."""
    sources: List[Dict[str, Any]]


class DocsExcerptResponse(BaseModel):
    """Response containing documentation excerpts."""
    sources: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "v1"
    providers: List[str]
    redaction_mode: str = "read_only"


# -------------------------
# Endpoints
# -------------------------

@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """
    Health check for AI Context Adapter.
    
    Returns adapter version and available providers.
    """
    return HealthResponse(
        status="ok",
        version="v1",
        providers=[
            "run_summary",
            "design_intent",
            "governance_notes",
            "docs_excerpt",
            "ui_state_hint",
        ],
        redaction_mode="read_only",
    )


@router.get("/envelope", response_model=ContextEnvelopeResponse)
def get_context_envelope(
    intent: str = Query(..., description="What the AI should help with"),
    run_id: Optional[str] = Query(None, description="RMOS run ID"),
    pattern_id: Optional[str] = Query(None, description="Pattern/design ID"),
    session_id: Optional[str] = Query(None, description="Workflow session ID"),
    project_id: Optional[str] = Query(None, description="Project ID"),
    actor_role: str = Query("builder", description="Actor role (builder, operator, admin, viewer)"),
    redaction_level: str = Query("strict", description="Redaction level (strict, balanced)"),
) -> ContextEnvelopeResponse:
    """
    Get a complete context envelope for AI consumption.
    
    This endpoint assembles context from all relevant providers,
    applies redaction, and returns a complete envelope.
    
    **Read-only**: This endpoint only reads data, never modifies.
    """
    # Build request
    req = ContextRequest(
        request_id=generate_request_id(),
        intent=intent,
        actor=Actor(
            kind=ActorKind.HUMAN,
            role=ActorRole(actor_role),
            auth_context="toolbox_session",
        ),
        scope=Scope(
            run_id=run_id,
            pattern_id=pattern_id,
            session_id=session_id,
            project_id=project_id,
        ),
    )
    
    # Build policy
    policy = RedactionPolicy(
        redaction_level=RedactionLevel(redaction_level),
    )
    
    # Assemble context
    result = default_assembler.build(req, policy)
    
    return ContextEnvelopeResponse(
        envelope=result.envelope.to_dict(),
        warnings=[w.to_dict() for w in result.warnings],
    )


@router.get("/run_summary", response_model=RunSummaryResponse)
def get_run_summary(
    run_id: str = Query(..., description="RMOS run ID"),
    redaction_level: str = Query("strict", description="Redaction level"),
) -> RunSummaryResponse:
    """
    Get run summary context for a specific run.
    
    Returns status, candidate counts, blockers, and feasibility summary.
    Does NOT include toolpaths or manufacturing details.
    
    **Read-only**: This endpoint only reads data, never modifies.
    """
    from .providers import run_summary_provider
    
    req = ContextRequest(
        request_id=generate_request_id(),
        intent="Get run summary",
        actor=Actor(
            kind=ActorKind.HUMAN,
            role=ActorRole.BUILDER,
            auth_context="toolbox_session",
        ),
        scope=Scope(run_id=run_id),
    )
    
    policy = RedactionPolicy(
        redaction_level=RedactionLevel(redaction_level),
    )
    
    sources, _, warnings = run_summary_provider.provide(req, policy)
    
    if not sources:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    
    source = sources[0]
    return RunSummaryResponse(
        source_id=source.source_id,
        kind=source.kind.value,
        content_type=source.content_type,
        payload=source.payload,
    )


@router.get("/design_intent", response_model=DesignIntentResponse)
def get_design_intent(
    pattern_id: str = Query(..., description="Pattern/design ID"),
    redaction_level: str = Query("strict", description="Redaction level"),
) -> DesignIntentResponse:
    """
    Get design intent context for a specific pattern.
    
    Returns pattern parameters, visual metadata, and design constraints.
    Does NOT include manufacturing parameters.
    
    **Read-only**: This endpoint only reads data, never modifies.
    """
    from .providers import design_intent_provider
    
    req = ContextRequest(
        request_id=generate_request_id(),
        intent="Get design intent",
        actor=Actor(
            kind=ActorKind.HUMAN,
            role=ActorRole.BUILDER,
            auth_context="toolbox_session",
        ),
        scope=Scope(pattern_id=pattern_id),
    )
    
    policy = RedactionPolicy(
        redaction_level=RedactionLevel(redaction_level),
    )
    
    sources, _, warnings = design_intent_provider.provide(req, policy)
    
    if not sources:
        raise HTTPException(status_code=404, detail=f"Pattern '{pattern_id}' not found")
    
    source = sources[0]
    return DesignIntentResponse(
        source_id=source.source_id,
        kind=source.kind.value,
        content_type=source.content_type,
        payload=source.payload,
    )


@router.get("/governance_notes", response_model=GovernanceNotesResponse)
def get_governance_notes(
    topic: Optional[str] = Query(None, description="Specific topic (feasibility, boundary, etc.)"),
    intent: str = Query("general governance help", description="What the user needs help with"),
) -> GovernanceNotesResponse:
    """
    Get governance notes explaining why something is blocked.
    
    Returns relevant governance rules, typical causes, and suggested actions.
    
    **Read-only**: This endpoint only provides documentation, never modifies.
    """
    from .providers import governance_notes_provider
    
    # Incorporate topic into intent if provided
    full_intent = f"{intent} {topic}" if topic else intent
    
    req = ContextRequest(
        request_id=generate_request_id(),
        intent=full_intent,
        actor=Actor(
            kind=ActorKind.HUMAN,
            role=ActorRole.BUILDER,
            auth_context="toolbox_session",
        ),
        scope=Scope(),
    )
    
    policy = RedactionPolicy()
    
    sources, _, warnings = governance_notes_provider.provide(req, policy)
    
    return GovernanceNotesResponse(
        sources=[s.to_dict() for s in sources],
    )


@router.get("/docs_excerpt", response_model=DocsExcerptResponse)
def get_docs_excerpt(
    intent: str = Query(..., description="What the user needs help with"),
    doc_id: Optional[str] = Query(None, description="Specific doc path (optional)"),
    anchor: Optional[str] = Query(None, description="Section anchor (optional)"),
) -> DocsExcerptResponse:
    """
    Get relevant documentation excerpts.
    
    Returns short, focused excerpts from relevant documentation files.
    
    **Read-only**: This endpoint only reads docs, never modifies.
    """
    from .providers import docs_excerpt_provider
    
    # Incorporate doc_id into intent if provided
    full_intent = f"{intent} {doc_id}" if doc_id else intent
    
    req = ContextRequest(
        request_id=generate_request_id(),
        intent=full_intent,
        actor=Actor(
            kind=ActorKind.HUMAN,
            role=ActorRole.BUILDER,
            auth_context="toolbox_session",
        ),
        scope=Scope(),
    )
    
    policy = RedactionPolicy()
    
    sources, _, warnings = docs_excerpt_provider.provide(req, policy)
    
    return DocsExcerptResponse(
        sources=[s.to_dict() for s in sources],
    )
