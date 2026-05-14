"""
MRP-4A: Translator Capabilities

Capability declarations, categories, and maturity levels for translators.

This module defines the capability metadata that translators declare,
enabling discovery, negotiation, and governance enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TranslatorCategory(str, Enum):
    """Translator category classification."""
    SERIALIZATION = "serialization"      # Geometry to file format (DXF, SVG, STEP)
    VISUALIZATION = "visualization"      # Visual output (PNG, PDF preview)
    MANUFACTURING = "manufacturing"      # CAM-ready output (G-code, toolpaths)
    ARCHIVAL = "archival"                # Long-term storage formats
    ANALYSIS = "analysis"                # Measurement/analysis output


class TranslatorMaturity(str, Enum):
    """Translator maturity level."""
    PLACEHOLDER = "placeholder"          # Registered but not implemented
    EXPERIMENTAL = "experimental"        # Under development, may change
    CANDIDATE = "candidate"              # Feature complete, under validation
    GOVERNED = "governed"                # Production-ready, governed
    DEPRECATED = "deprecated"            # Scheduled for removal


class ExecutionState(str, Enum):
    """Translator execution state."""
    VALIDATION_ONLY = "validation_only"              # Can validate, cannot execute
    GOVERNED_EXECUTION = "governed_execution"        # Full execution authorized
    EXPERIMENTAL = "experimental"                    # Execution allowed, not governed
    EXECUTION_DISABLED = "execution_disabled"        # Explicitly disabled
    DEPRECATED = "deprecated"                        # Will be removed


@dataclass
class TranslatorCapabilities:
    """
    Capability declaration for a translator.

    Declares what a translator CAN do, enabling discovery and negotiation.
    """
    translator_id: str
    translator_name: str
    translator_version: str
    target_format: str
    format_version: Optional[str] = None

    category: TranslatorCategory = TranslatorCategory.SERIALIZATION
    maturity: TranslatorMaturity = TranslatorMaturity.PLACEHOLDER
    execution_state: ExecutionState = ExecutionState.VALIDATION_ONLY

    execution_supported: bool = False
    artifact_generation_supported: bool = False
    machine_output_supported: bool = False
    provenance_supported: bool = True
    deterministic: bool = True

    supported_operations: List[str] = field(default_factory=list)
    supported_geometry_types: List[str] = field(default_factory=list)
    supported_units: List[str] = field(default_factory=lambda: ["mm"])

    description: Optional[str] = None
    notes: Optional[str] = None

    def can_execute(self) -> bool:
        """Check if translator is authorized for execution."""
        return (
            self.execution_state == ExecutionState.GOVERNED_EXECUTION
            and self.execution_supported
        )

    def is_governed(self) -> bool:
        """Check if translator has governed maturity."""
        return self.maturity == TranslatorMaturity.GOVERNED

    def supports_operation(self, operation: str) -> bool:
        """Check if translator supports an operation."""
        return operation in self.supported_operations

    def supports_geometry_type(self, geometry_type: str) -> bool:
        """Check if translator supports a geometry type."""
        return geometry_type in self.supported_geometry_types


# Capability templates for common translator types

def dxf_serialization_capabilities(
    translator_id: str,
    format_version: str,
    execution_supported: bool = True,
) -> TranslatorCapabilities:
    """Create capabilities for a DXF serialization translator."""
    return TranslatorCapabilities(
        translator_id=translator_id,
        translator_name=f"DXF {format_version} Translator",
        translator_version="1.0.0",
        target_format="dxf",
        format_version=format_version,
        category=TranslatorCategory.SERIALIZATION,
        maturity=TranslatorMaturity.GOVERNED,
        execution_state=(
            ExecutionState.GOVERNED_EXECUTION
            if execution_supported
            else ExecutionState.VALIDATION_ONLY
        ),
        execution_supported=execution_supported,
        artifact_generation_supported=execution_supported,
        machine_output_supported=False,
        provenance_supported=True,
        deterministic=True,
        supported_operations=["body_profiling"],
        supported_geometry_types=["closed_contour"],
        supported_units=["mm"],
        description=f"DXF {format_version} geometry translator",
    )


def svg_visualization_capabilities(
    translator_id: str,
    execution_supported: bool = True,
) -> TranslatorCapabilities:
    """Create capabilities for an SVG visualization translator."""
    return TranslatorCapabilities(
        translator_id=translator_id,
        translator_name="SVG Visualization Translator",
        translator_version="1.0.0",
        target_format="svg",
        format_version="1.1",
        category=TranslatorCategory.VISUALIZATION,
        maturity=TranslatorMaturity.GOVERNED,
        execution_state=(
            ExecutionState.GOVERNED_EXECUTION
            if execution_supported
            else ExecutionState.VALIDATION_ONLY
        ),
        execution_supported=execution_supported,
        artifact_generation_supported=execution_supported,
        machine_output_supported=False,
        provenance_supported=True,
        deterministic=True,
        supported_operations=["body_profiling"],
        supported_geometry_types=["closed_contour"],
        supported_units=["mm"],
        description="SVG visualization for Export Objects",
    )
