"""
Classical Guitar Model Stub

Wave 14 Guitar Model - Classical/Spanish Guitar

Specifications:
- Scale Length: 650.0mm (25.6")
- Frets: 19
- Strings: 6 (nylon)
- Radius: Flat (infinite)
- Category: Acoustic Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "classical",
    "display_name": "Classical Guitar",
    "manufacturer": "Various",
    "year_introduced": 1850,
    "scale_length_mm": 650.0,
    "fret_count": 19,
    "string_count": 6,
    "nut_width_mm": 52.0,
    "body_width_mm": 370.0,
    "body_length_mm": 480.0,
    "radius_mm": float("inf"),  # Flat
    "category": "acoustic_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Classical Guitar."""
    return InstrumentSpec(
        instrument_type="classical",
        scale_length_mm=650.0,
        fret_count=19,
        string_count=6,
        base_radius_mm=None,  # Flat fretboard
    )
