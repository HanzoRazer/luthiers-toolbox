"""
Geometry Authority Reference — Factories

CAM Dev Order 7T reference-construction helpers, split out of
``geometry_authority_reference.py`` to keep that module within the file-size
budget. Every factory here is re-exported from ``geometry_authority_reference``
(bottom of that module), so importers of the reference module are unaffected —
this file is not intended to be imported directly.

Dependency direction is one-way: this module imports the
``GeometryAuthorityReference`` model from the reference module; the reference
module only re-exports these names at the very bottom (after the model is
defined), so the import cycle is entered exclusively through the reference
module and resolves safely.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.cam.geometry_authority_taxonomy import (
    GeometryAuthorityLayer,
    get_layer_definition,
    is_canonical_layer,
)
from app.cam.canonical_geometry_process_approval import (
    CanonicalProcessApprovalRecord,
    validate_canonical_process_approval_record,
)

# NOTE: ``GeometryAuthorityReference`` is imported LAZILY inside the constructing
# factories (not at module top) on purpose. The reference module re-exports these
# factories at its bottom, so a top-level import here would form a module-load
# cycle that breaks when this module is imported first. A function-local import
# resolves after both modules are defined, making this module import-safe in any
# order.


def create_canonical_geometry_reference(
    owning_domain: str,
    source_authority: str,
    provenance_hash: Optional[str] = None,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> GeometryAuthorityReference:
    """
    LEGACY / UNAPPROVED canonical reference — NOT a normal creation path.

    Creates a canonical reference WITHOUT a process-approval record. Under the
    C2 process-exclusive ruling (RATIFIED 2026-07-04), canonical authority is
    created only by the approved canonical process following a governed approval
    event — so a reference from this factory carries NO process-approval metadata
    and will raise a transition-state *warning* during validation (still not a RED
    gate; the strict RED flip remains deferred).

    RETIRED for runtime/API creation (GOV-CONVERGE-007-A): the HTTP path
    ``POST /references/canonical`` now returns 410 and does not call this factory.
    Use ``create_process_approved_canonical_geometry_reference()`` for any real
    canonical geometry. This factory is retained ONLY for explicit legacy /
    transition-warning tests; do NOT use it as a normal fixture path.
    """
    layer_def = get_layer_definition("canonical_geometry")

    from app.cam.geometry_authority_reference import GeometryAuthorityReference

    ref = GeometryAuthorityReference(
        authority_layer="canonical_geometry",
        owning_domain=owning_domain,
        source_authority=source_authority,
        provenance_hash=provenance_hash,
        allowed_uses=layer_def.allowed_uses,  # type: ignore
        may_define_canonical_geometry=True,
        description=description,
        metadata=metadata or {"layer": "canonical"},
    )
    ref.deterministic_reference_hash = ref.compute_hash()
    return ref


def create_process_approved_canonical_geometry_reference(
    approval_record: CanonicalProcessApprovalRecord,
    owning_domain: str,
    source_authority: str = "canonical_process",
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> GeometryAuthorityReference:
    """
    Create a canonical geometry reference backed by a governed process-approval
    record (C2 process-exclusive ruling — PROPOSED).

    The reference's canonical authority is evidenced by the approval record, not
    by its owning domain, format, route, or storage location. Representation-only
    source claims are not accepted: the approval record's ``provenance_hash``
    must point at the actual upstream geometry source.

    Behaviour:
      - Produces ``authority_layer="canonical_geometry"``.
      - Sets ``may_define_canonical_geometry=True``.
      - Copies process-approval metadata onto the reference.
      - Carries ``provenance_hash`` from the approval record.
      - Does NOT authorize execution or machine output (7T invariants hold).
    """
    approval_valid, approval_reason = validate_canonical_process_approval_record(
        approval_record
    )
    if not approval_valid:
        raise ValueError(
            "Invalid canonical process approval record: "
            f"{approval_reason or 'unknown validation failure'}"
        )

    record_hash = approval_record.compute_hash()

    layer_def = get_layer_definition("canonical_geometry")

    from app.cam.geometry_authority_reference import GeometryAuthorityReference

    ref = GeometryAuthorityReference(
        authority_layer="canonical_geometry",
        owning_domain=owning_domain,
        source_authority=source_authority,
        provenance_hash=approval_record.provenance_hash,
        allowed_uses=layer_def.allowed_uses,  # type: ignore
        may_define_canonical_geometry=True,
        description=description,
        metadata=metadata or {"layer": "canonical", "authority_origin": "process_approved"},
        process_approval_record_id=approval_record.approval_record_id,
        process_approval_record_hash=record_hash,
        canonical_process_id=approval_record.canonical_process_id,
        canonical_process_version=approval_record.canonical_process_version,
        governed_approval_event_id=approval_record.governed_approval_event_id,
        process_source_geometry_id=approval_record.source_geometry_id,
        authentication=approval_record.authentication,
    )
    ref.deterministic_reference_hash = ref.compute_hash()
    return ref


def create_derived_geometry_reference(
    authority_layer: GeometryAuthorityLayer,
    source_geometry_id: str,
    owning_domain: str,
    source_authority: Optional[str] = None,
    derived_from: Optional[List[str]] = None,
    provenance_hash: Optional[str] = None,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> GeometryAuthorityReference:
    """
    Create a derived geometry reference.

    Derived references require source references and cannot define canonical truth.
    """
    if is_canonical_layer(authority_layer):
        raise ValueError(
            "Cannot create derived reference for canonical_geometry layer — "
            "use create_process_approved_canonical_geometry_reference instead"
        )

    layer_def = get_layer_definition(authority_layer)

    from app.cam.geometry_authority_reference import GeometryAuthorityReference

    ref = GeometryAuthorityReference(
        authority_layer=authority_layer,
        source_geometry_id=source_geometry_id,
        derived_from=derived_from or [],
        owning_domain=owning_domain,
        source_authority=source_authority,
        provenance_hash=provenance_hash,
        allowed_uses=layer_def.allowed_uses,  # type: ignore
        prohibited_uses=layer_def.prohibited_uses,
        may_define_canonical_geometry=False,
        description=description,
        metadata=metadata or {"layer": authority_layer},
    )
    ref.deterministic_reference_hash = ref.compute_hash()
    return ref


def create_manufacturing_geometry_reference(
    source_geometry_id: str,
    owning_domain: str = "cam",
    source_authority: Optional[str] = None,
    provenance_hash: Optional[str] = None,
    description: str = "",
) -> GeometryAuthorityReference:
    """Create a manufacturing geometry reference."""
    return create_derived_geometry_reference(
        authority_layer="manufacturing_geometry",
        source_geometry_id=source_geometry_id,
        owning_domain=owning_domain,
        source_authority=source_authority,
        provenance_hash=provenance_hash,
        description=description,
    )


def create_cognition_geometry_reference(
    source_geometry_id: str,
    owning_domain: str = "cam",
    source_authority: Optional[str] = None,
    provenance_hash: Optional[str] = None,
    description: str = "",
) -> GeometryAuthorityReference:
    """Create a cognition geometry reference for 7S strategy/workspace use."""
    return create_derived_geometry_reference(
        authority_layer="cognition_geometry",
        source_geometry_id=source_geometry_id,
        owning_domain=owning_domain,
        source_authority=source_authority,
        provenance_hash=provenance_hash,
        description=description,
    )


def create_export_geometry_reference(
    source_geometry_id: str,
    owning_domain: str = "export",
    source_authority: Optional[str] = None,
    provenance_hash: Optional[str] = None,
    description: str = "",
) -> GeometryAuthorityReference:
    """Create an export geometry reference."""
    return create_derived_geometry_reference(
        authority_layer="export_geometry",
        source_geometry_id=source_geometry_id,
        owning_domain=owning_domain,
        source_authority=source_authority,
        provenance_hash=provenance_hash,
        description=description,
    )


def create_visualization_geometry_reference(
    source_geometry_id: str,
    owning_domain: str = "ui",
    source_authority: Optional[str] = None,
    provenance_hash: Optional[str] = None,
    description: str = "",
) -> GeometryAuthorityReference:
    """Create a visualization geometry reference."""
    return create_derived_geometry_reference(
        authority_layer="visualization_geometry",
        source_geometry_id=source_geometry_id,
        owning_domain=owning_domain,
        source_authority=source_authority,
        provenance_hash=provenance_hash,
        description=description,
    )
