"""
Translator Governance Continuity Graph Router

CAM Dev Order 7L: REST API for governance continuity replay infrastructure.

Endpoints:
  POST /api/cam/translators/governance-continuity/build
  GET  /api/cam/translators/governance-continuity
  GET  /api/cam/translators/governance-continuity/{continuity_graph_id}
  GET  /api/cam/translators/governance-continuity/by-translator/{translator_id}
  GET  /api/cam/translators/governance-continuity/{continuity_graph_id}/replay
  GET  /api/cam/translators/governance-continuity/policy

7L invariants:
  - replayable = true (always)
  - immutable = true (always)
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7L continuity graph remains immutable replay infrastructure only.
  No mutation, approval, execution, serializer invocation,
  or machine-output semantics.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.cam.translator_governance_continuity_graph import (
    TranslatorGovernanceContinuityGraph,
    GovernanceReplayResult,
    GovernanceContinuityGraphSummary,
    build_continuity_graph_for_translator,
    get_continuity_graph,
    list_continuity_graphs,
    list_continuity_graphs_for_translator,
    replay_governance_trace,
    to_summary,
    ContinuityGraphBuildError,
    MixedTranslatorError,
)
from app.cam.translator_governance_review_ledger import (
    list_review_ledger_entries_for_translator,
)


router = APIRouter(
    prefix="/api/cam/translators/governance-continuity",
    tags=["cam", "governance", "continuity"],
)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class BuildContinuityGraphRequest(BaseModel):
    """Request to build a continuity graph for a translator."""
    translator_id: str = Field(..., description="Translator identifier")
    persist_to_rmos: bool = Field(
        default=False,
        description="Whether to persist to RMOS"
    )


class ContinuityPolicyResponse(BaseModel):
    """7L continuity policy information."""
    replayable: bool = True
    immutable: bool = True
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    mutation_allowed: bool = False
    rebuild_from_scratch: bool = True
    per_translator_scope: bool = True
    dev_order: str = "7L"
    guardrail: str = (
        "7L continuity graph remains immutable replay infrastructure only. "
        "No mutation, approval, execution, serializer invocation, "
        "or machine-output semantics."
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/policy",
    response_model=ContinuityPolicyResponse,
    summary="Get 7L continuity policy",
)
def get_continuity_policy() -> ContinuityPolicyResponse:
    """
    Get the 7L governance continuity policy.

    Returns the invariants and guardrails enforced by this module.
    """
    return ContinuityPolicyResponse()


@router.post(
    "/build",
    response_model=TranslatorGovernanceContinuityGraph,
    status_code=201,
    summary="Build continuity graph for translator",
)
def build_continuity_graph_endpoint(
    request: BuildContinuityGraphRequest,
) -> TranslatorGovernanceContinuityGraph:
    """
    Build a governance continuity graph for a translator.

    Looks up ledger entries from the index and builds an immutable
    continuity graph for deterministic replay.

    Raises:
        400: If no ledger entries found or mixed translator_ids
        409: If graph already exists (duplicate)
    """
    try:
        graph = build_continuity_graph_for_translator(
            translator_id=request.translator_id,
            register=True,
        )

        if request.persist_to_rmos:
            from app.cam.translator_governance_continuity_graph import (
                persist_continuity_graph_to_rmos,
            )
            persist_continuity_graph_to_rmos(graph)

        return graph

    except ContinuityGraphBuildError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MixedTranslatorError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=List[GovernanceContinuityGraphSummary],
    summary="List all continuity graphs",
)
def list_continuity_graphs_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> List[GovernanceContinuityGraphSummary]:
    """
    List all governance continuity graphs.

    Returns summaries for pagination efficiency.
    """
    graphs = list_continuity_graphs()

    # Apply pagination
    paginated = graphs[offset:offset + limit]

    return [to_summary(g) for g in paginated]


@router.get(
    "/{continuity_graph_id}",
    response_model=TranslatorGovernanceContinuityGraph,
    summary="Get continuity graph by ID",
)
def get_continuity_graph_endpoint(
    continuity_graph_id: str,
) -> TranslatorGovernanceContinuityGraph:
    """
    Get a governance continuity graph by its ID.

    Raises:
        404: If graph not found
    """
    graph = get_continuity_graph(continuity_graph_id)
    if graph is None:
        raise HTTPException(
            status_code=404,
            detail=f"Continuity graph not found: {continuity_graph_id}"
        )
    return graph


@router.get(
    "/by-translator/{translator_id}",
    response_model=List[GovernanceContinuityGraphSummary],
    summary="List continuity graphs for translator",
)
def list_continuity_graphs_for_translator_endpoint(
    translator_id: str,
) -> List[GovernanceContinuityGraphSummary]:
    """
    List all governance continuity graphs for a specific translator.

    Returns summaries for efficiency.
    """
    graphs = list_continuity_graphs_for_translator(translator_id)
    return [to_summary(g) for g in graphs]


@router.get(
    "/{continuity_graph_id}/replay",
    response_model=GovernanceReplayResult,
    summary="Replay governance trace",
)
def replay_governance_trace_endpoint(
    continuity_graph_id: str,
) -> GovernanceReplayResult:
    """
    Perform deterministic governance replay traversal.

    Returns a structured GovernanceReplayResult with the ordered
    chain of ledger entries and integrity verification.

    Note:
        Replay means deterministic ancestry traversal only.
        NOT runtime replay, execution replay, or serializer replay.

    Raises:
        404: If graph not found
    """
    graph = get_continuity_graph(continuity_graph_id)
    if graph is None:
        raise HTTPException(
            status_code=404,
            detail=f"Continuity graph not found: {continuity_graph_id}"
        )

    # Get ledger entries for replay
    ledger_entries = list_review_ledger_entries_for_translator(
        graph.translator_id
    )

    return replay_governance_trace(graph, ledger_entries)


@router.get(
    "/by-translator/{translator_id}/build-or-get",
    response_model=TranslatorGovernanceContinuityGraph,
    summary="Build or get existing continuity graph",
)
def build_or_get_continuity_graph_endpoint(
    translator_id: str,
) -> TranslatorGovernanceContinuityGraph:
    """
    Build a new continuity graph or return existing one.

    If a graph with the same deterministic ID already exists,
    returns the existing graph (idempotent).

    Raises:
        400: If no ledger entries found for translator
    """
    try:
        graph = build_continuity_graph_for_translator(
            translator_id=translator_id,
            register=True,
        )
        return graph
    except ContinuityGraphBuildError as e:
        raise HTTPException(status_code=400, detail=str(e))
