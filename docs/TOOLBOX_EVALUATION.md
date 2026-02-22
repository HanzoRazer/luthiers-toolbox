# Luthiers Toolbox Evaluation

**Date:** 2026-02-22
**Evaluator:** Claude Code (Opus 4.5)
**Overall Score:** 7.5/10

---

## Executive Summary

Luthiers Toolbox is a capable, safety-conscious manufacturing platform with solid architecture. The RMOS decision authority and feasibility engine are particularly well-designed. Main gaps are UX polish (simulation, undo) and accumulation of technical debt in the UI layer.

---

## Strengths

### 1. Comprehensive Domain Coverage
- Covers the full luthier workflow: design → CAM → manufacturing → quality assurance
- Integrates acoustic analysis (tap_tone_pi), CAM generation, feasibility checking, and RMOS decision authority
- Smart Guitar integration bridges traditional lutherie with IoT/connected instruments

### 2. Strong Architecture Patterns
- **RMOS** (Run Management & Orchestration System) provides clear decision authority
- **Content-addressed storage** (CAS) for artifacts ensures traceability
- **Feasibility engine** with 22+ rules prevents unsafe machining operations
- Clean separation: UI → SDK → API → Services

### 3. Safety-First Manufacturing
- RED/YELLOW/GREEN risk levels with human-readable explanations
- Adversarial detection rules (F020-F029) block dangerous operations
- Override audit trail for accountability
- 30-run validation protocol for release gates

---

## Weaknesses

### 1. UI Complexity
- Components like `AdaptivePocketLab.vue` grew to 1200+ lines before decomposition
- Many views mix concerns (data fetching, state, rendering, business logic)
- Decomposition work achieved 60.9% reduction but should continue across other large components

### 2. Test Coverage Gaps
- Tests occasionally written for different implementation than actual code
- Missing integration tests for critical paths (CAM → RMOS → export)
- Vue lifecycle warnings in tests suggest composables need dedicated test utilities

### 3. Documentation Fragmentation
- Domain knowledge scattered across code comments, markdown files, and copilot-instructions
- No centralized "how the system works" guide for new contributors

---

## Recommended Additions

| Priority | Element | Rationale |
|----------|---------|-----------|
| **High** | **Simulation Preview** | Visual 3D toolpath simulation before cutting - critical for operator confidence |
| **High** | **Undo/History System** | No way to revert changes in design workflows; single mistakes require restart |
| **High** | **Offline Mode** | Luthiers often work in shops without reliable internet |
| **Medium** | **Material Library** | Hardcoded materials; need user-extensible wood species database with cutting parameters |
| **Medium** | **Tool Library** | User should define their actual tooling inventory with wear tracking |
| **Medium** | **Cost Estimation** | Time + material + tooling wear estimates before committing to a job |
| **Low** | **Multi-language (i18n)** | Internationalization for global luthier community |
| **Low** | **Mobile Companion** | Monitor running jobs, receive alerts from shop floor |

---

## Technical Debt

### Immediate Priority
1. **Legacy vision stack** (`_experimental/ai_graphics`) needs migration to canonical `app.vision`
2. **Fence baseline** has 126 symbol violations to clean up gradually

### Ongoing
3. **Large components** still exist and need decomposition:
   - `DxfToGcodeView.vue`
   - `RmosRunViewerView.vue`
   - `SawBatchPanel.vue`
   - `BlueprintImporter.vue`

4. **Inconsistent naming conventions**:
   - Preset keys: snake_case (`les_paul`) vs camelCase (`lesPaul`)
   - API responses: mixed conventions

### Resolved (Recent)
- `AdaptivePocketLab.vue`: 1283 → 502 lines (−60.9%) via composable extraction
- `useGuitarDimensions` tests: aligned with actual composable behavior

---

## Architecture Highlights

### RMOS Decision Authority
```
Request → Feasibility Engine → Decision (GREEN/YELLOW/RED) → Gated Export
                ↓
         22+ Safety Rules
         Override Audit Trail
         Explanation Generation
```

### Composable Pattern (Recommended)
```typescript
// Config: static dependencies (refs from parent)
interface ComposableConfig {
  toolD: Ref<number>
  postId: Ref<string>
}

// Deps: dynamic dependencies (functions, other composable outputs)
interface ComposableDeps {
  plan: () => Promise<void>
  moves: Ref<Move[]>
}

// State: what this composable provides
interface ComposableState {
  result: Ref<Result>
  execute: () => Promise<void>
}

export function useComposable(config: Config, deps: Deps): State
```

---

## Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Client Tests | 358 passing | 17 skipped (Wave 6 pending) |
| API Tests | ~1150 passing | Full coverage of RMOS, CAM, Art Studio |
| Feasibility Rules | 22 | F001-F007 (core), F010-F013 (warnings), F020-F029 (adversarial), F030-F041 (edge) |
| Composables Extracted | 12 | From AdaptivePocketLab alone |
| Line Reduction | 60.9% | AdaptivePocketLab: 1283 → 502 lines |

---

## Recommendations Summary

1. **Continue composable extraction** - Apply same pattern to remaining large components
2. **Add simulation preview** - Highest-impact UX improvement for operator confidence
3. **Implement undo system** - Critical for design workflow usability
4. **Clean fence violations** - Gradually reduce 126 baseline violations to 0
5. **Centralize documentation** - Create "System Architecture" guide consolidating domain knowledge

---

## Appendix: Files Analyzed

- `packages/client/src/components/AdaptivePocketLab.vue`
- `packages/client/src/components/adaptive/composables/*.ts`
- `packages/client/src/components/toolbox/composables/useGuitarDimensions.ts`
- `packages/client/src/testing/__tests__/toolbox-composables.test.ts`
- `services/api/app/rmos/feasibility/`
- `services/api/app/rmos/validation/`
- `docs/RMOS_FEASIBILITY_RULES_v1.md`
