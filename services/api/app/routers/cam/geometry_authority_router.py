"""
Geometry Authority Router

CAM Dev Order 7T: HTTP endpoints for geometry authority reference contracts.

Provides endpoints for:
  - Layer taxonomy inspection
  - Reference registration and lookup
  - Validation
  - CI summary

7T invariants:
  - No endpoint authorizes execution
  - No endpoint allows machine output
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.geometry_authority_taxonomy import (
    GeometryAuthorityLayer,
    GeometryAuthorityLayerDefinition,
    get_layer_definition,
    list_layer_definitions,
)
from app.cam.geometry_authority_reference import (
    GeometryAuthorityReference,
    GeometryUse,
    create_canonical_geometry_reference,
    create_process_approved_canonical_geometry_reference,
    create_cognition_geometry_reference,
    create_derived_geometry_reference,
    create_export_geometry_reference,
    create_manufacturing_geometry_reference,
    create_visualization_geometry_reference,
)
from app.cam.canonical_geometry_process_approval import (
    CanonicalProcessApprovalError,
    create_canonical_process_approval_record,
)
from app.cam.geometry_authority_validation import (
    GeometryAuthorityValidationResult,
    validate_canonical_process_authority,
)
from app.cam.geometry_authority_registry import (
    get_ci_summary,
    get_geometry_authority_reference,
    get_validation_for_reference,
    get_validation_result,
    list_geometry_authority_references,
    list_references_by_layer,
    list_references_by_source,
    list_validations,
    register_geometry_authority_reference,
    validate_reference,
)


router = APIRouter(
    prefix="/api/cam/geometry-authority",
    tags=["CAM", "Geometry", "Authority"],
)


class GeometryAuthorityMeta(BaseModel):
    """Metadata for Geometry Authority API."""

    version: str = "7T"
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    description: str = "Geometry authority reference contracts — no execution"


@router.get("/", response_model=GeometryAuthorityMeta)
async def get_meta() -> GeometryAuthorityMeta:
    """Get Geometry Authority API metadata."""
    return GeometryAuthorityMeta()


# ============================================================================
# LAYER TAXONOMY ENDPOINTS
# ============================================================================


@router.get("/layers", response_model=List[GeometryAuthorityLayerDefinition])
async def list_layers() -> List[GeometryAuthorityLayerDefinition]:
    """List all geometry authority layers in authority order."""
    return list_layer_definitions()


@router.get("/layers/{layer}", response_model=GeometryAuthorityLayerDefinition)
async def get_layer(layer: GeometryAuthorityLayer) -> GeometryAuthorityLayerDefinition:
    """Get a specific layer definition."""
    try:
        return get_layer_definition(layer)
    except KeyError:
        raise HTTPException(404, f"Layer '{layer}' not found")


# ============================================================================
# REFERENCE ENDPOINTS
# ============================================================================


class CreateCanonicalReferenceRequest(BaseModel):
    """Request to create a legacy/unapproved canonical geometry reference."""

    owning_domain: str = Field(..., description="Domain that owns this geometry")
    source_authority: str = Field(..., description="Authority that defined the geometry")
    provenance_hash: Optional[str] = None
    description: str = ""
    metadata: Optional[Dict[str, Any]] = None


class CreateCanonicalProcessApprovalRequest(BaseModel):
    """Request body for a governed canonical-process approval record."""

    canonical_process_id: str
    canonical_process_version: str
    governed_approval_event_id: str
    approval_rule_id: str
    source_geometry_id: str
    provenance_hash: str
    process_inputs_hash: str
    approver_id: str
    source_geometry_role: str = "evidence"
    source_authority_state: str = "governed_evidence_candidate"
    approver_role: str = "reviewer"
    output_geometry_id: Optional[str] = None
    notes: str = ""
    metadata: Optional[Dict[str, Any]] = None


class CreateProcessApprovedCanonicalReferenceRequest(BaseModel):
    """Request to create a process-approved canonical geometry reference."""

    owning_domain: str = Field(..., description="Domain that owns this geometry")
    source_authority: str = "canonical_process"
    approval_record: CreateCanonicalProcessApprovalRequest
    description: str = ""
    metadata: Optional[Dict[str, Any]] = None


class CreateDerivedReferenceRequest(BaseModel):
    """Request to create a derived geometry reference."""

    authority_layer: GeometryAuthorityLayer = Field(
        ..., description="Layer for this reference"
    )
    source_geometry_id: str = Field(..., description="Source geometry ID")
    owning_domain: str = Field(..., description="Domain that owns this reference")
    source_authority: Optional[str] = None
    derived_from: Optional[List[str]] = None
    provenance_hash: Optional[str] = None
    description: str = ""
    metadata: Optional[Dict[str, Any]] = None


def _has_process_approval_metadata(reference: GeometryAuthorityReference) -> bool:
    """True when raw reference payload carries process-approval fields."""
    return any(
        [
            reference.process_approval_record_id,
            reference.process_approval_record_hash,
            reference.canonical_process_id,
            reference.canonical_process_version,
            reference.governed_approval_event_id,
            reference.process_source_geometry_id,
        ]
    )


@router.post("/references/canonical", response_model=GeometryAuthorityReference)
async def create_canonical_reference(
    request: CreateCanonicalReferenceRequest,
) -> GeometryAuthorityReference:
    """Create and register a legacy/unapproved canonical geometry reference."""
    ref = create_canonical_geometry_reference(
        owning_domain=request.owning_domain,
        source_authority=request.source_authority,
        provenance_hash=request.provenance_hash,
        description=request.description,
        metadata=request.metadata,
    )
    return register_geometry_authority_reference(ref)


@router.post(
    "/references/canonical/process-approved",
    response_model=GeometryAuthorityReference,
)
async def create_process_approved_canonical_reference(
    request: CreateProcessApprovedCanonicalReferenceRequest,
) -> GeometryAuthorityReference:
    """Create and register a process-approved canonical geometry reference."""
    try:
        approval_record = create_canonical_process_approval_record(
            canonical_process_id=request.approval_record.canonical_process_id,
            canonical_process_version=request.approval_record.canonical_process_version,
            governed_approval_event_id=request.approval_record.governed_approval_event_id,
            approval_rule_id=request.approval_record.approval_rule_id,
            source_geometry_id=request.approval_record.source_geometry_id,
            provenance_hash=request.approval_record.provenance_hash,
            process_inputs_hash=request.approval_record.process_inputs_hash,
            approver_id=request.approval_record.approver_id,
            source_geometry_role=request.approval_record.source_geometry_role,
            source_authority_state=request.approval_record.source_authority_state,
            approver_role=request.approval_record.approver_role,
            output_geometry_id=request.approval_record.output_geometry_id,
            notes=request.approval_record.notes,
            metadata=request.approval_record.metadata,
        )
        ref = create_process_approved_canonical_geometry_reference(
            approval_record=approval_record,
            owning_domain=request.owning_domain,
            source_authority=request.source_authority,
            description=request.description,
            metadata=request.metadata,
        )
    except (CanonicalProcessApprovalError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc

    return register_geometry_authority_reference(ref)


@router.post("/references/derived", response_model=GeometryAuthorityReference)
async def create_derived_reference(
    request: CreateDerivedReferenceRequest,
) -> GeometryAuthorityReference:
    """Create and register a derived geometry reference."""
    if request.authority_layer == "canonical_geometry":
        raise HTTPException(
            400,
            "Cannot create canonical reference via derived endpoint — "
            "use /references/canonical/process-approved instead"
        )

    ref = create_derived_geometry_reference(
        authority_layer=request.authority_layer,
        source_geometry_id=request.source_geometry_id,
        owning_domain=request.owning_domain,
        source_authority=request.source_authority,
        derived_from=request.derived_from,
        provenance_hash=request.provenance_hash,
        description=request.description,
        metadata=request.metadata,
    )
    return register_geometry_authority_reference(ref)


@router.post("/references", response_model=GeometryAuthorityReference)
async def register_reference(
    reference: GeometryAuthorityReference,
) -> GeometryAuthorityReference:
    """Register a geometry authority reference directly."""
    if reference.authority_layer == "canonical_geometry" and _has_process_approval_metadata(
        reference
    ):
        canonical_ok, canonical_reason = validate_canonical_process_authority(reference)
        if not canonical_ok:
            raise HTTPException(400, canonical_reason)
        raise HTTPException(
            400,
            "Generic registration cannot verify a canonical process approval record; "
            "use /references/canonical/process-approved so the approval record is "
            "created and validated at the API boundary.",
        )
    return register_geometry_authority_reference(reference)


@router.get("/references", response_model=List[GeometryAuthorityReference])
async def list_references() -> List[GeometryAuthorityReference]:
    """List all registered geometry authority references."""
    return list_geometry_authority_references()


@router.get("/references/{reference_id}", response_model=GeometryAuthorityReference)
async def get_reference(reference_id: str) -> GeometryAuthorityReference:
    """Get a specific reference by ID."""
    ref = get_geometry_authority_reference(reference_id)
    if not ref:
        raise HTTPException(404, f"Reference '{reference_id}' not found")
    return ref


@router.get(
    "/references/by-source/{source_geometry_id}",
    response_model=List[GeometryAuthorityReference],
)
async def get_references_by_source(
    source_geometry_id: str,
) -> List[GeometryAuthorityReference]:
    """List all references derived from a source geometry."""
    return list_references_by_source(source_geometry_id)


@router.get(
    "/references/by-layer/{layer}",
    response_model=List[GeometryAuthorityReference],
)
async def get_references_by_layer(
    layer: GeometryAuthorityLayer,
) -> List[GeometryAuthorityReference]:
    """List all references at a specific authority layer."""
    return list_references_by_layer(layer)


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================


@router.post(
    "/validate/{reference_id}",
    response_model=GeometryAuthorityValidationResult,
)
async def validate_reference_endpoint(
    reference_id: str,
) -> GeometryAuthorityValidationResult:
    """Validate a registered reference."""
    result = validate_reference(reference_id)
    if not result:
        raise HTTPException(404, f"Reference '{reference_id}' not found")
    return result


@router.get(
    "/validations/{validation_id}",
    response_model=GeometryAuthorityValidationResult,
)
async def get_validation(validation_id: str) -> GeometryAuthorityValidationResult:
    """Get a specific validation result by ID."""
    result = get_validation_result(validation_id)
    if not result:
        raise HTTPException(404, f"Validation '{validation_id}' not found")
    return result


@router.get("/validations", response_model=List[GeometryAuthorityValidationResult])
async def list_all_validations() -> List[GeometryAuthorityValidationResult]:
    """List all validation results."""
    return list_validations()


@router.get(
    "/validations/for-reference/{reference_id}",
    response_model=Optional[GeometryAuthorityValidationResult],
)
async def get_validation_for_ref(
    reference_id: str,
) -> Optional[GeometryAuthorityValidationResult]:
    """Get the most recent validation for a reference."""
    return get_validation_for_reference(reference_id)


# ============================================================================
# CI ENDPOINT
# ============================================================================


@router.get("/ci")
async def get_ci_status() -> Dict[str, Any]:
    """
    Get CI summary for geometry authority health.

    Returns:
      - total_references
      - total_validations
      - unvalidated_reference_count
      - green_count
      - yellow_count
      - red_count
      - authority_collapse_count
      - status: pass|warn|fail

    Status:
      - fail: RED validations or authority collapse exists
      - warn: unvalidated refs or YELLOW validations exist
      - pass: all refs have GREEN validation
    """
    return get_ci_summary()
