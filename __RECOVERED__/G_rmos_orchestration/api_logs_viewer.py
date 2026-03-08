# services/api/app/rmos/api_logs_viewer.py
"""
RMOS AI Log Viewer API - Endpoints for querying AI constraint search logs.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from .schemas_logs_ai import (
    AiAttemptLogView,
    AiRunSummaryLogView,
    AiLogQueryParams,
)

router = APIRouter(
    prefix="/rmos/logs/ai",
    tags=["rmos-logs-ai"],
)


# -------------------------------------------------------------------
# Logging backend integration
# -------------------------------------------------------------------

try:
    from .logging_core import query_rmos_events
except ImportError:  # WP-1: narrowed from except Exception
    def query_rmos_events(
        event_type: str,
        filters: Dict[str, Any],
        limit: int,
        order: str = "desc",
    ) -> List[Dict[str, Any]]:
        """Safe no-op stub if logging_core is not wired yet."""
        return []


# -------------------------------------------------------------------
# Query parameter parsing
# -------------------------------------------------------------------

def _parse_query_params(
    run_id: str | None = Query(default=None),
    tool_id: str | None = Query(default=None),
    material_id: str | None = Query(default=None),
    workflow_mode: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> AiLogQueryParams:
    return AiLogQueryParams(
        run_id=run_id,
        tool_id=tool_id,
        material_id=material_id,
        workflow_mode=workflow_mode,
        limit=limit,
    )


def _build_filters(params: AiLogQueryParams) -> Dict[str, Any]:
    filters: Dict[str, Any] = {}
    if params.run_id:
        filters["run_id"] = params.run_id
    if params.tool_id:
        filters["tool_id"] = params.tool_id
    if params.material_id:
        filters["material_id"] = params.material_id
    if params.workflow_mode:
        filters["workflow_mode"] = params.workflow_mode
    return filters


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------

@router.get(
    "/attempts",
    response_model=List[AiAttemptLogView],
    summary="List recent AI constraint attempts.",
)
def list_ai_attempts(
    params: AiLogQueryParams = Depends(_parse_query_params),
) -> List[AiAttemptLogView]:
    """
    Return recent AI constraint attempts filtered by:
      - run_id
      - tool_id
      - material_id
      - workflow_mode
    """
    filters = _build_filters(params)
    raw_events = query_rmos_events(
        event_type="ai_constraint_attempt",
        filters=filters,
        limit=params.limit,
        order="desc",
    )

    attempts: List[AiAttemptLogView] = []
    for evt in raw_events:
        try:
            attempts.append(AiAttemptLogView.model_validate(evt))
        except (ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
            continue

    return attempts


@router.get(
    "/runs",
    response_model=List[AiRunSummaryLogView],
    summary="List recent AI constraint run summaries.",
)
def list_ai_runs(
    params: AiLogQueryParams = Depends(_parse_query_params),
) -> List[AiRunSummaryLogView]:
    """
    Return recent AI constraint run summaries filtered by:
      - run_id
      - tool_id
      - material_id
      - workflow_mode
    """
    filters = _build_filters(params)
    raw_events = query_rmos_events(
        event_type="ai_constraint_run_summary",
        filters=filters,
        limit=params.limit,
        order="desc",
    )

    runs: List[AiRunSummaryLogView] = []
    for evt in raw_events:
        try:
            runs.append(AiRunSummaryLogView.model_validate(evt))
        except (ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
            continue

    return runs
