# services/api/app/cad/__init__.py
"""
CAD / DXF Core Module for Luthier's ToolBox.

This package provides:
  - Validated DXF document creation (dxf_engine)
  - Geometry primitives with Pydantic validation (geometry_models)
  - Optional offset operations via Shapely (offset_engine)
  - Standard layer definitions (dxf_layers)

This package is intentionally AI-agnostic. All geometry is driven by
explicit parameters and validators. AI systems should output parameters
that flow through this package, not raw geometry.

Usage:
    from cad import DxfEngine, Point2D, Polyline2D, Circle2D
    from cad.dxf_layers import LAYER_OUTLINE, LAYER_ROSETTE
    
    engine = DxfEngine()
    engine.add_circle(Circle2D(center=Point2D(x=0, y=0), radius=50))
    dxf_bytes = engine.to_bytes()
"""

from .exceptions import (
    CadEngineError,
    DxfValidationError,
    DxfExportError,
    OffsetEngineError,
    OffsetEngineNotAvailable,
    GeometryError,
)

from .geometry_models import (
    Point2D,
    Point3D,
    Polyline2D,
    Circle2D,
    Arc2D,
    Line2D,
    LayerStyle,
    DxfDocumentConfig,
)

from .dxf_engine import DxfEngine

from .offset_engine import (
    is_offset_available,
    offset_polyline,
    parallel_offset,
    inset_polygon,
    union_polylines,
)

from . import dxf_layers
from . import dxf_validators

__all__ = [
    # Exceptions
    "CadEngineError",
    "DxfValidationError",
    "DxfExportError",
    "OffsetEngineError",
    "OffsetEngineNotAvailable",
    "GeometryError",
    
    # Geometry models
    "Point2D",
    "Point3D",
    "Polyline2D",
    "Circle2D",
    "Arc2D",
    "Line2D",
    "LayerStyle",
    "DxfDocumentConfig",
    
    # Engine
    "DxfEngine",
    
    # Offset operations
    "is_offset_available",
    "offset_polyline",
    "parallel_offset",
    "inset_polygon",
    "union_polylines",
    
    # Modules
    "dxf_layers",
    "dxf_validators",
]

__version__ = "1.0.0"
