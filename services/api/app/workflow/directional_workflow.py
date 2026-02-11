"""
Directional Workflow 2.0 for Art Studio / RMOS integration.

This module implements three distinct workflow modes for rosette/pattern design:

1. design_first: Full artistic freedom, then machine constraints
   - User designs freely, system warns about feasibility issues after
   - Best for experienced designers who know machine limits

2. constraint_first: Start with machine limits, then design within bounds
   - System enforces hard limits upfront (RPM, feed, tool geometry)
   - Best for production-focused workflows

3. ai_assisted: AI-driven parameter suggestions based on goals
   - User specifies goals (speed, quality, tool life)
   - System suggests optimal parameters
   - Best for learning or complex multi-objective optimization

Part of RMOS 2.0.
"""
from app.safety import safety_critical

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DirectionalMode(str, Enum):
    """Workflow mode selection."""
    design_first = "design_first"
    constraint_first = "constraint_first"
    ai_assisted = "ai_assisted"


class ModeConstraints(BaseModel):
    """Constraints applied in a given mode."""
    
    mode: DirectionalMode
    hard_limits: Dict[str, Any] = Field(
        default_factory=dict,
        description="Hard limits enforced by the system (cannot be exceeded)"
    )
    soft_limits: Dict[str, Any] = Field(
        default_factory=dict,
        description="Soft limits that trigger warnings but allow override"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggested parameter values or ranges"
    )


class ModePreviewRequest(BaseModel):
    """Request payload for mode preview endpoint."""
    
    mode: DirectionalMode = Field(
        ...,
        description="The workflow mode to preview"
    )
    
    # Optional context for personalized constraints
    tool_id: Optional[str] = Field(
        None,
        description="Tool identifier (e.g., 'router:6_2_6.35' or 'saw:10_24_3.0')"
    )
    material_id: Optional[str] = Field(
        None,
        description="Material identifier from material library"
    )
    machine_profile: Optional[str] = Field(
        None,
        description="Machine profile for constraint derivation"
    )
    
    # AI-assisted mode goal weights (0.0-1.0)
    goal_speed: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Weight for cycle time optimization"
    )
    goal_quality: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Weight for surface finish quality"
    )
    goal_tool_life: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Weight for tool longevity"
    )


class ModePreviewResult(BaseModel):
    """Result of mode preview computation."""
    
    mode: DirectionalMode
    constraints: ModeConstraints
    feasibility_score: Optional[float] = Field(
        None,
        description="Pre-computed feasibility score (0-100) if context provided"
    )
    risk_level: Optional[str] = Field(
        None,
        description="Risk classification: GREEN, YELLOW, RED"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about parameter combinations"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="AI-generated recommendations (ai_assisted mode)"
    )


# Default constraint sets per mode
_MODE_DEFAULTS: Dict[DirectionalMode, Dict[str, Any]] = {
    DirectionalMode.design_first: {
        "hard_limits": {},  # No hard limits in design-first
        "soft_limits": {
            "max_rpm": 24000,
            "max_feed_mm_min": 5000,
            "max_stepover_pct": 80,
            "max_depth_mm": 25,
        },
        "suggestions": [
            "Design freely - feasibility warnings will appear after changes",
            "Use Preview button to check machine compatibility",
            "Consider material hardness when setting aggressive parameters",
        ],
    },
    DirectionalMode.constraint_first: {
        "hard_limits": {
            "max_rpm": 18000,
            "max_feed_mm_min": 3000,
            "max_stepover_pct": 60,
            "max_depth_mm": 15,
            "min_tool_diameter_mm": 3.0,
        },
        "soft_limits": {
            "recommended_rpm": 12000,
            "recommended_feed_mm_min": 1500,
            "recommended_stepover_pct": 40,
        },
        "suggestions": [
            "Parameters are clamped to safe machine limits",
            "Green indicators show optimal ranges",
            "Use machine profile to customize limits",
        ],
    },
    DirectionalMode.ai_assisted: {
        "hard_limits": {
            "max_rpm": 24000,
            "max_feed_mm_min": 5000,
        },
        "soft_limits": {},  # AI will compute dynamically
        "suggestions": [
            "Adjust goal sliders to prioritize speed, quality, or tool life",
            "AI will suggest optimal parameters based on your priorities",
            "Review recommendations before applying",
        ],
    },
}


def get_mode_constraints(
    mode: DirectionalMode,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    machine_profile: Optional[str] = None,
) -> ModeConstraints:
    """
    Get constraints for a given workflow mode.
    
    Args:
        mode: The directional workflow mode
        tool_id: Optional tool identifier for tool-specific limits
        material_id: Optional material identifier for material-specific limits
        machine_profile: Optional machine profile for machine-specific limits
    
    Returns:
        ModeConstraints with hard limits, soft limits, and suggestions
    """
    defaults = _MODE_DEFAULTS.get(mode, _MODE_DEFAULTS[DirectionalMode.design_first])
    
    hard_limits = dict(defaults["hard_limits"])
    soft_limits = dict(defaults["soft_limits"])
    suggestions = list(defaults["suggestions"])
    
    # Customize based on tool type
    if tool_id:
        if tool_id.startswith("saw:"):
            # Saw tools have different constraints
            hard_limits["max_rpm"] = min(hard_limits.get("max_rpm", 6000), 6000)
            hard_limits["max_feed_mm_min"] = min(hard_limits.get("max_feed_mm_min", 2000), 2000)
            suggestions.append("Saw mode: Lower RPM and feed limits applied")
        elif tool_id.startswith("router:"):
            # Router-specific adjustments
            suggestions.append("Router mode: Standard milling constraints active")
    
    # Customize based on machine profile (placeholder for future M.4 integration)
    if machine_profile:
        suggestions.append(f"Using machine profile: {machine_profile}")
    
    # Customize based on material (placeholder for material library integration)
    if material_id:
        suggestions.append(f"Material-specific limits for: {material_id}")
    
    return ModeConstraints(
        mode=mode,
        hard_limits=hard_limits,
        soft_limits=soft_limits,
        suggestions=suggestions,
    )


