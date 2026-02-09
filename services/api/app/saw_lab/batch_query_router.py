"""
Saw Lab Batch Query Router

Query/lookup endpoints extracted from batch_router.py:
  - Execution by decision (single + list)
  - Executions by label, plan, spec
  - Decisions by plan, spec
  - Op-toolpaths by decision, execution
  - Toolpaths by decision (lookup)
  - Batch links

Mounted at: /api/saw/batch
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.saw_lab.batch_router_schemas import (
    BatchExecutionByDecisionResponse,
    BatchExecutionsByDecisionResponse,
    BatchToolpathsByDecisionResponse,
)
from app.saw_lab.store import (
    get_artifact,
    query_decisions_by_plan,
    query_decisions_by_spec,
    query_executions_by_decision,
    query_executions_by_label,
    query_executions_by_plan,
    query_executions_by_spec,
    query_latest_by_label_and_session,
    query_op_toolpaths_by_decision,
    query_op_toolpaths_by_execution,
)

router = APIRouter(prefix="/api/saw/batch", tags=["saw", "batch"])


# ---------------------------------------------------------------------------
# Execution Lookup Endpoints
# ---------------------------------------------------------------------------


@router.get("/execution")
def get_execution_by_decision(
    batch_decision_artifact_id: str = Query(
        ..., description="Decision artifact ID to look up execution for"
    ),
) -> Dict[str, Any]:
    """
    Look up the latest execution artifact for a given decision.

    Returns the execution artifact with id, kind, status, and index_meta.
    Returns 404 if no execution exists for the decision.
    """
    executions = query_executions_by_decision(batch_decision_artifact_id)
    if not executions:
        raise HTTPException(
            status_code=404,
            detail=f"No execution artifact found for decision {batch_decision_artifact_id}",
        )

    # Return the latest execution (first in sorted list)
    latest = executions[0]
    payload = latest.get("payload", {})

    # Build index_meta with setdefault fallbacks for older artifacts
    index_meta = latest.get("index_meta") or {}
    index_meta.setdefault(
        "parent_batch_decision_artifact_id",
        payload.get("batch_decision_artifact_id") or batch_decision_artifact_id,
    )
    index_meta.setdefault("batch_label", payload.get("batch_label"))
    index_meta.setdefault("session_id", payload.get("session_id"))
    index_meta.setdefault("tool_kind", "saw_lab")
    index_meta.setdefault("kind_group", "batch")

    return {
        "artifact_id": latest.get("artifact_id"),
        "id": latest.get("artifact_id"),  # Alias for compatibility
        "kind": latest.get("kind", "saw_batch_execution"),
        "status": latest.get("status", "OK"),
        "created_utc": latest.get("created_utc"),
        "index_meta": index_meta,
    }


@router.get("/executions")
def list_executions_by_label(
    batch_label: str = Query(..., description="Batch label to filter by"),
    session_id: Optional[str] = Query(None, description="Optional session ID filter"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List execution artifacts by batch_label, newest first.

    Optionally filter by session_id.
    """
    executions = query_executions_by_label(batch_label, session_id)[:limit]

    results = []
    for ex in executions:
        payload = ex.get("payload", {})
        index_meta = ex.get("index_meta") or {}
        index_meta.setdefault("batch_label", payload.get("batch_label"))
        index_meta.setdefault("session_id", payload.get("session_id"))
        index_meta.setdefault("tool_kind", "saw_lab")
        index_meta.setdefault("kind_group", "batch")

        results.append(
            {
                "artifact_id": ex.get("artifact_id"),
                "id": ex.get("artifact_id"),
                "kind": ex.get("kind", "saw_batch_execution"),
                "status": ex.get("status", "OK"),
                "created_utc": ex.get("created_utc"),
                "index_meta": index_meta,
            }
        )

    return results


