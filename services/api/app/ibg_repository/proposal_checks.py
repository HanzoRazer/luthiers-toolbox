"""
Proposal-evaluation check builders — the 25 structural checks, grouped by owning category.

Split out of ``proposal_evaluator.py`` (which keeps the public API + orchestration) purely to keep
each module within the repository's file-size decomposition target; there is no behavioral change.
Every function here is a pure, side-effect-free reader of the two frozen contracts that returns a
deterministic tuple of ``EvaluationFinding``. None performs git, filesystem, network, or GitHub work,
and none mutates its inputs. The owning orchestrator sorts each returned tuple by ``(category,
check_id)`` before it enters the content-addressed evaluation, so incidental order here never leaks
into identity. Each of the five builders owns exactly one category (25 checks total); a finding is
never duplicated across lists. The per-check inventory is documented in ``IBG_PROPOSAL_EVALUATION.md``.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

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
    EvaluationFinding,
    FINDING_CATEGORY_COMPLETENESS,
    FINDING_CATEGORY_EXECUTION,
    FINDING_CATEGORY_GOVERNANCE,
    FINDING_CATEGORY_INVARIANT,
    FINDING_CATEGORY_PROVENANCE,
    FINDING_STATUS_FAIL,
    FINDING_STATUS_NOT_APPLICABLE,
    FINDING_STATUS_PASS,
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


def completeness_findings(
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


def governance_findings(proposal: RepositoryChangeProposal) -> Tuple[EvaluationFinding, ...]:
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

    # Asserts the carried authority state is a label the governance enum recognizes (an invented or
    # relabelled state is how an upgrade would be smuggled past review). It deliberately does NOT judge
    # WHICH recognized state the evidence holds — the evaluator has no access to the live candidate to
    # compare against, so asserting a "correct" state would be an invented claim.
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


def provenance_findings(
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


def execution_findings(plan: RepositoryExecutionPlan) -> Tuple[EvaluationFinding, ...]:
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

    # An id that does not match the plan's own content means it was altered after being built (the
    # reviewer must see that). A plan missing a required child record cannot hash itself at all; that
    # is an evaluable defect to report, not an exception to propagate — the reviewer needs the rest.
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


def invariant_findings(
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
