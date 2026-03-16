# app/cam/carving/__init__.py

"""
3D Surface Carving Module (BEN-GAP-08)

Generates toolpaths for graduated thickness carving of archtop guitar
tops/backs, Les Paul carved tops, and other 3D surfaces.

Features:
- Graduation map loading and interpolation
- Parametric archtop profile generation (ellipsoidal dome with recurve)
- Parallel-plane (waterline) roughing strategy
- Raster finishing with ball-end scallop control
- Tool compensation for ball/bull nose mills

Usage:
    from app.cam.carving import CarvingPipeline, CarvingConfig, GraduationMap

    # Create graduation map (parametric or from file)
    grad_map = GraduationMap.create_parametric(config.graduation_map)

    # Create pipeline
    pipeline = CarvingPipeline(config, grad_map)

    # Generate complete program
    result = pipeline.generate()
    print(result.get_gcode())
"""

from .config import (
    CarvingConfig,
    CarvingToolSpec,
    CarvingStrategy,
    SurfaceType,
    MaterialHardness,
    GraduationMapConfig,
    RoughingConfig,
    FinishingConfig,
    AsymmetricCarveProfile,
    DEFAULT_CARVING_TOOLS,
    create_benedetto_17_config,
    create_les_paul_top_config,
    create_les_paul_1959_asymmetric_config,
)

from .graduation_map import (
    GraduationMap,
    GraduationPoint,
)

from .surface_carving import (
    SurfaceCarvingGenerator,
    CarvingResult,
    CarvingPass,
    CarvingMove,
)

from .orchestrator import (
    CarvingPipeline,
    CarvingPipelineResult,
)

__all__ = [
    # Config
    "CarvingConfig",
    "CarvingToolSpec",
    "CarvingStrategy",
    "SurfaceType",
    "MaterialHardness",
    "GraduationMapConfig",
    "RoughingConfig",
    "FinishingConfig",
    "AsymmetricCarveProfile",
    "DEFAULT_CARVING_TOOLS",
    "create_benedetto_17_config",
    "create_les_paul_top_config",
    "create_les_paul_1959_asymmetric_config",
    # Graduation Map
    "GraduationMap",
    "GraduationPoint",
    # Surface Carving
    "SurfaceCarvingGenerator",
    "CarvingResult",
    "CarvingPass",
    "CarvingMove",
    # Orchestrator
    "CarvingPipeline",
    "CarvingPipelineResult",
]
