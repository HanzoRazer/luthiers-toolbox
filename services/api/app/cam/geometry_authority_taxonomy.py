"""
Geometry Authority Taxonomy

CAM Dev Order 7T: Five-layer geometry authority taxonomy.

Provides:
  - GeometryAuthorityLayer enum
  - Layer definitions with authority rules
  - Layer metadata and constraints

7T invariants:
  - Only canonical_geometry may define design truth
  - All derived layers must reference upstream authority
  - No layer may authorize execution
  - No layer may allow machine output

Core principle:
  Derived geometry may carry provenance.
  Derived geometry may not acquire authority.
"""

from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


GeometryAuthorityLayer = Literal[
    "canonical_geometry",
    "manufacturing_geometry",
    "cognition_geometry",
    "export_geometry",
    "visualization_geometry",
]


class GeometryAuthorityLayerDefinition(BaseModel):
    """
    Definition of a geometry authority layer.

    Each layer has specific authority constraints that determine
    what operations are permitted with geometry at that layer.
    """

    layer: GeometryAuthorityLayer = Field(
        ..., description="Layer identifier"
    )
    display_name: str = Field(
        ..., description="Human-readable layer name"
    )
    description: str = Field(
        default="", description="Layer description"
    )

    owns_design_truth: bool = Field(
        default=False,
        description="Whether this layer owns authoritative design truth"
    )
    derived_layer: bool = Field(
        default=False,
        description="Whether this layer is derived from another"
    )

    may_define_canonical_geometry: bool = Field(
        default=False,
        description="Whether geometry at this layer may define canonical truth"
    )
    may_be_exported: bool = Field(
        default=False,
        description="Whether geometry at this layer may be exported"
    )
    may_be_visualized: bool = Field(
        default=True,
        description="Whether geometry at this layer may be visualized"
    )
    may_be_used_for_strategy: bool = Field(
        default=False,
        description="Whether geometry at this layer may be used for strategy reasoning"
    )

    requires_source_reference: bool = Field(
        default=False,
        description="Whether geometry at this layer requires a source reference"
    )

    allowed_uses: List[str] = Field(
        default_factory=list,
        description="Allowed uses for geometry at this layer"
    )
    prohibited_uses: List[str] = Field(
        default_factory=list,
        description="Prohibited uses for geometry at this layer"
    )

    authority_rank: int = Field(
        default=0,
        description="Authority rank (higher = more authoritative)"
    )


GEOMETRY_AUTHORITY_LAYER_DEFINITIONS: Dict[GeometryAuthorityLayer, GeometryAuthorityLayerDefinition] = {
    "canonical_geometry": GeometryAuthorityLayerDefinition(
        layer="canonical_geometry",
        display_name="Canonical Geometry",
        description="Authoritative design truth owned by IBG/BOE",
        owns_design_truth=True,
        derived_layer=False,
        may_define_canonical_geometry=True,
        may_be_exported=True,
        may_be_visualized=True,
        may_be_used_for_strategy=True,
        requires_source_reference=False,
        allowed_uses=[
            "strategy",
            "workspace",
            "export",
            "translation",
            "visualization",
            "validation",
            "review",
            "canonical_definition",
        ],
        prohibited_uses=[],
        authority_rank=100,
    ),
    "manufacturing_geometry": GeometryAuthorityLayerDefinition(
        layer="manufacturing_geometry",
        display_name="Manufacturing Geometry",
        description="Derived manufacturing interpretation consumed by CAM",
        owns_design_truth=False,
        derived_layer=True,
        may_define_canonical_geometry=False,
        may_be_exported=True,
        may_be_visualized=True,
        may_be_used_for_strategy=True,
        requires_source_reference=True,
        allowed_uses=[
            "strategy",
            "workspace",
            "export",
            "translation",
            "visualization",
            "validation",
            "review",
        ],
        prohibited_uses=[
            "canonical_definition",
            "source_authority",
        ],
        authority_rank=80,
    ),
    "cognition_geometry": GeometryAuthorityLayerDefinition(
        layer="cognition_geometry",
        display_name="Cognition Geometry",
        description="Reasoning abstraction for 7S strategies/workspaces",
        owns_design_truth=False,
        derived_layer=True,
        may_define_canonical_geometry=False,
        may_be_exported=False,
        may_be_visualized=True,
        may_be_used_for_strategy=True,
        requires_source_reference=True,
        allowed_uses=[
            "strategy",
            "workspace",
            "visualization",
            "validation",
            "review",
        ],
        prohibited_uses=[
            "canonical_definition",
            "source_authority",
            "export",
            "translation",
        ],
        authority_rank=60,
    ),
    "export_geometry": GeometryAuthorityLayerDefinition(
        layer="export_geometry",
        display_name="Export Geometry",
        description="Serialized downstream representation for translators/export",
        owns_design_truth=False,
        derived_layer=True,
        may_define_canonical_geometry=False,
        may_be_exported=True,
        may_be_visualized=True,
        may_be_used_for_strategy=False,
        requires_source_reference=True,
        allowed_uses=[
            "export",
            "translation",
            "visualization",
            "review",
        ],
        prohibited_uses=[
            "canonical_definition",
            "source_authority",
            "strategy",
            "workspace",
        ],
        authority_rank=40,
    ),
    "visualization_geometry": GeometryAuthorityLayerDefinition(
        layer="visualization_geometry",
        display_name="Visualization Geometry",
        description="UI/rendering convenience only",
        owns_design_truth=False,
        derived_layer=True,
        may_define_canonical_geometry=False,
        may_be_exported=False,
        may_be_visualized=True,
        may_be_used_for_strategy=False,
        requires_source_reference=True,
        allowed_uses=[
            "visualization",
            "review",
        ],
        prohibited_uses=[
            "canonical_definition",
            "source_authority",
            "strategy",
            "workspace",
            "export",
            "translation",
        ],
        authority_rank=20,
    ),
}


