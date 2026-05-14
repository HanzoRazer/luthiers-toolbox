"""
MRP-2B: Body Outline Export Bridge Endpoint

POST /api/export/body-outline
  - Accepts BOE-approved geometry JSON
  - Returns DXF-agnostic Export Object candidate
  - Free tier with rate limiting (10/hour unauth, 100/hour auth)

Sprint: MRP-2B
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth.deps import get_optional_principal
from app.auth.principal import Principal
from app.export.body_export_bridge import (
    BOEApprovedGeometry,
    BodyExportObject,
    IBGContext,
    create_body_export_object,
    is_export_ready,
)
from app.middleware.rate_limit import limiter


router = APIRouter(tags=["Export", "Body"])


# ─── Rate Limit Configuration ────────────────────────────────────────────────

BODY_EXPORT_RATE_FREE = os.getenv("BODY_EXPORT_RATE_FREE", "10/hour")
BODY_EXPORT_RATE_AUTH = os.getenv("BODY_EXPORT_RATE_AUTH", "100/hour")


# ─── Request/Response Models ─────────────────────────────────────────────────


class BodyExportRequest(BaseModel):
    """
    Request body for body outline export endpoint.

    The geometry field accepts BOE JSON export format.
    Optional ibg_context provides IBG session enrichment.
    """
    geometry: BOEApprovedGeometry = Field(
        ...,
        description="BOE-approved body geometry (JSON export format)",
    )
    ibg_context: Optional[IBGContext] = Field(
        None,
        description="Optional IBG session context for enrichment",
    )


class BodyExportResponse(BaseModel):
    """
    Response from body outline export endpoint.

    Contains the Export Object candidate and summary validation info.
    """
    export_object: BodyExportObject
    export_ready: bool = Field(
        ...,
        description="True if geometry passes validation (green/yellow gate)",
    )
    gate_status: str = Field(
        ...,
        description="Validation gate status: green, yellow, or red",
    )
    issues: list = Field(
        default_factory=list,
        description="Validation issues (failures)",
    )
    warnings: list = Field(
        default_factory=list,
        description="Validation warnings",
    )


class ValidationOnlyResponse(BaseModel):
    """Response from validation-only endpoint."""
    valid: bool
    gate_status: str
    issues: list
    warnings: list
    checks: list


# ─── Helper Functions ────────────────────────────────────────────────────────


def _get_rate_limit(principal: Optional[Principal]) -> str:
    """Get rate limit based on auth status."""
    if principal is not None:
        return BODY_EXPORT_RATE_AUTH
    return BODY_EXPORT_RATE_FREE


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post(
    "/body-outline",
    response_model=BodyExportResponse,
    summary="Convert BOE geometry to Export Object",
    description="""
Transform BOE-approved body geometry into a DXF-agnostic Export Object candidate.

The Export Object contains:
- **metadata**: export_id, source provenance, timestamp
- **geometry**: coordinate system, bounds, contour entities
- **validation**: gate status, checks performed, issues/warnings
- **intent**: operation type, finish requirements
- **extensions**: optional IBG morphology data

Gate status meanings:
- **green**: All checks passed, ready for export
- **yellow**: Warnings present but exportable
- **red**: Validation failures, not export-ready

Rate limits: 10/hour unauthenticated, 100/hour authenticated
    """,
)
@limiter.limit(BODY_EXPORT_RATE_FREE)
async def create_body_export(
    request: Request,
    payload: BodyExportRequest,
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> BodyExportResponse:
    """
    Transform BOE-approved geometry to Export Object.

    Accepts BOE JSON export format and returns a validated Export Object
    candidate suitable for downstream translators.
    """
    try:
        # Create Export Object using bridge adapter
        export_obj = create_body_export_object(
            approved=payload.geometry,
            ibg_context=payload.ibg_context,
        )

        # Check if export-ready
        export_ready = is_export_ready(export_obj.validation)

        return BodyExportResponse(
            export_object=export_obj,
            export_ready=export_ready,
            gate_status=export_obj.validation.gate_status,
            issues=export_obj.validation.issues,
            warnings=export_obj.validation.warnings,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export object creation failed: {str(e)}",
        )


@router.post(
    "/body-outline/validate",
    response_model=ValidationOnlyResponse,
    summary="Validate BOE geometry without creating Export Object",
    description="""
Dry-run validation of BOE geometry.

Returns validation status without creating a full Export Object.
Useful for pre-flight checks before export.
    """,
)
@limiter.limit(BODY_EXPORT_RATE_FREE)
async def validate_body_geometry(
    request: Request,
    payload: BodyExportRequest,
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> ValidationOnlyResponse:
    """
    Validate BOE geometry without creating Export Object.

    Returns validation results only (dry run).
    """
    try:
        from app.export.body_export_bridge import validate_body_geometry as _validate

        validation = _validate(
            outer=payload.geometry.outer,
            voids=payload.geometry.voids,
        )

        return ValidationOnlyResponse(
            valid=validation.gate_status in ("green", "yellow"),
            gate_status=validation.gate_status,
            issues=validation.issues,
            warnings=validation.warnings,
            checks=[c.model_dump() for c in validation.checks_performed],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}",
        )
