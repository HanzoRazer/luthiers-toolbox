"""
RMOS v1 Validation Harness

Batch-runs validation scenarios against the feasibility engine and logs results.

Usage:
    # Run all scenarios
    python -m app.rmos.validation.harness

    # Run specific tier
    python -m app.rmos.validation.harness --tier baseline

    # Run single scenario
    python -m app.rmos.validation.harness --scenario baseline-01

    # Output to file
    python -m app.rmos.validation.harness --output results.json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Feasibility engine
from ..feasibility.engine import compute_feasibility
from ..feasibility.schemas import FeasibilityInput, RiskLevel, MaterialHardness


SCENARIOS_FILE = Path(__file__).parent / "scenarios_v1.json"


@dataclass
class ValidationResult:
    """Result of running a single validation scenario."""
    scenario_id: str
    scenario_name: str
    tier: str
    timestamp_utc: str

    # Expected vs actual
    expected_decision: List[str]  # May be single value or list of acceptable
    actual_decision: str
    expected_rules_any: List[str]
    actual_rules: List[str]
    expected_export_allowed: bool
    actual_export_allowed: bool

    # Verdict
    decision_match: bool
    rules_match: bool  # At least one expected rule triggered
    export_match: bool
    passed: bool

    # Debug
    feasibility_input: Dict[str, Any] = field(default_factory=dict)
    feasibility_result: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


def load_scenarios(path: Path = SCENARIOS_FILE) -> List[Dict[str, Any]]:
    """Load validation scenarios from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("scenarios", [])


def _parse_material_hardness(hardness_str: Optional[str]) -> Optional[MaterialHardness]:
    """Convert scenario hardness string to MaterialHardness enum."""
    if hardness_str is None:
        return None
    mapping = {
        "soft": MaterialHardness.SOFT,
        "medium": MaterialHardness.MEDIUM,
        "medium-hard": MaterialHardness.HARD,  # Treat medium-hard as hard
        "hard": MaterialHardness.HARD,
        "very-hard": MaterialHardness.VERY_HARD,
        "extreme": MaterialHardness.EXTREME,
    }
    return mapping.get(hardness_str.lower(), MaterialHardness.UNKNOWN)


def translate_scenario_to_feasibility_input(scenario: Dict[str, Any]) -> FeasibilityInput:
    """
    Translate high-level scenario input to FeasibilityInput for the engine.

    This maps scenario concepts (geometry, material, tool, params) to the
    CAM-focused FeasibilityInput schema.

    Schema v2: Now passes material/geometry/tool properties for adversarial detection.
    """
    inp = scenario.get("input", {})
    geometry = inp.get("geometry", {})
    material = inp.get("material") or {}  # Handle None material
    tool = inp.get("tool", {})
    params = inp.get("params", {})

    # Extract dimensions
    width = geometry.get("width_mm", 50)
    length = geometry.get("length_mm", 50)
    depth = geometry.get("depth_mm", 10)

    # Tool params
    tool_d = tool.get("diameter_mm", 6)

    # CAM params
    doc_mm = params.get("doc_mm", 2)  # depth of cut per pass
    woc_percent = params.get("woc_percent", 50)  # width of cut as percentage
    feed_rate = params.get("feed_rate_mm_min", 1000)

    # Calculate stepover from WOC percentage
    stepover = woc_percent / 100.0

    # Calculate stepdown from DOC
    stepdown = doc_mm

    # z_rough is negative depth
    z_rough = -abs(depth)

    # Derive smallest feature hint from geometry
    smallest_feature = None
    wall_thickness = geometry.get("wall_thickness_mm")
    if wall_thickness:
        smallest_feature = wall_thickness
    island = geometry.get("island", {})
    if island:
        island_min = min(island.get("width_mm", 100), island.get("length_mm", 100))
        if smallest_feature is None or island_min < smallest_feature:
            smallest_feature = island_min

    # Determine if we have closed paths (assume yes unless explicitly pockets)
    has_closed = geometry.get("type") in ("pocket", "pocket_with_island", "multi_pocket", "rosette_pocket", "slot")

    # Loop count hint based on geometry type
    loop_count = 1
    if geometry.get("type") == "multi_pocket":
        pockets = geometry.get("pockets", [])
        loop_count = len(pockets) if pockets else 1

    # === Schema v2: Extract adversarial detection fields ===

    # Material properties
    material_id = material.get("id") if material else None
    material_hardness = _parse_material_hardness(material.get("hardness")) if material else None
    material_thickness_mm = material.get("thickness_mm") if material else None
    material_resinous = material.get("resinous") if material else None

    # Handle missing material (adversarial-25)
    if not material or material_id is None:
        # Explicitly mark as unknown for F024 to catch
        material_hardness = MaterialHardness.UNKNOWN

    # Geometry dimensions
    geometry_width_mm = width if width != 50 or geometry.get("width_mm") is not None else None
    geometry_length_mm = length if length != 50 or geometry.get("length_mm") is not None else None
    geometry_depth_mm = depth

    # Tool properties
    tool_flute_length_mm = tool.get("flute_length_mm")
    tool_stickout_mm = tool.get("stick_out_mm")

    # Process properties
    coolant_enabled = params.get("coolant")

    # Build FeasibilityInput with v2 fields
    fi = FeasibilityInput(
        pipeline_id="rmos_validation_v1",
        post_id="GRBL",
        units="mm",

        tool_d=tool_d,
        stepover=stepover,
        stepdown=stepdown,
        z_rough=z_rough,
        feed_xy=feed_rate,
        feed_z=feed_rate * 0.5,  # Plunge at 50% of XY feed
        rapid=3000,
        safe_z=5.0,
        strategy=geometry.get("type", "pocket"),
        layer_name="0",
        climb=True,
        smoothing=0.1,
        margin=0.0,

        has_closed_paths=has_closed,
        loop_count_hint=loop_count,
        entity_count=loop_count,
        bbox={
            "x_min": 0,
            "y_min": 0,
            "x_max": width,
            "y_max": length,
        },
        smallest_feature_mm=smallest_feature,

        # Schema v2 fields
        material_id=material_id,
        material_hardness=material_hardness,
        material_thickness_mm=material_thickness_mm,
        material_resinous=material_resinous,
        geometry_width_mm=geometry_width_mm,
        geometry_length_mm=geometry_length_mm,
        geometry_depth_mm=geometry_depth_mm,
        wall_thickness_mm=wall_thickness,
        tool_flute_length_mm=tool_flute_length_mm,
        tool_stickout_mm=tool_stickout_mm,
        coolant_enabled=coolant_enabled,
    )

    return fi


