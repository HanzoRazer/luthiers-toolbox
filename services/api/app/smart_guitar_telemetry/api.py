"""
Smart Guitar -> ToolBox Telemetry Ingestion API

This endpoint receives telemetry from Smart Guitar devices and validates
it against the manufacturing-only boundary contract.

POST /api/telemetry/ingest
- Accepts telemetry payloads
- Validates against schema + forbidden field list
- Rejects any player/pedagogy data
- Returns validation result
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from .validator import (
    validate_telemetry,
    TelemetryValidationResult,
    FORBIDDEN_FIELDS,
)
from .schemas import TelemetryPayload, TelemetryCategory

_log = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================


class TelemetryIngestResponse(BaseModel):
    """Response for successful telemetry ingestion."""
    accepted: bool = Field(..., description="Whether the payload was accepted")
    telemetry_id: Optional[str] = Field(None, description="Assigned telemetry ID if accepted")
    instrument_id: str = Field(..., description="Instrument that sent the telemetry")
    category: str = Field(..., description="Telemetry category")
    metric_count: int = Field(..., description="Number of metrics in payload")
    received_at_utc: str = Field(..., description="Server receive timestamp")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warnings")


class TelemetryRejectResponse(BaseModel):
    """Response for rejected telemetry."""
    accepted: bool = Field(False, description="Always false for rejections")
    errors: List[str] = Field(..., description="Validation errors")
    contract_version: str = Field("v1", description="Contract version used for validation")
    forbidden_fields_detected: List[str] = Field(
        default_factory=list,
        description="List of forbidden fields found in payload"
    )


class TelemetryValidateResponse(BaseModel):
    """Response for dry-run validation."""
    valid: bool = Field(..., description="Whether the payload is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    contract_version: str = Field("v1", description="Contract version used for validation")


class ContractInfoResponse(BaseModel):
    """Response for contract info endpoint."""
    contract_name: str = Field(..., description="Contract name")
    contract_version: str = Field(..., description="Contract version")
    allowed_categories: List[str] = Field(..., description="Allowed telemetry categories")
    forbidden_fields: List[str] = Field(..., description="Fields that will cause rejection")
    schema_url: str = Field(..., description="URL to JSON Schema")


# =============================================================================
# Telemetry Counter (in-memory for now)
# =============================================================================

_telemetry_counter = 0


def _generate_telemetry_id() -> str:
    """Generate a unique telemetry ID."""
    global _telemetry_counter
    _telemetry_counter += 1
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"telem_{ts}_{_telemetry_counter:06d}"


# =============================================================================
# API Endpoints
# =============================================================================


@router.post(
    "/ingest",
    response_model=TelemetryIngestResponse,
    responses={
        422: {"model": TelemetryRejectResponse, "description": "Payload rejected"},
    },
    summary="Ingest telemetry from Smart Guitar",
    description="""
Receives telemetry payloads from Smart Guitar devices.

**Contract Enforcement:**
- Only manufacturing telemetry is accepted
- Player/pedagogy data is hard-blocked
- Categories: utilization, hardware_performance, environment, lifecycle

**Forbidden Fields (will cause rejection):**
player_id, lesson_id, accuracy, timing, midi, audio, coach_feedback, etc.
""",
)
async def ingest_telemetry(payload: Dict[str, Any]) -> TelemetryIngestResponse:
    """
    Ingest telemetry payload from Smart Guitar.

    Validates against the contract and stores if valid.
    Returns 422 if payload contains forbidden fields or fails validation.
    """
    result = validate_telemetry(payload)

    if not result.valid:
        # Extract any forbidden fields that were detected
        forbidden_detected = []
        for field in FORBIDDEN_FIELDS:
            if field in str(result.errors).lower():
                forbidden_detected.append(field)

        _log.warning(
            "Telemetry rejected: instrument=%s errors=%s",
            payload.get("instrument_id", "unknown"),
            result.errors,
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "accepted": False,
                "errors": result.errors,
                "contract_version": "v1",
                "forbidden_fields_detected": forbidden_detected,
            },
        )

    # Payload is valid - accept it
    telemetry_id = _generate_telemetry_id()
    received_at = datetime.now(timezone.utc).isoformat()

    _log.info(
        "Telemetry accepted: id=%s instrument=%s category=%s metrics=%d",
        telemetry_id,
        result.payload.instrument_id,
        result.payload.telemetry_category.value,
        len(result.payload.metrics),
    )

    # TODO: Store telemetry in database/time-series store
    # For now, just acknowledge receipt

    return TelemetryIngestResponse(
        accepted=True,
        telemetry_id=telemetry_id,
        instrument_id=result.payload.instrument_id,
        category=result.payload.telemetry_category.value,
        metric_count=len(result.payload.metrics),
        received_at_utc=received_at,
        warnings=result.warnings,
    )


@router.post(
    "/validate",
    response_model=TelemetryValidateResponse,
    summary="Validate telemetry payload (dry-run)",
    description="""
Validates a telemetry payload without ingesting it.
Use this to test payloads before sending to /ingest.
""",
)
async def validate_telemetry_payload(payload: Dict[str, Any]) -> TelemetryValidateResponse:
    """
    Validate telemetry payload without storing.

    Useful for testing payloads before ingestion.
    """
    result = validate_telemetry(payload)

    return TelemetryValidateResponse(
        valid=result.valid,
        errors=result.errors,
        warnings=result.warnings,
        contract_version="v1",
    )


@router.get(
    "/contract",
    response_model=ContractInfoResponse,
    summary="Get telemetry contract info",
    description="Returns information about the telemetry contract including allowed categories and forbidden fields.",
)
async def get_contract_info() -> ContractInfoResponse:
    """
    Get information about the telemetry contract.

    Returns allowed categories, forbidden fields, and schema location.
    """
    return ContractInfoResponse(
        contract_name="Smart Guitar -> ToolBox Telemetry Contract",
        contract_version="v1",
        allowed_categories=[cat.value for cat in TelemetryCategory],
        forbidden_fields=sorted(FORBIDDEN_FIELDS),
        schema_url="/contracts/smart_guitar_toolbox_telemetry_v1.schema.json",
    )


@router.get(
    "/health",
    summary="Telemetry ingestion health check",
    description="Returns health status of the telemetry ingestion endpoint.",
)
async def telemetry_health() -> Dict[str, Any]:
    """Health check for telemetry ingestion."""
    return {
        "status": "healthy",
        "service": "smart_guitar_telemetry_ingestion",
        "contract_version": "v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
