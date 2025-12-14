"""
RMOS 2.0 Feasibility Scorer
Aggregates calculator results with weighted averaging and risk bucketing.

Supports three tool modes:
    - Router mode (default): For rosette/router operations
    - Saw mode: Activated when tool_id starts with "saw:" prefix

Supports three workflow modes (Directional Workflow 2.0):
    - design_first: No upfront constraints, feasibility checked after changes
    - constraint_first: Hard limits enforced upfront, safe parameters only
    - ai_assisted: AI-driven suggestions based on goal weights

Integrates with migrated pipeline calculators:
    - rosette_calc: Channel width/depth from design parameters
    - bracing_calc: Brace mass/glue calculations (future)
"""
from typing import Dict, Any, List, Optional
from .api_contracts import RmosContext, RmosFeasibilityResult, RiskBucket

# Import migrated rosette calculator
try:
    from ..pipelines.rosette import compute as rosette_compute
except ImportError:
    rosette_compute = None  # Graceful fallback

# Import workflow types (graceful fallback if not available)
try:
    from ..workflow import DirectionalMode
except ImportError:
    DirectionalMode = None  # type: ignore

try:
    from ..art_studio.schemas import RosetteParamSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    from .api_contracts import RosetteParamSpec


def _is_saw_tool(tool_id: Optional[str]) -> bool:
    """Check if tool_id indicates a saw blade operation."""
    if not tool_id:
        return False
    return tool_id.lower().startswith("saw:")


def score_design_feasibility(
    design: RosetteParamSpec,
    ctx: RmosContext,
    workflow_mode: Optional[str] = None
) -> RmosFeasibilityResult:
    """
    Aggregate multiple calculator results into single feasibility score.
    Uses weighted averaging and worst-case risk propagation.
    
    Branches on:
    - Saw mode when tool_id starts with "saw:" prefix
    - Workflow mode affects constraint application and warnings
    
    Args:
        design: Rosette design parameters
        ctx: Manufacturing environment context
        workflow_mode: Optional workflow mode (design_first, constraint_first, ai_assisted)
    
    Returns:
        RmosFeasibilityResult with 0-100 score, risk bucket, and warnings
    """
    # Apply workflow mode modifiers if specified
    mode_warnings = []
    if workflow_mode and DirectionalMode:
        try:
            mode = DirectionalMode(workflow_mode)
            if mode == DirectionalMode.design_first:
                # No upfront constraints - proceed to scoring
                mode_warnings.append("Design-first mode: Full scoring applied, no hard limits enforced")
            elif mode == DirectionalMode.constraint_first:
                # Check hard limits before scoring
                limit_violations = _check_hard_limits(design, ctx)
                if limit_violations:
                    return RmosFeasibilityResult(
                        score=0.0,
                        risk_bucket=RiskBucket.RED,
                        warnings=limit_violations + ["Constraint-first mode: Hard limits violated"],
                        efficiency=0.0,
                        estimated_cut_time_seconds=0.0,
                        calculator_results={"limit_violations": limit_violations}
                    )
                mode_warnings.append("Constraint-first mode: Operating within hard limits")
            elif mode == DirectionalMode.ai_assisted:
                mode_warnings.append("AI-assisted mode: Enhanced recommendations available")
        except ValueError:
            mode_warnings.append(f"Unknown workflow mode: {workflow_mode}")
    
    # Check for saw mode first
    if _is_saw_tool(ctx.tool_id):
        result = _score_saw_feasibility(design, ctx)
    else:
        # Router mode (default)
        result = _score_router_feasibility(design, ctx)
    
    # Add workflow mode warnings to result
    if mode_warnings:
        result.warnings = mode_warnings + result.warnings
    
    return result


def _check_hard_limits(design: RosetteParamSpec, ctx: RmosContext) -> List[str]:
    """
    Check hard limits for constraint_first mode.
    Returns list of violations (empty if all OK).
    """
    violations = []
    
    # Hard limits from constraint_first mode defaults
    hard_limits = {
        "max_rpm": 18000,
        "max_feed_mm_min": 3000,
        "max_depth_mm": 15.0,
        "min_tool_diameter_mm": 3.0,
    }
    
    # Check RPM limit
    if ctx.rpm and ctx.rpm > hard_limits["max_rpm"]:
        violations.append(f"RPM {ctx.rpm} exceeds limit {hard_limits['max_rpm']}")
    
    # Check feed rate limit
    if ctx.feed_rate_mm_min and ctx.feed_rate_mm_min > hard_limits["max_feed_mm_min"]:
        violations.append(f"Feed rate {ctx.feed_rate_mm_min} exceeds limit {hard_limits['max_feed_mm_min']}")
    
    # Check depth limit (from design)
    if hasattr(design, 'depth_mm') and design.depth_mm > hard_limits["max_depth_mm"]:
        violations.append(f"Depth {design.depth_mm}mm exceeds limit {hard_limits['max_depth_mm']}mm")
    
    # Check minimum tool diameter
    if hasattr(ctx, 'tool_diameter_mm') and ctx.tool_diameter_mm:
        if ctx.tool_diameter_mm < hard_limits["min_tool_diameter_mm"]:
            violations.append(f"Tool diameter {ctx.tool_diameter_mm}mm below minimum {hard_limits['min_tool_diameter_mm']}mm")
    
    return violations


def _score_saw_feasibility(
    design: RosetteParamSpec,
    ctx: RmosContext
) -> RmosFeasibilityResult:
    """Score feasibility using Saw Lab calculators."""
    try:
        from ..toolpath.saw_engine import get_saw_engine
        engine = get_saw_engine()
        return engine.check_feasibility(design, ctx)
    except ImportError as e:
        return RmosFeasibilityResult(
            score=50.0,
            risk_bucket=RiskBucket.YELLOW,
            warnings=[f"Saw Lab module not available: {str(e)}"],
            efficiency=0.0,
            estimated_cut_time_seconds=0.0,
            calculator_results={}
        )


