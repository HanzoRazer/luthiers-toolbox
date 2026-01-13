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
from .store import (
    store_telemetry,
    get_telemetry,
    list_telemetry,
    count_telemetry,
    get_instrument_summary,
    TelemetryStore,
)

# Cost attribution integration
from app.cost_attribution.mapper import telemetry_to_cost_facts
from app.cost_attribution.store import append_cost_facts

_log = logging.getLogger(__name__)

def _repo_root() -> Path:
    """Get repository root for cost attribution."""
    from pathlib import Path
    return Path(__file__).resolve().parents[4]

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
# Additional Response Models
# =============================================================================


class TelemetryRecordResponse(BaseModel):
    """Response for a single telemetry record."""
    telemetry_id: str = Field(..., description="Unique telemetry ID")
    received_at_utc: str = Field(..., description="Server receive timestamp")
    partition: str = Field(..., description="Storage partition (date)")
    instrument_id: str = Field(..., description="Instrument ID")
    manufacturing_batch_id: str = Field(..., description="Manufacturing batch ID")
    category: str = Field(..., description="Telemetry category")
    emitted_at_utc: str = Field(..., description="When payload was emitted")
    metric_count: int = Field(..., description="Number of metrics")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class TelemetryListResponse(BaseModel):
    """Response for listing telemetry records."""
    items: List[TelemetryRecordResponse] = Field(..., description="Telemetry records")
    total: int = Field(..., description="Total matching records")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")


class InstrumentSummaryResponse(BaseModel):
    """Summary statistics for an instrument."""
    instrument_id: str = Field(..., description="Instrument ID")
    total_records: int = Field(..., description="Total telemetry records")
    categories: Dict[str, int] = Field(..., description="Record count by category")
    first_seen_utc: Optional[str] = Field(None, description="First telemetry received")
    last_seen_utc: Optional[str] = Field(None, description="Most recent telemetry")
    batches: List[str] = Field(default_factory=list, description="Manufacturing batches")


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

    # Payload is valid - store it
    stored = store_telemetry(result.payload, warnings=result.warnings)

    # Map to internal cost facts (if applicable)
    try:
        payload_dict = {
            "schema_id": result.payload.schema_id,
            "schema_version": result.payload.schema_version,
            "emitted_at_utc": result.payload.emitted_at_utc.isoformat(),
            "instrument_id": result.payload.instrument_id,
            "manufacturing_batch_id": result.payload.manufacturing_batch_id,
            "telemetry_category": result.payload.telemetry_category.value,
            "metrics": {k: {"value": v.value, "unit": v.unit.value, "aggregation": v.aggregation.value} for k, v in result.payload.metrics.items()},
            "design_revision_id": result.payload.design_revision_id,
            "hardware_sku": result.payload.hardware_sku,
            "component_lot_id": result.payload.component_lot_id,
        }
        cost_facts, cost_warnings = telemetry_to_cost_facts(_repo_root(), payload_dict)
        if cost_facts:
            append_cost_facts(_repo_root(), cost_facts)
            _log.info("Cost attribution: mapped %d facts from telemetry %s", len(cost_facts), stored.telemetry_id)
        result.warnings.extend(cost_warnings)
    except Exception as e:
        _log.warning("Cost attribution failed (non-fatal): %s", e)

    _log.info(
        "Telemetry accepted: id=%s instrument=%s category=%s metrics=%d",
        stored.telemetry_id,
        result.payload.instrument_id,
        result.payload.telemetry_category.value,
        len(result.payload.metrics),
    )

    return TelemetryIngestResponse(
        accepted=True,
        telemetry_id=stored.telemetry_id,
        instrument_id=result.payload.instrument_id,
        category=result.payload.telemetry_category.value,
        metric_count=len(result.payload.metrics),
        received_at_utc=stored.received_at_utc.isoformat(),
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


# =============================================================================
# Query Endpoints
# =============================================================================


@router.get(
    "/records/{telemetry_id}",
    response_model=TelemetryRecordResponse,
    summary="Get telemetry record by ID",
    description="Retrieve a specific telemetry record by its ID.",
)
async def get_telemetry_record(telemetry_id: str) -> TelemetryRecordResponse:
    """Get a telemetry record by ID."""
    record = get_telemetry(telemetry_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry record not found: {telemetry_id}",
        )

    return TelemetryRecordResponse(
        telemetry_id=record.telemetry_id,
        received_at_utc=record.received_at_utc.isoformat(),
        partition=record.partition,
        instrument_id=record.payload.instrument_id,
        manufacturing_batch_id=record.payload.manufacturing_batch_id,
        category=record.payload.telemetry_category.value,
        emitted_at_utc=record.payload.emitted_at_utc.isoformat(),
        metric_count=len(record.payload.metrics),
        warnings=record.warnings,
    )


@router.get(
    "/records",
    response_model=TelemetryListResponse,
    summary="List telemetry records",
    description="List telemetry records with optional filtering by instrument, batch, or category.",
)
async def list_telemetry_records(
    limit: int = 50,
    offset: int = 0,
    instrument_id: Optional[str] = None,
    manufacturing_batch_id: Optional[str] = None,
    category: Optional[str] = None,
) -> TelemetryListResponse:
    """List telemetry records with optional filtering."""
    # Parse category if provided
    cat_enum = None
    if category:
        try:
            cat_enum = TelemetryCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}. Must be one of: {[c.value for c in TelemetryCategory]}",
            )

    records = list_telemetry(
        limit=limit,
        offset=offset,
        instrument_id=instrument_id,
        manufacturing_batch_id=manufacturing_batch_id,
        category=cat_enum,
    )

    total = count_telemetry(
        instrument_id=instrument_id,
        manufacturing_batch_id=manufacturing_batch_id,
        category=cat_enum,
    )

    items = [
        TelemetryRecordResponse(
            telemetry_id=r.telemetry_id,
            received_at_utc=r.received_at_utc.isoformat(),
            partition=r.partition,
            instrument_id=r.payload.instrument_id,
            manufacturing_batch_id=r.payload.manufacturing_batch_id,
            category=r.payload.telemetry_category.value,
            emitted_at_utc=r.payload.emitted_at_utc.isoformat(),
            metric_count=len(r.payload.metrics),
            warnings=r.warnings,
        )
        for r in records
    ]

    return TelemetryListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/instruments/{instrument_id}/summary",
    response_model=InstrumentSummaryResponse,
    summary="Get instrument telemetry summary",
    description="Get summary statistics for a specific instrument.",
)
async def get_instrument_telemetry_summary(instrument_id: str) -> InstrumentSummaryResponse:
    """Get summary statistics for an instrument."""
    summary = get_instrument_summary(instrument_id)

    return InstrumentSummaryResponse(
        instrument_id=summary["instrument_id"],
        total_records=summary["total_records"],
        categories=summary["categories"],
        first_seen_utc=summary.get("first_seen_utc"),
        last_seen_utc=summary.get("last_seen_utc"),
        batches=summary.get("batches", []),
    )


@router.get(
    "/stats",
    summary="Get telemetry statistics",
    description="Get overall telemetry ingestion statistics.",
)
async def get_telemetry_stats() -> Dict[str, Any]:
    """Get overall telemetry statistics."""
    total = count_telemetry()

    # Count by category
    categories = {}
    for cat in TelemetryCategory:
        categories[cat.value] = count_telemetry(category=cat)

    return {
        "total_records": total,
        "by_category": categories,
        "contract_version": "v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