def get_layer_definition(
    layer: GeometryAuthorityLayer,
) -> GeometryAuthorityLayerDefinition:
    """Get the definition for a geometry authority layer."""
    return GEOMETRY_AUTHORITY_LAYER_DEFINITIONS[layer]


def list_layer_definitions() -> List[GeometryAuthorityLayerDefinition]:
    """List all layer definitions in authority order (highest first)."""
    return sorted(
        GEOMETRY_AUTHORITY_LAYER_DEFINITIONS.values(),
        key=lambda d: d.authority_rank,
        reverse=True,
    )


def is_canonical_layer(layer: GeometryAuthorityLayer) -> bool:
    """Check if a layer is the canonical layer."""
    return layer == "canonical_geometry"


def is_derived_layer(layer: GeometryAuthorityLayer) -> bool:
    """Check if a layer is derived (not canonical)."""
    return GEOMETRY_AUTHORITY_LAYER_DEFINITIONS[layer].derived_layer


def layer_may_define_canonical(layer: GeometryAuthorityLayer) -> bool:
    """Check if a layer may define canonical geometry."""
    return GEOMETRY_AUTHORITY_LAYER_DEFINITIONS[layer].may_define_canonical_geometry


def layer_requires_source(layer: GeometryAuthorityLayer) -> bool:
    """Check if a layer requires a source reference."""
    return GEOMETRY_AUTHORITY_LAYER_DEFINITIONS[layer].requires_source_reference


def is_use_allowed(layer: GeometryAuthorityLayer, use: str) -> bool:
    """Check if a use is allowed for a layer."""
    defn = GEOMETRY_AUTHORITY_LAYER_DEFINITIONS[layer]
    if use in defn.prohibited_uses:
        return False
    if defn.allowed_uses and use not in defn.allowed_uses:
        return False
    return True


def is_use_prohibited(layer: GeometryAuthorityLayer, use: str) -> bool:
    """Check if a use is explicitly prohibited for a layer."""
    defn = GEOMETRY_AUTHORITY_LAYER_DEFINITIONS[layer]
    return use in defn.prohibited_uses


def get_authority_rank(layer: GeometryAuthorityLayer) -> int:
    """Get the authority rank of a layer."""
    return GEOMETRY_AUTHORITY_LAYER_DEFINITIONS[layer].authority_rank


def compare_authority(
    layer_a: GeometryAuthorityLayer,
    layer_b: GeometryAuthorityLayer,
) -> int:
    """
    Compare authority of two layers.

    Returns:
        positive if a > b (more authority)
        negative if a < b (less authority)
        0 if equal
    """
    return get_authority_rank(layer_a) - get_authority_rank(layer_b)
