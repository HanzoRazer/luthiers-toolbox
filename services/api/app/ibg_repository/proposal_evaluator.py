"""
Proposal Evaluator — deterministically evaluates a ``RepositoryChangeProposal`` plus its
``RepositoryExecutionPlan`` into an OBSERVATIONAL ``RepositoryProposalEvaluation``.

This evaluator is the PR-F companion to PR-E's descriptive execution planner. Where the planner
describes how approved work could be organized, this evaluator reports whether the proposal and plan
are structurally complete, internally consistent, and continuous with the provenance they claim —
before a human reviewer ever opens a pull request. It is a SEPARATE downstream consumer of the merged
contracts: it does not modify, wrap, or attach to ``RepositoryProposalPipeline`` or ``ExecutionPlanner``.

Constitutional boundary (PR F):

    * It SCORES, CLASSIFIES, and REPORTS. It never edits a proposal or plan, generates a commit,
      executes git, creates a pull request, alters governance, promotes evidence, or authorizes
      engineering. Both inputs are treated as strictly read-only.
    * A failed check is a reported observation, NOT a rejection, a block, or a withheld approval.
      The evaluator has no approve/reject/merge/authorize vocabulary because it holds no such authority.
    * It performs NO git, filesystem-mutation, GitHub, or network operation, and imports none of the
      PR-B execution machinery (git_runner, worktree builder/validator, filesystem mutators).
    * It reuses the existing validators (CBSP21 packet validation, the behavior-change articulation
      rule, the proposal's authorized-path containment, PR-E's supported risk set) rather than forking
      their rule sets into a second, drifting implementation.

Error vs finding. ``ProposalEvaluationError`` is raised ONLY when the artifacts cannot be coherently
evaluated: a wrong type, ``None``, or a proposal and plan that describe different proposals. Every
substantive readiness gap in an evaluable artifact — missing provenance, an empty validation sequence,
invalid CBSP21 content, files outside the authorized boundary, an unsupported risk level, a
plan/proposal file-set mismatch, provenance discontinuity — is REPORTED as a failed finding. The
evaluator reports evaluable defects; it never suppresses them behind an exception, because an
exception would hide from the reviewer exactly what they need to see.

Why defects are reachable at all. ``build_repository_change_proposal`` and ``build_execution_plan``
are fail-closed, so artifacts produced through them cannot carry most of these defects. The contracts
are plain frozen dataclasses and can also be constructed directly, so this evaluator deliberately
evaluates the artifacts AS GIVEN rather than assuming a builder produced them. That is the point: it
is an independent check, not a restatement of the builders' preconditions.

Determinism: identical artifacts produce byte-identical evaluations (content-addressed ``eval-`` id).
No wall-clock time, environment paths, object reprs, iteration accidents, or unordered collections
enter the canonical form; findings are sorted by ``(category, check_id)``.

The 25 structural checks themselves live in ``proposal_checks.py`` (five category builders, one per
owning category); this module orchestrates them, derives the score/readiness, and owns the public API.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .proposal_checks import (
    completeness_findings,
    execution_findings,
    governance_findings,
    invariant_findings,
    provenance_findings,
)
from .repository_change_proposal import RepositoryChangeProposal
from .repository_execution_plan import RepositoryExecutionPlan
from .repository_proposal_evaluation import (
    EVALUATION_CONSTITUTIONAL_CLASSIFICATION,
    EvaluationFinding,
    FINDING_CATEGORIES,
    FINDING_STATUSES,
    ProposalEvaluationError,
    READINESS_COMPLETE,
    READINESS_INCOMPLETE,
    RepositoryProposalEvaluation,
    _hash_content,
    compute_completeness_score,
    sort_findings,
    summarize_findings,
)


# --- summary ------------------------------------------------------------------------------------


def _evaluation_summary(
    *,
    proposal_id: str,
    execution_plan_id: str,
    readiness_summary: str,
    counts: Dict[str, int],
    completeness_score: str,
) -> str:
    """A deterministic, fact-only summary from a fixed template. States results; recommends nothing."""
    return (
        f"Observational evaluation of proposal {proposal_id} against execution plan "
        f"{execution_plan_id}: {counts['passed']} of {counts['applicable']} applicable structural "
        f"check(s) passed (score {completeness_score}), {counts['failed']} failed, "
        f"{counts['not_applicable']} not applicable. Structural readiness: {readiness_summary}. "
        "This is an observation of structural completeness only — it is not an approval, a "
        "rejection, or an authorization to execute, and the human review boundary is unchanged."
    )


# --- public API ---------------------------------------------------------------------------------


def evaluate_execution_plan(
    proposal: RepositoryChangeProposal, plan: RepositoryExecutionPlan
) -> Tuple[EvaluationFinding, ...]:
    """The plan-facing findings only (plan-internal execution integrity + cross-artifact invariants).

    Exposed for reviewers and dashboards that want the plan's story alone. The full evaluation is
    ``evaluate_repository_proposal``; this shares its logic rather than forking it.
    """
    _require_evaluable(proposal, plan)
    return sort_findings(execution_findings(plan) + invariant_findings(proposal, plan))


def _require_evaluable(proposal: Any, plan: Any) -> None:
    """Fail closed when the artifacts cannot be coherently evaluated (never for a readiness gap)."""
    if proposal is None:
        raise ProposalEvaluationError("proposal is required")
    if plan is None:
        raise ProposalEvaluationError("plan is required")
    if not isinstance(proposal, RepositoryChangeProposal):
        raise ProposalEvaluationError(
            f"proposal must be a RepositoryChangeProposal, not {type(proposal).__name__}"
        )
    if not isinstance(plan, RepositoryExecutionPlan):
        raise ProposalEvaluationError(
            f"plan must be a RepositoryExecutionPlan, not {type(plan).__name__}"
        )
    # Not a readiness gap: two artifacts describing different proposals cannot be evaluated against
    # each other at all, and reporting a finding would imply the pairing was meaningful.
    if proposal.proposal_id != plan.proposal_id:
        raise ProposalEvaluationError(
            f"plan describes proposal {plan.proposal_id!r}, not {proposal.proposal_id!r}"
        )


def evaluate_repository_proposal(
    proposal: RepositoryChangeProposal,
    plan: RepositoryExecutionPlan,
    *,
    created_at: Optional[datetime] = None,
) -> RepositoryProposalEvaluation:
    """
    Deterministically evaluate a proposal + its execution plan into an OBSERVATIONAL evaluation.

    Reports structural completeness, governed-contract conformance, provenance continuity, plan
    integrity, and cross-artifact invariants. Neither input is mutated, no evidence is promoted, and
    no approval/rejection is expressed or implied.

    Fail-closed only on inputs that cannot be coherently evaluated (wrong type, ``None``, mismatched
    proposal ids, no applicable checks, or content that cannot be canonically serialized). Every
    substantive readiness gap is returned as a failed finding instead.
    """
    _require_evaluable(proposal, plan)

    completeness = sort_findings(completeness_findings(proposal, plan))
    governance = sort_findings(governance_findings(proposal))
    provenance = sort_findings(provenance_findings(proposal, plan))
    execution = sort_findings(execution_findings(plan))
    invariants = sort_findings(invariant_findings(proposal, plan))

    every = completeness + governance + provenance + execution + invariants
    counts = summarize_findings(every)

    # Fails closed rather than inventing a score for an empty denominator.
    completeness_score = compute_completeness_score(counts["passed"], counts["applicable"])

    # Structural label only: derived purely from whether any applicable check failed.
    readiness_summary = READINESS_COMPLETE if counts["failed"] == 0 else READINESS_INCOMPLETE

    summary = _evaluation_summary(
        proposal_id=proposal.proposal_id,
        execution_plan_id=plan.execution_plan_id,
        readiness_summary=readiness_summary,
        counts=counts,
        completeness_score=completeness_score,
    )

    content = {
        "proposal_id": proposal.proposal_id,
        "execution_plan_id": plan.execution_plan_id,
        "readiness_summary": readiness_summary,
        "checks_passed": counts["passed"],
        "checks_failed": counts["failed"],
        "checks_not_applicable": counts["not_applicable"],
        "checks_applicable": counts["applicable"],
        "completeness_score": completeness_score,
        "completeness_findings": [f.to_canonical_dict() for f in completeness],
        "governance_findings": [f.to_canonical_dict() for f in governance],
        "provenance_findings": [f.to_canonical_dict() for f in provenance],
        "execution_findings": [f.to_canonical_dict() for f in execution],
        "invariant_results": [f.to_canonical_dict() for f in invariants],
        "evaluation_summary": summary,
        "constitutional_classification": EVALUATION_CONSTITUTIONAL_CLASSIFICATION,
    }
    try:
        evaluation_id = "eval-" + _hash_content(content)
    except (TypeError, ValueError) as exc:
        raise ProposalEvaluationError(
            f"evaluation content cannot be canonically serialized: {exc}"
        ) from exc

    return RepositoryProposalEvaluation(
        evaluation_id=evaluation_id,
        proposal_id=proposal.proposal_id,
        execution_plan_id=plan.execution_plan_id,
        readiness_summary=readiness_summary,
        checks_passed=counts["passed"],
        checks_failed=counts["failed"],
        checks_not_applicable=counts["not_applicable"],
        checks_applicable=counts["applicable"],
        completeness_score=completeness_score,
        completeness_findings=completeness,
        governance_findings=governance,
        provenance_findings=provenance,
        execution_findings=execution,
        invariant_results=invariants,
        evaluation_summary=summary,
        created_at=created_at,
    )


def validate_repository_proposal_evaluation(
    evaluation: RepositoryProposalEvaluation,
) -> RepositoryProposalEvaluation:
    """
    Fail-closed structural check of an already-built evaluation (used by tests and consumers).

    Verifies the content-addressed id matches the evaluation's own canonical content, that the
    counts agree with the findings, that the score matches the counts, that the readiness label is
    derived from the failed count, and that every finding carries a recognized category/status.
    Never invokes git, the filesystem, or the network. Returns the evaluation unchanged on success.
    """
    if not isinstance(evaluation, RepositoryProposalEvaluation):
        raise ProposalEvaluationError(
            f"input must be a RepositoryProposalEvaluation, not {type(evaluation).__name__}"
        )
    expected_id = "eval-" + evaluation.compute_evaluation_hash()
    if evaluation.evaluation_id != expected_id:
        raise ProposalEvaluationError(
            f"evaluation_id {evaluation.evaluation_id!r} does not match content hash {expected_id!r}"
        )

    findings = evaluation.all_findings()
    for finding in findings:
        if finding.category not in FINDING_CATEGORIES:
            raise ProposalEvaluationError(
                f"finding {finding.check_id!r} has unrecognized category {finding.category!r}"
            )
        if finding.status not in FINDING_STATUSES:
            raise ProposalEvaluationError(
                f"finding {finding.check_id!r} has unrecognized status {finding.status!r}"
            )

    counts = summarize_findings(findings)
    if (
        counts["passed"] != evaluation.checks_passed
        or counts["failed"] != evaluation.checks_failed
        or counts["not_applicable"] != evaluation.checks_not_applicable
        or counts["applicable"] != evaluation.checks_applicable
    ):
        raise ProposalEvaluationError(
            "evaluation counts disagree with its findings: "
            f"declared passed/failed/not_applicable/applicable="
            f"{evaluation.checks_passed}/{evaluation.checks_failed}/"
            f"{evaluation.checks_not_applicable}/{evaluation.checks_applicable}, "
            f"observed={counts['passed']}/{counts['failed']}/"
            f"{counts['not_applicable']}/{counts['applicable']}"
        )

    expected_score = compute_completeness_score(counts["passed"], counts["applicable"])
    if evaluation.completeness_score != expected_score:
        raise ProposalEvaluationError(
            f"completeness_score {evaluation.completeness_score!r} does not match the counts "
            f"({counts['passed']}/{counts['applicable']} -> {expected_score!r})"
        )

    expected_readiness = READINESS_COMPLETE if counts["failed"] == 0 else READINESS_INCOMPLETE
    if evaluation.readiness_summary != expected_readiness:
        raise ProposalEvaluationError(
            f"readiness_summary {evaluation.readiness_summary!r} does not follow from "
            f"{counts['failed']} failed applicable check(s) (expected {expected_readiness!r})"
        )

    if evaluation.constitutional_classification != EVALUATION_CONSTITUTIONAL_CLASSIFICATION:
        raise ProposalEvaluationError(
            f"constitutional_classification {evaluation.constitutional_classification!r} is not "
            f"{EVALUATION_CONSTITUTIONAL_CLASSIFICATION!r}"
        )
    return evaluation


@dataclass(frozen=True)
class ProposalEvaluator:
    """The stateless, observational evaluator. One operation — ``evaluate`` — no decision verb.

    Mirrors PR-E's ``ExecutionPlanner`` shape: a frozen, logic-light entry point that delegates to
    the owning function above and introduces no state. It owns no git/filesystem/GitHub/network
    capability and no method that approves, rejects, blocks, commits, or authorizes.
    """

    def evaluate(
        self,
        proposal: RepositoryChangeProposal,
        plan: RepositoryExecutionPlan,
        *,
        created_at: Optional[datetime] = None,
    ) -> RepositoryProposalEvaluation:
        """Observationally evaluate a proposal + plan (equivalent to ``evaluate_repository_proposal``)."""
        return evaluate_repository_proposal(proposal, plan, created_at=created_at)


def proposal_evaluator() -> ProposalEvaluator:
    """Factory: return a stateless ``ProposalEvaluator`` (parallels ``execution_plan_builder``)."""
    return ProposalEvaluator()
