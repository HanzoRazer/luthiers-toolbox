"""
Gibson Les Paul — 1956-59 Standard / Goldtop

Full implementation with CNC body generator (OP20-OP63), Tier 1 neck profile,
669-point body outline, carved maple top geometry, headstock outline.

Authoritative spec: specs/gibson_les_paul.json

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 22
- Strings: 6
- Radius: 12" (304.8mm)
- Body: 444 x 330 x 50.8 mm (maple cap + mahogany back)
- Neck Joint: Set neck, long tenon, 4° angle
- Category: Electric Guitar
"""

from . import spec_from_model_info

MODEL_INFO = {
    "id": "les_paul",
    "display_name": "Gibson Les Paul",
    "manufacturer": "Gibson",
    "year_introduced": 1952,
    "scale_length_mm": 628.65,
    "fret_count": 22,
    "string_count": 6,
    "nut_width_mm": 43.05,
    "end_of_board_width_mm": 57.4,
    "body_width_mm": 330.0,
    "body_length_mm": 444.0,
    "body_thickness_mm": 50.8,
    "body_construction": "solid_mahogany_maple_cap",
    "radius_mm": 304.8,
    "category": "electric_guitar",
    "spec_file": "specs/gibson_les_paul.json",
    "neck_joint": "set_neck_long_tenon",
    "neck_angle_deg": 4.0,
    "neck_profile": "1950s_rounded_C",
    "neck_depth_1st_fret_mm": 22.86,
    "neck_depth_12th_fret_mm": 25.4,
    "headstock_angle_deg": 17.0,
    "headstock_thickness_mm": 17.0,
    "inlays": "trapezoid_pearloid",
    "top_carve": "maple_cap_compound_radius",
}


def get_spec():
    """Get default InstrumentSpec for Les-Paul."""
    return spec_from_model_info(MODEL_INFO)
