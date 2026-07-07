"""
Canonical Process Authorization Anchor Tests (AUTHORIZED_CANONICAL_APPROVERS).

C2 process-exclusive canonical authority — the authorization pass. Proves WHO may
turn a governed process approval into VERIFIED canonical authority, that the
decision is made ONCE on the approval record (the reference inherits it), and that
the anchor ships FAIL-CLOSED (empty allowlist -> nothing verified) so the ratified
``unverified_pending_governance`` baseline is preserved and stays GREEN.

These tests seed a temporary authorized approver via monkeypatch; the shipped
anchor is never mutated and no approver id is committed.
"""

import pytest

from app.cam import canonical_geometry_process_policy as policy
from app.cam.canonical_geometry_process_policy import (
    PROPOSED_APPROVAL_RULE_ID,
    PROPOSED_CANONICAL_PROCESS_ID,
    PROPOSED_CANONICAL_PROCESS_VERSION,
    UNVERIFIED_PENDING_GOVERNANCE,
    VERIFIED_GOVERNED_PROCESS,
    is_authorized_canonical_approver,
)
from app.cam.canonical_geometry_process_approval import (
    CanonicalProcessApprovalError,
    CanonicalProcessApprovalRecord,
    compute_governed_approval_event_id,
    create_canonical_process_approval_record,
    validate_canonical_process_approval_record,
)
from app.cam.geometry_authority_reference import (
    create_canonical_geometry_reference,
    create_process_approved_canonical_geometry_reference,
)
from app.cam.geometry_authority_validation import (
    validate_canonical_process_authority,
    validate_geometry_authority_reference,
)


AUTHORIZED_APPROVER = "human:luthier-ross"


def _valid_kwargs(**overrides):
    kwargs = dict(
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        source_geometry_id="geo-src-001",
        provenance_hash="prov-hash-deadbeef",
        process_inputs_hash="inputs-hash-cafe",
        approver_id=AUTHORIZED_APPROVER,
        approver_role="reviewer",
        source_geometry_role="evidence",
        source_authority_state="governed_evidence_candidate",
    )
    kwargs.update(overrides)
    return kwargs


@pytest.fixture
def seed_authorized_approver(monkeypatch):
    """Temporarily add a ratified approver id to the (otherwise empty) anchor.

    monkeypatch.setitem auto-reverts, so the shipped fail-closed anchor is never
    persistently mutated.
    """
    monkeypatch.setitem(
        policy.AUTHORIZED_CANONICAL_APPROVERS,
        (PROPOSED_CANONICAL_PROCESS_ID, PROPOSED_CANONICAL_PROCESS_VERSION),
        {
            PROPOSED_APPROVAL_RULE_ID: {
                "roles": frozenset({"reviewer", "owner"}),
                "approvers": frozenset({AUTHORIZED_APPROVER}),
            }
        },
    )
    return AUTHORIZED_APPROVER


# ---------------------------------------------------------------------------
# 1. Authorized approver -> verified process-approved reference (single decision)
# ---------------------------------------------------------------------------

def test_authorized_approver_verifies_process_approved_reference(seed_authorized_approver):
    record = create_canonical_process_approval_record(**_valid_kwargs())
    assert record.authentication == VERIFIED_GOVERNED_PROCESS

    ref = create_process_approved_canonical_geometry_reference(
        approval_record=record, owning_domain="boe",
    )
    # Single decision point: the reference INHERITS authentication from the record.
    assert ref.authentication == VERIFIED_GOVERNED_PROCESS

    ok, reason = validate_canonical_process_authority(ref)
    assert ok, reason
    result = validate_geometry_authority_reference(ref)
    assert result.gate == "green"
    assert result.blocking_issues == []


# ---------------------------------------------------------------------------
# 2. Unauthorized (unmatched) approver -> soft downgrade, unverified, still GREEN
# ---------------------------------------------------------------------------

def test_unauthorized_approver_remains_unverified_not_rejected():
    # Shipped anchor is empty -> this approver is not allowlisted -> soft.
    record = create_canonical_process_approval_record(
        **_valid_kwargs(approver_id="human:not-authorized")
    )
    assert record.authentication == UNVERIFIED_PENDING_GOVERNANCE

    ref = create_process_approved_canonical_geometry_reference(
        approval_record=record, owning_domain="boe",
    )
    assert ref.authentication == UNVERIFIED_PENDING_GOVERNANCE
    # Baseline is NOT downgraded to a warning in this PR.
    result = validate_geometry_authority_reference(ref)
    assert result.gate == "green"


