"""
Canonical Geometry Process Approval Tests

C2 geometry-origin closure — PR 1 (process-exclusive canonical authority).

Proves, at the code level, the keystone ruling (PROPOSED / ratification-ready):

    Canonical geometry authority is process-derived, not artifact-derived.
    No artifact, format, route, registry location, or individual reviewer
    identity creates canonical authority by itself — only the approved canonical
    process following a governed approval event does.

These tests are additive. They do NOT assert C2 is closed, and they hold the
transition-mode line: a legacy canonical reference without process-approval
metadata WARNS, it does not RED.
"""

import pytest

from app.cam.canonical_geometry_process_approval import (
    CanonicalProcessApprovalRecord,
    CanonicalProcessApprovalError,
    PROPOSED_CANONICAL_PROCESS_ID,
    PROPOSED_CANONICAL_PROCESS_VERSION,
    PROPOSED_APPROVAL_RULE_ID,
    compute_governed_approval_event_id,
    create_canonical_process_approval_record,
    validate_canonical_process_approval_record,
    process_covers_source_case,
)
from app.cam.geometry_authority_reference import (
    GeometryAuthorityReference,
    create_canonical_geometry_reference,
    create_process_approved_canonical_geometry_reference,
    create_derived_geometry_reference,
)
from app.cam.geometry_authority_validation import (
    validate_geometry_authority_reference,
    validate_canonical_process_authority,
    detect_authority_collapse,
)


def _valid_kwargs(**overrides):
    """Baseline kwargs for the governed approval FACTORY.

    NOTE: no ``governed_approval_event_id`` — under the C2 PR-1 gap-1 lock the
    event id is derived SERVER-SIDE and the factory does not accept it.
    """
    kwargs = dict(
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        source_geometry_id="geo-src-001",
        provenance_hash="prov-hash-deadbeef",
        process_inputs_hash="inputs-hash-cafe",
        approver_id="human:luthier-ross",
        source_geometry_role="evidence",
        source_authority_state="governed_evidence_candidate",
    )
    kwargs.update(overrides)
    return kwargs


def _valid_model_kwargs(**overrides):
    """Baseline kwargs for constructing the RECORD MODEL directly (event id
    supplied, as it would be when a record is rehydrated/inspected)."""
    event_id = overrides.pop("governed_approval_event_id", None)
    kwargs = dict(_valid_kwargs())
    kwargs.update(overrides)
    if event_id is None:
        event_id = compute_governed_approval_event_id(
            approver_id=kwargs["approver_id"],
            canonical_process_id=kwargs["canonical_process_id"],
            canonical_process_version=kwargs["canonical_process_version"],
            approval_rule_id=kwargs["approval_rule_id"],
            source_geometry_id=kwargs["source_geometry_id"],
            provenance_hash=kwargs["provenance_hash"],
            process_inputs_hash=kwargs["process_inputs_hash"],
            decision=kwargs.get("decision", "approve"),
        )
    kwargs["governed_approval_event_id"] = event_id
    return kwargs


# ---------------------------------------------------------------------------
# 1. Governed process approval creates a valid record
# ---------------------------------------------------------------------------

def test_governed_process_approval_creates_record():
    record = create_canonical_process_approval_record(**_valid_kwargs())
    assert isinstance(record, CanonicalProcessApprovalRecord)
    assert record.decision == "approve"
    assert record.canonical_process_id == PROPOSED_CANONICAL_PROCESS_ID
    assert record.deterministic_approval_hash  # populated by factory

    is_valid, reason = validate_canonical_process_approval_record(record)
    assert is_valid
    assert reason is None


def test_approval_hash_is_deterministic_and_excludes_timestamp():
    # compute_hash() is over record CONTENT (incl. the server-set event id and
    # authentication status), excluding the auto timestamp. Two models with
    # identical content -> identical hash.
    r1 = CanonicalProcessApprovalRecord(
        approval_record_id="rec-stable",
        **_valid_model_kwargs(),
    )
    r2 = CanonicalProcessApprovalRecord(
        approval_record_id="rec-stable",
        **_valid_model_kwargs(),
    )
    assert r1.compute_hash() == r2.compute_hash()


