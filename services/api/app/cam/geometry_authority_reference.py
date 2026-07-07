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
    ALLOWED_AUTHENTICATION_STATES,
    CanonicalProcessApprovalRecord,
    UNVERIFIED_PENDING_GOVERNANCE,
    VERIFIED_GOVERNED_PROCESS,
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
            "Authenticity status INHERITED from the backing process-approval "
            "record. Fail-safe default: 'unverified_pending_governance'. "
            "'verified_governed_process' is only ever set by inheritance from a "
            "governed CanonicalProcessApprovalRecord whose approver cleared the "
            "authorization anchor; the model validator refuses a verified reference "
            "that lacks complete backing process-approval metadata, so it cannot be "
            "asserted directly. The anchor ships EMPTY (fail-closed), so today no "
            "reference carries verified; a caller must never treat an unverified "
            "reference as authenticated canonical authority."
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

        if self.authentication not in ALLOWED_AUTHENTICATION_STATES:
            raise ValueError(
                f"authentication '{self.authentication}' is not a permitted "
                "authenticity state; legal values are "
                f"{sorted(ALLOWED_AUTHENTICATION_STATES)}. The verified state is "
                "minted only by the authorization anchor at approval-record "
                "creation and inherited here; references cannot assert it directly."
            )

        # A verified reference must be a genuine inheritance from a governed
        # approval record, not a naked hand-set flag. The reference does not carry
        # approver identity, so it cannot re-run the authorization anchor itself
        # (that lock lives on CanonicalProcessApprovalRecord, the only mint path);
        # what it CAN require is that the complete backing process-approval
        # metadata is present. This refuses a directly-constructed reference that
        # claims 'verified_governed_process' with no record behind it.
        if self.authentication == VERIFIED_GOVERNED_PROCESS:
            required_backing = {
                "process_approval_record_id": self.process_approval_record_id,
                "process_approval_record_hash": self.process_approval_record_hash,
                "canonical_process_id": self.canonical_process_id,
                "canonical_process_version": self.canonical_process_version,
                "governed_approval_event_id": self.governed_approval_event_id,
                "process_source_geometry_id": self.process_source_geometry_id,
            }
            missing = sorted(name for name, value in required_backing.items() if not value)
            if missing:
                raise ValueError(
                    "authentication 'verified_governed_process' requires complete "
                    f"backing process-approval metadata; missing {missing}. A verified "
                    "reference must inherit its authentication from a governed "
                    "CanonicalProcessApprovalRecord via "
                    "create_process_approved_canonical_geometry_reference(); it cannot "
                    "be asserted directly on a reference."
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
        process_metadata = {
            "process_approval_record_id": self.process_approval_record_id,
            "process_approval_record_hash": self.process_approval_record_hash,
            "canonical_process_id": self.canonical_process_id,
            "canonical_process_version": self.canonical_process_version,
            "governed_approval_event_id": self.governed_approval_event_id,
            "process_source_geometry_id": self.process_source_geometry_id,
            "authentication": self.authentication,
        }
        if any(process_metadata.values()):
            hash_input["process_approval"] = process_metadata
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


# --- Reference factories -----------------------------------------------------
# The reference-construction factories are split into
# ``geometry_authority_reference_factories.py`` to keep this module within the
# file-size budget, and re-exported here so importers of this module are
# unaffected. This import MUST stay at the bottom: the factories module imports
# ``GeometryAuthorityReference`` (defined above), so the cycle resolves only when
# entry happens through this module — which is the sole supported import path.
from app.cam.geometry_authority_reference_factories import (  # noqa: E402
    create_canonical_geometry_reference,
    create_process_approved_canonical_geometry_reference,
    create_derived_geometry_reference,
    create_manufacturing_geometry_reference,
    create_cognition_geometry_reference,
    create_export_geometry_reference,
    create_visualization_geometry_reference,
)

__all__ = [
    "GeometryUse",
    "GeometryAuthorityReference",
    "create_canonical_geometry_reference",
    "create_process_approved_canonical_geometry_reference",
    "create_derived_geometry_reference",
    "create_manufacturing_geometry_reference",
    "create_cognition_geometry_reference",
    "create_export_geometry_reference",
    "create_visualization_geometry_reference",
]
