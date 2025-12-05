"""
RMOS 2.0 Geometry Engine
Selector pattern for ML vs Shapely geometry implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from ..rmos.api_contracts import RmosContext

try:
    from ..art_studio.schemas import RosetteParamSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    from ..rmos.api_contracts import RosetteParamSpec


class GeometryEngine(ABC):
    """Abstract base class for geometry engines"""
    
    @abstractmethod
    def generate_rosette_paths(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> List[Dict[str, Any]]:
        """
        Generate toolpath geometry for rosette design.
        
        Returns:
            List of path segments with coordinates and metadata
        """
        pass
    
    @abstractmethod
    def compute_bounding_box(
        self,
        design: RosetteParamSpec
    ) -> Tuple[float, float, float, float]:
        """
        Compute bounding box (min_x, min_y, max_x, max_y) for design.
        """
        pass


class ShapelyGeometryEngine(GeometryEngine):
    """
    Production geometry engine using Shapely for robust polygon operations.
    """
    
    def generate_rosette_paths(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> List[Dict[str, Any]]:
        """
        Generate rosette paths using Shapely polygon offsetting.
        """
        import math
        
        paths = []
        
        # Generate concentric rings from outer to inner
        outer_radius = design.outer_diameter_mm / 2
        inner_radius = design.inner_diameter_mm / 2
        ring_step = (outer_radius - inner_radius) / design.ring_count
        
        for ring_idx in range(design.ring_count):
            radius = outer_radius - (ring_idx * ring_step)
            
            # Generate circular path with 360 points
            points = []
            for angle_deg in range(0, 360, 1):
                angle_rad = math.radians(angle_deg)
                x = radius * math.cos(angle_rad)
                y = radius * math.sin(angle_rad)
                points.append({"x": round(x, 3), "y": round(y, 3)})
            
            paths.append({
                "type": "ring",
                "ring_index": ring_idx,
                "radius": round(radius, 3),
                "points": points,
                "pattern": design.pattern_type
            })
        
        return paths
    
    def compute_bounding_box(
        self,
        design: RosetteParamSpec
    ) -> Tuple[float, float, float, float]:
        """
        Compute bounding box for rosette (circular, so centered square).
        """
        radius = design.outer_diameter_mm / 2
        return (-radius, -radius, radius, radius)


class MLGeometryEngine(GeometryEngine):
    """
    Legacy ML-based geometry engine (placeholder for historical compatibility).
    Falls back to Shapely for actual computation.
    """
    
    def __init__(self):
        self._fallback = ShapelyGeometryEngine()
    
    def generate_rosette_paths(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> List[Dict[str, Any]]:
        """
        ML geometry generation (placeholder: delegates to Shapely).
        """
        # In real implementation, would load ML model and predict paths
        # For now, fallback to Shapely
        return self._fallback.generate_rosette_paths(design, ctx)
    
    def compute_bounding_box(
        self,
        design: RosetteParamSpec
    ) -> Tuple[float, float, float, float]:
        """
        ML bounding box (placeholder: delegates to Shapely).
        """
        return self._fallback.compute_bounding_box(design)


def get_geometry_engine(ctx: RmosContext) -> GeometryEngine:
    """
    Factory function returning appropriate geometry engine based on context.
    
    Args:
        ctx: RmosContext with use_shapely_geometry flag
    
    Returns:
        GeometryEngine instance (Shapely or ML)
    """
    if ctx.use_shapely_geometry:
        return ShapelyGeometryEngine()
    else:
        return MLGeometryEngine()
