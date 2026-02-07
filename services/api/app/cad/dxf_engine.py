# services/api/app/cad/dxf_engine.py
"""
Core DXF Engine - Validated wrapper around ezdxf.

This engine:
  - Provides a clean, type-safe API for DXF creation
  - Enforces validation guardrails on all geometry
  - Is AI-agnostic (no knowledge of AI systems)
  - Supports multiple export formats (bytes, file)

Usage:
    from cad.dxf_engine import DxfEngine
    from cad.geometry_models import Polyline2D, Point2D, DxfDocumentConfig
    
    engine = DxfEngine()
    engine.add_polyline(Polyline2D(points=[Point2D(x=0, y=0), Point2D(x=100, y=100)]))
    dxf_bytes = engine.to_bytes()
"""

from __future__ import annotations

from io import StringIO
from typing import Iterable, Tuple, Optional, List, Dict, Any
from pathlib import Path
import logging

import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace

from .exceptions import DxfExportError, DxfValidationError
from .geometry_models import (
    Arc2D, Circle2D, DxfDocumentConfig, Line2D,
    Point2D, Polyline2D, EntityList,
)
from .dxf_validators import (
    ensure_entity_limit, validate_polyline, validate_circle,
    validate_arc, validate_line, ensure_point_within_bounds,
)
from . import dxf_layers


logger = logging.getLogger(__name__)


