"""
Feasibility Rules — Phase 3 Explainability

Each rule now emits a rule_id that maps to the authoritative registry.
The message is preserved for backward compatibility, but rule_id is
the canonical reference for explanation lookup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .schemas import FeasibilityInput, MaterialHardness


@dataclass(frozen=True)
class RuleHit:
    """
    A single rule trigger result.
    
    Attributes:
        rule_id: Canonical rule identifier (e.g., "F001") — lookup in rule_registry.py
        level: "RED" or "YELLOW"
        message: Human-readable message (for backward compatibility)
        constraint: Optional constraint expression that was violated
    """
    rule_id: str  # Phase 3: canonical identifier for registry lookup
    level: str  # "RED" or "YELLOW"
    message: str
    constraint: Optional[str] = None


# =============================================================================
# RED rules (blocking)
# =============================================================================

def rule_red_invalid_tool(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.tool_d <= 0:
        hits.append(RuleHit("F001", "RED", "tool_d must be > 0"))
    return hits


def rule_red_invalid_stepover(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    # Allow 100% stepover for slotting operations (full-width cuts)
    max_stepover = 1.0 if fi.strategy == "slot" else 0.95
    if fi.stepover <= 0 or fi.stepover > max_stepover:
        hits.append(RuleHit("F002", "RED", f"stepover must be in (0, {max_stepover}]"))
    return hits


def rule_red_invalid_stepdown(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.stepdown <= 0:
        hits.append(RuleHit("F003", "RED", "stepdown must be > 0"))
    return hits


def rule_red_invalid_depth(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.z_rough >= 0:
        hits.append(RuleHit("F004", "RED", "z_rough must be negative (cutting depth)"))
    return hits


def rule_red_invalid_safe_z(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.safe_z <= 0:
        hits.append(RuleHit("F005", "RED", "safe_z must be > 0"))
    return hits


def rule_red_no_closed_geometry_hint(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    # We only enforce this if we actually know it from preflight.
    if fi.has_closed_paths is False:
        hits.append(RuleHit("F006", "RED", "DXF contains no closed paths on selected layer"))
    # Optional hint: if loop_count_hint is known and == 0, treat as RED
    if fi.loop_count_hint is not None and fi.loop_count_hint <= 0:
        hits.append(RuleHit("F007", "RED", "No closed loops detected in DXF (preflight)"))
    return hits


# =============================================================================
# RED rules — Adversarial Detection (F020-F029)
# =============================================================================

def rule_red_excessive_doc_hardwood(fi: FeasibilityInput) -> List[RuleHit]:
    """F020: Excessive DOC in hard/extreme material — tool breakage or machine stall."""
    hits: List[RuleHit] = []
    if fi.material_hardness in (MaterialHardness.HARD, MaterialHardness.VERY_HARD, MaterialHardness.EXTREME):
        # In hardwood, DOC > tool_d is dangerous; DOC > 2*tool_d is catastrophic
        max_doc = fi.tool_d * 1.5  # Conservative limit for hardwood
        if fi.stepdown > max_doc:
            hits.append(RuleHit(
                "F020", "RED",
                f"DOC ({fi.stepdown}mm) too aggressive for {fi.material_hardness.value} material; max safe = {max_doc:.1f}mm",
                constraint=f"stepdown <= {max_doc:.1f}"
            ))
    return hits


def rule_red_tool_breakage_doc_ratio(fi: FeasibilityInput) -> List[RuleHit]:
    """F021: DOC:diameter ratio exceeds safe limits — tool breakage risk."""
    hits: List[RuleHit] = []
    if fi.tool_d > 0:
        doc_ratio = fi.stepdown / fi.tool_d
        # Ratio > 5:1 is dangerous; > 10:1 is catastrophic
        if doc_ratio > 5:
            hits.append(RuleHit(
                "F021", "RED",
                f"DOC:diameter ratio ({doc_ratio:.1f}:1) exceeds safe limit (5:1); tool breakage likely",
                constraint="stepdown / tool_d <= 5"
            ))
    return hits


def rule_red_depth_exceeds_material(fi: FeasibilityInput) -> List[RuleHit]:
    """F022: Cutting depth exceeds material thickness — impossible geometry."""
    hits: List[RuleHit] = []
    if fi.material_thickness_mm is not None and fi.geometry_depth_mm is not None:
        if fi.geometry_depth_mm > fi.material_thickness_mm:
            hits.append(RuleHit(
                "F022", "RED",
                f"Pocket depth ({fi.geometry_depth_mm}mm) exceeds material thickness ({fi.material_thickness_mm}mm)",
                constraint=f"geometry_depth_mm <= {fi.material_thickness_mm}"
            ))
    return hits


def rule_red_invalid_geometry_dimensions(fi: FeasibilityInput) -> List[RuleHit]:
    """F023: Zero or negative geometry dimensions — invalid input."""
    hits: List[RuleHit] = []
    if fi.geometry_width_mm is not None and fi.geometry_width_mm <= 0:
        hits.append(RuleHit("F023", "RED", f"Invalid geometry: width must be > 0 (got {fi.geometry_width_mm})"))
    if fi.geometry_length_mm is not None and fi.geometry_length_mm <= 0:
        hits.append(RuleHit("F023", "RED", f"Invalid geometry: length must be > 0 (got {fi.geometry_length_mm})"))
    if fi.geometry_depth_mm is not None and fi.geometry_depth_mm <= 0:
        hits.append(RuleHit("F023", "RED", f"Invalid geometry: depth must be > 0 (got {fi.geometry_depth_mm})"))
    return hits


def rule_red_missing_material(fi: FeasibilityInput) -> List[RuleHit]:
    """F024: No material specified — cannot validate safety."""
    hits: List[RuleHit] = []
    # If hardness is explicitly unknown OR material_id is not set and hardness is None
    if fi.material_hardness == MaterialHardness.UNKNOWN:
        hits.append(RuleHit("F024", "RED", "Material hardness unknown — cannot validate CAM parameters"))
    elif fi.material_id is None and fi.material_hardness is None:
        hits.append(RuleHit("F024", "RED", "No material specified — safety validation requires material info"))
    return hits


def rule_red_tool_larger_than_pocket(fi: FeasibilityInput) -> List[RuleHit]:
    """F025: Tool diameter exceeds geometry width — physically impossible."""
    hits: List[RuleHit] = []
    if fi.geometry_width_mm is not None:
        if fi.tool_d > fi.geometry_width_mm:
            hits.append(RuleHit(
                "F025", "RED",
                f"Tool diameter ({fi.tool_d}mm) exceeds pocket width ({fi.geometry_width_mm}mm); cannot machine",
                constraint=f"tool_d <= {fi.geometry_width_mm}"
            ))
    return hits


def rule_red_chatter_deflection_risk(fi: FeasibilityInput) -> List[RuleHit]:
    """F026: Tool stickout:diameter ratio too high — chatter/deflection risk."""
    hits: List[RuleHit] = []
    if fi.tool_stickout_mm is not None and fi.tool_d > 0:
        stickout_ratio = fi.tool_stickout_mm / fi.tool_d
        # Stickout > 5x diameter is risky; > 10x in hardwood is dangerous
        limit = 5 if fi.material_hardness in (MaterialHardness.HARD, MaterialHardness.VERY_HARD, MaterialHardness.EXTREME) else 8
        if stickout_ratio > limit:
            hits.append(RuleHit(
                "F026", "RED",
                f"Tool stickout:diameter ratio ({stickout_ratio:.1f}:1) exceeds safe limit ({limit}:1); chatter/deflection likely",
                constraint=f"tool_stickout / tool_d <= {limit}"
            ))
    return hits


def rule_red_thermal_risk(fi: FeasibilityInput) -> List[RuleHit]:
    """F027: Resinous material + small tool + no coolant — thermal damage risk."""
    hits: List[RuleHit] = []
    if fi.material_resinous is True:
        # Small tools in resinous material without coolant risk gumming/burning
        if fi.tool_d < 3.0 and fi.coolant_enabled is False:
            hits.append(RuleHit(
                "F027", "RED",
                f"Resinous material + small tool ({fi.tool_d}mm) + no coolant = high thermal/gumming risk",
                constraint="coolant_enabled = true OR tool_d >= 3.0"
            ))
        # Very hard + resinous is dangerous regardless
        if fi.material_hardness in (MaterialHardness.VERY_HARD, MaterialHardness.EXTREME):
            hits.append(RuleHit(
                "F027", "RED",
                f"Resinous + very hard material ({fi.material_hardness.value}) = extreme thermal risk",
            ))
    return hits


def rule_red_structural_wall_failure(fi: FeasibilityInput) -> List[RuleHit]:
    """F028: Wall thickness too thin — structural failure risk."""
    hits: List[RuleHit] = []
    if fi.wall_thickness_mm is not None:
        # Walls < 1mm are fragile; < 0.5mm will likely fail
        if fi.wall_thickness_mm < 1.0:
            hits.append(RuleHit(
                "F028", "RED",
                f"Wall thickness ({fi.wall_thickness_mm}mm) below structural minimum (1mm); likely to break during machining",
                constraint="wall_thickness_mm >= 1.0"
            ))
    return hits


def rule_red_combined_adversarial(fi: FeasibilityInput) -> List[RuleHit]:
    """F029: Multiple unsafe conditions combined — catastrophic risk."""
    hits: List[RuleHit] = []
    risk_factors = 0

    # Check for combined risk factors
    if fi.material_hardness in (MaterialHardness.HARD, MaterialHardness.VERY_HARD, MaterialHardness.EXTREME):
        risk_factors += 1
    if fi.tool_d is not None and fi.tool_d < 3:
        risk_factors += 1
    if fi.stepdown > 5:
        risk_factors += 1
    if fi.stepover > 0.7:
        risk_factors += 1
    if fi.wall_thickness_mm is not None and fi.wall_thickness_mm < 2:
        risk_factors += 1
    if fi.tool_flute_length_mm is not None and fi.geometry_depth_mm is not None:
        if fi.geometry_depth_mm > fi.tool_flute_length_mm:
            risk_factors += 1

    # 3+ risk factors = RED (combined adversarial)
    if risk_factors >= 3:
        hits.append(RuleHit(
            "F029", "RED",
            f"Multiple unsafe conditions detected ({risk_factors} risk factors); combined adversarial parameters",
        ))
    return hits


# =============================================================================
# YELLOW rules (warnings)
# =============================================================================

def rule_yellow_tool_too_large(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.smallest_feature_mm is not None and fi.tool_d > fi.smallest_feature_mm:
        hits.append(
            RuleHit(
                "F010",
                "YELLOW",
                "tool_d exceeds smallest feature; fine details may be unreachable",
                constraint=f"tool_d <= {fi.smallest_feature_mm}",
            )
        )
    return hits


def rule_yellow_feed_z_gt_feed_xy(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.feed_z > fi.feed_xy:
        hits.append(RuleHit("F011", "YELLOW", "feed_z > feed_xy; plunge may be too aggressive"))
    return hits


def rule_yellow_stepdown_large(fi: FeasibilityInput, max_stepdown_mm: float = 3.0) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.stepdown > max_stepdown_mm:
        hits.append(
            RuleHit(
                "F012",
                "YELLOW",
                f"stepdown is high (> {max_stepdown_mm}mm); consider smaller passes",
                constraint=f"stepdown <= {max_stepdown_mm}",
            )
        )
    return hits


def rule_yellow_loop_count_high(fi: FeasibilityInput, max_loops: int = 1000) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.loop_count_hint is not None and fi.loop_count_hint > max_loops:
        hits.append(
            RuleHit(
                "F013",
                "YELLOW",
                f"loop_count is high ({fi.loop_count_hint}); may be slow/heavy",
                constraint=f"loop_count <= {max_loops}",
            )
        )
    return hits


def all_rules(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    # Original RED rules (F001-F007)
    hits += rule_red_invalid_tool(fi)
    hits += rule_red_invalid_stepover(fi)
    hits += rule_red_invalid_stepdown(fi)
    hits += rule_red_invalid_depth(fi)
    hits += rule_red_invalid_safe_z(fi)
    hits += rule_red_no_closed_geometry_hint(fi)

    # Adversarial RED rules (F020-F029)
    hits += rule_red_excessive_doc_hardwood(fi)
    hits += rule_red_tool_breakage_doc_ratio(fi)
    hits += rule_red_depth_exceeds_material(fi)
    hits += rule_red_invalid_geometry_dimensions(fi)
    hits += rule_red_missing_material(fi)
    hits += rule_red_tool_larger_than_pocket(fi)
    hits += rule_red_chatter_deflection_risk(fi)
    hits += rule_red_thermal_risk(fi)
    hits += rule_red_structural_wall_failure(fi)
    hits += rule_red_combined_adversarial(fi)

    # YELLOW rules (F010-F013)
    hits += rule_yellow_tool_too_large(fi)
    hits += rule_yellow_feed_z_gt_feed_xy(fi)
    hits += rule_yellow_stepdown_large(fi)
    hits += rule_yellow_loop_count_high(fi)
    return hits
