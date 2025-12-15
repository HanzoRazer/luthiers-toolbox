# Current __init__.py Contents

**File:** `services/api/app/instrument_geometry/__init__.py`

```python
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
from .models import (  # noqa: F401
    GuitarModelSpec,
    ScaleSpec,
    MultiScaleSpec,
    NeckJointSpec,
    BridgeSpec,
    StringSpec,
    StringSetSpec,
    DXFMappingSpec,
    load_model_spec,
    load_model_json,
    list_available_model_ids,
    list_model_files,
    inch_to_mm,
    INCH_TO_MM,
    MODELS_DIR,
)

# Legacy compatibility: re-exports from shims (these still work)
from .profiles import InstrumentSpec, FretboardSpec  # noqa: F401
from .scale_length import (  # noqa: F401
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
    compute_compensated_scale_length_mm,
)

__all__ = [
    # Wave 14 Core
    "InstrumentModelId",
    "InstrumentModelStatus",
    "InstrumentCategory",
    "ScaleLengthSpec",
    "FretPosition",
    "NeckProfileSpec",
    "COMMON_SCALE_LENGTHS",
    "MODEL_CATEGORIES",
    # Registry
    "get_model_info",
    "get_model_status",
    "list_models",
    "list_production_models",
    "list_stub_models",
    "get_registry_version",
    "get_all_models_summary",
    # Legacy compatibility
    "InstrumentSpec",
    "FretboardSpec",
    "BridgeSpec",
    "compute_fret_positions_mm",
    "compute_fret_spacing_mm",
    "compute_compensated_scale_length_mm",
]
```

## Issue

The import `from .models import ...` is trying to import from the old Wave 14 `models.py` file, but the new Wave 19 code is in:
- `models/specs.py` (dataclasses)
- `models/loader.py` (loading functions)

This causes import errors when trying to test the new Wave 19 model system.
