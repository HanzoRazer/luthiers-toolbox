"""Contract tests for RepositoryReadinessReport: serialization, determinism, identity, vocabulary."""

from __future__ import annotations

import dataclasses
import json

import pytest

from app.ibg_repository import (
    READINESS_REPORT_CONSTITUTIONAL_CLASSIFICATION,
    READINESS_REPORT_ID_PREFIX,
    REPORT_SECTION_ORDER,
    ReadinessReportError,
    RepositoryGovernanceSummary,
    RepositoryReadinessReport,
    RepositoryReadinessSection,
    build_execution_plan,
    build_repository_readiness_report,
    evaluate_repository_proposal,
    validate_readiness_summary,
)


def _report(make_proposal, **kwargs):
    proposal = make_proposal(**kwargs)
    plan = build_execution_plan(proposal)
    evaluation = evaluate_repository_proposal(proposal, plan)
    return build_repository_readiness_report(proposal, plan, evaluation)


def test_report_is_frozen(make_proposal):
    report = _report(make_proposal)
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.readiness_report_id = "rpt-tampered"  # type: ignore[misc]


def test_governance_summary_and_section_are_frozen():
    summary = RepositoryGovernanceSummary(finding_count=0, check_ids=())
    section = RepositoryReadinessSection(section_key="proposal", entries=())
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.finding_count = 1  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        section.section_key = "execution"  # type: ignore[misc]


def test_report_id_is_content_addressed_and_prefixed(make_proposal):
    report = _report(make_proposal)
    assert report.readiness_report_id.startswith(READINESS_REPORT_ID_PREFIX)
    assert report.readiness_report_id == READINESS_REPORT_ID_PREFIX + report.compute_report_hash()


def test_report_id_ignores_created_at(make_proposal):
    """Identical semantic content with a different created_at yields the same id."""
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    evaluation = evaluate_repository_proposal(proposal, plan)
    from datetime import datetime

    a = build_repository_readiness_report(proposal, plan, evaluation)
    b = build_repository_readiness_report(
        proposal, plan, evaluation, created_at=datetime(2020, 1, 1)
    )
    assert a.readiness_report_id == b.readiness_report_id
    assert a.to_canonical_dict() == b.to_canonical_dict()


def test_report_id_is_stable_across_independent_builds(make_proposal):
    """Same artifacts rebuilt through content-addressed builders produce a byte-identical report."""
    proposal = make_proposal()
    plan_a = build_execution_plan(proposal)
    plan_b = build_execution_plan(proposal)
    eval_a = evaluate_repository_proposal(proposal, plan_a)
    eval_b = evaluate_repository_proposal(proposal, plan_b)
    report_a = build_repository_readiness_report(proposal, plan_a, eval_a)
    report_b = build_repository_readiness_report(proposal, plan_b, eval_b)
    assert report_a.readiness_report_id == report_b.readiness_report_id
    assert json.dumps(report_a.to_canonical_dict(), sort_keys=True) == json.dumps(
        report_b.to_canonical_dict(), sort_keys=True
    )


def test_report_id_changes_when_a_semantic_field_changes(make_proposal):
    report = _report(make_proposal)
    # Flip to the OTHER valid readiness label so the mutation is guaranteed to differ from the
    # built value whatever the chain evaluates to. Hardcoding "incomplete" is a silent no-op (and
    # thus a false pass) whenever the fixture already evaluates to "incomplete".
    other = "incomplete" if report.readiness_summary == "complete" else "complete"
    mutated = dataclasses.replace(report, readiness_summary=other)
    # A different semantic field must change the recomputed hash.
    assert mutated.compute_report_hash() != report.compute_report_hash()


def test_canonical_dict_excludes_created_at(make_proposal):
    from datetime import datetime

    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    evaluation = evaluate_repository_proposal(proposal, plan)
    report = build_repository_readiness_report(
        proposal, plan, evaluation, created_at=datetime(2021, 6, 1)
    )
    assert "created_at" not in report.to_canonical_dict()
    assert report.to_audit_dict()["created_at"] == "2021-06-01T00:00:00"


def test_canonical_dict_round_trips_through_json(make_proposal):
    report = _report(make_proposal)
    restored = json.loads(json.dumps(report.to_canonical_dict()))
    assert restored["readiness_report_id"] == report.readiness_report_id
    assert restored["readiness_summary"] == report.readiness_summary


def test_sections_serialize_in_canonical_order(make_proposal):
    report = _report(make_proposal)
    serialized = report.to_canonical_dict()["report_sections"]
    assert tuple(s["section_key"] for s in serialized) == REPORT_SECTION_ORDER


def test_classification_declares_no_approval_authority(make_proposal):
    report = _report(make_proposal)
    assert report.constitutional_classification == READINESS_REPORT_CONSTITUTIONAL_CLASSIFICATION
    assert "no_approval_authority" in report.constitutional_classification


def test_validate_readiness_summary_rejects_foreign_vocabulary():
    for good in ("complete", "incomplete"):
        assert validate_readiness_summary(good) == good
    for bad in ("ready", "blocked", "approved", "rejected", "pass", "fail", ""):
        with pytest.raises(ReadinessReportError):
            validate_readiness_summary(bad)
