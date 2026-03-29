"""
Telecaster Model Stub

Wave 14 Guitar Model - Fender Telecaster

Specifications:
- Scale Length: 647.7mm (25.5")
- Frets: 21
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
    "scale_length_mm": 647.7,
    "fret_count": 21,
    "neck_profile": "modern_C",
    "nut_width_mm": 41.91,
    "neck_depth_1st_mm": 20.0,
    "neck_depth_12th_mm": 22.0,
    "neck_angle_deg": 0.0,
    "headstock_angle_deg": 0.0,
    "fretboard_radius_mm": 241.3,
    "neck_joint": "bolt_on",
    "body_join_fret": 17,
    "source": "Verified spec sheet 2026-03-29",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Telecaster."""
    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=647.7,
        fret_count=21,
        string_count=6,
        base_radius_mm=241.3,
    )
