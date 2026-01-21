# RMOS Feasibility Rules Reference v1

> **Status**: RELEASE AUTHORIZED
> **Validation**: 30/30 scenarios passed (100%)
> **RED Leaks**: 0
> **Last Updated**: 2026-01-21

This document is the authoritative reference for all feasibility rules in RMOS v1. Each rule has a unique ID that appears in `rules_triggered` arrays in API responses.

---

## Rule Levels

| Level | Meaning | Export Allowed |
|-------|---------|----------------|
| **RED** | Blocking — unsafe to proceed | No |
| **YELLOW** | Warning — proceed with caution | Yes |
| **GREEN** | Safe — no issues detected | Yes |

---

## Core Validation Rules (F001-F007)

### F001: Invalid Tool Diameter
- **Level**: RED
- **Trigger**: `tool_d <= 0`
- **Message**: "tool_d must be > 0"
- **Fix**: Specify a valid tool diameter in mm

### F002: Invalid Stepover
- **Level**: RED
- **Trigger**: `stepover <= 0` or `stepover > 0.95` (or > 1.0 for slots)
- **Message**: "stepover must be in (0, 0.95]"
- **Fix**: Use stepover between 1% and 95% (100% allowed for slotting)

### F003: Invalid Stepdown
- **Level**: RED
- **Trigger**: `stepdown <= 0`
- **Message**: "stepdown must be > 0"
- **Fix**: Specify a positive depth of cut per pass

### F004: Invalid Cutting Depth
- **Level**: RED
- **Trigger**: `z_rough >= 0`
- **Message**: "z_rough must be negative (cutting depth)"
- **Fix**: z_rough should be negative (e.g., -10 for 10mm deep)

### F005: Invalid Safe Z
- **Level**: RED
- **Trigger**: `safe_z <= 0`
- **Message**: "safe_z must be > 0"
- **Fix**: Set safe_z to a positive clearance height

### F006: No Closed Paths
- **Level**: RED
- **Trigger**: `has_closed_paths == false`
- **Message**: "DXF contains no closed paths on selected layer"
- **Fix**: Ensure DXF has closed polylines on the target layer

### F007: No Closed Loops
- **Level**: RED
- **Trigger**: `loop_count_hint <= 0`
- **Message**: "No closed loops detected in DXF (preflight)"
- **Fix**: Check DXF geometry — pockets require closed boundaries

---

## Basic Warning Rules (F010-F013)

### F010: Tool Too Large for Feature
- **Level**: YELLOW
- **Trigger**: `tool_d > smallest_feature_mm`
- **Message**: "tool_d exceeds smallest feature; fine details may be unreachable"
- **Fix**: Use a smaller tool or accept that fine details will be skipped

### F011: Aggressive Plunge Feed
- **Level**: YELLOW
- **Trigger**: `feed_z > feed_xy`
- **Message**: "feed_z > feed_xy; plunge may be too aggressive"
- **Fix**: Reduce plunge feed rate to ≤ XY feed rate

### F012: Large Stepdown
- **Level**: YELLOW
- **Trigger**: `stepdown > 3.0mm`
- **Message**: "stepdown is high (> 3mm); consider smaller passes"
- **Fix**: Reduce DOC for better chip evacuation and tool life

### F013: High Loop Count
- **Level**: YELLOW
- **Trigger**: `loop_count_hint > 1000`
- **Message**: "loop_count is high; may be slow/heavy"
- **Fix**: Consider simplifying geometry or splitting into multiple jobs

---

## Adversarial Blocking Rules (F020-F029)

These rules catch dangerous parameter combinations that could cause tool breakage, machine damage, or operator injury.

### F020: Excessive DOC in Hardwood
- **Level**: RED
- **Trigger**: `material_hardness in (hard, very-hard, extreme)` AND `stepdown > tool_d * 1.5`
- **Message**: "DOC too aggressive for hard material"
- **Fix**: Reduce stepdown to ≤ 1.5x tool diameter for hardwoods

### F021: Tool Breakage Risk (DOC:Diameter Ratio)
- **Level**: RED
- **Trigger**: `stepdown / tool_d > 5`
- **Message**: "DOC:diameter ratio exceeds safe limit (5:1); tool breakage likely"
- **Fix**: Reduce stepdown or use a larger tool

### F022: Depth Exceeds Material Thickness
- **Level**: RED
- **Trigger**: `geometry_depth_mm > material_thickness_mm`
- **Message**: "Pocket depth exceeds material thickness"
- **Fix**: Reduce pocket depth or use thicker stock

### F023: Invalid Geometry Dimensions
- **Level**: RED
- **Trigger**: `geometry_width_mm <= 0` OR `geometry_length_mm <= 0` OR `geometry_depth_mm <= 0`
- **Message**: "Invalid geometry: dimension must be > 0"
- **Fix**: Correct the geometry dimensions

### F024: Missing Material Specification
- **Level**: RED
- **Trigger**: `material_id == null` AND `material_hardness == null`
- **Message**: "No material specified — safety validation requires material info"
- **Fix**: Specify material type and hardness

### F025: Tool Larger Than Pocket
- **Level**: RED
- **Trigger**: `tool_d > geometry_width_mm`
- **Message**: "Tool diameter exceeds pocket width; cannot machine"
- **Fix**: Use a smaller tool that fits the pocket

### F026: Chatter/Deflection Risk
- **Level**: RED
- **Trigger**: `tool_stickout_mm / tool_d > 5` (hardwood) or `> 8` (softwood)
- **Message**: "Tool stickout:diameter ratio exceeds safe limit; chatter/deflection likely"
- **Fix**: Reduce tool stickout or use a larger diameter tool

