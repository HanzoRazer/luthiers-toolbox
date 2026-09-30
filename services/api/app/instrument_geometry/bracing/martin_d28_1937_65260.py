"""
Martin D-28 #65260 top/bracing reconstruction V0.1.

This module is intentionally NOT manufacturing authority. It records only the
geometry that is presently source-measured or drawing-derived for the 1937
Martin D-28 serial #65260 reconstruction.

Primary source chain:
- John Arnold drawing of 1937 D-28 #65260
- John Arnold direct side-height correspondence
- 2026-09-30 draftsman extraction from the Arnold drawing

Datum A is the soundhole. Brace endpoint coordinates are deliberately absent
until every page-2 dimension has an unambiguous datum mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


INCH_TO_MM = 25.4


@dataclass(frozen=True)
class DatumA:
    """Primary top-bracing datum."""

    feature: str
    diameter_in: float
    role: str
    allowed_references: Tuple[str, ...]


@dataclass(frozen=True)
class AngularGeometry:
    """Source-derived angular relationships for the top bracing."""

    x_leg_left_deg: float
    x_leg_right_deg: float
    x_included_deg: float
    lower_brace_relationship_deg: float


@dataclass(frozen=True)
class ReconstructionGeometry:
    """Measured/drawing-derived geometry that may anchor the reconstruction."""

    model_id: str
    maturity: str
    body_length_in: float
    upper_bout_width_in: float
    lower_bout_width_in: float
    datum_a: DatumA
    angles: AngularGeometry
    unmapped_longitudinal_dimensions_in: Tuple[float, ...]
    source_note: str

    @property
    def body_length_mm(self) -> float:
        return self.body_length_in * INCH_TO_MM

    @property
    def upper_bout_width_mm(self) -> float:
        return self.upper_bout_width_in * INCH_TO_MM

    @property
    def lower_bout_width_mm(self) -> float:
        return self.lower_bout_width_in * INCH_TO_MM

    def validate(self) -> None:
        """Fail closed if the currently declared source geometry is inconsistent."""
        if self.maturity != "RECONSTRUCTION_CANDIDATE":
            raise ValueError("D-28 #65260 V0.1 must remain reconstruction-candidate authority")
        if self.datum_a.feature != "soundhole":
            raise ValueError("Datum A must remain the soundhole")
        if self.datum_a.diameter_in <= 0:
            raise ValueError("Soundhole diameter must be positive")
        expected = self.angles.x_leg_left_deg + self.angles.x_leg_right_deg
        if abs(expected - self.angles.x_included_deg) > 1e-9:
            raise ValueError(
                "X-brace angular extraction inconsistent: "
                f"{self.angles.x_leg_left_deg}+{self.angles.x_leg_right_deg}"
                f"!={self.angles.x_included_deg}"
            )
        if any(value <= 0 for value in self.unmapped_longitudinal_dimensions_in):
            raise ValueError("Draftsman dimensions must be positive")


D28_65260_RECONSTRUCTION_V01 = ReconstructionGeometry(
    model_id="martin_d28_1937_65260_reconstruction_v0_1",
    maturity="RECONSTRUCTION_CANDIDATE",
    body_length_in=20.0,
    upper_bout_width_in=11.7,
    lower_bout_width_in=15.7,
    datum_a=DatumA(
        feature="soundhole",
        diameter_in=4.0,
        role="primary_bracing_datum",
        allowed_references=("center", "upper_tangent", "lower_tangent", "edge"),
    ),
    angles=AngularGeometry(
        x_leg_left_deg=49.0,
        x_leg_right_deg=49.0,
        x_included_deg=98.0,
        lower_brace_relationship_deg=110.0,
    ),
    # These are visible on page 2 of the draftsman extraction, but are not
    # assigned to named brace features until their leaders/datum references
    # are independently reconciled. Keeping them unmapped prevents false
    # precision from entering the production geometry.
    unmapped_longitudinal_dimensions_in=(
        1.68,
        1.77,
        1.80,
        1.91,
        2.42,
        4.11,
        4.24,
        9.91,
        10.00,
        11.22,
        12.38,
    ),
    source_note=(
        "John Arnold #65260 drawing plus 2026-09-30 draftsman extraction; "
        "Datum A = soundhole. No brace endpoints are inferred in V0.1."
    ),
)


def get_martin_d28_1937_65260_reconstruction() -> ReconstructionGeometry:
    """Return the validated V0.1 reconstruction candidate."""
    D28_65260_RECONSTRUCTION_V01.validate()
    return D28_65260_RECONSTRUCTION_V01
