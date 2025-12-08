"""
OM/000 Model Stub

Wave 14 Guitar Model - Martin OM/000 Acoustic

Specifications:
- Scale Length: 645.16mm (25.4")
- Frets: 20
- Strings: 6
- Radius: 16" (406.4mm)
- Category: Acoustic Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "om_000",
    "display_name": "OM/000 Acoustic",
    "manufacturer": "Martin",
    "year_introduced": 1929,
    "scale_length_mm": 645.16,
    "fret_count": 20,
    "string_count": 6,
    "nut_width_mm": 44.5,
    "body_width_mm": 380.0,
    "body_length_mm": 490.0,
    "radius_mm": 406.4,
    "category": "acoustic_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for OM/000."""
    return InstrumentSpec(
        instrument_type="flat_top",
        scale_length_mm=645.16,
        fret_count=20,
        string_count=6,
        base_radius_mm=406.4,
    )
