# CAM Export Governance Policy

**Date:** 2026-05-07  
**Status:** ACTIVE POLICY  
**Scope:** All CAM export and machine-adjacent output

---

## Purpose

This document defines the safety rules that must be satisfied before any machine-adjacent output can be generated. It establishes gates and forbidden patterns.

---

## Current Export Capabilities

| Export Type | Status | Format | Machine-Adjacent? |
|-------------|--------|--------|-------------------|
| Preview JSON | ✓ Active | JSON | No — visualization only |
| DXF geometry | ✓ Active | R12/R2000 | **Yes** — can be imported to CAM |
| SVG backplot | ✓ Active | SVG | No — visualization only |
| G-code | ✗ None | N/A | N/A |

---

## Export Classification

### Class A: Visualization Only

Not machine-adjacent. No governance required beyond data validity.

- Preview JSON (toolpath moves for frontend rendering)
- SVG backplots (2D path visualization)
- Statistics JSON (move counts, time estimates)

### Class B: Geometry Export

Machine-adjacent but not executable. DXF governance applies.

- DXF body outlines
- DXF fretboard geometry
- DXF inlay patterns

### Class C: Machine Instructions

Directly executable by CNC. **Not yet implemented.**

- G-code files
- Machine streaming
- Post-processed output

---

## Required Before Machine Output (Class C)

When Class C export is implemented, ALL of the following must pass:

### Gate 1: Preview Validation

All existing preview gates must pass:

| Check | Condition | Gate |
|-------|-----------|------|
| Parameter bounds | All values within Pydantic constraints | RED if fails |
| Tool vs slot | tool_diameter ≤ slot_width | RED if fails |
| Depth ratio | slot_depth < 0.8 × stock_thickness | RED if fails |
| Position bounds | All positions within workpiece | RED if fails |
| Position order | Positions strictly increasing | RED if fails |

### Gate 2: Coordinate Validation

| Check | Condition | Gate |
|-------|-----------|------|
| Origin declared | coordinate_system.origin specified | RED if missing |
| Z-zero declared | coordinate_system.z_zero specified | RED if missing |
| Units declared | units == "mm" | RED if not mm |

### Gate 3: Machine Profile Validation

| Check | Condition | Gate |
|-------|-----------|------|
| Profile selected | machine_id is valid | RED if missing |
| Envelope check | All moves within machine limits | RED if fails |
| Feed check | All feeds ≤ machine.max_feed | YELLOW if exceeds |
| Spindle check | RPM within machine range | YELLOW if outside |

### Gate 4: Tool Validation

| Check | Condition | Gate |
|-------|-----------|------|
| Tool specified | tool.diameter_mm > 0 | RED if missing |
| Reach check | tool can reach max depth | RED if fails |
| Compatibility | Tool suitable for material | YELLOW warning |

### Gate 5: Stock Validation

| Check | Condition | Gate |
|-------|-----------|------|
| Thickness specified | stock_thickness_mm > 0 | RED if missing |
| Depth check | No cut exceeds safe ratio | RED if fails |
| Material specified | Optional but recommended | INFO if missing |

### Gate 6: Safe Z Validation

| Check | Condition | Gate |
|-------|-----------|------|
| Safe Z specified | safe_z_mm > 0 | RED if missing |
| Safe Z adequate | safe_z_mm ≥ 2.0 | YELLOW if low |
| Clearance moves | All rapids at safe Z | RED if fails |

### Gate 7: Manual Review

| Check | Condition | Gate |
|-------|-----------|------|
| Preview reviewed | User has viewed preview | Required |
| Parameters confirmed | User acknowledges settings | Required |
| Machine confirmed | User confirms machine selection | Required |

---

## Forbidden Until Explicitly Approved

The following capabilities require explicit architectural approval before implementation:

### 1. Direct G-code Generation

**Status:** FORBIDDEN

No endpoint may return G-code until:
- Postprocessor framework exists
- Machine profile system exists
- All 7 gates implemented

### 2. Machine Streaming

**Status:** FORBIDDEN

No direct serial/network streaming to machines. Output must be:
- Downloaded as file
- Manually loaded by operator
- Manually started by operator

### 3. Automatic Execution

**Status:** FORBIDDEN

No background jobs that produce machine output. No scheduled machining. No headless export.

### 4. Headless Export

**Status:** FORBIDDEN

No API endpoint that returns machine code without user session. All machine output requires authenticated user interaction.

---

## DXF Export Governance

DXF is Class B (geometry, not instructions) but can be imported into CAM software.

### DXF Safety Rules

| Rule | Requirement |
|------|-------------|
| Format | R12 (free tier) or R2000 (paid tier) |
| Entities | LINE (R12) or LWPOLYLINE (R2000) only |
| Layers | Named layers only — no geometry on layer 0 |
| Precision | Coordinates rounded to 3dp |
| Units | mm only (INSUNITS=4) |

### DXF Warnings

Include in export metadata:

```
WARNING: This DXF contains geometry only, not machining instructions.
If used as CAM input, verify:
  - Scale is correct (mm, 1:1)
  - Z depth is appropriate for your stock
  - Toolpaths are validated for your machine
```

### DXF Cross-Reference

- `dxf_writer.py` — Central DXF output
- `dxf_compat.py` — Version-aware entity creation
- `CAM_COORDINATE_SYSTEM_GOVERNANCE.md` — Coordinate standards

---

## Gate Status Responses

All CAM preview/export endpoints must return gate status:

```json
{
  "gate": "green",
  "gate_details": {
    "preview_validation": "passed",
    "coordinate_validation": "passed",
    "machine_validation": "not_applicable",
    "tool_validation": "passed",
    "stock_validation": "passed",
    "safe_z_validation": "passed"
  },
  "issues": [],
  "warnings": [],
  "export_allowed": true
}
```

### Gate Escalation

| Condition | Gate | Export |
|-----------|------|--------|
| All checks pass | GREEN | Allowed |
| Warnings present, no errors | YELLOW | Allowed with confirmation |
| Any error present | RED | Blocked |

---

## Audit Trail Requirements

When Class C export is implemented, log:

| Field | Purpose |
|-------|---------|
| timestamp | When export occurred |
| user_id | Who requested export |
| operation_type | What was exported |
| machine_id | Target machine profile |
| gate_status | Final gate result |
| input_hash | Hash of input parameters |
| output_hash | Hash of generated output |
| file_size | Output file size |
| line_count | G-code line count |

---

## Governance Exceptions

No exceptions to RED gates. YELLOW gates may be overridden with:

1. Explicit user confirmation
2. Reason logged
3. Override flag in audit trail

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_COORDINATE_SYSTEM_GOVERNANCE.md` | Coordinate validation rules |
| `CAM_POSTPROCESSOR_BOUNDARY.md` | What constitutes machine output |
| `CAM_MACHINE_READINESS_PLAN.md` | Roadmap for Class C export |
| `CAM_TOOLING_AND_STOCK_MODEL.md` | Tool/stock validation |
| `CAM_PROMOTION_FRAMEWORK.md` | Promotion stages for candidates |
| `CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md` | Quarantine rules |

---

*Policy established: 2026-05-07*  
*Cross-references updated: 2026-05-09*
