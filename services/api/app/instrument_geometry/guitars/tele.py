"""
Telecaster Model Stub

Wave 14 Guitar Model - Fender Telecaster

Specifications:
- Scale Length: 648.0mm (25.5")
- Frets: 22
- Strings: 6
- Radius: 9.5" (241.3mm)
- Category: Electric Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "telecaster",
    "display_name": "Fender Telecaster",
    "manufacturer": "Fender",
    "year_introduced": 1950,
    "scale_length_mm": 648.0,
    "fret_count": 22,
    "string_count": 6,
    "nut_width_mm": 42.0,
    "body_width_mm": 320.0,
    "body_length_mm": 430.0,
    "radius_mm": 241.3,
    "category": "electric_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Telecaster."""
    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=648.0,
        fret_count=22,
        string_count=6,
        base_radius_mm=241.3,
    )
