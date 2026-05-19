# CAM Tool Library Standard

**Date:** 2026-05-10  
**Status:** ARCHITECTURAL DEFINITION  
**Dev Order:** 6A  
**Scope:** Tooling abstraction for export objects and postprocessors

---

## Purpose

This document defines the **Tool Library** — the abstraction layer for cutting tools used in export objects and validated by postprocessors.

---

## Design Principles

1. **Tool as data** — Tools are declarative specifications, not code
2. **Geometry-first** — Physical dimensions are required; material/coating are metadata
3. **Operation-aware** — Tools declare which operation types they support
4. **Validation-friendly** — Tool specs support machine compatibility checks
5. **User-extensible** — Users can add custom tools

---

## Tool Schema

### Top-Level Structure

```json
{
  "schema_version": "1.0.0",
  "tool_id": "nut_slot_saw_056",
  "tool_name": "Nut Slot Saw 0.56mm",
  
  "tool_type": "slot_saw",
  "geometry": { ... },
  "material": { ... },
  "operation_class": [ ... ],
  "parameters": { ... },
  "metadata": { ... }
}
```

---

### Tool Types

| Type | Description | Typical Use |
|------|-------------|-------------|
| end_mill | Flat or ball end mill | Profiling, pocketing |
| slot_saw | Thin kerf slotting blade | Nut slots, fret slots |
| v_bit | V-groove cutter | Engraving, chamfers |
| drill | Twist drill | Drilling holes |
| ball_mill | Ball nose end mill | 3D surfacing |
| router_bit | General router bit | Edge profiling |
| engraver | Fine point engraving | Detail work |

---

### Geometry Block

