"""
Annotation Base Classes
=======================

Base classes for all annotation types.

Author: Luthier's Toolbox
Version: 4.0.0
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class AnnotationType(Enum):
    """Types of annotations that should stay separate from geometry."""
    LINEAR_DIMENSION = "linear_dimension"
    RADIAL_DIMENSION = "radial_dimension"
    ANGULAR_DIMENSION = "angular_dimension"
    LEADER_NOTE = "leader_note"
    DATUM_FEATURE = "datum_feature"
    GEOMETRIC_TOLERANCE = "geometric_tolerance"
    SURFACE_FINISH = "surface_finish"
    WELD_SYMBOL = "weld_symbol"
    DATUM_TARGET = "datum_target"


class AnnotationSource(Enum):
    """Source of annotation detection."""
    OCR = "ocr"              # Direct from text recognition
    ARROW = "arrow"          # Found via leader lines
    WITNESS = "witness"      # From witness line detection
    INFERRED = "inferred"    # Calculated from geometry
    TEMPLATE = "template"    # Matched from instrument profile
    MANUAL = "manual"        # User-entered
    HYBRID = "hybrid"        # Combined from multiple sources


@dataclass
class Annotation:
    """
    Base class for all annotations.

    Annotations are metadata that describe geometry but should not be
    treated as geometry themselves. They export to separate DXF layers
    and can be toggled independently.
    """
    # Note: type has default None to allow subclasses to auto-set in __post_init__
    text: str = ""
    type: AnnotationType = None  # Set by subclasses in __post_init__
    value: Optional[float] = None
    unit: str = "mm"
    confidence: float = 1.0
    layer: str = "DIMENSIONS"

    # Association with geometry
    feature_id: Optional[str] = None  # e.g., "body_outline_0", "pickup_route_2"
    associated_geometry: Optional[str] = None  # DXF entity handle (resolved during export)
    leader_points: List[Tuple[float, float]] = field(default_factory=list)

    # Position in DXF (for placement)
    text_position: Tuple[float, float] = (0, 0)
    dimension_line_position: Optional[Tuple[float, float]] = None

    # Source tracking
    source: AnnotationSource = AnnotationSource.OCR
    source_details: Dict[str, float] = field(default_factory=dict)
    original_raw_text: str = ""

    def __post_init__(self):
        """Initialize source details for hybrid annotations."""
        if self.source == AnnotationSource.HYBRID and not self.source_details:
            self.source_details = {
                'ocr_confidence': 0.0,
                'arrow_confidence': 0.0,
                'witness_confidence': 0.0,
                'combined_confidence': self.confidence
            }

    def resolve_handle(self, id_to_handle: Dict[str, str]) -> Optional[str]:
        """
        Map internal feature ID to DXF handle during export.

        Args:
            id_to_handle: Mapping of feature IDs to DXF handles

        Returns:
            DXF entity handle or None
        """
        if self.feature_id:
            self.associated_geometry = id_to_handle.get(self.feature_id)
        return self.associated_geometry

    def to_dxf_entity(self, msp: Any, dxf_version: str = 'R12') -> Any:
        """
        Convert to appropriate DXF entity based on version.

        Args:
            msp: ezdxf modelspace
            dxf_version: Target DXF version string

        Returns:
            Created DXF entity
        """
        if dxf_version >= 'R13':
            return self._create_modern_dimension(msp)
        else:
            return self._create_r12_compatible(msp)

    def _create_modern_dimension(self, msp: Any) -> Any:
        """Create DXF dimension entity (R13+). Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _create_modern_dimension")

    def _create_r12_compatible(self, msp: Any) -> Any:
        """Create R12-compatible representation. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _create_r12_compatible")

    def to_dict(self) -> Dict[str, Any]:
        """Export annotation as dictionary."""
        return {
            'type': self.type.value,
            'text': self.text,
            'value': self.value,
            'unit': self.unit,
            'confidence': self.confidence,
            'feature_id': self.feature_id,
            'source': self.source.value,
            'position': {
                'text': self.text_position,
                'leaders': self.leader_points
            }
        }
