"""
ES-335 Model Stub

Wave 14 Guitar Model - Gibson ES-335

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 22
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Electric Guitar (Semi-hollow)
"""

from . import spec_from_model_info

MODEL_INFO = {
    "id": "es_335",
    "display_name": "Gibson ES-335",
    "manufacturer": "Gibson",
    "year_introduced": 1958,
    "scale_length_mm": 628.65,
    "fret_count": 22,
    "neck_profile": "modern_C",
    "nut_width_mm": 42.85,
    "neck_depth_1st_mm": 21.59,
    "neck_depth_12th_mm": 24.13,
    "neck_angle_deg": 4.0,
    "headstock_angle_deg": 17.0,
    "body_construction": "semi_hollow_thinline",
    "source": "Verified spec sheet 2026-03-29",
}


def get_spec():
    """Get default InstrumentSpec for Es-335."""
    return spec_from_model_info(MODEL_INFO)
