"""
Boundary and regression tests for C2 process-approved canonical authority.

Kept separate from the approval-record tests so the debt-gates file-size ratchet
continues to guard the test surface instead of accepting a new oversized file.
"""

import pytest

from app.cam.canonical_geometry_process_approval import (
    CanonicalProcessApprovalError,
    PROPOSED_CANONICAL_PROCESS_ID,
    PROPOSED_CANONICAL_PROCESS_VERSION,
    create_canonical_process_approval_record,
    process_covers_source_case,
)
from app.cam.geometry_authority_reference import (
    GeometryAuthorityReference,
    create_canonical_geometry_reference,
    create_derived_geometry_reference,
    create_process_approved_canonical_geometry_reference,
)
from app.cam.geometry_authority_validation import (
    detect_authority_collapse,
    validate_canonical_process_authority,
    validate_geometry_authority_reference,
)
from .test_canonical_geometry_process_approval import _valid_kwargs


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


@pytest.mark.parametrize("origin", ["ibg", "vectorizer", "user_template", "instrument_spec"])
def test_ibg_vectorizer_template_and_spec_inputs_are_not_direct_authority(origin):
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

    ok, _ = validate_canonical_process_authority(ref)
    assert ok

    naked = create_canonical_geometry_reference(
        owning_domain=origin, source_authority=origin
    )
    naked_ok, _ = validate_canonical_process_authority(naked)
    assert naked_ok is False


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


def test_derived_geometry_still_requires_source_reference():
    with pytest.raises(ValueError):
        create_derived_geometry_reference(
            authority_layer="manufacturing_geometry",
            source_geometry_id="",
            owning_domain="cam",
        )


def test_existing_non_canonical_authority_collapse_guards_still_red():
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
