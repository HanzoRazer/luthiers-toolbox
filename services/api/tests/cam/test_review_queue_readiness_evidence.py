"""
Evidence-adapter tests, including historical-gap regressions.

These are the tests that keep the check honest about what actually changed since the
historical 8F assessment. They assert current reality, so if the repository closes a gap,
the corresponding test fails and forces the requirement set to be revisited — which is
exactly the failure mode 8F itself suffered when the timestamp gap closed underneath it.
"""

from app.cam.review_queue_readiness import ReadinessStatus
from app.cam.review_queue_readiness_evaluator import evaluate_requirement
from app.cam.review_queue_readiness_evidence import collect_readiness_evidence
from app.cam.review_queue_readiness_requirements import (
    EVIDENCE_ATTRIBUTABLE_IDENTITY,
    EVIDENCE_CREATION_TIMESTAMP,
    EVIDENCE_DURABLE_PERSISTENCE,
    EVIDENCE_NOTIFICATION_DELIVERY,
    get_requirements,
)


def _finding(requirement_id):
    evidence = collect_readiness_evidence()
    req = next(r for r in get_requirements() if r.requirement_id == requirement_id)
    return evaluate_requirement(req, evidence)


class TestEvidenceContract:
    def test_every_evidence_item_cites_a_source(self):
        for item in collect_readiness_evidence():
            assert item.source.strip(), f"{item.evidence_kind} has no citable source"

    def test_collection_is_deterministic(self):
        first = [(e.evidence_kind, e.present, e.source) for e in collect_readiness_evidence()]
        second = [(e.evidence_kind, e.present, e.source) for e in collect_readiness_evidence()]
        assert first == second

    def test_all_requirement_kinds_are_covered(self):
        kinds = {e.evidence_kind for e in collect_readiness_evidence()}
        assert kinds == {
            EVIDENCE_DURABLE_PERSISTENCE,
            EVIDENCE_ATTRIBUTABLE_IDENTITY,
            EVIDENCE_CREATION_TIMESTAMP,
            EVIDENCE_NOTIFICATION_DELIVERY,
        }


class TestHistoricalGapRegressions:
    """Current status of the four gaps the historical 8F assessment recorded."""

    def test_timestamp_gap_is_closed(self):
        """8F recorded this as open in 2026-05. It has since closed.

        If this test ever fails, the timestamp declaration was removed — not that 8F was
        right after all.
        """
        finding = _finding("RQR-003-TIMESTAMPS")
        assert finding.status is ReadinessStatus.SATISFIED

    def test_persistence_gap_remains_open(self):
        """Registry code existing is not persistence."""
        finding = _finding("RQR-001-PERSISTENCE")
        assert finding.status is ReadinessStatus.UNSATISFIED
        assert "not persistence" in finding.detail.lower()

    def test_identity_is_not_automatically_satisfied(self):
        """A declared reviewer_ref does not prove authentication is enforced."""
        finding = _finding("RQR-002-IDENTITY")
        assert finding.status in (
            ReadinessStatus.UNSATISFIED,
            ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED,
        )

    def test_notification_gap_remains_open(self):
        finding = _finding("RQR-004-NOTIFICATION")
        assert finding.status is ReadinessStatus.UNSATISFIED


class TestNoInferenceFromNames:
    def test_registry_module_name_does_not_imply_persistence(self):
        """The module is called *_registry and still is not durable storage."""
        evidence = next(
            e for e in collect_readiness_evidence()
            if e.evidence_kind == EVIDENCE_DURABLE_PERSISTENCE
        )
        assert evidence.present is False
        assert "review_queue_registry.py" in evidence.source


class TestRequirementRegistry:
    def test_requirement_ids_are_unique(self):
        ids = [r.requirement_id for r in get_requirements()]
        assert len(ids) == len(set(ids))

    def test_every_requirement_names_its_authority(self):
        for req in get_requirements():
            assert req.authority_source.strip()

    def test_ratified_authority_is_recorded(self):
        for req in get_requirements():
            assert "8F" in req.authority_source
