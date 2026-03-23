"""RMOS CAM Materials - Stub module.

Provides build_segment_cam_params for rmos_gcode_materials.py compatibility.
"""
from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas.strip_family import MaterialSpec


def build_segment_cam_params(
    material_spec: "MaterialSpec",
    machine_defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """Build CAM parameters for a material segment.

    Args:
        material_spec: Material specification
        machine_defaults: Default machine parameters

    Returns:
        CAM parameters dict with feed_rate_mm_min, spindle_rpm, etc.
    """
    # Start with machine defaults
    params = dict(machine_defaults)

    # Get material properties
    mat_type = getattr(material_spec, 'type', 'wood')
    species = getattr(material_spec, 'species', None)
    hardness = getattr(material_spec, 'hardness', 'medium')

    # Default CAM profile
    params.setdefault('cam_profile_id', f'{mat_type}_{hardness}')
    params.setdefault('feed_rate_mm_min', 1000)
    params.setdefault('spindle_rpm', 18000)
    params.setdefault('fragility_score', 0.3 if hardness == 'soft' else 0.5)

    # Add notes
    if species:
        params['notes'] = f'Material: {species} ({mat_type})'

    return params


def summarize_profiles_for_family(strip_family: dict) -> Dict[str, Any]:
    """Get CAM summary for a strip family.

    Args:
        strip_family: Strip family dict with materials list

    Returns:
        Summary with profile_ids, average_feed, fragility range
    """
    materials = strip_family.get('materials', [])

    if not materials:
        return {
            'profile_ids': [],
            'avg_feed_rate_mm_min': 1000,
            'fragility_range': [0.3, 0.5],
            'lane_hint': 'standard'
        }

    profile_ids = []
    for mat in materials:
        mat_type = mat.get('type', 'wood')
        hardness = mat.get('hardness', 'medium')
        profile_ids.append(f'{mat_type}_{hardness}')

    return {
        'profile_ids': profile_ids,
        'avg_feed_rate_mm_min': 1000,
        'fragility_range': [0.3, 0.7],
        'lane_hint': 'mixed' if len(set(profile_ids)) > 1 else 'standard'
    }
