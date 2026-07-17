"""ProposalEvaluator readiness and boundary tests."""

from __future__ import annotations

import copy
import dataclasses

import app.ibg_repository as ibg_repo
from app.ibg_repository import (
    READINESS_COMPLETE,
    READINESS_INCOMPLETE,
    build_execution_plan,
    evaluate_execution_plan,
    evaluate_repository_proposal,
    validate_repository_proposal_evaluation,
)
from .proposal_evaluator_helpers import (
    FILES,
    _reseal_plan,
    _reseal_proposal,
    _status,
)

# --- readiness label semantics ---------------------------------------------------------------------


def test_a_scalar_changed_file_summary_is_read_without_crashing(make_proposal):
    """A hand-built contract may carry a bare string; a string is one entry, never its characters."""
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    proposal = _reseal_proposal(
        dataclasses.replace(proposal, changed_file_summary=FILES[0])  # type: ignore[arg-type]
    )
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "completeness.changed_file_summary_present") == "pass"
    assert _status(evaluation, "invariant.plan_covers_all_declared_files") == "pass"
    assert _status(evaluation, "governance.changed_files_within_authorized_paths") == "pass"


def test_a_plan_with_no_group_collections_is_read_without_crashing(make_proposal):
    proposal = make_proposal()
    # Not resealed: a plan with no group collections cannot hash itself, which the id check reports.
    plan = dataclasses.replace(
        build_execution_plan(proposal),
        recommended_review_order=None,  # type: ignore[arg-type]
        structural_dependency_groups=None,  # type: ignore[arg-type]
    )
    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "execution.plan_groups_internally_consistent") == "pass"
    assert _status(evaluation, "execution.plan_id_matches_content_hash") == "fail"


def test_readiness_is_derived_only_from_failed_applicable_checks(make_proposal):
    proposal = make_proposal()
    complete = evaluate_repository_proposal(proposal, build_execution_plan(proposal))
    assert complete.checks_failed == 0
    assert complete.readiness_summary == READINESS_COMPLETE

    plan = _reseal_plan(
        dataclasses.replace(
            build_execution_plan(proposal), recommended_validation_sequence=("something else",)
        )
    )
    incomplete = evaluate_repository_proposal(proposal, plan)
    assert incomplete.checks_failed > 0
    assert incomplete.readiness_summary == READINESS_INCOMPLETE


def test_a_not_applicable_check_alone_never_makes_an_evaluation_incomplete(make_proposal):
    """not_applicable is an absence of evidence, not a defect — it cannot flip the label."""
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    proposal = _reseal_proposal(dataclasses.replace(proposal, changed_file_summary=()))
    plan = _reseal_plan(
        dataclasses.replace(plan, proposal_id=proposal.proposal_id, recommended_commit_sequence=())
    )
    evaluation = evaluate_repository_proposal(proposal, plan)
    # This artifact does have real failures; assert the label tracks failures, not the n/a count.
    assert evaluation.readiness_summary == (
        READINESS_COMPLETE if evaluation.checks_failed == 0 else READINESS_INCOMPLETE
    )


# --- observational boundary ------------------------------------------------------------------------


def test_evaluation_does_not_mutate_the_proposal_or_the_plan(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    proposal_before = copy.deepcopy(proposal.to_audit_dict())
    plan_before = copy.deepcopy(plan.to_audit_dict())

    evaluate_repository_proposal(proposal, plan)

    assert proposal.to_audit_dict() == proposal_before
    assert plan.to_audit_dict() == plan_before


def test_evaluation_does_not_upgrade_the_authority_state(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    before = proposal.target.source_authority_state

    evaluate_repository_proposal(proposal, plan)

    assert proposal.target.source_authority_state == before
    assert plan.provenance_reference.source_authority_state == before


def test_evaluation_carries_no_repository_or_approval_authority(evaluation_of):
    evaluation = evaluation_of()
    for forbidden in ("approve", "reject", "block", "authorize", "merge", "commit", "push", "execute"):
        assert not hasattr(evaluation, forbidden)
    assert (
        evaluation.constitutional_classification
        == "observational_proposal_evaluation__no_approval_authority"
    )


def test_evaluate_execution_plan_returns_only_the_plan_facing_findings(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    findings = evaluate_execution_plan(proposal, plan)

    assert {f.category for f in findings} == {"execution", "invariant"}
    # Shares the full evaluation's logic rather than forking it.
    full = evaluate_repository_proposal(proposal, plan)
    assert findings == tuple(
        f for f in full.all_findings() if f.category in {"execution", "invariant"}
    )
    assert list(findings) == sorted(findings, key=lambda f: (f.category, f.check_id))


def test_evaluator_modules_perform_no_git_filesystem_github_or_network_operation():
    """AST-precise: the evaluator may not even IMPORT an execution or network capability."""
    import ast
    from pathlib import Path

    pkg_dir = Path(ibg_repo.__file__).parent
    forbidden_top = {
        "subprocess",
        "os",
        "shutil",
        "tempfile",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "http",
        "pygithub",
        "github",
    }
    forbidden_local = (
        "git_runner",
        "worktree_builder",
        "worktree_validator",
        "worktree_spec",
        "worktree_state",
    )
    for module_name in ("repository_proposal_evaluation.py", "proposal_evaluator.py"):
        src = (pkg_dir / module_name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = (node.module or "").split(".")[0]
                if base:
                    imported.add(base)
                if node.module:
                    for local in forbidden_local:
                        assert local not in node.module, f"{module_name} must not import PR-B {local}"
        leaked = imported & forbidden_top
        assert not leaked, f"{module_name} must not import {leaked}"


def test_evaluator_does_not_attach_to_the_pipeline_or_the_planner():
    """PR F is a separate downstream consumer: it must not modify or wrap the upstream stages.

    The evaluation layer is two files — ``proposal_evaluator.py`` (orchestration + public API) and
    ``proposal_checks.py`` (the 25 check builders) — so the invariant is asserted over BOTH: neither
    may import the pipeline/review-bundle or any plan/pipeline BUILDER, or call one.
    """
    import ast
    from pathlib import Path

    layer = Path(ibg_repo.__file__).parent
    imported_names: set[str] = set()
    called: set[str] = set()
    for module_file in ("proposal_evaluator.py", "proposal_checks.py"):
        tree = ast.parse((layer / module_file).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "repository_proposal_pipeline" not in node.module, module_file
                assert "repository_review_bundle" not in node.module, module_file
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.add(node.func.id)

    # The layer reuses the planner's supported-risk set, but imports no plan/pipeline BUILDER...
    assert "SUPPORTED_RISK_LEVELS" in imported_names
    for builder in ("build_execution_plan", "ExecutionPlanner", "run_repository_proposal_pipeline"):
        assert builder not in imported_names, f"evaluation layer must not import {builder}"

    # ...and calls none of them anywhere (AST-precise: prose in a docstring is not a call).
    assert not called & {"build_execution_plan", "ExecutionPlanner", "build_review_bundle"}


def test_evaluation_is_not_wired_into_the_existing_pipeline():
    """The pipeline is unchanged by PR F; nothing evaluates implicitly as a side effect."""
    from app.ibg_repository import repository_proposal_pipeline

    src_names = dir(repository_proposal_pipeline)
    assert "evaluate_repository_proposal" not in src_names
    assert "ProposalEvaluator" not in src_names
    assert "RepositoryProposalEvaluation" not in src_names
