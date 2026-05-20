"""
Runtime Enforcement Policy Engine

CAM Dev Order 7P: Hard-coded governance rules for runtime enforcement.

This module provides:
  - Prohibited runtime actions (canonical list)
  - RED condition definitions (blocking)
  - YELLOW condition definitions (warnings)
  - Checkpoint evaluation logic
  - Severity classification
  - CI status determination

Policy is NOT configurable in 7P. This is boundary enforcement,
not tenant policy. Future configurability requires separate dev order.

7P invariants (always enforced):
  - execution_authorized = False
  - machine_output_allowed = False
  - serializer_execution_allowed = False
  - runtime_self_authorized = False

Guardrail:
  7P evaluates declared runtime-adjacent pathways for governance compliance.
  It does not intercept live traffic, invoke serializers, execute runtimes,
  or authorize machine output.
"""

from __future__ import annotations

from typing import List, Tuple

from app.cam.runtime_governance_enforcement import (
    CheckpointType,
    EnforcementCheckpoint,
    EnforcementCheckpointReport,
    EnforcementSeverity,
    GovernanceLinkage,
    ParsedPathway,
    RuntimeEnforcementRequest,
    RuntimeGovernanceEnforcementEvaluation,
    lookup_governance_linkage,
    parse_runtime_pathway,
    register_enforcement_evaluation,
    register_enforcement_report,
    list_enforcement_evaluations,
)


# -----------------------------------------------------------------------------
# Prohibited Runtime Actions (from 7H)
# -----------------------------------------------------------------------------

PROHIBITED_RUNTIME_ACTIONS: List[str] = [
    "DXF_generation",
    "SVG_generation",
    "G-code_generation",
    "serializer_invocation",
    "runtime_translator_execution",
    "plugin_loading",
    "machine_output",
    "subprocess_execution",
]


# -----------------------------------------------------------------------------
# RED Conditions (Blocking)
# -----------------------------------------------------------------------------

RED_CONDITIONS: List[str] = [
    "execution_authorized_true",
    "machine_output_allowed_true",
    "serializer_invocation_pathway_detected",
    "runtime_bypass_detected",
    "translator_execution_requested",
    "quarantine_violation",
    "unauthorized_export_routing",
    "runtime_self_authorization",
    "referenced_id_not_found",
    "machine_output_boundary_declared",
]


# -----------------------------------------------------------------------------
# YELLOW Conditions (Warnings)
# -----------------------------------------------------------------------------

YELLOW_CONDITIONS: List[str] = [
    "missing_provenance_references",
    "incomplete_governance_linkage",
    "missing_readiness_references",
    "weak_dispatch_classification",
    "unknown_pathway_type_no_execution",
    "missing_quarantine_reference",
    "missing_consumer_reference",
    "missing_ledger_reference",
]


# -----------------------------------------------------------------------------
# Checkpoint Type Descriptions
# -----------------------------------------------------------------------------

CHECKPOINT_DESCRIPTIONS: dict[CheckpointType, str] = {
    "quarantine_enforcement": "Validates against 7H execution quarantine state",
    "consumption_discipline": "Validates against 7N semantic consumption discipline",
    "ledger_lineage": "Validates against 7O consumption ledger and drift state",
    "pathway_classification": "Classifies pathway type and execution implications",
    "invariant_verification": "Verifies 7P invariants are maintained",
}


# -----------------------------------------------------------------------------
# Policy Evaluation Functions
# -----------------------------------------------------------------------------