def test_governed_approval_event_id_is_server_derived_not_client_supplied():
    # The factory does not accept a caller-supplied event id (gap-1 lock).
    with pytest.raises(TypeError):
        create_canonical_process_approval_record(
            **_valid_kwargs(), governed_approval_event_id="event-i-picked"
        )
    # And what it DOES produce is a server-derived id (not any client string).
    record = create_canonical_process_approval_record(**_valid_kwargs())
    assert record.governed_approval_event_id.startswith("gae-")
    assert record.governed_approval_event_id != "event-i-picked"


def test_governed_approval_event_id_is_stable_for_same_logical_approval():
    first = create_canonical_process_approval_record(**_valid_kwargs())
    second = create_canonical_process_approval_record(**_valid_kwargs())

    assert first.governed_approval_event_id == second.governed_approval_event_id


def test_governed_approval_event_id_changes_when_inputs_change():
    baseline = create_canonical_process_approval_record(**_valid_kwargs())
    changed = create_canonical_process_approval_record(
        **_valid_kwargs(process_inputs_hash="inputs-hash-different")
    )

    assert baseline.governed_approval_event_id != changed.governed_approval_event_id


def test_api_minted_approval_is_unverified_by_default():
    # Fail-safe: every factory-minted approval is unverified in PR-1.
    record = create_canonical_process_approval_record(**_valid_kwargs())
    assert record.authentication == "unverified_pending_governance"


def test_authentication_cannot_be_constructed_verified():
    # No path to a verified record exists in PR-1 — the model refuses it.
    with pytest.raises(ValueError, match="authentication"):
        CanonicalProcessApprovalRecord(
            **_valid_model_kwargs(authentication="verified")
        )


# ---------------------------------------------------------------------------
# 2. A system actor cannot approve process output
# ---------------------------------------------------------------------------

def test_system_actor_cannot_approve_process_output():
    with pytest.raises(CanonicalProcessApprovalError) as exc:
        create_canonical_process_approval_record(
            **_valid_kwargs(approver_id="system:auto-approver")
        )
    assert "system" in str(exc.value).lower()


def test_human_actor_alone_is_not_authority_but_is_permitted_participation():
    # A human approver participates; authority still comes from the full
    # governed record (process id/version/event/provenance), not the human id.
    record = create_canonical_process_approval_record(
        **_valid_kwargs(approver_id="human:someone")
    )
    assert record.approver_id == "human:someone"
    # Stripping the process identity would have blocked it — proving identity
    # alone is insufficient.
    with pytest.raises(CanonicalProcessApprovalError):
        create_canonical_process_approval_record(
            **_valid_kwargs(approver_id="human:someone", canonical_process_id="")
        )


# ---------------------------------------------------------------------------
# 3. Missing process identity blocks the record
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "field",
    [
        "canonical_process_id",
        "canonical_process_version",
        "approval_rule_id",
        "source_geometry_id",
    ],
)
def test_missing_process_identity_blocks_approval_record(field):
    # governed_approval_event_id is intentionally NOT here — it is server-derived
    # and can never be empty/caller-blank (see the dedicated derivation test).
    with pytest.raises(CanonicalProcessApprovalError):
        create_canonical_process_approval_record(**_valid_kwargs(**{field: ""}))


# ---------------------------------------------------------------------------
# 4. Missing provenance blocks the record
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", ["provenance_hash", "process_inputs_hash"])
def test_missing_provenance_blocks_approval_record(field):
    with pytest.raises(CanonicalProcessApprovalError):
        create_canonical_process_approval_record(**_valid_kwargs(**{field: ""}))


# ---------------------------------------------------------------------------
# 5. Process-approved canonical reference carries the approval hash + metadata
# ---------------------------------------------------------------------------

