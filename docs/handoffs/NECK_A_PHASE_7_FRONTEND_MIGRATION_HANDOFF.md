# NECK-A Phase 7 — Frontend Migration Handoff

**Date:** 2026-05-06  
**Commit:** `81576eda` feat(setup): add expert setup diagnostics  
**Branch:** `fix/wood-shrinkage-data-integrity`  
**Status:** Complete and merged, ready for frontend consolidation

---

## 1. Executive Summary

Phase 7 adds symptom-based expert diagnostics to the Neck Studio setup workflow. Users select player-reported symptoms (buzz locations, playability feel), and the system correlates them with existing Relief/Action/Nut measurements to produce actionable diagnoses.

This completes the NECK-A vertical slice:

```
Relief → Action → Nut → Combined → Expert
```

The frontend migration sprint should treat these five panels as a single cohesive unit when consolidating into the shared workspace architecture.

---

## 2. What Phase 7 Adds

### Backend

**File:** `services/api/app/instrument_geometry/neck/setup_workflow.py`

New models:

```python
class PlayerSymptom(str, Enum):
    BUZZ_OPEN_STRINGS = "buzz_open_strings"
    BUZZ_LOW_FRETS = "buzz_low_frets"
    BUZZ_MIDDLE_FRETS = "buzz_middle_frets"
    BUZZ_UPPER_FRETS = "buzz_upper_frets"
    FRETTED_NOTES_BUZZ = "fretted_notes_buzz"
    FIRST_POSITION_HARD = "first_position_hard"
    FIRST_POSITION_SHARP = "first_position_sharp"
    FEELS_STIFF = "feels_stiff"
    FEELS_SLINKY = "feels_slinky"

class ExpertDiagnostic(BaseModel):
    id: str
    gate: DiagnosticGate          # GREEN/YELLOW/RED
    symptom: PlayerSymptom
    message: str
    probable_causes: List[str]
    recommended_checks: List[str]
    recommended_actions: List[str]
    confidence: float             # 0.0–1.0

class ExpertDiagnosticsResponse(BaseModel):
    overall_gate: DiagnosticGate
    diagnostics: List[ExpertDiagnostic]
```

New function:

```python
def evaluate_expert_symptoms(
    symptoms: List[PlayerSymptom],
    relief_gate: DiagnosticGate,
    relief_diagnostic_ids: List[str],
    action_gate: DiagnosticGate,
    action_diagnostic_ids: List[str],
    nut_gate: DiagnosticGate,
    nut_diagnostic_ids: List[str],
) -> ExpertDiagnosticsResponse
```

**File:** `services/api/app/routers/instrument_geometry/setup_router.py`

New endpoint:

```
POST /api/instrument/setup/workflow/expert/evaluate
```

Request shape:

```json
{
  "symptoms": ["buzz_low_frets", "feels_stiff"],
  "relief_gate": "red",
  "relief_diagnostic_ids": ["relief_too_low"],
  "action_gate": "green",
  "action_diagnostic_ids": [],
  "nut_gate": "green",
  "nut_diagnostic_ids": []
}
```

Response shape:

```json
{
  "overall_gate": "red",
  "diagnostics": [
    {
      "id": "expert_buzz_low_relief",
      "gate": "red",
      "symptom": "buzz_low_frets",
      "message": "Low fret buzz correlates with insufficient neck relief.",
      "probable_causes": ["Relief too low for string gauge/action"],
      "recommended_checks": ["Re-measure relief at fret 8"],
      "recommended_actions": ["Loosen truss rod 1/8 turn"],
      "confidence": 0.85
    }
  ]
}
```

### Frontend

**File:** `packages/client/src/stores/instrumentGeometryStore.ts`

New state:

```ts
expertSymptoms: PlayerSymptom[]
expertDiagnosticsResult: ExpertDiagnosticsResponse | null
expertDiagnosticsLoading: boolean
expertDiagnosticsError: string | null
```