def evaluate_pathway_classification(
    parsed: ParsedPathway,
) -> Tuple[EnforcementCheckpoint, List[str], List[str]]:
    """
    Evaluate pathway classification checkpoint.

    Returns: (checkpoint, blocking_issues, warnings)
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # Check for machine output boundary (always RED)
    if parsed.pathway_type == "machine_output_boundary":
        blocking_issues.append(
            f"Machine output boundary declared: {parsed.pathway_target}"
        )
        return (
            EnforcementCheckpoint(
                checkpoint_type="pathway_classification",
                checkpoint_passed=False,
                severity="red",
                message=f"Machine output boundary pathway detected: {parsed.raw_pathway}",
                blocking=True,
            ),
            blocking_issues,
            warnings,
        )

    # Check for serializer boundary
    if parsed.pathway_type == "serializer_boundary":
        blocking_issues.append(
            f"Serializer boundary declared: {parsed.pathway_target}"
        )
        return (
            EnforcementCheckpoint(
                checkpoint_type="pathway_classification",
                checkpoint_passed=False,
                severity="red",
                message=f"Serializer boundary pathway detected: {parsed.raw_pathway}",
                blocking=True,
            ),
            blocking_issues,
            warnings,
        )

    # Check for unknown pathway type
    if parsed.pathway_type == "unknown":
        if parsed.implies_execution:
            # Unknown type that implies execution = RED
            blocking_issues.append(
                f"Unknown pathway type with execution implication: {parsed.raw_pathway}"
            )
            return (
                EnforcementCheckpoint(
                    checkpoint_type="pathway_classification",
                    checkpoint_passed=False,
                    severity="red",
                    message=f"Unknown pathway type implies execution: {parsed.raw_pathway}",
                    blocking=True,
                ),
                blocking_issues,
                warnings,
            )
        else:
            # Unknown type without execution implication = YELLOW
            warnings.append(
                f"Unknown pathway type (no execution implied): {parsed.raw_pathway}"
            )
            return (
                EnforcementCheckpoint(
                    checkpoint_type="pathway_classification",
                    checkpoint_passed=True,
                    severity="yellow",
                    message=f"Unknown pathway type, no execution implied: {parsed.raw_pathway}",
                    blocking=False,
                ),
                blocking_issues,
                warnings,
            )

    # Check for parse errors
    if not parsed.parse_valid:
        warnings.append(f"Pathway parse error: {parsed.parse_error}")
        return (
            EnforcementCheckpoint(
                checkpoint_type="pathway_classification",
                checkpoint_passed=True,
                severity="yellow",
                message=f"Pathway parse warning: {parsed.parse_error}",
                blocking=False,
            ),
            blocking_issues,
            warnings,
        )

    # Valid canonical pathway type
    return (
        EnforcementCheckpoint(
            checkpoint_type="pathway_classification",
            checkpoint_passed=True,
            severity="green",
            message=f"Pathway classified as {parsed.pathway_type}: {parsed.pathway_target}",
            blocking=False,
        ),
        blocking_issues,
        warnings,
    )


def evaluate_quarantine_enforcement(
    linkage: GovernanceLinkage,
) -> Tuple[EnforcementCheckpoint, List[str], List[str]]:
    """
    Evaluate quarantine enforcement checkpoint against 7H state.

    Returns: (checkpoint, blocking_issues, warnings)
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # If quarantine_id provided but not found = RED
    if linkage.quarantine_id and not linkage.quarantine_found:
        blocking_issues.append(
            f"Referenced quarantine_id not found: {linkage.quarantine_id}"
        )
        return (
            EnforcementCheckpoint(
                checkpoint_type="quarantine_enforcement",
                checkpoint_passed=False,
                severity="red",
                message=f"Quarantine reference not found: {linkage.quarantine_id}",
                blocking=True,
            ),
            blocking_issues,
            warnings,
        )

    # If no quarantine reference = YELLOW (incomplete linkage)
    if not linkage.quarantine_id:
        warnings.append("Missing quarantine reference — incomplete governance linkage")
        return (
            EnforcementCheckpoint(
                checkpoint_type="quarantine_enforcement",
                checkpoint_passed=True,
                severity="yellow",
                message="No quarantine reference provided — governance linkage incomplete",
                blocking=False,
            ),
            blocking_issues,
            warnings,
        )

    # Quarantine found — verify state
    if linkage.quarantine_state == "future_escalation_required":
        # This is expected state — GREEN
        return (
            EnforcementCheckpoint(
                checkpoint_type="quarantine_enforcement",
                checkpoint_passed=True,
                severity="green",
                message=f"Quarantine state verified: {linkage.quarantine_state}",
                blocking=False,
            ),
            blocking_issues,
            warnings,
        )

    # Other quarantine states
    return (
        EnforcementCheckpoint(
            checkpoint_type="quarantine_enforcement",
            checkpoint_passed=True,
            severity="green",
            message=f"Quarantine enforcement passed: state={linkage.quarantine_state}",
            blocking=False,
        ),
        blocking_issues,
        warnings,
    )