def test_process_approved_canonical_reference_includes_approval_hash():
    record = create_canonical_process_approval_record(**_valid_kwargs())
    ref = create_process_approved_canonical_geometry_reference(
        approval_record=record,
        owning_domain="boe",
    )
    assert ref.authority_layer == "canonical_geometry"
    assert ref.may_define_canonical_geometry is True
    assert ref.process_approval_record_id == record.approval_record_id
    assert ref.process_approval_record_hash == record.deterministic_approval_hash
    assert ref.canonical_process_id == PROPOSED_CANONICAL_PROCESS_ID
    assert ref.canonical_process_version == PROPOSED_CANONICAL_PROCESS_VERSION
    # Event id is server-derived, and carried onto the reference verbatim.
    assert ref.governed_approval_event_id.startswith("gae-")
    assert ref.governed_approval_event_id == record.governed_approval_event_id
    assert ref.provenance_hash == "prov-hash-deadbeef"
    # Authenticity status propagates (fail-safe: unverified in PR-1).
    assert ref.authentication == "unverified_pending_governance"
    # 7T invariants still hold.
    assert ref.execution_authorized is False
    assert ref.machine_output_allowed is False


def test_approval_identity_is_bound_into_reference_hash():
    from app.cam.geometry_authority_reference import GeometryAuthorityReference

    base = dict(
        geometry_reference_id="geo-auth-fixed",
        authority_layer="canonical_geometry",
        owning_domain="boe",
        may_define_canonical_geometry=True,
        process_approval_record_id="rec-1",
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        governed_approval_event_id="gae-fixed",
        process_source_geometry_id="geo-src-fixed",
    )
    a = GeometryAuthorityReference(**base, process_approval_record_hash="hash-A")
    b = GeometryAuthorityReference(**base, process_approval_record_hash="hash-B")
    # Same identity, different backing approval -> different reference hash.
    assert a.compute_hash() != b.compute_hash()

    # A legacy canonical ref (no process metadata) preserves the pre-existing
    # hash shape — process keys are omitted, not None-injected.
    legacy = GeometryAuthorityReference(
        geometry_reference_id="geo-auth-fixed",
        authority_layer="canonical_geometry",
        owning_domain="boe",
        may_define_canonical_geometry=True,
    )
    assert legacy.compute_hash() != a.compute_hash()


def test_process_approved_reference_hash_binds_authentication_if_mutated():
    record = create_canonical_process_approval_record(**_valid_kwargs())
    ref = create_process_approved_canonical_geometry_reference(
        approval_record=record,
        owning_domain="boe",
    )
    original_hash = ref.compute_hash()

    ref.authentication = "verified"

    assert ref.compute_hash() != original_hash


def test_reference_model_rejects_verified_authentication_in_pr1():
    with pytest.raises(ValueError, match="authentication"):
        GeometryAuthorityReference(
            authority_layer="canonical_geometry",
            owning_domain="boe",
            may_define_canonical_geometry=True,
            authentication="verified",
        )


def test_mutated_verified_authentication_is_blocking_not_warning():
    record = create_canonical_process_approval_record(**_valid_kwargs())
    ref = create_process_approved_canonical_geometry_reference(
        approval_record=record,
        owning_domain="boe",
    )
    ref.authentication = "verified"

    ok, reason = validate_canonical_process_authority(ref)
    assert ok is False
    assert reason is not None
    assert "authentication" in reason

    result = validate_geometry_authority_reference(ref)
    assert result.gate == "red"
    assert any("authentication" in issue for issue in result.blocking_issues)


def test_process_approved_canonical_reference_validates_green():
    record = create_canonical_process_approval_record(**_valid_kwargs())
    ref = create_process_approved_canonical_geometry_reference(
        approval_record=record, owning_domain="boe"
    )
    ok, reason = validate_canonical_process_authority(ref)
    assert ok, reason
    result = validate_geometry_authority_reference(ref)
    # No process-approval warning present.
    assert not any("process-approval metadata" in w for w in result.warnings)
    assert result.gate in ("green", "yellow")  # yellow only from unrelated hygiene
    assert result.authority_collapse_detected is False


