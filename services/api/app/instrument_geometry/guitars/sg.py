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
    "neck_profile": "modern_C",
    "nut_width_mm": 43.05,
    "neck_depth_1st_mm": 20.32,
    "neck_depth_12th_mm": 22.225,
    "neck_angle_deg": 4.0,
    "headstock_angle_deg": 17.0,
    "body_join_fret": 19,
    "body_construction": "solid_double_cutaway",
    "source": "Verified spec sheet 2026-03-29",
}


def get_spec():
    """Get default InstrumentSpec for Sg."""
    return spec_from_model_info(MODEL_INFO)
