"""Fast checks for F-2. They do not convert a blueprint."""
from __future__ import annotations

import base64
from types import SimpleNamespace

import pytest

from vectorizer.text_masking_counts import (
    MaskingReductionNotPermitted,
    assert_known_fixture_reduced,
    assert_reported_count_matches_artifact,
    cached_flag_calls,
    reported_entity_count,
)


def _dxf_bytes(line_count: int) -> bytes:
    parts = ["0", "SECTION", "2", "ENTITIES"]
    for _ in range(line_count):
        parts.extend(["0", "LINE", "8", "0"])
    parts.extend(["0", "ENDSEC", "0", "EOF", ""])
    return "\n".join(parts).encode("ascii")


def _result(entity_count, payload: bytes = b""):
    return SimpleNamespace(
        dxf=SimpleNamespace(
            entity_count=entity_count,
            base64=base64.b64encode(payload).decode("ascii"),
        )
    )


def test_missing_dxf_fails_instead_of_substituting_zero():
    with pytest.raises(AttributeError):
        reported_entity_count(SimpleNamespace())


def test_missing_entity_count_fails_instead_of_substituting_zero():
    with pytest.raises(AttributeError):
        reported_entity_count(SimpleNamespace(dxf=SimpleNamespace()))


def test_bool_count_is_rejected():
    with pytest.raises(TypeError):
        reported_entity_count(_result(True))


def test_reported_count_matches_the_emitted_dxf():
    payload = _dxf_bytes(2)
    result = _result(2, payload)
    assert reported_entity_count(result) == 2
    assert_reported_count_matches_artifact(result)


def test_reported_count_rejects_a_mismatch_with_the_emitted_dxf():
    with pytest.raises(AssertionError, match="does not match"):
        assert_reported_count_matches_artifact(_result(1, _dxf_bytes(2)))


def test_applied_mask_passes_when_the_known_fixture_shrinks():
    assert_known_fixture_reduced(_result(3), _result(5), applied=True)


def test_identical_counts_fail_when_masking_was_applied():
    with pytest.raises(AssertionError, match="did not reduce"):
        assert_known_fixture_reduced(_result(5), _result(5), applied=True)


@pytest.mark.parametrize("applied", [False, None])
def test_reduction_is_not_permitted_without_applied(applied):
    with pytest.raises(MaskingReductionNotPermitted):
        assert_known_fixture_reduced(_result(3), _result(5), applied=applied)


def test_omitted_disposition_does_not_permit_reduction():
    with pytest.raises(MaskingReductionNotPermitted):
        assert_known_fixture_reduced(_result(3), _result(5))


def test_cached_flags_perform_exactly_two_calls():
    seen = []

    def compute(mask_text: bool):
        seen.append(mask_text)
        return mask_text

    run = cached_flag_calls(compute)
    assert run(True) is True
    assert run(False) is False
    assert run(True) is True
    assert run(False) is False
    assert seen == [True, False]
    assert run.calls == [True, False]
