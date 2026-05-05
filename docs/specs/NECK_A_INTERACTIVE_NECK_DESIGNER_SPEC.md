# NECK-A: Interactive Neck Designer Specification

**Status:** Draft  
**Date:** 2026-05-05  
**Author:** System  
**Scope:** Specification only — no implementation

---

## Abstract

NECK-A defines the `NeckEcosphere` schema and associated workflows for interactive neck design, setup evaluation, and CAM integration. It extends the existing `instrumentGeometryStore` with structured blocks for geometry, physics, setup measurements, player profiles, diagnostics, and CAM references. The system uses a linear user workflow (measure → diagnose → adjust → verify) backed by a state machine with GREEN/YELLOW/RED gates.

---

## Motivation

The current system has:

1. **Orphan endpoints** — Setup evaluation, string tension, bridge presets, and saddle compensation endpoints exist but lack a unifying schema.

2. **Fragmented state** — Fretboard geometry, CAM parameters, and setup data are stored in separate, uncoordinated structures.

3. **No diagnostic model** — Rules for detecting setup issues (buzz, action problems, intonation errors) are implicit in UI logic, not formalized.

4. **No player context** — Setup recommendations are generic; there's no model for player preferences or historical setup data.

NECK-A addresses these gaps by providing a canonical schema that:
- Unifies neck-related data under one coherent model
- Formalizes diagnostic rules
- Introduces player profiles
- Establishes a clear CAM integration path for nut slot machining

---

## Goals

1. Define `NeckEcosphere` as a modular, block-based schema
2. Formalize the setup workflow with gate-based state machine
3. Encode v1 diagnostic rules with a path to JSON configuration
4. Introduce player profile model with numeric parameters and presets
5. Specify nut slot CAM output formats (toolpath JSON, G-code)
6. Extend `instrumentGeometryStore` without breaking existing fretboard state

## Non-Goals

1. User-editable diagnostic rules (v1 uses hardcoded rules)
2. Undo/redo in the setup workflow (deferred to v2)
3. Full CAM orchestration (nut slot CAM is standalone in v1)
4. Store replacement or major refactor (extension only)
5. DXF output for nut slots (optional, deferred)

---

## Existing System

### Current State

```
instrumentGeometryStore.ts
├── fretboard geometry (scale length, fret count, width, etc.)
├── wood species reference
├── Phase 0 additions:
│   ├── setup evaluation (issues, gates, suggestions)
│   ├── string tension (per-string tension, total)
│   ├── bridge spec (body style, dimensions, gate)
│   └── saddle compensation (design mode, setup mode)
└── CAM parameters (fret slot depth, tooling)
```

### Limitations

- No unified schema for neck-as-system
- Setup data is request/response, not persistent state
- No player context
- No historical snapshots
- Diagnostic logic is implicit

---

## Specification

### NeckEcosphere Schema

The schema is organized into six blocks. Each block is independently addressable and composable.

```
NeckEcosphere
├── geometry        # Physical dimensions
├── physics         # Material properties, tension
├── setup           # Current measurements
├── player          # Player profile + preferences
├── diagnostics     # Rule evaluations + gates
└── cam             # CAM references + outputs
```

---

## Data Models

### Block 1: Geometry

```typescript
interface NeckGeometry {
  scale_length_mm: number;
  fret_count: number;
  nut_width_mm: number;
  nut_thickness_mm: number;
  heel_width_mm: number;
  
  // Profile
  profile_type: 'C' | 'D' | 'V' | 'U' | 'asymmetric';
  profile_depth_1st_mm: number;
  profile_depth_12th_mm: number;
  
  // Fretboard
  fretboard_radius_mm: number | 'compound';
  compound_radius_start_mm?: number;
  compound_radius_end_mm?: number;
  
  // Headstock transition
  headstock_angle_deg: number;
  volute_type: 'none' | 'standard' | 'carved';
  
  // Nut slots
  string_count: number;
  nut_slot_spacing_mm: number[];
  nut_slot_depths_mm: number[];
}
```

### Block 2: Physics

```typescript
interface NeckPhysics {
  wood_species_key: string;
  density_kg_m3: number;
  
  // From string tension calculator
  string_set_key: string;
  string_gauges_inches: number[];
  total_tension_lb: number;
  per_string_tension_lb: number[];
  
  // Derived
  truss_rod_type: 'single_action' | 'dual_action' | 'none';
  carbon_fiber_reinforcement: boolean;
}
```

### Block 3: Setup

```typescript
interface NeckSetup {
  // Measured values (user input)
  relief_mm: number;
  action_1st_fret_mm: number[];      // per string
  action_12th_fret_mm: number[];     // per string
  nut_slot_depth_mm: number[];       // per string
  saddle_height_mm: number;
  
  // Intonation (cents error at 12th fret)
  intonation_cents: number[];        // per string
  
  // Timestamps
  measured_at: string;               // ISO 8601
  measured_by?: string;              // optional user ID
}
```