```json
{
  "geometry": {
    "diameter_mm": 0.56,
    "cutting_length_mm": 5.0,
    "shank_diameter_mm": 3.175,
    "overall_length_mm": 38.0,
    "flute_count": 2,
    "helix_angle_deg": 30,
    "tip_geometry": "flat",
    "corner_radius_mm": 0.0
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| diameter_mm | number | Yes | Cutting diameter |
| cutting_length_mm | number | Yes | Effective cutting length |
| shank_diameter_mm | number | Yes | Shank diameter for collet |
| overall_length_mm | number | Yes | Total tool length |
| flute_count | number | No | Number of flutes |
| helix_angle_deg | number | No | Helix angle |
| tip_geometry | string | No | "flat", "ball", "v", "drill_point" |
| corner_radius_mm | number | No | Corner radius (for bull nose) |

**Tip Geometry Values:**

| Value | Description |
|-------|-------------|
| flat | Flat end mill |
| ball | Ball nose |
| v | V-groove (requires included_angle_deg) |
| drill_point | Standard drill point (118° or 135°) |
| radiused | Corner radius (bull nose) |

---

### Material Block

```json
{
  "material": {
    "substrate": "carbide",
    "coating": "TiAlN",
    "hardness": "HRC 65"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| substrate | string | No | "hss", "carbide", "cobalt", "ceramic" |
| coating | string | No | "uncoated", "TiN", "TiAlN", "DLC", etc. |
| hardness | string | No | Material hardness |

---

### Operation Class

```json
{
  "operation_class": [
    "slot_cutting",
    "grooving"
  ]
}
```

Supported operation classes:

| Class | Description |
|-------|-------------|
| profiling | External contour cutting |
| pocketing | Internal area removal |
| slot_cutting | Narrow slot cutting |
| grooving | V-groove or channel |
| drilling | Hole making |
| facing | Surface leveling |
| engraving | Fine detail marking |
| chamfering | Edge breaking |
| 3d_surfacing | 3D contour finishing |

---

### Parameters Block

```json
{
  "parameters": {
    "recommended_rpm_min": 15000,
    "recommended_rpm_max": 25000,
    "recommended_feed_mm_min": 200,
    "recommended_doc_mm": 1.0,
    "max_doc_mm": 3.0,
    "chip_load_mm": 0.05,
    "plunge_capable": true,
    "climb_milling_preferred": true
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| recommended_rpm_min | number | No | Minimum recommended RPM |
| recommended_rpm_max | number | No | Maximum recommended RPM |
| recommended_feed_mm_min | number | No | Recommended feed rate |
| recommended_doc_mm | number | No | Recommended depth of cut |
| max_doc_mm | number | No | Maximum depth of cut |
| chip_load_mm | number | No | Chip load per tooth |
| plunge_capable | boolean | No | Can plunge cut? |
| climb_milling_preferred | boolean | No | Prefer climb over conventional? |

---

### Metadata Block

```json
{
  "metadata": {
    "manufacturer": "StewMac",
    "part_number": "5557",
    "source_url": "https://www.stewmac.com/...",
    "notes": "Specific to nut slot cutting for wound strings",
    "created_at": "2026-05-10T12:00:00Z"
  }
}
```

---

## Example: Nut Slot Saw

```json
{
  "schema_version": "1.0.0",
  "tool_id": "nut_slot_saw_056",
  "tool_name": "Nut Slot Saw 0.56mm",
  
  "tool_type": "slot_saw",
  "geometry": {
    "diameter_mm": 0.56,
    "cutting_length_mm": 5.0,
    "shank_diameter_mm": 3.175,
    "overall_length_mm": 38.0,
    "flute_count": 2,
    "tip_geometry": "flat"
  },
  "material": {
    "substrate": "carbide",
    "coating": "TiAlN"
  },
  "operation_class": ["slot_cutting", "grooving"],
  "parameters": {
    "recommended_rpm_min": 15000,
    "recommended_rpm_max": 24000,
    "recommended_feed_mm_min": 100,
    "recommended_doc_mm": 1.5,
    "max_doc_mm": 3.0,
    "plunge_capable": true
  },
  "metadata": {
    "manufacturer": "StewMac",
    "part_number": "5557",
    "notes": "Wound string nut slot"
  }
}
```

---

## Example: End Mill

```json
{
  "schema_version": "1.0.0",
  "tool_id": "end_mill_3mm_2f",
  "tool_name": "3mm 2-Flute End Mill",
  
  "tool_type": "end_mill",
  "geometry": {
    "diameter_mm": 3.0,
    "cutting_length_mm": 12.0,
    "shank_diameter_mm": 3.0,
    "overall_length_mm": 38.0,
    "flute_count": 2,
    "helix_angle_deg": 30,
    "tip_geometry": "flat"
  },
  "material": {
    "substrate": "carbide",
    "coating": "TiAlN"
  },
  "operation_class": ["profiling", "pocketing", "slot_cutting"],
  "parameters": {
    "recommended_rpm_min": 12000,
    "recommended_rpm_max": 20000,
    "recommended_feed_mm_min": 500,
    "recommended_doc_mm": 1.5,
    "max_doc_mm": 3.0,
    "chip_load_mm": 0.04,
    "plunge_capable": false,
    "climb_milling_preferred": true
  }
}
```

---

## Example: V-Bit

```json
{
  "schema_version": "1.0.0",
  "tool_id": "v_bit_60deg_6mm",
  "tool_name": "60° V-Bit 6mm Shank",
  
  "tool_type": "v_bit",
  "geometry": {
    "diameter_mm": 6.0,
    "cutting_length_mm": 8.0,
    "shank_diameter_mm": 6.0,
    "overall_length_mm": 50.0,
    "flute_count": 2,
    "tip_geometry": "v",
    "included_angle_deg": 60,
    "tip_flat_mm": 0.1
  },
  "material": {
    "substrate": "carbide"
  },
  "operation_class": ["engraving", "chamfering", "grooving"],
  "parameters": {
    "recommended_rpm_min": 18000,
    "recommended_rpm_max": 24000,
    "recommended_feed_mm_min": 300,
    "plunge_capable": true
  }
}
```

---

## Tool Validation

### Required Fields

Every tool must have:
- schema_version
- tool_id
- tool_type
- geometry.diameter_mm
- geometry.cutting_length_mm
- geometry.shank_diameter_mm
- geometry.overall_length_mm

### Validation Rules

| Rule | Condition |
|------|-----------|
| Diameter positive | diameter_mm > 0 |
| Cutting length positive | cutting_length_mm > 0 |
| Shank fits collet | shank_diameter_mm in machine.collet_sizes_mm |
| DOC within limits | operation DOC <= max_doc_mm |
| RPM within range | operation RPM within recommended range |

---

## Tool Library Registry

Tools are stored in `data/tool_library/` with naming convention:

```
{tool_id}.json
```

Organization:
```
data/tool_library/
  nut_slot_saws/
    nut_slot_saw_030.json
    nut_slot_saw_046.json
    nut_slot_saw_056.json
    ...
  end_mills/
    end_mill_1mm_2f.json
    end_mill_3mm_2f.json
    ...
  v_bits/
    v_bit_30deg_6mm.json
    v_bit_60deg_6mm.json
    ...
  drills/
    drill_2mm.json
    drill_3mm.json
    ...
```

---

## Standard Tool Sets

### Nut Slot Saws (by string gauge)

| Tool ID | Diameter | Use |
|---------|----------|-----|
| nut_slot_saw_024 | 0.24mm | High E (0.010) |
| nut_slot_saw_030 | 0.30mm | B string (0.013) |
| nut_slot_saw_040 | 0.40mm | G string (0.017) |
| nut_slot_saw_046 | 0.46mm | D wound (0.026) |
| nut_slot_saw_056 | 0.56mm | A wound (0.036) |
| nut_slot_saw_066 | 0.66mm | Low E (0.046) |

### Fret Slot Saws

| Tool ID | Kerf | Use |
|---------|------|-----|
| fret_slot_saw_023 | 0.58mm (0.023") | Standard fretwire |
| fret_slot_saw_024 | 0.61mm (0.024") | Wide fretwire |

---

## Machine Compatibility

Tools are validated against machine profiles:

```python
def validate_tool_for_machine(tool: Tool, machine: MachineProfile) -> ValidationResult:
    issues = []
    
    # Shank fit
    if tool.geometry.shank_diameter_mm not in machine.spindle.collet_sizes_mm:
        issues.append(
            f"Shank {tool.geometry.shank_diameter_mm}mm not in collets: "
            f"{machine.spindle.collet_sizes_mm}"
        )
    
    # RPM range
    if tool.parameters.recommended_rpm_min > machine.spindle.max_rpm:
        issues.append(
            f"Tool min RPM {tool.parameters.recommended_rpm_min} exceeds "
            f"machine max {machine.spindle.max_rpm}"
        )
    
    # Tool length vs Z travel
    if tool.geometry.overall_length_mm > machine.work_envelope.z_mm * 2:
        issues.append("Tool length may exceed usable Z travel")
    
    return ValidationResult(
        passed=len(issues) == 0,
        issues=issues
    )
```

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | Architectural context |
| `CAM_EXPORT_OBJECT_MODEL.md` | Export tooling block |
| `CAM_MACHINE_PROFILE_STANDARD.md` | Machine validation |
| `CAM_POSTPROCESSOR_INTERFACE_STANDARD.md` | Consumer interface |

---

*Standard defined: 2026-05-10*
