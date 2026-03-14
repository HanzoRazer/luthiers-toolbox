"""
Inlay Pattern Engines

Four core engines that generate all inlay patterns:
1. GridEngine    - Tile repetition on a grid
2. RadialEngine  - N-fold patterns around a center
3. PathEngine    - Patterns along a backbone curve
4. MedallionEngine - Concentric layered patterns

All engines produce GeometryCollection output.
"""
from __future__ import annotations

# Grid Engine
from .grid_engine import (
    GridConfig,
    GridEngine,
)

# Radial Engine
from .radial_engine import (
    RadialConfig,
    RadialEngine,
)

# Path Engine
from .path_engine import (
    PathConfig,
    PathEngine,
)

# Medallion Engine
from .medallion_engine import (
    MedallionConfig,
    MedallionEngine,
    MedallionLayer,
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
