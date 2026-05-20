"""
Continuity Checker.

Sprint: MRP-5I
Status: PROTOTYPE

Validates continuity at shell junctions: G0, G1, G2.

Continuity Levels:
- G0: Positional continuity (surfaces touch)
- G1: Tangent continuity (surfaces are smooth)
- G2: Curvature continuity (surfaces have matching curvature)

Key Principle: Validation does NOT mutate topology.
"""

from typing import Any, Dict, List, Optional

from .contracts import (
    ContinuityReport,
    ValidationCategory,
    ValidationFinding,
    ValidationSeverity,
    ValidationTier,
)
from .exceptions import ContinuityError


# Tolerance constants
G0_GAP_TOLERANCE_MM = 0.1  # 0.1mm positional tolerance
G0_GAP_TOLERANCE_PRODUCTION_MM = 0.01  # 0.01mm for PRODUCTION
G1_ANGLE_TOLERANCE_DEG = 5.0  # 5 degree tangent tolerance
G1_ANGLE_TOLERANCE_PRODUCTION_DEG = 1.0  # 1 degree for PRODUCTION
G2_CURVATURE_TOLERANCE = 0.1  # Relative curvature tolerance


class ContinuityChecker:
    """
    Checks continuity at shell junctions.

    Evaluates whether surfaces meet continuity requirements
    at their junction points.
    """

    def __init__(self, tier: ValidationTier = ValidationTier.PROTOTYPE):
        """
        Initialize the checker.

        Args:
            tier: Validation tier affecting strictness and tolerances
        """
        self.tier = tier
        self._set_tolerances()

    def _set_tolerances(self) -> None:
        """Set tolerances based on tier."""
        if self.tier == ValidationTier.PRODUCTION:
            self.g0_tolerance = G0_GAP_TOLERANCE_PRODUCTION_MM
            self.g1_tolerance = G1_ANGLE_TOLERANCE_PRODUCTION_DEG
        else:
            self.g0_tolerance = G0_GAP_TOLERANCE_MM
            self.g1_tolerance = G1_ANGLE_TOLERANCE_DEG

        self.g2_tolerance = G2_CURVATURE_TOLERANCE

    def check_junction(
        self,
        junction_name: str,
        target_level: str,
        continuity_metadata: Optional[Dict[str, Any]] = None,
    ) -> ContinuityReport:
        """
        Check continuity at a junction.

        Args:
            junction_name: Name of the junction
            target_level: Required continuity level (G0, G1, G2)
            continuity_metadata: Metadata from topology builder

        Returns:
            ContinuityReport with check results
        """
        report = ContinuityReport(
            junction_name=junction_name,
            target_level=target_level,
        )

        if continuity_metadata:
            achieved = continuity_metadata.get("achieved")
            if achieved:
                report.achieved_level = achieved
            report.gap_mm = continuity_metadata.get("gap_mm")
            report.angle_deviation_deg = continuity_metadata.get("angle_deviation_deg")
            report.curvature_deviation = continuity_metadata.get("curvature_deviation")

        # Evaluate continuity
        self._evaluate_continuity(report)

        return report

    def check_junctions(
        self,
        continuity_targets: Dict[str, str],
        continuity_metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ContinuityReport]:
        """
        Check continuity at multiple junctions.

        Args:
            continuity_targets: Dict mapping junction names to target levels
            continuity_metadata: List of continuity metadata from topology builder

        Returns:
            List of ContinuityReport
        """
        metadata_by_name = {}
        if continuity_metadata:
            for cm in continuity_metadata:
                name = cm.get("junction_name")
                if name:
                    metadata_by_name[name] = cm

        reports = []
        for junction_name, target_level in continuity_targets.items():
            meta = metadata_by_name.get(junction_name)
            report = self.check_junction(junction_name, target_level, meta)
            reports.append(report)

        return reports

    def _evaluate_continuity(self, report: ContinuityReport) -> None:
        """Evaluate whether continuity target was met."""
        target = report.target_level.upper()
        achieved = (report.achieved_level or "").upper()

        # Order for comparison
        levels = ["G0", "G1", "G2"]

        if achieved and achieved in levels:
            target_idx = levels.index(target) if target in levels else -1
            achieved_idx = levels.index(achieved)
            report.met_target = achieved_idx >= target_idx
        else:
            report.met_target = False

        # Add findings based on result
        if not report.met_target:
            self._add_continuity_finding(report)
        elif report.gap_mm is not None and report.gap_mm > self.g0_tolerance:
            self._add_gap_warning(report)

    def _add_continuity_finding(self, report: ContinuityReport) -> None:
        """Add finding for unmet continuity target."""
        if self.tier == ValidationTier.PRODUCTION:
            severity = ValidationSeverity.BLOCKING
        else:
            severity = ValidationSeverity.MAJOR

        achieved_str = report.achieved_level or "none"
        report.findings.append(
            ValidationFinding(
                category=ValidationCategory.CONTINUITY,
                severity=severity,
                message=(
                    f"Junction '{report.junction_name}' requires {report.target_level} "
                    f"but achieved {achieved_str}"
                ),
                location=report.junction_name,
                details={
                    "target": report.target_level,
                    "achieved": achieved_str,
                    "gap_mm": report.gap_mm,
                    "angle_deviation_deg": report.angle_deviation_deg,
                },
            )
        )

    def _add_gap_warning(self, report: ContinuityReport) -> None:
        """Add warning for gap exceeding tolerance (but continuity target met)."""
        report.findings.append(
            ValidationFinding(
                category=ValidationCategory.CONTINUITY,
                severity=ValidationSeverity.MINOR,
                message=(
                    f"Junction '{report.junction_name}' has gap {report.gap_mm:.4f}mm "
                    f"(tolerance: {self.g0_tolerance}mm)"
                ),
                location=report.junction_name,
                details={
                    "gap_mm": report.gap_mm,
                    "tolerance_mm": self.g0_tolerance,
                },
            )
        )


def check_continuity(
    junction_name: str,
    target_level: str,
    continuity_metadata: Optional[Dict[str, Any]] = None,
    tier: ValidationTier = ValidationTier.PROTOTYPE,
) -> ContinuityReport:
    """
    Convenience function to check continuity at a junction.

    Args:
        junction_name: Name of the junction
        target_level: Required continuity level
        continuity_metadata: Metadata from topology builder
        tier: Validation tier

    Returns:
        ContinuityReport
    """
    checker = ContinuityChecker(tier=tier)
    return checker.check_junction(junction_name, target_level, continuity_metadata)


def check_all_continuity(
    continuity_targets: Dict[str, str],
    continuity_metadata: Optional[List[Dict[str, Any]]] = None,
    tier: ValidationTier = ValidationTier.PROTOTYPE,
) -> List[ContinuityReport]:
    """
    Convenience function to check continuity at multiple junctions.

    Args:
        continuity_targets: Dict mapping junction names to target levels
        continuity_metadata: List of continuity metadata
        tier: Validation tier

    Returns:
        List of ContinuityReport
    """
    checker = ContinuityChecker(tier=tier)
    return checker.check_junctions(continuity_targets, continuity_metadata)