### Block 4: Player Profile

```typescript
interface PlayerProfile {
  id: string;
  name: string;
  
  // Numeric parameters (primary)
  attack_force: number;              // 0.0 (light) to 1.0 (heavy)
  preferred_action_low_mm: number;
  preferred_action_high_mm: number;
  preferred_relief_mm: number;
  string_gauge_preference: 'light' | 'medium' | 'heavy' | 'custom';
  
  // Derived preset (optional convenience)
  preset?: 'light_touch' | 'moderate' | 'heavy_strummer' | 'fingerpicker';
  
  // Historical snapshots
  setup_history: SetupSnapshot[];
}

interface SetupSnapshot {
  timestamp: string;
  setup: NeckSetup;
  diagnostics_summary: string;
  adjustments_made: string[];
}
```

### Block 5: Diagnostics

```typescript
interface DiagnosticResult {
  rule_id: string;
  severity: 'info' | 'warning' | 'error';
  gate: 'GREEN' | 'YELLOW' | 'RED';
  message: string;
  affected_strings?: number[];
  suggested_action?: string;
}

interface DiagnosticsBlock {
  evaluated_at: string;
  overall_gate: 'GREEN' | 'YELLOW' | 'RED';
  results: DiagnosticResult[];
}
```

#### V1 Diagnostic Rules

| Rule ID | Condition | Gate | Message |
|---------|-----------|------|---------|
| `relief_low` | relief < 0.1mm | YELLOW | Relief too low — may cause buzz |
| `relief_high` | relief > 0.5mm | YELLOW | Relief too high — action will feel high |
| `action_low_1st` | action_1st < 0.3mm | RED | Nut slots too deep — string buzz at open position |
| `action_high_1st` | action_1st > 0.8mm | YELLOW | Nut slots too shallow — hard to fret |
| `action_low_12th` | action_12th < 1.5mm | YELLOW | Action too low at 12th — buzz likely |
| `action_high_12th` | action_12th > 3.0mm | YELLOW | Action too high at 12th — playability affected |
| `intonation_sharp` | cents > +5 | YELLOW | Intonation sharp — saddle needs forward adjustment |
| `intonation_flat` | cents < -5 | YELLOW | Intonation flat — saddle needs backward adjustment |
| `buzz_low_frets` | action_1st low + relief low | RED | Buzz on frets 1-5 — check nut slots and relief |
| `buzz_mid_frets` | relief low + action_12th ok | YELLOW | Buzz on frets 5-12 — add relief |
| `buzz_upper_frets` | fallaway insufficient | YELLOW | Buzz on frets 12+ — check neck angle or fallaway |
| `saddle_range` | compensation > max_adjustment | RED | Saddle adjustment exceeds slot range |

Rules are hardcoded in v1. Path to JSON configuration:

```python
# Future: services/api/app/config/diagnostic_rules.json
{
  "rules": [
    {
      "id": "relief_low",
      "condition": "setup.relief_mm < 0.1",
      "gate": "YELLOW",
      "message": "Relief too low — may cause buzz"
    }
  ]
}
```

### Block 6: CAM References

```typescript
interface NeckCAMReferences {
  // Nut slot CAM
  nut_slot_toolpath?: ToolpathJSON;
  nut_slot_gcode?: string;
  
  // Fret slot CAM (existing)
  fret_slot_toolpath_ref?: string;  // reference to existing CAM output
  
  // Generation metadata
  generated_at?: string;
  tool_diameter_mm?: number;
  feed_rate_mm_min?: number;
}

interface ToolpathJSON {
  version: '1.0';
  units: 'mm';
  operations: ToolpathOperation[];
}

interface ToolpathOperation {
  type: 'plunge' | 'linear' | 'arc' | 'rapid';
  x?: number;
  y?: number;
  z?: number;
  f?: number;  // feed rate
}
```

---

## Setup Workflow

### User Workflow (Linear)

```
┌─────────┐    ┌──────────┐    ┌────────┐    ┌────────┐
│ MEASURE │ → │ DIAGNOSE │ → │ ADJUST │ → │ VERIFY │
└─────────┘    └──────────┘    └────────┘    └────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
  Input          Rules          User          Re-run
  values         evaluate       makes         diagnostics
                 → gates        changes
```

### Backend State Machine