def test_process_approved_factory_rejects_unapproved_manual_record():
    event_id = compute_governed_approval_event_id(
        approver_id="human:tester",
        canonical_process_id="unknown-process",
        canonical_process_version="v9",
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        source_geometry_id="geo-src-manual",
        provenance_hash="prov-hash-manual",
        process_inputs_hash="inputs-hash-manual",
    )
    record = CanonicalProcessApprovalRecord(
        canonical_process_id="unknown-process",
        canonical_process_version="v9",
        governed_approval_event_id=event_id,
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        source_geometry_id="geo-src-manual",
        provenance_hash="prov-hash-manual",
        process_inputs_hash="inputs-hash-manual",
        approver_id="human:tester",
    )

    with pytest.raises(ValueError, match="process extension required"):
        create_process_approved_canonical_geometry_reference(
            approval_record=record,
            owning_domain="boe",
        )


def test_approval_record_model_rejects_fabricated_event_id():
    with pytest.raises(ValueError, match="governed_approval_event_id"):
        CanonicalProcessApprovalRecord(
            canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
            canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
            governed_approval_event_id="event-manual",
            approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
            source_geometry_id="geo-src-manual",
            provenance_hash="prov-hash-manual",
            process_inputs_hash="inputs-hash-manual",
            approver_id="human:tester",
        )


def test_process_approved_factory_rejects_stale_manual_approval_hash():
    record = create_canonical_process_approval_record(**_valid_kwargs())
    record.deterministic_approval_hash = "hash-stale"

    with pytest.raises(ValueError, match="deterministic approval hash"):
        create_process_approved_canonical_geometry_reference(
            approval_record=record,
            owning_domain="boe",
        )


def test_approval_record_model_rejects_stale_manual_approval_hash():
    with pytest.raises(ValueError, match="deterministic_approval_hash"):
        CanonicalProcessApprovalRecord(
            **_valid_model_kwargs(deterministic_approval_hash="hash-stale")
        )


def test_rehydrated_manual_record_with_matching_event_id_validates():
    event_id = compute_governed_approval_event_id(
        approver_id="human:luthier-ross",
        canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
        canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
        approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
        source_geometry_id="geo-src-001",
        provenance_hash="prov-hash-deadbeef",
        process_inputs_hash="inputs-hash-cafe",
    )
    record = CanonicalProcessApprovalRecord(
        **_valid_model_kwargs(governed_approval_event_id=event_id)
    )

    is_valid, reason = validate_canonical_process_approval_record(record)
    assert is_valid, reason


