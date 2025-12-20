"""
Instrument Geometry Package

Central home for fret/scale/bridge/radius math used across:

- RMOS 2.0
- Art Studio
- CAM / Toolpath Engine
- Archtop / Flat-top / Electric designs

Wave 14 Structure:
- models.py: InstrumentModelId enum (19 models), InstrumentModelStatus
- registry.py: JSON-backed model registry with caching
- neck/: Fret math, neck profiles, radius calculations
- body/: Body outlines, fretboard geometry
- bridge/: Bridge placement, saddle compensation
- bracing/: X-brace and fan-brace patterns
- guitars/: Per-model stub files (19 models)

See docs/KnowledgeBase/Instrument_Geometry/ for derivations, references, and assumptions.

Design Principles:
- Pure functions: these modules should not know about HTTP, FastAPI, or persistence.
- No side effects: all functions take clear inputs and return simple values or dataclasses.
- Unit-testable: each function gets tests with known scales and geometries.
"""

# Wave 19 Foundation: Model specs and loader
from .models.specs import (  # noqa: F401
    GuitarModelSpec,
    ScaleSpec,
    MultiScaleSpec,
    NeckJointSpec,
    BridgeSpec,
    StringSpec,
    StringSetSpec,
    DXFMappingSpec,
)
from .models.loader import (  # noqa: F401
    load_model_spec,
    load_model_json,
    list_available_model_ids,
    list_model_files,
    inch_to_mm,
    INCH_TO_MM,
    MODELS_DIR,
)

# Canonical exports (updated December 2025 - shims deprecated)
from .neck.fret_math import (  # noqa: F401
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
    compute_compensated_scale_length_mm,
)
from .neck.neck_profiles import (  # noqa: F401
    InstrumentSpec,
    FretboardSpec,
)

__all__ = [
    # Wave 19 Core Types
    "GuitarModelSpec",
    "ScaleSpec",
    "MultiScaleSpec",
    "NeckJointSpec",
    "BridgeSpec",
    "StringSpec",
    "StringSetSpec",
    "DXFMappingSpec",
    # Wave 19 Loader API
    "load_model_spec",
    "load_model_json",
    "list_available_model_ids",
    "list_model_files",
    "inch_to_mm",
    "INCH_TO_MM",
    "MODELS_DIR",
    # Legacy scale utilities (still supported)
    "compute_fret_positions_mm",
    "compute_fret_spacing_mm",
    "compute_compensated_scale_length_mm",
]
