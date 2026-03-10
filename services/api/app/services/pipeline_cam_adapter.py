"""
Pipeline Result to CAM Adapter
==============================

Bridges Phase 4 PipelineResult to CAM-ready format by extracting
geometry loops and applying dimension-based parameters.

Resolves: VEC-GAP-03 (Phase 4 PipelineResult has no consumer)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CamReadySpec:
    """CAM-ready specification from pipeline result."""
    
    loops: List[List[Tuple[float, float]]] = field(default_factory=list)
    islands: List[List[Tuple[float, float]]] = field(default_factory=list)
    body_width_mm: float = 0.0
    body_height_mm: float = 0.0
    pocket_depths: Dict[str, float] = field(default_factory=dict)
    suggested_tool_d_mm: float = 6.35
    suggested_stepdown_mm: float = 2.0
    suggested_feed_xy: float = 1200.0
    source_file: str = ""
    association_rate: float = 0.0
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "geometry": {
                "loops": self.loops,
                "islands": self.islands,
                "loop_count": len(self.loops),
                "island_count": len(self.islands),
            },
            "dimensions": {
                "body_width_mm": self.body_width_mm,
                "body_height_mm": self.body_height_mm,
                "pocket_depths": self.pocket_depths,
            },
            "suggested_params": {
                "tool_d_mm": self.suggested_tool_d_mm,
                "stepdown_mm": self.suggested_stepdown_mm,
                "feed_xy": self.suggested_feed_xy,
            },
            "metadata": {
                "source_file": self.source_file,
                "association_rate": self.association_rate,
            },
            "warnings": self.warnings,
        }


def _suggest_tool_params(body_width: float, pocket_depths: Dict[str, float]) -> Tuple[float, float, float]:
    """Suggest CAM parameters based on dimensions."""
    if body_width < 200:
        tool_d = 3.175
    elif body_width < 400:
        tool_d = 6.35
    else:
        tool_d = 12.7
    
    max_depth = max(pocket_depths.values()) if pocket_depths else 20.0
    stepdown = min(tool_d / 2, max_depth / 4, 3.0)
    feed_xy = 800 if body_width < 300 else 1200
    
    return tool_d, stepdown, feed_xy


def adapt_pipeline_to_cam(pipeline_result: Any) -> CamReadySpec:
    """Convert Phase 4 PipelineResult to CAM-ready specification."""
    spec = CamReadySpec()
    
    if pipeline_result is None:
        spec.warnings.append("No pipeline result provided")
        return spec
    
    spec.source_file = getattr(pipeline_result, 'source_file', '')
    spec.association_rate = getattr(pipeline_result, 'association_rate', 0.0)
    
    dims = getattr(pipeline_result, 'dimensions_mm', (0.0, 0.0))
    if isinstance(dims, (list, tuple)) and len(dims) >= 2:
        spec.body_width_mm = float(dims[0])
        spec.body_height_mm = float(dims[1])
    
    linked_dims = getattr(pipeline_result, 'linked_dimensions', None)
    if linked_dims:
        for dim in getattr(linked_dims, 'dimensions', []):
            target = getattr(dim, 'target_feature', None)
            if target and hasattr(dim, 'text_region'):
                text_region = dim.text_region
                value = getattr(text_region, 'value_mm', None)
                category = getattr(target, 'category', 'unknown')
                if value and 'depth' in category.lower():
                    spec.pocket_depths[category] = value
    
    tool_d, stepdown, feed_xy = _suggest_tool_params(spec.body_width_mm, spec.pocket_depths)
    spec.suggested_tool_d_mm = tool_d
    spec.suggested_stepdown_mm = stepdown
    spec.suggested_feed_xy = feed_xy
    
    if not spec.loops:
        spec.warnings.append("No geometry loops - use DXF import for CAM")
    
    if spec.association_rate < 0.5:
        spec.warnings.append(f"Low association rate ({spec.association_rate:.0%})")
    
    return spec


def adapt_dict_to_cam(result_dict: Dict[str, Any]) -> CamReadySpec:
    """Convert dictionary (from PipelineResult.to_dict()) to CAM spec."""
    spec = CamReadySpec()
    
    spec.source_file = result_dict.get('source_file', '')
    
    extraction = result_dict.get('extraction', {})
    dims = extraction.get('dimensions_mm', (0.0, 0.0))
    if isinstance(dims, (list, tuple)) and len(dims) >= 2:
        spec.body_width_mm = float(dims[0])
        spec.body_height_mm = float(dims[1])
    
    linking = result_dict.get('linking', {})
    spec.association_rate = linking.get('association_rate', 0.0)
    
    tool_d, stepdown, feed_xy = _suggest_tool_params(spec.body_width_mm, spec.pocket_depths)
    spec.suggested_tool_d_mm = tool_d
    spec.suggested_stepdown_mm = stepdown
    spec.suggested_feed_xy = feed_xy
    
    return spec
