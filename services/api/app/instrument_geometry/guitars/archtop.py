"""
Archtop Model Stub

Wave 14 Guitar Model - Jazz Archtop

Specifications:
- Scale Length: 635.0mm (25")
- Frets: 20
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Archtop
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "archtop",
    "display_name": "Jazz Archtop",
    "manufacturer": "Various",
    "year_introduced": 1922,
    "scale_length_mm": 635.0,
    "fret_count": 20,
    "string_count": 6,
    "nut_width_mm": 43.0,
    "body_width_mm": 420.0,
    "body_length_mm": 540.0,
    "radius_mm": 304.8,
    "category": "archtop",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Archtop."""
    return InstrumentSpec(
        instrument_type="archtop",
        scale_length_mm=635.0,
        fret_count=20,
        string_count=6,
        base_radius_mm=304.8,
    )
