# CAM Machine Readiness Plan

**Date:** 2026-05-07  
**Status:** ROADMAP — NO IMPLEMENTATION YET  
**Scope:** Defines requirements before machine-safe output can exist

---

## Purpose

This document defines what must be built before the system can produce machine-ready output. It is a roadmap, not an implementation spec.

---

## Current State

```
┌────────────────────────────────────────┐
│  PREVIEW-GRADE CAM                     │
│  ─────────────────                     │
│  • Toolpath JSON generation    ✓       │
│  • Gate evaluation             ✓       │
│  • Preview visualization       ✓       │
│  • Statistics calculation      ✓       │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  MACHINE-GRADE CAM                     │
│  ─────────────────                     │
│  • Machine profiles            ✗       │
│  • Postprocessors              ✗       │
│  • Coordinate transforms       ✗       │
│  • Travel validation           ✗       │
│  • G-code generation           ✗       │
│  • Execution streaming         ✗       │
└────────────────────────────────────────┘
```

---

## Machine Profile Requirements

Before supporting any machine, the system must define:

### 1. Machine Profile Schema

```typescript
interface MachineProfile {
  // Identity
  id: string;
  name: string;
  manufacturer: string;
  model: string;
  
  // Envelope
  x_min_mm: number;
  x_max_mm: number;
  y_min_mm: number;
  y_max_mm: number;
  z_min_mm: number;
  z_max_mm: number;
  
  // Kinematics
  max_feed_mm_min: number;
  max_rapid_mm_min: number;
  max_accel_mm_s2: number;
  
  // Spindle
  spindle_rpm_min: number;
  spindle_rpm_max: number;
  spindle_type: 'router' | 'spindle' | 'none';
  
  // Controller
  controller_type: 'grbl' | 'linuxcnc' | 'mach3' | 'fanuc' | 'other';
  gcode_dialect: GcodeDialect;
  
  // Safety
  requires_homing: boolean;
  has_limit_switches: boolean;
  has_probe: boolean;
  safe_z_mm: number;
  
  // Coordinate system
  work_offsets: string[];  // ['G54', 'G55', ...]
  default_work_offset: string;
}
```

### 2. Machine Profile Registry

```
machines/
├── grbl/
│   ├── generic_3018.json
│   ├── shapeoko_3.json
│   └── x_carve_1000.json
├── linuxcnc/
│   └── custom_router.json
└── mach3/
    └── chinese_6040.json
```

### 3. Machine Profile Validation

Before generating output for a machine, validate:

| Check | Condition |
|-------|-----------|
| Envelope | All moves within x/y/z limits |
| Feed rate | All feeds ≤ max_feed |
| Rapid rate | All rapids ≤ max_rapid |
| Spindle RPM | Requested RPM within range |
| Tool change | If multi-tool, machine supports T/M6 |
| Work offset | Selected offset available |

---

## Postprocessor Requirements

### 1. Postprocessor Interface

```python
class Postprocessor(Protocol):
    def process(
        self,
        toolpath: ValidatedToolpath,
        machine: MachineProfile,
        options: PostOptions,
    ) -> GcodeOutput:
        ...
    
    def header(self, machine: MachineProfile) -> str:
        ...
    
    def footer(self, machine: MachineProfile) -> str:
        ...
    
    def format_move(self, move: ToolpathMove, modal: ModalState) -> str:
        ...
```

### 2. Dialect Differences to Handle

| Feature | GRBL | LinuxCNC | Mach3 |
|---------|------|----------|-------|
| Units | G21 | G21 | G21 |
| Abs/Inc | G90 | G90 | G90 |
| Blend | N/A | G64 Px.xx | N/A |
| Spindle CW | M3 | M3 | M3 |
| Tool change | Manual | M6 Tx | M6 Tx |
| Dwell | G4 Px | G4 Px | G4 Px |
| Probe | G38.2 | G38.2 | G31 |

### 3. Coordinate Transform

```
Toolpath coordinates (local origin, stock-relative Z)
    ↓
Work offset application (G54 = X+50, Y+100, Z-25)
    ↓
Machine coordinates
```

---

## Validation Requirements Before Machine Output

### Gate 1: Preview Validation (existing)

- Parameter bounds check
- Tool vs slot width
- Depth vs stock thickness
- Position monotonicity

### Gate 2: Machine Validation (not implemented)

- Envelope bounds
- Feed/rapid limits
- Spindle capability
- Work offset availability

### Gate 3: Operator Confirmation (not implemented)

- Machine profile acknowledged
- Work offset confirmed
- Tool installed confirmed
- Stock secured confirmed

---

## Safety Requirements

### 1. No Automatic Execution

G-code output must be:
- Downloaded as file
- Manually loaded into controller
- Manually started by operator

No direct streaming to machine without explicit operator action.

### 2. Conservative Defaults

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| Safe Z | 5mm | Generous clearance |
| Feed rate | 50% of max | Conservative start |
| Spindle RPM | Mid-range | Avoid extremes |
| Rapid rate | 80% of max | Account for accel |

### 3. Warning Escalation

| Condition | Response |
|-----------|----------|
| Near envelope edge (< 5mm) | YELLOW warning |
| Feed > 80% max | YELLOW warning |
| RPM at limit | YELLOW warning |
| Any envelope violation | RED block |
| Tool change without M6 | RED block |

---

## Implementation Phases (Future)

### Phase A: Machine Profile System

1. Define MachineProfile schema
2. Create profile registry
3. Add machine selection UI
4. Add envelope validation

### Phase B: Postprocessor Framework

1. Define Postprocessor interface
2. Implement GRBL postprocessor
3. Add coordinate transform logic
4. Add header/footer generation

### Phase C: Export Pipeline

1. Connect preview → postprocessor
2. Add Gate 2 validation
3. Add download endpoint
4. Add audit logging

### Phase D: Operator Confirmation

1. Add confirmation modal
2. Add checklist UI
3. Add signed export token
4. Add RMOS artifact tracking

---

## What This Document Does NOT Define

- Specific machine profiles (Phase A)
- Postprocessor implementation (Phase B)
- Export endpoint spec (Phase C)
- Streaming protocol (out of scope)
- Collision detection (out of scope)
- Stock simulation (out of scope)

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_POSTPROCESSOR_BOUNDARY.md` | Layer architecture |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Safety gates |
| `CAM_TOOLING_AND_STOCK_MODEL.md` | Tool/stock abstraction |

---

*Roadmap defined: 2026-05-07*
