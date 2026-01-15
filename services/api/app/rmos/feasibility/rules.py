from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .schemas import FeasibilityInput


@dataclass(frozen=True)
class RuleHit:
    level: str  # "RED" or "YELLOW"
    message: str
    constraint: Optional[str] = None


def rule_red_invalid_tool(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.tool_d <= 0:
        hits.append(RuleHit("RED", "tool_d must be > 0"))
    return hits


def rule_red_invalid_stepover(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.stepover <= 0 or fi.stepover > 0.95:
        hits.append(RuleHit("RED", "stepover must be in (0, 0.95]"))
    return hits


def rule_red_invalid_stepdown(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.stepdown <= 0:
        hits.append(RuleHit("RED", "stepdown must be > 0"))
    return hits


def rule_red_invalid_depth(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.z_rough >= 0:
        hits.append(RuleHit("RED", "z_rough must be negative (cutting depth)"))
    return hits


def rule_red_invalid_safe_z(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.safe_z <= 0:
        hits.append(RuleHit("RED", "safe_z must be > 0"))
    return hits


def rule_red_no_closed_geometry_hint(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    # We only enforce this if we actually know it from preflight.
    if fi.has_closed_paths is False:
        hits.append(RuleHit("RED", "DXF contains no closed paths on selected layer"))
    # Optional hint: if loop_count_hint is known and == 0, treat as RED
    if fi.loop_count_hint is not None and fi.loop_count_hint <= 0:
        hits.append(RuleHit("RED", "No closed loops detected in DXF (preflight)"))
    return hits


def rule_yellow_tool_too_large(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.smallest_feature_mm is not None and fi.tool_d > fi.smallest_feature_mm:
        hits.append(
            RuleHit(
                "YELLOW",
                "tool_d exceeds smallest feature; fine details may be unreachable",
                constraint=f"tool_d <= {fi.smallest_feature_mm}",
            )
        )
    return hits


def rule_yellow_feed_z_gt_feed_xy(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.feed_z > fi.feed_xy:
        hits.append(RuleHit("YELLOW", "feed_z > feed_xy; plunge may be too aggressive"))
    return hits


def rule_yellow_stepdown_large(fi: FeasibilityInput, max_stepdown_mm: float = 3.0) -> List[RuleHit]:
    hits: List[RuleHit] = []
    if fi.stepdown > max_stepdown_mm:
        hits.append(
            RuleHit(
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
                "YELLOW",
                f"loop_count is high ({fi.loop_count_hint}); may be slow/heavy",
                constraint=f"loop_count <= {max_loops}",
            )
        )
    return hits


def all_rules(fi: FeasibilityInput) -> List[RuleHit]:
    hits: List[RuleHit] = []
    hits += rule_red_invalid_tool(fi)
    hits += rule_red_invalid_stepover(fi)
    hits += rule_red_invalid_stepdown(fi)
    hits += rule_red_invalid_depth(fi)
    hits += rule_red_invalid_safe_z(fi)
    hits += rule_red_no_closed_geometry_hint(fi)

    hits += rule_yellow_tool_too_large(fi)
    hits += rule_yellow_feed_z_gt_feed_xy(fi)
    hits += rule_yellow_stepdown_large(fi)
    hits += rule_yellow_loop_count_high(fi)
    return hits
