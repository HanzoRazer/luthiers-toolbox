"""Builder tests: lineage enforcement, provenance cross-check, verbatim copying, and boundaries."""

from __future__ import annotations

import dataclasses

import pytest

import app.ibg_repository as ibg_repo
from app.ibg_repository import (
    REPORT_SECTION_ORDER,
    ReadinessReportError,
    build_execution_plan,
    build_repository_readiness_report,
    evaluate_repository_proposal,
    validate_repository_readiness_report,
)


def _chain(make_proposal, **kwargs):
    """A coherent (proposal, plan, evaluation) triple sharing one lineage chain."""
    proposal = make_proposal(**kwargs)
    plan = build_execution_plan(proposal)
    evaluation = evaluate_repository_proposal(proposal, plan)
    return proposal, plan, evaluation


def _entries(report, section_key):
    section = next(s for s in report.report_sections if s.section_key == section_key)
    return dict(section.entries)


# --------------------------------------------------------------------------- happy path


def test_builds_a_valid_report_over_a_coherent_chain(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    assert validate_repository_readiness_report(report) is report
    assert report.proposal_id == proposal.proposal_id
    assert report.execution_plan_id == plan.execution_plan_id
    assert report.evaluation_id == evaluation.evaluation_id


def test_sections_are_exactly_the_four_canonical_keys_in_order(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    assert tuple(s.section_key for s in report.report_sections) == REPORT_SECTION_ORDER


# --------------------------------------------------------------------------- verbatim copying


def test_summaries_are_copied_verbatim(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    # execution_summary is the documented rename of the plan's canonical planning_summary.
    assert report.execution_summary == plan.planning_summary
    assert report.evaluation_summary == evaluation.evaluation_summary
    assert report.readiness_summary == evaluation.readiness_summary


def test_governance_summary_projects_check_ids_in_upstream_order(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    expected = tuple(f.check_id for f in evaluation.governance_findings)
    # Verbatim upstream order — the builder must NOT re-sort.
    assert report.governance_summary.check_ids == expected
    assert report.governance_summary.finding_count == len(evaluation.governance_findings)
    assert report.governance_summary.finding_count == len(report.governance_summary.check_ids)


def test_evaluation_section_values_equal_their_source_fields_exactly(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    e = _entries(report, "evaluation")
    assert e["evaluation_id"] == evaluation.evaluation_id
    assert e["readiness_summary"] == evaluation.readiness_summary
    assert e["completeness_score"] == evaluation.completeness_score
    assert e["checks_passed"] == evaluation.checks_passed
    assert e["checks_failed"] == evaluation.checks_failed
    assert e["checks_not_applicable"] == evaluation.checks_not_applicable
    assert e["checks_applicable"] == evaluation.checks_applicable
    assert e["evaluation_summary"] == evaluation.evaluation_summary


def test_provenance_section_copies_the_plan_reference_verbatim(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    p = _entries(report, "provenance")
    ref = plan.provenance_reference
    assert p["evidence_candidate_id"] == ref.evidence_candidate_id
    assert p["evidence_provenance_hash"] == ref.evidence_provenance_hash
    assert p["producing_subsystem"] == ref.producing_subsystem
    assert p["source_authority_state"] == ref.source_authority_state


def test_proposal_section_copies_proposal_and_binding_values(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    s = _entries(report, "proposal")
    assert s["proposal_id"] == proposal.proposal_id
    assert s["proposed_branch"] == proposal.proposed_branch
    assert s["repository_id"] == proposal.target.repository_id
    assert s["base_revision"] == proposal.target.base_revision
    assert s["change_intent"] == proposal.target.change_intent


# --------------------------------------------------------------------------- lineage enforcement


def test_rejects_proposal_plan_lineage_mismatch(make_proposal):
    proposal_a, plan_a, eval_a = _chain(make_proposal)
    proposal_b = make_proposal()  # fresh evidence -> different proposal_id
    with pytest.raises(ReadinessReportError, match="describes proposal"):
        build_repository_readiness_report(proposal_b, plan_a, eval_a)


def test_rejects_proposal_evaluation_lineage_mismatch(make_proposal):
    proposal_a, plan_a, eval_a = _chain(make_proposal)
    proposal_b, plan_b, _ = _chain(make_proposal)
    # plan_b matches proposal_b, but eval_a describes proposal_a -> evaluation mismatch.
    with pytest.raises(ReadinessReportError, match="evaluation describes proposal"):
        build_repository_readiness_report(proposal_b, plan_b, eval_a)


def test_rejects_plan_evaluation_execution_id_mismatch(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    # Same proposal_id, but an evaluation pointing at a different execution_plan_id.
    stray_eval = dataclasses.replace(evaluation, execution_plan_id="rep-0000000000000000")
    with pytest.raises(ReadinessReportError, match="execution_plan"):
        build_repository_readiness_report(proposal, plan, stray_eval)


def test_rejects_provenance_disagreement(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    corrupted_ref = dataclasses.replace(
        plan.provenance_reference, producing_subsystem="some_other_subsystem"
    )
    corrupted_plan = dataclasses.replace(plan, provenance_reference=corrupted_ref)
    # Rebuild the evaluation so lineage IDs still line up and only provenance disagrees.
    corrupted_eval = dataclasses.replace(
        evaluation, execution_plan_id=corrupted_plan.execution_plan_id
    )
    with pytest.raises(ReadinessReportError, match="provenance field"):
        build_repository_readiness_report(proposal, corrupted_plan, corrupted_eval)


# --------------------------------------------------------------------------- fail-closed inputs


@pytest.mark.parametrize("slot", [0, 1, 2])
def test_none_inputs_fail_closed(make_proposal, slot):
    proposal, plan, evaluation = _chain(make_proposal)
    args = [proposal, plan, evaluation]
    args[slot] = None
    with pytest.raises(ReadinessReportError):
        build_repository_readiness_report(*args)


@pytest.mark.parametrize("slot", [0, 1, 2])
def test_wrong_type_inputs_fail_closed(make_proposal, slot):
    proposal, plan, evaluation = _chain(make_proposal)
    args = [proposal, plan, evaluation]
    args[slot] = "not-an-artifact"
    with pytest.raises(ReadinessReportError):
        build_repository_readiness_report(*args)


# --------------------------------------------------------------------------- immutability & determinism


def test_inputs_are_not_mutated(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    before = (proposal.to_canonical_dict(), plan.to_canonical_dict(), evaluation.to_canonical_dict())
    build_repository_readiness_report(proposal, plan, evaluation)
    after = (proposal.to_canonical_dict(), plan.to_canonical_dict(), evaluation.to_canonical_dict())
    assert before == after


def test_validate_rejects_a_tampered_id(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    tampered = dataclasses.replace(report, readiness_report_id="rpt-deadbeefdeadbeef")
    with pytest.raises(ReadinessReportError, match="does not match content hash"):
        validate_repository_readiness_report(tampered)


# --------------------------------------------------------------------------- constitutional boundary


def test_report_and_builder_speak_no_decision_vocabulary(make_proposal):
    """No approve/reject/authorize/merge vocabulary appears in the report's carried values."""
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    forbidden = ("approve", "reject", "authorize", "merge", "block", "commit", "push")
    haystacks = [report.readiness_summary]
    for section in report.report_sections:
        for name, value in section.entries:
            if isinstance(value, str) and name not in ("planning_summary", "evaluation_summary"):
                # The two carried upstream summaries are canonical prose owned by E/F; the report's
                # OWN vocabulary (keys, labels, readiness) is what must stay decision-free.
                haystacks.append(f"{name}={value}")
    blob = " ".join(haystacks).lower()
    for word in forbidden:
        assert word not in blob, f"decision word {word!r} leaked into report vocabulary"


def test_g_modules_perform_no_git_filesystem_github_or_network_operation():
    """AST-precise: the report modules may not even IMPORT an execution or network capability."""
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
    for module_name in ("repository_readiness_report.py", "readiness_report_builder.py"):
        src = (pkg_dir / module_name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported: set = set()
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


def test_report_is_not_wired_into_the_upstream_pipeline_or_evaluator():
    """PR G is a separate downstream consumer; upstream modules are unchanged by it."""
    from app.ibg_repository import repository_proposal_pipeline, proposal_evaluator

    assert "build_repository_readiness_report" not in dir(repository_proposal_pipeline)
    assert "build_repository_readiness_report" not in dir(proposal_evaluator)
    assert "RepositoryReadinessReport" not in dir(proposal_evaluator)


# --------------------------------------------------------------------------- validator fail-closed branches


def test_validate_rejects_a_non_report():
    with pytest.raises(ReadinessReportError, match="must be a RepositoryReadinessReport"):
        validate_repository_readiness_report("not-a-report")


def _rehash(report):
    """Re-mint the id so only the deliberately corrupted field trips the validator (not the id)."""
    from app.ibg_repository import READINESS_REPORT_ID_PREFIX

    return dataclasses.replace(
        report, readiness_report_id=READINESS_REPORT_ID_PREFIX + report.compute_report_hash()
    )


def test_validate_rejects_governance_count_mismatch(make_proposal):
    from app.ibg_repository import RepositoryGovernanceSummary

    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    broken = _rehash(
        dataclasses.replace(
            report,
            governance_summary=RepositoryGovernanceSummary(finding_count=99, check_ids=("a",)),
        )
    )
    with pytest.raises(ReadinessReportError, match="finding_count"):
        validate_repository_readiness_report(broken)


def test_validate_rejects_wrong_section_order(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    reordered = tuple(reversed(report.report_sections))
    broken = _rehash(dataclasses.replace(report, report_sections=reordered))
    with pytest.raises(ReadinessReportError, match="report_sections must be exactly"):
        validate_repository_readiness_report(broken)


def test_validate_rejects_empty_identity(make_proposal):
    proposal, plan, evaluation = _chain(make_proposal)
    report = build_repository_readiness_report(proposal, plan, evaluation)
    broken = _rehash(dataclasses.replace(report, evaluation_id="   "))
    with pytest.raises(ReadinessReportError, match="evaluation_id must be a non-empty string"):
        validate_repository_readiness_report(broken)
