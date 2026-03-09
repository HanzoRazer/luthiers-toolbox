"""
Annotation Layer Management for DXF Export
==========================================

Ensures dimensions remain as metadata, not geometry.

Sprint 1 (Phase 4.0): LinearDimension, RadialDimension
Sprint 2 (Phase 4.1): AngularDimension, LeaderNote
Sprint 3 (Phase 4.2): DatumFeature, GeometricTolerance
Future: SurfaceFinish, WeldSymbol, DatumTarget

Author: The Production Shop
Version: 4.0.0
"""

from .base import Annotation, AnnotationType, AnnotationSource
from .dimensions import LinearDimension, RadialDimension
from .exporter import AnnotationAwareExporter, check_dxf_compatibility
from .json_exporter import AnnotationJSONExporter

__all__ = [
    'Annotation',
    'AnnotationType',
    'AnnotationSource',
    'LinearDimension',
    'RadialDimension',
    'AnnotationAwareExporter',
    'AnnotationJSONExporter',
    'check_dxf_compatibility'
]

__version__ = '4.0.0'
