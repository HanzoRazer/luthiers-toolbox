"""
Ukulele Model Stub

Wave 14 Guitar Model - Soprano Ukulele

Specifications:
- Scale Length: 330.0mm (13")
- Frets: 12
- Strings: 4
- Radius: Flat or slight
- Category: Ukulele
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "ukulele",
    "display_name": "Soprano Ukulele",
    "manufacturer": "Various",
    "year_introduced": 1879,
    "scale_length_mm": 330.0,
    "fret_count": 12,
    "string_count": 4,
    "nut_width_mm": 35.0,
    "body_width_mm": 200.0,
    "body_length_mm": 280.0,
    "radius_mm": None,  # Typically flat
    "category": "ukulele",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Soprano Ukulele."""
    return InstrumentSpec(
        instrument_type="ukulele",
        scale_length_mm=330.0,
        fret_count=12,
        string_count=4,
        base_radius_mm=None,  # Flat
    )