### F027: Thermal Risk
- **Level**: RED
- **Trigger**: `material_resinous == true` AND (`tool_d < 3.0` AND `coolant_enabled == false`) OR `material_hardness in (very-hard, extreme)`
- **Message**: "Resinous material + small tool + no coolant = high thermal/gumming risk"
- **Fix**: Enable coolant/air blast, use larger tool, or choose different material

### F028: Structural Wall Failure
- **Level**: RED
- **Trigger**: `wall_thickness_mm < 1.0`
- **Message**: "Wall thickness below structural minimum (1mm); likely to break"
- **Fix**: Increase wall thickness or reduce pocket depth

### F029: Combined Adversarial
- **Level**: RED
- **Trigger**: 3+ risk factors combined (hard material, small tool, high DOC, high stepover, thin wall, depth > flute length)
- **Message**: "Multiple unsafe conditions detected; combined adversarial parameters"
- **Fix**: Address individual risk factors

---

## Edge Pressure Warning Rules (F030-F040)

### F030: Deep Pocket
- **Level**: YELLOW
- **Trigger**: `geometry_depth_mm > tool_d * 2`
- **Message**: "Deep pocket: depth is Nx tool diameter; requires care"
- **Fix**: Consider multiple depth passes; ensure chip evacuation

### F031: Moderate DOC in Hardwood
- **Level**: YELLOW
- **Trigger**: `material_hardness in (hard, very-hard, extreme)` AND `stepdown > tool_d * 0.5` AND `stepdown <= tool_d * 1.5`
- **Message**: "DOC is aggressive for hard material; consider lighter passes"
- **Fix**: Reduce DOC to ≤ 0.5x tool diameter for best results

### F032: Small Tool Warning
- **Level**: YELLOW
- **Trigger**: `tool_d < 2.0mm`
- **Message**: "Small tool — higher breakage risk; use conservative feeds/speeds"
- **Fix**: Reduce feeds and speeds; monitor closely

### F033: Depth Exceeds Flute Length
- **Level**: RED
- **Trigger**: `geometry_depth_mm > tool_flute_length_mm`
- **Message**: "Pocket depth exceeds flute length; shank will contact material"
- **Fix**: Use a tool with longer flutes or reduce pocket depth

### F034: Narrow Slot Aspect Ratio
- **Level**: YELLOW
- **Trigger**: `strategy == "slot"` AND `geometry_depth_mm / geometry_width_mm > 2`
- **Message**: "Narrow slot: depth:width ratio is high; chip evacuation may be difficult"
- **Fix**: Use peck drilling/ramping; ensure air blast

### F035: Aggressive Stepover
- **Level**: YELLOW
- **Trigger**: `stepover > 0.7` AND `strategy != "slot"`
- **Message**: "Stepover is aggressive; consider lighter passes for finish quality"
- **Fix**: Reduce stepover to ≤ 70% for better surface finish

### F036: Thin Wall Warning
- **Level**: YELLOW
- **Trigger**: `wall_thickness_mm >= 1.0` AND `wall_thickness_mm < 2.0`
- **Message**: "Thin wall — handle with care; reduce feeds near edges"
- **Fix**: Reduce feed rates near thin walls; consider climb milling

### F037: Combined Edge Pressure
- **Level**: YELLOW
- **Trigger**: 2+ edge factors (hard material, deep pocket, high stepover, high stepdown, thin wall)
- **Message**: "Multiple edge conditions detected; elevated risk — proceed carefully"
- **Fix**: Address individual factors; increase monitoring

### F038: Thin Floor
- **Level**: YELLOW
- **Trigger**: `floor_thickness_mm < 2.0`
- **Message**: "Thin floor — risk of punching through; verify depth carefully"
- **Fix**: Verify material thickness; use depth stop if available

### F039: Complex Geometry
- **Level**: YELLOW
- **Trigger**: `geometry_complex == true` (L-shapes, T-shapes, multiple islands)
- **Message**: "Complex geometry — verify toolpaths carefully"
- **Fix**: Review simulation; check for gouging or missed areas

### F040: Feed Override Warning
- **Level**: YELLOW
- **Trigger**: `feed_override_percent > 120` OR `feed_override_percent < 80`
- **Message**: "Feed override applied — verify settings"
- **Fix**: Review override reason; monitor operation

---

## Severe Combined Pressure (F041)

### F041: Severe Combined Pressure
- **Level**: RED
- **Trigger**: 3+ severe factors:
  - Hard/very-hard/extreme material
  - Depth ≥ 3x tool diameter
  - Stepover ≥ 60%
  - Stepdown ≥ 3mm
  - Wall thickness ≤ 3mm
  - Complex geometry
- **Message**: "Severe combined pressure — unsafe without manual review"
- **Fix**: Reduce at least 2 risk factors before proceeding

---

## API Usage

```python
from app.rmos.feasibility.engine import compute_feasibility
from app.rmos.feasibility.schemas import FeasibilityInput

result = compute_feasibility(FeasibilityInput(
    tool_d=6.0,
    stepover=0.5,
    stepdown=3.0,
    # ... other params
))

# Check result
if result.risk_level == "RED":
    print("BLOCKED:", result.blocking_reasons)
    print("Rules:", result.rules_triggered)  # e.g., ["F020", "F021"]
elif result.risk_level == "YELLOW":
    print("WARNINGS:", result.warnings)
    print("Rules:", result.rules_triggered)
else:
    print("GREEN: Safe to proceed")
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-01-21 | Initial release — 22 rules, 30/30 validation |