# ---------------------------------------------------------------------------
# 3. System actor -> hard rejection (record creation) and never authorized
# ---------------------------------------------------------------------------

def test_system_actor_cannot_approve():
    with pytest.raises(CanonicalProcessApprovalError) as exc:
        create_canonical_process_approval_record(**_valid_kwargs(approver_id="system:auto"))
    assert "system" in str(exc.value).lower()


def test_helper_never_authorizes_system_actor(seed_authorized_approver):
    ok, reason = is_authorized_canonical_approver(
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        approver_id="system:auto",
        approver_role="reviewer",
    )
    assert ok is False
    assert "system" in (reason or "").lower()


# ---------------------------------------------------------------------------
# 4. Wrong process version -> not authorized (and unmintable: process extension)
# ---------------------------------------------------------------------------

def test_wrong_process_version_not_authorized(seed_authorized_approver):
    ok, reason = is_authorized_canonical_approver(
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version="v2",
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        approver_id=AUTHORIZED_APPROVER,
        approver_role="reviewer",
    )
    assert ok is False and reason

    with pytest.raises(CanonicalProcessApprovalError, match="process extension required"):
        create_canonical_process_approval_record(**_valid_kwargs(canonical_process_version="v2"))


# ---------------------------------------------------------------------------
# 5. Wrong approval rule -> not authorized -> record stays unverified (soft)
# ---------------------------------------------------------------------------

def test_wrong_approval_rule_not_authorized(seed_authorized_approver):
    ok, _ = is_authorized_canonical_approver(
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        approval_rule_id="some-other-rule",
        approver_id=AUTHORIZED_APPROVER,
        approver_role="reviewer",
    )
    assert ok is False

    record = create_canonical_process_approval_record(
        **_valid_kwargs(approval_rule_id="some-other-rule")
    )
    assert record.authentication == UNVERIFIED_PENDING_GOVERNANCE


# ---------------------------------------------------------------------------
# 6. Fabricated governed_approval_event_id -> hard rejection (model-level)
# ---------------------------------------------------------------------------

def test_fabricated_event_id_rejected():
    with pytest.raises(ValueError, match="governed_approval_event_id"):
        CanonicalProcessApprovalRecord(
            canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
            canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
            governed_approval_event_id="event-manual",
            approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
            source_geometry_id="geo-src",
            provenance_hash="prov",
            process_inputs_hash="inputs",
            approver_id=AUTHORIZED_APPROVER,
        )


# ---------------------------------------------------------------------------
# 7. Legacy canonical route remains a compatibility path (warns, not RED)
# ---------------------------------------------------------------------------

