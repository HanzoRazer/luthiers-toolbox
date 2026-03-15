"""
Geometry Authority — family priors, export tolerances, retry policies.
=====================================================================

Single source of truth for expected instrument dimensions (mm) and
the policy knobs that body-isolation scoring, the coach, and the
export gate share.

Every number here is deliberately conservative:
  - width/height ranges are loose enough for most real instruments
  - tolerances are generous; tightening should be data-driven
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


# (height_min_mm, height_max_mm, width_min_mm, width_max_mm)
_FAMILY_BODY_PRIORS_MM: Dict[str, Tuple[float, float, float, float]] = {
    "solid_body": (350.0, 520.0, 280.0, 430.0),
    "archtop":    (430.0, 600.0, 330.0, 460.0),
    "acoustic":   (430.0, 600.0, 330.0, 520.0),
    "bass":       (420.0, 650.0, 280.0, 420.0),
    "ukulele":    (180.0, 380.0, 120.0, 260.0),
}


@dataclass(frozen=True)
class ExportTolerancePolicy:
    pass_threshold: float = 0.75
    review_threshold: float = 0.45
    reject_threshold: float = 0.30


@dataclass(frozen=True)
class RetryPolicy:
    action: str
    notes: str = ""


class GeometryAuthority:
    """
    Minimal geometry authority for coachable vectorization.

    Responsibilities:
      - family body priors
      - export tolerance bands
      - bounded retry suggestions
    """

    def __init__(
        self,
        *,
        family_body_priors_mm: Optional[Dict[str, Tuple[float, float, float, float]]] = None,
    ):
        self.family_body_priors_mm = family_body_priors_mm or _FAMILY_BODY_PRIORS_MM.copy()

    def get_expected_body_profile(self, family: Any) -> Optional[Tuple[float, float, float, float]]:
        fam = self._normalize_family(family)
        return self.family_body_priors_mm.get(fam)

    def get_export_tolerance_policy(self, family: Any = None, workflow: str = "default") -> ExportTolerancePolicy:
        return ExportTolerancePolicy()

    def get_retry_policy(self, issue_type: str, family: Any = None) -> RetryPolicy:
        if issue_type == "lower_bout_missing_likely":
            return RetryPolicy(
                action="rerun_body_isolation",
                notes="Expand lower bounds and retry body ownership.",
            )
        if issue_type == "border_contact_likely":
            return RetryPolicy(
                action="rerun_body_isolation",
                notes="Apply border-ignore bias and retry body ownership.",
            )
        if issue_type == "neck_included_in_body_contour":
            return RetryPolicy(
                action="rerun_contour_stage",
                notes="Try alternate merge/election profile before review.",
            )
        return RetryPolicy(
            action="manual_review_required",
            notes=f"No retry policy defined for issue '{issue_type}'.",
        )

    def score_dimension_fit(
        self,
        *,
        family: Any,
        estimated_height_mm: Optional[float],
        estimated_width_mm: Optional[float],
    ) -> Dict[str, Optional[float]]:
        profile = self.get_expected_body_profile(family)
        if not profile:
            return {"height_fit": None, "width_fit": None}

        h_min, h_max, w_min, w_max = profile
        return {
            "height_fit": self._band_fit(estimated_height_mm, h_min, h_max),
            "width_fit": self._band_fit(estimated_width_mm, w_min, w_max),
        }

    @staticmethod
    def _band_fit(value: Optional[float], lower: float, upper: float) -> Optional[float]:
        if value is None:
            return None
        if lower <= value <= upper:
            return 1.0
        if value < lower:
            return max(0.0, value / lower)
        return max(0.0, upper / value)

    @staticmethod
    def _normalize_family(family: Any) -> Optional[str]:
        if family is None:
            return None
        if isinstance(family, str):
            return family
        # Enum support (InstrumentFamily.ACOUSTIC → "acoustic")
        val = getattr(family, "value", None)
        if isinstance(val, str):
            return val
        # Classification object with .family attribute
        inner = getattr(family, "family", None)
        if isinstance(inner, str):
            return inner
        if inner is not None:
            return getattr(inner, "value", None)
        return None