@safety_critical
def compute_feasibility_for_mode(
    request: ModePreviewRequest,
) -> ModePreviewResult:
    """
    Compute feasibility preview for a given workflow mode and context.
    
    This function:
    1. Gets base constraints for the mode
    2. Applies tool/material/machine customizations
    3. Computes preliminary feasibility score if context provided
    4. Generates AI recommendations for ai_assisted mode
    
    Args:
        request: ModePreviewRequest with mode and optional context
    
    Returns:
        ModePreviewResult with constraints, score, and recommendations
    """
    # Get base constraints
    constraints = get_mode_constraints(
        mode=request.mode,
        tool_id=request.tool_id,
        material_id=request.material_id,
        machine_profile=request.machine_profile,
    )
    
    warnings: List[str] = []
    recommendations: List[str] = []
    feasibility_score: Optional[float] = None
    risk_level: Optional[str] = None
    
    # Mode-specific processing
    if request.mode == DirectionalMode.design_first:
        # Design-first: No upfront scoring, just constraint info
        warnings.append("Design-first mode: Feasibility checked after parameter changes")
        
    elif request.mode == DirectionalMode.constraint_first:
        # Constraint-first: Compute baseline feasibility
        if request.tool_id or request.material_id:
            # Simplified scoring based on presence of context
            feasibility_score = 85.0  # Default high score with constraints active
            risk_level = "GREEN"
            recommendations.append("Operating within safe limits")
        else:
            warnings.append("Provide tool_id or material_id for feasibility scoring")
            
    elif request.mode == DirectionalMode.ai_assisted:
        # AI-assisted: Generate recommendations based on goals
        recommendations = _generate_ai_recommendations(
            goal_speed=request.goal_speed,
            goal_quality=request.goal_quality,
            goal_tool_life=request.goal_tool_life,
            tool_id=request.tool_id,
            material_id=request.material_id,
        )
        
        # Compute balanced score based on goal weights
        feasibility_score = _compute_ai_feasibility(
            goal_speed=request.goal_speed,
            goal_quality=request.goal_quality,
            goal_tool_life=request.goal_tool_life,
        )
        risk_level = _score_to_risk(feasibility_score)
    
    return ModePreviewResult(
        mode=request.mode,
        constraints=constraints,
        feasibility_score=feasibility_score,
        risk_level=risk_level,
        warnings=warnings,
        recommendations=recommendations,
    )


def _generate_ai_recommendations(
    goal_speed: float,
    goal_quality: float,
    goal_tool_life: float,
    tool_id: Optional[str],
    material_id: Optional[str],
) -> List[str]:
    """Generate AI recommendations based on goal weights."""
    recommendations = []
    
    # Determine dominant goal
    goals = {
        "speed": goal_speed,
        "quality": goal_quality,
        "tool_life": goal_tool_life,
    }
    dominant = max(goals, key=goals.get)
    
    if dominant == "speed":
        recommendations.append("Prioritizing speed: Consider higher feed rates and stepovers")
        recommendations.append("Suggested feed: 2000-3000 mm/min for softwood")
        recommendations.append("Suggested stepover: 50-60% of tool diameter")
    elif dominant == "quality":
        recommendations.append("Prioritizing quality: Use finer stepovers and lower feeds")
        recommendations.append("Suggested feed: 800-1200 mm/min for optimal finish")
        recommendations.append("Suggested stepover: 30-40% of tool diameter")
    else:
        recommendations.append("Prioritizing tool life: Conservative parameters recommended")
        recommendations.append("Suggested RPM: 70% of maximum for reduced wear")
        recommendations.append("Suggested depth: Light passes (1-2mm) to reduce tool stress")
    
    # Tool-specific recommendations
    if tool_id:
        if tool_id.startswith("saw:"):
            recommendations.append("Saw tool: Optimize tooth engagement and feed per tooth")
        else:
            recommendations.append("Router tool: Balance chipload with surface speed")
    
    # Material-specific recommendations (placeholder)
    if material_id:
        recommendations.append(f"Consider {material_id} hardness when setting feed rate")
    
    return recommendations


def _compute_ai_feasibility(
    goal_speed: float,
    goal_quality: float,
    goal_tool_life: float,
) -> float:
    """
    Compute AI-assisted feasibility score.
    
    Higher goal diversity (all goals balanced) → higher baseline score
    Extreme single-goal focus → lower baseline score (harder to achieve)
    """
    # Normalize goals
    total = goal_speed + goal_quality + goal_tool_life
    if total == 0:
        return 75.0  # Default neutral score
    
    # Compute balance metric (entropy-like)
    weights = [goal_speed / total, goal_quality / total, goal_tool_life / total]
    balance = 1.0 - max(weights)  # 0 = all focus on one, 0.67 = perfectly balanced
    
    # Balanced goals are easier to achieve
    base_score = 70.0 + (balance * 20.0)  # 70-90 range
    
    return round(base_score, 1)


def _score_to_risk(score: float) -> str:
    """Convert feasibility score to risk level."""
    if score >= 80:
        return "GREEN"
    elif score >= 60:
        return "YELLOW"
    else:
        return "RED"
