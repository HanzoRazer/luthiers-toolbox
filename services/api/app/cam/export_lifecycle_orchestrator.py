"""
Governed Export Lifecycle Orchestrator

CAM Dev Order 6E/6F/6G/6H/6I: End-to-end lifecycle validation with policy enforcement.

This module orchestrates the complete governed export lifecycle:
  Policy → Preview → Export Object → Postprocessor Compatibility → Translator Compatibility

It is ORCHESTRATION, not EXECUTION. No output is generated.

Core rule:
  - Policy engine controls lifecycle stages BEFORE they run
  - Coordinates validation across all layers
  - Propagates gates (RED > YELLOW > GREEN)
  - No DXF generation
  - No G-code generation
  - No machine output

6F additions:
  - Optional RMOS artifact persistence (persist_to_rmos flag)
  - Lightweight export provenance ID (RUN-EXPORT-{uuid})
  - No RunStoreV2 lifecycle coupling

6G additions:
  - Drilling operation support
  - Multi-operation dispatcher pattern

6H additions:
  - Registry-driven operation support
  - Supported operations derived from CAM_OPERATION_REGISTRY
  - Single source of truth for lifecycle capabilities

6I additions:
  - Policy engine integration
  - Stage-level permission enforcement
  - Exportability class enforcement
  - Maturity enforcement
  - RMOS eligibility enforcement

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
from app.cam.routers.drilling.drilling_preview_router import (
    DrillingPreviewRequest,
    generate_drilling_preview,
)
from app.cam.drilling_export import create_drilling_export_object
from app.cam.postprocessor_boundary import (
    MachineProfileValidationOnly,
    evaluate_postprocessor_compatibility,
)
from app.cam.export_rmos_artifacts import (
    RMOSPersistenceResult,
    persist_export_lifecycle_artifacts,
    create_empty_persistence_result,
)
from app.cam.cam_operation_registry import (
    get_operation_capability,
    list_lifecycle_supported_operations,
)
from app.cam.cam_lifecycle_policy_engine import (
    LifecyclePolicyEvaluation,
    evaluate_lifecycle_policy,
)


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
    persist_to_rmos: bool = Field(
        default=False,
        description="If true, persist export object and lifecycle report to RMOS"
    )


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

    # RMOS persistence (6F)
    rmos: Optional[RMOSPersistenceResult] = Field(
        None,
        description="RMOS artifact persistence result (if persist_to_rmos was true)"
    )

    # Policy evaluation (6I)
    policy_evaluation: Optional[LifecyclePolicyEvaluation] = Field(
        None,
        description="Policy engine evaluation result"
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

    Uses CAM_OPERATION_REGISTRY as single source of truth for supported operations.

    Returns (preview_response, gate, errors, warnings).
    """
    # Check registry for lifecycle support (6H)
    capability = get_operation_capability(operation)
    if capability is None or not capability.lifecycle_supported:
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

    if operation == "drilling":
        try:
            request = DrillingPreviewRequest(**payload)
            preview = generate_drilling_preview(request)
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

    if operation == "drilling":
        try:
            request = DrillingPreviewRequest(**payload)
            export_obj = create_drilling_export_object(preview, request)
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

    Flow (6I policy-governed):
      0. Evaluate lifecycle policy (6I)
      1. If policy RED: return early with lifecycle-shaped report
      2. Generate governed preview (if preview_allowed)
      3. Build export object (if export_object_allowed and preview GREEN)
      4. Run machine compatibility validation (if machine_validation_allowed)
      5. Run translator compatibility validation (if translator_validation_allowed)
      6. Aggregate lifecycle report
      7. Propagate lifecycle gate
      8. Persist to RMOS (if rmos_persistence_allowed and persist_to_rmos)

    No DXF generation. No G-code generation. No machine output.
    """
    operation = request.preview_request.operation
    payload = request.preview_request.payload

    # --- Step 0: Evaluate lifecycle policy (6I) ---
    policy = evaluate_lifecycle_policy(
        operation=operation,
        persist_to_rmos=request.persist_to_rmos,
    )

    # --- Step 1: If policy RED, return early ---
    if not policy.allowed:
        return GovernedExportLifecycleReport(
            lifecycle_gate="red",
            export_ready=False,
            machine_ready=False,
            translator_ready=False,
            machine_output_generated=False,
            translator_output_generated=False,
            preview_gate="red",
            preview_operation=operation,
            export_object_summary=None,
            machine_validation_gate=None,
            machine_validation_compatible=None,
            translator_validation_gate=None,
            translator_validation_compatible=None,
            blocking_issues=list(policy.blocking_issues),
            warnings=list(policy.warnings),
            metadata=LifecycleMetadata(
                validation_only=True,
                risk_class="B",
                governed_export_pipeline=True,
            ),
            rmos=create_empty_persistence_result(),
            policy_evaluation=policy,
        )

    blocking_issues = list(policy.blocking_issues)
    warnings = list(policy.warnings)
    gates = [policy.lifecycle_gate]

    # --- Step 2: Generate governed preview (if allowed) ---
    preview = None
    preview_gate = "red"

    if policy.preview_allowed:
        preview, preview_gate, preview_errors, preview_warnings = dispatch_preview(
            operation, payload
        )
        gates.append(preview_gate)
        blocking_issues.extend(preview_errors)
        warnings.extend(preview_warnings)

    # --- Step 3: Build export object (if allowed and preview GREEN) ---
    export_object = None
    export_summary = None

    if (
        policy.export_object_allowed
        and preview_gate != "red"
        and preview is not None
    ):
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

    # --- Step 4: Machine compatibility validation (if allowed) ---
    machine_gate = None
    machine_compatible = None

    if policy.machine_validation_allowed and export_object is not None:
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

    # --- Step 5: Translator compatibility validation (if allowed) ---
    translator_gate = None
    translator_compatible = None

    if policy.translator_validation_allowed and export_object is not None:
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

    # --- Step 8: RMOS persistence (if allowed and requested) ---
    rmos_result: Optional[RMOSPersistenceResult] = None

    if request.persist_to_rmos and policy.rmos_persistence_allowed:
        # Serialize export object if created
        export_object_dict = None
        if export_object is not None:
            export_object_dict = export_object.model_dump(mode="json")

        # Build lifecycle report dict for persistence
        # (we build it manually to avoid circular reference)
        lifecycle_report_dict = {
            "lifecycle_gate": lifecycle_gate,
            "export_ready": export_ready,
            "machine_ready": False,
            "translator_ready": translator_ready,
            "machine_output_generated": False,
            "translator_output_generated": False,
            "preview_gate": preview_gate,
            "preview_operation": operation,
            "export_object_summary": export_summary.model_dump() if export_summary else None,
            "machine_validation_gate": machine_gate,
            "machine_validation_compatible": machine_compatible,
            "translator_validation_gate": translator_gate,
            "translator_validation_compatible": translator_compatible,
            "blocking_issues": blocking_issues,
            "warnings": warnings,
            "metadata": {
                "validation_only": True,
                "risk_class": "B",
                "governed_export_pipeline": True,
            },
            "policy_evaluation": policy.model_dump(),
        }

        rmos_result = persist_export_lifecycle_artifacts(
            export_object=export_object_dict,
            lifecycle_report=lifecycle_report_dict,
        )
    else:
        rmos_result = create_empty_persistence_result()

    return GovernedExportLifecycleReport(
        lifecycle_gate=lifecycle_gate,
        export_ready=export_ready,
        machine_ready=False,  # Always false
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
        rmos=rmos_result,
        policy_evaluation=policy,
    )
