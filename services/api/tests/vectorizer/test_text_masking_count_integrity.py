"""Fast checks for F-2. They do not convert a blueprint."""
from __future__ import annotations

import base64
import io
from types import SimpleNamespace

import pytest
from vectorizer.text_masking_counts import (
    MaskingReductionNotPermitted,
    assert_known_fixture_reduced,
    assert_reported_count_matches_artifact,
    cached_flag_calls,
    reported_entity_count,
)

from app.util.dxf_compat import add_polyline, create_document


def _dxf_bytes(
    line_count: int,
    *,
    version: str = "R12",
    text_values: tuple[str, ...] = (),
    crlf: bool = False,
) -> bytes:
    """A real DXF from dxf_compat: R12 emits LINE segments, R2000 one LWPOLYLINE.

    ``crlf`` matches the line endings the pipeline writes.
    """
    doc = create_document(version)
    msp = doc.modelspace()
    points = [(float(i), 0.0) for i in range(line_count + 1)]
    add_polyline(msp, points, version=version)
    for value in text_values:
        msp.add_text(value)
    stream = io.StringIO()
    doc.write(stream)
    text = stream.getvalue()
    if crlf:
        text = text.replace("\n", "\r\n")
    return text.encode("utf-8")


def _substring_count(dxf_bytes: bytes) -> int:
    """The orchestrator encode stage's counting rule, reproduced only to contrast with it."""
    text = dxf_bytes.decode("utf-8", errors="ignore").replace("\r\n", "\n")
    return text.count("\nLINE\n") + text.count("\nLWPOLYLINE\n")


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


def test_crlf_dxf_is_parsed_not_read_as_empty():
    """The pipeline writes CRLF. Unnormalized, ezdxf reads it as zero entities."""
    payload = _dxf_bytes(3, crlf=True)
    assert b"\r\nLINE\r\n" in payload
    assert_reported_count_matches_artifact(_result(3, payload))


def test_lwpolyline_counts_as_one_entity():
    payload = _dxf_bytes(4, version="R2000")
    assert_reported_count_matches_artifact(_result(1, payload))


def test_artifact_check_is_independent_of_the_substring_count():
    """A TEXT whose value is LINE is not an entity.

    The substring rule counts it, so a count derived that way disagrees with the
    parse. If the helper ever reverted to the substring rule, both sides would
    agree by construction and this test would fail.
    """
    payload = _dxf_bytes(2, text_values=("LINE",))
    assert _substring_count(payload) == 3
    assert_reported_count_matches_artifact(_result(2, payload))
    with pytest.raises(AssertionError, match="does not match"):
        assert_reported_count_matches_artifact(_result(_substring_count(payload), payload))


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
