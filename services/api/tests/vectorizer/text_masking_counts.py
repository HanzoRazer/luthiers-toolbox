"""Count checks for the text-masking regression.

``dxf.entity_count`` is the count the application reports. Comparing a masked
run with an unmasked run is allowed only when the caller states that masking
was applied. Production does not report that disposition yet. F-3 will.
"""
from __future__ import annotations

import base64


class MaskingReductionNotPermitted(AssertionError):
    """A reduction comparison was requested without masking reported as applied."""


def reported_entity_count(result) -> int:
    """Read ``result.dxf.entity_count``. A missing attribute raises."""
    count = result.dxf.entity_count
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError(f"dxf.entity_count must be an int, got {count!r}")
    return count


def emitted_line_entity_count(dxf_bytes: bytes) -> int:
    """Count LINE and LWPOLYLINE records the same way the orchestrator does.

    This checks bytes that were already produced. It does not run a conversion.
    """
    text = dxf_bytes.decode("utf-8", errors="ignore").replace("\r\n", "\n")
    return text.count("\nLINE\n") + text.count("\nLWPOLYLINE\n")


def assert_reported_count_matches_artifact(result) -> None:
    """The reported count must equal the entities in the emitted DXF bytes."""
    reported = reported_entity_count(result)
    raw = base64.b64decode(result.dxf.base64)
    parsed = emitted_line_entity_count(raw)
    if reported != parsed:
        raise AssertionError(
            f"reported dxf.entity_count {reported} does not match "
            f"{parsed} entities in the emitted DXF"
        )


def assert_known_fixture_reduced(masked, unmasked, *, applied=None) -> None:
    """Strict reduction for one known text-bearing fixture, and only if applied.

    This is not a universal vectorizer rule. Equality on that fixture means
    the regression protection failed.
    """
    if applied is not True:
        raise MaskingReductionNotPermitted(
            "reduction assertion is not permitted unless masking reports applied"
        )
    masked_count = reported_entity_count(masked)
    unmasked_count = reported_entity_count(unmasked)
    if not masked_count < unmasked_count:
        raise AssertionError(
            "known text-bearing fixture did not reduce entity count: "
            f"{masked_count} is not < {unmasked_count}"
        )


def cached_flag_calls(compute):
    """Call ``compute`` once per distinct boolean flag and reuse the result."""
    results = {}
    calls = []

    def run(mask_text: bool):
        if mask_text not in results:
            calls.append(mask_text)
            results[mask_text] = compute(mask_text)
        return results[mask_text]

    run.calls = calls
    return run
