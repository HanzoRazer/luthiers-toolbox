"""
Annotation-Aware DXF Exporter
=============================

DXF exporter that keeps annotations separate from geometry.

Author: The Production Shop
Version: 4.0.0
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

from .base import Annotation

logger = logging.getLogger(__name__)


# Default layer configuration
DEFAULT_LAYER_CONFIG = {
    'DIMENSIONS': {
        'color': 2,       # Yellow
        'lineweight': 25,
        'plot': 0,        # Don't plot by default
        'linetype': 'CONTINUOUS'
    },
    'BODY_OUTLINE': {
        'color': 1,       # Red
        'lineweight': 35,
        'plot': 1
    },
    'PICKGUARD': {
        'color': 3,       # Green
        'lineweight': 25,
        'plot': 1
    },
    'NECK_POCKET': {
        'color': 4,       # Cyan
        'lineweight': 25,
        'plot': 1
    },
    'PICKUP_ROUTE': {
        'color': 5,       # Blue
        'lineweight': 25,
        'plot': 1
    },
    'CONTROL_CAVITY': {
        'color': 6,       # Magenta
        'lineweight': 25,
        'plot': 1
    },
    'BRIDGE_ROUTE': {
        'color': 7,       # White/Black
        'lineweight': 25,
        'plot': 1
    },
    'SOUNDHOLE': {
        'color': 30,      # Orange
        'lineweight': 25,
        'plot': 1
    },
    'ROSETTE': {
        'color': 40,      # Light orange
        'lineweight': 15,
        'plot': 1
    }
}


def check_dxf_compatibility(annotations: List[Annotation], version: str) -> bool:
    """
    Check and warn if annotations will be non-associative.

    Args:
        annotations: List of annotations to export
        version: Target DXF version

    Returns:
        True if associative dimensions supported, False otherwise
    """
    if version == 'R12' and annotations:
        logger.warning(
            "DXF R12 selected but annotations present. "
            "Dimensions will be exported as non-associative lines+text. "
            "Use R2000+ for associative dimensions."
        )
        return False
    return True


class AnnotationAwareExporter:
    """
    DXF exporter that keeps annotations separate from geometry.

    Features:
    - Separate layers for geometry and annotations
    - XDATA storage for annotation metadata
    - R12 compatibility mode
    - Configurable layer properties from shop_config

    Usage:
        exporter = AnnotationAwareExporter()
        exporter.export_with_annotations(
            geometry=extraction_result.contours_by_category,
            annotations=annotations,
            output_path='output.dxf',
            dxf_version='R2000'
        )
    """

    GEOMETRY_LAYERS = [
        'BODY_OUTLINE', 'PICKGUARD', 'NECK_POCKET',
        'PICKUP_ROUTE', 'CONTROL_CAVITY', 'BRIDGE_ROUTE',
        'SOUNDHOLE', 'ROSETTE', 'BRACING', 'F_HOLE', 'D_HOLE'
    ]

    def __init__(
        self,
        annotation_layer: str = "DIMENSIONS",
        config: Optional[Dict[str, Any]] = None,
        confidence_threshold: float = 0.0
    ):
        """
        Initialize exporter.

        Args:
            annotation_layer: Name of annotation layer
            config: Layer configuration from shop_config
            confidence_threshold: Minimum confidence for annotation export
        """
        if not EZDXF_AVAILABLE:
            raise ImportError("ezdxf is required for DXF export")

        self.annotation_layer = annotation_layer
        self.config = config or {}
        self.confidence_threshold = confidence_threshold

    def _get_layer_properties(self, layer_name: str) -> Dict[str, Any]:
        """
        Get layer properties from config or defaults.

        Args:
            layer_name: Name of layer

        Returns:
            Dictionary of layer properties
        """
        # Check config first
        if self.config and 'layers' in self.config:
            if layer_name in self.config['layers']:
                return self.config['layers'][layer_name]

        # Fall back to defaults
        return DEFAULT_LAYER_CONFIG.get(layer_name, {
            'color': 7,
            'lineweight': 25,
            'plot': 1
        })

    def _setup_layers(self, doc: Any) -> None:
        """
        Create all layers with proper properties.

        Args:
            doc: ezdxf document
        """
        # Create geometry layers
        for layer_name in self.GEOMETRY_LAYERS:
            if layer_name not in doc.layers:
                props = self._get_layer_properties(layer_name)
                doc.layers.new(
                    name=layer_name,
                    dxfattribs={
                        'color': props.get('color', 7),
                        'lineweight': props.get('lineweight', 25),
                    }
                )

        # Create annotation layer
        if self.annotation_layer not in doc.layers:
            props = self._get_layer_properties(self.annotation_layer)
            layer = doc.layers.new(
                name=self.annotation_layer,
                dxfattribs={
                    'color': props.get('color', 2),
                    'lineweight': props.get('lineweight', 25),
                }
            )
            # Set plot flag if supported
            if hasattr(layer.dxf, 'plot'):
                layer.dxf.plot = props.get('plot', 0)

    def _export_contour(
        self,
        msp: Any,
        contour: Any,
        layer: str
    ) -> Any:
        """
        Export a single contour as polyline.

        Args:
            msp: ezdxf modelspace
            contour: ContourInfo object
            layer: Target layer name

        Returns:
            Created DXF entity
        """
        # Get points from contour
        if hasattr(contour, 'points'):
            points = contour.points
        elif hasattr(contour, 'contour'):
            # Raw numpy contour
            points = [(p[0][0], p[0][1]) for p in contour.contour]
        else:
            points = list(contour)

        if len(points) < 2:
            return None

        # Create polyline
        polyline = msp.add_lwpolyline(
            points,
            dxfattribs={
                'layer': layer,
                'closed': True
            }
        )

        return polyline

    def export_with_annotations(
        self,
        geometry: Dict[str, List[Any]],
        annotations: List[Annotation],
        output_path: str,
        dxf_version: str = 'R2000'
    ) -> Dict[str, Any]:
        """
        Export geometry and annotations with proper separation.

        Args:
            geometry: Dictionary of category -> contour list
            annotations: List of Annotation objects
            output_path: Output DXF file path
            dxf_version: Target DXF version

        Returns:
            Export statistics dictionary
        """
        # Check compatibility
        check_dxf_compatibility(annotations, dxf_version)

        # Create document
        doc = ezdxf.new(dxf_version)
        msp = doc.modelspace()

        # Setup layers
        self._setup_layers(doc)

        # Statistics
        stats = {
            'geometry_count': 0,
            'annotation_count': 0,
            'filtered_annotations': 0,
            'layers_used': set()
        }

        # First pass: Export geometry, collect handle mapping
        id_to_handle = {}

        for category, contours in geometry.items():
            # Normalize category name to layer
            if hasattr(category, 'value'):
                layer = category.value.upper()
            else:
                layer = str(category).upper()

            if layer not in self.GEOMETRY_LAYERS:
                layer = 'BODY_OUTLINE'  # Default

            for i, contour in enumerate(contours):
                entity = self._export_contour(msp, contour, layer)
                if entity:
                    # Store handle for annotation association
                    feature_id = f"{category.value if hasattr(category, 'value') else category}_{i}"
                    id_to_handle[feature_id] = entity.dxf.handle
                    stats['geometry_count'] += 1
                    stats['layers_used'].add(layer)

        # Second pass: Export annotations with resolved handles
        for annotation in annotations:
            # Filter by confidence
            if annotation.confidence < self.confidence_threshold:
                stats['filtered_annotations'] += 1
                continue

            # Resolve geometry handle
            if annotation.feature_id:
                annotation.associated_geometry = id_to_handle.get(annotation.feature_id)

            # Export annotation
            try:
                annotation.to_dxf_entity(msp, dxf_version)
                stats['annotation_count'] += 1
                stats['layers_used'].add(self.annotation_layer)
            except Exception as e:
                logger.warning(f"Failed to export annotation: {e}")

        # Add informational comment
        layer_list = ', '.join(sorted(stats['layers_used']))
        msp.add_text(
            f"LAYERS: Geometry on various layers | Annotations on {self.annotation_layer}",
            dxfattribs={
                'layer': '0',
                'height': 0.1,
                'insert': (0, -20)
            }
        )

        # Save
        doc.saveas(output_path)

        stats['layers_used'] = list(stats['layers_used'])
        logger.info(
            f"Exported {stats['geometry_count']} geometry entities, "
            f"{stats['annotation_count']} annotations to {output_path}"
        )

        return stats


def split_dimension_layers(dxf_path: str, output_path: Optional[str] = None) -> str:
    """
    Utility to split DIMENSIONS layer into type-specific layers.

    Reads XDATA from annotations and moves them to appropriate layers
    (e.g., DIM_LINEAR_DIMENSION, DIM_RADIAL_DIMENSION).

    Args:
        dxf_path: Input DXF file path
        output_path: Output path (default: input_split.dxf)

    Returns:
        Output file path
    """
    if not EZDXF_AVAILABLE:
        raise ImportError("ezdxf is required")

    doc = ezdxf.readfile(dxf_path)

    for entity in doc.modelspace():
        try:
            xdata = entity.get_xdata('ANNOTATION')
            if xdata and len(xdata) >= 2:
                # Extract annotation type from XDATA
                ann_type = None
                for tag, value in xdata:
                    if tag == 1000 and value not in ('true', ''):
                        ann_type = value
                        break

                if ann_type:
                    new_layer = f"DIM_{ann_type.upper()}"

                    # Create layer if needed
                    if new_layer not in doc.layers:
                        doc.layers.new(new_layer, dxfattribs={'color': 2})

                    # Move entity
                    entity.dxf.layer = new_layer

        except Exception:
            continue  # Skip entities without XDATA

    # Save
    if output_path is None:
        output_path = str(Path(dxf_path).with_suffix('')) + '_split.dxf'

    doc.saveas(output_path)
    logger.info(f"Split dimension layers saved to {output_path}")

    return output_path
