# NECK-A Build Alignment Handoff

**Date:** 2026-05-06  
**Purpose:** Synchronize frontend migration sprint with NECK-A completion

---

## 1. Current Branch + Latest Commit

| Field | Value |
|-------|-------|
| Branch | `fix/wood-shrinkage-data-integrity` |
| Latest pushed commit | `81576eda` |
| Commit message | `feat(setup): add expert setup diagnostics` |
| Working tree clean | **No** |

### Uncommitted changes (unrelated to NECK-A)

Modified files (Aperture/spiral work in progress):
```
packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue
services/api/app/calculators/soundhole_calc.py
services/api/app/calculators/soundhole_facade.py
services/api/app/instrument_geometry/soundhole/spiral_geometry.py
services/api/tests/test_soundhole_spiral.py
```

Untracked files (handoffs, experimental):
```
docs/handoffs/*.md (multiple new handoff docs)
spiral_acoustic_model.py
spiral_q_fh_solver.py
test_spiral_*.py
```

**NECK-A files are clean** — all Phase 7 changes are committed.

---

## 2. Phase Status

| Phase | Status | Commit |
|-------|--------|--------|
| Phase 0: Endpoint wiring | Complete | Prior commits |
| Phase 1: Classification | Complete | Prior commits |
| Phase 2: Cleanup | Complete | Prior commits |
| Phase 3: Relief workflow | Complete | `2451c093` |
| Phase 4: Action workflow | Complete | `740f6936` |
| Phase 5: Nut workflow | Complete | `a72e40a9` |
| Phase 6: Combined diagnostics | Complete | `a72e40a9` |
| Phase 7: Expert diagnostics | Complete | `81576eda` |

**All NECK-A phases are complete.**

---

## 3. Current Frontend Structure

### Panels composed into InstrumentGeometryPanel.vue

Order (lines 211-229):
```vue
<!-- Phase 0 orphan panels -->
<SetupEvaluationPanel />
<StringTensionPanel />
<BridgePresetSelector />
<SaddleCompensationPanel />

<!-- NECK-A workflow panels -->
<SetupWorkflowReliefPanel />      <!-- Phase 3 -->
<SetupWorkflowActionPanel />      <!-- Phase 4 -->
<SetupWorkflowNutPanel />         <!-- Phase 5 -->
<SetupWorkflowCombinedPanel />    <!-- Phase 6 -->
<SetupWorkflowExpertPanel />      <!-- Phase 7 -->
```

### Known layout issues

- No visual grouping between Phase 0 orphan panels and NECK-A workflow panels
- Panels stack vertically in left control column; no collapsible sections
- No visual hierarchy indicating workflow dependencies

### Temporary UI compromises

- Prerequisite notice is inline text, not a blocking modal
- Expert symptom checkboxes use 2-column grid; could be tighter

---

## 4. Current Backend API Surface

### Setup workflow endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/instrument/setup/evaluate` | Legacy setup evaluation |
| POST | `/api/instrument/setup/workflow/evaluate` | Relief workflow (Phase 3) |
| POST | `/api/instrument/setup/workflow/action/evaluate` | Action workflow (Phase 4) |
| POST | `/api/instrument/setup/workflow/nut/evaluate` | Nut workflow (Phase 5) |
| POST | `/api/instrument/setup/workflow/combined/evaluate` | Combined diagnostics (Phase 6) |
| POST | `/api/instrument/setup/workflow/expert/evaluate` | Expert diagnostics (Phase 7) |

### Request/Response shapes

**Relief (Phase 3)**
```ts
// Request
{ relief_mm: number }

// Response
{
  overall_gate: "green" | "yellow" | "red",
  diagnostics: [{
    id: string,
    gate: string,
    message: string,
    suggested_action: string | null
  }]
}
```

**Action (Phase 4)**
```ts
// Request
{ action_mm: number }

// Response — same shape as Relief
```

**Nut (Phase 5)**
```ts
// Request
{ nut_clearance_mm: number }

// Response — same shape as Relief
```

**Combined (Phase 6)**
```ts
// Request
{
  relief_gate: string,
  relief_diagnostic_ids: string[],
  action_gate: string,
  action_diagnostic_ids: string[],
  nut_gate: string,
  nut_diagnostic_ids: string[]
}

// Response — same shape as Relief
```

**Expert (Phase 7)**
```ts
// Request
{
  symptoms: string[],
  relief_gate: string,
  relief_diagnostic_ids: string[],
  action_gate: string,
  action_diagnostic_ids: string[],
  nut_gate: string,
  nut_diagnostic_ids: string[]
}

// Response
{
  overall_gate: "green" | "yellow" | "red",
  diagnostics: [{
    id: string,
    gate: string,
    symptom: string,
    message: string,
    probable_causes: string[],
    recommended_checks: string[],
    recommended_actions: string[],
    confidence: number
  }]
}
```

### Temporary endpoints

- `/api/instrument/setup/evaluate` — legacy endpoint, kept for backward compatibility
- Consider deprecating after frontend migration confirms new workflow endpoints cover all use cases

---

## 5. Current Store State

### Added to instrumentGeometryStore.ts

