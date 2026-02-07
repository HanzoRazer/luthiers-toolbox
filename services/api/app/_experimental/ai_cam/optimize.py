"""
Toolpath Optimization Engine (Wave 11)

Goal:
Take an operation proposal (feed/rpm/doc/woc) and recommend parameters
that maximize:
- tool life
- surface finish
- efficiency
- safety

Wave 11 seeds the structure; later waves will supply real optimization math.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Import Calculator Spine service
try:
    from ..calculators.service import (
        CutOperationSpec,
        evaluate_cut_operation,
    )
    CALCULATOR_AVAILABLE = True
except ImportError:
    CALCULATOR_AVAILABLE = False
    CutOperationSpec = None


@dataclass
class OptimizationCandidate:
    """A candidate parameter set with its physics evaluation."""
    feed_mm_min: float
    rpm: float
    depth_of_cut_mm: float
    width_of_cut_mm: Optional[float]
    score: float
    physics: Dict[str, Any]
    notes: List[str]


class CAMOptimizer:
    """
    Explores small variations in parameters to find improved physics outcomes.
    """

    def __init__(self, search_pct: float = 0.10):
        """
        Initialize optimizer.
        
        Args:
            search_pct: Percentage variation to explore (0.10 = ±10%)
        """
        self.search_pct = search_pct

    def search(
        self,
        tool_id: str,
        material_id: str,
        tool_kind: str,
        feed_mm_min: float,
        rpm: float,
        depth_of_cut_mm: float,
        width_of_cut_mm: Optional[float] = None,
        machine_id: Optional[str] = None,
    ) -> List[OptimizationCandidate]:
        """
        Search for improved parameter combinations.
        
        Explores ±search_pct variations in feed and RPM to find
        combinations with better physics outcomes.
        
        Args:
            tool_id: Tool identifier
            material_id: Material identifier
            tool_kind: "router_bit" or "saw_blade"
            feed_mm_min: Base feed rate
            rpm: Base spindle speed
            depth_of_cut_mm: Depth of cut
            width_of_cut_mm: Width of cut (optional)
            machine_id: Machine profile ID (optional)
        
        Returns:
            List of OptimizationCandidate sorted by score (best first)
        """
        if not CALCULATOR_AVAILABLE:
            return [
                OptimizationCandidate(
                    feed_mm_min=feed_mm_min,
                    rpm=rpm,
                    depth_of_cut_mm=depth_of_cut_mm,
                    width_of_cut_mm=width_of_cut_mm,
                    score=0.0,
                    physics={},
                    notes=["Calculator Spine not available — optimization disabled"],
                )
            ]

        candidates: List[OptimizationCandidate] = []
        
        # Generate variations
        feed_vals = [
            feed_mm_min * (1 - self.search_pct),
            feed_mm_min,
            feed_mm_min * (1 + self.search_pct),
        ]

        rpm_vals = [
            rpm * (1 - self.search_pct),
            rpm,
            rpm * (1 + self.search_pct),
        ]

        for f in feed_vals:
            for r in rpm_vals:
                try:
                    spec = CutOperationSpec(
                        tool_id=tool_id,
                        material_id=material_id,
                        tool_kind=tool_kind,
                        feed_mm_min=f,
                        rpm=r,
                        depth_of_cut_mm=depth_of_cut_mm,
                        width_of_cut_mm=width_of_cut_mm,
                        machine_id=machine_id,
                    )
                    result = evaluate_cut_operation(spec)
                    physics = result.as_dict() if hasattr(result, 'as_dict') else {}
                    
                    # Score the candidate
                    score, notes = self._score_physics(physics, f, r, feed_mm_min, rpm)
                    
                    candidates.append(
                        OptimizationCandidate(
                            feed_mm_min=round(f, 1),
                            rpm=round(r, 0),
                            depth_of_cut_mm=depth_of_cut_mm,
                            width_of_cut_mm=width_of_cut_mm,
                            score=score,
                            physics=physics,
                            notes=notes,
                        )
                    )
                except Exception as e:  # WP-1: keep broad — calculator spine can raise anything
                    candidates.append(
                        OptimizationCandidate(
                            feed_mm_min=round(f, 1),
                            rpm=round(r, 0),
                            depth_of_cut_mm=depth_of_cut_mm,
                            width_of_cut_mm=width_of_cut_mm,
                            score=-1000.0,
                            physics={},
                            notes=[f"Evaluation error: {str(e)}"],
                        )
                    )

        # Sort by score (highest first)
        candidates.sort(key=lambda c: c.score, reverse=True)
        
        return candidates

    def _score_physics(
        self,
        physics: Dict[str, Any],
        feed: float,
        rpm: float,
        base_feed: float,
        base_rpm: float,
    ) -> Tuple[float, List[str]]:
        """
        Score physics results for optimization ranking.
        
        Higher score = better.
        
        Returns:
            Tuple of (score, notes)
        """
        score = 100.0  # Start with perfect score
        notes: List[str] = []

        # Chipload scoring
        chipload = physics.get("chipload", {})
        if chipload:
            if chipload.get("in_range", True):
                notes.append("✓ Chipload in range")
            else:
                score -= 30
                notes.append("✗ Chipload out of range")

        # Heat scoring
        heat = physics.get("heat", {})
        if heat:
            category = heat.get("category", "UNKNOWN")
            if category == "COLD":
                notes.append("✓ Heat: COLD (optimal)")
            elif category == "WARM":
                score -= 10
                notes.append("~ Heat: WARM (acceptable)")
            elif category == "HOT":
                score -= 40
                notes.append("✗ Heat: HOT (dangerous)")

        # Deflection scoring
        deflection = physics.get("deflection", {})
        if deflection:
            risk = deflection.get("risk", "UNKNOWN")
            if risk == "GREEN":
                notes.append("✓ Deflection: GREEN (safe)")
            elif risk == "YELLOW":
                score -= 15
                notes.append("~ Deflection: YELLOW (caution)")
            elif risk == "RED":
                score -= 50
                notes.append("✗ Deflection: RED (unsafe)")

        # Kickback scoring (for saw operations)
        kickback = physics.get("kickback", {})
        if kickback:
            category = kickback.get("category", "UNKNOWN")
            if category == "LOW":
                notes.append("✓ Kickback: LOW")
            elif category == "MEDIUM":
                score -= 20
                notes.append("~ Kickback: MEDIUM")
            elif category == "HIGH":
                score -= 60
                notes.append("✗ Kickback: HIGH")

        # Prefer minimal deviation from base parameters
        feed_deviation = abs(feed - base_feed) / base_feed
        rpm_deviation = abs(rpm - base_rpm) / base_rpm
        deviation_penalty = (feed_deviation + rpm_deviation) * 5
        score -= deviation_penalty

        if feed != base_feed or rpm != base_rpm:
            notes.append(f"Deviation: feed {feed_deviation*100:.1f}%, rpm {rpm_deviation*100:.1f}%")

        return round(score, 1), notes

    def suggest_best(
        self,
        tool_id: str,
        material_id: str,
        tool_kind: str,
        feed_mm_min: float,
        rpm: float,
        depth_of_cut_mm: float,
        width_of_cut_mm: Optional[float] = None,
        machine_id: Optional[str] = None,
    ) -> Optional[OptimizationCandidate]:
        """
        Get the single best parameter suggestion.
        
        Returns:
            Best OptimizationCandidate or None if no good options
        """
        candidates = self.search(
            tool_id=tool_id,
            material_id=material_id,
            tool_kind=tool_kind,
            feed_mm_min=feed_mm_min,
            rpm=rpm,
            depth_of_cut_mm=depth_of_cut_mm,
            width_of_cut_mm=width_of_cut_mm,
            machine_id=machine_id,
        )
        
        if candidates and candidates[0].score > 0:
            return candidates[0]
        return None