New actions:

```ts
toggleExpertSymptom(symptom: PlayerSymptom): void
evaluateExpertDiagnostics(): Promise<void>
canEvaluateExpertDiagnostics(): boolean  // requires Relief+Action+Nut results
```

**Files:**

```
packages/client/src/components/SetupWorkflowExpertPanel.vue
packages/client/src/components/SetupWorkflowExpertPanel.module.css
```

UI features:

- 9-symptom checkbox grid
- Prerequisite notice when workflows not evaluated
- Diagnostic cards with gate badge, confidence %, causes/checks/actions
- Color-coded lists (causes=yellow, checks=blue, actions=green)

---

## 3. Complete NECK-A Panel Inventory

The following panels form the NECK-A vertical slice:

| Panel | File | Purpose |
|-------|------|---------|
| Relief | `SetupWorkflowReliefPanel.vue` | Neck relief measurement + diagnostics |
| Action | `SetupWorkflowActionPanel.vue` | String action measurement + diagnostics |
| Nut | `SetupWorkflowNutPanel.vue` | Nut slot depth measurement + diagnostics |
| Combined | `SetupWorkflowCombinedPanel.vue` | Cross-step correlation diagnostics |
| Expert | `SetupWorkflowExpertPanel.vue` | Symptom-based expert diagnostics |

Current composition in `InstrumentGeometryPanel.vue`:

```vue
<!-- ===== NECK-A Phase 3: Relief Workflow ===== -->
<SetupWorkflowReliefPanel />

<!-- ===== NECK-A Phase 4: Action Workflow ===== -->
<SetupWorkflowActionPanel />

<!-- ===== NECK-A Phase 5: Nut Slot Workflow ===== -->
<SetupWorkflowNutPanel />

<!-- ===== NECK-A Phase 6: Combined Diagnostics ===== -->
<SetupWorkflowCombinedPanel />

<!-- ===== NECK-A Phase 7: Expert Diagnostics ===== -->
<SetupWorkflowExpertPanel />
```

---

## 4. Alignment with Aperture Workspace Refactor

### Shared Architecture Patterns

The NECK-A panels should migrate to the same shared infrastructure as the Aperture Workspace:

| Aperture Pattern | NECK-A Equivalent |
|------------------|-------------------|
| `ApertureDesignerWorkspace.vue` | `NeckSetupWorkspace.vue` (proposed) |
| `SpiralAperturePanel.vue` | `SetupWorkflowReliefPanel.vue` |
| `ApertureComparisonPanel.vue` | `SetupWorkflowCombinedPanel.vue` |
| `InverseSolverPanel.vue` | `SetupWorkflowExpertPanel.vue` |

### Recommended Consolidation

```
ArtStudioWorkspace
├─ ApertureWorkspace
│   ├─ RoundOvalFholePanel
│   ├─ SpiralAperturePanel
│   ├─ ApertureComparisonPanel
│   └─ InverseSolverPanel
└─ NeckSetupWorkspace
    ├─ ReliefPanel
    ├─ ActionPanel
    ├─ NutPanel
    ├─ CombinedDiagnosticsPanel
    └─ ExpertDiagnosticsPanel
```

### Shared Components to Reuse

The NECK-A panels already use patterns that should become canonical:

| Pattern | Current Implementation | Shared Target |
|---------|------------------------|---------------|
| Gate badges | `.gateBadge` + `.gateGreen/.gateYellow/.gateRed` | `GateBadge.vue` |
| Diagnostic cards | `.diagnosticCard` with border-left coloring | `DiagnosticCard.vue` |
| Prerequisite notices | `.prerequisiteNotice` | `PrerequisiteNotice.vue` |
| Section labels | `.diagSectionLabel` uppercase + letter-spacing | `SectionLabel.vue` |

---

## 5. Store Extraction Guidance

### Current State

All NECK-A state lives in `instrumentGeometryStore.ts`:

```ts
// Phase 3: Relief
reliefMeasurement_mm: number
reliefResult: ReliefWorkflowResponse | null
reliefLoading: boolean
reliefError: string | null

// Phase 4: Action
actionMeasurement_mm: number
actionResult: ActionWorkflowResponse | null
actionLoading: boolean
actionError: string | null

// Phase 5: Nut
nutMeasurement_mm: number
nutResult: NutWorkflowResponse | null
nutLoading: boolean
nutError: string | null

// Phase 6: Combined
combinedResult: CombinedDiagnosticsResponse | null
combinedLoading: boolean
combinedError: string | null

// Phase 7: Expert
expertSymptoms: PlayerSymptom[]
expertDiagnosticsResult: ExpertDiagnosticsResponse | null
expertDiagnosticsLoading: boolean
expertDiagnosticsError: string | null
```

### Recommended Extraction

When consolidating, consider extracting to a dedicated store:

```ts
// stores/neckSetupStore.ts
export const useNeckSetupStore = defineStore('neckSetup', () => {
  // All NECK-A state and actions
})
```

This mirrors the aperture workspace having its own store.

---

## 6. API Contract Summary

### NECK-A Setup Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/instrument/setup/workflow/relief/evaluate` | Relief diagnostics |
| POST | `/api/instrument/setup/workflow/action/evaluate` | Action diagnostics |
| POST | `/api/instrument/setup/workflow/nut/evaluate` | Nut slot diagnostics |
| POST | `/api/instrument/setup/workflow/combined/evaluate` | Cross-step diagnostics |
| POST | `/api/instrument/setup/workflow/expert/evaluate` | Symptom-based diagnostics |

### Response Shape Consistency

All workflow endpoints return the same gate structure:

```ts
interface WorkflowResponse {
  overall_gate: 'green' | 'yellow' | 'red'
  diagnostics: Diagnostic[]
}

interface Diagnostic {
  id: string
  gate: 'green' | 'yellow' | 'red'
  message: string
  // ... additional fields per phase
}
```

This consistency enables shared rendering components.

---

## 7. Testing

### Backend Tests

```
services/api/tests/instrument_geometry/test_setup_workflow_expert.py
```

22 tests covering:
- All 8 diagnostic rules
- Fallback behavior
- Multiple symptom handling
- Gate sorting (RED → YELLOW → GREEN)
- Confidence values
- Endpoint validation

### Run All NECK-A Tests

```bash
pytest services/api/tests/instrument_geometry/test_setup_workflow*.py -v
```

---

## 8. CSS Module Patterns

The Expert panel CSS (`SetupWorkflowExpertPanel.module.css`) introduces patterns that should be standardized:

```css
/* Gate coloring - extract to shared */
.gateGreen { background: #065f46; color: #6ee7b7; }
.gateYellow { background: #78350f; color: #fcd34d; }
.gateRed { background: #7f1d1d; color: #fca5a5; }

/* Diagnostic card border coloring */
.diagnosticCard.gateGreen { border-left-color: #10b981; }
.diagnosticCard.gateYellow { border-left-color: #f59e0b; }
.diagnosticCard.gateRed { border-left-color: #ef4444; }

/* List coloring by category */
.causesList li { color: #fbbf24; }    /* yellow - causes */
.checksList li { color: #60a5fa; }    /* blue - checks */
.actionsList li { color: #34d399; }   /* green - actions */
```

These colors match the dark theme and should be promoted to shared styles.

---

## 9. Migration Checklist

When incorporating NECK-A into the shared workspace:

- [ ] Create `NeckSetupWorkspace.vue` wrapper
- [ ] Extract gate badge to shared `GateBadge.vue`
- [ ] Extract diagnostic card to shared `DiagnosticCard.vue`
- [ ] Move NECK-A state to dedicated `neckSetupStore.ts`
- [ ] Update imports in `InstrumentGeometryPanel.vue`
- [ ] Add NECK-A workspace to tool registry
- [ ] Verify all 5 panels render in new structure
- [ ] Run full test suite
- [ ] Update router if paths change

