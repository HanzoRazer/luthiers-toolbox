"""Reference fretboard preset library.

Each preset is a complete FretboardInput suitable for direct submission to
build_ecosphere(). Presets are reusable by tests, CLI scripts, and any
future Fusion 360 add-in that needs canonical reference geometry.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.instrument_geometry.neck.fretboard_ecosphere import (
    FretboardInput,
    ScaleType,
    TemperamentType,
)


FRETBOARD_PRESETS: Dict[str, FretboardInput] = {
    "fender_strat_25.5": FretboardInput(
        scale_type=ScaleType.STANDARD,
        scale_length_mm=647.7,
        fret_count=22,
        temperament=TemperamentType.EQUAL_12,
        string_count=6,
    ),
    "gibson_les_paul_24.75": FretboardInput(
        scale_type=ScaleType.STANDARD,
        scale_length_mm=628.65,
        fret_count=22,
        temperament=TemperamentType.EQUAL_12,
        string_count=6,
    ),
    "prs_25.0": FretboardInput(
        scale_type=ScaleType.STANDARD,
        scale_length_mm=635.0,
        fret_count=24,
        temperament=TemperamentType.EQUAL_12,
        string_count=6,
    ),
    "fender_jazz_bass_34.0": FretboardInput(
        scale_type=ScaleType.STANDARD,
        scale_length_mm=863.6,
        fret_count=20,
        temperament=TemperamentType.EQUAL_12,
        string_count=4,
    ),
    "smart_guitar_pro_fan_686_648": FretboardInput(
        scale_type=ScaleType.MULTISCALE,
        scale_length_mm=648.0,
        bass_scale_length_mm=686.0,
        fret_count=24,
        temperament=TemperamentType.EQUAL_12,
        string_count=6,
        perpendicular_fret=12,
    ),
}


def get_preset(name: str) -> FretboardInput:
    """Look up a preset by name. Raises KeyError if not found."""
    if name not in FRETBOARD_PRESETS:
        raise KeyError(
            f"Unknown preset: {name!r}. "
            f"Available: {sorted(FRETBOARD_PRESETS.keys())}"
        )
    return FRETBOARD_PRESETS[name]


def list_presets() -> List[Dict[str, Any]]:
    """Return preset summaries for the GET /presets endpoint.

    Returns label + brief identifying info, not the full FretboardInput
    (clients that want full input call /presets/{name} or supply their own).
    """
    return [
        {
            "name": name,
            "scale_length_mm": preset.scale_length_mm,
            "fret_count": preset.fret_count,
            "temperament": preset.temperament.value,
            "string_count": preset.string_count,
            "is_multiscale": preset.scale_type == ScaleType.MULTISCALE,
        }
        for name, preset in FRETBOARD_PRESETS.items()
    ]