class DxfEngine:
    """
    Validated DXF document builder.
    
    Features:
      - Automatic layer creation
      - Coordinate and entity count guardrails
      - Multiple entity type support
      - Export to bytes or file
    
    Thread Safety:
      NOT thread-safe. Create one engine per document.
    """
    
    def __init__(self, config: Optional[DxfDocumentConfig] = None) -> None:
        """
        Initialize a new DXF document.
        
        Args:
            config: Document configuration. Uses defaults if None.
        """
        self.config = config or DxfDocumentConfig()
        
        # Create ezdxf document
        self.doc: Drawing = ezdxf.new(self.config.version)
        self.msp: Modelspace = self.doc.modelspace()
        
        # Track entity count for guardrail
        self._entity_count: int = 0
        
        # Track created layers
        self._layers_created: set = set()
        
        # Setup
        self._setup_units()
        if self.config.create_default_layers:
            self._ensure_default_layers()
    
    # =========================================================================
    # PROPERTIES
    # =========================================================================
    
    @property
    def entity_count(self) -> int:
        """Current entity count in document."""
        return self._entity_count
    
    @property
    def layers(self) -> List[str]:
        """List of layer names in the document."""
        return [layer.dxf.name for layer in self.doc.layers]
    
    # =========================================================================
    # INTERNAL SETUP
    # =========================================================================
    
    def _setup_units(self) -> None:
        """
        Configure INSUNITS for the document based on config.units.
        
        DXF INSUNITS values:
          0 = Unitless
          1 = Inches
          4 = Millimeters
        """
        units_map = {"mm": 4, "inch": 1}
        self.doc.header["$INSUNITS"] = units_map.get(self.config.units, 4)
        logger.debug(f"DXF units set to: {self.config.units}")
    
    def _ensure_default_layers(self) -> None:
        """Create standard layers if they don't exist."""
        for layer_name in dxf_layers.DEFAULT_LAYERS:
            self._ensure_layer(layer_name)
    
    def _ensure_layer(self, name: str) -> None:
        """Create a layer if it doesn't exist."""
        if name not in self._layers_created and name not in self.doc.layers:
            layer_config = dxf_layers.get_layer_config(name)
            self.doc.layers.new(
                name=name,
                dxfattribs={
                    "color": layer_config.color_index,
                    "linetype": layer_config.linetype,
                }
            )
            self._layers_created.add(name)
            logger.debug(f"Created layer: {name}")
    
    def _increment_entities(self, count: int = 1) -> None:
        """Increment entity count and check limit."""
        self._entity_count += count
        ensure_entity_limit(self._entity_count, self.config)
    
    # =========================================================================
    # PUBLIC GEOMETRY METHODS
    # =========================================================================
    
    def add_polyline(
        self, 
        poly: Polyline2D, 
        layer: str = dxf_layers.LAYER_OUTLINE,
        dxfattribs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a polyline to the document.
        
        Args:
            poly: Polyline geometry
            layer: Target layer name
            dxfattribs: Additional DXF attributes
        """
        if self.config.validate_geometry:
            validate_polyline(poly, self.config)
        
        self._ensure_layer(layer)
        
        attribs = {"layer": layer, "closed": poly.closed}
        if dxfattribs:
            attribs.update(dxfattribs)
        
        self.msp.add_lwpolyline(poly.to_tuples(), dxfattribs=attribs)
        self._increment_entities()
    
    def add_circle(
        self, 
        circle: Circle2D, 
        layer: str = dxf_layers.LAYER_OUTLINE,
        dxfattribs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a circle to the document.
        
        Args:
            circle: Circle geometry
            layer: Target layer name
            dxfattribs: Additional DXF attributes
        """
        if self.config.validate_geometry:
            validate_circle(circle, self.config)
        
        self._ensure_layer(layer)
        
        attribs = {"layer": layer}
        if dxfattribs:
            attribs.update(dxfattribs)
        
        self.msp.add_circle(
            center=circle.center.to_tuple(),
            radius=circle.radius,
            dxfattribs=attribs,
        )
        self._increment_entities()
    
    def add_arc(
        self, 
        arc: Arc2D, 
        layer: str = dxf_layers.LAYER_OUTLINE,
        dxfattribs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add an arc to the document.
        
        Args:
            arc: Arc geometry
            layer: Target layer name
            dxfattribs: Additional DXF attributes
        """
        if self.config.validate_geometry:
            validate_arc(arc, self.config)
        
        self._ensure_layer(layer)
        
        attribs = {"layer": layer}
        if dxfattribs:
            attribs.update(dxfattribs)
        
        self.msp.add_arc(
            center=arc.center.to_tuple(),
            radius=arc.radius,
            start_angle=arc.start_angle_deg,
            end_angle=arc.end_angle_deg,
            dxfattribs=attribs,
        )
        self._increment_entities()
    
    def add_line(
        self, 
        line: Line2D, 
        layer: str = dxf_layers.LAYER_OUTLINE,
        dxfattribs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a line to the document.
        
        Args:
            line: Line geometry
            layer: Target layer name
            dxfattribs: Additional DXF attributes
        """
        if self.config.validate_geometry:
            validate_line(line, self.config)
        
        self._ensure_layer(layer)
        
        attribs = {"layer": layer}
        if dxfattribs:
            attribs.update(dxfattribs)
        
        self.msp.add_line(
            start=line.start.to_tuple(),
            end=line.end.to_tuple(),
            dxfattribs=attribs,
        )
        self._increment_entities()
    
    def add_point(
        self, 
        point: Point2D, 
        layer: str = dxf_layers.LAYER_CONSTRUCTION,
        dxfattribs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a point entity to the document.
        
        Args:
            point: Point location
            layer: Target layer name
            dxfattribs: Additional DXF attributes
        """
        if self.config.validate_geometry:
            ensure_point_within_bounds(point, self.config)
        
        self._ensure_layer(layer)
        
        attribs = {"layer": layer}
        if dxfattribs:
            attribs.update(dxfattribs)
        
        self.msp.add_point(point.to_tuple(), dxfattribs=attribs)
        self._increment_entities()
    
    def add_points(
        self, 
        points: Iterable[Point2D], 
        layer: str = dxf_layers.LAYER_CONSTRUCTION,
    ) -> None:
        """Add multiple points."""
        for point in points:
            self.add_point(point, layer=layer)
    
    def add_text(
        self,
        text: str,
        position: Point2D,
        height: float = 2.5,
        layer: str = dxf_layers.LAYER_TEXT,
        rotation: float = 0.0,
    ) -> None:
        """
        Add text annotation.
        
        Args:
            text: Text content
            position: Insertion point
            height: Text height in model units
            layer: Target layer
            rotation: Rotation angle in degrees
        """
        if self.config.validate_geometry:
            ensure_point_within_bounds(position, self.config)
        
        self._ensure_layer(layer)
        
        self.msp.add_text(
            text,
            dxfattribs={
                "layer": layer,
                "insert": position.to_tuple(),
                "height": height,
                "rotation": rotation,
            }
        )
        self._increment_entities()
    
    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================
    
    def add_concentric_circles(
        self,
        center: Point2D,
        radii: List[float],
        layer: str = dxf_layers.LAYER_ROSETTE,
    ) -> None:
        """
        Add multiple concentric circles (e.g., for rosette rings).
        
        Args:
            center: Common center point
            radii: List of radii
            layer: Target layer
        """
        for radius in radii:
            self.add_circle(Circle2D(center=center, radius=radius), layer=layer)
    
    def add_ring(
        self,
        center: Point2D,
        inner_radius: float,
        outer_radius: float,
        layer: str = dxf_layers.LAYER_ROSETTE,
    ) -> None:
        """
        Add a ring (two concentric circles).
        
        Args:
            center: Ring center
            inner_radius: Inner circle radius
            outer_radius: Outer circle radius
            layer: Target layer
        """
        self.add_circle(Circle2D(center=center, radius=inner_radius), layer=layer)
        self.add_circle(Circle2D(center=center, radius=outer_radius), layer=layer)
    
    def add_entities(
        self,
        entities: EntityList,
        layer: str = dxf_layers.LAYER_OUTLINE,
    ) -> None:
        """
        Add multiple entities to the document.
        
        Args:
            entities: List of geometry entities
            layer: Target layer for all entities
        """
        for entity in entities:
            if isinstance(entity, Polyline2D):
                self.add_polyline(entity, layer=layer)
            elif isinstance(entity, Circle2D):
                self.add_circle(entity, layer=layer)
            elif isinstance(entity, Arc2D):
                self.add_arc(entity, layer=layer)
            elif isinstance(entity, Line2D):
                self.add_line(entity, layer=layer)
            else:
                raise DxfValidationError(
                    f"Unsupported entity type: {type(entity).__name__}"
                )
    
    # =========================================================================
    # EXPORT METHODS
    # =========================================================================
    
    def to_bytes(self) -> bytes:
        """
        Export document to DXF bytes.
        
        Returns:
            DXF file content as bytes
            
        Raises:
            DxfExportError: If export fails
        """
        try:
            # ezdxf needs a text stream, then encode to bytes
            buffer = StringIO()
            self.doc.write(buffer)
            return buffer.getvalue().encode('utf-8')
        except (OSError, ValueError) as exc:  # WP-1: narrowed from except Exception
            logger.error(f"DXF export to bytes failed: {exc}")
            raise DxfExportError(
                f"Failed to export DXF document: {exc}",
                operation="to_bytes"
            ) from exc
    
    def to_file(self, path: str | Path) -> None:
        """
        Save document to a DXF file.
        
        Args:
            path: Output file path
            
        Raises:
            DxfExportError: If save fails
        """
        try:
            self.doc.saveas(str(path))
            logger.info(f"DXF saved to: {path}")
        except (OSError, ValueError) as exc:  # WP-1: narrowed from except Exception
            logger.error(f"DXF export to file failed: {exc}")
            raise DxfExportError(
                f"Failed to save DXF to '{path}': {exc}",
                operation="to_file"
            ) from exc
    
    # =========================================================================
    # DOCUMENT INFO
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get document statistics.
        
        Returns:
            Dict with entity count, layer count, etc.
        """
        return {
            "entity_count": self._entity_count,
            "layer_count": len(self.doc.layers),
            "layers": self.layers,
            "units": self.config.units,
            "version": self.config.version,
            "max_entities": self.config.max_entities,
        }
