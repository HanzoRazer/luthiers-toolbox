"""
Post-Freeze Expansion Readiness

CAM Dev Order 8A: Readiness evaluation for post-freeze proposals.

Provides:
  - PostFreezeExpansionReadiness model
  - Gate classification (green/yellow/red)
  - Freeze compatibility checking

8A invariants:
  - implementation_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Readiness evaluation classifies proposals for human review.
  It does not authorize implementation, execution, or machine output.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


PostFreezeGate = Literal["green", "yellow", "red"]


class PostFreezeExpansionReadiness(BaseModel):
    """
    Post-freeze expansion readiness evaluation.

    Classifies a proposal's readiness for human review.

    8A invariants (model-enforced):
      - implementation_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    readiness_id: str = Field(
        default_factory=lambda: f"pfer-{uuid4().hex[:12]}",
        description="Unique readiness identifier"
    )

    proposal_id: str = Field(
        ...,
        description="Proposal ID being evaluated"
    )

    freeze_compatible: bool = Field(
        default=True,
        description="Whether proposal is compatible with frozen baseline"
    )

    freeze_exists: bool = Field(
        default=False,
        description="Whether referenced freeze exists in 7Z registry"
    )

    freeze_status: Optional[str] = Field(
        default=None,
        description="Status of referenced freeze (if found)"
    )

    freeze_blocking_issues: List[str] = Field(
        default_factory=list,
        description="Blocking issues from referenced freeze"
    )

    required_reviews_declared: bool = Field(
        default=False,
        description="Whether required reviews are declared"
    )

    no_execution_authority: bool = Field(
        default=True,
        description="Confirms execution is not requested"
    )

    no_machine_output_authority: bool = Field(
        default=True,
        description="Confirms machine output is not requested"
    )

    ontology_mutation_requested: bool = Field(
        default=False,
        description="Whether ontology mutation is requested"
    )

    baseline_rewrite_requested: bool = Field(
        default=False,
        description="Whether baseline rewrite is requested"
    )

    gate: PostFreezeGate = Field(
        default="yellow",
        description="Gate classification: green, yellow, or red"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Blocking issues preventing green gate"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings that cause yellow gate"
    )

    # 8A invariants
    implementation_authorized: bool = Field(
        default=False,
        description="Always False — 8A does not authorize implementation"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 8A does not authorize execution"
    )

    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 8A does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_readiness_hash: str = Field(
        default="",
        description="Deterministic hash of readiness state"
    )

    @model_validator(mode="after")
    def enforce_8a_invariants(self) -> "PostFreezeExpansionReadiness":
        """Enforce 8A invariants."""
        if self.implementation_authorized:
            raise ValueError(
                "8A invariant violation: implementation_authorized must be False — "
                "8A does not authorize implementation"
            )
        if self.execution_authorized:
            raise ValueError(
                "8A invariant violation: execution_authorized must be False — "
                "8A does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "8A invariant violation: machine_output_allowed must be False — "
                "8A does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of readiness state."""
        hash_input = {
            "proposal_id": self.proposal_id,
            "freeze_compatible": self.freeze_compatible,
            "freeze_exists": self.freeze_exists,
            "freeze_status": self.freeze_status,
            "required_reviews_declared": self.required_reviews_declared,
            "no_execution_authority": self.no_execution_authority,
            "no_machine_output_authority": self.no_machine_output_authority,
            "ontology_mutation_requested": self.ontology_mutation_requested,
            "baseline_rewrite_requested": self.baseline_rewrite_requested,
            "gate": self.gate,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def classify_post_freeze_gate(
    baseline_rewrite_requested: bool,
    execution_authorized: bool,
    machine_output_allowed: bool,
    implementation_authorized: bool,
    ontology_mutation_requested: bool,
    depends_on_freeze_id: Optional[str],
    freeze_exists: bool,
    required_reviews_declared: bool,
    target_layer_clear: bool,
    governance_risks_complete: bool,
) -> Tuple[PostFreezeGate, List[str], List[str]]:
    """
    Classify post-freeze expansion gate.

    RED conditions:
      - baseline_rewrite_requested
      - execution_authorized == True
      - machine_output_allowed == True
      - implementation_authorized == True
      - ontology_mutation_requested without explicit governance order

    YELLOW conditions:
      - depends_on_freeze_id is None (missing freeze reference)
      - depends_on_freeze_id provided but not found (stronger warning)
      - required_reviews not declared
      - unclear target layer
      - incomplete governance risks

    GREEN:
      - freeze compatible
      - required reviews declared
      - no execution authority
      - no machine output authority
      - no baseline rewrite

    Returns:
        (gate, blocking_issues, warnings)
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # RED conditions
    if baseline_rewrite_requested:
        blocking_issues.append("Baseline rewrite requested — requires explicit governance approval")

    if execution_authorized:
        blocking_issues.append("Execution authority requested — 8A does not authorize execution")

    if machine_output_allowed:
        blocking_issues.append("Machine output requested — 8A does not allow machine output")

    if implementation_authorized:
        blocking_issues.append("Implementation authority requested — 8A does not authorize implementation")

    if ontology_mutation_requested:
        blocking_issues.append("Ontology mutation requested — requires explicit future governance order")

    if blocking_issues:
        return "red", blocking_issues, warnings

    # YELLOW conditions
    if depends_on_freeze_id is None:
        warnings.append("Missing freeze reference — incomplete governance linkage")
    elif not freeze_exists:
        warnings.append(f"Freeze reference '{depends_on_freeze_id}' not found — verify freeze ID")

    if not required_reviews_declared:
        warnings.append("Required reviews not declared")

    if not target_layer_clear:
        warnings.append("Target layer unclear")

    if not governance_risks_complete:
        warnings.append("Governance risks list may be incomplete")

    if warnings:
        return "yellow", blocking_issues, warnings

    return "green", blocking_issues, warnings


def build_post_freeze_readiness_hash(readiness: PostFreezeExpansionReadiness) -> str:
    """Build deterministic hash for readiness evaluation."""
    return readiness.compute_hash()


def validate_freeze_compatibility(
    depends_on_freeze_id: Optional[str],
) -> Tuple[bool, bool, Optional[str], List[str]]:
    """
    Validate freeze compatibility by checking 7Z registry.

    Returns:
        (freeze_compatible, freeze_exists, freeze_status, freeze_blocking_issues)
    """
    if depends_on_freeze_id is None:
        return True, False, None, []

    # Try to resolve freeze in 7Z registry
    try:
        from .governance_freeze_registry import get_governance_freeze
        freeze = get_governance_freeze(depends_on_freeze_id)
        if freeze:
            return True, True, freeze.status, list(getattr(freeze, 'blocking_issues', []) or [])
        else:
            return True, False, None, []
    except ImportError:
        return True, False, None, []


def detect_baseline_rewrite_request(
    baseline_rewrite_requested: bool,
    governance_risks: List[str],
) -> bool:
    """
    Detect baseline rewrite request.

    Primary detection is from explicit field.
    Free-text governance_risks can produce warnings but not RED.
    """
    return baseline_rewrite_requested


def detect_execution_authority_request(
    execution_authorized: bool,
    machine_output_allowed: bool,
    implementation_authorized: bool,
) -> bool:
    """Detect any execution authority request."""
    return execution_authorized or machine_output_allowed or implementation_authorized


def get_readiness_summary(readiness: PostFreezeExpansionReadiness) -> Dict[str, Any]:
    """Get readiness summary for API response."""
    return {
        "readiness_id": readiness.readiness_id,
        "proposal_id": readiness.proposal_id,
        "freeze_compatible": readiness.freeze_compatible,
        "freeze_exists": readiness.freeze_exists,
        "freeze_status": readiness.freeze_status,
        "required_reviews_declared": readiness.required_reviews_declared,
        "no_execution_authority": readiness.no_execution_authority,
        "no_machine_output_authority": readiness.no_machine_output_authority,
        "ontology_mutation_requested": readiness.ontology_mutation_requested,
        "baseline_rewrite_requested": readiness.baseline_rewrite_requested,
        "gate": readiness.gate,
        "blocking_issue_count": len(readiness.blocking_issues),
        "warning_count": len(readiness.warnings),
        "implementation_authorized": readiness.implementation_authorized,
        "execution_authorized": readiness.execution_authorized,
        "machine_output_allowed": readiness.machine_output_allowed,
        "created_at": readiness.created_at.isoformat(),
    }


def get_readiness_status_message(readiness: PostFreezeExpansionReadiness) -> str:
    """Get human-readable status message for readiness."""
    if readiness.gate == "green":
        return "Proposal ready for human review — all checks passed"
    elif readiness.gate == "yellow":
        warning_parts = []
        if not readiness.freeze_exists and readiness.proposal_id:
            warning_parts.append("freeze reference missing or not found")
        if not readiness.required_reviews_declared:
            warning_parts.append("reviews not declared")
        if readiness.warnings:
            warning_parts.append(f"{len(readiness.warnings)} warning(s)")
        return f"Proposal needs attention: {', '.join(warning_parts) or 'see warnings'}"
    else:
        return f"Proposal blocked: {'; '.join(readiness.blocking_issues) or 'see blocking issues'}"
