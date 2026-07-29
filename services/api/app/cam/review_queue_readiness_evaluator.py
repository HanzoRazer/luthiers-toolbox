"""
Review queue architecture readiness — evaluator.

A pure function over typed inputs. No filesystem access, no framework coupling, no
global state. Evidence collection lives in ``review_queue_readiness_evidence``; policy
lives here. Keeping them apart is what makes the policy testable without a repository.

Determinism is a requirement, not a nicety: this runs in CI, and a report that reorders
between runs cannot be diffed.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .review_queue_readiness import (
    AggregateReadiness,
    ReadinessEvaluationError,
    ReadinessEvidence,
    ReadinessFinding,
    ReadinessRequirement,
    ReadinessSeverity,
    ReadinessStatus,
    ReviewQueueReadinessContext,
    ReviewQueueReadinessReport,
    VerificationMode,
)

# Severity ordering for stable sorting: blocking failures surface first.
_SEVERITY_ORDER: Dict[ReadinessSeverity, int] = {
    ReadinessSeverity.BLOCKING: 0,
    ReadinessSeverity.WARNING: 1,
    ReadinessSeverity.INFO: 2,
}


def _evidence_for(
    requirement: ReadinessRequirement,
    evidence: Tuple[ReadinessEvidence, ...],
) -> List[ReadinessEvidence]:
    """All evidence matching a requirement's evidence_kind, in stable order."""
    return [e for e in evidence if e.evidence_kind == requirement.evidence_kind]


def evaluate_requirement(
    requirement: ReadinessRequirement,
    evidence: Tuple[ReadinessEvidence, ...],
) -> ReadinessFinding:
    """Evaluate one requirement against the evidence collection.

    Distinguishes five outcomes. The important distinction is between *confirmed absence*
    and *cannot be determined statically* — reporting an unverifiable requirement as
    UNSATISFIED would be a false accusation, and reporting it as SATISFIED would be a
    false clearance.
    """
    matched = _evidence_for(requirement, evidence)
    sources = [e.source for e in matched]

    # A RUNTIME requirement can never be settled by static evidence. Say so plainly
    # rather than guessing in either direction.
    if requirement.verification_mode is VerificationMode.RUNTIME and not matched:
        return ReadinessFinding(
            requirement_id=requirement.requirement_id,
            title=requirement.title,
            status=ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED,
            severity=requirement.severity,
            detail=(
                requirement.runtime_validation_note
                or "Requires runtime validation; static inspection cannot settle it."
            ),
            evidence_sources=[],
        )

    if not matched:
        # No evidence of the declared kind was produced by the collector. The collector
        # emits present=False for confirmed absence, so an empty match means the property
        # was never inspected — unverifiable, not absent.
        return ReadinessFinding(
            requirement_id=requirement.requirement_id,
            title=requirement.title,
            status=ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED,
            severity=requirement.severity,
            detail=(
                f"No evidence of kind {requirement.evidence_kind!r} was collected. "
                "Absence of evidence is not evidence of absence — this is unverified, "
                "not failed."
            ),
            evidence_sources=[],
        )

    present = [e for e in matched if e.present]

    if present:
        # HYBRID: a declaration exists, but enforcement cannot be proven statically.
        if requirement.verification_mode is VerificationMode.HYBRID:
            return ReadinessFinding(
                requirement_id=requirement.requirement_id,
                title=requirement.title,
                status=ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED,
                severity=requirement.severity,
                detail=(
                    "A declaration was found, but this requirement also depends on runtime "
                    "enforcement that static inspection cannot prove. "
                    + (requirement.runtime_validation_note or "")
                ).strip(),
                evidence_sources=sources,
            )
        return ReadinessFinding(
            requirement_id=requirement.requirement_id,
            title=requirement.title,
            status=ReadinessStatus.SATISFIED,
            severity=requirement.severity,
            detail="; ".join(e.detail for e in present if e.detail)
            or "Declared and found.",
            evidence_sources=sources,
        )

    # Every matching evidence item reported present=False — confirmed absence.
    return ReadinessFinding(
        requirement_id=requirement.requirement_id,
        title=requirement.title,
        status=ReadinessStatus.UNSATISFIED,
        severity=requirement.severity,
        detail="; ".join(e.detail for e in matched if e.detail)
        or "No declaration found.",
        evidence_sources=sources,
    )


def aggregate_readiness(findings: Tuple[ReadinessFinding, ...]) -> AggregateReadiness:
    """Roll findings up to a report status.

    Never accepts a caller override — the aggregate is a consequence of the findings and
    nothing else. This is the specific property the historical TD-2 design lacked.
    """
    if any(f.is_blocking_failure for f in findings):
        return AggregateReadiness.NOT_READY
    if any(f.is_warning for f in findings):
        return AggregateReadiness.READY_WITH_WARNINGS
    return AggregateReadiness.READY


def _sort_key(finding: ReadinessFinding) -> Tuple[int, int, str]:
    """Stable ordering: blocking failures first, then severity, then requirement id.

    Requirement id is the final tiebreak so ordering never depends on input order.
    """
    return (
        0 if finding.is_blocking_failure else 1,
        _SEVERITY_ORDER.get(finding.severity, 99),
        finding.requirement_id,
    )


def evaluate_review_queue_readiness(
    context: ReviewQueueReadinessContext,
) -> ReviewQueueReadinessReport:
    """Evaluate all requirements and produce a deterministic report.

    Raises:
        ReadinessEvaluationError: if evaluation itself fails. Deliberately distinct from a
            truthful NOT_READY: a broken evaluator must never be reported as a readiness
            verdict, and the CLI maps it to a different exit code.
    """
    try:
        findings = tuple(
            evaluate_requirement(req, context.evidence) for req in context.requirements
        )
        ordered = tuple(sorted(findings, key=_sort_key))
        return ReviewQueueReadinessReport(
            aggregate=aggregate_readiness(ordered),
            findings=ordered,
        )
    except ReadinessEvaluationError:
        raise
    except Exception as exc:  # noqa: BLE001 - re-raised as a typed evaluator error
        raise ReadinessEvaluationError(
            f"Readiness evaluation failed: {type(exc).__name__}: {exc}"
        ) from exc