```
         ┌──────────────────────────────────────┐
         │                                      │
         ▼                                      │
    ┌─────────┐                                 │
    │  IDLE   │ ← no measurements               │
    └────┬────┘                                 │
         │ submit measurements                  │
         ▼                                      │
    ┌─────────┐                                 │
    │EVALUATING│ ← running diagnostic rules     │
    └────┬────┘                                 │
         │                                      │
    ┌────┴────┬─────────────┐                   │
    ▼         ▼             ▼                   │
┌───────┐ ┌────────┐ ┌─────────┐                │
│ GREEN │ │ YELLOW │ │   RED   │                │
└───┬───┘ └────┬───┘ └────┬────┘                │
    │          │          │                     │
    │          │          │ user adjusts        │
    │          │          └─────────────────────┘
    │          │
    ▼          ▼
  READY     REVIEW
  (CAM ok)  (CAM blocked or warned)
```

---

## API Implications

### New Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/neck/ecosphere` | GET | Retrieve current NeckEcosphere state |
| `/api/neck/ecosphere` | PUT | Update ecosphere (partial or full) |
| `/api/neck/ecosphere/setup` | POST | Submit setup measurements |
| `/api/neck/ecosphere/diagnose` | POST | Run diagnostics on current setup |
| `/api/neck/player-profile` | GET/POST/PUT | Manage player profiles |
| `/api/neck/player-profile/{id}/snapshots` | GET/POST | Setup history snapshots |
| `/api/neck/cam/nut-slots` | POST | Generate nut slot toolpath |
| `/api/neck/cam/nut-slots/gcode` | POST | Convert toolpath to G-code |

### Existing Endpoints (Unchanged)

Phase 0 endpoints remain unchanged:
- `/api/instrument/string-tension/*`
- `/api/instrument/bridge/*`
- `/api/instrument/setup/evaluate`
- `/api/instrument/bridge/compensation`

These feed into `NeckEcosphere.physics` and `NeckEcosphere.setup` blocks.

---

## Frontend Implications

### Store Extension

```typescript
// instrumentGeometryStore.ts additions

interface InstrumentGeometryState {
  // ... existing state ...
  
  // NECK-A additions
  neckEcosphere: NeckEcosphere | null;
  playerProfiles: PlayerProfile[];
  activePlayerProfileId: string | null;
  
  // Workflow state
  setupWorkflowStage: 'idle' | 'measure' | 'diagnose' | 'adjust' | 'verify';
  diagnosticsLoading: boolean;
  diagnosticsError: string | null;
}
```

### New Actions

```typescript
// New store actions
loadNeckEcosphere(): Promise<void>
updateNeckEcosphere(partial: Partial<NeckEcosphere>): Promise<void>
submitSetupMeasurements(setup: NeckSetup): Promise<void>
runDiagnostics(): Promise<DiagnosticsBlock>
loadPlayerProfiles(): Promise<void>
setActivePlayerProfile(id: string): void
saveSetupSnapshot(): Promise<void>
generateNutSlotToolpath(): Promise<ToolpathJSON>
```

### New Components

| Component | Purpose |
|-----------|---------|
| `NeckEcospherePanel.vue` | Master panel orchestrating blocks |
| `SetupMeasurementForm.vue` | Input form for setup measurements |
| `DiagnosticsResultPanel.vue` | Display diagnostic results with gates |
| `PlayerProfileSelector.vue` | Select/manage player profiles |
| `SetupHistoryPanel.vue` | View historical setup snapshots |
| `NutSlotCAMPanel.vue` | Generate and preview nut slot toolpaths |

---

## Migration Plan

### Phase 1: Schema Introduction

1. Add `NeckEcosphere` types to `instrumentGeometryStore.ts`
2. Initialize with `null` — no breaking change
3. Existing fretboard state unchanged

### Phase 2: Backend Endpoints

1. Implement `/api/neck/ecosphere` endpoints
2. Wire diagnostic rules (hardcoded v1)
3. Add nut slot CAM generation

### Phase 3: Frontend Components

1. Create `NeckEcospherePanel.vue` as opt-in view
2. Wire to new store state
3. Keep existing panels functional

### Phase 4: Integration

1. Connect Phase 0 panels to NeckEcosphere blocks
2. Flow data: string tension → physics, setup evaluation → diagnostics
3. Player profiles populate defaults

### Rollback Strategy

- All additions are opt-in
- Existing state paths unchanged
- `neckEcosphere: null` is valid state
- No database migrations in v1 (state is session-based)

---

## Open Questions

1. **Persistence**: Should NeckEcosphere state persist to backend, or remain session-only in v1?

2. **Player profile storage**: Backend database vs. browser localStorage?

3. **Multi-instrument**: Does NeckEcosphere apply to one instrument at a time, or can multiple be active?

4. **Nut slot CAM safety**: What machine/material validation is required before G-code generation?

5. **Diagnostic thresholds**: Should thresholds be player-profile-aware (e.g., lower action tolerance for light touch players)?

6. **Export format**: Should setup snapshots be exportable as JSON/PDF for customer handoff?

---

*End of specification*
