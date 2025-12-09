"""
Gibson L-00 Model Stub

Wave 14 Guitar Model - Gibson L-00 Small Body

Specifications:
- Scale Length: 628.65mm (24.75")
- Frets: 19
- Strings: 6
- Radius: 12" (304.8mm)
- Category: Acoustic Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "gibson_l_00",
    "display_name": "Gibson L-00",
    "manufacturer": "Gibson",
    "year_introduced": 1926,
    "scale_length_mm": 628.65,
    "fret_count": 19,
    "string_count": 6,
    "nut_width_mm": 43.0,
    "body_width_mm": 350.0,
    "body_length_mm": 450.0,
    "radius_mm": 304.8,
    "category": "acoustic_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Gibson L-00."""
    return InstrumentSpec(
        instrument_type="flat_top",
        scale_length_mm=628.65,
        fret_count=19,
        string_count=6,
        base_radius_mm=304.8,
    )
