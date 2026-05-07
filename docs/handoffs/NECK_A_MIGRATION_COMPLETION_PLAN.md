# NECK-A Migration Completion Plan

**Date:** 2026-05-06  
**Status:** Ready to execute  
**Prerequisite:** Phase 7 complete @ `81576eda`

---

## Sprint Goal

```
Finish frontend migration WITHOUT changing behavior of NECK-A system
```

Success =

```
Same inputs → same diagnostics → cleaner UI + store
```

---

## Core Rule (non-negotiable)

```
Migration = structural changes only
NOT behavioral changes
```

If a diagnostic changes → rollback that change.

---

## Phase M1 — Stabilize Entry Points (1 day)

### Goal

Stop further drift.

### Actions

Freeze:
- `setup_workflow.py`
- all `/setup/workflow/*` endpoints

Add comment banner in code:

```python
# MIGRATION LOCK:
# Do not modify API shape or diagnostic logic during frontend migration.
```

```ts
// MIGRATION LOCK:
// Do not modify API shape or diagnostic logic during frontend migration.
```

---

## Phase M2 — Extract Shared UI Primitives (1–2 days)

### Goal

Remove duplication without touching logic.

### Create

```
packages/client/src/components/shared/
```

### Extract

**1. GateBadge.vue**

From repeated CSS:
```css
.gateGreen / .gateYellow / .gateRed
```

**2. DiagnosticCard.vue**

Props:
```ts
{
  gate,
  message,
  probable_causes?,
  recommended_checks?,
  recommended_actions?,
  confidence?
}
```

**3. PrerequisiteNotice.vue**

Used by:
- Combined
- Expert

### Replace in all panels

```
Relief
Action
Nut
Combined
Expert
```

No logic change. Only rendering.

---

## Phase M3 — Normalize Response Handling (1 day)

### Goal

Unify frontend expectations without touching backend.

### Fix inconsistency

```
Relief → diagnostics[0].gate
Others → overall_gate
```

### Add adapter layer in store

```ts
function getOverallGate(result) {
  return result.overall_gate ?? result.diagnostics?.[0]?.gate
}
```

Do NOT change backend.

---

## Phase M4 — Extract Dedicated Store (2 days)

### Goal

Remove NECK-A from monolithic store safely.

### Create

```
packages/client/src/stores/neckSetupStore.ts
```

### Move

```ts
relief*
action*
nut*
combined*
expert*
```

### Keep API identical

```ts
evaluateRelief()
evaluateAction()
evaluateNut()
evaluateCombined()
evaluateExpertDiagnostics()
```

### In old store

```ts
// TEMP BRIDGE
export { useNeckSetupStore } from './neckSetupStore'
```

No component breaks.

---

## Phase M5 — Component Recomposition (2–3 days)

### Goal

Replace panel stack with structured layout.

### Create structure

```
components/workflow/
  WorkflowSection.vue
  WorkflowStep.vue
```

### Group UI

```
Measurement Steps:
  Relief
  Action
  Nut

Diagnostics:
  Combined
  Expert
```

### DO NOT

- change panel logic
- merge steps
- add wizard behavior

---

## Phase M6 — Clean InstrumentGeometryPanel.vue (1–2 days)

### Goal

Turn 500-line file into composition shell.

### Replace

```vue
<SetupWorkflowReliefPanel />
...
```

With:

```vue
<WorkflowSection title="Setup Measurements">
  <ReliefStep />
  <ActionStep />
  <NutStep />
</WorkflowSection>

<WorkflowSection title="Diagnostics">
  <CombinedDiagnostics />
  <ExpertDiagnostics />
</WorkflowSection>
```

---

## Phase M7 — Remove Duplication + Dead Code (1 day)

### Remove

- duplicated gate CSS
- inline diagnostic rendering
- repeated loading/error blocks

---

## Phase M8 — Full Regression Pass (CRITICAL)

### Run

```bash
pytest services/api/tests/instrument_geometry/test_setup_workflow*.py
npm run type-check
```

### Manual browser test

Verify ALL:

```
Relief
Action
Nut
Combined
Expert
```

Still produce **identical outputs**.

---

## Phase M9 — Commit Strategy

Do NOT do one giant commit.

Split:

```
1. shared components
2. store extraction
3. component restructuring
4. cleanup
```

---

## High-Risk Areas

### 1. Diagnostic ID usage

```
Combined + Expert depend on IDs
```

Never rename them.

### 2. Gate normalization

Mistake here = wrong diagnostics.

### 3. Store refactor

Biggest risk. Keep API identical.

### 4. Component extraction

Easy to accidentally drop props.

---

## Hard NOs During This Sprint

```
NO CAM
NO new workflow steps
NO rule changes
NO API changes
NO adding "smart UX"
NO async orchestration changes
```

---

## Definition of Done

```
- UI cleaner
- store separated
- components reusable
- ZERO behavior change
- all tests pass
- smoke test identical results
```

---

## Next Support Options

### 1. Migration diff review before commit

Use when frontend migration has active changes.

Review for:
- accidental API contract changes
- diagnostic ID changes
- gate logic changes
- lost prerequisite checks
- store behavior drift
- broken panel wiring
- duplicated migration code
- changes that belong in later sprint

Inputs needed:
- git diff or changed files list
- current test/typecheck status
- any known failing UI behavior

### 2. Phase 8 direction plan

Use after migration is complete and stable.

Choose one direction:

**A. Manufacturing path**
- nut slot CAM
- toolpath JSON
- G-code later
- bridge into existing CAM orchestrator

**B. Expert-system path**
- richer buzz localization
- player feel modeling
- setup presets
- confidence tuning
- diagnostic history later

Inputs needed:
- whether migrated UI is stable
- business priority: shop output vs smarter guidance
- available dev time
- whether physical production needs nut CAM soon

---

## Final Note

You're not building anymore.

You're **preserving a working system while reshaping it**.

That's harder than building.
