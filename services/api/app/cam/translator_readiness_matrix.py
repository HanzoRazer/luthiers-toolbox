"""
Translator Readiness Matrix + Promotion Constraints

CAM Dev Order 7G: Execution readiness evaluation for translators.

This module evaluates translator readiness for execution based on:
  - Governance state (maturity, execution_state)
  - Provenance lineage (if available)
  - Authorization evaluation (from 7E)
  - Promotion constraints

7G invariants:
  - execution_ready: always false in 7G
  - machine_operation_authorized: always false
  - promotion_authorized: always false (requires human approval)

Key distinction:
  Readiness evaluation ≠ execution authorization
  Readiness determines what WOULD BE required, not what IS authorized.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from app.cam.translator_execution_quarantine import ExecutionQuarantineSummary

from app.cam.translator_capability_registry import (
    TranslatorCapability,
    TranslatorMaturity,
    ExecutionState,
    get_translator_capability,
)
from app.cam.translation_artifact import TranslationArtifact
from app.cam.translation_artifact_authorization import (
    TranslationArtifactAuthorizationEvaluation,
    evaluate_translation_artifact_authorization,
)
from app.cam.translation_artifact_provenance import (
    TranslationArtifactProvenance,
    get_provenance,
    get_provenance_by_artifact,
)


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

ReadinessLevel = Literal[
    "experimental",           # Level 1: Unstable prototype
    "governed_experimental",  # Level 2: Regression-tracked
    "stable_candidate",       # Level 3: Deterministic, validated
    "production",             # Level 4: Full production approval
]

ReadinessGate = Literal["green", "yellow", "red"]

PromotionBlocker = Literal[
    "missing_regression_corpus",
    "insufficient_test_coverage",
    "topology_verification_failed",
    "determinism_not_guaranteed",
    "external_validation_missing",
    "stability_period_incomplete",
    "governance_approval_required",
    "provenance_lineage_missing",
    "authorization_gate_red",
    "execution_state_incompatible",
    "maturity_insufficient",
]


# -----------------------------------------------------------------------------
# Promotion Requirements Matrix
# -----------------------------------------------------------------------------

PROMOTION_REQUIREMENTS: Dict[ReadinessLevel, Dict[str, Any]] = {
    "experimental": {
        "from_level": None,
        "required_maturity": "placeholder",
        "required_execution_state": ["validation_only", "execution_disabled"],
        "min_test_fixtures": 0,
        "min_test_pass_rate": 0.0,
        "requires_regression_corpus": False,
        "requires_topology_verification": False,
        "requires_determinism_guarantee": False,
        "requires_external_validation": False,
        "stability_days_required": 0,
        "requires_governance_approval": False,
    },
    "governed_experimental": {
        "from_level": "experimental",
        "required_maturity": "candidate",
        "required_execution_state": ["validation_only", "execution_planned"],
        "min_test_fixtures": 5,
        "min_test_pass_rate": 0.80,
        "requires_regression_corpus": True,
        "requires_topology_verification": True,
        "requires_determinism_guarantee": False,
        "requires_external_validation": False,
        "stability_days_required": 0,
        "requires_governance_approval": False,
    },
    "stable_candidate": {
        "from_level": "governed_experimental",
        "required_maturity": "governed",
        "required_execution_state": ["execution_planned", "governed_execution"],
        "min_test_fixtures": 10,
        "min_test_pass_rate": 1.00,
        "requires_regression_corpus": True,
        "requires_topology_verification": True,
        "requires_determinism_guarantee": True,
        "requires_external_validation": True,
        "stability_days_required": 30,
        "requires_governance_approval": True,
    },
    "production": {
        "from_level": "stable_candidate",
        "required_maturity": "canonical",
        "required_execution_state": ["governed_execution"],
        "min_test_fixtures": 20,
        "min_test_pass_rate": 1.00,
        "requires_regression_corpus": True,
        "requires_topology_verification": True,
        "requires_determinism_guarantee": True,
        "requires_external_validation": True,
        "stability_days_required": 90,
        "requires_governance_approval": True,
    },
}


# -----------------------------------------------------------------------------
# Maturity to Readiness Level Mapping
# -----------------------------------------------------------------------------

MATURITY_TO_READINESS: Dict[TranslatorMaturity, ReadinessLevel] = {
    "placeholder": "experimental",
    "candidate": "governed_experimental",
    "governed": "stable_candidate",
    "canonical": "production",
}


# -----------------------------------------------------------------------------
# Readiness Evaluation Summary
# -----------------------------------------------------------------------------

class TranslatorReadinessEvaluationSummary(BaseModel):
    """
    Lightweight readiness summary for lifecycle reports.
    """

    translator_id: str = Field(..., description="Translator identifier")
    current_level: ReadinessLevel = Field(..., description="Current readiness level")
    target_level: Optional[ReadinessLevel] = Field(
        default=None, description="Target promotion level"
    )
    gate: ReadinessGate = Field(..., description="Readiness gate status")
    promotion_eligible: bool = Field(
        default=False, description="Whether promotion is possible"
    )

    # 7G invariants
    execution_ready: bool = Field(
        default=False, description="Always false in 7G"
    )


# -----------------------------------------------------------------------------
# Full Readiness Evaluation Model
# -----------------------------------------------------------------------------

class TranslatorReadinessEvaluation(BaseModel):
    """
    Full readiness evaluation for a translator.

    Evaluates whether a translator meets requirements for its
    current or target readiness level.

    7G invariants (model-enforced):
      - execution_ready: always false
      - machine_operation_authorized: always false
      - promotion_authorized: always false
    """

    # --- Identity ---
    translator_id: str = Field(..., description="Translator identifier")
    evaluation_id: str = Field(
        default_factory=lambda: f"readiness-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        description="Evaluation identifier"
    )

    # --- Readiness Levels ---
    current_level: ReadinessLevel = Field(..., description="Current readiness level")
    target_level: Optional[ReadinessLevel] = Field(
        default=None, description="Target promotion level (if evaluating promotion)"
    )

    # --- Gate ---
    gate: ReadinessGate = Field(..., description="Readiness gate status")

    # --- Evaluation Results ---
    requirements_met: Dict[str, bool] = Field(
        default_factory=dict,
        description="Requirements check results"
    )
    promotion_blockers: List[PromotionBlocker] = Field(
        default_factory=list,
        description="Blocking issues for promotion"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    # --- Capability State ---
    capability_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Translator capability at evaluation time"
    )

    # --- Authorization Integration (7E) ---
    authorization_gate: Optional[ReadinessGate] = Field(
        default=None,
        description="Authorization gate from 7E (if artifact provided)"
    )

    # --- Provenance Integration (7F) ---
    has_provenance_lineage: bool = Field(
        default=False,
        description="Whether provenance lineage exists"
    )
    provenance_count: int = Field(
        default=0,
        description="Number of provenance records"
    )

    # --- Quarantine Integration (7H) ---
    execution_quarantine_summary: Optional[Any] = Field(
        default=None,
        description="Execution quarantine summary from 7H (if evaluated)"
    )

    # --- 7G Invariants ---
    execution_ready: bool = Field(
        default=False,
        description="Always false in 7G — no execution readiness"
    )
    machine_operation_authorized: bool = Field(
        default=False,
        description="Always false in 7G — no machine operation"
    )
    promotion_authorized: bool = Field(
        default=False,
        description="Always false — promotion requires human approval"
    )
    promotion_eligible: bool = Field(
        default=False,
        description="Whether promotion is possible (gate != red)"
    )

    # --- Timestamps ---
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evaluation metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_7g_invariants(self) -> "TranslatorReadinessEvaluation":
        """
        Enforce 7G invariants:
        - execution_ready must be False
        - machine_operation_authorized must be False
        - promotion_authorized must be False
        - promotion_eligible requires gate != red
        """
        if self.execution_ready:
            raise ValueError(
                "execution_ready must be False in 7G — "
                "no execution readiness determination"
            )

        if self.machine_operation_authorized:
            raise ValueError(
                "machine_operation_authorized must be False in 7G — "
                "no machine operation authorization"
            )

        if self.promotion_authorized:
            raise ValueError(
                "promotion_authorized must be False in 7G — "
                "promotion requires human approval"
            )

        if self.gate == "red" and self.promotion_eligible:
            raise ValueError(
                "promotion_eligible cannot be True when gate is red"
            )

        return self

    def to_summary(self) -> TranslatorReadinessEvaluationSummary:
        """Create lightweight summary for lifecycle reports."""
        return TranslatorReadinessEvaluationSummary(
            translator_id=self.translator_id,
            current_level=self.current_level,
            target_level=self.target_level,
            gate=self.gate,
            promotion_eligible=self.promotion_eligible,
            execution_ready=False,
        )


# -----------------------------------------------------------------------------
# Readiness Evaluation Index (In-Memory)
# -----------------------------------------------------------------------------

READINESS_INDEX: Dict[str, TranslatorReadinessEvaluation] = {}


def register_readiness_evaluation(evaluation: TranslatorReadinessEvaluation) -> None:
    """Register evaluation in the in-memory index."""
    key = f"{evaluation.translator_id}:{evaluation.evaluation_id}"
    READINESS_INDEX[key] = evaluation


def get_readiness_evaluation(
    translator_id: str,
    evaluation_id: Optional[str] = None,
) -> Optional[TranslatorReadinessEvaluation]:
    """Get readiness evaluation by translator ID and optional evaluation ID."""
    if evaluation_id:
        key = f"{translator_id}:{evaluation_id}"
        return READINESS_INDEX.get(key)

    # Return most recent evaluation for translator
    evaluations = [
        e for e in READINESS_INDEX.values()
        if e.translator_id == translator_id
    ]
    if not evaluations:
        return None
    return max(evaluations, key=lambda e: e.evaluated_at)


def list_readiness_evaluations(
    translator_id: Optional[str] = None,
) -> List[TranslatorReadinessEvaluation]:
    """List readiness evaluations, optionally filtered by translator."""
    if translator_id:
        return [
            e for e in READINESS_INDEX.values()
            if e.translator_id == translator_id
        ]
    return list(READINESS_INDEX.values())


def clear_readiness_index() -> None:
    """Clear the readiness index (for testing)."""
    READINESS_INDEX.clear()


# -----------------------------------------------------------------------------
# Readiness Evaluator
# -----------------------------------------------------------------------------

def _derive_readiness_level(capability: TranslatorCapability) -> ReadinessLevel:
    """Derive readiness level from capability maturity."""
    return MATURITY_TO_READINESS.get(capability.maturity, "experimental")


def _check_promotion_requirements(
    capability: TranslatorCapability,
    current_level: ReadinessLevel,
    target_level: ReadinessLevel,
    artifact: Optional[TranslationArtifact] = None,
    provenance: Optional[TranslationArtifactProvenance] = None,
) -> tuple[Dict[str, bool], List[PromotionBlocker], List[str]]:
    """
    Check whether promotion requirements are met.

    Returns:
        (requirements_met, blockers, warnings)
    """
    requirements = PROMOTION_REQUIREMENTS.get(target_level, {})
    requirements_met: Dict[str, bool] = {}
    blockers: List[PromotionBlocker] = []
    warnings: List[str] = []

    # Check from_level requirement
    expected_from = requirements.get("from_level")
    if expected_from and current_level != expected_from:
        requirements_met["from_level"] = False
        warnings.append(
            f"Promotion to {target_level} typically requires {expected_from}, "
            f"current level is {current_level}"
        )
    else:
        requirements_met["from_level"] = True

    # Check maturity requirement
    required_maturity = requirements.get("required_maturity")
    if required_maturity:
        maturity_ok = capability.maturity == required_maturity
        requirements_met["maturity"] = maturity_ok
        if not maturity_ok:
            blockers.append("maturity_insufficient")
            warnings.append(
                f"Target level {target_level} requires maturity={required_maturity}, "
                f"current is {capability.maturity}"
            )

    # Check execution_state requirement
    required_states = requirements.get("required_execution_state", [])
    if required_states:
        state_ok = capability.execution_state in required_states
        requirements_met["execution_state"] = state_ok
        if not state_ok:
            blockers.append("execution_state_incompatible")
            warnings.append(
                f"Target level {target_level} requires execution_state in {required_states}, "
                f"current is {capability.execution_state}"
            )

    # Check governance approval requirement
    if requirements.get("requires_governance_approval"):
        requirements_met["governance_approval"] = False
        blockers.append("governance_approval_required")
        warnings.append("Promotion requires governance board approval")

    # Check provenance lineage if artifact provided
    if artifact:
        provenances = get_provenance_by_artifact(artifact.artifact_id)
        has_provenance = len(provenances) > 0
        requirements_met["provenance_lineage"] = has_provenance
        if not has_provenance and target_level in ("stable_candidate", "production"):
            blockers.append("provenance_lineage_missing")
            warnings.append("Provenance lineage required for stable/production levels")

    # Note: The following requirements would need integration with test/regression
    # systems that are out of scope for 7G. They're marked as "not_evaluated".
    for req_key in [
        "requires_regression_corpus",
        "requires_topology_verification",
        "requires_determinism_guarantee",
        "requires_external_validation",
    ]:
        if requirements.get(req_key):
            requirements_met[req_key] = False  # Cannot evaluate in 7G
            warnings.append(f"{req_key} not evaluated in 7G scope")

    return requirements_met, blockers, warnings


def evaluate_translator_readiness(
    translator_id: str,
    target_level: Optional[ReadinessLevel] = None,
    artifact: Optional[TranslationArtifact] = None,
) -> TranslatorReadinessEvaluation:
    """
    Evaluate translator readiness for current or target level.

    This is READINESS EVALUATION, not execution authorization.

    Checks:
      1. Translator exists in capability registry
      2. Current readiness level derived from maturity
      3. Target level promotion requirements (if specified)
      4. Authorization gate (if artifact provided)
      5. Provenance lineage (if artifact provided)

    Returns evaluation with:
      - gate: green/yellow/red
      - promotion_eligible: true if gate != red
      - execution_ready: always false
      - promotion_authorized: always false

    No DXF. No G-code. No machine output. No actual promotion.
    """
    blockers: List[PromotionBlocker] = []
    warnings: List[str] = []
    requirements_met: Dict[str, bool] = {}
    authorization_gate: Optional[ReadinessGate] = None
    has_provenance = False
    provenance_count = 0

    # --- Check 1: Translator exists ---
    capability = get_translator_capability(translator_id)

    if capability is None:
        return TranslatorReadinessEvaluation(
            translator_id=translator_id,
            current_level="experimental",
            target_level=target_level,
            gate="red",
            requirements_met={"translator_exists": False},
            promotion_blockers=["execution_state_incompatible"],
            warnings=[f"Translator '{translator_id}' not found in registry"],
            capability_snapshot={},
            execution_ready=False,
            machine_operation_authorized=False,
            promotion_authorized=False,
            promotion_eligible=False,
            metadata={
                "evaluation_type": "translator_readiness",
                "dev_order": "7G",
            },
        )

    requirements_met["translator_exists"] = True

    # --- Check 2: Derive current level ---
    current_level = _derive_readiness_level(capability)

    # --- Check 3: Authorization integration (if artifact provided) ---
    if artifact:
        auth_eval = evaluate_translation_artifact_authorization(artifact)
        authorization_gate = auth_eval.gate

        if auth_eval.gate == "red":
            blockers.append("authorization_gate_red")
            warnings.extend(auth_eval.blocking_issues)
        elif auth_eval.gate == "yellow":
            warnings.extend(auth_eval.warnings)

        # Check provenance
        provenances = get_provenance_by_artifact(artifact.artifact_id)
        has_provenance = len(provenances) > 0
        provenance_count = len(provenances)

    # --- Check 4: Target level requirements (if specified) ---
    if target_level:
        req_met, req_blockers, req_warnings = _check_promotion_requirements(
            capability=capability,
            current_level=current_level,
            target_level=target_level,
            artifact=artifact,
        )
        requirements_met.update(req_met)
        blockers.extend(req_blockers)
        warnings.extend(req_warnings)

    # --- Determine gate ---
    if blockers:
        gate: ReadinessGate = "red"
    elif warnings:
        gate = "yellow"
    else:
        gate = "green"

    # Gate propagation from authorization (RED > YELLOW > GREEN)
    if authorization_gate == "red" and gate != "red":
        gate = "red"
    elif authorization_gate == "yellow" and gate == "green":
        gate = "yellow"

    # Eligibility requires non-RED gate
    promotion_eligible = gate != "red"

    evaluation = TranslatorReadinessEvaluation(
        translator_id=translator_id,
        current_level=current_level,
        target_level=target_level,
        gate=gate,
        requirements_met=requirements_met,
        promotion_blockers=blockers,
        warnings=warnings,
        capability_snapshot=capability.model_dump(mode="json"),
        authorization_gate=authorization_gate,
        has_provenance_lineage=has_provenance,
        provenance_count=provenance_count,
        execution_ready=False,
        machine_operation_authorized=False,
        promotion_authorized=False,
        promotion_eligible=promotion_eligible,
        metadata={
            "evaluation_type": "translator_readiness",
            "dev_order": "7G",
            "maturity": capability.maturity,
            "execution_state": capability.execution_state,
        },
    )

    # Register in index
    register_readiness_evaluation(evaluation)

    return evaluation


def evaluate_translator_readiness_by_artifact(
    artifact: TranslationArtifact,
    target_level: Optional[ReadinessLevel] = None,
) -> TranslatorReadinessEvaluation:
    """
    Evaluate translator readiness using artifact's translator_id.

    Convenience wrapper that extracts translator_id from artifact.
    """
    return evaluate_translator_readiness(
        translator_id=artifact.translator_id,
        target_level=target_level,
        artifact=artifact,
    )


# -----------------------------------------------------------------------------
# Promotion Constraint Queries
# -----------------------------------------------------------------------------

def get_promotion_requirements(target_level: ReadinessLevel) -> Dict[str, Any]:
    """Get promotion requirements for a target level."""
    return PROMOTION_REQUIREMENTS.get(target_level, {})


def get_next_promotion_level(current_level: ReadinessLevel) -> Optional[ReadinessLevel]:
    """Get the next promotion level for a given level."""
    level_order: List[ReadinessLevel] = [
        "experimental",
        "governed_experimental",
        "stable_candidate",
        "production",
    ]
    try:
        idx = level_order.index(current_level)
        if idx < len(level_order) - 1:
            return level_order[idx + 1]
        return None
    except ValueError:
        return None


def can_promote(
    translator_id: str,
    target_level: Optional[ReadinessLevel] = None,
) -> tuple[bool, List[str]]:
    """
    Quick check whether translator can be promoted.

    Returns (can_promote, reasons).

    Note: This is eligibility, not authorization. Actual promotion
    requires human approval.
    """
    evaluation = evaluate_translator_readiness(
        translator_id=translator_id,
        target_level=target_level,
    )
    reasons = [str(b) for b in evaluation.promotion_blockers]
    return evaluation.promotion_eligible, reasons
