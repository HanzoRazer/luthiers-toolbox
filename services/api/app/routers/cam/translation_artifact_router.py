"""
Translation Artifact Router

CAM Dev Order 7D: Introspection endpoints for translation artifacts.

Provides read-only access to:
  - Registered artifact classes (what types of artifacts exist)
  - Individual artifact lookup
  - Filtering by output class and translator category

7D invariants:
  - All responses are metadata only
  - No executable payloads
  - No machine output
"""

from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.cam.translation_artifact_registry import (
    ArtifactClassRegistration,
    ArtifactOutputClass,
    get_artifact_class,
    get_artifact_classes_by_category,
    get_artifact_classes_by_output,
    list_artifact_classes,
    list_artifact_class_ids,
)


router = APIRouter(
    prefix="/api/cam/translation-artifacts",
    tags=["CAM Translation Artifacts"],
)


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class ArtifactClassListResponse(BaseModel):
    """Response for listing artifact classes."""

    artifact_classes: List[ArtifactClassRegistration] = Field(
        ..., description="List of registered artifact classes"
    )
    count: int = Field(..., description="Total number of artifact classes")

    # 7D Safety Assertions
    executable_artifacts_present: bool = Field(
        default=False,
        description="Always false in 7D — no executable artifacts"
    )
    machine_output_artifacts_present: bool = Field(
        default=False,
        description="Always false in 7D — no machine output artifacts"
    )


class ArtifactClassResponse(BaseModel):
    """Response for single artifact class lookup."""

    artifact_class: ArtifactClassRegistration = Field(
        ..., description="Artifact class registration"
    )

    # 7D Safety Assertions
    executable_output_supported: bool = Field(
        default=False,
        description="Always false in 7D — no executable output"
    )
    machine_output_supported: bool = Field(
        default=False,
        description="Always false in 7D — no machine output"
    )


class ArtifactClassIdListResponse(BaseModel):
    """Response for listing artifact class IDs only."""

    artifact_class_ids: List[str] = Field(
        ..., description="List of artifact class identifiers"
    )
    count: int = Field(..., description="Total number of artifact classes")


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=ArtifactClassListResponse,
    summary="List all translation artifact classes",
    description="Returns all registered translation artifact classes with their metadata.",
)
def list_translation_artifact_classes(
    output_class: Optional[ArtifactOutputClass] = Query(
        default=None,
        description="Filter by output class (dxf, svg, neutral_toolpath, gcode, machine_output)",
    ),
    translator_category: Optional[Literal["translator", "postprocessor"]] = Query(
        default=None,
        description="Filter by translator category",
    ),
) -> ArtifactClassListResponse:
    """List all registered translation artifact classes."""
    # Apply filters if provided
    if output_class is not None:
        classes = get_artifact_classes_by_output(output_class)
    elif translator_category is not None:
        classes = get_artifact_classes_by_category(translator_category)
    else:
        classes = list_artifact_classes()

    # Apply second filter if both provided
    if output_class is not None and translator_category is not None:
        classes = [
            c for c in classes
            if c.translator_category == translator_category
        ]

    return ArtifactClassListResponse(
        artifact_classes=classes,
        count=len(classes),
        executable_artifacts_present=False,
        machine_output_artifacts_present=False,
    )


@router.get(
    "/ids",
    response_model=ArtifactClassIdListResponse,
    summary="List artifact class IDs",
    description="Returns just the IDs of registered artifact classes.",
)
def list_translation_artifact_class_ids() -> ArtifactClassIdListResponse:
    """List all registered artifact class IDs."""
    ids = list_artifact_class_ids()
    return ArtifactClassIdListResponse(
        artifact_class_ids=ids,
        count=len(ids),
    )


@router.get(
    "/{artifact_class_id}",
    response_model=ArtifactClassResponse,
    summary="Get artifact class by ID",
    description="Returns a single artifact class registration by its ID.",
)
def get_translation_artifact_class(
    artifact_class_id: str = Path(
        ..., description="Artifact class identifier"
    ),
) -> ArtifactClassResponse:
    """Get a specific artifact class by ID."""
    artifact_class = get_artifact_class(artifact_class_id)

    if artifact_class is None:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact class '{artifact_class_id}' not found in registry",
        )

    return ArtifactClassResponse(
        artifact_class=artifact_class,
        executable_output_supported=False,
        machine_output_supported=False,
    )


@router.get(
    "/by-output/{output_class}",
    response_model=ArtifactClassListResponse,
    summary="Get artifact classes by output type",
    description="Returns all artifact classes for a specific output type.",
)
def get_translation_artifact_classes_by_output(
    output_class: ArtifactOutputClass = Path(
        ..., description="Output class (dxf, svg, neutral_toolpath, gcode, machine_output)"
    ),
) -> ArtifactClassListResponse:
    """Get artifact classes filtered by output class."""
    classes = get_artifact_classes_by_output(output_class)

    return ArtifactClassListResponse(
        artifact_classes=classes,
        count=len(classes),
        executable_artifacts_present=False,
        machine_output_artifacts_present=False,
    )


@router.get(
    "/by-category/{translator_category}",
    response_model=ArtifactClassListResponse,
    summary="Get artifact classes by translator category",
    description="Returns all artifact classes for translators or postprocessors.",
)
def get_translation_artifact_classes_by_category(
    translator_category: Literal["translator", "postprocessor"] = Path(
        ..., description="Translator category (translator or postprocessor)"
    ),
) -> ArtifactClassListResponse:
    """Get artifact classes filtered by translator category."""
    classes = get_artifact_classes_by_category(translator_category)

    return ArtifactClassListResponse(
        artifact_classes=classes,
        count=len(classes),
        executable_artifacts_present=False,
        machine_output_artifacts_present=False,
    )
