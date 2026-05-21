"""
Geometry Authority Registry

CAM Dev Order 7T: In-memory registry for geometry authority references.

Provides:
  - Reference registration and lookup
  - Validation integration
  - Index management
  - CI summary generation

7T invariants:
  - No registered reference may authorize execution
  - No registered reference may allow machine output
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from app.cam.geometry_authority_taxonomy import (
    GeometryAuthorityLayer,
    list_layer_definitions,
)
from app.cam.geometry_authority_reference import (
    GeometryAuthorityReference,
)
from app.cam.geometry_authority_validation import (
    GeometryAuthorityValidationResult,
    detect_authority_collapse,
    validate_geometry_authority_reference,
)


GEOMETRY_AUTHORITY_REFERENCE_INDEX: Dict[str, GeometryAuthorityReference] = {}

GEOMETRY_AUTHORITY_VALIDATION_INDEX: Dict[str, GeometryAuthorityValidationResult] = {}

GEOMETRY_REFERENCES_BY_SOURCE_INDEX: Dict[str, List[str]] = {}

GEOMETRY_REFERENCES_BY_LAYER_INDEX: Dict[GeometryAuthorityLayer, List[str]] = {
    "canonical_geometry": [],
    "manufacturing_geometry": [],
    "cognition_geometry": [],
    "export_geometry": [],
    "visualization_geometry": [],
}


def register_geometry_authority_reference(
    reference: GeometryAuthorityReference,
    validate_on_register: bool = True,
) -> GeometryAuthorityReference:
    """
    Register a geometry authority reference.

    Optionally validates on registration and stores the validation result.

    Args:
        reference: Reference to register
        validate_on_register: Whether to validate immediately

    Returns:
        The registered reference
    """
    reference.deterministic_reference_hash = reference.compute_hash()

    GEOMETRY_AUTHORITY_REFERENCE_INDEX[reference.geometry_reference_id] = reference

    layer = reference.authority_layer
    if reference.geometry_reference_id not in GEOMETRY_REFERENCES_BY_LAYER_INDEX[layer]:
        GEOMETRY_REFERENCES_BY_LAYER_INDEX[layer].append(reference.geometry_reference_id)

    if reference.source_geometry_id:
        if reference.source_geometry_id not in GEOMETRY_REFERENCES_BY_SOURCE_INDEX:
            GEOMETRY_REFERENCES_BY_SOURCE_INDEX[reference.source_geometry_id] = []
        if reference.geometry_reference_id not in GEOMETRY_REFERENCES_BY_SOURCE_INDEX[reference.source_geometry_id]:
            GEOMETRY_REFERENCES_BY_SOURCE_INDEX[reference.source_geometry_id].append(
                reference.geometry_reference_id
            )

    if validate_on_register:
        validation = validate_geometry_authority_reference(
            reference,
            source_exists_checker=lambda sid: sid in GEOMETRY_AUTHORITY_REFERENCE_INDEX,
        )
        GEOMETRY_AUTHORITY_VALIDATION_INDEX[validation.validation_id] = validation

    return reference


def get_geometry_authority_reference(
    reference_id: str,
) -> Optional[GeometryAuthorityReference]:
    """Get a geometry authority reference by ID."""
    return GEOMETRY_AUTHORITY_REFERENCE_INDEX.get(reference_id)


def list_geometry_authority_references() -> List[GeometryAuthorityReference]:
    """List all registered geometry authority references."""
    return list(GEOMETRY_AUTHORITY_REFERENCE_INDEX.values())


def list_references_by_source(
    source_geometry_id: str,
) -> List[GeometryAuthorityReference]:
    """List all references derived from a source geometry."""
    ref_ids = GEOMETRY_REFERENCES_BY_SOURCE_INDEX.get(source_geometry_id, [])
    return [
        GEOMETRY_AUTHORITY_REFERENCE_INDEX[rid]
        for rid in ref_ids
        if rid in GEOMETRY_AUTHORITY_REFERENCE_INDEX
    ]


def list_references_by_layer(
    layer: GeometryAuthorityLayer,
) -> List[GeometryAuthorityReference]:
    """List all references at a specific authority layer."""
    ref_ids = GEOMETRY_REFERENCES_BY_LAYER_INDEX.get(layer, [])
    return [
        GEOMETRY_AUTHORITY_REFERENCE_INDEX[rid]
        for rid in ref_ids
        if rid in GEOMETRY_AUTHORITY_REFERENCE_INDEX
    ]


def get_validation_for_reference(
    reference_id: str,
) -> Optional[GeometryAuthorityValidationResult]:
    """Get the most recent validation result for a reference."""
    for validation in GEOMETRY_AUTHORITY_VALIDATION_INDEX.values():
        if validation.geometry_reference_id == reference_id:
            return validation
    return None


def validate_reference(
    reference_id: str,
) -> Optional[GeometryAuthorityValidationResult]:
    """
    Validate a registered reference.

    Args:
        reference_id: ID of reference to validate

    Returns:
        Validation result or None if reference not found
    """
    reference = GEOMETRY_AUTHORITY_REFERENCE_INDEX.get(reference_id)
    if not reference:
        return None

    validation = validate_geometry_authority_reference(
        reference,
        source_exists_checker=lambda sid: sid in GEOMETRY_AUTHORITY_REFERENCE_INDEX,
    )
    GEOMETRY_AUTHORITY_VALIDATION_INDEX[validation.validation_id] = validation

    return validation


def get_validation_result(
    validation_id: str,
) -> Optional[GeometryAuthorityValidationResult]:
    """Get a validation result by ID."""
    return GEOMETRY_AUTHORITY_VALIDATION_INDEX.get(validation_id)


def list_validations() -> List[GeometryAuthorityValidationResult]:
    """List all validation results."""
    return list(GEOMETRY_AUTHORITY_VALIDATION_INDEX.values())


def get_unvalidated_references() -> List[GeometryAuthorityReference]:
    """Get references that have never been validated."""
    validated_ref_ids = {
        v.geometry_reference_id for v in GEOMETRY_AUTHORITY_VALIDATION_INDEX.values()
    }
    return [
        ref for ref in GEOMETRY_AUTHORITY_REFERENCE_INDEX.values()
        if ref.geometry_reference_id not in validated_ref_ids
    ]


CIStatus = Literal["pass", "warn", "fail"]


class GeometryAuthorityCISummary(Dict[str, Any]):
    """CI summary for geometry authority health."""

    pass


def get_ci_summary() -> GeometryAuthorityCISummary:
    """
    Generate CI summary for geometry authority health.

    Returns summary with:
      - total_references
      - total_validations
      - unvalidated_reference_count
      - green_count
      - yellow_count
      - red_count
      - authority_collapse_count
      - status: pass|warn|fail
    """
    total_references = len(GEOMETRY_AUTHORITY_REFERENCE_INDEX)
    total_validations = len(GEOMETRY_AUTHORITY_VALIDATION_INDEX)

    unvalidated = get_unvalidated_references()
    unvalidated_count = len(unvalidated)

    green_count = 0
    yellow_count = 0
    red_count = 0
    authority_collapse_count = 0

    for validation in GEOMETRY_AUTHORITY_VALIDATION_INDEX.values():
        if validation.gate == "green":
            green_count += 1
        elif validation.gate == "yellow":
            yellow_count += 1
        elif validation.gate == "red":
            red_count += 1

        if validation.authority_collapse_detected:
            authority_collapse_count += 1

    status: CIStatus
    if red_count > 0 or authority_collapse_count > 0:
        status = "fail"
    elif unvalidated_count > 0 or yellow_count > 0:
        status = "warn"
    else:
        status = "pass"

    references_by_layer = {
        layer: len(refs)
        for layer, refs in GEOMETRY_REFERENCES_BY_LAYER_INDEX.items()
    }

    return GeometryAuthorityCISummary(
        total_references=total_references,
        total_validations=total_validations,
        unvalidated_reference_count=unvalidated_count,
        unvalidated_reference_ids=[r.geometry_reference_id for r in unvalidated],
        green_count=green_count,
        yellow_count=yellow_count,
        red_count=red_count,
        authority_collapse_count=authority_collapse_count,
        references_by_layer=references_by_layer,
        status=status,
    )


def clear_geometry_authority_indexes() -> None:
    """Clear all indexes (for testing)."""
    GEOMETRY_AUTHORITY_REFERENCE_INDEX.clear()
    GEOMETRY_AUTHORITY_VALIDATION_INDEX.clear()
    GEOMETRY_REFERENCES_BY_SOURCE_INDEX.clear()
    for layer in GEOMETRY_REFERENCES_BY_LAYER_INDEX:
        GEOMETRY_REFERENCES_BY_LAYER_INDEX[layer] = []
