"""
Cuatro Venezolano Model

Venezuelan cuatro - national instrument of Venezuela.
4 single nylon strings with reentrant tuning (A-D-F#-B).

Specifications (IMCUA 000 Quibor):
- Scale Length: 556.5mm (21.9")
- Frets: 15
- Strings: 4 (nylon, single course)
- Radius: Flat
- Category: Folk String (Latin American family)

Source: Ideal Music Corp drawing IMCUA 000, 8 sheets
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "cuatro_venezolano",
    "display_name": "Cuatro Venezolano (Quibor)",
    "manufacturer": "Various / Ideal Music Corp reference",
    "regional_tradition": "Venezuela",
    "year_introduced": 1500,
    "scale_length_mm": 556.5,
    "fret_count": 15,
    "string_count": 4,
    "nut_width_mm": 40.0,
    "body_width_mm": 250.1,
    "body_length_mm": 350.0,
    "body_depth_mm": 95.0,
    "radius_mm": float("inf"),  # Flat
    "category": "folk_string",
    "family_id": "latin_american",
    "tuning": "A-D-F#-B",
    "tuning_type": "reentrant",
    "spec_file": "models/cuatro_venezolano_spec.json",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Cuatro Venezolano."""
    return InstrumentSpec(
        instrument_type="cuatro",
        scale_length_mm=556.5,
        fret_count=15,
        string_count=4,
        base_radius_mm=None,  # Flat fretboard
    )


def get_body_outline():
    """
    Get body outline points for Cuatro Venezolano.

    Returns:
        None - body outline not yet extracted from DXF.
        When available, returns List[Tuple[float, float]] of (x, y) points in mm.
    """
    return None
