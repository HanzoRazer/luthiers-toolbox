# Luthier's Tool Box - Architecture

> System design, data flows, and integration patterns for the CNC guitar lutherie platform.

**Last Updated**: February 2026
**Version**: 2.0 - RMOS Safety Architecture

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Repository Organization](#repository-organization)
3. [RMOS Decision Pipeline](#rmos-decision-pipeline)
4. [Data Flows](#data-flows)
5. [API Architecture](#api-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [CAM Integration](#cam-integration)
8. [Feature Flags](#feature-flags)
9. [Design Decisions](#design-decisions)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BROWSER CLIENT                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Vue 3 + Vite (TypeScript)                                    │  │
│  │  ├── DxfToGcodeView      (DXF → G-code workflow)              │  │
│  │  ├── AdaptivePocketLab   (Toolpath configuration)             │  │
│  │  ├── RmosRunViewer       (Run inspection + audit)             │  │
│  │  └── ScaleLengthDesigner (Parametric calculations)            │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                             │ HTTP API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI SERVER                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  services/api/app/                                            │  │
│  │  ├── rmos/           (RMOS Safety System - Core)              │  │
│  │  │   ├── feasibility/  (22 rules: F001-F029)                  │  │
│  │  │   ├── runs_v2/      (Immutable run artifacts)              │  │
│  │  │   └── operations/   (Export gates, overrides)              │  │
│  │  ├── cam/            (CAM Operations)                         │  │
│  │  │   ├── adaptive_pocket  (Spiral/trochoidal toolpaths)       │  │
│  │  │   └── posts/           (GRBL, Mach4, LinuxCNC, etc.)       │  │
│  │  ├── saw_lab/        (Batch sawing + decision intelligence)   │  │
│  │  └── calculators/    (Fret, scale length, chipload)           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ARTIFACT STORAGE                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  Run        │  │  Content-   │  │  Audit      │                 │
│  │  Artifacts  │  │  Addressed  │  │  Trail      │                 │
│  │  (JSON)     │  │  Store      │  │  (Append)   │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                      │
│  Paths:                                                              │
│  - {RMOS_RUNS_DIR}/runs/{run_id}/run.json                           │
│  - {RMOS_RUNS_DIR}/attachments/{sha256}                             │
│  - {RMOS_RUNS_DIR}/validation_logs/                                 │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CNC CONTROLLERS                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │   GRBL   │ │  Mach4   │ │ LinuxCNC │ │ PathPilot│ │  MASSO   │ │
│  │  (Hobby) │ │          │ │  (EMC2)  │ │ (Tormach)│ │          │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Repository Organization

### Monorepo Structure

```
luthiers-toolbox/
├── packages/
│   └── client/                 # Vue 3 frontend
│       └── src/
│           ├── components/     # Reusable UI components
│           │   ├── dxf/        # DXF workflow components
│           │   ├── rmos/       # RMOS-specific components
│           │   ├── toolbox/    # Calculator components
│           │   └── ui/         # Generic UI (badges, panels)
│           ├── views/          # Page-level components
│           ├── stores/         # Pinia state management
│           └── sdk/            # API client endpoints
│
├── services/
│   └── api/
│       └── app/                # FastAPI backend (236 LOC main.py)
│           ├── rmos/           # RMOS Safety System
│           ├── cam/            # CAM operations
│           ├── saw_lab/        # Saw Lab decision intelligence
│           ├── calculators/    # Parametric calculators
│           ├── feasibility/    # Feasibility engine
│           ├── vision/         # AI Vision (experimental)
│           └── routers/        # API route handlers
│
├── contracts/                  # JSON Schema contracts
├── docs/                       # Documentation
├── tests/                      # Test suites
└── ci/                         # CI/CD scripts and fences
```

---

## RMOS Decision Pipeline

### Overview

RMOS (Run Manufacturing Operations System) is the safety-critical decision layer that gates all CNC operations.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     RMOS DECISION PIPELINE                           │
│                                                                      │
│   DXF Input                                                          │
│       │                                                              │
│       ▼                                                              │
│   ┌─────────────┐                                                    │
│   │  Preflight  │  Validate DXF geometry, layer names, closure      │
│   │  Checks     │                                                    │
│   └──────┬──────┘                                                    │
│          │                                                           │
│          ▼                                                           │
│   ┌─────────────┐    ┌──────────────────────────────────────────┐   │
│   │ Feasibility │───▶│  22 Rules (F001-F029)                    │   │
│   │   Engine    │    │  ├─ F001-F007: RED (blocking)            │   │
│   └──────┬──────┘    │  ├─ F010-F013: YELLOW (warnings)         │   │
│          │           │  ├─ F020-F029: RED (adversarial)         │   │
│          │           │  └─ F030-F041: YELLOW/RED (edge cases)   │   │
│          │           └──────────────────────────────────────────┘   │
│          ▼                                                           │
│   ┌─────────────┐                                                    │
│   │  Decision   │  risk_level: GREEN | YELLOW | RED                 │
│   │  Authority  │  export_allowed: true | false                     │
│   └──────┬──────┘                                                    │
│          │                                                           │
│          ├────────────────┬────────────────┐                        │
│          │                │                │                        │
│          ▼                ▼                ▼                        │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐                  │
│   │   GREEN   │    │  YELLOW   │    │    RED    │                  │
│   │  Proceed  │    │  Override │    │  BLOCKED  │                  │
│   │           │    │  Required │    │           │                  │
│   └─────┬─────┘    └─────┬─────┘    └───────────┘                  │
│         │                │                                          │
│         ▼                ▼                                          │
│   ┌─────────────────────────────────────┐                           │
│   │         CAM Execution               │                           │
│   │  ├─ Generate toolpaths              │                           │
│   │  ├─ Post-process G-code             │                           │
│   │  └─ Create operator pack            │                           │
│   └──────────────┬──────────────────────┘                           │
│                  │                                                   │
│                  ▼                                                   │
│   ┌─────────────────────────────────────┐                           │
│   │       Artifact Store                │                           │
│   │  ├─ Run artifact (immutable)        │                           │
│   │  ├─ G-code (content-addressed)      │                           │
│   │  └─ Audit trail (append-only)       │                           │
│   └─────────────────────────────────────┘                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Risk Levels

| Level | Meaning | Export Allowed | Action Required |
|-------|---------|----------------|-----------------|
| **GREEN** | All checks pass | Yes | None |
| **YELLOW** | Warnings present | Yes (with override) | Review warnings, acknowledge |
| **RED** | Safety violation | No | Fix parameters or abort |

### Key Rules

| Rule ID | Level | Trigger |
|---------|-------|---------|
| F001 | RED | Invalid tool diameter (<0.5mm or >50mm) |
| F002 | RED | Stepover out of range (<10% or >100%) |
| F003 | RED | Stepdown exceeds safe limit |
| F020 | RED | Excessive DOC in hardwood |
| F021 | RED | Tool breakage risk (DOC:diameter >5:1) |
| F010 | YELLOW | feed_z > feed_xy |
| F011 | YELLOW | High loop count (>50) |

Full reference: `docs/RMOS_FEASIBILITY_RULES_v1.md`

---

## Data Flows

### DXF → G-code Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  DXF File   │────▶│  Preflight  │────▶│ Feasibility │────▶│    CAM      │
│  (Upload)   │     │  Validation │     │   Check     │     │  Execution  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Download   │◀────│  Operator   │◀────│   G-code    │◀────│  Post-      │
│  .nc file   │     │   Pack      │     │  Generation │     │  Process    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### API Endpoints (Golden Path)

```bash
# 1. Upload DXF and get feasibility + plan
POST /api/rmos/wrap/mvp/dxf-to-grbl
  -F "file=@design.dxf"
  -F "tool_d=6.0"
  -F "stepover=0.4"
  -F "z_rough=-3.0"

# Response:
{
  "ok": true,
  "run_id": "run_abc123...",
  "decision": {
    "risk_level": "GREEN",
    "warnings": []
  },
  "gcode": { "inline": true, "text": "G90\nG17\n..." }
}

# 2. Download operator pack
GET /api/rmos/runs_v2/{run_id}/operator-pack
# Returns ZIP: manifest.json, input.dxf, output.nc, feasibility.json
```

### Run Artifact Structure

```json
{
  "run_id": "run_20260218T143022_abc123",
  "created_at": "2026-02-18T14:30:22Z",
  "request_summary": {
    "tool_d": 6.0,
    "stepover": 0.4,
    "z_rough": -3.0
  },
  "feasibility": {
    "risk_level": "GREEN",
    "rules_triggered": [],
    "export_allowed": true
  },
  "decision": {
    "risk_level": "GREEN",
    "block_reason": null
  },
  "attachments": {
    "gcode_sha256": "abc123...",
    "input_dxf_sha256": "def456..."
  }
}
```

---

## API Architecture

### Router Organization

The API uses 64 routers organized by domain:

| Prefix | Domain | Key Endpoints |
|--------|--------|---------------|
| `/api/rmos/` | Safety system | runs_v2, feasibility, override |
| `/api/cam/` | CAM operations | pocket/adaptive, posts |
| `/api/saw/` | Saw Lab | batch, toolpaths, execution |
| `/api/calculators/` | Tools | fret, scale-length, chipload |
| `/api/health/` | Operations | status, detailed, features |

### Safety Decorators

```python
@safety_critical(fail_closed=True)
def compute_feasibility(input: FeasibilityInput) -> FeasibilityResult:
    """
    Decorated functions:
    - Log all invocations
    - Fail closed on any exception (return RED)
    - Cannot be bypassed
    """
    pass
```

36 functions are marked `@safety_critical` across the codebase.

---

## Frontend Architecture

### Component Hierarchy

```
App.vue
├── AppNav.vue (navigation)
├── Views/
│   ├── DxfToGcodeView.vue (main workflow)
│   │   ├── DxfUploadZone.vue
│   │   ├── CamParametersForm.vue
│   │   ├── RunCompareCard.vue
│   │   ├── RiskBadge.vue
│   │   ├── OverrideBanner.vue
│   │   └── WhyPanel.vue
│   │
│   ├── AdaptivePocketLab.vue (advanced CAM)
│   │   ├── ToolLibraryPanel.vue
│   │   ├── ParameterGrid.vue
│   │   └── (5 more extracted components)
│   │
│   └── ScaleLengthDesigner.vue (calculators)
│       ├── ScalePresetsPanel.vue
│       ├── TensionCalculatorPanel.vue
│       ├── IntonationPanel.vue
│       └── MultiscalePanel.vue
```

### State Management

- **Pinia stores** for global state
- **Composables** for reusable logic (`useScaleLengthCalculator`, `usePocketSettings`)
- **SDK endpoints** for API calls (`packages/client/src/sdk/`)

---

## CAM Integration

### Supported Post-Processors

| Post ID | Machine | Spindle | End Code |
|---------|---------|---------|----------|
| GRBL | Hobby CNC | M3 S18000 | M30 |
| Mach4 | Industrial | M3 S18000 | M30 |
| LinuxCNC | EMC2 | M3 S18000 | M2 |
| PathPilot | Tormach | M3 S18000 | M30 |
| MASSO | MASSO G3 | M3 S18000 | M30 |

### DXF Requirements

- **Format**: R12 (AC1009) for maximum compatibility
- **Units**: Millimeters (INSUNITS=4)
- **Geometry**: Closed LWPOLYLINE entities
- **Layers**: Named by operation (GEOMETRY, PROFILE, POCKET)

---

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `RMOS_RUNS_V2_ENABLED` | true | Use v2 run artifact store |
| `AI_CONTEXT_ENABLED` | true | Enable AI context adapter |
| `SAW_LAB_LEARNING_HOOK_ENABLED` | false | Enable learning hooks |
| `RMOS_ALLOW_RED_OVERRIDE` | false | Allow RED override (dangerous) |

Access via: `GET /api/features/catalog`

---

## Design Decisions

### 1. Why RMOS?

**Decision**: All CNC operations go through a safety decision layer.

**Rationale**:
- CNC errors can damage expensive materials and machines
- Operators need clear guidance on risk
- Audit trail enables post-incident analysis
- Consistent safety checks across all workflows

### 2. Why Content-Addressed Storage?

**Decision**: Artifacts stored by SHA256 hash.

**Rationale**:
- Immutable: same hash = same content
- Deduplication: identical G-code stored once
- Verifiable: detect tampering
- Cacheable: safe to cache forever

### 3. Why Component Extraction?

**Decision**: Large Vue components split into focused child components.

**Rationale**:
- Maintainability: <500 LOC per component
- Testability: isolated units
- Reusability: shared components (RiskBadge, WhyPanel)
- Performance: better tree-shaking

---

## Next Steps

### Completed
- [x] RMOS v2 with 22 feasibility rules
- [x] Multi-post G-code generation
- [x] Run artifact persistence
- [x] Vue component decomposition (Phase 3)

### In Progress
- [ ] Quick Cut onboarding flow
- [ ] Test coverage improvement (36% → 50%)
- [ ] RMOS concept tooltips

### Planned
- [ ] Real-time toolpath simulation
- [ ] Machine profiles UI
- [ ] Offline-capable PWA

---

**Document Maintained By**: AI Agent + Human Collaborator
**Last Review**: February 2026