def evaluate_consumption_discipline(
    linkage: GovernanceLinkage,
) -> Tuple[EnforcementCheckpoint, List[str], List[str]]:
    """
    Evaluate consumption discipline checkpoint against 7N state.

    Returns: (checkpoint, blocking_issues, warnings)
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # If consumer_id provided but not found = RED
    if linkage.consumer_id and not linkage.consumer_found:
        blocking_issues.append(
            f"Referenced consumer_id not found: {linkage.consumer_id}"
        )
        return (
            EnforcementCheckpoint(
                checkpoint_type="consumption_discipline",
                checkpoint_passed=False,
                severity="red",
                message=f"Consumer reference not found: {linkage.consumer_id}",
                blocking=True,
            ),
            blocking_issues,
            warnings,
        )

    # If no consumer reference = YELLOW
    if not linkage.consumer_id:
        warnings.append("Missing consumer reference — incomplete governance linkage")
        return (
            EnforcementCheckpoint(
                checkpoint_type="consumption_discipline",
                checkpoint_passed=True,
                severity="yellow",
                message="No consumer reference provided — governance linkage incomplete",
                blocking=False,
            ),
            blocking_issues,
            warnings,
        )

    # Consumer found — GREEN
    return (
        EnforcementCheckpoint(
            checkpoint_type="consumption_discipline",
            checkpoint_passed=True,
            severity="green",
            message=f"Consumption discipline verified for consumer: {linkage.consumer_id}",
            blocking=False,
        ),
        blocking_issues,
        warnings,
    )


def evaluate_ledger_lineage(
    linkage: GovernanceLinkage,
) -> Tuple[EnforcementCheckpoint, List[str], List[str]]:
    """
    Evaluate ledger lineage checkpoint against 7O state.

    Returns: (checkpoint, blocking_issues, warnings)
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # If ledger_entry_id provided but not found = RED
    if linkage.ledger_entry_id and not linkage.ledger_entry_found:
        blocking_issues.append(
            f"Referenced ledger_entry_id not found: {linkage.ledger_entry_id}"
        )
        return (
            EnforcementCheckpoint(
                checkpoint_type="ledger_lineage",
                checkpoint_passed=False,
                severity="red",
                message=f"Ledger entry reference not found: {linkage.ledger_entry_id}",
                blocking=True,
            ),
            blocking_issues,
            warnings,
        )

    # If no ledger reference = YELLOW
    if not linkage.ledger_entry_id:
        warnings.append("Missing ledger reference — incomplete governance linkage")
        return (
            EnforcementCheckpoint(
                checkpoint_type="ledger_lineage",
                checkpoint_passed=True,
                severity="yellow",
                message="No ledger entry reference provided — governance linkage incomplete",
                blocking=False,
            ),
            blocking_issues,
            warnings,
        )

    # Check escalation severity
    if linkage.ledger_escalation_severity in ("high", "critical"):
        warnings.append(
            f"Ledger shows escalation severity: {linkage.ledger_escalation_severity}"
        )
        return (
            EnforcementCheckpoint(
                checkpoint_type="ledger_lineage",
                checkpoint_passed=True,
                severity="yellow",
                message=f"Ledger escalation severity: {linkage.ledger_escalation_severity}",
                blocking=False,
            ),
            blocking_issues,
            warnings,
        )

    # Ledger found, no critical escalation — GREEN
    return (
        EnforcementCheckpoint(
            checkpoint_type="ledger_lineage",
            checkpoint_passed=True,
            severity="green",
            message=f"Ledger lineage verified: {linkage.ledger_entry_id}",
            blocking=False,
        ),
        blocking_issues,
        warnings,
    )


def evaluate_invariant_verification() -> EnforcementCheckpoint:
    """
    Verify 7P invariants are maintained.

    This is always GREEN because invariants are model-enforced.
    If we reach this point, invariants are valid.
    """
    return EnforcementCheckpoint(
        checkpoint_type="invariant_verification",
        checkpoint_passed=True,
        severity="green",
        message="7P invariants verified: execution_authorized=False, "
                "machine_output_allowed=False, serializer_execution_allowed=False",
        blocking=False,
    )


