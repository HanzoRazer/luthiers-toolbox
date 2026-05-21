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
    Create a canonical geometry reference.

    Canonical references own design truth and do not require source references.
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
            "use create_canonical_geometry_reference instead"
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
