"""
RMOS AI Advisory Router

FastAPI router for advisory request/retrieval endpoints.

Endpoints:
- POST /api/rmos/advisories/request - Request a new advisory
- GET /api/rmos/advisories/{advisory_id} - Get advisory by ID
- GET /api/rmos/advisories - List recent advisories
"""

from __future__ import annotations

import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from .exceptions import (
    AiIntegratorError,
    AiIntegratorGovernance,
    AiIntegratorSchema,
    AiIntegratorUnsupported,
)
from .schemas import (
    AdvisoryArtifactV1,
    AdvisoryGetResponse,
    AdvisoryRequestResponse,
    AIContextPacketV1,
)
from .service import request_advisory
from .store import list_advisories, load_advisory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advisories", tags=["RMOS", "AI Advisory"])


class AdvisoryListResponse(BaseModel):
    """Response for listing advisories."""

    ok: bool = True
    advisories: List[AdvisoryArtifactV1]
    count: int


@router.post("/request", response_model=AdvisoryRequestResponse)
async def post_request_advisory(
    packet: AIContextPacketV1,
    request: Request,
) -> AdvisoryRequestResponse:
    """
    Request a new AI advisory from RMOS.

    This is the ONLY entry point for AI advisory generation.
    ToolBox sends an AIContextPacket; RMOS invokes ai-integrator CLI,
    validates output, persists the artifact, and returns advisory_id.

    Raises:
        422: Invalid AIContextPacket schema
        400: Governance violation
        503: AI integrator unavailable or runtime error
    """
    # Extract user_id from request if available (for audit)
    user_id = getattr(request.state, "user_id", None)

    try:
        return request_advisory(packet.model_dump(), user_id=user_id)

    except AiIntegratorSchema as e:
        logger.warning(f"Schema validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "SCHEMA_VALIDATION_ERROR",
                "message": str(e),
                "exit_code": e.exit_code,
            },
        ) from e

    except AiIntegratorGovernance as e:
        logger.warning(f"Governance violation: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "GOVERNANCE_VIOLATION",
                "message": str(e),
                "exit_code": e.exit_code,
            },
        ) from e

    except AiIntegratorUnsupported as e:
        logger.warning(f"Unsupported request: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNSUPPORTED_REQUEST",
                "message": str(e),
                "exit_code": e.exit_code,
            },
        ) from e

    except AiIntegratorError as e:
        logger.error(f"AI integrator error: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "AI_INTEGRATOR_ERROR",
                "message": str(e),
                "exit_code": e.exit_code,
            },
        ) from e


@router.get("/{advisory_id}", response_model=AdvisoryGetResponse)
async def get_advisory(advisory_id: str) -> AdvisoryGetResponse:
    """
    Get an advisory artifact by ID.

    Raises:
        404: Advisory not found
    """
    artifact = load_advisory(advisory_id)
    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "ADVISORY_NOT_FOUND",
                "message": f"Advisory '{advisory_id}' not found",
            },
        )

    return AdvisoryGetResponse(ok=True, artifact=artifact)


@router.get("", response_model=AdvisoryListResponse)
async def get_advisories(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    date_from: Annotated[Optional[str], Query(description="ISO date (YYYY-MM-DD)")] = None,
    date_to: Annotated[Optional[str], Query(description="ISO date (YYYY-MM-DD)")] = None,
) -> AdvisoryListResponse:
    """
    List recent advisory artifacts.

    Returns advisories sorted by creation date, newest first.
    """
    advisories = list_advisories(
        limit=limit,
        date_from=date_from,
        date_to=date_to,
    )

    return AdvisoryListResponse(
        ok=True,
        advisories=advisories,
        count=len(advisories),
    )
