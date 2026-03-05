"""
Phase 4.0: Leader Line Association
===================================

This module provides dimension-to-geometry association for blueprint extraction.

Components:
- ArrowDetector: Hybrid arrow/arrowhead detection
- LeaderLineAssociator: Links arrows to dimension text
- DimensionLinker: High-level orchestrator
- BlueprintPipeline: End-to-end processing pipeline

Usage:
    from phase4 import BlueprintPipeline

    pipeline = BlueprintPipeline()
    result = pipeline.process("blueprint.pdf")

    for dim in result.linked_dimensions.dimensions:
        print(f"{dim.text_region.text} -> {dim.target_feature.category}")

Version: 4.0.0
"""

from .arrow_detector import ArrowDetector, Arrow, ArrowOrientation
from .leader_associator import LeaderLineAssociator, TextRegion, AssociatedDimension
from .dimension_linker import DimensionLinker, LinkedDimensions, link_blueprint_dimensions
from .pipeline import BlueprintPipeline, PipelineResult, process_blueprint

__all__ = [
    # Arrow detection
    'ArrowDetector',
    'Arrow',
    'ArrowOrientation',
    # Leader association
    'LeaderLineAssociator',
    'TextRegion',
    'AssociatedDimension',
    # Dimension linking
    'DimensionLinker',
    'LinkedDimensions',
    'link_blueprint_dimensions',
    # Pipeline
    'BlueprintPipeline',
    'PipelineResult',
    'process_blueprint',
]

__version__ = '4.0.0'
