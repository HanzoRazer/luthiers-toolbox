"""
RMOS CAM Materials Adapter (MM-2)

Applies CAM profiles to material segments for G-code generation.
"""
from __future__ import annotations

from typing import Any, Dict

from ..schemas.strip_family import MaterialSpec
from .cam_profile_registry import infer_profile_for_material


def build_segment_cam_params(
    material: MaterialSpec,
    machine_defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge machine defaults with material-specific CAM profile.
    
    Args:
        material: Material specification from strip family
        machine_defaults: Base machine parameters (spindle_rpm, feed_rate, etc.)
    
    Returns:
        Dictionary of CAM parameters including:
          - cam_profile_id: str
          - spindle_rpm: int
          - feed_rate_mm_min: int
          - plunge_rate_mm_min: int
          - stepdown_mm: float
          - cut_direction: str
          - coolant: str
          - fragility_score: float
    
    machine_defaults can include:
      - spindle_rpm
      - feed_rate_mm_min
      - plunge_rate_mm_min
      - stepdown_mm
      - cut_direction
      - coolant
    """
    prof = infer_profile_for_material(material)
    params = dict(machine_defaults)

    if prof:
        params["cam_profile_id"] = prof.id
        params["spindle_rpm"] = prof.spindle_rpm
        params["feed_rate_mm_min"] = prof.feed_rate_mm_min
        params["plunge_rate_mm_min"] = prof.plunge_rate_mm_min
        params["stepdown_mm"] = prof.stepdown_mm
        params["cut_direction"] = prof.cut_direction
        params["coolant"] = prof.coolant
        params["fragility_score"] = prof.fragility_score
        params["recommended_tool"] = prof.recommended_tool
        params["notes"] = prof.notes
    else:
        # fallback if no profile; leave defaults, but mark unknown
        params.setdefault("cam_profile_id", "unknown")
        params.setdefault("fragility_score", 0.5)

    return params
