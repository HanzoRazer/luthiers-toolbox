# app/cam/fhole/__init__.py

"""
F-Hole Routing Module (BEN-GAP-09)

Generates G-code toolpaths for routing F-holes through archtop guitar tops.

Features:
- Parametric F-hole geometry generation (traditional, contemporary, Venetian)
- Inside-contour toolpaths with tool radius compensation
- Helical or ramp plunge entry strategies
- Multi-pass depth stepping for through-cuts
- Symmetric F-hole pair generation

Usage:
    from app.cam.fhole import FHoleToolpathGenerator, create_benedetto_17_fhole_config

    # Create configuration
    config = create_benedetto_17_fhole_config()

    # Generate toolpaths
    generator = FHoleToolpathGenerator(config)
    result = generator.generate()

    # Get G-code
    print(result.get_gcode())
"""

from .config import (
    FHoleStyle,
    PlungeStrategy,
    FHoleToolSpec,
    FHoleGeometryConfig,
    FHolePositionConfig,
    FHoleRoutingConfig,
    create_benedetto_17_fhole_config,
    create_les_paul_fhole_config,
    create_jumbo_archtop_fhole_config,
)

from .geometry import (
    FHoleContour,
    FHoleGenerator,
    transform_contour,
    generate_fhole_pair,
)

from .toolpath import (
    FHoleToolpathResult,
    FHoleToolpathGenerator,
)

__all__ = [
    # Config
    "FHoleStyle",
    "PlungeStrategy",
    "FHoleToolSpec",
    "FHoleGeometryConfig",
    "FHolePositionConfig",
    "FHoleRoutingConfig",
    "create_benedetto_17_fhole_config",
    "create_les_paul_fhole_config",
    "create_jumbo_archtop_fhole_config",
    # Geometry
    "FHoleContour",
    "FHoleGenerator",
    "transform_contour",
    "generate_fhole_pair",
    # Toolpath
    "FHoleToolpathResult",
    "FHoleToolpathGenerator",
]
