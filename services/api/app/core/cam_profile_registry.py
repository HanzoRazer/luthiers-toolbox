"""
CAM Profile Registry (MM-2)

Manages CAM profiles for mixed-material rosette manufacturing.
Provides profile lookup, inference, and summary statistics.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas.cam_profile import CamProfile, MaterialType
from ..schemas.strip_family import MaterialSpec


DEFAULT_CAM_PROFILES_PATH = Path(os.getcwd()) / "data" / "rmos" / "cam_profiles.json"


@lru_cache()
def _load_profiles_raw(path: Path = DEFAULT_CAM_PROFILES_PATH) -> List[CamProfile]:
    """Load CAM profiles from JSON file with validation."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    out: List[CamProfile] = []
    for item in data:
        try:
            out.append(CamProfile(**item))
        except (ValueError, TypeError):  # WP-1: narrowed from except Exception
            # In production: log invalid entries.
            continue
    return out


@lru_cache()
def _profiles_by_id() -> Dict[str, CamProfile]:
    """Build ID-based lookup dictionary."""
    return {p.id: p for p in _load_profiles_raw()}


def get_cam_profile(profile_id: str) -> Optional[CamProfile]:
    """Get CAM profile by ID."""
    return _profiles_by_id().get(profile_id)


def _default_profile_for_type(material_type: MaterialType) -> Optional[CamProfile]:
    """
    Get default CAM profile for a material type.
    Prefers hard-coded favorites, falls back to first match.
    """
    profiles = _load_profiles_raw()
    # Hard-coded favorites:
    favorites = {
        "wood": "wood_standard",
        "metal": "metal_inlay",
        "shell": "shell_inlay",
        "paper": "paper_marquetry",
        "charred": "charred_wood",
        "resin": "resin_infill",
    }
    fav_id = favorites.get(material_type)
    if fav_id:
        p = get_cam_profile(fav_id)
        if p:
            return p

    for p in profiles:
        if p.material_type == material_type:
            return p
    return None


def infer_profile_for_material(material: MaterialSpec) -> Optional[CamProfile]:
    """
    Infer CAM profile for a material.
    Uses explicit cam_profile if set, otherwise infers from material.type.
    """
    if material.cam_profile:
        p = get_cam_profile(material.cam_profile)
        if p:
            return p

    mtype = material.type  # type: ignore[assignment]
    return _default_profile_for_type(mtype)


def summarize_profiles_for_family(family: dict) -> dict:
    """
    Compute CAM profile summary for a strip family.
    
    Returns:
        {
            "profile_ids": [str],
            "min_feed_rate_mm_min": int,
            "max_feed_rate_mm_min": int,
            "worst_fragility_score": float,
            "dominant_lane_hint": str
        }
    """
    materials = family.get("materials") or []
    profile_ids = set()
    min_feed = None
    max_feed = None
    worst_fragility = 0.0
    lane_hints: Dict[str, int] = {}

    for m in materials:
        spec = MaterialSpec(**m)
        prof = infer_profile_for_material(spec)
        if not prof:
            continue
        profile_ids.add(prof.id)
        min_feed = prof.feed_rate_mm_min if min_feed is None else min(min_feed, prof.feed_rate_mm_min)
        max_feed = prof.feed_rate_mm_min if max_feed is None else max(max_feed, prof.feed_rate_mm_min)
        if prof.fragility_score > worst_fragility:
            worst_fragility = prof.fragility_score
        if prof.priority_lane_hint:
            lane_hints[prof.priority_lane_hint] = lane_hints.get(prof.priority_lane_hint, 0) + 1

    dominant_lane_hint = None
    if lane_hints:
        dominant_lane_hint = max(lane_hints.items(), key=lambda kv: kv[1])[0]

    return {
        "profile_ids": sorted(profile_ids),
        "min_feed_rate_mm_min": min_feed,
        "max_feed_rate_mm_min": max_feed,
        "worst_fragility_score": worst_fragility,
        "dominant_lane_hint": dominant_lane_hint,
    }
