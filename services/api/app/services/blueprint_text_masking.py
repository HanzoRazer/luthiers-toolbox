"""Text-masking acceptance for enhanced blueprint output.

The orchestrator and extract modules are already over the file-size ratchet.
The disposition decision lives here so those files do not grow.
"""

from __future__ import annotations

from typing import Any, Optional

from .contour_recommendation import RecommendationAction

_MASKING_DEGRADED_CODES = frozenset({
    "OCR_PROVIDER_UNAVAILABLE",
    "OCR_INITIALIZATION_FAILED",
    "OCR_EXECUTION_FAILED",
})

_DEGRADED_DXF_WARNING = (
    "Text masking was requested but did not apply. "
    "DXF emitted as degraded output."
)

_REVIEW_REASON = (
    "Text masking was requested but did not apply. "
    "The emitted DXF requires review before manufacturing use."
)


def enhanced_acceptance(
    dxf_valid: bool,
    text_masking: Optional[dict],
) -> tuple[bool, str, RecommendationAction, list[str]]:
    """Accept enhanced output when a requested mask applied or was not needed.

    A degraded mask still has a DXF. That file is review output.
    No text detected is a completed mask and stays acceptable.
    """
    code = (text_masking or {}).get("diagnostic_code")
    if dxf_valid and code not in _MASKING_DEGRADED_CODES:
        return True, "complete", RecommendationAction.ACCEPT, ["Full edge detail preserved"]
    if dxf_valid and code in _MASKING_DEGRADED_CODES:
        return False, "complete", RecommendationAction.REVIEW, [_REVIEW_REASON]
    return False, "extraction", RecommendationAction.REJECT, ["Extraction produced no output"]


def record_text_masking(result: Any, warnings: list[str]) -> Optional[dict]:
    """Copy the conversion disposition and warn when the DXF is degraded."""
    disposition = getattr(result, "text_masking", None)
    masking = disposition.to_dict() if disposition is not None else None
    status = getattr(result, "status", None)
    if getattr(status, "value", None) == "DEGRADED":
        warnings.append(_DEGRADED_DXF_WARNING)
    return masking
