"""
PRS Model Stub

Wave 14 Guitar Model - PRS Custom 24

Specifications:
- Scale Length: 635.0mm (25")
- Frets: 24
- Strings: 6
- Radius: 10" (254mm)
- Category: Electric Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "prs",
    "display_name": "PRS Custom 24",
    "manufacturer": "PRS",
    "year_introduced": 1985,
    "scale_length_mm": 635.0,
    "fret_count": 24,
    "string_count": 6,
    "nut_width_mm": 42.5,
    "body_width_mm": 330.0,
    "body_length_mm": 445.0,
    "radius_mm": 254.0,
    "category": "electric_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for PRS."""
    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=635.0,
        fret_count=24,
        string_count=6,
        base_radius_mm=254.0,
    )
