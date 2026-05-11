"""
Governed Export Lifecycle Orchestrator

CAM Dev Order 6E: End-to-end lifecycle validation without output generation.

This module orchestrates the complete governed export lifecycle:
  Preview → Export Object → Postprocessor Compatibility → Translator Compatibility

It is ORCHESTRATION, not EXECUTION. No output is generated.

Core rule:
  - Coordinates validation across all layers
  - Propagates gates (RED > YELLOW > GREEN)
  - No DXF generation
  - No G-code generation
  - No machine output
  - No RMOS persistence

Safety assertions:
  - machine_output_generated: always false
  - translator_output_generated: always false
  - machine_ready: always false
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.cam.dxf_translator_boundary import DXFTranslatorProfile
from app.cam.export_object import ExportObject
from app.cam.export_object_to_dxf_adapter import evaluate_dxf_translator_compatibility
from app.cam.nut_slot_cam import NutSlotPreviewRequest, generate_nut_slot_preview
from app.cam.nut_slot_export import create_nut_slot_export_object
from app.cam.postprocessor_boundary import (
    MachineProfileValidationOnly,
    evaluate_postprocessor_compatibility,
)


# -----------------------------------------------------------------------------
# Supported Operations
# -----------------------------------------------------------------------------

SUPPORTED_OPERATIONS = ["nut_slot"]


# -----------------------------------------------------------------------------
# Lifecycle Models
# -----------------------------------------------------------------------------

class PreviewRequestWrapper(BaseModel):
    """Wrapper for preview request with operation type."""
    operation: str = Field(..., description="Operation type (e.g., 'nut_slot')")
    payload: Dict[str, Any] = Field(..., description="Preview request payload")


class GovernedExportLifecycleRequest(BaseModel):
    """Request for governed export lifecycle validation."""
    preview_request: PreviewRequestWrapper = Field(..., description="Preview request with operation type")
    machine_profile: MachineProfileValidationOnly = Field(..., description="Machine profile for compatibility")
    translator_profile: DXFTranslatorProfile = Field(..., description="Translator profile for compatibility")


class ExportObjectSummary(BaseModel):
    """Lightweight summary of export object (not full object)."""
    export_id: str
    operation: str
    toolpath_count: int
    entity_count: int
    units: str


class LifecycleMetadata(BaseModel):
    """Metadata about the lifecycle validation."""
    validation_only: bool = True
    risk_class: Literal["A", "B", "C"] = "B"
    governed_export_pipeline: bool = True


class GovernedExportLifecycleReport(BaseModel):
    """
    Aggregated result of governed export lifecycle validation.

    This is a VALIDATION REPORT, not output generation.
    """
    lifecycle_gate: Literal["green", "yellow", "red"] = Field(
        ..., description="Aggregated lifecycle gate"
    )
    export_ready: bool = Field(
        ..., description="Whether export object can be created"
    )
    machine_ready: bool = Field(
        default=False,
        description="Always false in 6E — no machine execution"
    )
    translator_ready: bool = Field(
        ..., description="Whether translator compatibility valid"
    )

    # Safety assertions — always false
    machine_output_generated: bool = Field(
        default=False,
        description="Always false — no machine output in 6E"
    )
    translator_output_generated: bool = Field(
        default=False,
        description="Always false — no translator output in 6E"
    )

    # Results from each layer
    preview_gate: Literal["green", "yellow", "red"] = Field(
        ..., description="Preview gate status"
    )
    preview_operation: str = Field(..., description="Operation type")

    export_object_summary: Optional[ExportObjectSummary] = Field(
        None, description="Summary of export object (if created)"
    )

    machine_validation_gate: Optional[Literal["green", "yellow", "red"]] = Field(
        None, description="Machine compatibility gate"
    )
    machine_validation_compatible: Optional[bool] = Field(
        None, description="Machine compatibility result"
    )

    translator_validation_gate: Optional[Literal["green", "yellow", "red"]] = Field(
        None, description="Translator compatibility gate"
    )
    translator_validation_compatible: Optional[bool] = Field(
        None, description="Translator compatibility result"
    )

    # Issues
    blocking_issues: List[str] = Field(default_factory=list, description="RED issues")
    warnings: List[str] = Field(default_factory=list, description="YELLOW warnings")

    metadata: LifecycleMetadata = Field(
        default_factory=LifecycleMetadata,
        description="Validation metadata"
    )


# -----------------------------------------------------------------------------
# Gate Propagation
# -----------------------------------------------------------------------------

def propagate_gate(*gates: str) -> str:
    """
    Propagate gate status with precedence: RED > YELLOW > GREEN.

    Returns the most severe gate status.
    """
    if "red" in gates:
        return "red"
    if "yellow" in gates:
        return "yellow"
    return "green"


# -----------------------------------------------------------------------------
# Preview Dispatcher
# -----------------------------------------------------------------------------

def dispatch_preview(
    operation: str,
    payload: Dict[str, Any],
) -> tuple[Any, str, List[str], List[str]]:
    """
    Dispatch preview request to appropriate generator.

    Returns (preview_response, gate, errors, warnings).
    """
    if operation not in SUPPORTED_OPERATIONS:
        return None, "red", [f"Unsupported lifecycle operation: {operation}"], []

    if operation == "nut_slot":
        try:
            request = NutSlotPreviewRequest(**payload)
            preview = generate_nut_slot_preview(request)
            return (
                preview,
                preview.gate.value,
                list(preview.errors),
                list(preview.warnings),
            )
        except Exception as e:
            return None, "red", [f"Preview generation failed: {str(e)}"], []

    return None, "red", [f"Operation '{operation}' not implemented"], []


# -----------------------------------------------------------------------------
# Export Object Builder Dispatcher
# -----------------------------------------------------------------------------

def dispatch_export_object(
    operation: str,
    preview: Any,
    payload: Dict[str, Any],
) -> tuple[Optional[ExportObject], List[str]]:
    """
    Dispatch export object creation to appropriate builder.

    Returns (export_object, errors).
    """
    if operation == "nut_slot":
        try:
            request = NutSlotPreviewRequest(**payload)
            export_obj = create_nut_slot_export_object(preview, request)
            return export_obj, []
        except Exception as e:
            return None, [f"Export object creation failed: {str(e)}"]

    return None, [f"Export object builder not implemented for '{operation}'"]


# -----------------------------------------------------------------------------
# Main Orchestration Function
# -----------------------------------------------------------------------------

def run_governed_export_lifecycle(
    request: GovernedExportLifecycleRequest,
) -> GovernedExportLifecycleReport:
    """
    Run the complete governed export lifecycle validation.

    Flow:
      1. Generate governed preview
      2. Validate preview gate
      3. Build export object (if preview not RED)
      4. Run postprocessor compatibility validation
      5. Run translator compatibility validation
      6. Aggregate lifecycle report
      7. Propagate lifecycle gate

    No serialization. No persistence. No output generation.
    """
    blocking_issues = []
    warnings = []
    gates = []

    operation = request.preview_request.operation
    payload = request.preview_request.payload

    # --- Step 1: Generate governed preview ---
    preview, preview_gate, preview_errors, preview_warnings = dispatch_preview(
        operation, payload
    )
    gates.append(preview_gate)
    blocking_issues.extend(preview_errors)
    warnings.extend(preview_warnings)

    # --- Step 2: Check preview gate ---
    export_object = None
    export_summary = None

    if preview_gate != "red" and preview is not None:
        # --- Step 3: Build export object ---
        export_object, export_errors = dispatch_export_object(
            operation, preview, payload
        )
        if export_errors:
            blocking_issues.extend(export_errors)
            gates.append("red")
        elif export_object:
            export_summary = ExportObjectSummary(
                export_id=export_object.export_id,
                operation=export_object.intent.operation_type,
                toolpath_count=len(export_object.toolpaths.operations),
                entity_count=len(export_object.geometry.entities),
                units=export_object.geometry.coordinate_system.units,
            )

    # --- Step 4: Machine compatibility validation ---
    machine_gate = None
    machine_compatible = None

    if export_object is not None:
        machine_report = evaluate_postprocessor_compatibility(
            export_object, request.machine_profile
        )
        machine_gate = machine_report.gate
        machine_compatible = machine_report.compatible
        gates.append(machine_gate)

        if machine_report.blocking_issues:
            blocking_issues.extend(
                [f"[Machine] {issue}" for issue in machine_report.blocking_issues]
            )
        if machine_report.warnings:
            warnings.extend(
                [f"[Machine] {warning}" for warning in machine_report.warnings]
            )

    # --- Step 5: Translator compatibility validation ---
    translator_gate = None
    translator_compatible = None

    if export_object is not None:
        translator_report = evaluate_dxf_translator_compatibility(
            export_object, request.translator_profile
        )
        translator_gate = translator_report.gate
        translator_compatible = translator_report.compatible
        gates.append(translator_gate)

        if translator_report.blocking_issues:
            blocking_issues.extend(
                [f"[Translator] {issue}" for issue in translator_report.blocking_issues]
            )
        if translator_report.warnings:
            warnings.extend(
                [f"[Translator] {warning}" for warning in translator_report.warnings]
            )

    # --- Step 6: Aggregate lifecycle gate ---
    lifecycle_gate = propagate_gate(*gates)

    # --- Step 7: Determine readiness ---
    export_ready = (
        preview_gate != "red"
        and export_object is not None
    )
    translator_ready = translator_compatible is True

    return GovernedExportLifecycleReport(
        lifecycle_gate=lifecycle_gate,
        export_ready=export_ready,
        machine_ready=False,  # Always false in 6E
        translator_ready=translator_ready,
        machine_output_generated=False,  # Always false
        translator_output_generated=False,  # Always false
        preview_gate=preview_gate,
        preview_operation=operation,
        export_object_summary=export_summary,
        machine_validation_gate=machine_gate,
        machine_validation_compatible=machine_compatible,
        translator_validation_gate=translator_gate,
        translator_validation_compatible=translator_compatible,
        blocking_issues=blocking_issues,
        warnings=warnings,
        metadata=LifecycleMetadata(
            validation_only=True,
            risk_class="B",
            governed_export_pipeline=True,
        ),
    )
