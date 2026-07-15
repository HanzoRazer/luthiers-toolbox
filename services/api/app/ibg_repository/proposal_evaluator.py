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

Check inventory (25 checks; each owned by exactly ONE category, never duplicated across lists):

    completeness  proposal_id_present, changed_file_summary_present, cbsp21_packet_readable,
                  execution_plan_id_present, execution_groups_present, validation_sequence_present,
                  complexity_summary_present, provenance_reference_present
    governance    cbsp21_packet_valid, declared_risk_supported, behavior_change_articulated,
                  changed_files_within_authorized_paths, proposal_classification_unchanged,
                  authority_state_not_upgraded
    provenance    <field>_continuous for each of the four governed evidence fields
    execution     plan_classification_descriptive, plan_id_matches_content_hash,
                  plan_groups_internally_consistent
    invariant     plan_proposal_id_matches, plan_covers_all_declared_files,
                  plan_introduces_no_undeclared_files, validation_sequence_matches_packet
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.governance.authority_state import AuthorityState

from .cbsp21_patch_adapter import (
    CBSP21PacketError,
    validate_behavior_change_articulation,
    validate_cbsp21_patch_packet,
)
from .execution_planner import SUPPORTED_RISK_LEVELS
from .repository_change_proposal import (
    PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
    RepositoryChangeProposal,
    _file_within_authorized,
)
from .repository_execution_plan import (
    EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION,
    RepositoryExecutionPlan,
)
from .repository_proposal_evaluation import (
    EVALUATION_CONSTITUTIONAL_CLASSIFICATION,
    EvaluationFinding,
    FINDING_CATEGORIES,
    FINDING_CATEGORY_COMPLETENESS,
    FINDING_CATEGORY_EXECUTION,
    FINDING_CATEGORY_GOVERNANCE,
    FINDING_CATEGORY_INVARIANT,
    FINDING_CATEGORY_PROVENANCE,
    FINDING_STATUS_FAIL,
    FINDING_STATUS_NOT_APPLICABLE,
    FINDING_STATUS_PASS,
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

# The four evidence-owned provenance fields, carried (never reinterpreted) from binding to plan.
GOVERNED_PROVENANCE_FIELDS: Tuple[str, ...] = (
    "evidence_candidate_id",
    "evidence_provenance_hash",
    "producing_subsystem",
    "source_authority_state",
)

# Recognized authority-state labels, read from the governance enum rather than restated here, so an
# added state can never silently read as "unrecognized".
_RECOGNIZED_AUTHORITY_STATES = frozenset(state.value for state in AuthorityState)


def _finding(check_id: str, category: str, status: str, detail: str) -> EvaluationFinding:
    return EvaluationFinding(check_id=check_id, category=category, status=status, detail=detail)


def _present(value: Any) -> bool:
    """True when a scalar field is a non-empty, non-whitespace string."""
    return isinstance(value, str) and bool(value.strip())


def _as_tuple(value: Any) -> Tuple[Any, ...]:
    """Coerce a sequence-ish field to a tuple without raising on a hand-built contract."""
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return (value,)


def _normalized_path(raw: Any) -> str:
    return str(raw).strip().replace("\\", "/").strip("/")


def _packet_declared_commands(packet: Any) -> Optional[Tuple[str, ...]]:
    """The packet's declared verification commands, or ``None`` when the packet declares no list.

    ``None`` (no readable ``verification.commands_run`` list) is distinct from ``()`` (a list that is
    explicitly empty): the first means the packet cannot say, the second means it says "none".
    """
    if not isinstance(packet, dict):
        return None
    verification = packet.get("verification")
    if not isinstance(verification, dict):
        return None
    commands = verification.get("commands_run")
    if not isinstance(commands, (list, tuple)):
        return None
    return tuple(str(c) for c in commands)


def _plan_group_files(plan: RepositoryExecutionPlan) -> Tuple[str, ...]:
    """Every file referenced by the plan's commit sequence, normalized and deduped."""
    files = set()
    for group in _as_tuple(plan.recommended_commit_sequence):
        for f in _as_tuple(getattr(group, "files", ())):
            files.add(_normalized_path(f))
    files.discard("")
    return tuple(sorted(files))


# --- completeness -------------------------------------------------------------------------------


def _completeness_findings(
    proposal: RepositoryChangeProposal, plan: RepositoryExecutionPlan
) -> Tuple[EvaluationFinding, ...]:
    """Structural presence of the fields the two contracts are required to carry."""
    out: List[EvaluationFinding] = []

    def add(check_id: str, status: str, detail: str) -> None:
        out.append(_finding(check_id, FINDING_CATEGORY_COMPLETENESS, status, detail))

    add(
        "completeness.proposal_id_present",
        FINDING_STATUS_PASS if _present(proposal.proposal_id) else FINDING_STATUS_FAIL,
        f"proposal_id={proposal.proposal_id!r}",
    )

    changed_files = tuple(_as_tuple(proposal.changed_file_summary))
    add(
        "completeness.changed_file_summary_present",
        FINDING_STATUS_PASS if changed_files else FINDING_STATUS_FAIL,
        f"proposal declares {len(changed_files)} changed file(s)",
    )

    packet_readable = isinstance(proposal.cbsp21_packet, dict)
    add(
        "completeness.cbsp21_packet_readable",
        FINDING_STATUS_PASS if packet_readable else FINDING_STATUS_FAIL,
        "cbsp21_packet is a readable object"
        if packet_readable
        else f"cbsp21_packet is {type(proposal.cbsp21_packet).__name__}, not a readable object",
    )

    add(
        "completeness.execution_plan_id_present",
        FINDING_STATUS_PASS if _present(plan.execution_plan_id) else FINDING_STATUS_FAIL,
        f"execution_plan_id={plan.execution_plan_id!r}",
    )

    # Conditional: groups are only required to exist when the proposal declares files to group.
    groups = _as_tuple(plan.recommended_commit_sequence)
    if not changed_files:
        add(
            "completeness.execution_groups_present",
            FINDING_STATUS_NOT_APPLICABLE,
            "proposal declares no changed files, so no execution group is required",
        )
    else:
        add(
            "completeness.execution_groups_present",
            FINDING_STATUS_PASS if groups else FINDING_STATUS_FAIL,
            f"plan declares {len(groups)} execution group(s) for {len(changed_files)} changed file(s)",
        )

    # Conditional: a packet that legitimately declares no commands cannot make the plan's empty
    # validation sequence a defect — that is not_applicable, never a failure.
    declared_commands = _packet_declared_commands(proposal.cbsp21_packet)
    plan_commands = _as_tuple(plan.recommended_validation_sequence)
    if declared_commands is None:
        add(
            "completeness.validation_sequence_present",
            FINDING_STATUS_NOT_APPLICABLE,
            "cbsp21_packet declares no readable verification.commands_run list",
        )
    elif not declared_commands:
        add(
            "completeness.validation_sequence_present",
            FINDING_STATUS_NOT_APPLICABLE,
            "cbsp21_packet declares an empty verification.commands_run list",
        )
    else:
        add(
            "completeness.validation_sequence_present",
            FINDING_STATUS_PASS if plan_commands else FINDING_STATUS_FAIL,
            f"packet declares {len(declared_commands)} command(s); "
            f"plan carries {len(plan_commands)}",
        )

    complexity_present = plan.estimated_complexity is not None and _present(
        getattr(plan.estimated_complexity, "label", None)
    )
    add(
        "completeness.complexity_summary_present",
        FINDING_STATUS_PASS if complexity_present else FINDING_STATUS_FAIL,
        f"estimated_complexity label="
        f"{getattr(plan.estimated_complexity, 'label', None)!r}",
    )

    provenance_present = plan.provenance_reference is not None
    add(
        "completeness.provenance_reference_present",
        FINDING_STATUS_PASS if provenance_present else FINDING_STATUS_FAIL,
        "plan carries a provenance_reference"
        if provenance_present
        else "plan carries no provenance_reference",
    )

    return tuple(out)


# --- governance ---------------------------------------------------------------------------------


def _governance_findings(proposal: RepositoryChangeProposal) -> Tuple[EvaluationFinding, ...]:
    """Governed-contract conformance, delegating to the existing validators (never forking them)."""
    out: List[EvaluationFinding] = []

    def add(check_id: str, status: str, detail: str) -> None:
        out.append(_finding(check_id, FINDING_CATEGORY_GOVERNANCE, status, detail))

    packet = proposal.cbsp21_packet
    packet_readable = isinstance(packet, dict)

    # Delegates wholly to the CBSP21 adapter — the packet-contract authority.
    try:
        validate_cbsp21_patch_packet(packet)
    except CBSP21PacketError as exc:
        add("governance.cbsp21_packet_valid", FINDING_STATUS_FAIL, f"CBSP21 validation failed: {exc}")
    else:
        add("governance.cbsp21_packet_valid", FINDING_STATUS_PASS, "CBSP21 packet validates")

    # Reuses PR-E's supported set so the two layers can never disagree about a classifiable risk.
    if not packet_readable:
        add(
            "governance.declared_risk_supported",
            FINDING_STATUS_FAIL,
            "cbsp21_packet is not readable, so declared risk_level cannot be read",
        )
    else:
        declared_risk = str(packet.get("risk_level", "")).strip().lower()
        add(
            "governance.declared_risk_supported",
            FINDING_STATUS_PASS if declared_risk in SUPPORTED_RISK_LEVELS else FINDING_STATUS_FAIL,
            f"declared risk_level={packet.get('risk_level')!r}; "
            f"supported={list(SUPPORTED_RISK_LEVELS)}",
        )

    # Delegates to the single extracted articulation rule rather than restating the threshold.
    if not packet_readable:
        add(
            "governance.behavior_change_articulated",
            FINDING_STATUS_NOT_APPLICABLE,
            "cbsp21_packet is not readable, so the articulation rule cannot be evaluated",
        )
    else:
        try:
            validate_behavior_change_articulation(packet)
        except CBSP21PacketError as exc:
            add("governance.behavior_change_articulated", FINDING_STATUS_FAIL, str(exc))
        else:
            add(
                "governance.behavior_change_articulated",
                FINDING_STATUS_PASS,
                f"behavior_change={packet.get('behavior_change')!r} is articulated per the CBSP21 rule",
            )

    # Reuses the proposal builder's containment semantics so the boundary is read identically here.
    authorized = tuple(_as_tuple(proposal.target.authorized_target_paths))
    changed_files = tuple(_as_tuple(proposal.changed_file_summary))
    if not changed_files:
        add(
            "governance.changed_files_within_authorized_paths",
            FINDING_STATUS_NOT_APPLICABLE,
            "proposal declares no changed files to place within the authorized boundary",
        )
    else:
        outside = sorted(
            {str(f) for f in changed_files if not _file_within_authorized(str(f), authorized)}
        )
        add(
            "governance.changed_files_within_authorized_paths",
            FINDING_STATUS_FAIL if outside else FINDING_STATUS_PASS,
            f"{len(outside)} declared file(s) outside authorized_target_paths {list(authorized)}: {outside}"
            if outside
            else f"all {len(changed_files)} declared file(s) fall within authorized_target_paths",
        )

    classification_ok = proposal.constitutional_classification == PROPOSAL_CONSTITUTIONAL_CLASSIFICATION
    add(
        "governance.proposal_classification_unchanged",
        FINDING_STATUS_PASS if classification_ok else FINDING_STATUS_FAIL,
        f"proposal constitutional_classification={proposal.constitutional_classification!r}; "
        f"expected {PROPOSAL_CONSTITUTIONAL_CLASSIFICATION!r}",
    )

    # Asserts the carried authority state is a label the governance enum recognizes. An invented or
    # relabelled state is how an upgrade would be smuggled past review, and that is detectable here.
    # It deliberately does NOT judge WHICH recognized state the evidence holds: a proposal built from
    # canonical evidence legitimately carries canonical_geometry, and the evaluator has no access to
    # the live candidate to compare against — asserting a "correct" state would be an invented claim.
    declared_state = proposal.target.source_authority_state
    add(
        "governance.authority_state_not_upgraded",
        FINDING_STATUS_PASS
        if declared_state in _RECOGNIZED_AUTHORITY_STATES
        else FINDING_STATUS_FAIL,
        f"source_authority_state={declared_state!r} is a recognized governance authority state"
        if declared_state in _RECOGNIZED_AUTHORITY_STATES
        else f"source_authority_state={declared_state!r} is not a recognized governance authority state",
    )

    return tuple(out)


# --- provenance ---------------------------------------------------------------------------------


def _provenance_findings(
    proposal: RepositoryChangeProposal, plan: RepositoryExecutionPlan
) -> Tuple[EvaluationFinding, ...]:
    """Continuity of the four governed evidence fields across proposal.target -> plan.provenance_reference.

    Reports discontinuity; never infers, repairs, or back-fills a missing provenance value.
    """
    out: List[EvaluationFinding] = []
    reference = plan.provenance_reference

    for field in GOVERNED_PROVENANCE_FIELDS:
        check_id = f"provenance.{field}_continuous"
        proposal_value = getattr(proposal.target, field, None)

        if reference is None:
            out.append(
                _finding(
                    check_id,
                    FINDING_CATEGORY_PROVENANCE,
                    FINDING_STATUS_FAIL,
                    f"plan carries no provenance_reference, so {field} continuity cannot be confirmed",
                )
            )
            continue

        plan_value = getattr(reference, field, None)
        if not _present(proposal_value) or not _present(plan_value):
            out.append(
                _finding(
                    check_id,
                    FINDING_CATEGORY_PROVENANCE,
                    FINDING_STATUS_FAIL,
                    f"{field} is missing: proposal={proposal_value!r}, plan={plan_value!r}",
                )
            )
        elif proposal_value != plan_value:
            out.append(
                _finding(
                    check_id,
                    FINDING_CATEGORY_PROVENANCE,
                    FINDING_STATUS_FAIL,
                    f"{field} discontinuity: proposal={proposal_value!r}, plan={plan_value!r}",
                )
            )
        else:
            out.append(
                _finding(
                    check_id,
                    FINDING_CATEGORY_PROVENANCE,
                    FINDING_STATUS_PASS,
                    f"{field} preserved exactly from proposal to plan",
                )
            )

    return tuple(out)


# --- execution (plan-internal) ------------------------------------------------------------------


def _execution_findings(plan: RepositoryExecutionPlan) -> Tuple[EvaluationFinding, ...]:
    """Internal integrity of the plan itself (its classification, its id, its own group consistency)."""
    out: List[EvaluationFinding] = []

    def add(check_id: str, status: str, detail: str) -> None:
        out.append(_finding(check_id, FINDING_CATEGORY_EXECUTION, status, detail))

    classification_ok = (
        plan.constitutional_classification == EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION
    )
    add(
        "execution.plan_classification_descriptive",
        FINDING_STATUS_PASS if classification_ok else FINDING_STATUS_FAIL,
        f"plan constitutional_classification={plan.constitutional_classification!r}; "
        f"expected {EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION!r}",
    )

    # The plan is content-addressed; an id that does not match its own content means the plan was
    # altered after it was built, which the reviewer must see.
    # A plan missing a required child record cannot hash itself at all; that is an evaluable defect
    # to report, not an exception to propagate — the reviewer still needs the other 24 results.
    try:
        expected_id = "rep-" + plan.compute_plan_hash()
    except (AttributeError, TypeError, ValueError) as exc:
        add(
            "execution.plan_id_matches_content_hash",
            FINDING_STATUS_FAIL,
            f"plan content is not canonically serializable: {exc}",
        )
    else:
        add(
            "execution.plan_id_matches_content_hash",
            FINDING_STATUS_PASS if plan.execution_plan_id == expected_id else FINDING_STATUS_FAIL,
            f"execution_plan_id={plan.execution_plan_id!r}; content hash={expected_id!r}",
        )

    # The review order and structural groups may only reference files the commit sequence declares.
    declared = set(_plan_group_files(plan))
    stray: List[str] = []
    for collection in (plan.recommended_review_order, plan.structural_dependency_groups):
        for group in _as_tuple(collection):
            for f in _as_tuple(getattr(group, "files", ())):
                if _normalized_path(f) not in declared:
                    stray.append(f"{getattr(group, 'group_id', '?')}:{_normalized_path(f)}")
    add(
        "execution.plan_groups_internally_consistent",
        FINDING_STATUS_FAIL if stray else FINDING_STATUS_PASS,
        f"{len(stray)} group file reference(s) absent from the commit sequence: {sorted(stray)}"
        if stray
        else "review-order and structural groups reference only commit-sequence files",
    )

    return tuple(out)


# --- invariants (cross-artifact) ----------------------------------------------------------------


def _invariant_findings(
    proposal: RepositoryChangeProposal, plan: RepositoryExecutionPlan
) -> Tuple[EvaluationFinding, ...]:
    """Cross-artifact agreement between the proposal and the plan that claims to describe it."""
    out: List[EvaluationFinding] = []

    def add(check_id: str, status: str, detail: str) -> None:
        out.append(_finding(check_id, FINDING_CATEGORY_INVARIANT, status, detail))

    # Always passes when an evaluation is produced: a proposal-id mismatch means the two artifacts
    # describe different proposals, which is not evaluable and raises before any check runs. The
    # check is still reported so the reviewer sees the invariant was affirmatively established.
    add(
        "invariant.plan_proposal_id_matches",
        FINDING_STATUS_PASS,
        f"plan.proposal_id == proposal.proposal_id == {proposal.proposal_id!r}",
    )

    declared_files = {_normalized_path(f) for f in _as_tuple(proposal.changed_file_summary)}
    declared_files.discard("")
    plan_files = set(_plan_group_files(plan))

    missing = sorted(declared_files - plan_files)
    add(
        "invariant.plan_covers_all_declared_files",
        FINDING_STATUS_FAIL if missing else FINDING_STATUS_PASS,
        f"{len(missing)} declared file(s) absent from the plan's groups: {missing}"
        if missing
        else f"plan groups cover all {len(declared_files)} declared file(s)",
    )

    # The plan may only describe work the proposal declares; an extra file is invented scope.
    undeclared = sorted(plan_files - declared_files)
    add(
        "invariant.plan_introduces_no_undeclared_files",
        FINDING_STATUS_FAIL if undeclared else FINDING_STATUS_PASS,
        f"{len(undeclared)} plan file(s) not declared by the proposal: {undeclared}"
        if undeclared
        else "plan introduces no file the proposal does not declare",
    )

    declared_commands = _packet_declared_commands(proposal.cbsp21_packet)
    plan_commands = tuple(str(c) for c in _as_tuple(plan.recommended_validation_sequence))
    if declared_commands is None:
        add(
            "invariant.validation_sequence_matches_packet",
            FINDING_STATUS_NOT_APPLICABLE,
            "cbsp21_packet declares no readable verification.commands_run list to compare against",
        )
    elif not declared_commands and not plan_commands:
        add(
            "invariant.validation_sequence_matches_packet",
            FINDING_STATUS_NOT_APPLICABLE,
            "packet declares no verification commands and the plan carries none",
        )
    else:
        add(
            "invariant.validation_sequence_matches_packet",
            FINDING_STATUS_PASS if plan_commands == declared_commands else FINDING_STATUS_FAIL,
            f"plan validation sequence {'matches' if plan_commands == declared_commands else 'differs from'} "
            f"the packet's declared commands (packet={len(declared_commands)}, plan={len(plan_commands)})",
        )

    return tuple(out)


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
    return sort_findings(_execution_findings(plan) + _invariant_findings(proposal, plan))


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

    completeness = sort_findings(_completeness_findings(proposal, plan))
    governance = sort_findings(_governance_findings(proposal))
    provenance = sort_findings(_provenance_findings(proposal, plan))
    execution = sort_findings(_execution_findings(plan))
    invariants = sort_findings(_invariant_findings(proposal, plan))

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
