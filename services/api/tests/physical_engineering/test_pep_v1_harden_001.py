"""Adversarial cases for the resolver, test policy, and snapshot boundary."""
from __future__ import annotations

import hashlib
import inspect

import pytest
from dataclasses import replace

from app.physical_engineering import (
    CONTRADICTION_RULE_VERSION,
    VALIDATOR_VERSION,
    EvidenceDigestMismatch,
    EvidenceNotFound,
    EvidenceRef,
    FrozenValidationSnapshotV1,
    SnapshotIntegrityError,
    ValidationResult,
    ValidatorConfigurationError,
    capture_snapshot,
    is_finite_number,
    replay_validation,
    validate_proposal,
)
from app.physical_engineering import proposal_v1
from app.physical_engineering.proposal_v1 import CONTRADICTION_RULE_VERSION as RULE_VERSION
from .test_physical_engineering_proposal_v1 import (
    _artifact,
    _policy,
    _proposal,
    _refs,
    _resolver,
    _screen,
    _store,
)


def test_kind_mismatch_is_rejected():
    store = _store()
    store["thk-2026-10-04-R17"] = replace(store["thk-2026-10-04-R17"], kind="density")
    refs = (_refs()[0], EvidenceRef("thk-2026-10-04-R17", "thickness_map"))
    verdict = _screen(_proposal(evidence_refs=refs), resolver=_resolver(store))
    assert verdict.result is ValidationResult.REJECTED
    assert verdict.reason_codes == ("EVIDENCE_KIND_MISMATCH",)
    assert verdict.advisory_review_allowed is False


def test_digest_mismatch_is_rejected():
    store = _store()
    store["thk-2026-10-04-R17"] = replace(
        store["thk-2026-10-04-R17"],
        expected_sha256="0" * 64,
    )
    verdict = _screen(resolver=_resolver(store))
    assert verdict.result is ValidationResult.REJECTED
    assert verdict.reason_codes == ("EVIDENCE_DIGEST_MISMATCH",)


def test_resolver_recomputes_the_digest_from_bytes():
    artifact = _store()["thk-2026-10-04-R17"]
    with pytest.raises(EvidenceDigestMismatch):
        _resolver({"thk-2026-10-04-R17": replace(artifact, artifact_bytes=b"tampered")}).resolve(
            EvidenceRef("thk-2026-10-04-R17", "thickness_map")
        )
    resolved = _resolver().resolve(EvidenceRef("thk-2026-10-04-R17", "thickness_map"))
    assert resolved.artifact_sha256 == hashlib.sha256(artifact.artifact_bytes).hexdigest()


def test_missing_reference_is_evidence_required_not_rejected():
    with pytest.raises(EvidenceNotFound):
        _resolver().resolve(EvidenceRef("missing", "thickness_map"))
    verdict = _screen(_proposal(evidence_refs=(EvidenceRef("missing", "thickness_map"),)))
    assert verdict.result is ValidationResult.EVIDENCE_REQUIRED
    assert "EVIDENCE_REFERENCE_NOT_FOUND" in verdict.reason_codes


def test_projected_remaining_thickness_conflict_is_independent():
    proposal = _proposal(
        contradictory_evidence=(),
        proposed_change=proposal_v1.ProposedChange(
            proposal_v1.ActionType.REMOVE_MATERIAL, 0.5, "half millimetre"
        ),
    )
    verdict = _screen(proposal)
    assert 2.9 >= 2.5
    assert verdict.result is ValidationResult.EVIDENCE_REQUIRED
    assert verdict.reason_codes == ("THICKNESS_CONFLICT_WITH_REMOVAL",)
    assert verdict.advisory_review_allowed is False


def test_remaining_thickness_equal_to_the_minimum_is_allowed():
    proposal = _proposal(
        proposed_change=proposal_v1.ProposedChange(
            proposal_v1.ActionType.REMOVE_MATERIAL, 0.4, "within the test minimum"
        ),
    )
    verdict = _screen(proposal)
    assert verdict.result is ValidationResult.ADVISORY_ALLOWED
    assert verdict.advisory_review_allowed is True


def test_policy_and_resolver_required_before_any_verdict():
    proposal = _proposal()
    with pytest.raises(TypeError):
        validate_proposal(proposal)
    with pytest.raises(ValidatorConfigurationError):
        validate_proposal(proposal, resolver=None, policy=_policy())
    with pytest.raises(ValidatorConfigurationError):
        validate_proposal(proposal, resolver=_resolver(), policy=None)


def test_acquisition_still_requires_configuration():
    ask = _proposal(
        proposed_change=proposal_v1.ProposedChange(
            proposal_v1.ActionType.ACQUIRE_MORE_EVIDENCE,
            description="ask for a scan",
        ),
        evidence_refs=(),
    )

    class Boom:
        def resolve(self, ref):
            raise AssertionError("acquisition without citations must not resolve")

    with pytest.raises(ValidatorConfigurationError):
        validate_proposal(ask, resolver=None, policy=_policy())
    verdict = validate_proposal(ask, resolver=Boom(), policy=_policy())
    assert verdict.result is ValidationResult.ADVISORY_ALLOWED
    assert verdict.advisory_review_allowed is True


