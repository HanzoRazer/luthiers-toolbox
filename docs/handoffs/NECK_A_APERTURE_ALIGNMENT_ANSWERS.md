# NECK-A Architecture Questions — Answers for Aperture Sprint

**Date:** 2026-05-06  
**From:** NECK-A Phase 7 implementation  
**To:** Aperture Workspace sprint

---

## Summary

The honest answer to most questions: **not yet abstracted**.

NECK-A delivered working vertical slices (Relief → Action → Nut → Combined → Expert) but did not create shared infrastructure. The patterns exist in code but are not extracted into reusable components.

This creates an opportunity: **Aperture can define the abstractions** that both workspaces will use.

---

## Q1 — Is the workspace shell abstracted?

**Answer: No.**

The orchestration is embedded directly in `InstrumentGeometryPanel.vue`. There is no `NeckSetupWorkspace.vue` wrapper yet — that was a recommendation in the handoff, not an implemented reality.

Current structure:

```vue
<!-- InstrumentGeometryPanel.vue -->
<SetupWorkflowReliefPanel />
<SetupWorkflowActionPanel />
<SetupWorkflowNutPanel />
<SetupWorkflowCombinedPanel />
<SetupWorkflowExpertPanel />
```

No shell component wraps these. No orchestration abstraction exists.

**Recommendation:** Aperture sprint should define the workspace shell pattern. NECK-A will adopt it.

---

## Q2 — Is there a canonical diagnostic workflow abstraction?

**Answer: No.**

The panels are hardcoded sequences. They share conceptual patterns but no `WorkflowStage`, `WorkflowDiagnostic`, `WorkflowGate`, or `WorkflowDependency` abstractions exist in code.

What exists (patterns, not abstractions):

```ts
// Repeated in each panel, not extracted
interface SomeWorkflowResponse {
  overall_gate: DiagnosticGate
  diagnostics: SomeDiagnostic[]
}
```

**Recommendation:** Create shared types:

```ts
// packages/client/src/types/workflow.ts
interface WorkflowGate {
  level: 'green' | 'yellow' | 'red'
}

interface WorkflowDiagnostic {
  id: string
  gate: WorkflowGate
  message: string
}

interface WorkflowResponse<D extends WorkflowDiagnostic> {
  overall_gate: WorkflowGate
  diagnostics: D[]
}
```

Both NECK-A and Aperture can extend these.

---

## Q3 — Are gate badges and diagnostic cards promoted to shared components?

**Answer: No.**

These are local CSS module patterns inside each NECK-A panel:

```css
/* SetupWorkflowExpertPanel.module.css */
.gateGreen { background: #065f46; color: #6ee7b7; }
.gateYellow { background: #78350f; color: #fcd34d; }
.gateRed { background: #7f1d1d; color: #fca5a5; }
```

No `GateBadge.vue` or `DiagnosticCard.vue` exists yet.

**Recommendation:** Aperture sprint should create:

```
packages/client/src/components/shared/
├── GateBadge.vue
├── DiagnosticCard.vue
├── PrerequisiteNotice.vue
└── workflow.module.css
```

NECK-A panels will refactor to use them.

---

## Q4 — What is the intended store architecture?

**Answer: Currently monolithic, no platform rule established.**

All NECK-A state lives in `instrumentGeometryStore.ts` alongside unrelated fretboard/CAM state. The handoff proposed extracting to `neckSetupStore.ts` but this has not happened.

Current state:

```ts
// instrumentGeometryStore.ts - ~800 lines, mixed concerns
export const useInstrumentGeometryStore = defineStore('instrumentGeometry', () => {
  // Fretboard CAM state
  // Setup workflow state (Relief, Action, Nut, Combined, Expert)
  // Bridge preset state
  // String tension state
  // ... everything
})
```

**Recommendation:** Establish the rule now:

```
stores/
├── apertureWorkspaceStore.ts    # Aperture owns this
├── neckSetupStore.ts            # Extract from instrumentGeometryStore
├── rosetteWorkspaceStore.ts     # Future
└── instrumentGeometryStore.ts   # Fretboard CAM only
```

One store per workspace as platform convention.

---

## Q5 — Is the Tool Registry finalized?

**Answer: No Tool Registry exists.**

Grep confirms no `ToolRegistry`, `WorkflowStage`, or `WorkflowGate` abstractions in `packages/client/src`.

Current tool discovery is implicit via Vue Router and sidebar hardcoding.

**Recommendation:** Define the registry schema:

```ts
// packages/client/src/registry/toolRegistry.ts
interface WorkspaceTool {
  id: string
  category: 'aperture' | 'neck' | 'rosette' | 'calculator'
  route: string
  icon: string
  status: 'stable' | 'beta' | 'experimental'
  capabilities: {
    export: ('dxf' | 'svg' | 'json' | 'gcode')[]
    import: ('measurement' | 'preset')[]
  }
}
```

Both sprints register their tools. Sidebar renders from registry.

---

## Q6 — Are export systems becoming shared infrastructure?

**Answer: No, each system exports independently.**

NECK-A has no export system — diagnostics display only.

Fretboard CAM has hardcoded DXF/G-code export in the store:

```ts
downloadDxf() { /* inline blob creation */ }
downloadGcode() { /* inline blob creation */ }
```

Spiral soundhole has its own DXF export path.

