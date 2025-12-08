"""
Firebird Model Stub

Wave 14 Guitar Model - Gibson Firebird

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 22
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Electric Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "firebird",
    "display_name": "Gibson Firebird",
    "manufacturer": "Gibson",
    "year_introduced": 1963,
    "scale_length_mm": 628.65,
    "fret_count": 22,
    "string_count": 6,
    "nut_width_mm": 43.0,
    "body_width_mm": 350.0,
    "body_length_mm": 480.0,
    "radius_mm": 304.8,
    "category": "electric_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Firebird."""
    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=628.65,
        fret_count=22,
        string_count=6,
        base_radius_mm=304.8,
    )