# -----------------------------------------------------------------------------
# Main Evaluation Function
# -----------------------------------------------------------------------------

def evaluate_runtime_enforcement(
    request: RuntimeEnforcementRequest,
) -> RuntimeGovernanceEnforcementEvaluation:
    """
    Evaluate runtime governance enforcement for a pathway declaration.

    This is the main entry point for 7P enforcement evaluation.

    Args:
        request: RuntimeEnforcementRequest with pathway and optional linkage

    Returns:
        RuntimeGovernanceEnforcementEvaluation with checkpoint results

    Guardrail:
        7P evaluates declared runtime-adjacent pathways for governance compliance.
        It does not intercept live traffic, invoke serializers, execute runtimes,
        or authorize machine output.
    """
    checkpoints: List[EnforcementCheckpoint] = []
    all_blocking_issues: List[str] = []
    all_warnings: List[str] = []

    # --- Step 1: Parse pathway ---
    parsed = parse_runtime_pathway(request.runtime_pathway)

    # --- Step 2: Build governance linkage ---
    linkage = GovernanceLinkage(
        quarantine_id=request.quarantine_id,
        consumer_id=request.consumer_id,
        ledger_entry_id=request.ledger_entry_id,
        translator_id=request.translator_id,
        export_route=request.export_route,
    )

    # Look up references in 7H/7N/7O
    linkage = lookup_governance_linkage(linkage)

    # --- Step 3: Run checkpoints ---

    # Checkpoint 1: Pathway classification
    cp1, issues1, warns1 = evaluate_pathway_classification(parsed)
    checkpoints.append(cp1)
    all_blocking_issues.extend(issues1)
    all_warnings.extend(warns1)

    # Checkpoint 2: Quarantine enforcement (7H)
    cp2, issues2, warns2 = evaluate_quarantine_enforcement(linkage)
    checkpoints.append(cp2)
    all_blocking_issues.extend(issues2)
    all_warnings.extend(warns2)

    # Checkpoint 3: Consumption discipline (7N)
    cp3, issues3, warns3 = evaluate_consumption_discipline(linkage)
    checkpoints.append(cp3)
    all_blocking_issues.extend(issues3)
    all_warnings.extend(warns3)

    # Checkpoint 4: Ledger lineage (7O)
    cp4, issues4, warns4 = evaluate_ledger_lineage(linkage)
    checkpoints.append(cp4)
    all_blocking_issues.extend(issues4)
    all_warnings.extend(warns4)

    # Checkpoint 5: Invariant verification
    cp5 = evaluate_invariant_verification()
    checkpoints.append(cp5)

    # --- Step 4: Determine overall results ---

    # Detection flags
    serializer_path_detected = parsed.pathway_type == "serializer_boundary"
    runtime_bypass_detected = (
        parsed.pathway_type == "unknown" and parsed.implies_execution
    )
    authority_leak_detected = parsed.pathway_type == "machine_output_boundary"

    # Quarantine respected if no execution pathways detected
    runtime_quarantine_respected = not (
        serializer_path_detected or runtime_bypass_detected or authority_leak_detected
    )

    # Overall checkpoint passed
    governance_checkpoint_passed = all(cp.checkpoint_passed for cp in checkpoints)

    # Determine severity
    if all_blocking_issues:
        severity: EnforcementSeverity = "red"
    elif all_warnings:
        severity = "yellow"
    else:
        severity = "green"

    # --- Step 5: Build evaluation result ---
    evaluation = RuntimeGovernanceEnforcementEvaluation(
        runtime_pathway=request.runtime_pathway,
        parsed_pathway=parsed,
        translator_id=request.translator_id,
        export_route=request.export_route,
        governance_linkage=linkage,
        checkpoints=checkpoints,
        governance_checkpoint_passed=governance_checkpoint_passed,
        runtime_quarantine_respected=runtime_quarantine_respected,
        serializer_path_detected=serializer_path_detected,
        runtime_bypass_detected=runtime_bypass_detected,
        authority_leak_detected=authority_leak_detected,
        severity=severity,
        blocking_issues=all_blocking_issues,
        warnings=all_warnings,
        execution_authorized=False,
        machine_output_allowed=False,
        serializer_execution_allowed=False,
        runtime_self_authorized=False,
        metadata={
            "dev_order": "7P",
            "evaluation_type": "runtime_governance_enforcement",
            "request_context": request.request_context,
        },
    )

    # Compute deterministic hash
    evaluation.deterministic_enforcement_hash = evaluation.compute_enforcement_hash()

    # Register in index
    register_enforcement_evaluation(evaluation)

    return evaluation