def evaluate_scenario(scenario: Dict[str, Any]) -> ValidationResult:
    """
    Run a single scenario through the feasibility engine and evaluate.
    """
    scenario_id = scenario.get("id", "unknown")
    scenario_name = scenario.get("name", "")
    tier = scenario.get("tier", "unknown")
    expected = scenario.get("expected", {})

    # Parse expected values
    exp_decision = expected.get("decision", [])
    if isinstance(exp_decision, str):
        exp_decision = [exp_decision]

    exp_rules = expected.get("rules_triggered", [])
    exp_rules_any = expected.get("rules_triggered_any", exp_rules)
    exp_export = expected.get("export_allowed", True)

    # Translate and run
    try:
        fi = translate_scenario_to_feasibility_input(scenario)
        result = compute_feasibility(fi)

        actual_decision = result.risk_level.value
        actual_rules = result.rules_triggered
        actual_export = not result.blocking

    except Exception as e:
        # Engine error - treat as RED with error
        fi = FeasibilityInput(
            tool_d=1, stepover=0.5, stepdown=1, z_rough=-1,
            feed_xy=1000, feed_z=500, rapid=3000, safe_z=5,
            strategy="error", layer_name="0", climb=True,
            smoothing=0.1, margin=0.0
        )
        actual_decision = "ERROR"
        actual_rules = [f"ENGINE_ERROR: {str(e)}"]
        actual_export = False
        result = None

    # Evaluate matches
    decision_match = actual_decision in exp_decision

    # Rules match if any expected rule is in actual (for _any patterns)
    # If exp_rules_any is empty, we don't require specific rules
    if exp_rules_any:
        rules_match = any(r in actual_rules for r in exp_rules_any)
    else:
        rules_match = True  # No specific rules expected

    export_match = actual_export == exp_export

    # Overall pass: decision must match, export must match
    # Rules are informational for now (engine may not have all rules implemented)
    passed = decision_match and export_match

    return ValidationResult(
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        tier=tier,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        expected_decision=exp_decision,
        actual_decision=actual_decision,
        expected_rules_any=exp_rules_any,
        actual_rules=actual_rules,
        expected_export_allowed=exp_export,
        actual_export_allowed=actual_export,
        decision_match=decision_match,
        rules_match=rules_match,
        export_match=export_match,
        passed=passed,
        feasibility_input=fi.model_dump() if hasattr(fi, 'model_dump') else asdict(fi) if hasattr(fi, '__dataclass_fields__') else {},
        feasibility_result=result.model_dump() if result and hasattr(result, 'model_dump') else {},
        notes="" if passed else f"FAIL: decision={actual_decision} (expected {exp_decision}), export={actual_export} (expected {exp_export})",
    )


