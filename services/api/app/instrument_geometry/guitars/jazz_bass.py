"""
Jazz Bass Model Stub

Wave 14 Guitar Model - Fender Jazz Bass

Specifications:
- Scale Length: 863.6mm (34")
- Frets: 20
- Strings: 4
- Radius: 9.5" (241.3mm)
- Category: Bass
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "jazz_bass",
    "display_name": "Fender Jazz Bass",
    "manufacturer": "Fender",
    "year_introduced": 1960,
    "scale_length_mm": 863.6,
    "fret_count": 20,
    "string_count": 4,
    "nut_width_mm": 38.1,
    "body_width_mm": 340.0,
    "body_length_mm": 480.0,
    "radius_mm": 241.3,
    "category": "bass",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Jazz Bass."""
    return InstrumentSpec(
        instrument_type="bass",
        scale_length_mm=863.6,
        fret_count=20,
        string_count=4,
        base_radius_mm=241.3,
    )