def _score_router_feasibility(
    design: RosetteParamSpec,
    ctx: RmosContext
) -> RmosFeasibilityResult:
    """Score feasibility using router calculators (original logic)."""
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
    
    # 6. Rosette channel dimensions (weight: 0.1) - from migrated rosette_calc
    try:
        channel_result = _check_rosette_channel(design, ctx)
        calculator_results["rosette_channel"] = channel_result
        scores.append(channel_result.get("score", 100.0))
        weights.append(0.1)
        risk_levels.append(_classify_risk(channel_result.get("score", 100.0)))
        if channel_result.get("warning"):
            warnings.append(f"Channel: {channel_result['warning']}")
    except Exception as e:
        # Non-critical - just log warning, don't affect score
        calculator_results["rosette_channel"] = {"error": str(e)}
    
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


def _check_rosette_channel(design: RosetteParamSpec, ctx: RmosContext) -> Dict[str, Any]:
    """
    Check rosette channel dimensions using migrated rosette_calc.
    
    Validates:
    - Channel width is achievable with current tool
    - Channel depth is reasonable for material
    - Total dimensions fit within design bounds
    """
    if rosette_compute is None:
        return {"score": 100.0, "warning": "rosette_calc not available", "skipped": True}
    
    # Build params from design (adapt to rosette_calc format)
    params = _design_to_rosette_params(design)
    
    try:
        result = rosette_compute(params)
        channel_width = result.get('channel_width_mm', 0)
        channel_depth = result.get('channel_depth_mm', 0)
        
        score = 100.0
        warnings = []
        
        # Check channel width vs tool diameter
        tool_diameter = getattr(ctx, 'tool_diameter_mm', None) or 6.0
        if channel_width > 0 and channel_width < tool_diameter * 1.2:
            # Channel barely wider than tool - risky
            score -= 20
            warnings.append(f"Channel width ({channel_width:.1f}mm) near tool diameter ({tool_diameter}mm)")
        
        # Check channel depth vs typical limits
        if channel_depth > 5.0:
            score -= 15
            warnings.append(f"Channel depth ({channel_depth:.1f}mm) exceeds 5mm - multiple passes needed")
        elif channel_depth > 3.0:
            score -= 5
            warnings.append(f"Channel depth ({channel_depth:.1f}mm) may need stepdown passes")
        
        # Check for very narrow channels (hard to cut cleanly)
        if 0 < channel_width < 3.0:
            score -= 25
            warnings.append(f"Very narrow channel ({channel_width:.1f}mm) - may need smaller tool")
        
        return {
            "score": max(0, score),
            "channel_width_mm": channel_width,
            "channel_depth_mm": channel_depth,
            "warning": "; ".join(warnings) if warnings else None,
            "raw_result": result,
        }
    except Exception as e:
        return {"score": 50.0, "warning": f"Channel calculation error: {str(e)}", "error": True}


def _design_to_rosette_params(design: RosetteParamSpec) -> Dict[str, Any]:
    """Convert RosetteParamSpec to rosette_calc params format."""
    # Map from RosetteParamSpec fields to rosette_calc expected format
    params = {
        'soundhole_diameter_mm': getattr(design, 'outer_diameter_mm', 100.0),
    }
    
    # Try to extract central band from design
    if hasattr(design, 'central_band'):
        params['central_band'] = design.central_band
    elif hasattr(design, 'ring_count') and hasattr(design, 'outer_diameter_mm'):
        # Estimate central band from ring geometry
        ring_count = getattr(design, 'ring_count', 3)
        outer_d = getattr(design, 'outer_diameter_mm', 100.0)
        inner_d = getattr(design, 'inner_diameter_mm', 20.0)
        channel_width = (outer_d - inner_d) / 2
        band_width = channel_width / max(1, ring_count)
        params['central_band'] = {
            'width_mm': band_width,
            'thickness_mm': 1.0,  # Default thickness
        }
    else:
        # Fallback default
        params['central_band'] = {'width_mm': 18, 'thickness_mm': 1.0}
    
    return params


def _estimate_efficiency(design: RosetteParamSpec, ctx: RmosContext) -> float:
    """
    Estimate material efficiency percentage.
    Uses rosette_calc channel dimensions when available for more accurate estimate.
    """
    try:
        outer_d = getattr(design, 'outer_diameter_mm', 100.0)
        inner_d = getattr(design, 'inner_diameter_mm', 20.0)
        
        # Try to get actual channel dimensions from rosette_calc
        if rosette_compute is not None:
            try:
                params = _design_to_rosette_params(design)
                result = rosette_compute(params)
                channel_width = result.get('channel_width_mm', 0)
                if channel_width > 0:
                    # Actual rosette area vs bounding box
                    outer_r = outer_d / 2
                    inner_r = inner_d / 2
                    channel_outer_r = (outer_d / 2) + (channel_width / 2)
                    channel_inner_r = (inner_d / 2) - (channel_width / 2)
                    
                    rosette_area = 3.14159 * (channel_outer_r**2 - channel_inner_r**2)
                    bounding_area = 3.14159 * channel_outer_r**2
                    
                    return round((rosette_area / bounding_area) * 100, 2)
            except Exception:
                pass  # Fall through to basic estimate
        
        # Basic estimate: larger inner diameter = higher waste
        outer_area = 3.14159 * (outer_d / 2) ** 2
        inner_area = 3.14159 * (inner_d / 2) ** 2
        usable_area = outer_area - inner_area
        return round((usable_area / outer_area) * 100, 2)
    except Exception:
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