def test_fabricated_process_metadata_is_blocking_not_warning():
    ref = GeometryAuthorityReference(
        authority_layer="canonical_geometry",
        owning_domain="boe",
        may_define_canonical_geometry=True,
        process_approval_record_id="approval-fake",
        process_approval_record_hash="hash-fake",
        canonical_process_id="unknown-process",
        canonical_process_version="v9",
        governed_approval_event_id="event-fake",
        process_source_geometry_id="geo-fake",
        provenance_hash="prov-fake",
    )

    ok, reason = validate_canonical_process_authority(ref)
    assert ok is False
    assert reason is not None
    assert "unregistered canonical process" in reason

    result = validate_geometry_authority_reference(ref)
    assert result.gate == "red"
    assert result.blocking_issues
    assert not any("process-approval metadata" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# 6. Legacy canonical reference without process approval WARNS, not RED
# ---------------------------------------------------------------------------

def test_canonical_reference_without_process_approval_warns_in_transition_mode():
    legacy = create_canonical_geometry_reference(
        owning_domain="ibg",
        source_authority="legacy",
    )
    ok, reason = validate_canonical_process_authority(legacy)
    assert ok is False
    assert reason is not None
    assert "process-approval metadata" in reason

    result = validate_geometry_authority_reference(legacy)
    # Transition mode: warning, NOT red, NOT a blocking issue.
    assert result.gate != "red"
    assert not result.blocking_issues
    assert any("process-approval metadata" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# 7. Export/representation cannot self-promote to canonical by format claim
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bad_state",
    [
        "dxf",
        "DXF",
        "svg",
        "step",
        "route",
        "storage_location",
        "filename",
        "path/to/x",
        "derived_from_dxf",
        "representation:dxf",
        "upstream_svg",
    ],
)
def test_export_representation_cannot_self_promote_to_canonical(bad_state):
    with pytest.raises(CanonicalProcessApprovalError) as exc:
        create_canonical_process_approval_record(
            **_valid_kwargs(source_authority_state=bad_state)
        )
    msg = str(exc.value).lower()
    assert "format" in msg or "route" in msg or "storage" in msg


def test_source_role_cannot_claim_authority_by_role():
    for bad_role in ["authority", "canonical", "source_authority"]:
        with pytest.raises(CanonicalProcessApprovalError):
            create_canonical_process_approval_record(
                **_valid_kwargs(source_geometry_role=bad_role)
            )


# ---------------------------------------------------------------------------
# 8. IBG / vectorizer / template / spec inputs are eligible but not authority
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("origin", ["ibg", "vectorizer", "user_template", "instrument_spec"])
def test_ibg_vectorizer_template_and_spec_inputs_are_not_direct_authority(origin):
    # Each origin is eligible as an evidence/candidate INPUT to the process...
    record = create_canonical_process_approval_record(
        **_valid_kwargs(
            source_geometry_id=f"geo-{origin}-1",
            source_geometry_role="evidence",
            metadata={"origin": origin},
        )
    )
    ref = create_process_approved_canonical_geometry_reference(
        approval_record=record, owning_domain=origin
    )
    # ...and its canonical authority is evidenced by the process, not by the
    # origin/domain. Removing the process backing removes the authority signal.
    ok, _ = validate_canonical_process_authority(ref)
    assert ok

    naked = create_canonical_geometry_reference(
        owning_domain=origin, source_authority=origin
    )
    naked_ok, _ = validate_canonical_process_authority(naked)
    assert naked_ok is False  # origin alone confers nothing


# ---------------------------------------------------------------------------
# 9. Artifact-specific exception requires process extension
# ---------------------------------------------------------------------------

def test_artifact_exception_requires_process_extension_unknown_process():
    with pytest.raises(CanonicalProcessApprovalError) as exc:
        create_canonical_process_approval_record(
            **_valid_kwargs(canonical_process_id="one-off-bless-this-dxf")
        )
    assert "process extension required" in str(exc.value).lower()


def test_artifact_exception_requires_process_extension_uncovered_role():
    with pytest.raises(CanonicalProcessApprovalError) as exc:
        create_canonical_process_approval_record(
            **_valid_kwargs(source_geometry_role="artifact_specific_exception")
        )
    assert "process extension required" in str(exc.value).lower()


def test_process_coverage_helper():
    assert process_covers_source_case(
        PROPOSED_CANONICAL_PROCESS_ID, PROPOSED_CANONICAL_PROCESS_VERSION, "evidence"
    )
    assert not process_covers_source_case(
        PROPOSED_CANONICAL_PROCESS_ID, PROPOSED_CANONICAL_PROCESS_VERSION, "nope"
    )
    assert not process_covers_source_case("unknown", "v9", "evidence")


# ---------------------------------------------------------------------------
# 10 & 11. No regression to existing 7T guards
# ---------------------------------------------------------------------------

def test_derived_geometry_still_requires_source_reference():
    with pytest.raises(ValueError):
        create_derived_geometry_reference(
            authority_layer="manufacturing_geometry",
            source_geometry_id="",  # missing source
            owning_domain="cam",
        )


def test_existing_non_canonical_authority_collapse_guards_still_red():
    # Force a collapse: a derived reference cannot be constructed with
    # may_define_canonical_geometry=True (model rejects), so verify the
    # collapse detector still flags an export ref carrying canonical_definition.
    from app.cam.geometry_authority_reference import GeometryAuthorityReference

    ref = GeometryAuthorityReference(
        authority_layer="export_geometry",
        source_geometry_id="geo-src-9",
        owning_domain="export",
        allowed_uses=["export", "canonical_definition"],
    )
    assert detect_authority_collapse(ref) is True
    result = validate_geometry_authority_reference(ref)
    assert result.gate == "red"
    assert result.authority_collapse_detected is True
