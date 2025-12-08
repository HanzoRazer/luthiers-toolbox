"""
J-45 Model Stub

Wave 14 Guitar Model - Gibson J-45

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 20
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Acoustic Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "j_45",
    "display_name": "Gibson J-45",
    "manufacturer": "Gibson",
    "year_introduced": 1942,
    "scale_length_mm": 628.65,
    "fret_count": 20,
    "string_count": 6,
    "nut_width_mm": 43.8,
    "body_width_mm": 410.0,
    "body_length_mm": 510.0,
    "radius_mm": 304.8,
    "category": "acoustic_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for J-45."""
    return InstrumentSpec(
        instrument_type="flat_top",
        scale_length_mm=628.65,
        fret_count=20,
        string_count=6,
        base_radius_mm=304.8,
    )