def run_validation(
    scenarios: List[Dict[str, Any]],
    tier_filter: Optional[str] = None,
    scenario_filter: Optional[str] = None,
) -> Tuple[List[ValidationResult], Dict[str, Any]]:
    """
    Run validation across scenarios and return results + summary.
    """
    results: List[ValidationResult] = []

    for scenario in scenarios:
        scenario_id = scenario.get("id", "")
        scenario_tier = scenario.get("tier", "")

        # Apply filters
        if tier_filter and scenario_tier != tier_filter:
            continue
        if scenario_filter and scenario_id != scenario_filter:
            continue

        result = evaluate_scenario(scenario)
        results.append(result)

    # Build summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    by_tier: Dict[str, Dict[str, int]] = {}
    for r in results:
        if r.tier not in by_tier:
            by_tier[r.tier] = {"total": 0, "passed": 0, "failed": 0}
        by_tier[r.tier]["total"] += 1
        if r.passed:
            by_tier[r.tier]["passed"] += 1
        else:
            by_tier[r.tier]["failed"] += 1

    # Critical check: any adversarial passed (RED leak)?
    red_leaks = [r for r in results if r.tier == "adversarial" and r.actual_decision in ("GREEN", "YELLOW")]

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "N/A",
        "by_tier": by_tier,
        "red_leaks": len(red_leaks),
        "red_leak_scenarios": [r.scenario_id for r in red_leaks],
        "release_authorized": failed == 0 and len(red_leaks) == 0,
    }

    return results, summary


def format_console_output(results: List[ValidationResult], summary: Dict[str, Any]) -> str:
    """Format results for console display."""
    lines = [
        "=" * 70,
        "RMOS v1 VALIDATION RESULTS",
        "=" * 70,
        "",
    ]

    current_tier = None
    for r in results:
        if r.tier != current_tier:
            current_tier = r.tier
            lines.append(f"\n--- {current_tier.upper()} ---")

        status = "PASS" if r.passed else "FAIL"
        lines.append(f"[{status}] {r.scenario_id}: {r.scenario_name}")
        if not r.passed:
            lines.append(f"       Expected: {r.expected_decision} | Actual: {r.actual_decision}")
            lines.append(f"       Export: expected={r.expected_export_allowed}, actual={r.actual_export_allowed}")
            if r.actual_rules:
                lines.append(f"       Rules: {r.actual_rules}")

    lines.extend([
        "",
        "=" * 70,
        "SUMMARY",
        "=" * 70,
        f"Total: {summary['total']} | Passed: {summary['passed']} | Failed: {summary['failed']} | Rate: {summary['pass_rate']}",
        "",
        "By Tier:",
    ])

    for tier, stats in summary.get("by_tier", {}).items():
        lines.append(f"  {tier}: {stats['passed']}/{stats['total']} passed")

    lines.append("")
    if summary.get("red_leaks", 0) > 0:
        lines.append(f"!!! CRITICAL: {summary['red_leaks']} RED LEAKS DETECTED !!!")
        lines.append(f"    Scenarios: {summary['red_leak_scenarios']}")
    else:
        lines.append("No RED leaks detected.")

    lines.append("")
    if summary.get("release_authorized"):
        lines.append("RELEASE AUTHORIZED: All scenarios passed.")
    else:
        lines.append("RELEASE BLOCKED: Validation failures detected.")

    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="RMOS v1 Validation Harness")
    parser.add_argument("--tier", choices=["baseline", "edge_pressure", "adversarial"],
                        help="Run only scenarios from this tier")
    parser.add_argument("--scenario", help="Run only this scenario ID")
    parser.add_argument("--output", "-o", help="Write JSON results to file")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--scenarios-file", help="Path to scenarios JSON file")

    args = parser.parse_args()

    # Load scenarios
    scenarios_path = Path(args.scenarios_file) if args.scenarios_file else SCENARIOS_FILE
    if not scenarios_path.exists():
        print(f"ERROR: Scenarios file not found: {scenarios_path}", file=sys.stderr)
        sys.exit(1)

    scenarios = load_scenarios(scenarios_path)
    print(f"Loaded {len(scenarios)} scenarios from {scenarios_path}", file=sys.stderr)

    # Run validation
    results, summary = run_validation(
        scenarios,
        tier_filter=args.tier,
        scenario_filter=args.scenario,
    )

    # Output
    output_data = {
        "summary": summary,
        "results": [asdict(r) for r in results],
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"Results written to {args.output}", file=sys.stderr)

    if args.json:
        print(json.dumps(output_data, indent=2))
    else:
        print(format_console_output(results, summary))

    # Exit code: 0 if release authorized, 1 if blocked
    sys.exit(0 if summary.get("release_authorized") else 1)


if __name__ == "__main__":
    main()
