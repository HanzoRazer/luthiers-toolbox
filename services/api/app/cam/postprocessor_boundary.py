"""
Postprocessor Boundary Compatibility Validation

CAM Dev Order 6C: Postprocessor compatibility inspection without machine output.

This module evaluates whether a governed Export Object is compatible with
a given machine profile. It returns a compatibility report — NOT machine code.

Core rule:
  - 6C postprocessor output is a report, not machine code.
  - No G-code generation
  - No DXF generation
  - No file output
  - No executable machine instructions

Gate semantics:
  - GREEN: Export object operation supported, all checks pass
  - YELLOW: Supported with cautions (tight margins, incomplete metadata)
  - RED: Unsupported operation, unit mismatch, bounds violation, missing tooling
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.cam.export_object import ExportObject


# -----------------------------------------------------------------------------
# Machine Profile (Validation Only)
# -----------------------------------------------------------------------------

class WorkEnvelopeMM(BaseModel):
    """Machine work envelope in mm."""
    x: float = Field(..., gt=0, description="X axis travel in mm")
    y: float = Field(..., gt=0, description="Y axis travel in mm")
    z: float = Field(..., gt=0, description="Z axis travel in mm")


class MachineProfileValidationOnly(BaseModel):
    """
    Simplified machine profile for compatibility validation.

    This is NOT a production machine profile. It contains only the
    fields needed to evaluate export object compatibility.

    No controller dialect. No postprocessor settings. No execution config.
    """
    machine_profile_id: str = Field(..., description="Profile identifier")
    controller: str = Field(default="none", description="Controller type (always 'none' for validation)")
    units: Literal["mm", "inch"] = Field(default="mm", description="Machine units")
    supported_operations: List[str] = Field(..., description="Operations this machine supports")
    axis_count: int = Field(..., ge=1, description="Number of motion axes")
    work_envelope_mm: WorkEnvelopeMM = Field(..., description="Work envelope dimensions")
    supports_arcs: bool = Field(default=False, description="G2/G3 arc support")
    supports_tool_changes: bool = Field(default=False, description="Automatic tool change support")


# -----------------------------------------------------------------------------
# Compatibility Report
# -----------------------------------------------------------------------------

class CompatibilityMetadata(BaseModel):
    """Metadata about the compatibility check."""
    validation_only: bool = True
    risk_class: Literal["A", "B", "C"] = "B"
    machine_ready: bool = False


class PostprocessorCompatibilityReport(BaseModel):
    """
    Result of postprocessor compatibility evaluation.

    This is a REPORT, not machine output. No executable instructions.
    """
    compatible: bool = Field(..., description="Overall compatibility")
    gate: Literal["green", "yellow", "red"] = Field(..., description="Gate status")

    # Safety assertions — always false in 6C
    machine_output_generated: bool = Field(
        default=False,
        description="Always false — no machine output in 6C"
    )
    postprocessor_output_generated: bool = Field(
        default=False,
        description="Always false — no postprocessor output in 6C"
    )

    operation: str = Field(..., description="Operation being evaluated")
    supported_operations: List[str] = Field(..., description="Operations the machine supports")

    blocking_issues: List[str] = Field(default_factory=list, description="RED issues")
    warnings: List[str] = Field(default_factory=list, description="YELLOW warnings")

    required_capabilities: List[str] = Field(
        default_factory=list,
        description="Capabilities required by the export object"
    )
    unsupported_capabilities: List[str] = Field(
        default_factory=list,
        description="Required capabilities not supported by machine"
    )

    metadata: CompatibilityMetadata = Field(
        default_factory=CompatibilityMetadata,
        description="Validation metadata"
    )


# -----------------------------------------------------------------------------
# Compatibility Request
# -----------------------------------------------------------------------------

class PostprocessorCompatibilityRequest(BaseModel):
    """Request for postprocessor compatibility check."""
    export_object: ExportObject = Field(..., description="Governed export object from 6B")
    machine_profile: MachineProfileValidationOnly = Field(..., description="Machine profile for validation")


# -----------------------------------------------------------------------------
# Capability Inference
# -----------------------------------------------------------------------------

def infer_required_capabilities(export_object: ExportObject) -> List[str]:
    """
    Infer required machine capabilities from export object.

    Examines the export object structure to determine what
    the machine must support.
    """
    capabilities = []

    # Always require basic motion
    capabilities.append("3_axis_motion")
    capabilities.append("linear_interpolation")

    # Check for plunge moves
    if export_object.toolpaths:
        for op in export_object.toolpaths.operations:
            for move in op.moves:
                if move.type == "plunge":
                    if "controlled_plunge" not in capabilities:
                        capabilities.append("controlled_plunge")
                elif move.type in ("arc_cw", "arc_ccw"):
                    if "arc_interpolation" not in capabilities:
                        capabilities.append("arc_interpolation")

    return capabilities


# -----------------------------------------------------------------------------
# Validation Checks
# -----------------------------------------------------------------------------

def check_operation_support(
    export_object: ExportObject,
    machine_profile: MachineProfileValidationOnly,
) -> tuple[bool, Optional[str]]:
    """
    Check if operation is supported by machine.

    Returns (passed, error_message).
    """
    # Extract operation from intent or metadata
    operation = export_object.intent.operation_type

    # Normalize operation name for comparison
    # e.g., "nut_slot_cutting" should match "nut_slot"
    operation_base = operation.replace("_cutting", "").replace("_milling", "")

    supported = machine_profile.supported_operations

    # Check exact match or base match
    if operation in supported or operation_base in supported:
        return True, None

    # Check if any supported operation is a substring match
    for sup_op in supported:
        if sup_op in operation or operation in sup_op:
            return True, None

    return False, f"Operation '{operation}' not in supported operations: {supported}"


def check_unit_compatibility(
    export_object: ExportObject,
    machine_profile: MachineProfileValidationOnly,
) -> tuple[bool, Optional[str]]:
    """
    Check unit compatibility.

    Returns (passed, error_message).
    """
    export_units = export_object.geometry.coordinate_system.units
    machine_units = machine_profile.units

    if export_units != machine_units:
        return False, f"Unit mismatch: export uses '{export_units}', machine uses '{machine_units}'"

    return True, None


def check_axis_requirement(
    machine_profile: MachineProfileValidationOnly,
) -> tuple[bool, Optional[str]]:
    """
    Check axis count requirement (minimum 3 axes).

    Returns (passed, error_message).
    """
    if machine_profile.axis_count < 3:
        return False, f"Insufficient axes: machine has {machine_profile.axis_count}, minimum 3 required"

    return True, None


def check_bounds(
    export_object: ExportObject,
    machine_profile: MachineProfileValidationOnly,
) -> tuple[bool, List[str], List[str]]:
    """
    Check if toolpath bounds fit within machine envelope.

    Returns (passed, errors, warnings).
    """
    errors = []
    warnings = []

    bounds = export_object.geometry.bounds
    envelope = machine_profile.work_envelope_mm

    # X bounds check
    if bounds.x_max > envelope.x:
        errors.append(f"X exceeds envelope: {bounds.x_max:.2f}mm > {envelope.x:.2f}mm")
    elif bounds.x_max > envelope.x * 0.95:
        warnings.append(f"X near envelope limit: {bounds.x_max:.2f}mm (envelope: {envelope.x:.2f}mm)")

    # Y bounds check
    if bounds.y_max > envelope.y:
        errors.append(f"Y exceeds envelope: {bounds.y_max:.2f}mm > {envelope.y:.2f}mm")
    elif bounds.y_max > envelope.y * 0.95:
        warnings.append(f"Y near envelope limit: {bounds.y_max:.2f}mm (envelope: {envelope.y:.2f}mm)")

    # Z bounds check (z_min is typically negative for cutting depth)
    z_depth = abs(bounds.z_min)
    if z_depth > envelope.z:
        errors.append(f"Z depth exceeds envelope: {z_depth:.2f}mm > {envelope.z:.2f}mm")
    elif z_depth > envelope.z * 0.95:
        warnings.append(f"Z depth near envelope limit: {z_depth:.2f}mm (envelope: {envelope.z:.2f}mm)")

    passed = len(errors) == 0
    return passed, errors, warnings


def check_tooling_block(
    export_object: ExportObject,
) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Check tooling block presence and completeness.

    Returns (passed, error, warning).
    """
    tooling = export_object.tooling

    if tooling is None:
        return False, "Missing required tooling block", None

    # Check required fields
    if not tooling.tool_id:
        return False, "Tooling block missing tool_id", None

    if not tooling.geometry:
        return False, "Tooling block missing geometry", None

    if not tooling.geometry.diameter_mm:
        return False, "Tooling geometry missing diameter_mm", None

    # Check for incomplete but acceptable tooling
    warning = None
    if not tooling.geometry.cutting_length_mm:
        warning = "Tooling geometry incomplete: missing cutting_length_mm"
    elif not tooling.geometry.shank_diameter_mm:
        warning = "Tooling geometry incomplete: missing shank_diameter_mm"

    return True, None, warning