def test_matching_digest_does_not_make_bytes_trustworthy():
    """Integrity of opaque bytes is not a judgment that the measurement is true."""
    raw = b"not-a-measurement"
    artifact = _artifact(
        "thk-2026-10-04-R17",
        "thickness_map",
        2.9,
        "mm",
        artifact_bytes=raw,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )
    store = _store()
    store["thk-2026-10-04-R17"] = artifact
    verdict = _screen(resolver=_resolver(store))
    assert verdict.result is ValidationResult.ADVISORY_ALLOWED
    documented = " ".join(proposal_v1.__doc__.split())
    assert "no production engineering authority" in documented


@pytest.mark.parametrize("value", [True, False, float("nan"), float("inf"), "2.9"])
def test_non_finite_resolved_numbers_are_rejected(value):
    assert is_finite_number(value) is False
    store = _store()
    store["thk-2026-10-04-R17"] = replace(store["thk-2026-10-04-R17"], value=value)
    verdict = _screen(resolver=_resolver(store))
    assert verdict.result is ValidationResult.REJECTED
    assert verdict.reason_codes == ("INVALID_RESOLVED_EVIDENCE",)


def test_negative_resolved_uncertainty_is_rejected():
    store = _store()
    store["thk-2026-10-04-R17"] = replace(store["thk-2026-10-04-R17"], uncertainty=-0.01)
    assert _screen(resolver=_resolver(store)).result is ValidationResult.REJECTED


def test_replay_ignores_a_later_change_to_the_live_store():
    store = _store()
    resolver = _resolver(store)
    snapshot = capture_snapshot(_proposal(), resolver=resolver, policy=_policy())
    assert snapshot.result.result is ValidationResult.ADVISORY_ALLOWED
    del store["thk-2026-10-04-R17"]
    replayed = replay_validation(snapshot)
    assert replayed == snapshot.result
    live = validate_proposal(_proposal(), resolver=resolver, policy=_policy())
    assert live.result is ValidationResult.EVIDENCE_REQUIRED
    assert live.reason_codes == ("EVIDENCE_REFERENCE_NOT_FOUND",)
    assert replayed.result is ValidationResult.ADVISORY_ALLOWED


def test_replay_does_not_call_the_resolver():
    class Counting:
        def __init__(self, inner):
            self.inner = inner
            self.calls = 0

        def resolve(self, ref):
            self.calls += 1
            return self.inner.resolve(ref)

    resolver = Counting(_resolver())
    snapshot = capture_snapshot(_proposal(), resolver=resolver, policy=_policy())
    calls_after_capture = resolver.calls
    assert calls_after_capture == 2
    replay_validation(snapshot)
    assert resolver.calls == calls_after_capture
    assert "resolver" not in inspect.signature(replay_validation).parameters


def test_tampered_snapshot_refuses_to_replay():
    snapshot = capture_snapshot(_proposal(), resolver=_resolver(), policy=_policy())
    tampered = replace(
        snapshot,
        result=replace(snapshot.result, reason_codes=("ALL_CHECKS_PASSED", "injected")),
    )
    with pytest.raises(SnapshotIntegrityError):
        replay_validation(tampered)


def test_snapshot_records_the_authoritative_inputs():
    policy = _policy()
    snapshot = capture_snapshot(_proposal(), resolver=_resolver(), policy=policy)
    assert isinstance(snapshot, FrozenValidationSnapshotV1)
    assert snapshot.policy == policy
    assert snapshot.validator_version == VALIDATOR_VERSION
    assert snapshot.contradiction_rule_version == RULE_VERSION
    assert snapshot.resolution_status == "resolved"
    assert len(snapshot.resolved_evidence) == 2
    assert snapshot.snapshot_sha256 == snapshot.result.snapshot_sha256
    assert snapshot.result.validator_version == VALIDATOR_VERSION
    assert CONTRADICTION_RULE_VERSION == "projected-remaining-thickness-1"


def test_deleted_authority_names_are_absent():
    assert "advisory_authority_granted" not in proposal_v1.PhysicalEngineeringValidationV1.__dataclass_fields__
    assert not hasattr(proposal_v1, "MAX_SINGLE_PASS_REMOVAL_MM")
    assert not hasattr(proposal_v1, "AdvisoryReviewContext")
    assert "advisory_review_allowed" in proposal_v1.PhysicalEngineeringValidationV1.__dataclass_fields__


def test_geometry_limitation_is_documented():
    assert "PEP-MESH-SEAM-003" in proposal_v1.__doc__
    assert "untrusted" in proposal_v1.GeometryRegion.__doc__.lower()