**Recommendation:** Create shared export infrastructure:

```ts
// packages/client/src/services/exportService.ts
interface ExportService {
  exportDxf(geometry: ApertureGeometry | FretboardGeometry): Blob
  exportSvg(geometry: any): Blob
  exportJson(data: any): Blob
  downloadFile(blob: Blob, filename: string): void
}
```

Both workspaces use the same service.

---

## Q7 — Is there a canonical canvas abstraction?

**Answer: Mixed, no standard.**

Current rendering approaches:

| Component | Rendering |
|-----------|-----------|
| `FretboardPreviewSvg.vue` | Inline SVG |
| `SpiralSoundholeDesigner.vue` | SVG via computed paths |
| Other previews | Mixed |

No Konva, no shared Canvas2D wrapper.

**Recommendation:** Standardize on SVG for geometry preview:

```ts
// packages/client/src/components/shared/GeometryCanvas.vue
<svg :viewBox="viewBox">
  <slot />  <!-- Workspace-specific geometry -->
</svg>
```

With shared utilities for:
- Zoom/pan
- Grid overlay
- Measurement display
- Export to SVG file

---

## Q8 — Is the workflow routing hierarchical or flat?

**Answer: Currently flat.**

Current routes (inferred from component locations):

```
/art-studio/soundhole-designer   → SoundholeDesignerView.vue
/instrument-geometry             → InstrumentGeometryPanel.vue (contains NECK-A)
```

No `/art-studio/neck` or `/art-studio/aperture` hierarchy yet.

**Recommendation:** Adopt hierarchical structure:

```
/art-studio
├── /aperture      → ApertureWorkspace.vue
├── /neck          → NeckSetupWorkspace.vue
├── /rosette       → RosetteWorkspace.vue
└── /calculators   → ShopCalculatorWorkspace.vue
```

Each workspace has sub-routes for panels if needed.

---

## Q9 — Is Expert Diagnostics intended to become generic?

**Answer: Currently neck-specific, but the pattern is generalizable.**

The Expert evaluator signature:

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

The pattern:

```
user-reported observations + measured state → rule matching → diagnostics with confidence
```

This is identical to what Aperture inverse calibration will need:

```
measured f_H, Q + geometry → rule matching → acoustic diagnostics with confidence
```

**Recommendation:** Extract the pattern to a generic expert evaluator framework:

```python
# services/api/app/diagnostics/expert_framework.py
class ExpertRule(Protocol):
    def matches(self, observations: List[str], measured_state: Dict) -> bool
    def diagnose(self, observations: List[str], measured_state: Dict) -> Diagnostic

class ExpertEvaluator:
    def __init__(self, rules: List[ExpertRule]):
        self.rules = rules
    
    def evaluate(self, observations: List[str], measured_state: Dict) -> DiagnosticsResponse:
        # Generic rule matching with confidence
```

NECK-A Expert and Aperture Inverse Solver both use this framework.

---

## Q10 — Is measurement import becoming a shared platform feature?

**Answer: No shared framework exists.**

NECK-A measurements are manual input fields. No file import.

`tap_tone_pi` viewer packs are not currently consumed by `luthiers-toolbox`.

**Recommendation:** Define measurement import interface:

```ts
// packages/client/src/services/measurementImportService.ts
interface MeasurementImportService {
  importViewerPack(file: File): Promise<TapToneMeasurement>
  importSetupMeasurements(file: File): Promise<SetupMeasurement>
  parseFrequencyResponse(data: ArrayBuffer): FrequencyData
}
```

Aperture uses this for `tap_tone_pi` integration. NECK-A could use it for saved setup profiles.

---

## Summary: What Aperture Should Build

### Safe to build now (backend-only, no frontend abstraction dependency):

1. `ApertureGeometry` dataclass
2. `aperture_inverse_solver.py`
3. Compare `soundhole_calc.py` vs `soundhole_designer.html`
4. Backend acoustic abstractions
5. Tests

### Should build as shared infrastructure (Aperture defines, NECK-A adopts):

1. `GateBadge.vue`, `DiagnosticCard.vue`, `PrerequisiteNotice.vue`
2. `WorkflowResponse`, `WorkflowDiagnostic` TypeScript types
3. `ToolRegistry` schema
4. `ExportService`
5. `GeometryCanvas.vue` with zoom/pan
6. Store-per-workspace convention

### Hold until both sprints align:

1. Workspace shell pattern
2. Route hierarchy
3. Panel orchestration
4. Measurement import framework
5. Generic expert evaluator framework

---

## Proposed Coordination

The Aperture sprint should:

1. **Define shared components** in `packages/client/src/components/shared/`
2. **Define shared types** in `packages/client/src/types/`
3. **Define store convention** and extract `apertureWorkspaceStore.ts`
4. **Document patterns** in a short architecture ADR

NECK-A will:

1. **Refactor to use shared components** once they exist
2. **Extract `neckSetupStore.ts`** following the same convention
3. **Adopt route hierarchy** when established

This way Aperture leads the infrastructure, NECK-A validates it works.

---

## Contact

Questions about NECK-A implementation details:
- Backend logic: `services/api/app/instrument_geometry/neck/setup_workflow.py`
- Frontend panels: `packages/client/src/components/SetupWorkflow*.vue`
- Store: `packages/client/src/stores/instrumentGeometryStore.ts`