def check_arc_support(
    export_object: ExportObject,
    machine_profile: MachineProfileValidationOnly,
) -> tuple[bool, Optional[str]]:
    """
    Check if export requires arcs and machine supports them.

    Returns (passed, error).
    """
    requires_arcs = False

    if export_object.toolpaths:
        for op in export_object.toolpaths.operations:
            for move in op.moves:
                if move.type in ("arc_cw", "arc_ccw"):
                    requires_arcs = True
                    break
            if requires_arcs:
                break

    if requires_arcs and not machine_profile.supports_arcs:
        return False, "Export requires arc interpolation but machine does not support arcs"

    return True, None


# -----------------------------------------------------------------------------
# Main Evaluation Function
# -----------------------------------------------------------------------------

def evaluate_postprocessor_compatibility(
    export_object: ExportObject,
    machine_profile: MachineProfileValidationOnly,
) -> PostprocessorCompatibilityReport:
    """
    Evaluate export object compatibility with machine profile.

    Returns a compatibility REPORT, not machine output.

    Gate logic:
      - GREEN: All checks pass
      - YELLOW: Checks pass with warnings
      - RED: Any blocking check fails
    """
    blocking_issues = []
    warnings = []

    # Infer required capabilities
    required_capabilities = infer_required_capabilities(export_object)
    unsupported_capabilities = []

    # 1. Operation support check
    op_passed, op_error = check_operation_support(export_object, machine_profile)
    if not op_passed:
        blocking_issues.append(op_error)

    # 2. Unit compatibility check
    unit_passed, unit_error = check_unit_compatibility(export_object, machine_profile)
    if not unit_passed:
        blocking_issues.append(unit_error)

    # 3. Axis requirement check
    axis_passed, axis_error = check_axis_requirement(machine_profile)
    if not axis_passed:
        blocking_issues.append(axis_error)

    # 4. Bounds check
    bounds_passed, bounds_errors, bounds_warnings = check_bounds(export_object, machine_profile)
    blocking_issues.extend(bounds_errors)
    warnings.extend(bounds_warnings)

    # 5. Tooling block check
    tooling_passed, tooling_error, tooling_warning = check_tooling_block(export_object)
    if not tooling_passed:
        blocking_issues.append(tooling_error)
    if tooling_warning:
        warnings.append(tooling_warning)

    # 6. Arc support check
    arc_passed, arc_error = check_arc_support(export_object, machine_profile)
    if not arc_passed:
        blocking_issues.append(arc_error)
        unsupported_capabilities.append("arc_interpolation")

    # Determine gate status
    if blocking_issues:
        gate = "red"
        compatible = False
    elif warnings:
        gate = "yellow"
        compatible = True
    else:
        gate = "green"
        compatible = True

    # Extract operation name
    operation = export_object.intent.operation_type

    return PostprocessorCompatibilityReport(
        compatible=compatible,
        gate=gate,
        machine_output_generated=False,  # Always false in 6C
        postprocessor_output_generated=False,  # Always false in 6C
        operation=operation,
        supported_operations=machine_profile.supported_operations,
        blocking_issues=blocking_issues,
        warnings=warnings,
        required_capabilities=required_capabilities,
        unsupported_capabilities=unsupported_capabilities,
        metadata=CompatibilityMetadata(
            validation_only=True,
            risk_class="B",
            machine_ready=False,
        ),
    )
