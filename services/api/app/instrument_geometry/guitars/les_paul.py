"""
Les Paul Model Stub

Wave 14 Guitar Model - Gibson Les Paul

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 22
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Electric Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "les_paul",
    "display_name": "Gibson Les Paul",
    "manufacturer": "Gibson",
    "year_introduced": 1952,
    "scale_length_mm": 628.65,
    "fret_count": 22,
    "string_count": 6,
    "nut_width_mm": 43.0,
    "body_width_mm": 330.0,
    "body_length_mm": 440.0,
    "radius_mm": 304.8,
    "category": "electric_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Les Paul."""
    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=628.65,
        fret_count=22,
        string_count=6,
        base_radius_mm=304.8,
    )
