"""
RMOS 2.0 Feasibility Scorer
Aggregates calculator results with weighted averaging and risk bucketing.
"""
from typing import Dict, Any, List
from .api_contracts import RmosContext, RmosFeasibilityResult, RiskBucket

try:
    from ..art_studio.schemas import RosetteParamSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    from .api_contracts import RosetteParamSpec


def score_design_feasibility(
    design: RosetteParamSpec,
    ctx: RmosContext
) -> RmosFeasibilityResult:
    """
    Aggregate multiple calculator results into single feasibility score.
    Uses weighted averaging and worst-case risk propagation.
    
    Args:
        design: Rosette design parameters
        ctx: Manufacturing environment context
    
    Returns:
        RmosFeasibilityResult with 0-100 score, risk bucket, and warnings
    """
    from .api_contracts import RmosServices
    
    calc_service = RmosServices.get_calculator_service()
    
    # Collect individual calculator results
    calculator_results = {}
    warnings: List[str] = []
    scores: List[float] = []
    weights: List[float] = []
    risk_levels: List[RiskBucket] = []
    
    # 1. Chipload feasibility (weight: 0.3)
    try:
        chipload_result = calc_service.check_chipload_feasibility(design, ctx)
        calculator_results["chipload"] = chipload_result
        scores.append(chipload_result.get("score", 100.0))
        weights.append(0.3)
        risk_levels.append(_classify_risk(chipload_result.get("score", 100.0)))
        if chipload_result.get("warning"):
            warnings.append(f"Chipload: {chipload_result['warning']}")
    except Exception as e:
        warnings.append(f"Chipload calculation failed: {str(e)}")
        scores.append(50.0)  # Neutral score on error
        weights.append(0.3)
        risk_levels.append(RiskBucket.YELLOW)
    
    # 2. Heat dissipation (weight: 0.25)
    try:
        heat_result = calc_service.check_heat_dissipation(design, ctx)
        calculator_results["heat"] = heat_result
        scores.append(heat_result.get("score", 100.0))
        weights.append(0.25)
        risk_levels.append(_classify_risk(heat_result.get("score", 100.0)))
        if heat_result.get("warning"):
            warnings.append(f"Heat: {heat_result['warning']}")
    except Exception as e:
        warnings.append(f"Heat calculation failed: {str(e)}")
        scores.append(50.0)
        weights.append(0.25)
        risk_levels.append(RiskBucket.YELLOW)
    
    # 3. Tool deflection (weight: 0.2)
    try:
        deflection_result = calc_service.check_tool_deflection(design, ctx)
        calculator_results["deflection"] = deflection_result
        scores.append(deflection_result.get("score", 100.0))
        weights.append(0.2)
        risk_levels.append(_classify_risk(deflection_result.get("score", 100.0)))
        if deflection_result.get("warning"):
            warnings.append(f"Deflection: {deflection_result['warning']}")
    except Exception as e:
        warnings.append(f"Deflection calculation failed: {str(e)}")
        scores.append(50.0)
        weights.append(0.2)
        risk_levels.append(RiskBucket.YELLOW)
    
    # 4. Rim speed (weight: 0.15)
    try:
        rim_speed_result = calc_service.check_rim_speed(design, ctx)
        calculator_results["rim_speed"] = rim_speed_result
        scores.append(rim_speed_result.get("score", 100.0))
        weights.append(0.15)
        risk_levels.append(_classify_risk(rim_speed_result.get("score", 100.0)))
        if rim_speed_result.get("warning"):
            warnings.append(f"Rim Speed: {rim_speed_result['warning']}")
    except Exception as e:
        warnings.append(f"Rim speed calculation failed: {str(e)}")
        scores.append(50.0)
        weights.append(0.15)
        risk_levels.append(RiskBucket.YELLOW)
    
    # 5. Geometry complexity (weight: 0.1)
    try:
        geometry_result = calc_service.check_geometry_complexity(design, ctx)
        calculator_results["geometry"] = geometry_result
        scores.append(geometry_result.get("score", 100.0))
        weights.append(0.1)
        risk_levels.append(_classify_risk(geometry_result.get("score", 100.0)))
        if geometry_result.get("warning"):
            warnings.append(f"Geometry: {geometry_result['warning']}")
    except Exception as e:
        warnings.append(f"Geometry calculation failed: {str(e)}")
        scores.append(50.0)
        weights.append(0.1)
        risk_levels.append(RiskBucket.YELLOW)
    
    # Compute weighted average score
    if sum(weights) > 0:
        overall_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    else:
        overall_score = 50.0
        warnings.append("No valid calculator results; using neutral score")
    
    # Apply worst-case risk propagation (one RED makes overall RED)
    if RiskBucket.RED in risk_levels:
        overall_risk = RiskBucket.RED
    elif RiskBucket.YELLOW in risk_levels:
        overall_risk = RiskBucket.YELLOW
    else:
        overall_risk = RiskBucket.GREEN
    
    # Estimate efficiency and cut time (placeholder logic)
    efficiency = _estimate_efficiency(design, ctx)
    cut_time = _estimate_cut_time(design, ctx)
    
    return RmosFeasibilityResult(
        score=round(overall_score, 2),
        risk_bucket=overall_risk,
        warnings=warnings,
        efficiency=efficiency,
        estimated_cut_time_seconds=cut_time,
        calculator_results=calculator_results
    )


def _classify_risk(score: float) -> RiskBucket:
    """Convert 0-100 score to risk bucket"""
    if score >= 80:
        return RiskBucket.GREEN
    elif score >= 50:
        return RiskBucket.YELLOW
    else:
        return RiskBucket.RED


def _estimate_efficiency(design: RosetteParamSpec, ctx: RmosContext) -> float:
    """
    Placeholder: Estimate material efficiency percentage.
    Real implementation would compute rosette area / bounding box area.
    """
    # Simplified heuristic: larger inner diameter = higher waste
    try:
        outer_area = 3.14159 * (design.outer_diameter_mm / 2) ** 2
        inner_area = 3.14159 * (design.inner_diameter_mm / 2) ** 2
        usable_area = outer_area - inner_area
        return round((usable_area / outer_area) * 100, 2)
    except:
        return 85.0  # Default assumption


def _estimate_cut_time(design: RosetteParamSpec, ctx: RmosContext) -> float:
    """
    Placeholder: Estimate machining time in seconds.
    Real implementation would integrate with toolpath service.
    """
    # Simplified heuristic: proportional to ring count and diameter
    try:
        perimeter_mm = 3.14159 * design.outer_diameter_mm
        total_path_mm = perimeter_mm * design.ring_count * 2  # Rough estimate
        feed_rate_mm_per_min = 1200.0  # Typical feed rate
        time_minutes = total_path_mm / feed_rate_mm_per_min
        return round(time_minutes * 60, 2)  # Convert to seconds
    except:
        return 300.0  # 5-minute default
