"""
Geometry Authority Reference

CAM Dev Order 7T: Reference contracts for geometry authority tracking.

Provides:
  - GeometryAuthorityReference model
  - Source authority semantics
  - Provenance tracking
  - Use authorization

7T invariants:
  - may_define_canonical_geometry: False for all non-canonical layers
  - may_mutate_source_geometry: always False
  - may_promote_to_canonical: always False
  - machine_output_allowed: always False
  - execution_authorized: always False

Core principle:
  Derived geometry may carry provenance.
  Derived geometry may not acquire authority.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.cam.geometry_authority_taxonomy import (
    GeometryAuthorityLayer,
    get_layer_definition,
    is_canonical_layer,
    layer_may_define_canonical,
    layer_requires_source,
)
from app.cam.canonical_geometry_process_approval import (
    CanonicalProcessApprovalRecord,
    UNVERIFIED_PENDING_GOVERNANCE,
    validate_canonical_process_approval_record,
)


GeometryUse = Literal[
    "strategy",
    "workspace",
    "export",
    "translation",
    "visualization",
    "validation",
    "review",
    "canonical_definition",
    "source_authority",
]


class GeometryAuthorityReference(BaseModel):
    """
    Reference contract for geometry authority tracking.

    Tracks which layer owns a geometry reference, where it came from,
    and what uses are permitted.

    7T invariants (model-enforced):
      - may_mutate_source_geometry: always False
      - may_promote_to_canonical: always False
      - machine_output_allowed: always False
      - execution_authorized: always False
      - may_define_canonical_geometry: False for non-canonical layers
      - derived layers require source_geometry_id or derived_from
    """

    geometry_reference_id: str = Field(
        default_factory=lambda: f"geo-auth-{uuid4().hex[:12]}",
        description="Unique reference identifier"
    )

    authority_layer: GeometryAuthorityLayer = Field(
        ..., description="Which layer this geometry belongs to"
    )

    source_geometry_id: Optional[str] = Field(
        default=None,
        description="ID of the source geometry (required for derived layers)"
    )
    derived_from: List[str] = Field(
        default_factory=list,
        description="List of geometry IDs this was derived from"
    )

    owning_domain: str = Field(
        default="unknown",
        description="Domain that owns this geometry (ibg, boe, cam, export)"
    )
    source_authority: Optional[str] = Field(
        default=None,
        description="Authority that defined the source geometry"
    )

    provenance_hash: Optional[str] = Field(
        default=None,
        description="Hash of the source geometry for provenance tracking"
    )

    # --- C2 process-exclusive canonical authority (PROPOSED / additive) ---
    # These fields are populated only for canonical references that were
    # produced by the approved canonical process following a governed approval
    # event. Their ABSENCE on a canonical reference is a transition-state
    # signal (warning), not — in this PR — a RED gate.
    process_approval_record_id: Optional[str] = Field(
        default=None,
        description="ID of the CanonicalProcessApprovalRecord backing this reference"
    )
    process_approval_record_hash: Optional[str] = Field(
        default=None,
        description="Deterministic hash of the backing process approval record"
    )
    canonical_process_id: Optional[str] = Field(
        default=None,
        description="ID of the approved canonical process that produced this geometry"
    )
    canonical_process_version: Optional[str] = Field(
        default=None,
        description="Version of the approved canonical process"
    )
    governed_approval_event_id: Optional[str] = Field(
        default=None,
        description="ID of the governed approval event that created authority"
    )
    process_source_geometry_id: Optional[str] = Field(
        default=None,
        description="ID of the source/evidence geometry that entered the process"
    )
    authentication: str = Field(
        default=UNVERIFIED_PENDING_GOVERNANCE,
        description=(
            "Authenticity status inherited from the backing process-approval "
            "record. Fail-safe default: 'unverified_pending_governance'. In PR-1 "
            "nothing can carry a verified status (the authorized-approver anchor "
            "is the PR-2 hard prerequisite); a caller must never treat this "
            "reference as authenticated canonical authority while it is unverified."
        )
    )

    allowed_uses: List[GeometryUse] = Field(
        default_factory=list,
        description="Uses permitted for this geometry reference"
    )
    prohibited_uses: List[str] = Field(
        default_factory=list,
        description="Uses explicitly prohibited"
    )

    may_define_canonical_geometry: bool = Field(
        default=False,
        description="Whether this reference may define canonical truth"
    )
    may_mutate_source_geometry: bool = Field(
        default=False,
        description="Always False — references cannot mutate source"
    )
    may_promote_to_canonical: bool = Field(
        default=False,
        description="Always False — derived geometry cannot be promoted"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7T does not allow machine output"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7T does not authorize execution"
    )

    description: str = Field(
        default="",
        description="Human description of this reference"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    deterministic_reference_hash: str = Field(
        default="",
        description="Deterministic hash of reference state"
    )

    @model_validator(mode="after")
    def enforce_7t_invariants(self) -> "GeometryAuthorityReference":
        """
        Enforce 7T invariants:
        - may_mutate_source_geometry must be False
        - may_promote_to_canonical must be False
        - machine_output_allowed must be False
        - execution_authorized must be False
        - may_define_canonical_geometry must be False for non-canonical layers
        - derived layers require source_geometry_id or derived_from
        """
        if self.may_mutate_source_geometry:
            raise ValueError(
                "7T invariant violation: may_mutate_source_geometry must be False — "
                "references cannot mutate source geometry"
            )

        if self.may_promote_to_canonical:
            raise ValueError(
                "7T invariant violation: may_promote_to_canonical must be False — "
                "derived geometry cannot be promoted to canonical"
            )

        if self.machine_output_allowed:
            raise ValueError(
                "7T invariant violation: machine_output_allowed must be False — "
                "7T does not allow machine output"
            )

        if self.execution_authorized:
            raise ValueError(
                "7T invariant violation: execution_authorized must be False — "
                "7T does not authorize execution"
            )

        if not is_canonical_layer(self.authority_layer):
            if self.may_define_canonical_geometry:
                raise ValueError(
                    f"7T invariant violation: may_define_canonical_geometry must be False "
                    f"for non-canonical layer '{self.authority_layer}'"
                )

        if layer_requires_source(self.authority_layer):
            if not self.source_geometry_id and not self.derived_from:
                raise ValueError(
                    f"7T invariant violation: layer '{self.authority_layer}' requires "
                    f"source_geometry_id or derived_from to be set"
                )

        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of reference state."""
        hash_input = {
            "geometry_reference_id": self.geometry_reference_id,
            "authority_layer": self.authority_layer,
            "source_geometry_id": self.source_geometry_id,
            "derived_from": sorted(self.derived_from) if self.derived_from else [],
            "owning_domain": self.owning_domain,
            "provenance_hash": self.provenance_hash,
            "allowed_uses": sorted(self.allowed_uses),
        }
        # Process-approved canonical references bind their identity to the
        # governed approval record. Omitted (None) for legacy/derived
        # references, preserving their existing hashes.
        if self.process_approval_record_id or self.process_approval_record_hash:
            hash_input["process_approval_record_id"] = self.process_approval_record_id
            hash_input["process_approval_record_hash"] = self.process_approval_record_hash
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_canonical_geometry_reference(
    owning_domain: str,
    source_authority: str,
    provenance_hash: Optional[str] = None,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> GeometryAuthorityReference:
    """
    LEGACY / UNAPPROVED canonical reference.

    Creates a canonical reference WITHOUT a process-approval record. Under the
    C2 process-exclusive ruling (PROPOSED), canonical authority is created only
    by the approved canonical process following a governed approval event — so a
    reference from this factory carries NO process-approval metadata and will
    raise a transition-state *warning* during validation (not, in this PR, a RED
    gate).

    Use ``create_process_approved_canonical_geometry_reference()`` for C2
    geometry-origin-compliant body geometry. This factory is retained for
    compatibility with existing call sites and 7T tests until they migrate;
    deprecation / hard blocking is a follow-up (PR 4), not this pass.
    """
    layer_def = get_layer_definition("canonical_geometry")

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

    if approval_record.deterministic_approval_hash:
        record_hash = approval_record.deterministic_approval_hash
    else:
        record_hash = approval_record.compute_hash()

    layer_def = get_layer_definition("canonical_geometry")

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
