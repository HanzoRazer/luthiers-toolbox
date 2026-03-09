"""
Dimension Annotation Classes
============================

Linear and Radial dimension implementations for Phase 4.0.

Author: The Production Shop
Version: 4.0.0
"""

import logging
from dataclasses import dataclass, field
from typing import Tuple, Any, Optional, Dict

from .base import Annotation, AnnotationType, AnnotationSource

logger = logging.getLogger(__name__)


@dataclass
class LinearDimension(Annotation):
    """
    Linear dimension between two points.

    Represents a measurement between two points on geometry,
    typically with extension lines and a dimension line.
    """
    point1: Tuple[float, float] = (0, 0)
    point2: Tuple[float, float] = (0, 0)
    extension_line_offset: float = 2.0  # mm
    arrow_size: float = 2.5  # mm
    text_height: float = 2.5  # mm

    def __post_init__(self):
        """Set type and call parent post_init."""
        self.type = AnnotationType.LINEAR_DIMENSION
        super().__post_init__()

        # Calculate value if not provided and points are different
        if self.value is None and self.point1 != self.point2:
            import math
            dx = self.point2[0] - self.point1[0]
            dy = self.point2[1] - self.point1[1]
            self.value = math.sqrt(dx * dx + dy * dy)

    def _create_modern_dimension(self, msp: Any) -> Any:
        """
        Create DXF dimension entity (R13+).

        Uses ezdxf's add_linear_dim for proper associative dimensions.
        """
        try:
            # Calculate dimension line position (offset from points)
            mid_x = (self.point1[0] + self.point2[0]) / 2
            mid_y = (self.point1[1] + self.point2[1]) / 2

            # Use text_position if set, otherwise calculate
            if self.text_position != (0, 0):
                base = self.text_position
            else:
                # Offset perpendicular to dimension line
                base = (mid_x, mid_y + 10)

            dim = msp.add_linear_dim(
                base=base,
                p1=self.point1,
                p2=self.point2,
                dxfattribs={
                    'layer': self.layer,
                }
            )

            # Override dimension text if we have specific text
            if self.text:
                dim.dxf.text = self.text

            # Render the dimension (generates visual representation)
            dim.render()

            # Add XDATA for machine readability
            try:
                dim.set_xdata('ANNOTATION', [
                    (1000, 'true'),
                    (1000, self.type.value),
                    (1040, self.confidence),
                    (1000, self.source.value),
                    (1000, self.feature_id or '')
                ])
            except Exception as e:
                logger.debug(f"Could not set XDATA: {e}")

            return dim

        except Exception as e:
            logger.warning(f"Failed to create modern dimension: {e}")
            return self._create_r12_compatible(msp)

    def _create_r12_compatible(self, msp: Any) -> Any:
        """
        Create R12-compatible representation (separate entities).

        Creates extension lines, dimension line, and text as
        individual entities on the annotation layer.
        """
        entities = []

        # Calculate dimension line Y position
        max_y = max(self.point1[1], self.point2[1])
        dim_y = max_y + 15  # Offset above points

        # Extension line 1 (from point1 up to dimension line)
        ext1 = msp.add_line(
            self.point1,
            (self.point1[0], dim_y + 2),
            dxfattribs={
                'layer': self.layer,
                'linetype': 'CONTINUOUS'
            }
        )
        entities.append(ext1)

        # Extension line 2 (from point2 up to dimension line)
        ext2 = msp.add_line(
            self.point2,
            (self.point2[0], dim_y + 2),
            dxfattribs={
                'layer': self.layer,
                'linetype': 'CONTINUOUS'
            }
        )
        entities.append(ext2)

        # Dimension line (horizontal between extension lines)
        dim_line = msp.add_line(
            (self.point1[0], dim_y),
            (self.point2[0], dim_y),
            dxfattribs={
                'layer': self.layer,
                'linetype': 'CONTINUOUS'
            }
        )
        entities.append(dim_line)

        # Text (centered on dimension line)
        text_x = (self.point1[0] + self.point2[0]) / 2
        text_y = dim_y + 1

        if self.text_position != (0, 0):
            text_x, text_y = self.text_position

        text = msp.add_text(
            self.text or f"{self.value:.2f}" if self.value else "?",
            dxfattribs={
                'layer': self.layer,
                'height': self.text_height,
                'insert': (text_x, text_y)
            }
        )
        entities.append(text)

        return entities

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary with linear-specific fields."""
        base = super().to_dict()
        base['linear'] = {
            'point1': self.point1,
            'point2': self.point2,
            'measured_length': self.value
        }
        return base


@dataclass
class RadialDimension(Annotation):
    """
    Radial dimension for circles and arcs.

    Represents radius or diameter measurement with leader line.
    """
    center: Tuple[float, float] = (0, 0)
    radius: Optional[float] = None
    is_diameter: bool = False  # True for diameter, False for radius
    leader_angle: float = 45.0  # Angle of leader line in degrees
    text_height: float = 2.5  # mm

    def __post_init__(self):
        """Set type and call parent post_init."""
        self.type = AnnotationType.RADIAL_DIMENSION
        super().__post_init__()

        # Set value from radius if not provided
        if self.value is None and self.radius is not None:
            self.value = self.radius * 2 if self.is_diameter else self.radius

    def _create_modern_dimension(self, msp: Any) -> Any:
        """
        Create DXF radial dimension entity (R13+).
        """
        try:
            import math

            # Calculate point on circle for dimension
            angle_rad = math.radians(self.leader_angle)
            radius = self.radius or (self.value / 2 if self.is_diameter else self.value) or 10

            point_on_circle = (
                self.center[0] + radius * math.cos(angle_rad),
                self.center[1] + radius * math.sin(angle_rad)
            )

            if self.is_diameter:
                # Diameter dimension
                dim = msp.add_diameter_dim(
                    center=self.center,
                    mpoint=point_on_circle,
                    dxfattribs={'layer': self.layer}
                )
            else:
                # Radius dimension
                dim = msp.add_radius_dim(
                    center=self.center,
                    mpoint=point_on_circle,
                    dxfattribs={'layer': self.layer}
                )

            if self.text:
                dim.dxf.text = self.text

            dim.render()

            # Add XDATA
            try:
                dim.set_xdata('ANNOTATION', [
                    (1000, 'true'),
                    (1000, self.type.value),
                    (1040, self.confidence),
                    (1000, self.source.value),
                    (1000, self.feature_id or '')
                ])
            except Exception as e:
                logger.debug(f"Could not set XDATA: {e}")

            return dim

        except Exception as e:
            logger.warning(f"Failed to create modern radial dimension: {e}")
            return self._create_r12_compatible(msp)

    def _create_r12_compatible(self, msp: Any) -> Any:
        """
        Create R12-compatible radial dimension.

        Creates a leader line from center to edge with text.
        """
        import math
        entities = []

        angle_rad = math.radians(self.leader_angle)
        radius = self.radius or (self.value / 2 if self.is_diameter else self.value) or 10

        # Point on circle
        edge_point = (
            self.center[0] + radius * math.cos(angle_rad),
            self.center[1] + radius * math.sin(angle_rad)
        )

        # Extended point for text
        text_distance = radius + 10
        text_point = (
            self.center[0] + text_distance * math.cos(angle_rad),
            self.center[1] + text_distance * math.sin(angle_rad)
        )

        # Leader line from center to edge
        if self.is_diameter:
            # For diameter, draw through center
            opposite_point = (
                self.center[0] - radius * math.cos(angle_rad),
                self.center[1] - radius * math.sin(angle_rad)
            )
            line = msp.add_line(
                opposite_point,
                edge_point,
                dxfattribs={'layer': self.layer}
            )
        else:
            # For radius, draw from center to edge
            line = msp.add_line(
                self.center,
                edge_point,
                dxfattribs={'layer': self.layer}
            )
        entities.append(line)

        # Extension to text
        ext_line = msp.add_line(
            edge_point,
            text_point,
            dxfattribs={'layer': self.layer}
        )
        entities.append(ext_line)

        # Text
        prefix = "D" if self.is_diameter else "R"
        display_text = self.text or f"{prefix}{self.value:.2f}" if self.value else f"{prefix}?"

        text = msp.add_text(
            display_text,
            dxfattribs={
                'layer': self.layer,
                'height': self.text_height,
                'insert': text_point
            }
        )
        entities.append(text)

        return entities

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary with radial-specific fields."""
        base = super().to_dict()
        base['radial'] = {
            'center': self.center,
            'radius': self.radius,
            'is_diameter': self.is_diameter,
            'measured_value': self.value
        }
        return base
