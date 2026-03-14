"""
Inlay Pattern Engines (Backward Compatibility)

This module re-exports from the split engines/ package for backward compatibility.
New code should import directly from app.art_studio.services.generators.engines.

Original module split into:
- engines/grid_engine.py: GridConfig, GridEngine
- engines/radial_engine.py: RadialConfig, RadialEngine
- engines/path_engine.py: PathConfig, PathEngine
- engines/medallion_engine.py: MedallionConfig, MedallionEngine, MedallionLayer

Usage (unchanged):
    from app.art_studio.services.generators.inlay_engines import GridEngine
    geo = GridEngine.herringbone(params)
"""
from __future__ import annotations

# Re-export all public API for backward compatibility
from .engines import (
    GridConfig,
    GridEngine,
    MedallionConfig,
    MedallionEngine,
    MedallionLayer,
    PathConfig,
    PathEngine,
    RadialConfig,
    RadialEngine,
)

__all__ = [
    # Grid
    "GridConfig",
    "GridEngine",
    # Radial
    "RadialConfig",
    "RadialEngine",
    # Path
    "PathConfig",
    "PathEngine",
    # Medallion
    "MedallionConfig",
    "MedallionEngine",
    "MedallionLayer",
]
