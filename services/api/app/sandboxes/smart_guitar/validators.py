"""
Smart Guitar Validators (SG-SBX-0.1)
====================================

Validation logic for Smart Guitar specs.
Returns errors (blocking) and warnings (advisory).
"""

from __future__ import annotations

from typing import List, Tuple

from .schemas import CONTRACT_VERSION, PlanError, PlanWarning, SmartGuitarSpec


# Required component IDs for v0.1 Smart Guitar
REQUIRED_COMPONENT_IDS = {
    "pi5",
    "arduino_uno_r4",
    "hifiberry_dac_adc",
    "battery_pack",
    "fan_40mm",
}


def validate_spec(
    spec: SmartGuitarSpec,
) -> Tuple[List[PlanError], List[PlanWarning], SmartGuitarSpec]:
    """
    Validate a Smart Guitar spec.
    
    Returns:
        Tuple of (errors, warnings, normalized_spec)
        - errors: Blocking validation errors
        - warnings: Non-blocking warnings/advisories
        - normalized_spec: The validated (potentially normalized) spec
    """
    errors: List[PlanError] = []
    warnings: List[PlanWarning] = []

    # Contract version check
    if spec.contract_version != CONTRACT_VERSION:
        warnings.append(
            PlanWarning(
                code="contract_version_mismatch",
                message=f"Expected contract {CONTRACT_VERSION}, got {spec.contract_version}",
                severity="warn",
            )
        )

    b = spec.body

    # Core body invariants
    if b.rim_in < 0.50:
        errors.append(
            PlanError(
                code="rim_too_thin",
                message=f"rim_in must be >= 0.50; got {b.rim_in}",
            )
        )

    if b.top_skin_in < 0.30:
        errors.append(
            PlanError(
                code="top_skin_too_thin",
                message=f"top_skin_in must be >= 0.30; got {b.top_skin_in}",
            )
        )

    if b.spine_w_in < 1.50:
        errors.append(
            PlanError(
                code="spine_too_narrow",
                message=f"spine_w_in must be >= 1.50; got {b.spine_w_in}",
            )
        )

    # Hollow depth budget check
    max_hollow = b.thickness_in - b.top_skin_in
    if spec.target_hollow_depth_in > max_hollow:
        errors.append(
            PlanError(
                code="hollow_depth_exceeds_budget",
                message=f"target_hollow_depth_in {spec.target_hollow_depth_in} exceeds max {max_hollow}",
            )
        )

    # Pod depth budget check (conservative: same as hollow)
    max_pod = b.thickness_in - b.top_skin_in
    if spec.pod_depth_in > max_pod:
        errors.append(
            PlanError(
                code="pod_depth_exceeds_budget",
                message=f"pod_depth_in {spec.pod_depth_in} exceeds max {max_pod}",
            )
        )

    # Electronics must include standard stack
    present_ids = {c.id for c in spec.electronics}
    missing = sorted(list(REQUIRED_COMPONENT_IDS - present_ids))
    if missing:
        errors.append(
            PlanError(
                code="missing_required_components",
                message=f"Missing required electronics components: {missing}",
            )
        )

    # Thermal warning: fan but no vents declared
    if spec.thermal.cooling == "active_fan" and not spec.thermal.vents_defined:
        warnings.append(
            PlanWarning(
                code="vents_missing",
                message=(
                    "Active fan specified but vents_defined=false. "
                    "Add vent paths or expect thermal issues."
                ),
                severity="warn",
            )
        )

    return errors, warnings, spec
