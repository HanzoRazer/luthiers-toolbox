"""
RMOS Override Router - YELLOW Unlock Endpoint

Provides the operator workflow primitive for unlocking blocked runs.

POST /api/rmos/runs/{run_id}/override
- Creates override.json attachment (content-addressed)
- Updates run status to OK (for YELLOW)
- Preserves original decision.risk_level (authoritative history)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import Principal, require_roles, get_current_principal

from .schemas_override import (
    OverrideRequest,
    OverrideResponse,
    OverrideError as OverrideErrorSchema,
)
from .override_service import (
    apply_override,
    RunNotFoundError,
    NotBlockedError,
    AlreadyOverriddenError,
    RedOverrideNotAllowedError,
    RiskMismatchError,
    AcknowledgmentRequiredError,
    OverrideError,
)
from .store import get_run


router = APIRouter(tags=["runs", "override"])


# =============================================================================
# Dependency: Get operator identity
# =============================================================================

async def get_operator_identity(
    request: Request,
    principal: Principal = Depends(get_current_principal),
) -> tuple[str, Optional[str]]:
    """
    Extract operator ID and name from auth principal.

    Falls back to request header or 'anonymous' for development.
    """
    if principal and principal.user_id:
        # Principal doesn't have display_name, use email or user_id
        display_name = principal.email or principal.user_id
        return principal.user_id, display_name

    # Fallback: check X-Operator-Id header (for dev/testing)
    operator_id = request.headers.get("X-Operator-Id", "anonymous")
    operator_name = request.headers.get("X-Operator-Name")

    return operator_id, operator_name


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/{run_id}/override",
    response_model=OverrideResponse,
    responses={
        404: {"model": OverrideErrorSchema, "description": "Run not found"},
        409: {"model": OverrideErrorSchema, "description": "Already overridden or not blocked"},
        403: {"model": OverrideErrorSchema, "description": "RED override not allowed"},
        422: {"model": OverrideErrorSchema, "description": "Validation error"},
    },
    summary="Override a blocked run",
    description="""
    Override a YELLOW or RED blocked run without regenerating CAM/G-code.

    **Requirements:**
    - Run must be BLOCKED status
    - Run must not already have an override
    - Reason must be at least 10 characters

    **YELLOW Override:**
    - Default scope, always allowed
    - Status changes from BLOCKED → OK

    **RED Override:**
    - Requires `RMOS_ALLOW_RED_OVERRIDE=1` environment flag
    - Requires `acknowledge_risk=true` in request
    - Status changes from BLOCKED → OK

    **Governance:**
    - Original `decision.risk_level` is preserved (never modified)
    - Override is stored as content-addressed `override.json` attachment
    - `meta.override` contains quick-access override info
    - Every override is permanently traceable
    """,
)
async def override_run(
    run_id: str,
    request_body: OverrideRequest,
    request: Request,
    identity: tuple[str, Optional[str]] = Depends(get_operator_identity),
) -> OverrideResponse:
    """
    Override a blocked run.

    Creates an override.json attachment and updates run status to OK.
    """
    operator_id, operator_name = identity
    request_id = request.headers.get("X-Request-Id")

    try:
        response, _ = apply_override(
            run_id=run_id,
            request=request_body,
            operator_id=operator_id,
            operator_name=operator_name,
            request_id=request_id,
        )
        return response

    except RunNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": e.message,
                "code": e.code,
                "run_id": run_id,
            },
        )

    except NotBlockedError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "error": e.message,
                "code": e.code,
                "run_id": run_id,
                "current_status": e.context.get("status"),
            },
        )

    except AlreadyOverriddenError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "error": e.message,
                "code": e.code,
                "run_id": run_id,
                "existing_override_id": e.context.get("existing_override_id"),
            },
        )

    except RedOverrideNotAllowedError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "error": e.message,
                "code": e.code,
                "run_id": run_id,
                "detail": "Set RMOS_ALLOW_RED_OVERRIDE=1 to enable RED overrides",
            },
        )

    except RiskMismatchError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": e.message,
                "code": e.code,
                "run_id": run_id,
                "scope": e.context.get("scope"),
                "actual_risk": e.context.get("actual_risk"),
            },
        )

    except AcknowledgmentRequiredError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": e.message,
                "code": e.code,
                "run_id": run_id,
                "detail": "RED overrides require acknowledge_risk=true",
            },
        )

    except OverrideError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.message,
                "code": e.code,
                "run_id": run_id,
                **e.context,
            },
        )


@router.get(
    "/{run_id}/override",
    summary="Get override info for a run",
    description="Returns the override record if the run has been overridden, or 404 if not.",
)
async def get_override(run_id: str):
    """Get override info for a run."""
    from .override_service import get_override_info

    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"error": "Run not found", "run_id": run_id})

    override_info = get_override_info(run)
    if not override_info:
        raise HTTPException(
            status_code=404,
            detail={"error": "No override found", "run_id": run_id},
        )

    return {
        "run_id": run_id,
        "override": override_info.model_dump(mode="json"),
        "current_status": run.status,
        "original_risk_level": run.decision.risk_level if run.decision else None,
    }
