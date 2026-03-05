"""
Phase 4.0: Leader Line Association
===================================

This module provides dimension-to-geometry association for blueprint extraction.

Components:
- ArrowDetector: Hybrid arrow/arrowhead detection
- LeaderLineAssociator: Links arrows to dimension text
- DimensionLinker: High-level orchestrator

Usage:
    from phase4 import DimensionLinker

    linker = DimensionLinker()
    linked = linker.process_blueprint(extraction_result)

    for dim in linked.dimensions:
        print(f"{dim.text} -> {dim.target_feature.category}")

Version: 4.0.0-alpha
"""

from .arrow_detector import ArrowDetector, Arrow
from .leader_associator import LeaderLineAssociator, TextRegion
from .dimension_linker import DimensionLinker, LinkedDimensions

__all__ = [
    'ArrowDetector',
    'Arrow',
    'LeaderLineAssociator',
    'TextRegion',
    'DimensionLinker',
    'LinkedDimensions'
]

__version__ = '4.0.0-alpha'
