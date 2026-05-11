# CAM Export Lifecycle

**Date:** 2026-05-10  
**Status:** ARCHITECTURAL DEFINITION  
**Dev Order:** 6A  
**Scope:** Preview → Export → Machine flow specification

---

## Purpose

This document defines the **Export Lifecycle** — the sequence of states and transitions from initial geometry through machine execution.

---

## Lifecycle Stages

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  GEOMETRY   │────▶│   PREVIEW   │────▶│   EXPORT    │────▶│   MACHINE   │
│             │     │             │     │             │     │   OUTPUT    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     │                    │                   │                    │
     │                    │                   │                    │
  No gate            Gate eval           Gate check          Audit trail
  Neutral            Visualize           Portable            Executable
```

---

## Stage 1: GEOMETRY

### Definition

Pure dimensional data without machining semantics.

### Examples

- FretboardEcosphere calculations
- NeckGeometry dimensions
- Body outline coordinates
- Soundhole positions

### Characteristics

| Property | Value |
|----------|-------|
| Gate evaluation | None |
| Classification | NEUTRAL |
| Persistence | Optional (in-memory) |
| Validation | Dimensional only |

### Outputs

- Dimensions in mm
- Coordinate arrays
- Geometric primitives

### Transition: GEOMETRY → PREVIEW

**Requirements:**
1. Geometry calculations complete
2. Parameters specified for toolpath generation
3. CAM generator invoked

**Action:** Invoke preview endpoint with geometry + parameters

---

## Stage 2: PREVIEW

### Definition

Human-inspection-oriented representation with validation and visualization.

### Examples

- Nut slot preview JSON
- Fret slot backplot
- Drilling preview with hole positions
- Rosette pattern preview

### Characteristics

| Property | Value |
|----------|-------|
| Gate evaluation | GREEN / YELLOW / RED |
| Classification | PREVIEW |
| Persistence | Optional (RMOS) |
| Validation | Full governed preview checks |

### Governed Preview Fields

```json
{
  "operation": "nut_slot_preview",
  "status": "success",
  "gate": "green",
  "units": "mm",
  "coordinate_system": { ... },
  "canonical_toolpath": [ ... ],
  "warnings": [],
  "errors": [],
  "issues": [],
  "statistics": { ... },
  "metadata": { ... }
}
```

### Gate Semantics

| Gate | Meaning | Export Allowed |
|------|---------|----------------|
| GREEN | All checks passed | Yes |
| YELLOW | Warnings present, user should review | Yes (with confirmation) |
| RED | Critical issues, cannot proceed | No |

### Transition: PREVIEW → EXPORT

**Requirements:**
1. Gate status GREEN or YELLOW
2. User confirmation for YELLOW gates
3. Preview hash captured
4. RMOS run ID (if applicable)

**Blocked if:**
- Gate status RED
- Missing required preview fields
- Invalid coordinate system

**Action:** Create Export Object from validated preview

---

## Stage 3: EXPORT

### Definition

Portable manufacturing-oriented representation.

### Examples

- Export Object JSON bundle
- DXF geometry export
- Neutral toolpath package

### Characteristics

| Property | Value |
|----------|-------|
| Gate evaluation | Inherited from preview |
| Classification | EXPORT |
| Persistence | Required (RMOS) |
| Validation | Export object schema |

### Export Object Contents

```json
{
  "schema_version": "1.0.0",
  "export_id": "EXP-...",
  "export_type": "toolpath",
  "metadata": { ... },
  "geometry": { ... },
  "toolpaths": { ... },
  "tooling": { ... },
  "material": { ... },
  "stock": { ... },
  "validation": { ... },
  "intent": { ... }
}
```

### Export Validation

| Check | Requirement |
|-------|-------------|
| Source hash | Matches preview |
| Gate status | Not RED |
| Schema valid | All required fields present |
| Tool specified | Tooling block present |
| Coordinates defined | coordinate_system complete |

### Transition: EXPORT → MACHINE OUTPUT

**Requirements:**
1. Valid Export Object
2. Machine Profile selected
3. Tool validated against machine
4. Work envelope validated
5. RMOS run tracking active
6. User confirmation

**Blocked if:**
- No machine profile selected
- Tool incompatible with machine
- Geometry exceeds work envelope
- RMOS tracking not active

**Action:** Invoke postprocessor with Export Object + Machine Profile

---

## Stage 4: MACHINE OUTPUT

### Definition

Machine-executable representation.

### Examples

- GRBL G-code file (.nc)
- LinuxCNC program
- FANUC output

### Characteristics

| Property | Value |
|----------|-------|
| Gate evaluation | Export gates + machine validation |
| Classification | MACHINE OUTPUT |
| Persistence | Required (RMOS, with hash) |
| Validation | Postprocessor validation |

### Machine Output Contents

- G-code file content
- Header comments with traceability
- Units/coordinate declarations
- Toolpath instructions
- Footer/program end

### Audit Requirements

Every machine output must record:

| Field | Purpose |
|-------|---------|
| export_id | Source traceability |
| export_hash | Input verification |
| machine_profile_id | Target machine |
| output_hash | Output verification |
| postprocessor_id | Translation source |
| user_id | Accountability |
| timestamp | Audit trail |

---

## State Transitions Summary

```
GEOMETRY ──────────────────▶ PREVIEW
  │                            │
  │ Invoke preview endpoint    │ Gate evaluation
  │ Specify parameters         │ Visualization
  │ Select operation           │ Validation
  │                            │
  │                            ▼
  │                         PREVIEW
  │                            │
  │                            │ Gate GREEN/YELLOW
  │                            │ User review
  │                            │ RMOS capture
  │                            │
  │                            ▼
  │                         EXPORT
  │                            │
  │                            │ Machine profile selected
  │                            │ Tool validated
  │                            │ Envelope checked
  │                            │ User confirmed
  │                            │
  │                            ▼
  │                       MACHINE OUTPUT
  │                            │
  │                            │ Postprocessor executed
  │                            │ G-code generated
  │                            │ Audit recorded
  │                            │
  │                            ▼
  │                         [DONE]
  │
  └─────────────────────────▶ [DXF EXPORT]
                               │
                               │ Geometry-only path
                               │ No toolpaths
                               │ Classification: EXPORT
