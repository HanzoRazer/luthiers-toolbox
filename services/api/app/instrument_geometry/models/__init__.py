"""
Instrument Geometry Models Package

Wave 19 Module - Fan-Fret CAM Foundation

Provides typed dataclasses and JSON loading for instrument model presets.

Usage:
    from instrument_geometry.models import load_model_spec, list_available_model_ids
    from instrument_geometry.models import GuitarModelSpec, ScaleSpec
    
    # List available presets
    models = list_available_model_ids()
    # ['benedetto_17', 'strat_25_5', ...]
    
    # Load a specific model
    spec = load_model_spec("benedetto_17")
    print(spec.display_name)  # "Benedetto 17\" Archtop"
    print(spec.scale.scale_length_mm())  # 431.8 mm
    
    # Access multiscale (fan-fret) config if present
    if spec.scale.multiscale:
        fan_config = spec.scale.multiscale.to_mm()
        print(fan_config["treble_scale_mm"])  # 648.0 mm
"""

from __future__ import annotations

from .specs import (
    GuitarModelSpec,
    ScaleSpec,
    ScaleProfile,  # Wave 17 - Added for GuitarModelSpec integration
    MultiScaleSpec,
    NeckJointSpec,
    BridgeSpec,
    StringSpec,
    StringSetSpec,
    DXFMappingSpec,
    inch_to_mm,
    INCH_TO_MM,
)

from .loader import (
    load_model_spec,
    load_model_json,
    list_available_model_ids,
    list_model_files,
    MODELS_DIR,
)

# Wave 14 backward compatibility - import from parent models.py
try:
    from ..models import (
        InstrumentModelId,
        InstrumentModelStatus,
        InstrumentCategory,
        ScaleLengthSpec,
        FretPosition,
        NeckProfileSpec,
        # Note: ScaleProfile is now exported from specs.py (Wave 17)
    )
except ImportError:
    # If models.py is missing, define placeholders to prevent import errors
    InstrumentModelId = None
    InstrumentModelStatus = None
    InstrumentCategory = None
    ScaleLengthSpec = None
    FretPosition = None
    NeckProfileSpec = None


__all__ = [
    # Wave 19 specs
    "GuitarModelSpec",
    "ScaleSpec",
    "MultiScaleSpec",
    "NeckJointSpec",
    "BridgeSpec",
    "StringSpec",
    "StringSetSpec",
    "DXFMappingSpec",
    "inch_to_mm",
    "INCH_TO_MM",
    # Wave 19 loader
    "load_model_spec",
    "load_model_json",
    "list_available_model_ids",
    "list_model_files",
    "MODELS_DIR",
    # Wave 14 backward compatibility
    "InstrumentModelId",
    "InstrumentModelStatus",
    "InstrumentCategory",
    "ScaleLengthSpec",
    "FretPosition",
    "NeckProfileSpec",
]


__all__ = [
    # Dataclasses
    "GuitarModelSpec",
    "ScaleSpec",
    "MultiScaleSpec",
    "NeckJointSpec",
    "BridgeSpec",
    "StringSpec",
    "StringSetSpec",
    "DXFMappingSpec",
    
    # Loaders
    "load_model_spec",
    "load_model_json",
    "list_available_model_ids",
    "list_model_files",
    
    # Utilities
    "inch_to_mm",
    "INCH_TO_MM",
    "MODELS_DIR",
]
