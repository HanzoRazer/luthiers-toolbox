"""
Translator Capability Router

CAM Dev Order 7B: Translator introspection endpoints.

Provides endpoints for discovering translator and postprocessor capabilities
without executing any translations.

Core principle:
  Introspection, not execution.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.translator_capability_registry import (
    TranslatorCapability,
    TranslatorCategory,
    TranslatorOutputClass,
    get_translator_capability,
    list_translator_capabilities,
    list_translator_ids,
    list_translators_by_category,
    list_translators_by_output_class,
    list_translators_for_operation,
)


router = APIRouter(prefix="/translators", tags=["cam-translator-capabilities"])


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class TranslatorCapabilitiesListResponse(BaseModel):
    """Response containing all registered translator capabilities."""

    translators: List[TranslatorCapability] = Field(
        ..., description="List of registered translator capabilities"
    )
    total_count: int = Field(
        ..., description="Total number of registered translators"
    )
    translator_count: int = Field(
        ..., description="Number of translator-category entries"
    )
    postprocessor_count: int = Field(
        ..., description="Number of postprocessor-category entries"
    )


class TranslatorSummary(BaseModel):
    """Summary view of translator capabilities."""

    translator_id: str
    translator_name: str
    translator_category: str
    output_class: str
    execution_state: str
    maturity: str
    execution_supported: bool
    machine_output_supported: bool


class TranslatorCapabilitiesSummaryResponse(BaseModel):
    """Lightweight summary of all translator capabilities."""

    translators: List[TranslatorSummary] = Field(
        ..., description="Summary of each translator"
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/capabilities",
    response_model=TranslatorCapabilitiesListResponse,
    summary="List all translator capabilities",
    description="""
Get the complete capability declarations for all registered translators
and postprocessors.

This is the canonical source of truth for:
- What translators exist
- What output formats each translator produces
- What operations each translator declares support for
- Execution state and maturity levels

**No execution occurs.** This is introspection only.
""",
)
async def list_capabilities() -> TranslatorCapabilitiesListResponse:
    """List all registered translator capabilities."""
    all_caps = list_translator_capabilities()
    translators = list_translators_by_category("translator")
    postprocessors = list_translators_by_category("postprocessor")

    return TranslatorCapabilitiesListResponse(
        translators=all_caps,
        total_count=len(all_caps),
        translator_count=len(translators),
        postprocessor_count=len(postprocessors),
    )


@router.get(
    "/capabilities/summary",
    response_model=TranslatorCapabilitiesSummaryResponse,
    summary="Get lightweight summary of translator capabilities",
    description="""
Get a condensed view of translator capabilities for quick discovery.

Useful for UI dropdowns or capability checks without full detail.
""",
)
async def list_capabilities_summary() -> TranslatorCapabilitiesSummaryResponse:
    """Get lightweight summary of all translator capabilities."""
    all_caps = list_translator_capabilities()

    summaries = [
        TranslatorSummary(
            translator_id=cap.translator_id,
            translator_name=cap.translator_name,
            translator_category=cap.translator_category,
            output_class=cap.output_class,
            execution_state=cap.execution_state,
            maturity=cap.maturity,
            execution_supported=cap.execution_supported,
            machine_output_supported=cap.machine_output_supported,
        )
        for cap in all_caps
    ]

    return TranslatorCapabilitiesSummaryResponse(translators=summaries)


@router.get(
    "/capabilities/{translator_id}",
    response_model=TranslatorCapability,
    summary="Get capability for a specific translator",
    description="""
Get the complete capability declaration for a single translator.

Returns 404 if the translator is not registered.
""",
    responses={
        404: {"description": "Translator not found in registry"},
    },
)
async def get_capability(translator_id: str) -> TranslatorCapability:
    """Get capability declaration for a specific translator."""
    capability = get_translator_capability(translator_id)

    if capability is None:
        raise HTTPException(
            status_code=404,
            detail=f"Translator '{translator_id}' not found in capability registry",
        )

    return capability


@router.get(
    "/ids",
    response_model=List[str],
    summary="List all translator IDs",
    description="""
Get the list of all registered translator identifiers.

Useful for validation and discovery without full capability details.
""",
)
async def list_ids() -> List[str]:
    """List all registered translator identifiers."""
    return list_translator_ids()


@router.get(
    "/by-category/{category}",
    response_model=List[TranslatorCapability],
    summary="List translators by category",
    description="""
Get translators filtered by category (translator or postprocessor).

- `translator`: Produces format-specific artifacts (DXF, SVG)
- `postprocessor`: Produces machine-specific output (G-code)
""",
    responses={
        422: {"description": "Invalid category"},
    },
)
async def list_by_category(category: TranslatorCategory) -> List[TranslatorCapability]:
    """List translators by category."""
    return list_translators_by_category(category)


@router.get(
    "/by-output/{output_class}",
    response_model=List[TranslatorCapability],
    summary="List translators by output class",
    description="""
Get translators filtered by output format class.

Valid output classes: dxf, gcode, svg, toolpath
""",
    responses={
        422: {"description": "Invalid output class"},
    },
)
async def list_by_output(output_class: TranslatorOutputClass) -> List[TranslatorCapability]:
    """List translators by output format class."""
    return list_translators_by_output_class(output_class)


@router.get(
    "/for-operation/{operation}",
    response_model=List[TranslatorCapability],
    summary="List translators supporting an operation",
    description="""
Get translators that declare support for a specific CAM operation.

Note: This is capability declaration, not execution readiness.
A translator may declare support but still have execution_supported=False.
""",
)
async def list_for_operation(operation: str) -> List[TranslatorCapability]:
    """List translators that declare support for an operation."""
    return list_translators_for_operation(operation)
