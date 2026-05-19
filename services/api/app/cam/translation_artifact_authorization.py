"""
Translation Artifact Authorization Gate

CAM Dev Order 7E: Authorization evaluation for translation artifacts.

This module evaluates whether a translation artifact is eligible for
future execution WITHOUT authorizing or performing execution.

Key distinctions:
  - Eligibility ≠ Approval
  - Validation ≠ Execution
  - Human approval remains required

7E invariants:
  - authorized_for_execution: always false
  - human_approval_required: always true
  - No artifact generation
  - No DXF/SVG/G-code output
  - No machine output
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.cam.translation_artifact import TranslationArtifact
from app.cam.translator_capability_registry import (
    get_translator_capability,
    TranslatorCapability,
)


# -----------------------------------------------------------------------------
# Authorization Evaluation Model
# -----------------------------------------------------------------------------

class TranslationArtifactAuthorizationEvaluation(BaseModel):
    """
    Authorization evaluation result for a translation artifact.

    Determines eligibility for future execution without authorizing it.
    Human approval remains required. Execution remains disabled.

    7E invariants (model-enforced):
      - authorized_for_execution: always false
      - human_approval_required: always true
    """

    # --- Identity ---
    artifact_id: str = Field(..., description="Evaluated artifact identifier")
    translator_id: str = Field(..., description="Translator identifier")

    # --- Gate ---
    gate: Literal["green", "yellow", "red"] = Field(
        ..., description="Authorization gate status"
    )

    # --- Authorization State ---
    authorized_for_execution: bool = Field(
        default=False,
        description="Always false in 7E — execution not authorized"
    )
    eligible_for_future_execution: bool = Field(
        ..., description="Whether artifact is eligible for future execution"
    )
    human_approval_required: bool = Field(
        default=True,
        description="Always true — human approval required for execution"
    )

    # --- Issues ---
    blocking_issues: List[str] = Field(
        default_factory=list,
        description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="YELLOW warnings"
    )

    # --- Snapshots ---
    policy_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Policy state at evaluation time"
    )
    capability_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current translator capability (for comparison)"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evaluation metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_7e_invariants(self) -> "TranslationArtifactAuthorizationEvaluation":
        """
        Enforce 7E invariants:
        - authorized_for_execution must be False
        - human_approval_required must be True
        - eligible_for_future_execution requires GREEN or YELLOW gate
        """
        if self.authorized_for_execution:
            raise ValueError(
                "authorized_for_execution must be False in 7E — "
                "execution is not authorized"
            )

        if not self.human_approval_required:
            raise ValueError(
                "human_approval_required must be True in 7E — "
                "human approval is always required"
            )

        # Eligibility requires non-RED gate
        if self.gate == "red" and self.eligible_for_future_execution:
            raise ValueError(
                "eligible_for_future_execution cannot be True when gate is RED"
            )

        return self


# -----------------------------------------------------------------------------
# Authorization Request Model
# -----------------------------------------------------------------------------

class TranslationArtifactAuthorizationRequest(BaseModel):
    """Request model for artifact authorization validation."""

    artifact: TranslationArtifact = Field(
        ..., description="Translation artifact to evaluate"
    )


# -----------------------------------------------------------------------------
# Snapshot Comparison
# -----------------------------------------------------------------------------

def _compare_capability_snapshots(
    artifact_snapshot: Dict[str, Any],
    current_capability: TranslatorCapability,
) -> tuple[List[str], List[str]]:
    """
    Compare artifact's capability snapshot against current registry state.

    Returns (blocking_issues, warnings).

    YELLOW conditions:
      - translator version changed
      - maturity changed
      - description/metadata changed
      - supported_operations changed non-critically

    RED conditions:
      - translator_category changed
      - output_class changed
      - execution/machine-output flags inconsistent
      - current registry says machine_output_supported=true
    """
    blocking_issues = []
    warnings = []

    current_dict = current_capability.model_dump(mode="json")

    # RED: Category changed (safety boundary)
    if artifact_snapshot.get("translator_category") != current_dict.get("translator_category"):
        blocking_issues.append(
            f"translator_category changed: "
            f"'{artifact_snapshot.get('translator_category')}' → "
            f"'{current_dict.get('translator_category')}'"
        )

    # RED: Output class changed (safety boundary)
    if artifact_snapshot.get("output_class") != current_dict.get("output_class"):
        blocking_issues.append(
            f"output_class changed: "
            f"'{artifact_snapshot.get('output_class')}' → "
            f"'{current_dict.get('output_class')}'"
        )

    # RED: Machine output now supported (safety boundary violation)
    if current_dict.get("machine_output_supported") is True:
        blocking_issues.append(
            "Current registry has machine_output_supported=true — "
            "safety boundary violation"
        )

    # RED: Execution state inconsistency
    current_exec_state = current_dict.get("execution_state")
    artifact_exec_state = artifact_snapshot.get("execution_state")
    if current_exec_state == "execution_disabled" and artifact_exec_state != "execution_disabled":
        blocking_issues.append(
            f"Translator execution now disabled but artifact was created "
            f"with execution_state='{artifact_exec_state}'"
        )

    # YELLOW: Maturity changed
    if artifact_snapshot.get("maturity") != current_dict.get("maturity"):
        warnings.append(
            f"Translator maturity changed: "
            f"'{artifact_snapshot.get('maturity')}' → "
            f"'{current_dict.get('maturity')}'"
        )

    # YELLOW: Description changed
    if artifact_snapshot.get("description") != current_dict.get("description"):
        warnings.append("Translator description changed since artifact creation")

    # YELLOW: Supported operations changed
    artifact_ops = set(artifact_snapshot.get("supported_operations") or [])
    current_ops = set(current_dict.get("supported_operations") or [])
    if artifact_ops != current_ops:
        added = current_ops - artifact_ops
        removed = artifact_ops - current_ops
        if removed:
            warnings.append(
                f"Translator no longer supports operations: {sorted(removed)}"
            )
        if added:
            warnings.append(
                f"Translator now supports additional operations: {sorted(added)}"
            )

    # YELLOW: Notes changed
    if artifact_snapshot.get("notes") != current_dict.get("notes"):
        warnings.append("Translator notes changed since artifact creation")

    return blocking_issues, warnings


# -----------------------------------------------------------------------------
# Authorization Evaluator
# -----------------------------------------------------------------------------

def evaluate_translation_artifact_authorization(
    artifact: TranslationArtifact,
) -> TranslationArtifactAuthorizationEvaluation:
    """
    Evaluate whether a translation artifact is eligible for future execution.

    This is ELIGIBILITY EVALUATION, not approval or execution.

    Checks:
      1. Artifact structural validity (7D invariants)
      2. Translator exists in registry
      3. Category/output class match
      4. Capability snapshot comparison
      5. No executable payload or machine output

    Returns authorization evaluation with:
      - gate: green/yellow/red
      - eligible_for_future_execution: true if gate != red
      - authorized_for_execution: always false
      - human_approval_required: always true

    No DXF. No G-code. No machine output. No artifact generation.
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # --- Check 1: Artifact 7D invariants ---
    if artifact.execution_supported:
        blocking_issues.append(
            "Artifact has execution_supported=true — violates 7D invariant"
        )

    if artifact.executable_payload_present:
        blocking_issues.append(
            "Artifact has executable_payload_present=true — violates 7D invariant"
        )

    if artifact.machine_output_present:
        blocking_issues.append(
            "Artifact has machine_output_present=true — violates 7D invariant"
        )

    # --- Check 2: Translator exists in registry ---
    current_capability = get_translator_capability(artifact.translator_id)

    if current_capability is None:
        blocking_issues.append(
            f"Translator '{artifact.translator_id}' not found in registry"
        )
        # Cannot proceed with further checks
        gate = "red"
        return TranslationArtifactAuthorizationEvaluation(
            artifact_id=artifact.artifact_id,
            translator_id=artifact.translator_id,
            gate=gate,
            authorized_for_execution=False,
            eligible_for_future_execution=False,
            human_approval_required=True,
            blocking_issues=blocking_issues,
            warnings=warnings,
            policy_snapshot=artifact.policy_snapshot,
            capability_snapshot={},
            metadata={
                "evaluation_type": "translation_artifact_authorization",
                "dev_order": "7E",
                "validation_only": True,
            },
        )

    # --- Check 3: Category/output class match ---
    if artifact.translator_category != current_capability.translator_category:
        blocking_issues.append(
            f"Artifact translator_category '{artifact.translator_category}' "
            f"does not match registry '{current_capability.translator_category}'"
        )

    if artifact.output_class != current_capability.output_class:
        blocking_issues.append(
            f"Artifact output_class '{artifact.output_class}' "
            f"does not match registry '{current_capability.output_class}'"
        )

    # --- Check 4: Current capability safety checks ---
    if current_capability.machine_output_supported:
        blocking_issues.append(
            "Current translator capability has machine_output_supported=true — "
            "safety boundary violation"
        )

    if current_capability.execution_state == "execution_disabled":
        blocking_issues.append(
            f"Translator '{artifact.translator_id}' has execution_state='execution_disabled'"
        )

    # --- Check 5: Capability snapshot comparison ---
    if artifact.capability_snapshot:
        snapshot_blocking, snapshot_warnings = _compare_capability_snapshots(
            artifact.capability_snapshot,
            current_capability,
        )
        blocking_issues.extend(snapshot_blocking)
        warnings.extend(snapshot_warnings)

    # --- Check 6: Artifact state validity ---
    valid_states = {"validation_only", "non_executable", "execution_planned"}
    if artifact.artifact_state not in valid_states:
        blocking_issues.append(
            f"Invalid artifact_state '{artifact.artifact_state}'"
        )

    # --- Check 7: Maturity warnings ---
    if current_capability.maturity in ("prototype", "deprecated"):
        warnings.append(
            f"Translator maturity is '{current_capability.maturity}' — "
            f"not recommended for production"
        )

    # --- Determine gate ---
    if blocking_issues:
        gate = "red"
    elif warnings:
        gate = "yellow"
    else:
        gate = "green"

    # Eligibility requires non-RED gate
    eligible = gate != "red"

    return TranslationArtifactAuthorizationEvaluation(
        artifact_id=artifact.artifact_id,
        translator_id=artifact.translator_id,
        gate=gate,
        authorized_for_execution=False,
        eligible_for_future_execution=eligible,
        human_approval_required=True,
        blocking_issues=blocking_issues,
        warnings=warnings,
        policy_snapshot=artifact.policy_snapshot,
        capability_snapshot=current_capability.model_dump(mode="json"),
        metadata={
            "evaluation_type": "translation_artifact_authorization",
            "dev_order": "7E",
            "validation_only": True,
            "artifact_state": artifact.artifact_state,
            "output_class": artifact.output_class,
        },
    )
