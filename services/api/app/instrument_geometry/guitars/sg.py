"""
SG Model Stub

Wave 14 Guitar Model - Gibson SG

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 22
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Electric Guitar
"""

from . import spec_from_model_info

MODEL_INFO = {
    "id": "sg",
    "display_name": "Gibson SG",
    "manufacturer": "Gibson",
    "year_introduced": 1961,
    "scale_length_mm": 628.65,
    "fret_count": 22,
    "string_count": 6,
    "nut_width_mm": 43.0,
    "body_width_mm": 320.0,
    "body_length_mm": 400.0,
    "radius_mm": 304.8,
    "category": "electric_guitar",
}


def get_spec():
    """Get default InstrumentSpec for Sg."""
    return spec_from_model_info(MODEL_INFO)