```

---

## DXF Export Path

Some operations export geometry without toolpaths (e.g., body outline DXF for external CAM).

### DXF Lifecycle

```
GEOMETRY ──▶ DXF EXPORT
```

### DXF Classification

- Classification: EXPORT (not MACHINE OUTPUT)
- No postprocessor required
- No machine profile required
- Still requires RMOS tracking

---

## Error Handling

### Gate RED at PREVIEW

```
User action: Review issues, modify parameters, regenerate preview
System: Block export transition
Logging: Record RED gate with issues
```

### Validation Failure at EXPORT

```
User action: Fix missing fields, resubmit
System: Return validation errors
Logging: Record validation failure
```

### Machine Incompatibility at MACHINE OUTPUT

```
User action: Select different machine or modify export
System: Return compatibility errors
Logging: Record compatibility check failure
```

---

## RMOS Integration Points

| Stage | RMOS Role |
|-------|-----------|
| PREVIEW | Optional capture (run_id, snapshot) |
| EXPORT | Required (export_id, artifacts, lineage) |
| MACHINE OUTPUT | Required (output_id, hashes, audit) |

### RMOS Fields by Stage

**PREVIEW:**
```json
{
  "run_id": "RUN-...",
  "operation": "nut_slot_preview",
  "snapshot": { ... },
  "gate": "green"
}
```

**EXPORT:**
```json
{
  "export_id": "EXP-...",
  "run_id": "RUN-...",
  "artifacts": ["export_object.json"],
  "source_preview_hash": "sha256:..."
}
```

**MACHINE OUTPUT:**
```json
{
  "output_id": "OUT-...",
  "export_id": "EXP-...",
  "machine_profile_id": "...",
  "gcode_hash": "sha256:...",
  "user_id": "...",
  "timestamp": "..."
}
```

---

## Lifecycle Queries

### "Can I export this preview?"

```python
def can_export(preview: PreviewResponse) -> tuple[bool, list[str]]:
    issues = []
    
    if preview.gate == "red":
        issues.append("Gate is RED - cannot export")
    
    if not preview.coordinate_system:
        issues.append("Missing coordinate system")
    
    if not preview.canonical_toolpath:
        issues.append("No toolpath to export")
    
    return (len(issues) == 0, issues)
```

### "Can I postprocess this export?"

```python
def can_postprocess(
    export: ExportObject,
    machine: MachineProfile
) -> tuple[bool, list[str]]:
    issues = []
    
    # Gate check
    if export.validation.gate_status == "red":
        issues.append("Export gate is RED")
    
    # Envelope check
    bounds = export.geometry.bounds
    if bounds.x_max > machine.work_envelope.x_mm:
        issues.append(f"X exceeds envelope")
    if bounds.y_max > machine.work_envelope.y_mm:
        issues.append(f"Y exceeds envelope")
    
    # Tool check
    shank = export.tooling.geometry.shank_diameter_mm
    if shank not in machine.spindle.collet_sizes_mm:
        issues.append(f"Shank {shank}mm not compatible")
    
    return (len(issues) == 0, issues)
```

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | Architectural context |
| `CAM_EXPORT_OBJECT_MODEL.md` | Export schema |
| `CAM_POSTPROCESSOR_INTERFACE_STANDARD.md` | Postprocessor contract |
| `CAM_MACHINE_PROFILE_STANDARD.md` | Machine abstraction |
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Preview schema |

---

*Lifecycle defined: 2026-05-10*
