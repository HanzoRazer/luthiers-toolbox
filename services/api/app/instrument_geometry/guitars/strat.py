"""
Stratocaster Model Stub

Wave 14 Guitar Model - Fender Stratocaster

Specifications:
- Scale Length: 648.0mm (25.5")
- Frets: 22
- Strings: 6
- Radius: 9.5" (241.3mm) modern, 7.25" (184.15mm) vintage
- Category: Electric Guitar
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "stratocaster",
    "display_name": "Fender Stratocaster",
    "manufacturer": "Fender",
    "year_introduced": 1954,
    "scale_length_mm": 648.0,
    "fret_count": 22,
    "string_count": 6,
    "nut_width_mm": 42.0,
    "body_width_mm": 330.0,
    "body_length_mm": 460.0,
    "radius_mm": 241.3,  # Modern 9.5"
    "category": "electric_guitar",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Stratocaster."""
    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=648.0,
        fret_count=22,
        string_count=6,
        base_radius_mm=241.3,
        end_radius_mm=304.8,  # Compound: 9.5" to 12"
    )
