"""
Grid Zone Classifier
====================

Zone-based contour classification using the STEM Guitar body grid system.

The grid defines semantic regions that map to contour categories:
- Brown zone: Neck pocket
- Cream zones: Upper bout wings
- Blue zones: Wing boundaries (max body width)
- White zone: Main body canvas
- Gray zone: Bridge placement area
- Centerline: Symmetry axis

Author: Luthier's Toolbox
Version: 4.0.0
"""

from .zones import GridZone, GridZoneType, ELECTRIC_GUITAR_GRID
from .classifier import GridZoneClassifier, ZoneClassificationResult

__all__ = [
    'GridZone',
    'GridZoneType',
    'GridZoneClassifier',
    'ZoneClassificationResult',
    'ELECTRIC_GUITAR_GRID'
]

__version__ = '4.0.0'
