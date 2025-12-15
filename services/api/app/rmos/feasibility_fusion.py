"""
RMOS Feasibility Fusion

Wave 18: Phase D - Feasibility Fusion Router

Aggregates all calculator risk assessments (chipload, heat, deflection, rimspeed, BOM)
into a unified feasibility score with actionable recommendations.

This module provides the business logic for evaluating manufacturability of
guitar components across multiple CNC feasibility dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum

from .context import RmosContext
from ..calculators.service import (
    compute_chipload_risk,
    compute_heat_risk,
    compute_deflection_risk,
    compute_rimspeed_risk,
    compute_bom_efficiency,
)


class RiskLevel(str, Enum):
    """Risk level enumeration for feasibility checks."""
    GREEN = "GREEN"      # Safe to proceed
    YELLOW = "YELLOW"    # Caution advised
    RED = "RED"          # Not recommended
    UNKNOWN = "UNKNOWN"  # Insufficient data


@dataclass
class RiskAssessment:
    """
    Individual risk assessment result.
    
    Attributes:
        category: Risk category name (e.g., "chipload", "heat").
        score: Numeric score (0-100, higher is better).
        risk: Risk level (GREEN/YELLOW/RED).
        warnings: List of warning messages.
        details: Additional diagnostic data.
    """
    category: str
    score: float
    risk: RiskLevel
    warnings: List[str]
    details: Dict[str, Any]


@dataclass
class FeasibilityReport:
    """
    Unified feasibility report aggregating all risk dimensions.
    
    Attributes:
        overall_score: Weighted aggregate score (0-100).
        overall_risk: Worst-case risk level across all categories.
        assessments: Per-category risk assessments.
        recommendations: Actionable improvement suggestions.
        pass_threshold: Minimum score for GREEN status (default: 70).
    """
    overall_score: float
    overall_risk: RiskLevel
    assessments: List[RiskAssessment]
    recommendations: List[str]
    pass_threshold: float = 70.0
    
    def is_feasible(self) -> bool:
        """Check if operation is feasible (overall_risk not RED)."""
        return self.overall_risk != RiskLevel.RED
    
    def needs_review(self) -> bool:
        """Check if operation needs engineering review (YELLOW or RED)."""
        return self.overall_risk in (RiskLevel.YELLOW, RiskLevel.RED)


def normalize_risk_result(result: Dict[str, Any], category: str) -> RiskAssessment:
    """
    Normalize calculator output to RiskAssessment format.
    
    Different calculators may return slightly different schemas.
    This function provides a uniform interface.
    
    Args:
        result: Raw calculator output dict.
        category: Risk category name.
    
    Returns:
        Normalized RiskAssessment object.
    """
    score = result.get("score", 0.0)
    risk_str = result.get("risk", "UNKNOWN")
    warnings = result.get("warnings", [])
    details = result.get("details", {})
    
    # Normalize risk string to RiskLevel enum
    try:
        risk = RiskLevel(risk_str)
    except ValueError:
        risk = RiskLevel.UNKNOWN
    
    return RiskAssessment(
        category=category,
        score=score,
        risk=risk,
        warnings=warnings,
        details=details,
    )


def compute_weighted_score(assessments: List[RiskAssessment]) -> float:
    """
    Compute weighted aggregate score from individual assessments.
    
    Weights (tunable):
        - chipload: 30% (critical for tool life)
        - heat: 25% (critical for finish quality)
        - deflection: 20% (affects precision)
        - rimspeed: 15% (safety concern)
        - bom_efficiency: 10% (cost optimization)
    
    Args:
        assessments: List of RiskAssessment objects.
    
    Returns:
        Weighted score (0-100).
    """
    weights = {
        "chipload": 0.30,
        "heat": 0.25,
        "deflection": 0.20,
        "rimspeed": 0.15,
        "bom_efficiency": 0.10,
    }
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for assessment in assessments:
        weight = weights.get(assessment.category, 0.1)  # Default 10% for unknown
        weighted_sum += assessment.score * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return weighted_sum / total_weight


def determine_overall_risk(assessments: List[RiskAssessment]) -> RiskLevel:
    """
    Determine overall risk level (worst-case across all categories).
    
    Priority: RED > YELLOW > GREEN > UNKNOWN
    
    Args:
        assessments: List of RiskAssessment objects.
    
    Returns:
        Overall RiskLevel.
    """
    if not assessments:
        return RiskLevel.UNKNOWN
    
    # Check for RED (any RED assessment fails entire operation)
    if any(a.risk == RiskLevel.RED for a in assessments):
        return RiskLevel.RED
    
    # Check for YELLOW (caution advised)
    if any(a.risk == RiskLevel.YELLOW for a in assessments):
        return RiskLevel.YELLOW
    
    # All GREEN or UNKNOWN
    if all(a.risk in (RiskLevel.GREEN, RiskLevel.UNKNOWN) for a in assessments):
        return RiskLevel.GREEN
    
    return RiskLevel.UNKNOWN


def generate_recommendations(assessments: List[RiskAssessment]) -> List[str]:
    """
    Generate actionable recommendations based on risk assessments.
    
    Args:
        assessments: List of RiskAssessment objects.
    
    Returns:
        List of recommendation strings.
    """
    recommendations = []
    
    for assessment in assessments:
        if assessment.risk == RiskLevel.RED:
            if assessment.category == "chipload":
                recommendations.append(
                    "[WARNING] Chipload too high: Reduce feed rate or use larger tool diameter."
                )
            elif assessment.category == "heat":
                recommendations.append(
                    "[WARNING] Heat buildup risk: Increase coolant flow or reduce spindle speed."
                )
            elif assessment.category == "deflection":
                recommendations.append(
                    "[WARNING] Tool deflection excessive: Use stiffer tool or reduce depth of cut."
                )
            elif assessment.category == "rimspeed":
                recommendations.append(
                    "[WARNING] Rim speed exceeds safe limits: Reduce spindle RPM or use smaller tool."
                )
        
        elif assessment.risk == RiskLevel.YELLOW:
            if assessment.category == "chipload":
                recommendations.append(
                    "[CAUTION] Chipload marginal: Consider reducing feed by 10-20%."
                )
            elif assessment.category == "heat":
                recommendations.append(
                    "[CAUTION] Heat buildup moderate: Monitor temperature during operation."
                )
            elif assessment.category == "bom_efficiency":
                recommendations.append(
                    "[CAUTION] Material efficiency low: Review nesting/layout to reduce waste."
                )
    
    # Add general advice if all GREEN
    if all(a.risk == RiskLevel.GREEN for a in assessments):
        recommendations.append("[OK] All parameters within safe operating range.")
    
    return recommendations


def evaluate_feasibility(
    design: Dict[str, Any],
    context: RmosContext,
) -> FeasibilityReport:
    """
    Evaluate overall feasibility of a manufacturing operation.
    
    This is the main entry point for Phase D feasibility fusion.
    Orchestrates all calculator calls and aggregates results.
    
    Args:
        design: Design parameters (tool, feeds, speeds, geometry).
        context: RMOS context with material and constraints.
    
    Returns:
        FeasibilityReport with overall score and per-category assessments.
    
    Example:
        >>> from rmos.context import RmosContext
        >>> ctx = RmosContext.from_model_id("strat_25_5")
        >>> design = {
        ...     "tool_diameter_mm": 6.0,
        ...     "feed_rate_mmpm": 1200,
        ...     "spindle_rpm": 18000,
        ...     "depth_of_cut_mm": 3.0,
        ... }
        >>> report = evaluate_feasibility(design, ctx)
        >>> report.overall_score
        85.3
        >>> report.is_feasible()
        True
    """
    request = {"design": design, "context": context}
    
    assessments = []
    
    # Run all calculator checks
    try:
        chipload_result = compute_chipload_risk(request)
        assessments.append(normalize_risk_result(chipload_result, "chipload"))
    except Exception as e:
        assessments.append(RiskAssessment(
            category="chipload",
            score=0.0,
            risk=RiskLevel.UNKNOWN,
            warnings=[f"Chipload check failed: {str(e)}"],
            details={},
        ))
    
    try:
        heat_result = compute_heat_risk(request)
        assessments.append(normalize_risk_result(heat_result, "heat"))
    except Exception as e:
        assessments.append(RiskAssessment(
            category="heat",
            score=0.0,
            risk=RiskLevel.UNKNOWN,
            warnings=[f"Heat check failed: {str(e)}"],
            details={},
        ))
    
    try:
        deflection_result = compute_deflection_risk(request)
        assessments.append(normalize_risk_result(deflection_result, "deflection"))
    except Exception as e:
        assessments.append(RiskAssessment(
            category="deflection",
            score=0.0,
            risk=RiskLevel.UNKNOWN,
            warnings=[f"Deflection check failed: {str(e)}"],
            details={},
        ))
    
    try:
        rimspeed_result = compute_rimspeed_risk(request)
        assessments.append(normalize_risk_result(rimspeed_result, "rimspeed"))
    except Exception as e:
        assessments.append(RiskAssessment(
            category="rimspeed",
            score=0.0,
            risk=RiskLevel.UNKNOWN,
            warnings=[f"Rimspeed check failed: {str(e)}"],
            details={},
        ))
    
    try:
        bom_result = compute_bom_efficiency(request)
        assessments.append(normalize_risk_result(bom_result, "bom_efficiency"))
    except Exception as e:
        assessments.append(RiskAssessment(
            category="bom_efficiency",
            score=0.0,
            risk=RiskLevel.UNKNOWN,
            warnings=[f"BOM efficiency check failed: {str(e)}"],
            details={},
        ))
    
    # Aggregate results
    overall_score = compute_weighted_score(assessments)
    overall_risk = determine_overall_risk(assessments)
    recommendations = generate_recommendations(assessments)
    
    return FeasibilityReport(
        overall_score=overall_score,
        overall_risk=overall_risk,
        assessments=assessments,
        recommendations=recommendations,
    )


def evaluate_feasibility_for_model(
    model_id: str,
    design: Dict[str, Any],
) -> FeasibilityReport:
    """
    Convenience function: Evaluate feasibility from model_id.
    
    Automatically creates RmosContext from model_id and evaluates.
    
    Args:
        model_id: Guitar model identifier (e.g., "strat_25_5").
        design: Design parameters dict.
    
    Returns:
        FeasibilityReport.
    
    Example:
        >>> report = evaluate_feasibility_for_model(
        ...     "strat_25_5",
        ...     {"tool_diameter_mm": 6.0, "feed_rate_mmpm": 1200}
        ... )
    """
    context = RmosContext.from_model_id(model_id)
    return evaluate_feasibility(design, context)


# =============================================================================
# Wave 19 Phase C: Per-Fret Risk Analysis for Fan-Fret CAM
# =============================================================================

@dataclass
class PerFretRisk:
    """
    Risk assessment for a single fret slot operation.
    
    Attributes:
        fret_number: Fret number (1-24).
        angle_deg: Slot angle in degrees.
        chipload_risk: Chipload risk score (0-100).
        heat_risk: Heat accumulation risk score (0-100).
        deflection_risk: Tool deflection risk score (0-100).
        overall_risk: RiskLevel (GREEN/YELLOW/RED).
        warnings: List of warnings for this fret.
    """
    fret_number: int
    angle_deg: float
    chipload_risk: float
    heat_risk: float
    deflection_risk: float
    overall_risk: RiskLevel
    warnings: List[str]


def evaluate_per_fret_feasibility(
    toolpaths: List[Any],
    context: RmosContext,
) -> List[PerFretRisk]:
    """
    Evaluate feasibility for each fret slot individually.
    
    This function analyzes each fret's specific geometry (angle, length, depth)
    and material properties to identify high-risk operations.
    
    Args:
        toolpaths: List of FretSlotToolpath objects from CAM generator.
        context: RMOS context with material and machine data.
    
    Returns:
        List of PerFretRisk objects, one per fret.
    
    Notes:
        - For fan-fret, angles affect chipload (oblique cutting increases load).
        - Longer slots accumulate more heat (bass side slots longer than treble).
        - Deeper slots (compound radius) increase deflection risk.
    
    Example:
        >>> toolpaths = generate_fret_slot_cam(spec, ctx, mode='fan')
        >>> risks = evaluate_per_fret_feasibility(toolpaths, ctx)
        >>> high_risk_frets = [r for r in risks if r.overall_risk == RiskLevel.RED]
    """
    per_fret_risks = []
    
    for tp in toolpaths:
        # Extract fret-specific parameters
        fret_num = tp.fret_number
        angle_rad = getattr(tp, 'angle_rad', 0.0)
        angle_deg = abs(angle_rad * 180.0 / 3.14159265359)
        slot_depth = tp.slot_depth_mm
        feed_rate = tp.feed_rate_mmpm
        
        # Calculate slot length (bass to treble)
        import math
        slot_length = math.sqrt(
            (tp.treble_point[0] - tp.bass_point[0])**2 +
            (tp.treble_point[1] - tp.bass_point[1])**2
        )
        
        warnings = []
        
        # ===== Chipload Risk Analysis =====
        # Base chipload risk from standard calculation
        chipload_base = 50.0  # Baseline risk
        
        # Angle penalty: Oblique cutting increases effective chipload
        # 0° = no penalty, 30° = +50% risk
        angle_factor = 1.0 + (angle_deg / 30.0) * 0.5
        chipload_risk = min(100.0, chipload_base * angle_factor)
        
        if angle_deg > 20.0:
            warnings.append(f"High angle ({angle_deg:.1f}°) increases chipload")
            chipload_risk = min(100.0, chipload_risk * 1.2)
        
        # Material hardness factor
        if context.materials and context.materials.density_kg_m3:
            if context.materials.density_kg_m3 > 1000:  # Dense hardwood (ebony)
                chipload_risk = min(100.0, chipload_risk * 1.3)
                warnings.append("Dense material increases chipload stress")
        
        # ===== Heat Risk Analysis =====
        # Longer slots accumulate more heat
        # Base: 43mm slot (typical nut width) = 50 risk
        # Each additional mm adds ~1% risk
        heat_base = 50.0
        length_factor = slot_length / 43.0
        heat_risk = min(100.0, heat_base * length_factor)
        
        if slot_length > 56.0:  # Longer than typical heel width
            warnings.append(f"Long slot ({slot_length:.1f}mm) may accumulate heat")
            heat_risk = min(100.0, heat_risk * 1.15)
        
        # Feed rate adjustment (slower feed = more heat)
        if feed_rate < 800:
            heat_risk = min(100.0, heat_risk * 1.2)
            warnings.append("Low feedrate increases heat risk")
        
        # ===== Deflection Risk Analysis =====
        # Deeper cuts and angles increase deflection
        deflection_base = 40.0
        depth_factor = slot_depth / 3.0  # 3mm is nominal
        angle_deflection = 1.0 + (angle_deg / 30.0) * 0.3
        
        deflection_risk = min(100.0, deflection_base * depth_factor * angle_deflection)
        
        if slot_depth > 3.5:
            warnings.append(f"Deep slot ({slot_depth:.2f}mm) increases deflection")
            deflection_risk = min(100.0, deflection_risk * 1.25)
        
        # ===== Overall Risk Determination =====
        # Average the three risk factors
        avg_risk = (chipload_risk + heat_risk + deflection_risk) / 3.0
        
        if avg_risk > 80:
            overall_risk = RiskLevel.RED
            warnings.append("Overall risk HIGH - review required")
        elif avg_risk > 60:
            overall_risk = RiskLevel.YELLOW
        else:
            overall_risk = RiskLevel.GREEN
        
        per_fret_risk = PerFretRisk(
            fret_number=fret_num,
            angle_deg=angle_deg,
            chipload_risk=chipload_risk,
            heat_risk=heat_risk,
            deflection_risk=deflection_risk,
            overall_risk=overall_risk,
            warnings=warnings,
        )
        
        per_fret_risks.append(per_fret_risk)
    
    return per_fret_risks


def summarize_per_fret_risks(per_fret_risks: List[PerFretRisk]) -> Dict[str, Any]:
    """
    Summarize per-fret risk analysis for reporting.
    
    Args:
        per_fret_risks: List of PerFretRisk objects.
    
    Returns:
        Summary dict with counts, max risks, and high-risk frets.
    
    Example:
        >>> summary = summarize_per_fret_risks(risks)
        >>> summary['high_risk_count']
        3
        >>> summary['max_angle_deg']
        27.5
    """
    if not per_fret_risks:
        return {
            "total_frets": 0,
            "green_count": 0,
            "yellow_count": 0,
            "red_count": 0,
            "high_risk_frets": [],
            "max_angle_deg": 0.0,
            "max_chipload_risk": 0.0,
            "max_heat_risk": 0.0,
            "max_deflection_risk": 0.0,
        }
    
    green_count = sum(1 for r in per_fret_risks if r.overall_risk == RiskLevel.GREEN)
    yellow_count = sum(1 for r in per_fret_risks if r.overall_risk == RiskLevel.YELLOW)
    red_count = sum(1 for r in per_fret_risks if r.overall_risk == RiskLevel.RED)
    
    high_risk_frets = [
        {
            "fret_number": r.fret_number,
            "angle_deg": round(r.angle_deg, 2),
            "chipload_risk": round(r.chipload_risk, 1),
            "heat_risk": round(r.heat_risk, 1),
            "deflection_risk": round(r.deflection_risk, 1),
            "warnings": r.warnings,
        }
        for r in per_fret_risks
        if r.overall_risk in (RiskLevel.YELLOW, RiskLevel.RED)
    ]
    
    return {
        "total_frets": len(per_fret_risks),
        "green_count": green_count,
        "yellow_count": yellow_count,
        "red_count": red_count,
        "high_risk_frets": high_risk_frets,
        "max_angle_deg": max(r.angle_deg for r in per_fret_risks),
        "max_chipload_risk": max(r.chipload_risk for r in per_fret_risks),
        "max_heat_risk": max(r.heat_risk for r in per_fret_risks),
        "max_deflection_risk": max(r.deflection_risk for r in per_fret_risks),
    }

