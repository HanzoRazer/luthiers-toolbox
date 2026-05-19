"""
CAM Lifecycle Policy Engine

CAM Dev Order 6I: Lifecycle policy enforcement.

This module enforces governance rules from the capability registry.
It converts declarative metadata into active lifecycle policy.

Core principle:
  Policy engine controls lifecycle stages BEFORE they run.
  Do not run disallowed stages and report violations afterward.

The capability registry defines:
  what an operation claims

The policy engine enforces:
  what the lifecycle allows

Safety assertions:
  - machine_output_allowed: always false in 6I
  - translator_execution_allowed: always false in 6I
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.cam.cam_operation_registry import (
    CAMOperationCapability,
    get_operation_capability,
)


# -----------------------------------------------------------------------------
# Policy Models
# -----------------------------------------------------------------------------

class LifecyclePolicyEvaluation(BaseModel):
    """
    Result of lifecycle policy evaluation.

    This determines what the lifecycle orchestrator is allowed to do.
    """

    operation: str = Field(..., description="Operation being evaluated")

    allowed: bool = Field(
        ..., description="Whether lifecycle execution is allowed at all"
    )

    lifecycle_gate: Literal["green", "yellow", "red"] = Field(
        ..., description="Policy gate status"
    )

    exportability_class: str = Field(
        ..., description="Operation's exportability classification"
    )
    maturity: str = Field(..., description="Operation's maturity level")

    policy_checks: List[str] = Field(
        default_factory=list,
        description="List of policy checks performed with results"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="RED policy violations"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="YELLOW policy warnings"
    )

    # Stage permissions - orchestrator checks these before running stages
    preview_allowed: bool = Field(
        ..., description="Whether preview generation is allowed"
    )
    export_object_allowed: bool = Field(
        ..., description="Whether export object creation is allowed"
    )
    machine_validation_allowed: bool = Field(
        ..., description="Whether machine compatibility validation is allowed"
    )
    translator_validation_allowed: bool = Field(
        ..., description="Whether translator compatibility validation is allowed"
    )
    rmos_persistence_allowed: bool = Field(
        ..., description="Whether RMOS artifact persistence is allowed"
    )

    # Hard prohibitions - always false in 6I
    machine_output_allowed: bool = Field(
        default=False,
        description="Always false in 6I — no machine execution"
    )
    translator_execution_allowed: bool = Field(
        default=False,
        description="Always false in 6I — no translator execution"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional policy metadata"
    )


# -----------------------------------------------------------------------------
# Policy Check Results
# -----------------------------------------------------------------------------

class PolicyCheckResult:
    """Result of a single policy check."""

    def __init__(
        self,
        name: str,
        passed: bool,
        gate: Literal["green", "yellow", "red"],
        message: Optional[str] = None,
    ):
        self.name = name
        self.passed = passed
        self.gate = gate
        self.message = message

    def format(self) -> str:
        """Format check result for policy_checks list."""
        status = "PASS" if self.passed else ("WARN" if self.gate == "yellow" else "FAIL")
        return f"{self.name}: {status}"


# -----------------------------------------------------------------------------
# Policy Evaluation
# -----------------------------------------------------------------------------

def evaluate_lifecycle_policy(
    operation: str,
    persist_to_rmos: bool = False,
) -> LifecyclePolicyEvaluation:
    """
    Evaluate lifecycle policy for an operation.

    This function determines what the lifecycle orchestrator is allowed to do
    based on the operation's capability declaration and request parameters.

    Args:
        operation: Operation identifier
        persist_to_rmos: Whether RMOS persistence is requested

    Returns:
        LifecyclePolicyEvaluation with stage permissions and gate status
    """
    checks: List[PolicyCheckResult] = []
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # --- Check 1: Operation exists in registry ---
    capability = get_operation_capability(operation)

    if capability is None:
        checks.append(PolicyCheckResult(
            "operation_registered",
            passed=False,
            gate="red",
            message=f"Operation '{operation}' not found in capability registry",
        ))
        blocking_issues.append(f"Operation '{operation}' not found in capability registry")

        return LifecyclePolicyEvaluation(
            operation=operation,
            allowed=False,
            lifecycle_gate="red",
            exportability_class="unknown",
            maturity="unknown",
            policy_checks=[c.format() for c in checks],
            blocking_issues=blocking_issues,
            warnings=warnings,
            preview_allowed=False,
            export_object_allowed=False,
            machine_validation_allowed=False,
            translator_validation_allowed=False,
            rmos_persistence_allowed=False,
            machine_output_allowed=False,
            translator_execution_allowed=False,
            metadata={"reason": "operation_not_registered"},
        )

    checks.append(PolicyCheckResult(
        "operation_registered",
        passed=True,
        gate="green",
    ))

    # --- Check 2: Lifecycle support ---
    if not capability.lifecycle_supported:
        checks.append(PolicyCheckResult(
            "lifecycle_supported",
            passed=False,
            gate="red",
            message=f"Operation '{operation}' does not support lifecycle orchestration",
        ))
        blocking_issues.append(
            f"Operation '{operation}' does not support lifecycle orchestration"
        )

        return LifecyclePolicyEvaluation(
            operation=operation,
            allowed=False,
            lifecycle_gate="red",
            exportability_class=capability.exportability_class,
            maturity=capability.maturity,
            policy_checks=[c.format() for c in checks],
            blocking_issues=blocking_issues,
            warnings=warnings,
            preview_allowed=False,
            export_object_allowed=False,
            machine_validation_allowed=False,
            translator_validation_allowed=False,
            rmos_persistence_allowed=False,
            machine_output_allowed=False,
            translator_execution_allowed=False,
            metadata={"reason": "lifecycle_not_supported"},
        )

    checks.append(PolicyCheckResult(
        "lifecycle_supported",
        passed=True,
        gate="green",
    ))

    # --- Determine stage permissions based on exportability class ---
    stage_permissions = _compute_stage_permissions(capability)

    # --- Check 3: Exportability class ---
    exportability_check = _check_exportability_class(capability)
    checks.append(exportability_check)
    if exportability_check.message:
        if exportability_check.gate == "red":
            blocking_issues.append(exportability_check.message)
        elif exportability_check.gate == "yellow":
            warnings.append(exportability_check.message)

    # --- Check 4: Maturity ---
    maturity_check = _check_maturity(capability)
    checks.append(maturity_check)
    if maturity_check.message:
        if maturity_check.gate == "red":
            blocking_issues.append(maturity_check.message)
        elif maturity_check.gate == "yellow":
            warnings.append(maturity_check.message)

    # --- Check 5: RMOS persistence eligibility ---
    rmos_check = _check_rmos_eligibility(capability, persist_to_rmos, stage_permissions)
    checks.append(rmos_check)
    if rmos_check.message:
        if rmos_check.gate == "red":
            blocking_issues.append(rmos_check.message)
        elif rmos_check.gate == "yellow":
            warnings.append(rmos_check.message)

    # --- Check 6: Machine output prohibition ---
    machine_output_check = PolicyCheckResult(
        "machine_output_prohibited",
        passed=True,
        gate="green",
    )
    checks.append(machine_output_check)

    # --- Check 7: Translator execution prohibition ---
    translator_exec_check = PolicyCheckResult(
        "translator_execution_prohibited",
        passed=True,
        gate="green",
    )
    checks.append(translator_exec_check)

    # --- Compute final gate ---
    gates = [c.gate for c in checks]
    if "red" in gates:
        final_gate = "red"
        allowed = False
    elif "yellow" in gates:
        final_gate = "yellow"
        allowed = True
    else:
        final_gate = "green"
        allowed = True

    # If RMOS check failed, update stage permissions
    if rmos_check.gate == "red":
        stage_permissions["rmos_persistence_allowed"] = False

    return LifecyclePolicyEvaluation(
        operation=operation,
        allowed=allowed,
        lifecycle_gate=final_gate,
        exportability_class=capability.exportability_class,
        maturity=capability.maturity,
        policy_checks=[c.format() for c in checks],
        blocking_issues=blocking_issues,
        warnings=warnings,
        preview_allowed=stage_permissions["preview_allowed"],
        export_object_allowed=stage_permissions["export_object_allowed"],
        machine_validation_allowed=stage_permissions["machine_validation_allowed"],
        translator_validation_allowed=stage_permissions["translator_validation_allowed"],
        rmos_persistence_allowed=stage_permissions["rmos_persistence_allowed"] and not (rmos_check.gate == "red"),
        machine_output_allowed=False,
        translator_execution_allowed=False,
        metadata={
            "capability_notes": capability.notes,
        },
    )


def _compute_stage_permissions(
    capability: CAMOperationCapability,
) -> Dict[str, bool]:
    """
    Compute stage permissions based on exportability class.

    Returns dict of stage permission booleans.
    """
    exportability = capability.exportability_class

    if exportability == "preview_only":
        return {
            "preview_allowed": True,
            "export_object_allowed": False,
            "machine_validation_allowed": False,
            "translator_validation_allowed": False,
            "rmos_persistence_allowed": False,
        }

    if exportability == "governed_export":
        return {
            "preview_allowed": True,
            "export_object_allowed": capability.export_object_supported,
            "machine_validation_allowed": capability.machine_validation_supported,
            "translator_validation_allowed": capability.translator_validation_supported,
            "rmos_persistence_allowed": capability.rmos_persistence_supported,
        }

    if exportability == "translator_ready":
        return {
            "preview_allowed": True,
            "export_object_allowed": capability.export_object_supported,
            "machine_validation_allowed": capability.machine_validation_supported,
            "translator_validation_allowed": capability.translator_validation_supported,
            "rmos_persistence_allowed": capability.rmos_persistence_supported,
        }

    if exportability == "machine_candidate":
        return {
            "preview_allowed": True,
            "export_object_allowed": capability.export_object_supported,
            "machine_validation_allowed": capability.machine_validation_supported,
            "translator_validation_allowed": capability.translator_validation_supported,
            "rmos_persistence_allowed": capability.rmos_persistence_supported,
        }

    # Unknown exportability class - conservative defaults
    return {
        "preview_allowed": True,
        "export_object_allowed": False,
        "machine_validation_allowed": False,
        "translator_validation_allowed": False,
        "rmos_persistence_allowed": False,
    }


def _check_exportability_class(
    capability: CAMOperationCapability,
) -> PolicyCheckResult:
    """Check exportability class rules."""
    exportability = capability.exportability_class

    if exportability == "preview_only":
        return PolicyCheckResult(
            "exportability_class",
            passed=True,
            gate="yellow",
            message="Operation is preview_only; export object and validations skipped",
        )

    if exportability == "governed_export":
        return PolicyCheckResult(
            "exportability_class",
            passed=True,
            gate="green",
        )

    if exportability == "translator_ready":
        return PolicyCheckResult(
            "exportability_class",
            passed=True,
            gate="green",
        )

    if exportability == "machine_candidate":
        return PolicyCheckResult(
            "exportability_class",
            passed=True,
            gate="yellow",
            message="Operation is a machine-output candidate; execution remains prohibited",
        )

    # Unknown exportability class
    return PolicyCheckResult(
        "exportability_class",
        passed=False,
        gate="red",
        message=f"Unknown exportability class: {exportability}",
    )


def _check_maturity(
    capability: CAMOperationCapability,
) -> PolicyCheckResult:
    """Check maturity level rules."""
    maturity = capability.maturity

    if maturity == "canonical":
        return PolicyCheckResult(
            "maturity",
            passed=True,
            gate="green",
        )

    if maturity == "governed":
        return PolicyCheckResult(
            "maturity",
            passed=True,
            gate="green",
        )

    if maturity == "candidate":
        return PolicyCheckResult(
            "maturity",
            passed=True,
            gate="yellow",
            message="Operation maturity is candidate",
        )

    if maturity == "experimental":
        return PolicyCheckResult(
            "maturity",
            passed=True,
            gate="yellow",
            message="Operation maturity is experimental",
        )

    # Unknown maturity
    return PolicyCheckResult(
        "maturity",
        passed=False,
        gate="red",
        message=f"Unknown maturity level: {maturity}",
    )


def _check_rmos_eligibility(
    capability: CAMOperationCapability,
    persist_to_rmos: bool,
    stage_permissions: Dict[str, bool],
) -> PolicyCheckResult:
    """Check RMOS persistence eligibility."""
    if not persist_to_rmos:
        return PolicyCheckResult(
            "rmos_eligibility",
            passed=True,
            gate="green",
        )

    # RMOS persistence requested - check if allowed
    if not stage_permissions["rmos_persistence_allowed"]:
        return PolicyCheckResult(
            "rmos_eligibility",
            passed=False,
            gate="red",
            message="Operation does not permit RMOS persistence",
        )

    if not capability.rmos_persistence_supported:
        return PolicyCheckResult(
            "rmos_eligibility",
            passed=False,
            gate="red",
            message="Operation does not support RMOS persistence",
        )

    return PolicyCheckResult(
        "rmos_eligibility",
        passed=True,
        gate="green",
    )


# -----------------------------------------------------------------------------
# Policy Helper Functions
# -----------------------------------------------------------------------------

def is_lifecycle_allowed(operation: str) -> bool:
    """
    Quick check if an operation is allowed to use lifecycle.

    Args:
        operation: Operation identifier

    Returns:
        True if operation can use lifecycle orchestration
    """
    capability = get_operation_capability(operation)
    if capability is None:
        return False
    return capability.lifecycle_supported


def get_stage_permissions(operation: str) -> Optional[Dict[str, bool]]:
    """
    Get stage permissions for an operation without full policy evaluation.

    Args:
        operation: Operation identifier

    Returns:
        Dict of stage permissions or None if operation not found
    """
    capability = get_operation_capability(operation)
    if capability is None:
        return None
    return _compute_stage_permissions(capability)
