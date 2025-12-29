"""
Grain Field Service

Interprets grain measurement data and couples with geometry
to produce CAM policy constraints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class GrainZone:
    """A zone with grain-related properties."""
    zone_id: str
    grain_angle_deg: float
    confidence: float
    runout_detected: bool = False
    checking_risk: bool = False
    cam_constraint: Optional[str] = None  # e.g., "climb_only", "reduce_feed"


@dataclass
class GrainFieldResult:
    """Result of grain field analysis."""
    model_id: str
    coverage_pct: float
    mean_confidence: float
    zones: List[GrainZone] = field(default_factory=list)
    runout_zones: List[str] = field(default_factory=list)
    checking_zones: List[str] = field(default_factory=list)
    cam_policy_overrides: List[Dict[str, Any]] = field(default_factory=list)


class GrainFieldService:
    """
    Service for interpreting grain measurement data.

    This is the INTERPRETATION layer - it takes facts from tap_tone_pi
    and produces design/manufacturing guidance.
    """

    def __init__(self):
        self._cache: Dict[str, GrainFieldResult] = {}

    def ingest_tap_peaks(self, model_id: str, tap_peaks: Dict[str, Any]) -> None:
        """
        Ingest tap_peaks.json from tap_tone_pi.

        The frequency patterns can indicate grain orientation and uniformity.
        Higher-order modes may reveal grain angle variations.
        """
        # Stub: Extract grain-relevant features from peak patterns
        # - Peak frequency ratios → grain stiffness anisotropy
        # - Peak sharpness → grain uniformity
        # - Mode shapes → grain angle
        pass

    def ingest_external_map(self, model_id: str, grain_map: Dict[str, Any], manifest: Dict[str, Any]) -> None:
        """
        Ingest external grain map with provenance.

        Expects:
          - grain_map: {zone_id: {angle_deg, confidence, ...}}
          - manifest: provenance metadata from tap_tone_pi
        """
        # Stub: Validate provenance, store grain data
        pass

    def analyze(self, model_id: str, geometry: Optional[Any] = None) -> GrainFieldResult:
        """
        Analyze grain field and produce interpretation.

        Returns:
          - Zone-by-zone grain properties
          - Runout and checking risk areas
          - CAM policy override suggestions
        """
        # Stub: Combine ingested data with geometry
        # - Map grain zones to mesh faces
        # - Detect runout (grain angle deviation > threshold)
        # - Identify checking risk (end-grain exposure)
        # - Generate CAM policy overrides

        return GrainFieldResult(
            model_id=model_id,
            coverage_pct=0.0,
            mean_confidence=0.0,
            zones=[],
            runout_zones=[],
            checking_zones=[],
            cam_policy_overrides=[],
        )

    def get_cam_constraints(self, model_id: str) -> List[Dict[str, Any]]:
        """
        Get CAM policy constraints for grain-sensitive zones.

        Returns list of constraint dicts compatible with cam_policy.schema.json.
        """
        result = self._cache.get(model_id)
        if not result:
            return []

        constraints = []
        for zone in result.zones:
            if zone.runout_detected:
                constraints.append({
                    "region_id": zone.zone_id,
                    "type": "grain_sensitive",
                    "constraints": {
                        "feed_rate_max_mm_min": 1500,  # Reduced feed
                        "cut_direction": "climb",
                    },
                    "reason": f"Grain runout detected (angle: {zone.grain_angle_deg}°)",
                    "source_field": "grain_field",
                    "priority": 7,
                })
            if zone.checking_risk:
                constraints.append({
                    "region_id": f"{zone.zone_id}_checking",
                    "type": "grain_sensitive",
                    "constraints": {
                        "stepdown_max_mm": 0.5,
                        "feed_rate_max_mm_min": 1000,
                    },
                    "reason": "Checking risk - reduce aggression",
                    "source_field": "grain_field",
                    "priority": 8,
                })

        return constraints