```ts
// Phase 3: Relief
reliefMeasurement_mm: ref(0.2)
reliefResult: ref<ReliefWorkflowResponse | null>(null)
reliefLoading: ref(false)
reliefError: ref<string | null>(null)
evaluateRelief(): Promise<void>

// Phase 4: Action
actionMeasurement_mm: ref(2.0)
actionResult: ref<ActionWorkflowResponse | null>(null)
actionLoading: ref(false)
actionError: ref<string | null>(null)
evaluateAction(): Promise<void>

// Phase 5: Nut
nutMeasurement_mm: ref(0.5)
nutResult: ref<NutWorkflowResponse | null>(null)
nutLoading: ref(false)
nutError: ref<string | null>(null)
evaluateNut(): Promise<void>

// Phase 6: Combined
combinedResult: ref<CombinedDiagnosticsResponse | null>(null)
combinedLoading: ref(false)
combinedError: ref<string | null>(null)
canEvaluateCombined(): boolean
evaluateCombined(): Promise<void>

// Phase 7: Expert
expertSymptoms: ref<PlayerSymptom[]>([])
expertDiagnosticsResult: ref<ExpertDiagnosticsResponse | null>(null)
expertDiagnosticsLoading: ref(false)
expertDiagnosticsError: ref<string | null>(null)
toggleExpertSymptom(symptom: PlayerSymptom): void
evaluateExpertDiagnostics(): Promise<void>
```

### Known duplication / migration debt

- Pattern `{result, loading, error}` repeated 5 times — could be generic
- `canEvaluateCombined()` and expert prerequisite logic are similar
- All NECK-A state mixed with fretboard CAM state in same store (~800 lines total)
- TypeScript interfaces duplicated between store and backend models

---

## 6. Test Status

### Backend tests

```bash
pytest services/api/tests/instrument_geometry/test_setup_workflow*.py -v
```

| File | Tests | Status |
|------|-------|--------|
| test_setup_workflow.py | ~15 | Pass |
| test_setup_workflow_combined.py | ~18 | Pass |
| test_setup_workflow_expert.py | 22 | Pass |
| **Total** | **75** | **Pass** |

Coverage: 21.99% (above 20% threshold)

### Frontend type-check

```bash
npm run type-check
```

**Pre-existing errors** (NOT from NECK-A):
```
src/views/cam/headstock/WorkspaceView.vue — 10 errors
  - Missing properties: c2px, c2py, p2cx, p2cy, stage
  - Missing module: @/stores/variants
```

These errors exist on `main` branch and are unrelated to NECK-A work.

### Manual browser smoke test

**Status:** Passed (2026-05-06)

Verified:
- Expert panel renders after Combined
- Prerequisite notice shows when workflows not evaluated
- Symptom checkboxes toggle correctly
- RED diagnostic appears for buzz_low_frets + low relief
- Confidence, causes, checks, actions display
- No console errors related to NECK-A

---

## 7. Open Technical Debt

### Layout cleanup

- [ ] Add collapsible sections or tabs for panel groups
- [ ] Visual separator between Phase 0 orphan panels and NECK-A workflow
- [ ] Responsive layout for narrow viewports

### Store consolidation

- [ ] Extract NECK-A state to dedicated `neckSetupStore.ts`
- [ ] Create generic `WorkflowState<T>` pattern for {result, loading, error}
- [ ] Share TypeScript interfaces with backend (consider codegen)

### Frontend migration targets

- [ ] Extract `GateBadge.vue` from repeated CSS
- [ ] Extract `DiagnosticCard.vue` component
- [ ] Extract `PrerequisiteNotice.vue` component
- [ ] Standardize gate colors in shared CSS module

### Repeated CSS/component patterns

```css
/* Repeated in each panel CSS module */
.gateGreen { background: #065f46; color: #6ee7b7; }
.gateYellow { background: #78350f; color: #fcd34d; }
.gateRed { background: #7f1d1d; color: #fca5a5; }
```

### Intentionally deferred

- NeckEcosphere runtime — no implementation planned
- Measurement import from tap_tone_pi — future sprint
- Export/report generation — future sprint
- Undo/history for workflow state — not planned

---

## 8. What Should NOT Happen Next

| No-go | Reason |
|-------|--------|
| No CAM work | NECK-A is setup reasoning, not machining |
| No new workflow steps | Phase 7 closes the vertical slice |
| No store refactor outside migration sprint | Risk of breaking working code |
| No NeckEcosphere runtime | Not in scope, concept only |
| No changes to diagnostic rule logic | Rules are settled and tested |
| No changes to API request/response shapes | Frontend depends on current contracts |
| No changes to diagnostic IDs | Used for rule matching in Combined/Expert |

---

## 9. Recommended Next Sprint Boundary

### Frontend migration scope

**Absorb into shared infrastructure:**
```
SetupWorkflowReliefPanel.vue
SetupWorkflowActionPanel.vue
SetupWorkflowNutPanel.vue
SetupWorkflowCombinedPanel.vue
SetupWorkflowExpertPanel.vue
```

**Create shared components:**
```
packages/client/src/components/shared/
├── GateBadge.vue
├── DiagnosticCard.vue
├── PrerequisiteNotice.vue
└── workflow.module.css
```

**Extract store:**
```
packages/client/src/stores/neckSetupStore.ts
```

### Logic that must remain unchanged

- `setup_workflow.py` evaluation functions
- Diagnostic rule thresholds and IDs
- API endpoint paths and response shapes
- Gate enum values (green/yellow/red lowercase)
- Symptom enum values (snake_case)
- Confidence values (0.85 matched, 0.4 fallback)

### Rollback strategy

If migration breaks NECK-A functionality:

1. Revert frontend changes to `81576eda`
2. Keep shared components if they work
3. Re-integrate NECK-A panels incrementally
4. Run full test suite after each integration step

---

## 10. Quick Reference

**Latest safe commit:** `81576eda`

**Test command:**
```bash
pytest services/api/tests/instrument_geometry/test_setup_workflow*.py -v
```

**Type-check command:**
```bash
npm run type-check
```

**Dev server:**
```bash
# Backend
cd services/api && uvicorn app.main:app --port 8001 --reload

# Frontend
cd packages/client && npm run dev
```

**Smoke test URL:** `http://localhost:5173` → Instrument Geometry Designer
