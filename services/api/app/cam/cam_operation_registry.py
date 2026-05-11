"""
CAM Operation Capability Registry

CAM Dev Order 6H: Operation self-description and lifecycle introspection.

This module provides a governed capability registry where CAM operations
declare their lifecycle semantics explicitly.

Core principle:
  Operations are self-describing governed capabilities, NOT implicit router behavior.

The registry becomes the canonical source of truth for:
  - Lifecycle support
  - Exportability classification
  - Translator requirements
  - Machine capability requirements
  - RMOS eligibility
  - Governance maturity

Safety assertions:
  - machine_ready: always false in 6H
  - machine_output_supported: always false in 6H
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Capability Models
# -----------------------------------------------------------------------------

ExportabilityClass = Literal[
    "preview_only",
    "governed_export",
    "translator_ready",
    "machine_candidate",
]

MaturityLevel = Literal[
    "experimental",
    "candidate",
    "governed",
    "canonical",
]


class CAMOperationCapability(BaseModel):
    """
    Self-description schema for a CAM operation's lifecycle capabilities.

    This declares what an operation supports in the governed export pipeline,
    NOT what it executes. Capability declaration is separate from execution.
    """

    # --- Identity ---
    operation: str = Field(..., description="Operation identifier (e.g., 'nut_slot', 'drilling')")

    # --- Lifecycle Support Flags ---
    lifecycle_supported: bool = Field(
        ..., description="Whether operation is supported by lifecycle orchestrator"
    )
    export_object_supported: bool = Field(
        ..., description="Whether export object generation is supported"
    )
    machine_validation_supported: bool = Field(
        ..., description="Whether machine compatibility validation is supported"
    )
    translator_validation_supported: bool = Field(
        ..., description="Whether translator compatibility validation is supported"
    )
    rmos_persistence_supported: bool = Field(
        ..., description="Whether RMOS artifact persistence is supported"
    )

    # --- Routes ---
    preview_route: Optional[str] = Field(
        None, description="Preview endpoint path"
    )
    lifecycle_route: Optional[str] = Field(
        None, description="Lifecycle validation endpoint path"
    )

    # --- Classification ---
    exportability_class: ExportabilityClass = Field(
        ..., description="Export capability classification"
    )
    maturity: MaturityLevel = Field(
        ..., description="Governance maturity level"
    )

    # --- Requirements (semantic descriptors, not enforced in 6H) ---
    required_machine_capabilities: List[str] = Field(
        default_factory=list,
        description="Machine capabilities required for this operation (semantic only)"
    )
    required_translator_features: List[str] = Field(
        default_factory=list,
        description="Translator features required for this operation"
    )
    supported_geometry_types: List[str] = Field(
        default_factory=list,
        description="Geometry types this operation produces"
    )

    # --- Safety Assertions (always false in 6H) ---
    machine_ready: bool = Field(
        default=False,
        description="Always false in 6H — no machine execution"
    )
    machine_output_supported: bool = Field(
        default=False,
        description="Always false in 6H — no machine output generation"
    )

    # --- Documentation ---
    notes: Optional[str] = Field(
        None, description="Additional notes about this operation"
    )


# -----------------------------------------------------------------------------
# Canonical Registry
# -----------------------------------------------------------------------------

CAM_OPERATION_REGISTRY: Dict[str, CAMOperationCapability] = {
    "nut_slot": CAMOperationCapability(
        operation="nut_slot",
        lifecycle_supported=True,
        export_object_supported=True,
        machine_validation_supported=True,
        translator_validation_supported=True,
        rmos_persistence_supported=True,
        preview_route="/api/cam/nut-slot/preview",
        lifecycle_route="/api/cam/export/lifecycle/validate",
        exportability_class="governed_export",
        maturity="canonical",
        required_machine_capabilities=[
            "3_axis_motion",
            "controlled_plunge",
            "linear_interpolation",
        ],
        required_translator_features=[
            "polyline_support",
            "line_support",
        ],
        supported_geometry_types=[
            "line",
            "polyline",
        ],
        machine_ready=False,
        machine_output_supported=False,
        notes="Nut slot cutting for string instruments. Governed preview since 5C.",
    ),
    "drilling": CAMOperationCapability(
        operation="drilling",
        lifecycle_supported=True,
        export_object_supported=True,
        machine_validation_supported=True,
        translator_validation_supported=True,
        rmos_persistence_supported=True,
        preview_route="/api/cam/drilling/preview",
        lifecycle_route="/api/cam/export/lifecycle/validate",
        exportability_class="governed_export",
        maturity="canonical",
        required_machine_capabilities=[
            "3_axis_motion",
            "controlled_plunge",
            "z_axis_motion",
            "hole_positioning",
        ],
        required_translator_features=[
            "circle_support",
        ],
        supported_geometry_types=[
            "circle",
        ],
        machine_ready=False,
        machine_output_supported=False,
        notes="Drilling operations. Governed preview since 5E, lifecycle since 6G.",
    ),
}


# -----------------------------------------------------------------------------
# Registry Helper Functions
# -----------------------------------------------------------------------------

def get_operation_capability(operation: str) -> Optional[CAMOperationCapability]:
    """
    Get capability declaration for an operation.

    Args:
        operation: Operation identifier

    Returns:
        CAMOperationCapability if registered, None otherwise
    """
    return CAM_OPERATION_REGISTRY.get(operation)


def list_supported_operations() -> List[str]:
    """
    List all registered operation identifiers.

    Returns:
        List of operation names in the registry
    """
    return list(CAM_OPERATION_REGISTRY.keys())


def list_governed_operations() -> List[str]:
    """
    List operations with maturity level 'governed' or 'canonical'.

    Returns:
        List of operation names that are governed or canonical
    """
    return [
        op
        for op, cap in CAM_OPERATION_REGISTRY.items()
        if cap.maturity in ("governed", "canonical")
    ]


def list_lifecycle_supported_operations() -> List[str]:
    """
    List operations that support lifecycle orchestration.

    This is the canonical source for lifecycle dispatcher.

    Returns:
        List of operation names with lifecycle_supported=True
    """
    return [
        op
        for op, cap in CAM_OPERATION_REGISTRY.items()
        if cap.lifecycle_supported
    ]


def list_exportable_operations() -> List[str]:
    """
    List operations that support export object generation.

    Returns:
        List of operation names with export_object_supported=True
    """
    return [
        op
        for op, cap in CAM_OPERATION_REGISTRY.items()
        if cap.export_object_supported
    ]


def get_all_capabilities() -> List[CAMOperationCapability]:
    """
    Get all registered operation capabilities.

    Returns:
        List of all CAMOperationCapability entries
    """
    return list(CAM_OPERATION_REGISTRY.values())