@router.get("/decisions/by-plan")
def list_decisions_by_plan(
    batch_plan_artifact_id: str = Query(..., description="Plan artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List decision artifacts for a given plan, newest first.
    """
    decisions = query_decisions_by_plan(batch_plan_artifact_id)[:limit]

    results = []
    for dec in decisions:
        payload = dec.get("payload", {})
        index_meta = dec.get("index_meta") or {}
        index_meta.setdefault("parent_batch_plan_artifact_id", batch_plan_artifact_id)
        index_meta.setdefault("batch_label", payload.get("batch_label"))
        index_meta.setdefault("session_id", payload.get("session_id"))
        index_meta.setdefault("tool_kind", "saw_lab")
        index_meta.setdefault("kind_group", "batch")

        results.append(
            {
                "artifact_id": dec.get("artifact_id"),
                "id": dec.get("artifact_id"),
                "kind": dec.get("kind", "saw_batch_decision"),
                "status": dec.get("status", "OK"),
                "created_utc": dec.get("created_utc"),
                "index_meta": index_meta,
            }
        )

    return results


@router.get("/decisions/by-spec")
def list_decisions_by_spec(
    batch_spec_artifact_id: str = Query(..., description="Spec artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List decision artifacts for a given spec, newest first.
    """
    decisions = query_decisions_by_spec(batch_spec_artifact_id)[:limit]

    results = []
    for dec in decisions:
        payload = dec.get("payload", {})
        index_meta = dec.get("index_meta") or {}
        index_meta.setdefault("parent_batch_spec_artifact_id", batch_spec_artifact_id)
        index_meta.setdefault("batch_label", payload.get("batch_label"))
        index_meta.setdefault("session_id", payload.get("session_id"))
        index_meta.setdefault("tool_kind", "saw_lab")
        index_meta.setdefault("kind_group", "batch")

        results.append(
            {
                "artifact_id": dec.get("artifact_id"),
                "id": dec.get("artifact_id"),
                "kind": dec.get("kind", "saw_batch_decision"),
                "status": dec.get("status", "OK"),
                "created_utc": dec.get("created_utc"),
                "index_meta": index_meta,
            }
        )

    return results


@router.get("/executions/by-plan")
def list_executions_by_plan(
    batch_plan_artifact_id: str = Query(..., description="Plan artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List execution artifacts for a given plan, newest first.
    """
    executions = query_executions_by_plan(batch_plan_artifact_id)[:limit]

    results = []
    for ex in executions:
        payload = ex.get("payload", {})
        index_meta = ex.get("index_meta") or {}
        index_meta.setdefault("parent_batch_plan_artifact_id", batch_plan_artifact_id)
        index_meta.setdefault("batch_label", payload.get("batch_label"))
        index_meta.setdefault("session_id", payload.get("session_id"))
        index_meta.setdefault("tool_kind", "saw_lab")
        index_meta.setdefault("kind_group", "batch")

        results.append(
            {
                "artifact_id": ex.get("artifact_id"),
                "id": ex.get("artifact_id"),
                "kind": ex.get("kind", "saw_batch_execution"),
                "status": ex.get("status", "OK"),
                "created_utc": ex.get("created_utc"),
                "index_meta": index_meta,
            }
        )

    return results


@router.get("/executions/by-spec")
def list_executions_by_spec(
    batch_spec_artifact_id: str = Query(..., description="Spec artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List execution artifacts for a given spec, newest first.
    """
    executions = query_executions_by_spec(batch_spec_artifact_id)[:limit]

    results = []
    for ex in executions:
        payload = ex.get("payload", {})
        index_meta = ex.get("index_meta") or {}
        index_meta.setdefault("parent_batch_spec_artifact_id", batch_spec_artifact_id)
        index_meta.setdefault("batch_label", payload.get("batch_label"))
        index_meta.setdefault("session_id", payload.get("session_id"))
        index_meta.setdefault("tool_kind", "saw_lab")
        index_meta.setdefault("kind_group", "batch")

        results.append(
            {
                "artifact_id": ex.get("artifact_id"),
                "id": ex.get("artifact_id"),
                "kind": ex.get("kind", "saw_batch_execution"),
                "status": ex.get("status", "OK"),
                "created_utc": ex.get("created_utc"),
                "index_meta": index_meta,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Op-Toolpaths Lookup Endpoints
# ---------------------------------------------------------------------------


@router.get("/op-toolpaths/by-decision")
def list_op_toolpaths_by_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
    limit: int = Query(200, ge=1, le=1000, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List op_toolpaths artifacts for a given decision.
    """
    items = query_op_toolpaths_by_decision(batch_decision_artifact_id)[:limit]

    results = []
    for art in items:
        payload = art.get("payload", {})
        index_meta = art.get("index_meta") or {}
        index_meta.setdefault(
            "parent_batch_decision_artifact_id", batch_decision_artifact_id
        )
        index_meta.setdefault("op_id", payload.get("op_id"))
        index_meta.setdefault("setup_key", payload.get("setup_key"))

        results.append(
            {
                "artifact_id": art.get("artifact_id"),
                "id": art.get("artifact_id"),
                "kind": art.get("kind", "saw_batch_op_toolpaths"),
                "status": art.get("status", "OK"),
                "created_utc": art.get("created_utc"),
                "index_meta": index_meta,
                "payload": payload,
            }
        )

    return results


@router.get("/op-toolpaths/by-execution")
def list_op_toolpaths_by_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> List[Dict[str, Any]]:
    """
    List op_toolpaths artifacts for a given execution (from children).
    """
    items = query_op_toolpaths_by_execution(batch_execution_artifact_id)

    results = []
    for art in items:
        payload = art.get("payload", {})
        index_meta = art.get("index_meta") or {}
        index_meta.setdefault(
            "parent_batch_execution_artifact_id", batch_execution_artifact_id
        )
        index_meta.setdefault("op_id", payload.get("op_id"))
        index_meta.setdefault("setup_key", payload.get("setup_key"))

        results.append(
            {
                "artifact_id": art.get("artifact_id"),
                "id": art.get("artifact_id"),
                "kind": art.get("kind", "saw_batch_op_toolpaths"),
                "status": art.get("status", "OK"),
                "created_utc": art.get("created_utc"),
                "index_meta": index_meta,
                "payload": payload,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Convenience Lookup Aliases
# ---------------------------------------------------------------------------


@router.get("/toolpaths/by-decision", response_model=BatchToolpathsByDecisionResponse)
def toolpaths_by_decision(
    batch_decision_artifact_id: str,
) -> BatchToolpathsByDecisionResponse:
    """
    Convenience alias:
      decision -> latest toolpaths artifact id (+ small summary).
    This is a read-only lookup (no generation).
    """
    from .toolpaths_lookup_service import get_latest_toolpaths_for_decision

    out = get_latest_toolpaths_for_decision(
        batch_decision_artifact_id=batch_decision_artifact_id
    )
    if not out:
        return BatchToolpathsByDecisionResponse(
            batch_decision_artifact_id=batch_decision_artifact_id
        )
    return BatchToolpathsByDecisionResponse(**out)


@router.get("/execution/by-decision", response_model=BatchExecutionByDecisionResponse)
def execution_by_decision(
    batch_decision_artifact_id: str,
) -> BatchExecutionByDecisionResponse:
    """
    Convenience alias:
      decision -> latest execution artifact id (+ small summary).
    Read-only lookup (no execution start).
    """
    from .executions_lookup_service import get_latest_execution_for_decision

    out = get_latest_execution_for_decision(
        batch_decision_artifact_id=batch_decision_artifact_id
    )
    if not out:
        return BatchExecutionByDecisionResponse(
            batch_decision_artifact_id=batch_decision_artifact_id
        )
    return BatchExecutionByDecisionResponse(**out)


@router.get("/executions/by-decision", response_model=BatchExecutionsByDecisionResponse)
def executions_by_decision(
    batch_decision_artifact_id: str,
    limit: int = 200,
    offset: int = 0,
    newest_first: bool = True,
) -> BatchExecutionsByDecisionResponse:
    """
    Convenience list:
      decision -> all execution artifacts (summaries), optionally paginated.
    """
    from .executions_list_service import list_executions_for_decision

    out = list_executions_for_decision(
        batch_decision_artifact_id=batch_decision_artifact_id,
        limit=limit,
        offset=offset,
        newest_first=newest_first,
    )
    if not out:
        # consistent empty response
        return BatchExecutionsByDecisionResponse(
            batch_decision_artifact_id=batch_decision_artifact_id,
            total=0,
            offset=int(offset),
            limit=int(limit),
            items=[],
        )
    return BatchExecutionsByDecisionResponse(**out)


# ---------------------------------------------------------------------------
# Batch Links
# ---------------------------------------------------------------------------


@router.get("/links")
def get_batch_links(
    batch_label: str = Query(..., description="Batch label to look up"),
    session_id: str = Query(..., description="Session ID to look up"),
) -> Dict[str, Optional[str]]:
    """
    Get latest artifact IDs for a batch label + session.

    Returns latest_spec_artifact_id, latest_plan_artifact_id,
    latest_decision_artifact_id, latest_execution_artifact_id.
    """
    return query_latest_by_label_and_session(batch_label, session_id)
