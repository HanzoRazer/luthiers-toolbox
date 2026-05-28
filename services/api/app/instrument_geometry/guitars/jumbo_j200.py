"""
Jumbo J-200 Model — Gibson J-200 Super Jumbo

Canonical dimensions from Gibson spec + IBG FAMILY_DEFAULTS["jumbo"].

Specifications:
- Scale Length: 645.16mm (25.4")
- Frets: 20
- Strings: 6
- Radius: 12" (304.8mm)
- Lower Bout: 432mm (17")
- Category: Acoustic Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "jumbo_j200",
    "display_name": "Gibson J-200 Jumbo",
    "manufacturer": "Gibson",
    "year_introduced": 1937,
    "scale_length_mm": 645.16,
    "fret_count": 20,
    "string_count": 6,
    "nut_width_mm": 43.8,
    "body_width_mm": 432.0,
    "body_length_mm": 530.0,
    "lower_bout_mm": 432.0,
    "upper_bout_mm": 305.0,
    "waist_mm": 254.0,
    "radius_mm": 304.8,
    "category": "acoustic_guitar",
    "ibg_family": "jumbo",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for J-200."""
    return InstrumentSpec(
        instrument_type="flat_top",
        scale_length_mm=645.16,
        fret_count=20,
        string_count=6,
        base_radius_mm=304.8,
    )
