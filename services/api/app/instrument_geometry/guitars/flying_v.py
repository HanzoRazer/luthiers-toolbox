"""
Flying V Model Stub

Wave 14 Guitar Model - Gibson Flying V

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 22
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Electric Guitar
"""

from . import spec_from_model_info

MODEL_INFO = {
    "id": "flying_v",
    "display_name": "Gibson Flying V",
    "manufacturer": "Gibson",
    "year_introduced": 1958,
    "scale_length_mm": 628.65,
    "fret_count": 22,
    "string_count": 6,
    "nut_width_mm": 43.0,
    "body_width_mm": 400.0,
    "body_length_mm": 500.0,
    "radius_mm": 304.8,
    "category": "electric_guitar",
}


def get_spec():
    """Get default InstrumentSpec for Flying-V."""
    return spec_from_model_info(MODEL_INFO)