# -----------------------------------------------------------------------------
# CI Report Generation
# -----------------------------------------------------------------------------

def generate_enforcement_ci_report() -> EnforcementCheckpointReport:
    """
    Generate CI-visible enforcement report from all evaluations.

    Returns aggregated report suitable for CI status check.
    """
    evaluations = list_enforcement_evaluations()

    # Count by severity
    red_count = sum(1 for e in evaluations if e.severity == "red")
    yellow_count = sum(1 for e in evaluations if e.severity == "yellow")
    green_count = sum(1 for e in evaluations if e.severity == "green")

    # Detection counts
    serializer_paths = sum(1 for e in evaluations if e.serializer_path_detected)
    runtime_bypasses = sum(1 for e in evaluations if e.runtime_bypass_detected)
    authority_leaks = sum(1 for e in evaluations if e.authority_leak_detected)
    quarantine_violations = sum(
        1 for e in evaluations if not e.runtime_quarantine_respected
    )

    # Aggregate issues
    all_blocking: List[str] = []
    all_warns: List[str] = []
    for e in evaluations:
        all_blocking.extend(e.blocking_issues)
        all_warns.extend(e.warnings)

    # Determine CI status
    if red_count > 0:
        ci_status = "fail"
        summary = (
            f"FAIL: {red_count} RED evaluation(s), "
            f"{serializer_paths} serializer paths, "
            f"{runtime_bypasses} runtime bypasses, "
            f"{authority_leaks} authority leaks"
        )
    elif yellow_count > 0:
        ci_status = "warn"
        summary = (
            f"WARN: {yellow_count} YELLOW evaluation(s) — "
            f"incomplete governance linkage or warnings present"
        )
    else:
        ci_status = "pass"
        summary = f"PASS: {green_count} evaluation(s), all governance checkpoints passed"

    report = EnforcementCheckpointReport(
        evaluations_count=len(evaluations),
        evaluations_passed=green_count,
        evaluations_failed=red_count,
        evaluations_warned=yellow_count,
        serializer_paths_detected=serializer_paths,
        runtime_bypasses_detected=runtime_bypasses,
        authority_leaks_detected=authority_leaks,
        quarantine_violations=quarantine_violations,
        red_count=red_count,
        yellow_count=yellow_count,
        green_count=green_count,
        ci_status=ci_status,
        summary_message=summary,
        all_blocking_issues=list(set(all_blocking)),  # dedupe
        all_warnings=list(set(all_warns)),  # dedupe
        execution_authorized=False,
        machine_output_allowed=False,
    )

    # Compute hash
    report.deterministic_report_hash = report.compute_report_hash()

    # Register
    register_enforcement_report(report)

    return report


# -----------------------------------------------------------------------------
# Policy Constants Export
# -----------------------------------------------------------------------------

def get_enforcement_policy() -> dict:
    """
    Get enforcement policy summary.

    Returns hard-coded policy constants for API exposure.
    """
    return {
        "dev_order": "7P",
        "policy_type": "boundary_enforcement",
        "configurable": False,
        "prohibited_runtime_actions": PROHIBITED_RUNTIME_ACTIONS,
        "red_conditions": RED_CONDITIONS,
        "yellow_conditions": YELLOW_CONDITIONS,
        "checkpoint_types": list(CHECKPOINT_DESCRIPTIONS.keys()),
        "checkpoint_descriptions": CHECKPOINT_DESCRIPTIONS,
        "invariants": {
            "execution_authorized": False,
            "machine_output_allowed": False,
            "serializer_execution_allowed": False,
            "runtime_self_authorized": False,
        },
        "guardrail": (
            "7P evaluates declared runtime-adjacent pathways for governance compliance. "
            "It does not intercept live traffic, invoke serializers, execute runtimes, "
            "or authorize machine output."
        ),
    }
