"""
Lifecycle Capability Router

CAM Dev Order 6H: Operation introspection endpoints.

Provides endpoints for discovering CAM operation capabilities
without executing any operations.

Core principle:
  Introspection, not execution.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.cam_operation_registry import (
    CAMOperationCapability,
    get_operation_capability,
    get_all_capabilities,
    list_lifecycle_supported_operations,
    list_governed_operations,
)


router = APIRouter(prefix="/lifecycle", tags=["cam-lifecycle-capabilities"])


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class CapabilitiesListResponse(BaseModel):
    """Response containing all registered operation capabilities."""
    operations: List[CAMOperationCapability] = Field(
        ..., description="List of registered operation capabilities"
    )
    total_count: int = Field(..., description="Total number of registered operations")
    lifecycle_supported_count: int = Field(
        ..., description="Number of operations supporting lifecycle orchestration"
    )
    governed_count: int = Field(
        ..., description="Number of governed/canonical operations"
    )


class CapabilitySummary(BaseModel):
    """Summary view of operation capabilities."""
    operation: str
    maturity: str
    exportability_class: str
    lifecycle_supported: bool
    machine_ready: bool


class CapabilitiesSummaryResponse(BaseModel):
    """Lightweight summary of all capabilities."""
    operations: List[CapabilitySummary] = Field(
        ..., description="Summary of each operation"
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/capabilities",
    response_model=CapabilitiesListResponse,
    summary="List all CAM operation capabilities",
    description="""
Get the complete capability declarations for all registered CAM operations.

This is the canonical source of truth for:
- What operations the lifecycle supports
- What each operation can export
- What translator features each operation requires
- Governance maturity levels

**No execution occurs.** This is introspection only.
""",
)
async def list_capabilities() -> CapabilitiesListResponse:
    """List all registered CAM operation capabilities."""
    all_caps = get_all_capabilities()
    lifecycle_supported = list_lifecycle_supported_operations()
    governed = list_governed_operations()

    return CapabilitiesListResponse(
        operations=all_caps,
        total_count=len(all_caps),
        lifecycle_supported_count=len(lifecycle_supported),
        governed_count=len(governed),
    )


@router.get(
    "/capabilities/summary",
    response_model=CapabilitiesSummaryResponse,
    summary="Get lightweight summary of capabilities",
    description="""
Get a condensed view of operation capabilities for quick discovery.

Useful for UI dropdowns or capability checks without full detail.
""",
)
async def list_capabilities_summary() -> CapabilitiesSummaryResponse:
    """Get lightweight summary of all capabilities."""
    all_caps = get_all_capabilities()

    summaries = [
        CapabilitySummary(
            operation=cap.operation,
            maturity=cap.maturity,
            exportability_class=cap.exportability_class,
            lifecycle_supported=cap.lifecycle_supported,
            machine_ready=cap.machine_ready,
        )
        for cap in all_caps
    ]

    return CapabilitiesSummaryResponse(operations=summaries)


@router.get(
    "/capabilities/{operation}",
    response_model=CAMOperationCapability,
    summary="Get capability for a specific operation",
    description="""
Get the complete capability declaration for a single CAM operation.

Returns 404 if the operation is not registered.
""",
    responses={
        404: {"description": "Operation not found in registry"},
    },
)
async def get_capability(operation: str) -> CAMOperationCapability:
    """Get capability declaration for a specific operation."""
    capability = get_operation_capability(operation)

    if capability is None:
        raise HTTPException(
            status_code=404,
            detail=f"Operation '{operation}' not found in capability registry",
        )

    return capability


@router.get(
    "/supported-operations",
    response_model=List[str],
    summary="List lifecycle-supported operations",
    description="""
Get the list of operation identifiers that support lifecycle orchestration.

This is the canonical list used by the lifecycle dispatcher.
""",
)
async def list_supported() -> List[str]:
    """List operations that support lifecycle orchestration."""
    return list_lifecycle_supported_operations()
