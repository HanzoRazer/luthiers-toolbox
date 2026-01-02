"""
Thickness Map Service

Interprets thickness and stiffness data and couples with geometry
to produce CAM policy constraints and voicing assessment.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ThicknessZone:
    """A zone with thickness-related properties."""
    zone_id: str
    region: str  # e.g., "upper_bout", "waist", "lower_bout"
    target_mm: float
    measured_mm: Optional[float] = None
    tolerance_mm: float = 0.2
    moe_gpa: Optional[float] = None
    ei_ratio: Optional[float] = None  # EI / target_EI
    compliance: str = "unknown"  # pass, warn, fail
    is_voicing_zone: bool = False


@dataclass
class ThicknessMapResult:
    """Result of thickness map analysis."""
    model_id: str
    zone_count: int
    overall_compliance: str  # pass, warn, fail
    zones: List[ThicknessZone] = field(default_factory=list)
    voicing_zones: List[str] = field(default_factory=list)
    thickness_critical_zones: List[str] = field(default_factory=list)
    cam_policy_overrides: List[Dict[str, Any]] = field(default_factory=list)


class ThicknessMapService:
    """
    Service for interpreting thickness and stiffness data.

    This is the INTERPRETATION layer - it takes MOE facts from tap_tone_pi
    and produces voicing assessment and CAM constraints.
    """

    def __init__(self):
        self._cache: Dict[str, ThicknessMapResult] = {}

    def ingest_moe_results(self, model_id: str, moe_results: List[Dict[str, Any]]) -> None:
        """
        Ingest MOE results from tap_tone_pi.

        Each result contains:
          - sample_id, moe_gpa, ei_n_mm2
          - specimen_dimensions
        """
        # Stub: Map MOE measurements to thickness zones
        # - Match sample_ids to zone regions
        # - Compute EI ratios vs. targets
        # - Flag zones needing adjustment
        pass

    def set_target_profile(self, model_id: str, profile: Dict[str, float]) -> None:
        """
        Set target thickness profile.

        profile: {zone_id: target_mm}
        """
        # Stub: Store target profile for compliance checking
        pass

    def analyze(self, model_id: str, geometry: Optional[Any] = None) -> ThicknessMapResult:
        """
        Analyze thickness map and produce interpretation.

        Returns:
          - Zone-by-zone thickness/stiffness status
          - Voicing zone identification
          - Compliance assessment
          - CAM policy overrides
        """
        # Stub: Full analysis
        # - Compare measured vs. target
        # - Identify voicing-critical zones
        # - Flag thickness deviations
        # - Generate CAM constraints for critical zones

        return ThicknessMapResult(
            model_id=model_id,
            zone_count=0,
            overall_compliance="unknown",
            zones=[],
            voicing_zones=[],
            thickness_critical_zones=[],
            cam_policy_overrides=[],
        )

    def get_cam_constraints(self, model_id: str) -> List[Dict[str, Any]]:
        """
        Get CAM policy constraints for thickness-critical zones.

        Returns list of constraint dicts compatible with cam_policy.schema.json.
        """
        result = self._cache.get(model_id)
        if not result:
            return []

        constraints = []

        for zone in result.zones:
            if zone.is_voicing_zone:
                # Voicing zones need precise thickness control
                constraints.append({
                    "region_id": zone.zone_id,
                    "type": "thickness_critical",
                    "constraints": {
                        "stepdown_max_mm": 0.2,
                        "stepover_max_pct": 15,
                        "feed_rate_max_mm_min": 1200,
                    },
                    "reason": f"Voicing zone - target {zone.target_mm}mm ± {zone.tolerance_mm}mm",
                    "source_field": "thickness_map",
                    "priority": 8,
                })

            if zone.compliance == "warn":
                constraints.append({
                    "region_id": zone.zone_id,
                    "type": "thickness_critical",
                    "constraints": {
                        "stepdown_max_mm": 0.15,
                    },
                    "reason": f"Thickness deviation detected - measured {zone.measured_mm}mm vs target {zone.target_mm}mm",
                    "source_field": "thickness_map",
                    "priority": 7,
                })

        return constraints

    def get_voicing_assessment(self, model_id: str) -> Dict[str, Any]:
        """
        Get voicing compliance assessment.

        Returns summary of how well the piece matches target voicing profile.
        """
        result = self._cache.get(model_id)
        if not result:
            return {"status": "no_data"}

        passing = sum(1 for z in result.zones if z.compliance == "pass")
        warning = sum(1 for z in result.zones if z.compliance == "warn")
        failing = sum(1 for z in result.zones if z.compliance == "fail")

        return {
            "model_id": model_id,
            "overall_compliance": result.overall_compliance,
            "zones_pass": passing,
            "zones_warn": warning,
            "zones_fail": failing,
            "voicing_zones": result.voicing_zones,
            "recommendations": self._generate_recommendations(result),
        }

    def _generate_recommendations(self, result: ThicknessMapResult) -> List[str]:
        """Generate voicing recommendations based on analysis."""
        recs = []
        for zone in result.zones:
            if zone.compliance == "fail" and zone.measured_mm and zone.target_mm:
                delta = zone.measured_mm - zone.target_mm
                if delta > 0:
                    recs.append(f"{zone.zone_id}: Remove {abs(delta):.2f}mm to reach target")
                else:
                    recs.append(f"{zone.zone_id}: Already below target by {abs(delta):.2f}mm - STOP")
        return recs