def test_legacy_canonical_reference_warns_not_red():
    legacy = create_canonical_geometry_reference(owning_domain="ibg", source_authority="legacy")
    result = validate_geometry_authority_reference(legacy)
    assert result.gate != "red"
    assert not result.blocking_issues
    assert any("process-approval metadata" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# 8. Representation-only source cannot bypass authorization (even if authorized)
# ---------------------------------------------------------------------------

def test_representation_source_cannot_bypass_authorization(seed_authorized_approver):
    with pytest.raises(CanonicalProcessApprovalError):
        create_canonical_process_approval_record(**_valid_kwargs(source_authority_state="dxf_export"))


# ---------------------------------------------------------------------------
# Authorization semantics — id AND role required; role alone never suffices
# ---------------------------------------------------------------------------

def test_role_without_allowlisted_id_is_unauthorized(seed_authorized_approver):
    ok, reason = is_authorized_canonical_approver(
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        approver_id="human:some-other-reviewer",  # valid role, NOT allowlisted
        approver_role="reviewer",
    )
    assert ok is False
    assert "allowlist" in (reason or "").lower()


def test_allowlisted_id_with_unauthorized_role_is_unauthorized(seed_authorized_approver):
    ok, reason = is_authorized_canonical_approver(
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        approver_id=AUTHORIZED_APPROVER,
        approver_role="intern",  # not in {reviewer, owner}
    )
    assert ok is False
    assert "role" in (reason or "").lower()


# ---------------------------------------------------------------------------
# Fail-closed: the SHIPPED anchor authorizes nobody (no ratified approver id)
# ---------------------------------------------------------------------------

def test_shipped_anchor_is_fail_closed():
    ok, _ = is_authorized_canonical_approver(
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        approver_id=AUTHORIZED_APPROVER,
        approver_role="reviewer",
    )
    assert ok is False
    entry = policy.AUTHORIZED_CANONICAL_APPROVERS[
        (PROPOSED_CANONICAL_PROCESS_ID, PROPOSED_CANONICAL_PROCESS_VERSION)
    ][PROPOSED_APPROVAL_RULE_ID]
    assert entry["approvers"] == frozenset()


# ---------------------------------------------------------------------------
# Provenance-lock: the verified state cannot be forged by direct construction
# ---------------------------------------------------------------------------

def _computed_event_id(**overrides):
    kwargs = _valid_kwargs(**overrides)
    return compute_governed_approval_event_id(
        approver_id=kwargs["approver_id"],
        canonical_process_id=kwargs["canonical_process_id"],
        canonical_process_version=kwargs["canonical_process_version"],
        approval_rule_id=kwargs["approval_rule_id"],
        source_geometry_id=kwargs["source_geometry_id"],
        provenance_hash=kwargs["provenance_hash"],
        process_inputs_hash=kwargs["process_inputs_hash"],
        decision="approve",
    )


def test_forged_verified_record_rejected_at_construction():
    """A caller who computes a valid event id CANNOT hand-set verified authority:
    with the shipped (empty) anchor the approver is not authorized, so the model
    validator refuses the verified state even though every other field is valid."""
    event_id = _computed_event_id()
    with pytest.raises(ValueError, match="verified_governed_process.*not authorized"):
        CanonicalProcessApprovalRecord(
            **_valid_kwargs(),
            governed_approval_event_id=event_id,
            authentication=VERIFIED_GOVERNED_PROCESS,
        )


def test_forged_verified_record_rejected_by_policy_gate():
    """Defense-in-depth: the policy gate independently refuses an unauthorized
    verified record. model_construct() genuinely skips the model validator (unlike
    monkeypatching a compiled pydantic validator), so this exercises the policy
    gate on a record that otherwise looks internally consistent."""
    event_id = _computed_event_id()
    forged = CanonicalProcessApprovalRecord.model_construct(
        **_valid_kwargs(),
        governed_approval_event_id=event_id,
        authentication=VERIFIED_GOVERNED_PROCESS,
    )
    is_valid, reason = validate_canonical_process_approval_record(forged)
    assert is_valid is False
    assert "not authorized" in (reason or "")


def test_authorized_verified_record_rehydration_still_valid(seed_authorized_approver):
    """A genuinely verified record (approver on the anchor) round-trips: direct
    reconstruction with matching event id + verified authentication is accepted by
    BOTH the model validator (construction succeeds) and the policy gate."""
    event_id = _computed_event_id()
    record = CanonicalProcessApprovalRecord(
        **_valid_kwargs(),
        governed_approval_event_id=event_id,
        authentication=VERIFIED_GOVERNED_PROCESS,
    )
    assert record.authentication == VERIFIED_GOVERNED_PROCESS
    is_valid, reason = validate_canonical_process_approval_record(record)
    assert is_valid, reason


# ---------------------------------------------------------------------------
# Provenance-lock: reference boundary (naked forged ref refused; real one passes)
# ---------------------------------------------------------------------------

def test_naked_verified_reference_rejected():
    """A directly-constructed canonical reference cannot claim verified authority
    without the complete backing process-approval metadata."""
    from app.cam.geometry_authority_reference import GeometryAuthorityReference

    with pytest.raises(ValueError, match="requires complete backing process-approval"):
        GeometryAuthorityReference(
            authority_layer="canonical_geometry",
            owning_domain="boe",
            may_define_canonical_geometry=True,
            authentication=VERIFIED_GOVERNED_PROCESS,
        )


def test_verified_reference_with_backing_metadata_roundtrips(seed_authorized_approver):
    """End-to-end: an authorized approver mints a verified record, the reference
    factory inherits verified authentication AND carries the full backing metadata,
    so the reference-boundary lock passes and validation is green."""
    record = create_canonical_process_approval_record(**_valid_kwargs())
    assert record.authentication == VERIFIED_GOVERNED_PROCESS

    ref = create_process_approved_canonical_geometry_reference(
        approval_record=record, owning_domain="boe",
    )
    assert ref.authentication == VERIFIED_GOVERNED_PROCESS
    # Reference-boundary lock is satisfied by the inherited backing metadata.
    result = validate_geometry_authority_reference(ref)
    assert result.gate == "green"
    assert result.blocking_issues == []
