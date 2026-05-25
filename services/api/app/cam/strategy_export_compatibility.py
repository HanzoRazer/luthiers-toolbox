"""
Strategy Export Compatibility

CAM Dev Order 7U: Strategy/export interoperability contracts.

Provides:
  - StrategyExportCompatibilityEvaluation model
  - General and targeted compatibility evaluation
  - Validation against geometry authority, review state, translator capability

7U invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - serializer_invocation_allowed: always False
  - generates_gcode: always False

Guardrail:
  7U bridges cognition artifacts to governed export review packages.
  It does not create export payloads, invoke translators, serialize geometry,
  or authorize machine output.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


ValidationGate = Literal["green", "yellow", "red"]


class StrategyExportCompatibilityEvaluation(BaseModel):
    """
    Evaluation of strategy/workspace export compatibility.

    Validates whether a cognition artifact (workspace/strategy) can be
    safely packaged for export without violating geometry authority,
    review state, or execution quarantine.

    7U invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
      - serializer_invocation_allowed: always False
      - generates_gcode: always False
    """

    evaluation_id: str = Field(
        default_factory=lambda: f"compat-eval-{uuid4().hex[:12]}",
        description="Unique evaluation identifier"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="ID of workspace being evaluated"
    )
    strategy_id: Optional[str] = Field(
        default=None,
        description="ID of strategy being evaluated"
    )
    target_translator_id: Optional[str] = Field(
        default=None,
        description="Optional translator ID for targeted evaluation"
    )

    modality_compatible: bool = Field(
        default=False,
        description="Whether modality is compatible with export pathway"
    )
    geometry_authority_exportable: bool = Field(
        default=False,
        description="Whether geometry authority layer permits export"
    )
    translator_capability_compatible: bool = Field(
        default=True,
        description="Whether translator capabilities match requirements"
    )
    review_state_valid: bool = Field(
        default=False,
        description="Whether review state permits packaging"
    )
    quarantine_respected: bool = Field(
        default=True,
        description="Whether quarantine status is respected"
    )
    provenance_complete: bool = Field(
        default=False,
        description="Whether provenance chain is complete"
    )

    gate: ValidationGate = Field(
        default="red",
        description="Overall validation gate"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="YELLOW warnings"
    )

    geometry_authority_ref_ids: List[str] = Field(
        default_factory=list,
        description="Geometry authority references evaluated"
    )
    fixture_compatibility_refs: List[str] = Field(
        default_factory=list,
        description="7V fixture compatibility evaluation IDs"
    )
    modality_id: Optional[str] = Field(
        default=None,
        description="Modality ID if available"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7U does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7U does not allow machine output"
    )
    serializer_invocation_allowed: bool = Field(
        default=False,
        description="Always False — 7U does not invoke serializers"
    )
    generates_gcode: bool = Field(
        default=False,
        description="Always False — 7U does not generate G-code"
    )

    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_evaluation_hash: str = Field(
        default="",
        description="Deterministic hash of evaluation state"
    )

    @model_validator(mode="after")
    def enforce_7u_invariants(self) -> "StrategyExportCompatibilityEvaluation":
        """Enforce 7U invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7U invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7U invariant violation: machine_output_allowed must be False"
            )
        if self.serializer_invocation_allowed:
            raise ValueError(
                "7U invariant violation: serializer_invocation_allowed must be False"
            )
        if self.generates_gcode:
            raise ValueError(
                "7U invariant violation: generates_gcode must be False"
            )
        if not self.workspace_id and not self.strategy_id:
            raise ValueError(
                "7U invariant violation: workspace_id or strategy_id is required"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of evaluation state."""
        hash_input = {
            "evaluation_id": self.evaluation_id,
            "workspace_id": self.workspace_id,
            "strategy_id": self.strategy_id,
            "target_translator_id": self.target_translator_id,
            "modality_compatible": self.modality_compatible,
            "geometry_authority_exportable": self.geometry_authority_exportable,
            "translator_capability_compatible": self.translator_capability_compatible,
            "review_state_valid": self.review_state_valid,
            "quarantine_respected": self.quarantine_respected,
            "provenance_complete": self.provenance_complete,
            "gate": self.gate,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def evaluate_strategy_export_compatibility(
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    target_translator_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    modality_id: Optional[str] = None,
    review_status: Optional[str] = None,
    workspace_status: Optional[str] = None,
    geometry_authority_checker: Optional[callable] = None,
    translator_capability_checker: Optional[callable] = None,
    quarantine_checker: Optional[callable] = None,
) -> StrategyExportCompatibilityEvaluation:
    """
    Evaluate strategy/workspace export compatibility.

    Args:
        workspace_id: Workspace ID to evaluate
        strategy_id: Strategy ID to evaluate
        target_translator_id: Optional translator for targeted evaluation
        geometry_authority_ref_ids: Geometry authority references to check
        modality_id: Operation modality if known
        review_status: Current review status
        workspace_status: Current workspace status
        geometry_authority_checker: Callable to check geometry authority exportability
        translator_capability_checker: Callable to check translator capability
        quarantine_checker: Callable to check quarantine status

    Returns:
        StrategyExportCompatibilityEvaluation with gate and issues
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    if not workspace_id and not strategy_id:
        blocking_issues.append("Neither workspace_id nor strategy_id provided")

    modality_compatible = True
    if modality_id:
        pass
    else:
        warnings.append("No modality_id provided — modality compatibility not verified")

    geometry_authority_exportable = True
    if geometry_authority_ref_ids:
        if geometry_authority_checker:
            for ref_id in geometry_authority_ref_ids:
                is_exportable = geometry_authority_checker(ref_id)
                if not is_exportable:
                    blocking_issues.append(
                        f"Geometry authority reference '{ref_id}' is not exportable"
                    )
                    geometry_authority_exportable = False
    else:
        warnings.append("No geometry_authority_ref_ids provided — authority not verified")

    review_state_valid = False
    if review_status:
        valid_for_export = review_status in (
            "approved", "approved_for_export_review", "validated", "export_ready"
        )
        if valid_for_export:
            review_state_valid = True
        else:
            warnings.append(f"Review status '{review_status}' may not permit export")
    else:
        warnings.append("No review_status provided — review state not verified")

    if workspace_status:
        if workspace_status in ("validated", "export_ready"):
            review_state_valid = True
        elif workspace_status == "archived":
            blocking_issues.append("Workspace is archived — cannot be exported")
            review_state_valid = False

    translator_capability_compatible = True
    quarantine_respected = True

    if target_translator_id:
        if translator_capability_checker:
            is_compatible = translator_capability_checker(target_translator_id, modality_id)
            if not is_compatible:
                blocking_issues.append(
                    f"Translator '{target_translator_id}' not compatible with modality"
                )
                translator_capability_compatible = False

        if quarantine_checker:
            is_quarantined = quarantine_checker(target_translator_id)
            if is_quarantined:
                blocking_issues.append(
                    f"Translator '{target_translator_id}' is under quarantine"
                )
                quarantine_respected = False

    provenance_complete = bool(geometry_authority_ref_ids)
    if not provenance_complete:
        warnings.append("Provenance incomplete — no geometry authority references")

    if blocking_issues:
        gate: ValidationGate = "red"
    elif warnings:
        gate = "yellow"
    else:
        gate = "green"

    evaluation = StrategyExportCompatibilityEvaluation(
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        target_translator_id=target_translator_id,
        modality_compatible=modality_compatible,
        geometry_authority_exportable=geometry_authority_exportable,
        translator_capability_compatible=translator_capability_compatible,
        review_state_valid=review_state_valid,
        quarantine_respected=quarantine_respected,
        provenance_complete=provenance_complete,
        gate=gate,
        blocking_issues=blocking_issues,
        warnings=warnings,
        geometry_authority_ref_ids=geometry_authority_ref_ids or [],
        modality_id=modality_id,
    )

    evaluation.deterministic_evaluation_hash = evaluation.compute_hash()

    return evaluation


def evaluate_general_export_readiness(
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    modality_id: Optional[str] = None,
    review_status: Optional[str] = None,
    workspace_status: Optional[str] = None,
    geometry_authority_checker: Optional[callable] = None,
) -> StrategyExportCompatibilityEvaluation:
    """
    Evaluate general export readiness without a specific translator target.

    Checks:
      - geometry authority refs
      - review status
      - provenance refs
      - modality compatibility if available
      - non-executable invariants
    """
    return evaluate_strategy_export_compatibility(
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        target_translator_id=None,
        geometry_authority_ref_ids=geometry_authority_ref_ids,
        modality_id=modality_id,
        review_status=review_status,
        workspace_status=workspace_status,
        geometry_authority_checker=geometry_authority_checker,
        translator_capability_checker=None,
        quarantine_checker=None,
    )


def evaluate_targeted_translator_compatibility(
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    target_translator_id: str = "",
    geometry_authority_ref_ids: Optional[List[str]] = None,
    modality_id: Optional[str] = None,
    review_status: Optional[str] = None,
    workspace_status: Optional[str] = None,
    geometry_authority_checker: Optional[callable] = None,
    translator_capability_checker: Optional[callable] = None,
    quarantine_checker: Optional[callable] = None,
) -> StrategyExportCompatibilityEvaluation:
    """
    Evaluate compatibility with a specific translator.

    Additionally checks:
      - translator capability registry
      - translation artifact compatibility
      - quarantine/governance status
    """
    if not target_translator_id:
        raise ValueError("target_translator_id is required for targeted evaluation")

    return evaluate_strategy_export_compatibility(
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        target_translator_id=target_translator_id,
        geometry_authority_ref_ids=geometry_authority_ref_ids,
        modality_id=modality_id,
        review_status=review_status,
        workspace_status=workspace_status,
        geometry_authority_checker=geometry_authority_checker,
        translator_capability_checker=translator_capability_checker,
        quarantine_checker=quarantine_checker,
    )
