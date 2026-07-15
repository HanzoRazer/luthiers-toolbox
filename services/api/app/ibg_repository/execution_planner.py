"""
Execution Planner — deterministically transforms a ``RepositoryChangeProposal`` into a DESCRIPTIVE
``RepositoryExecutionPlan``.

This planner is the PR-E companion to PR-D's canonical proposal pipeline. Where the pipeline stops at
the human-review boundary with a review artifact, this planner produces a *descriptive* plan of how a
human engineer could organize the approved work. It is a SEPARATE downstream consumer of the merged
proposal contract: it does not modify, wrap, or attach to ``RepositoryProposalPipeline``.

Constitutional boundary (PR E):

    * It derives EVERY field from data the proposal already declares (its CBSP21 packet + binding).
      It invents no ordering, no dependency edges, no effort/duration/complexity inference.
    * It performs NO git, filesystem-mutation, GitHub, or network operation. It imports none of the
      PR-B execution machinery (git_runner, worktree builder/validator, filesystem mutators).
    * It never promotes evidence or alters the source authority state — provenance is carried through
      exactly. It reuses the existing proposal/CBSP21 validation and adds only PR-E invariants.

Determinism: identical proposals produce byte-identical plans (content-addressed ``rep-`` id). No
wall-clock time, environment paths, object reprs, or unordered collections enter the canonical form.

Complexity label table (documented, auditable — see ``_complexity_label``):

    file tier:  count <= 2 -> 0 ("low") | 3..8 -> 1 ("medium") | > 8 -> 2 ("high")
    risk tier:  low -> 0 | medium -> 1 | high -> 2 | critical -> 2
    label = ["low", "medium", "high"][max(file_tier, risk_tier)]
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Tuple

from .repository_change_proposal import RepositoryChangeProposal
from .repository_execution_plan import (
    ComplexitySummary,
    DependencyGroup,
    EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION,
    ExecutionGroup,
    ProvenanceReference,
    RepositoryExecutionPlan,
    STRUCTURAL_GROUPING_RELATIONSHIP,
)

# Supported declared risk levels. The CBSP21 packet does not enum-constrain risk_level (it only
# requires it non-empty), so PR-E fixes the set it can deterministically classify. An unsupported
# risk level is rejected rather than silently bucketed — the complexity label would otherwise be a
# guess. Kept lowercase; the declared value is normalized with .strip().lower() before lookup.
_RISK_TIER: Dict[str, int] = {"low": 0, "medium": 1, "high": 2, "critical": 2}
SUPPORTED_RISK_LEVELS: Tuple[str, ...] = tuple(sorted(_RISK_TIER))

_COMPLEXITY_LABELS: Tuple[str, ...] = ("low", "medium", "high")


class ExecutionPlanningError(Exception):
    """Raised when a proposal cannot be turned into a valid execution plan (fail-closed)."""


def _require_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExecutionPlanningError(f"{field} is required")
    return value


def _normalize_path(path: Any) -> str:
    """One repo-relative posix normalization: trim, ``\\`` -> ``/``, drop leading/trailing ``/``."""
    return str(path).strip().replace("\\", "/").strip("/")


def _normalize_declared_files(declared: Any) -> Tuple[str, ...]:
    """Normalize a declared-file collection to the canonical sorted, unique, posix form.

    The SINGLE normalization applied to BOTH sides of the scope-agreement check below. It mirrors
    the CBSP21 adapter's ``_sorted_unique_paths`` and the proposal builder's
    ``_file_within_authorized`` containment semantics.

    Why both sides: PR-A's ``build_repository_change_proposal`` derives ``changed_file_summary``
    with ``sorted({str(f) ...})`` — it does NOT normalize (only its *boundary check* normalizes).
    A packet built by ``build_cbsp21_patch_packet`` is already normalized, so the two agree; but a
    packet supplied as a raw dict (the shape ``RepositoryProposalPipeline`` accepts, and the shape
    a ``.cbsp21/patches/*.json`` file loads as) keeps its author's formatting. Comparing a raw
    summary to a normalized scope would then reject a proposal that agrees on the file *set* and
    differs only in formatting. Normalizing both sides removes that false negative while preserving
    the real check: two different file sets still compare unequal.
    """
    if declared is None:
        raw: List[Any] = []
    elif isinstance(declared, (list, tuple)):
        raw = list(declared)
    else:
        raw = [declared]
    return tuple(sorted({_normalize_path(f) for f in raw if str(f).strip()}))


def _packet_scope_files(packet: Dict[str, Any]) -> Tuple[str, ...]:
    """The packet's declared changed files in canonical normalized form."""
    scope = packet.get("scope") if isinstance(packet, dict) else None
    if not isinstance(scope, dict):
        raise ExecutionPlanningError("CBSP21 packet is missing a scope object")
    return _normalize_declared_files(scope.get("files_expected_to_change", []))


def _validation_sequence(packet: Dict[str, Any]) -> Tuple[str, ...]:
    """The declared verification commands, copied VERBATIM in declared order (no invention).

    CBSP21 does not define a canonical ordering for ``verification.commands_run`` — it is an ordered
    list the author ran — so the declared order is preserved rather than sorted. No command is added.
    """
    verification = packet.get("verification") if isinstance(packet, dict) else None
    if not isinstance(verification, dict):
        raise ExecutionPlanningError("CBSP21 packet is missing a verification object")
    commands = verification.get("commands_run", [])
    if not isinstance(commands, (list, tuple)):
        raise ExecutionPlanningError("verification.commands_run must be a list")
    out: List[str] = []
    for c in commands:
        if not isinstance(c, str) or not c.strip():
            raise ExecutionPlanningError(f"invalid verification command entry: {c!r}")
        out.append(c)
    return tuple(out)


def _most_specific_prefix(file_path: str, authorized: Tuple[str, ...]) -> Optional[str]:
    """Return the longest authorized prefix that contains ``file_path`` (exact or directory-prefix).

    Mirrors the proposal builder's ``_file_within_authorized`` containment semantics so grouping
    agrees with the boundary the proposal already enforced. Longest match wins so a file under a
    nested authorized path is assigned to the most specific group, deterministically.
    """
    f = _normalize_path(file_path)
    best: Optional[str] = None
    for entry in authorized:
        e = entry.strip("/")
        if not e:
            continue
        if f == e or f.startswith(e + "/"):
            if best is None or len(e) > len(best):
                best = e
    return best


def _grouped(
    changed_files: Tuple[str, ...], authorized: Tuple[str, ...]
) -> Tuple[Tuple[str, Tuple[str, ...]], ...]:
    """Deterministically group declared files by their most-specific authorized target-path prefix.

    Returns ``((path_prefix, (file, ...)), ...)`` ordered by ``path_prefix``. Every changed file is
    guaranteed to fall under some authorized path (the proposal builder enforces this); a file that
    somehow does not is a boundary violation and fails closed rather than being silently dropped.
    """
    buckets: Dict[str, List[str]] = {}
    for f in changed_files:
        prefix = _most_specific_prefix(f, authorized)
        if prefix is None:
            raise ExecutionPlanningError(
                f"declared file {f!r} falls outside authorized_target_paths {list(authorized)}"
            )
        buckets.setdefault(prefix, []).append(f)
    return tuple((prefix, tuple(sorted(buckets[prefix]))) for prefix in sorted(buckets))


def _complexity_label(changed_file_count: int, risk_level: str) -> str:
    """Deterministic complexity label from the documented table (counts + declared risk only)."""
    if changed_file_count <= 2:
        file_tier = 0
    elif changed_file_count <= 8:
        file_tier = 1
    else:
        file_tier = 2
    risk_tier = _RISK_TIER[risk_level]
    return _COMPLEXITY_LABELS[max(file_tier, risk_tier)]


def _provenance_reference(proposal: RepositoryChangeProposal) -> ProvenanceReference:
    """Preserve the four evidence-owned provenance fields EXACTLY (fail-closed if any is missing)."""
    t = proposal.target
    ref = ProvenanceReference(
        evidence_candidate_id=_require_str(t.evidence_candidate_id, "evidence_candidate_id"),
        evidence_provenance_hash=_require_str(t.evidence_provenance_hash, "evidence_provenance_hash"),
        producing_subsystem=_require_str(t.producing_subsystem, "producing_subsystem"),
        source_authority_state=_require_str(t.source_authority_state, "source_authority_state"),
    )
    return ref


def _planning_summary(
    *,
    proposal_id: str,
    packet: Dict[str, Any],
    changed_file_count: int,
    group_count: int,
    validation_count: int,
    complexity_label: str,
    risk_level: str,
) -> str:
    """A deterministic, fact-only summary. No recommendations beyond the declared facts."""
    change_type = str(packet.get("change_type", "")).strip() or "unspecified"
    return (
        f"Descriptive execution plan for proposal {proposal_id}: "
        f"{changed_file_count} declared file(s) across {group_count} authorized path group(s); "
        f"declared change_type={change_type}, risk={risk_level}, complexity={complexity_label}; "
        f"{validation_count} declared validation command(s), preserved in declared order. "
        "Groups are a structural path-containment grouping only — the proposal declares no "
        "inter-file dependency evidence, so no execution ordering or dependency is asserted."
    )


def build_execution_plan(
    proposal: RepositoryChangeProposal,
    *,
    created_at: Optional[datetime] = None,
) -> RepositoryExecutionPlan:
    """
    Deterministically build a DESCRIPTIVE ``RepositoryExecutionPlan`` from an approved proposal.

    Derives every field from the proposal and its CBSP21 packet; invents nothing. Fail-closed:
    a non-proposal input, an empty proposal id, an empty/boundary-violating changed-file set, a
    CBSP21-scope/summary disagreement, a missing provenance field, or an unsupported risk level
    raises ``ExecutionPlanningError`` rather than producing a plan. The proposal is never mutated.
    """
    if not isinstance(proposal, RepositoryChangeProposal):
        raise ExecutionPlanningError(
            f"input must be a RepositoryChangeProposal, not {type(proposal).__name__}"
        )
    _require_str(proposal.proposal_id, "proposal_id")

    packet = proposal.cbsp21_packet
    if not isinstance(packet, dict):
        raise ExecutionPlanningError("proposal.cbsp21_packet must be a dict")

    # Normalized on both sides: the comparison below is about the declared file SET, not its
    # formatting (see ``_normalize_declared_files``). The plan carries the normalized form.
    changed_files = _normalize_declared_files(proposal.changed_file_summary)
    if not changed_files:
        raise ExecutionPlanningError("proposal declares no changed files")

    # The proposal's changed-file summary must agree with the packet's declared scope; a mismatch
    # means the two contracts disagree about what changes, which the plan must not paper over.
    if changed_files != _packet_scope_files(packet):
        raise ExecutionPlanningError(
            "proposal.changed_file_summary disagrees with CBSP21 scope.files_expected_to_change"
        )

    authorized = tuple(proposal.target.authorized_target_paths)
    if not authorized:
        raise ExecutionPlanningError("proposal binding declares no authorized_target_paths")

    risk_level = str(packet.get("risk_level", "")).strip().lower()
    if risk_level not in _RISK_TIER:
        raise ExecutionPlanningError(
            f"unsupported declared risk_level {packet.get('risk_level')!r}; "
            f"supported: {list(SUPPORTED_RISK_LEVELS)}"
        )

    grouped = _grouped(changed_files, authorized)
    commit_sequence = tuple(
        ExecutionGroup(group_id=f"grp-{i:02d}", path_prefix=prefix, files=files)
        for i, (prefix, files) in enumerate(grouped)
    )
    # Review order reuses the same evidence-backed groups in the same deterministic path order — no
    # inferred reviewer priority. Built as distinct records so the two fields are independently frozen.
    review_order = tuple(
        ExecutionGroup(group_id=f"grp-{i:02d}", path_prefix=prefix, files=files)
        for i, (prefix, files) in enumerate(grouped)
    )
    structural_dependency_groups = tuple(
        DependencyGroup(
            group_id=f"grp-{i:02d}",
            path_prefix=prefix,
            files=files,
            relationship=STRUCTURAL_GROUPING_RELATIONSHIP,
        )
        for i, (prefix, files) in enumerate(grouped)
    )

    validation_sequence = _validation_sequence(packet)

    complexity = ComplexitySummary(
        label=_complexity_label(len(changed_files), risk_level),
        changed_file_count=len(changed_files),
        authorized_path_count=len(authorized),
        declared_risk_level=risk_level,
    )

    provenance = _provenance_reference(proposal)

    summary = _planning_summary(
        proposal_id=proposal.proposal_id,
        packet=packet,
        changed_file_count=len(changed_files),
        group_count=len(grouped),
        validation_count=len(validation_sequence),
        complexity_label=complexity.label,
        risk_level=risk_level,
    )

    # Content-address the plan from its OWN canonical form rather than a hand-assembled copy of it.
    # ``execution_plan_id`` is excluded from ``_canonical_content()``, so the placeholder below does
    # not perturb the hash. This keeps ONE definition of "the plan's canonical content" (the
    # contract's), so the builder and ``compute_plan_hash()`` cannot drift apart and emit a freshly
    # built plan whose id fails its own ``validate_execution_plan``.
    draft = RepositoryExecutionPlan(
        execution_plan_id="",
        proposal_id=proposal.proposal_id,
        recommended_commit_sequence=commit_sequence,
        recommended_validation_sequence=validation_sequence,
        recommended_review_order=review_order,
        structural_dependency_groups=structural_dependency_groups,
        estimated_complexity=complexity,
        provenance_reference=provenance,
        planning_summary=summary,
        created_at=created_at,
    )
    return replace(draft, execution_plan_id="rep-" + draft.compute_plan_hash())


def _validate_group_collection(groups: Iterable[Any], field: str) -> FrozenSet[str]:
    """Fail-closed check of one group collection; returns the file set it declares.

    A collection is a *partition* of the declared files by authorized path prefix (see
    ``_grouped``): every group is non-empty and well-formed, group ids are unique, each file sits
    under its own group's prefix, and no file is claimed by two groups.
    """
    materialized = list(groups)
    if not materialized:
        raise ExecutionPlanningError(f"{field} is empty")
    seen_ids: set = set()
    files: set = set()
    for group in materialized:
        _require_str(group.group_id, f"{field}.group_id")
        _require_str(group.path_prefix, f"{field}.path_prefix")
        if group.group_id in seen_ids:
            raise ExecutionPlanningError(f"{field} has a duplicate group_id {group.group_id!r}")
        seen_ids.add(group.group_id)
        if not group.files:
            raise ExecutionPlanningError(f"{field} group {group.group_id} declares no files")
        for f in group.files:
            _require_str(f, f"{field}.files entry")
            prefix = _normalize_path(group.path_prefix)
            if _normalize_path(f) != prefix and not _normalize_path(f).startswith(prefix + "/"):
                raise ExecutionPlanningError(
                    f"{field} group {group.group_id} lists file {f!r} outside its "
                    f"path_prefix {group.path_prefix!r}"
                )
            if f in files:
                raise ExecutionPlanningError(
                    f"{field} claims file {f!r} in more than one group (grouping must partition)"
                )
            files.add(f)
    return frozenset(files)


def validate_execution_plan(plan: RepositoryExecutionPlan) -> RepositoryExecutionPlan:
    """
    Fail-closed structural check of an already-built plan (used by tests and downstream consumers).

    Every plan ``build_execution_plan`` produces satisfies this by construction; the check exists
    for plans that arrive from ELSEWHERE — hand-constructed via the public frozen dataclasses, or
    revived from a serialized ``to_canonical_dict()``. For those, the content hash alone proves
    nothing about honesty: ``compute_plan_hash()`` is derived FROM the plan, so any self-consistent
    plan matches its own id. The hash detects tampering AFTER construction; the invariants below are
    what actually bind a plan to the PR-E boundary. So this verifies:

        * the content-addressed id matches the plan's own canonical content (anti-tamper), and
        * the constitutional classification is unchanged — a plan may not self-declare authority,
        * every structural group is honestly labelled ``declared_path_grouping`` — never a
          synthesized dependency edge the proposal has no evidence for,
        * commit/review/dependency collections partition the SAME declared file set (a plan cannot
          silently drop review or dependency coverage for a declared file),
        * provenance/summary/validation commands are present — CBSP21 requires at least one
          declared command, so a real plan always carries one,
        * the complexity label still equals the documented table over its own declared inputs.

    Never invokes git, the filesystem, or the network. Returns the plan unchanged on success.
    """
    if not isinstance(plan, RepositoryExecutionPlan):
        raise ExecutionPlanningError(
            f"input must be a RepositoryExecutionPlan, not {type(plan).__name__}"
        )
    expected_id = "rep-" + plan.compute_plan_hash()
    if plan.execution_plan_id != expected_id:
        raise ExecutionPlanningError(
            f"execution_plan_id {plan.execution_plan_id!r} does not match content hash {expected_id!r}"
        )
    _require_str(plan.proposal_id, "proposal_id")
    _require_str(plan.planning_summary, "planning_summary")

    # Constitutional boundary: descriptive-only. A plan may not relabel itself into authority.
    if plan.constitutional_classification != EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION:
        raise ExecutionPlanningError(
            "constitutional_classification must be "
            f"{EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION!r}, not "
            f"{plan.constitutional_classification!r}"
        )

    for field in (
        "evidence_candidate_id",
        "evidence_provenance_hash",
        "producing_subsystem",
        "source_authority_state",
    ):
        _require_str(getattr(plan.provenance_reference, field), f"provenance_reference.{field}")

    if not plan.recommended_validation_sequence:
        raise ExecutionPlanningError("recommended_validation_sequence is empty")
    for command in plan.recommended_validation_sequence:
        _require_str(command, "recommended_validation_sequence entry")

    declared = _validate_group_collection(
        plan.recommended_commit_sequence, "recommended_commit_sequence"
    )
    for field, collection in (
        ("recommended_review_order", plan.recommended_review_order),
        ("structural_dependency_groups", plan.structural_dependency_groups),
    ):
        if _validate_group_collection(collection, field) != declared:
            raise ExecutionPlanningError(
                f"{field} does not cover the same declared files as recommended_commit_sequence"
            )

    # Honesty of the structural grouping: never a claimed dependency edge.
    for group in plan.structural_dependency_groups:
        if group.relationship != STRUCTURAL_GROUPING_RELATIONSHIP:
            raise ExecutionPlanningError(
                f"structural_dependency_groups group {group.group_id} declares relationship "
                f"{group.relationship!r}; only {STRUCTURAL_GROUPING_RELATIONSHIP!r} is derivable "
                "(the proposal declares no inter-file dependency evidence)"
            )

    complexity = plan.estimated_complexity
    if complexity.declared_risk_level not in _RISK_TIER:
        raise ExecutionPlanningError(
            f"unsupported declared risk_level {complexity.declared_risk_level!r}; "
            f"supported: {list(SUPPORTED_RISK_LEVELS)}"
        )
    if complexity.changed_file_count != len(declared):
        raise ExecutionPlanningError(
            f"estimated_complexity.changed_file_count {complexity.changed_file_count} disagrees "
            f"with the {len(declared)} declared file(s)"
        )
    if complexity.authorized_path_count < 1:
        raise ExecutionPlanningError("estimated_complexity.authorized_path_count must be >= 1")
    expected_label = _complexity_label(complexity.changed_file_count, complexity.declared_risk_level)
    if complexity.label != expected_label:
        raise ExecutionPlanningError(
            f"estimated_complexity.label {complexity.label!r} disagrees with the documented table "
            f"({expected_label!r} for {complexity.changed_file_count} file(s) at risk "
            f"{complexity.declared_risk_level!r})"
        )
    return plan


@dataclass(frozen=True)
class ExecutionPlanner:
    """The stateless, descriptive execution planner. One operation — ``plan`` — no execution verb.

    Mirrors PR-D's ``RepositoryProposalPipeline`` shape: a frozen, logic-light entry point that
    composes the derivation above. It owns no git/filesystem/GitHub/network capability and no method
    that commits, pushes, merges, or creates a pull request.
    """

    def plan(
        self,
        proposal: RepositoryChangeProposal,
        *,
        created_at: Optional[datetime] = None,
    ) -> RepositoryExecutionPlan:
        """Descriptively plan an approved proposal (equivalent to ``build_execution_plan``)."""
        return build_execution_plan(proposal, created_at=created_at)


def execution_plan_builder() -> ExecutionPlanner:
    """Factory: return a stateless ``ExecutionPlanner`` (parallels PR-D's convenience entry points)."""
    return ExecutionPlanner()