---

## 10. Do NOT Change

During migration, preserve:

1. **API contracts** — endpoint paths and request/response shapes
2. **Diagnostic IDs** — used for rule matching (e.g., `relief_too_low`)
3. **Gate enum values** — `green`, `yellow`, `red` lowercase
4. **Symptom enum values** — lowercase snake_case
5. **Confidence calculation** — 0.85 for matched rules, 0.4 for fallback

---

## 11. Contact

Phase 7 implementation completed by Claude session on 2026-05-06.

For questions about diagnostic rule logic, see:
```
services/api/app/instrument_geometry/neck/setup_workflow.py:evaluate_expert_symptoms()
```

For questions about the broader Aperture Workspace alignment, see:
```
aperture_workspace_refactor_handoff_for_neck_studio_alignment.md
```

---

## 12. Clarifications — Migration Q&A

### Q1: Store extraction timing

Do **not** extract `neckSetupStore.ts` inside the Aperture consolidation sprint unless the team has time to regression-test all five NECK-A panels.

**Recommended sequence:**

```text
Aperture sprint:
  - define store convention
  - create apertureWorkspaceStore.ts
  - document one-store-per-workspace rule

NECK-A follow-up:
  - extract neckSetupStore.ts
  - keep API contracts and panel behavior unchanged
  - regression-test Relief → Action → Nut → Combined → Expert
```

**Reason:** NECK-A is already working. Moving its store during Aperture work risks destabilizing a completed vertical slice.

**Answer:** Define the convention now, migrate NECK-A store later.

---

### Q2: Shared component location

Use:

```text
packages/client/src/components/shared/workflow/
```

**Recommended structure:**

```text
packages/client/src/components/shared/workflow/
├── GateBadge.vue
├── DiagnosticCard.vue
├── PrerequisiteNotice.vue
├── SectionLabel.vue
└── workflow.module.css
```

**Reason:** These components are not Art-Studio-specific. They can serve Neck Setup, Aperture diagnostics, inverse calibration, measurement import, and future setup workflows.

**Avoid:** `components/art-studio/shared/` — NECK-A currently lives under instrument geometry/setup, and these components should become platform-level workflow UI.

---

### Q3: Router changes

Keep current routes stable for now. Do **not** change Neck routes during the first Aperture consolidation pass.

**Recommended staging:**

```text
Phase 1:
  - add shared components
  - add tool registry entries
  - keep existing route paths

Phase 2:
  - introduce /art-studio/neck or /instrument-geometry/setup as an alias
  - migrate UI shell if needed

Phase 3:
  - deprecate old route only after links/tests/docs are updated
```

**Answer:** No planned Neck route changes immediately. Aperture may introduce its own new route, but Neck should remain stable until the shared shell is proven.

---

### Q4: Tool registry entry

Register NECK-A as a setup/workflow tool, not as a generic neck geometry generator.

**Recommended entry:**

```ts
{
  id: 'neck-setup',
  label: 'Neck Setup Diagnostics',
  category: 'setup',
  route: '/instrument-geometry/setup',
  status: 'stable',
  capabilities: {
    export: ['json'],
    import: ['preset']
  }
}
```

**Long-term taxonomy:**

```ts
'aperture' | 'neck' | 'setup' | 'rosette' | 'pattern' | 'calculator'
```

**Status:** Mark NECK-A as `stable` because Phase 7 completes the vertical slice and has backend tests. Do not call it experimental.

---

## 13. Summary of Migration Decisions

| Question | Answer |
|----------|--------|
| Store extraction | Follow-up sprint, not inside Aperture |
| Shared components | `components/shared/workflow/` |
| Router changes | No immediate changes; preserve existing routes |
| Tool registry | `id: neck-setup`, `category: setup`, `status: stable` |
