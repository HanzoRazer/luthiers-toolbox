# services/api/app/art_studio/__init__.py

"""
Art Studio backend package.

This package hosts routes and services that support the Art Studio frontend:
- Bracing previews and calculations
- Rosette design and visualization  
- Inlay layouts and pattern generation
- Guitar component design tools
- VCarve SVG → G-code toolpaths (Wave 1)
- Relief SVG → DXF export (Wave 3)

The Art Studio is the visual design workspace of the The Production Shop,
providing interactive tools for guitar component design with real-time
physics calculations and CAM export capabilities.

## Architecture

```
Art Studio UI (Vue)
    │
    ▼
art_studio/*_router.py (FastAPI endpoints)
    │
    ▼
calculators/service.py (unified facade)
    │
    ▼
calculators/*_calc.py (domain facades)
    │
    ▼
pipelines/*/*.py (legacy math implementations)
```

## Available Routers

- `bracing_router`: Bracing section calculations, mass estimation, DXF export
- `rosette_router`: Rosette channel calculations and DXF export
- `inlay_router`: Fretboard inlay pattern design and DXF export
- `preview_router`: Consolidated SVG preview (relief + vcarve)
- `svg`: Prompt→SVG generation using AI Platform (AI Realignment)
- `prompts`: CNC prompt library with modes, validators, and design lenses
"""

from . import bracing_router
from . import svg  # AI-powered SVG generation (Option 2 architecture)
# REMOVED: rosette_router consolidated into /api/art/rosette (January 2026)
from . import inlay_router
from .preview_consolidated_router import (
    router as preview_router,
    relief_router,
    vcarve_router,
)
from . import prompts  # CNC prompt library (create, transform, optimize, validate)

__all__ = [
    "bracing_router",
    # "rosette_router",  # REMOVED: consolidated
    "inlay_router",
    "preview_router",  # Consolidated relief + vcarve preview
    "relief_router",
    "vcarve_router",
    "svg",  # AI-powered Prompt→SVG generation
    "prompts",  # CNC prompt library with modes and validators
]
