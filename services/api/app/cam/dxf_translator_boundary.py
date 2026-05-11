"""
DXF Translator Boundary Models

CAM Dev Order 6D: Translator boundary alignment without DXF generation.

This module defines the boundary between governed Export Objects and
DXF serialization infrastructure. It validates translator compatibility
without generating any DXF output.

Core rule:
  - DXF is a translator TARGET, not the manufacturing representation
  - Export Object owns manufacturing intent
  - DXF translator owns serialization adaptation
  - No DXF generation in this module

Safety assertions:
  - translator_output_generated: always false
  - dxf_generated: always false
  - No DXF serialization tokens in output
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.cam.export_object import ExportObject


# -----------------------------------------------------------------------------
# DXF Translator Profile (Validation Only)
# -----------------------------------------------------------------------------

class DXFTranslatorProfile(BaseModel):
    """
    Simplified DXF translator profile for compatibility validation.

    This is NOT a production translator config. It contains only the
    fields needed to evaluate export object compatibility with a
    theoretical DXF translator.

    No DXF version. No file settings. No serialization config.
    """
    translator_id: str = Field(..., description="Translator identifier")
    supported_geometry_types: List[str] = Field(
        ...,
        description="Geometry types this translator can handle (line, polyline, arc, spline, etc.)"
    )
    supports_layers: bool = Field(default=True, description="Can organize geometry into layers")
    supports_blocks: bool = Field(default=False, description="Can create block definitions")
    supports_splines: bool = Field(default=False, description="Can handle spline geometry")
    units: Literal["mm", "inch"] = Field(default="mm", description="Expected units")


# -----------------------------------------------------------------------------
# Translator Compatibility Metadata
# -----------------------------------------------------------------------------

class DXFTranslatorMetadata(BaseModel):
    """Metadata about the translator compatibility check."""
    validation_only: bool = True
    risk_class: Literal["A", "B", "C"] = "B"
    translator_class: str = "DXF"
    machine_ready: bool = False


# -----------------------------------------------------------------------------
# Translator Compatibility Report
# -----------------------------------------------------------------------------

class DXFTranslatorCompatibilityReport(BaseModel):
    """
    Result of DXF translator compatibility evaluation.

    This is a REPORT, not DXF output. No serialization occurs.
    """
    compatible: bool = Field(..., description="Overall translator compatibility")
    gate: Literal["green", "yellow", "red"] = Field(..., description="Gate status")

    # Safety assertions — always false in 6D
    translator_output_generated: bool = Field(
        default=False,
        description="Always false — no translator output in 6D"
    )
    dxf_generated: bool = Field(
        default=False,
        description="Always false — no DXF generation in 6D"
    )

    translation_ready: bool = Field(
        ...,
        description="Whether export object is ready for translation (pending translator execution)"
    )

    # Geometry analysis
    geometry_types_detected: List[str] = Field(
        default_factory=list,
        description="Geometry types detected in export object"
    )
    unsupported_geometry: List[str] = Field(
        default_factory=list,
        description="Geometry types not supported by translator"
    )

    # Issues
    warnings: List[str] = Field(default_factory=list, description="YELLOW warnings")
    blocking_issues: List[str] = Field(default_factory=list, description="RED issues")

    # Requirements
    required_translator_features: List[str] = Field(
        default_factory=list,
        description="Translator features required by this export object"
    )

    metadata: DXFTranslatorMetadata = Field(
        default_factory=DXFTranslatorMetadata,
        description="Validation metadata"
    )


# -----------------------------------------------------------------------------
# Request Model
# -----------------------------------------------------------------------------

class DXFTranslatorValidationRequest(BaseModel):
    """Request for DXF translator compatibility check."""
    export_object: ExportObject = Field(..., description="Governed export object from 6B")
    translator_profile: DXFTranslatorProfile = Field(..., description="DXF translator profile")
