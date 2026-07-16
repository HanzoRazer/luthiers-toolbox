"""
Readiness Report Builder — assembles a ``RepositoryReadinessReport`` from the three merged domain
artifacts (a proposal, its execution plan, and its evaluation) by COPYING their canonical values.

The builder is the report's only construction path. It proves the three artifacts describe one
coherent chain — matching lineage IDs and agreeing provenance — before it copies a single value, so
every report is an aggregation of artifacts already known to belong together. It composes no new
finding, score, severity, or interpretation; it copies canonical upstream values verbatim, arranges
them into the fixed sections, and mints the report's own content-addressed id.

Boundary (PR G): this module aggregates SUPPLIED domain artifacts. It executes no git, inspects no
worktree, invokes no subprocess, performs no filesystem archaeology or repository-state discovery,
and imports none of the package's git-execution utilities (``git_runner``, ``worktree_builder``,
and the worktree machinery). Any provenance the report carries is provenance the upstream artifacts
supplied; the report never discovers provenance itself.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Optional

from .repository_change_proposal import RepositoryChangeProposal
from .repository_execution_plan import RepositoryExecutionPlan
from .repository_proposal_evaluation import RepositoryProposalEvaluation
from .proposal_evaluator import GOVERNED_PROVENANCE_FIELDS
from .repository_readiness_report import (
    READINESS_REPORT_ID_PREFIX,
    REPORT_SECTION_ORDER,
    SECTION_EVALUATION,
    SECTION_EXECUTION,
    SECTION_PROPOSAL,
    SECTION_PROVENANCE,
    ReadinessReportError,
    RepositoryGovernanceSummary,
    RepositoryReadinessReport,
    RepositoryReadinessSection,
    _hash_content,
    validate_readiness_summary,
)


def _require_coherent_chain(
    proposal: Any,
    execution_plan: Any,
    evaluation: Any,
) -> None:
    """Fail closed unless the three artifacts are the right types and describe ONE coherent chain.

    Checks, in order: presence, type, the complete lineage-ID chain, and provenance agreement
    between the plan's ``provenance_reference`` and the proposal's target binding. Every failure is
    a construction error, never a report — a report over a broken chain would misrepresent artifacts
    that do not belong together.
    """
    if proposal is None:
        raise ReadinessReportError("proposal is required")
    if execution_plan is None:
        raise ReadinessReportError("execution_plan is required")
    if evaluation is None:
        raise ReadinessReportError("evaluation is required")

    if not isinstance(proposal, RepositoryChangeProposal):
        raise ReadinessReportError(
            f"proposal must be a RepositoryChangeProposal, not {type(proposal).__name__}"
        )
    if not isinstance(execution_plan, RepositoryExecutionPlan):
        raise ReadinessReportError(
            f"execution_plan must be a RepositoryExecutionPlan, not {type(execution_plan).__name__}"
        )
    if not isinstance(evaluation, RepositoryProposalEvaluation):
        raise ReadinessReportError(
            f"evaluation must be a RepositoryProposalEvaluation, not {type(evaluation).__name__}"
        )

    # Lineage: all three must agree on the proposal, and the plan/evaluation on the plan.
    if proposal.proposal_id != execution_plan.proposal_id:
        raise ReadinessReportError(
            f"execution_plan describes proposal {execution_plan.proposal_id!r}, "
            f"not {proposal.proposal_id!r}"
        )
    if proposal.proposal_id != evaluation.proposal_id:
        raise ReadinessReportError(
            f"evaluation describes proposal {evaluation.proposal_id!r}, "
            f"not {proposal.proposal_id!r}"
        )
    if execution_plan.execution_plan_id != evaluation.execution_plan_id:
        raise ReadinessReportError(
            f"evaluation describes execution_plan {evaluation.execution_plan_id!r}, "
            f"not {execution_plan.execution_plan_id!r}"
        )

    # Provenance: the plan's carried provenance must match the proposal's binding field-for-field.
    # A disagreement means the plan and the proposal reference different evidence — structurally the
    # same class of corruption as a lineage-ID mismatch, and treated the same way.
    binding = proposal.target
    reference = execution_plan.provenance_reference
    for field in GOVERNED_PROVENANCE_FIELDS:
        plan_value = getattr(reference, field)
        proposal_value = getattr(binding, field)
        if plan_value != proposal_value:
            raise ReadinessReportError(
                f"provenance field {field!r} disagrees: execution_plan={plan_value!r}, "
                f"proposal_binding={proposal_value!r}"
            )


def _proposal_section(proposal: RepositoryChangeProposal) -> RepositoryReadinessSection:
    binding = proposal.target
    return RepositoryReadinessSection(
        section_key=SECTION_PROPOSAL,
        entries=(
            ("proposal_id", proposal.proposal_id),
            ("repository_id", binding.repository_id),
            ("base_revision", binding.base_revision),
            ("proposed_branch", proposal.proposed_branch),
            ("change_intent", binding.change_intent),
            ("changed_file_count", len(proposal.changed_file_summary)),
            ("constitutional_classification", proposal.constitutional_classification),
        ),
    )


def _execution_section(plan: RepositoryExecutionPlan) -> RepositoryReadinessSection:
    complexity = plan.estimated_complexity
    return RepositoryReadinessSection(
        section_key=SECTION_EXECUTION,
        entries=(
            ("execution_plan_id", plan.execution_plan_id),
            ("complexity_label", complexity.label),
            ("changed_file_count", complexity.changed_file_count),
            ("authorized_path_count", complexity.authorized_path_count),
            ("declared_risk_level", complexity.declared_risk_level),
            ("planning_summary", plan.planning_summary),
            ("constitutional_classification", plan.constitutional_classification),
        ),
    )


def _evaluation_section(evaluation: RepositoryProposalEvaluation) -> RepositoryReadinessSection:
    return RepositoryReadinessSection(
        section_key=SECTION_EVALUATION,
        entries=(
            ("evaluation_id", evaluation.evaluation_id),
            ("readiness_summary", evaluation.readiness_summary),
            ("completeness_score", evaluation.completeness_score),
            ("checks_passed", evaluation.checks_passed),
            ("checks_failed", evaluation.checks_failed),
            ("checks_not_applicable", evaluation.checks_not_applicable),
            ("checks_applicable", evaluation.checks_applicable),
            ("evaluation_summary", evaluation.evaluation_summary),
            ("constitutional_classification", evaluation.constitutional_classification),
        ),
    )


def _provenance_section(plan: RepositoryExecutionPlan) -> RepositoryReadinessSection:
    # Single source: built solely from the plan's provenance_reference. The proposal binding was
    # already cross-checked against it in _require_coherent_chain, so there is one construction path.
    reference = plan.provenance_reference
    return RepositoryReadinessSection(
        section_key=SECTION_PROVENANCE,
        entries=tuple((field, getattr(reference, field)) for field in GOVERNED_PROVENANCE_FIELDS),
    )


def build_repository_readiness_report(
    proposal: RepositoryChangeProposal,
    execution_plan: RepositoryExecutionPlan,
    evaluation: RepositoryProposalEvaluation,
    *,
    created_at: Optional[datetime] = None,
) -> RepositoryReadinessReport:
    """Aggregate the three artifacts into a content-addressed ``RepositoryReadinessReport``.

    Fails closed (``ReadinessReportError``) on a wrong type, ``None``, a broken lineage chain, a
    provenance disagreement, an unsupported readiness value, or content that cannot be canonically
    serialized. It never mutates an input, composes a new finding or score, or emits a partial report.
    """
    _require_coherent_chain(proposal, execution_plan, evaluation)

    # Verbatim projection of the evaluation's readiness label — rejected if outside F's vocabulary.
    readiness_summary = validate_readiness_summary(evaluation.readiness_summary)

    # Structural governance projection: count + check_ids in the evaluation's own canonical order.
    governance_summary = RepositoryGovernanceSummary(
        finding_count=len(evaluation.governance_findings),
        check_ids=tuple(finding.check_id for finding in evaluation.governance_findings),
    )

    sections = (
        _proposal_section(proposal),
        _execution_section(execution_plan),
        _evaluation_section(evaluation),
        _provenance_section(execution_plan),
    )

    draft = RepositoryReadinessReport(
        # Placeholder id is excluded from _canonical_content(), so it cannot influence the hash; the
        # real id is grafted on below from the draft's own content, keeping builder and
        # compute_report_hash() unable to drift.
        readiness_report_id="",
        proposal_id=proposal.proposal_id,
        execution_plan_id=execution_plan.execution_plan_id,
        evaluation_id=evaluation.evaluation_id,
        governance_summary=governance_summary,
        # Documented mapping: the plan's canonical planning_summary is carried as execution_summary.
        execution_summary=execution_plan.planning_summary,
        evaluation_summary=evaluation.evaluation_summary,
        readiness_summary=readiness_summary,
        report_sections=sections,
        created_at=created_at,
    )

    try:
        report_id = READINESS_REPORT_ID_PREFIX + _hash_content(draft._canonical_content())
    except (TypeError, ValueError) as exc:
        raise ReadinessReportError(
            f"readiness report content cannot be canonically serialized: {exc}"
        ) from exc

    return replace(draft, readiness_report_id=report_id)


def validate_repository_readiness_report(
    report: RepositoryReadinessReport,
) -> RepositoryReadinessReport:
    """Fail-closed structural check of an already-built report (used by tests and consumers).

    Verifies the content-addressed id matches the report's own canonical content, the readiness
    label is within F's vocabulary, the governance count agrees with its check_ids, and the sections
    are exactly the four canonical keys in canonical order. Never mutates the report.
    """
    if not isinstance(report, RepositoryReadinessReport):
        raise ReadinessReportError(
            f"report must be a RepositoryReadinessReport, not {type(report).__name__}"
        )

    expected_id = READINESS_REPORT_ID_PREFIX + report.compute_report_hash()
    if report.readiness_report_id != expected_id:
        raise ReadinessReportError(
            f"readiness_report_id {report.readiness_report_id!r} does not match content hash "
            f"{expected_id!r}"
        )

    validate_readiness_summary(report.readiness_summary)

    if report.governance_summary.finding_count != len(report.governance_summary.check_ids):
        raise ReadinessReportError(
            f"governance finding_count {report.governance_summary.finding_count} disagrees with "
            f"{len(report.governance_summary.check_ids)} check_ids"
        )

    section_keys = tuple(section.section_key for section in report.report_sections)
    if section_keys != REPORT_SECTION_ORDER:
        raise ReadinessReportError(
            f"report_sections must be exactly {list(REPORT_SECTION_ORDER)} in order, got "
            f"{list(section_keys)}"
        )

    for identity_name, identity_value in (
        ("proposal_id", report.proposal_id),
        ("execution_plan_id", report.execution_plan_id),
        ("evaluation_id", report.evaluation_id),
    ):
        if not isinstance(identity_value, str) or not identity_value.strip():
            raise ReadinessReportError(f"{identity_name} must be a non-empty string")

    return report
