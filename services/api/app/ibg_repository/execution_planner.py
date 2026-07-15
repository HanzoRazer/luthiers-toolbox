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

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .repository_change_proposal import RepositoryChangeProposal
from .repository_execution_plan import (
    ComplexitySummary,
    DependencyGroup,
    EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION,
    ExecutionGroup,
    ProvenanceReference,
    RepositoryExecutionPlan,
    STRUCTURAL_GROUPING_RELATIONSHIP,
    _hash_content,
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


def _packet_scope_files(packet: Dict[str, Any]) -> Tuple[str, ...]:
    """The packet's declared changed files, normalized the same way the proposal derived them."""
    scope = packet.get("scope") if isinstance(packet, dict) else None
    if not isinstance(scope, dict):
        raise ExecutionPlanningError("CBSP21 packet is missing a scope object")
    declared = scope.get("files_expected_to_change", [])
    if isinstance(declared, (list, tuple)):
        raw = [str(f) for f in declared]
    elif declared is None:
        raw = []
    else:
        raw = [str(declared)]
    return tuple(sorted({f.strip().replace("\\", "/").strip("/") for f in raw if str(f).strip()}))


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
    f = file_path.strip().replace("\\", "/").strip("/")
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

    changed_files = tuple(proposal.changed_file_summary)
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

    content = {
        "proposal_id": proposal.proposal_id,
        "recommended_commit_sequence": [g.to_canonical_dict() for g in commit_sequence],
        "recommended_validation_sequence": list(validation_sequence),
        "recommended_review_order": [g.to_canonical_dict() for g in review_order],
        "structural_dependency_groups": [d.to_canonical_dict() for d in structural_dependency_groups],
        "estimated_complexity": complexity.to_canonical_dict(),
        "provenance_reference": provenance.to_canonical_dict(),
        "planning_summary": summary,
        "constitutional_classification": EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION,
    }
    execution_plan_id = "rep-" + _hash_content(content)

    return RepositoryExecutionPlan(
        execution_plan_id=execution_plan_id,
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


def validate_execution_plan(plan: RepositoryExecutionPlan) -> RepositoryExecutionPlan:
    """
    Fail-closed structural check of an already-built plan (used by tests and downstream consumers).

    Verifies the content-addressed id matches the plan's own canonical content, that provenance
    fields are present, and that no group references a file outside the plan's declared file set.
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
    for field in (
        "evidence_candidate_id",
        "evidence_provenance_hash",
        "producing_subsystem",
        "source_authority_state",
    ):
        _require_str(getattr(plan.provenance_reference, field), f"provenance_reference.{field}")

    declared = {f for g in plan.recommended_commit_sequence for f in g.files}
    for collection in (plan.recommended_review_order, plan.structural_dependency_groups):
        for group in collection:
            for f in group.files:
                if f not in declared:
                    raise ExecutionPlanningError(
                        f"group {group.group_id} references file {f!r} not in the commit sequence"
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
