"""
Federation CI Enforcement

CAM Dev Order 7Y: CI enforcement summary and classification.

Provides:
  - FederationCIEnforcementSummary model
  - CI status classification (pass/warn/fail)
  - Baseline comparison
  - Enforcement summary building

7Y invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  CI enforcement makes federation health measurable.
  It does not repair drift or mutate state.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .federation_drift_baseline import FederationDriftBaseline
from .federated_semantic_registry import build_cross_domain_summary


FederationCIStatus = Literal["pass", "warn", "fail"]


class FederationCIEnforcementSummary(BaseModel):
    """
    Federation CI enforcement summary.

    Records federation health state for CI evaluation.

    7Y invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    summary_id: str = Field(
        default_factory=lambda: f"fces-{uuid4().hex[:12]}",
        description="Unique summary identifier"
    )

    baseline_id: Optional[str] = Field(
        default=None,
        description="Baseline ID used for comparison"
    )

    total_federation_refs: int = Field(
        default=0,
        description="Total federation references"
    )
    total_continuity_records: int = Field(
        default=0,
        description="Total continuity records"
    )
    total_federated_packages: int = Field(
        default=0,
        description="Total federated packages"
    )

    authority_override_count: int = Field(
        default=0,
        description="Count of authority overrides detected"
    )
    ontology_mutation_attempt_count: int = Field(
        default=0,
        description="Count of ontology mutation attempts"
    )
    fragmented_federation_count: int = Field(
        default=0,
        description="Count of fragmented federations"
    )
    invalid_continuity_count: int = Field(
        default=0,
        description="Count of invalid continuity records"
    )
    warning_count: int = Field(
        default=0,
        description="Total warning count"
    )
    blocking_issue_count: int = Field(
        default=0,
        description="Total blocking issue count"
    )

    baseline_mismatch_detected: bool = Field(
        default=False,
        description="Whether baseline mismatch was detected"
    )

    status: FederationCIStatus = Field(
        default="pass",
        description="CI status: pass, warn, or fail"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Specific blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Specific warnings"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7Y does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7Y does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_summary_hash: str = Field(
        default="",
        description="Deterministic hash of summary state"
    )

    @model_validator(mode="after")
    def enforce_7y_invariants(self) -> "FederationCIEnforcementSummary":
        """Enforce 7Y invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7Y invariant violation: execution_authorized must be False — "
                "7Y does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7Y invariant violation: machine_output_allowed must be False — "
                "7Y does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of summary state."""
        hash_input = {
            "baseline_id": self.baseline_id,
            "total_federation_refs": self.total_federation_refs,
            "total_continuity_records": self.total_continuity_records,
            "total_federated_packages": self.total_federated_packages,
            "authority_override_count": self.authority_override_count,
            "ontology_mutation_attempt_count": self.ontology_mutation_attempt_count,
            "fragmented_federation_count": self.fragmented_federation_count,
            "invalid_continuity_count": self.invalid_continuity_count,
            "warning_count": self.warning_count,
            "blocking_issue_count": self.blocking_issue_count,
            "baseline_mismatch_detected": self.baseline_mismatch_detected,
            "status": self.status,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def classify_federation_ci_status(
    authority_override_count: int,
    ontology_mutation_attempt_count: int,
    invalid_continuity_count: int,
    blocking_issue_count: int,
    execution_authorized: bool,
    machine_output_allowed: bool,
    fragmented_federation_count: int,
    warning_count: int,
    baseline_mismatch_detected: bool,
    allowed_warning_count: int = 0,
    allowed_fragmented_federation_count: int = 0,
) -> FederationCIStatus:
    """
    Classify federation CI status.

    FAIL conditions:
      - authority_override_count > 0
      - ontology_mutation_attempt_count > 0
      - invalid_continuity_count > 0
      - blocking_issue_count > 0
      - execution_authorized == True
      - machine_output_allowed == True

    WARN conditions:
      - fragmented_federation_count > allowed threshold
      - warning_count > allowed threshold
      - baseline_mismatch_detected == True

    PASS: No failures, no warnings above threshold
    """
    # Check FAIL conditions
    if authority_override_count > 0:
        return "fail"
    if ontology_mutation_attempt_count > 0:
        return "fail"
    if invalid_continuity_count > 0:
        return "fail"
    if blocking_issue_count > 0:
        return "fail"
    if execution_authorized:
        return "fail"
    if machine_output_allowed:
        return "fail"

    # Check WARN conditions
    if fragmented_federation_count > allowed_fragmented_federation_count:
        return "warn"
    if warning_count > allowed_warning_count:
        return "warn"
    if baseline_mismatch_detected:
        return "warn"

    return "pass"


def compare_federation_to_baseline(
    total_federation_refs: int,
    total_continuity_records: int,
    total_federated_packages: int,
    baseline: FederationDriftBaseline,
) -> Tuple[bool, List[str]]:
    """
    Compare federation state to baseline.

    Returns:
        (mismatch_detected, mismatch_warnings)
    """
    mismatches: List[str] = []

    if baseline.expected_federation_ref_count is not None:
        if total_federation_refs != baseline.expected_federation_ref_count:
            mismatches.append(
                f"Federation ref count mismatch: expected {baseline.expected_federation_ref_count}, "
                f"got {total_federation_refs}"
            )

    if baseline.expected_continuity_record_count is not None:
        if total_continuity_records != baseline.expected_continuity_record_count:
            mismatches.append(
                f"Continuity record count mismatch: expected {baseline.expected_continuity_record_count}, "
                f"got {total_continuity_records}"
            )

    if baseline.expected_package_count is not None:
        if total_federated_packages != baseline.expected_package_count:
            mismatches.append(
                f"Package count mismatch: expected {baseline.expected_package_count}, "
                f"got {total_federated_packages}"
            )

    return len(mismatches) > 0, mismatches


def build_federation_ci_summary(
    baseline: Optional[FederationDriftBaseline] = None,
) -> FederationCIEnforcementSummary:
    """
    Build federation CI enforcement summary.

    Evaluates current federation state from 7X registry.
    Optionally compares against baseline.
    """
    # Get current federation state from 7X
    raw_summary = build_cross_domain_summary()

    total_federation_refs = raw_summary["total_federation_refs"]
    total_continuity_records = raw_summary["total_continuity_records"]
    total_federated_packages = raw_summary["total_federated_packages"]
    authority_override_count = raw_summary["authority_override_count"]
    ontology_mutation_attempt_count = raw_summary["ontology_mutation_attempt_count"]
    fragmented_federation_count = raw_summary["fragmented_federation_count"]
    invalid_continuity_count = raw_summary["invalid_continuity_count"]
    warning_count = raw_summary["warning_count"]
    blocking_issue_count = raw_summary["blocking_issue_count"]

    # Build initial summary
    summary = FederationCIEnforcementSummary(
        baseline_id=baseline.baseline_id if baseline else None,
        total_federation_refs=total_federation_refs,
        total_continuity_records=total_continuity_records,
        total_federated_packages=total_federated_packages,
        authority_override_count=authority_override_count,
        ontology_mutation_attempt_count=ontology_mutation_attempt_count,
        fragmented_federation_count=fragmented_federation_count,
        invalid_continuity_count=invalid_continuity_count,
        warning_count=warning_count,
        blocking_issue_count=blocking_issue_count,
    )

    # Compare to baseline if provided
    allowed_warning_count = 0
    allowed_fragmented_federation_count = 0

    if baseline:
        allowed_warning_count = baseline.allowed_warning_count
        allowed_fragmented_federation_count = baseline.allowed_fragmented_federation_count

        mismatch_detected, mismatch_warnings = compare_federation_to_baseline(
            total_federation_refs,
            total_continuity_records,
            total_federated_packages,
            baseline,
        )
        summary.baseline_mismatch_detected = mismatch_detected
        summary.warnings.extend(mismatch_warnings)

    # Classify status
    summary.status = classify_federation_ci_status(
        authority_override_count=authority_override_count,
        ontology_mutation_attempt_count=ontology_mutation_attempt_count,
        invalid_continuity_count=invalid_continuity_count,
        blocking_issue_count=blocking_issue_count,
        execution_authorized=False,
        machine_output_allowed=False,
        fragmented_federation_count=fragmented_federation_count,
        warning_count=warning_count + len(summary.warnings),
        baseline_mismatch_detected=summary.baseline_mismatch_detected,
        allowed_warning_count=allowed_warning_count,
        allowed_fragmented_federation_count=allowed_fragmented_federation_count,
    )

    # Add blocking issues if failing
    if authority_override_count > 0:
        summary.blocking_issues.append(f"{authority_override_count} authority override(s) detected")
    if ontology_mutation_attempt_count > 0:
        summary.blocking_issues.append(f"{ontology_mutation_attempt_count} ontology mutation attempt(s)")
    if invalid_continuity_count > 0:
        summary.blocking_issues.append(f"{invalid_continuity_count} invalid continuity record(s)")
    if blocking_issue_count > 0:
        summary.blocking_issues.append(f"{blocking_issue_count} blocking issue(s) in federation state")

    summary.deterministic_summary_hash = summary.compute_hash()
    return summary


def evaluate_against_baseline(
    baseline: FederationDriftBaseline,
) -> FederationCIEnforcementSummary:
    """
    Evaluate current federation state against a baseline.

    Wrapper for build_federation_ci_summary with required baseline.
    """
    return build_federation_ci_summary(baseline=baseline)


def count_federation_authority_overrides() -> int:
    """Count authority overrides in current federation state."""
    summary = build_cross_domain_summary()
    return summary["authority_override_count"]


def count_fragmented_federation() -> int:
    """Count fragmented federations in current state."""
    summary = build_cross_domain_summary()
    return summary["fragmented_federation_count"]


def count_invalid_continuity() -> int:
    """Count invalid continuity records in current state."""
    summary = build_cross_domain_summary()
    return summary["invalid_continuity_count"]


def count_federation_warnings() -> int:
    """Count warnings in current federation state."""
    summary = build_cross_domain_summary()
    return summary["warning_count"]


def get_summary_status_message(summary: FederationCIEnforcementSummary) -> str:
    """Get human-readable status message for summary."""
    if summary.status == "pass":
        return "Federation CI passed — all checks clean"
    elif summary.status == "warn":
        warning_parts = []
        if summary.baseline_mismatch_detected:
            warning_parts.append("baseline mismatch")
        if summary.fragmented_federation_count > 0:
            warning_parts.append(f"{summary.fragmented_federation_count} fragmented")
        if summary.warnings:
            warning_parts.append(f"{len(summary.warnings)} warning(s)")
        return f"Federation CI warning: {', '.join(warning_parts) or 'see warnings'}"
    else:
        return f"Federation CI failed: {'; '.join(summary.blocking_issues) or 'see blocking issues'}"


def build_ci_summary_hash(summary: FederationCIEnforcementSummary) -> str:
    """Build deterministic hash for a CI summary."""
    return summary.compute_hash()


def get_enforcement_summary_dict(summary: FederationCIEnforcementSummary) -> Dict[str, Any]:
    """Get summary as dictionary for API response."""
    return {
        "summary_id": summary.summary_id,
        "baseline_id": summary.baseline_id,
        "total_federation_refs": summary.total_federation_refs,
        "total_continuity_records": summary.total_continuity_records,
        "total_federated_packages": summary.total_federated_packages,
        "authority_override_count": summary.authority_override_count,
        "ontology_mutation_attempt_count": summary.ontology_mutation_attempt_count,
        "fragmented_federation_count": summary.fragmented_federation_count,
        "invalid_continuity_count": summary.invalid_continuity_count,
        "warning_count": summary.warning_count,
        "blocking_issue_count": summary.blocking_issue_count,
        "baseline_mismatch_detected": summary.baseline_mismatch_detected,
        "status": summary.status,
        "blocking_issues": summary.blocking_issues,
        "warnings": summary.warnings,
        "status_message": get_summary_status_message(summary),
    }
