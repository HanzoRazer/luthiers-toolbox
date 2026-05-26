#!/usr/bin/env python3
"""
CAM Assist Review Packet Generator

Generates a human-readable Markdown review packet from a validated
strategy package JSON file.

This generator is non-executing — it produces advisory documentation only.
It does not generate G-code, toolpaths, or machine instructions.

Usage:
    python scripts/generate_review_packet.py <strategy_json>
    python scripts/generate_review_packet.py examples/valid/fret_slot_strategy.json
    python scripts/generate_review_packet.py examples/valid/fret_slot_strategy.json --out /tmp/review.md

Exit codes:
    0 — Review packet generated successfully
    1 — Strategy validation failed
    2 — File/read/write error
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Import validation functions from A2 validator
sys.path.insert(0, str(Path(__file__).parent))
from validate_strategy_package import (
    validate_strategy_package,
    load_json,
    ValidationResult,
)


NON_EXECUTION_NOTICE = """
> **NON-EXECUTION NOTICE**
>
> This review packet is advisory only.
> It does not authorize machine execution.
> It does not generate G-code.
> It does not replace operator judgment.
> Human review and downstream CAM verification are required before machining.
"""


def generate_review_packet(data: dict) -> str:
    """Generate a Markdown review packet from validated strategy data."""
    lines: list[str] = []

    # Title
    op_type = data.get("operation_intent", {}).get("operation_type", "Unknown")
    strategy_id = data.get("strategy_id", "unknown")
    lines.append(f"# {op_type.replace('_', ' ').title()} Strategy Review Packet")
    lines.append("")
    lines.append(f"**Strategy ID:** `{strategy_id}`")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append("")

    # Section 1: Non-Execution Notice
    lines.append("---")
    lines.append("")
    lines.append("## 1. Non-Execution Notice")
    lines.append("")
    lines.append(NON_EXECUTION_NOTICE)
    lines.append("")

    # Section 2: Strategy Identity
    lines.append("---")
    lines.append("")
    lines.append("## 2. Strategy Identity")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Strategy ID | `{strategy_id}` |")
    lines.append(f"| Strategy Version | {data.get('strategy_version', 'N/A')} |")
    lines.append(f"| Approval State | {data.get('approval_state', 'N/A')} |")

    provenance = data.get("provenance", {})
    lines.append(f"| Source Spec ID | {provenance.get('source_spec_id', 'N/A')} |")
    lines.append(f"| CAM Assist Version | {provenance.get('cam_assist_version', 'N/A')} |")
    lines.append(f"| Created At | {provenance.get('created_at', 'N/A')} |")
    lines.append(f"| Created By | {provenance.get('created_by', 'N/A')} |")
    lines.append("")

    # Section 3: Instrument Context
    lines.append("---")
    lines.append("")
    lines.append("## 3. Instrument Context")
    lines.append("")
    source_spec = provenance.get("source_spec_id")
    if source_spec:
        lines.append(f"**Source Specification:** `{source_spec}`")
    else:
        lines.append("*Not specified in strategy package.*")
    lines.append("")

    # Section 4: Material Context
    lines.append("---")
    lines.append("")
    lines.append("## 4. Material Context")
    lines.append("")
    material = data.get("material_context", {})
    if material:
        lines.append(f"| Property | Value |")
        lines.append(f"|----------|-------|")
        lines.append(f"| Material Class | {material.get('material_class', 'N/A')} |")
        lines.append(f"| Species | {material.get('species', 'N/A')} |")
        lines.append(f"| Janka Hardness | {material.get('hardness_janka', 'N/A')} |")
        lines.append(f"| Grain Direction | {material.get('grain_direction', 'N/A')} |")
        if material.get("notes"):
            lines.append(f"| Notes | {material.get('notes')} |")
    else:
        lines.append("*Not specified in strategy package.*")
    lines.append("")

    # Section 5: Operation Intent
    lines.append("---")
    lines.append("")
    lines.append("## 5. Operation Intent")
    lines.append("")
    op_intent = data.get("operation_intent", {})
    lines.append(f"| Property | Value |")
    lines.append(f"|----------|-------|")
    lines.append(f"| Operation Type | {op_intent.get('operation_type', 'N/A')} |")
    lines.append(f"| Target Feature | {op_intent.get('target_feature', 'N/A')} |")
    lines.append(f"| Cut Intent | {op_intent.get('cut_intent', 'N/A')} |")
    non_exec = op_intent.get('non_execution_declaration')
    lines.append(f"| Non-Execution Declaration | **{non_exec}** |")
    lines.append("")

    # Section 6: Coordinate Frame
    lines.append("---")
    lines.append("")
    lines.append("## 6. Coordinate Frame")
    lines.append("")
    coord = data.get("coordinate_frame", {})
    lines.append(f"| Axis | Definition |")
    lines.append(f"|------|------------|")
    lines.append(f"| Origin | {coord.get('origin', 'N/A')} |")
    lines.append(f"| X-Axis | {coord.get('x_axis', 'N/A')} |")
    lines.append(f"| Y-Axis | {coord.get('y_axis', 'N/A')} |")
    lines.append(f"| Z-Axis | {coord.get('z_axis', 'N/A')} |")
    datum = coord.get("datum_point", {})
    if datum:
        lines.append(f"| Datum Point | ({datum.get('x', 0)}, {datum.get('y', 0)}, {datum.get('z', 0)}) |")
    lines.append("")
    lines.append(f"**Units:** {data.get('units', 'N/A')}")
    lines.append("")

    # Section 7: Fret Slot Summary
    lines.append("---")
    lines.append("")
    lines.append("## 7. Fret Slot Summary")
    lines.append("")

    positions = data.get("positions", [])
    calc_basis = data.get("calculation_basis", {})
    operation = data.get("operation", {})
    params = operation.get("parameters", {})
    tool = operation.get("tool", {})

    # Summary stats
    fret_count = len(positions)
    scale_length = calc_basis.get("scale_length", "N/A")
    temperament = calc_basis.get("temperament", "N/A")

    first_fret = positions[0] if positions else {}
    fret_12 = next((p for p in positions if p.get("fret") == 12), {})
    last_fret = positions[-1] if positions else {}

    lines.append("### Overview")
    lines.append("")
    lines.append(f"| Property | Value |")
    lines.append(f"|----------|-------|")
    lines.append(f"| Fret Count | {fret_count} |")
    lines.append(f"| Scale Length | {scale_length} {data.get('units', '')} |")
    lines.append(f"| Temperament | {temperament} |")
    lines.append(f"| Slot Width | {tool.get('diameter', 'N/A')} {data.get('units', '')} |")
    lines.append(f"| Slot Depth | {params.get('depth', 'N/A')} {data.get('units', '')} |")
    lines.append("")

    lines.append("### Key Positions")
    lines.append("")
    lines.append(f"| Fret | Distance from Nut |")
    lines.append(f"|------|-------------------|")
    if first_fret:
        lines.append(f"| 1 (first) | {first_fret.get('distance_from_nut', 'N/A')} {data.get('units', '')} |")
    if fret_12:
        lines.append(f"| 12 (octave) | {fret_12.get('distance_from_nut', 'N/A')} {data.get('units', '')} |")
    if last_fret and last_fret.get("fret") != 12:
        lines.append(f"| {last_fret.get('fret', 'N/A')} (last) | {last_fret.get('distance_from_nut', 'N/A')} {data.get('units', '')} |")
    lines.append("")

    # Full position table
    if positions:
        lines.append("### All Fret Positions")
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Click to expand full position table</summary>")
        lines.append("")
        lines.append(f"| Fret | Distance from Nut ({data.get('units', '')}) |")
        lines.append(f"|------|---------------------|")
        for pos in positions:
            lines.append(f"| {pos.get('fret', 'N/A')} | {pos.get('distance_from_nut', 'N/A')} |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # Calculation basis
    if calc_basis.get("formula"):
        lines.append("### Calculation Basis")
        lines.append("")
        lines.append(f"**Formula:** `{calc_basis.get('formula')}`")
        lines.append("")

    # Section 8: Tool Assumptions
    lines.append("---")
    lines.append("")
    lines.append("## 8. Tool Assumptions")
    lines.append("")
    if tool:
        lines.append(f"| Property | Value |")
        lines.append(f"|----------|-------|")
        lines.append(f"| Tool Type | {tool.get('tool_type', 'N/A')} |")
        lines.append(f"| Reference Type | {tool.get('reference_type', 'N/A')} |")
        lines.append(f"| Diameter | {tool.get('diameter', 'N/A')} {data.get('units', '')} |")
        lines.append(f"| Description | {tool.get('description', 'N/A')} |")
        lines.append("")

        req_dims = tool.get("required_dimensions", {})
        if req_dims:
            lines.append("**Required Dimensions:**")
            for key, val in req_dims.items():
                lines.append(f"- {key}: {val}")
            lines.append("")

        alternatives = tool.get("alternatives", [])
        if alternatives:
            lines.append("**Alternative Tools:**")
            for alt in alternatives:
                lines.append(f"- {alt}")
            lines.append("")
    else:
        lines.append("*Not specified in strategy package.*")
        lines.append("")

    # Section 9: Workholding Assumptions
    lines.append("---")
    lines.append("")
    lines.append("## 9. Workholding Assumptions")
    lines.append("")
    lines.append("*Not specified in strategy package.*")
    lines.append("")
    lines.append("> **Operator Note:** Verify adequate workholding before machining.")
    lines.append("> Fretboard stock must be securely clamped to prevent movement during slot cutting.")
    lines.append("")

    # Section 10: Safety Boundary
    lines.append("---")
    lines.append("")
    lines.append("## 10. Safety Boundary")
    lines.append("")
    safety = data.get("safety_boundary", {})
    lines.append(f"| Property | Value |")
    lines.append(f"|----------|-------|")
    lines.append(f"| Non-Execution Declaration | **{safety.get('non_execution_declaration', 'N/A')}** |")
    lines.append(f"| Human Review Required | **{safety.get('human_review_required', 'N/A')}** |")
    lines.append(f"| Max Depth | {safety.get('max_depth_inches', 'N/A')} {data.get('units', '')} |")
    lines.append(f"| Tool Diameter | {safety.get('tool_diameter_inches', 'N/A')} {data.get('units', '')} |")

    exec_claim = safety.get("execution_authority_claim")
    if exec_claim is not None:
        lines.append(f"| Execution Authority Claim | **{exec_claim}** |")
    lines.append("")

    # Section 11: Human Review Requirements
    lines.append("---")
    lines.append("")
    lines.append("## 11. Human Review Requirements")
    lines.append("")
    lines.append("Before proceeding to CAM or machining, the operator must verify:")
    lines.append("")
    lines.append("- [ ] Fret positions match instrument specification")
    lines.append("- [ ] Scale length is correct for target instrument")
    lines.append("- [ ] Slot width matches intended fret wire tang")
    lines.append("- [ ] Slot depth is appropriate for fretboard thickness")
    lines.append("- [ ] Material assumptions match actual workpiece")
    lines.append("- [ ] Tool selection is appropriate and available")
    lines.append("- [ ] Coordinate frame matches machine setup")
    lines.append("- [ ] Workholding is adequate and secure")
    lines.append("- [ ] Safety boundaries are understood")
    lines.append("")

    # Section 12: Warnings and Failure Modes
    lines.append("---")
    lines.append("")
    lines.append("## 12. Warnings and Failure Modes")
    lines.append("")

    warnings = data.get("warnings", [])
    if warnings:
        lines.append("### Strategy Warnings")
        lines.append("")
        for w in warnings:
            level = w.get("level", "INFO")
            msg = w.get("message", "No message")
            lines.append(f"- **[{level}]** {msg}")
        lines.append("")
    else:
        lines.append("*No warnings in strategy package.*")
        lines.append("")

    lines.append("### Potential Failure Modes")
    lines.append("")
    lines.append("- **Slot too shallow:** Fret wire may not seat properly")
    lines.append("- **Slot too deep:** May intersect truss rod channel or weaken fretboard")
    lines.append("- **Slot too narrow:** Fret wire will not fit")
    lines.append("- **Slot too wide:** Fret wire will be loose, poor sustain")
    lines.append("- **Position error:** Intonation problems, unplayable instrument")
    lines.append("- **Tearout:** Material damage from improper feed/speed or grain direction")
    lines.append("")

    # Section 13: Operator Sign-Off
    lines.append("---")
    lines.append("")
    lines.append("## 13. Operator Sign-Off")
    lines.append("")
    lines.append("I have reviewed this strategy package and confirm:")
    lines.append("")
    lines.append("- [ ] All parameters match the intended instrument specification")
    lines.append("- [ ] I understand this is advisory only and does not authorize execution")
    lines.append("- [ ] I will perform independent verification before machining")
    lines.append("- [ ] I accept responsibility for downstream CAM and execution decisions")
    lines.append("")
    lines.append("**Operator Name:** _________________________________")
    lines.append("")
    lines.append("**Date:** _________________________________")
    lines.append("")
    lines.append("**Signature:** _________________________________")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*This review packet was generated by CAM Assist Blueprint.*")
    lines.append("*It is advisory only and does not constitute execution authority.*")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a review packet from a validated strategy package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "strategy_json",
        type=Path,
        help="Path to the strategy package JSON file",
    )
    parser.add_argument(
        "--out", "-o",
        type=Path,
        default=None,
        help="Output path for review packet (default: <input>_review_packet.md)",
    )

    args = parser.parse_args()
    input_path: Path = args.strategy_json

    # Determine output path
    if args.out:
        output_path = args.out
    else:
        output_path = input_path.with_name(f"{input_path.stem}_review_packet.md")

    # Load JSON
    data, load_error = load_json(input_path)
    if load_error:
        print(f"FAIL: {load_error}", file=sys.stderr)
        return 2

    # Validate using A2 validator
    result = validate_strategy_package(data)
    if not result.valid:
        print("FAIL: strategy validation failed", file=sys.stderr)
        for error in result.errors:
            print(f"  [ERR] {error}", file=sys.stderr)
        return 1

    # Additional check: ensure non_execution_declaration is true
    op_intent = data.get("operation_intent", {})
    safety = data.get("safety_boundary", {})

    if op_intent.get("non_execution_declaration") is not True:
        print(
            "FAIL: operation_intent.non_execution_declaration must be true",
            file=sys.stderr
        )
        return 1

    if safety.get("non_execution_declaration") is not True:
        print(
            "FAIL: safety_boundary.non_execution_declaration must be true",
            file=sys.stderr
        )
        return 1

    if safety.get("execution_authority_claim") is True:
        print(
            "FAIL: execution_authority_claim must be false or absent",
            file=sys.stderr
        )
        return 1

    # Generate review packet
    try:
        packet_content = generate_review_packet(data)
    except Exception as e:
        print(f"FAIL: error generating review packet: {e}", file=sys.stderr)
        return 2

    # Write output
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(packet_content)
    except Exception as e:
        print(f"FAIL: error writing output: {e}", file=sys.stderr)
        return 2

    print(f"PASS: review packet generated: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
