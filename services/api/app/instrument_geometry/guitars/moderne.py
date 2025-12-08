"""
Moderne Model Stub

Wave 14 Guitar Model - Gibson Moderne

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 22
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Electric Guitar

Note: The original 1958 Moderne was never commercially produced.
Gibson released reissues starting in 1982.
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "moderne",
    "display_name": "Gibson Moderne",
    "manufacturer": "Gibson",
    "year_introduced": 1958,
    "scale_length_mm": 628.65,
    "fret_count": 22,
    "string_count": 6,
    "nut_width_mm": 43.0,
    "body_width_mm": 380.0,
    "body_length_mm": 470.0,
    "radius_mm": 304.8,
    "category": "electric_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Moderne."""
    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=628.65,
        fret_count=22,
        string_count=6,
        base_radius_mm=304.8,
    )
