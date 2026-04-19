"""
Cuatro Puertorriqueno Model

Puerto Rican cuatro - national instrument of Puerto Rico.
10 strings in 5 double courses with octave and unison pairs.
Tuned in fourths: B-E-A-D-G.

Specifications:
- Scale Length: 577.85mm (22.75")
- Frets: 20
- Strings: 10 (nylon, 5 courses x 2)
- Radius: Flat
- Category: Folk String (Latin American family)

Note: Body shape is viola-like with horn extensions at lower bout corners.
Entirely distinct from Venezuelan cuatro despite shared name.

Source: cuatro_puertorriqueno.pdf, Mexico luthier collection
"""

from ..neck.neck_profiles import InstrumentSpec

MODEL_INFO = {
    "id": "cuatro_puertorriqueno",
    "display_name": "Cuatro Puertorriqueno",
    "manufacturer": "Various",
    "regional_tradition": "Puerto Rico",
    "year_introduced": 1500,
    "scale_length_mm": 577.85,
    "fret_count": 20,
    "string_count": 10,
    "courses": 5,
    "strings_per_course": 2,
    "nut_width_mm": 42.0,
    "body_width_mm": 304.8,
    "body_depth_mm": 76.2,
    "radius_mm": float("inf"),  # Flat
    "category": "folk_string",
    "family_id": "latin_american",
    "tuning": "B-E-A-D-G",
    "tuning_type": "standard_fourths",
    "body_shape": "viola_like",
    "spec_file": "models/cuatro_puertorriqueno_spec.json",
}


def get_spec() -> InstrumentSpec:
    """Get default InstrumentSpec for Cuatro Puertorriqueno."""
    return InstrumentSpec(
        instrument_type="cuatro",
        scale_length_mm=577.85,
        fret_count=20,
        string_count=10,
        base_radius_mm=None,  # Flat fretboard
    )


def get_body_outline():
    """
    Get body outline points for Cuatro Puertorriqueno.

    Returns:
        None - body outline not yet extracted.
        Viola-like shape with horn extensions requires Fusion 360 tracing.
        When available, returns List[Tuple[float, float]] of (x, y) points in mm.
    """
    return None
