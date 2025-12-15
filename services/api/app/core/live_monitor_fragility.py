"""
RMOS Live Monitor Fragility Context (MM-6)

Extracts material and fragility information from job metadata for real-time visibility
in the Live Monitor. Integrates with MM-0 (materials), MM-2 (CAM profiles), and
MM-4/MM-5 (analytics/policy) to surface fragility context as jobs run.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict


FragilityBand = Literal["stable", "medium", "fragile", "unknown"]


class FragilityContext(TypedDict, total=False):
    """Fragility and material context for Live Monitor events."""
    materials: List[str]
    worst_fragility_score: float | None
    fragility_band: FragilityBand
    lane_hint: str | None


def _classify_fragility(score: float | None) -> FragilityBand:
    """
    Classify fragility score into human-readable band.
    
    Bands:
    - stable: <0.4 (solid wood, MDF, resin)
    - medium: 0.4-0.69 (plywood, charred wood, paper)
    - fragile: ≥0.7 (shell, metal inlay)
    - unknown: None or invalid
    
    Args:
        score: Worst fragility score (0.0-1.0) or None
    
    Returns:
        FragilityBand enum value
    """
    if score is None:
        return "unknown"
    if score < 0.4:
        return "stable"
    if score < 0.7:
        return "medium"
    return "fragile"


def build_fragility_context_for_job(entry: Dict[str, Any]) -> FragilityContext:
    """
    Extract fragility and material info from a joblog entry for Live Monitor display.
    
    Expected job metadata structure (from MM-2/MM-4):
        {
            "metadata": {
                "cam_profile_summary": {
                    "worst_fragility_score": 0.85,
                    "dominant_lane_hint": "tuned_v1"  # optional
                },
                "materials": [
                    {"type": "wood", "thickness_mm": 2.0},
                    {"type": "shell", "thickness_mm": 1.2}
                ],
                "lane_hint": "experimental"  # fallback
            }
        }
    
    Args:
        entry: Job log entry dict with metadata
    
    Returns:
        FragilityContext dict with:
        - materials: List of material types (e.g., ["wood", "shell"])
        - worst_fragility_score: Float 0.0-1.0 or None
        - fragility_band: "stable", "medium", "fragile", or "unknown"
        - lane_hint: Suggested quality lane or None
    
    Example:
        entry = {
            "id": "job_123",
            "metadata": {
                "cam_profile_summary": {"worst_fragility_score": 0.85},
                "materials": [{"type": "shell"}, {"type": "copper"}]
            }
        }
        
        ctx = build_fragility_context_for_job(entry)
        # ctx = {
        #     "materials": ["shell", "copper"],
        #     "worst_fragility_score": 0.85,
        #     "fragility_band": "fragile",
        #     "lane_hint": None
        # }
    """
    meta = entry.get("metadata") or {}
    cam_summary = meta.get("cam_profile_summary") or {}
    materials_meta = meta.get("materials") or []

    # Extract fragility score
    worst_fragility = cam_summary.get("worst_fragility_score")
    if not isinstance(worst_fragility, (int, float)):
        worst_fragility = None

    # Extract lane hint (prefer cam_profile_summary, fallback to root metadata)
    lane_hint = cam_summary.get("dominant_lane_hint") or meta.get("lane_hint")

    # Collect unique material types
    material_types: List[str] = []
    for m in materials_meta:
        m_type = (m.get("type") or "unknown").lower()
        if m_type and m_type not in material_types:
            material_types.append(m_type)

    # Classify fragility into band
    band = _classify_fragility(worst_fragility)

    ctx: FragilityContext = {
        "materials": material_types,
        "worst_fragility_score": worst_fragility,
        "fragility_band": band,
        "lane_hint": lane_hint,
    }
    return ctx
