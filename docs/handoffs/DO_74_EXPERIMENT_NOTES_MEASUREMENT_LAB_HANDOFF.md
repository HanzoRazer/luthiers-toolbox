# Dev Order 74: Experiment Notes Layer — Measurement Lab

**Sprint:** Measurement Lab  
**Order:** DO 74  
**Status:** COMPLETE  
**Date:** 2026-05-25

---

## Executive Summary

Dev Order 74 adds an experiment notes layer to the Measurement Lab, enabling human-entered observational annotations that attach to measurement records. Notes preserve interpretation alongside archives, residuals, correlations, drift timelines, and synthesis records.

**Key principle:** Notes are OBSERVATIONAL ONLY. They do not establish authority, alter measurement data, or imply calibration or recommendation.

---

## Deliverables

| Deliverable | Path | Status |
|-------------|------|--------|
| Types | `packages/client/src/types/acoustics/experimentNote.ts` | COMPLETE |
| Utilities | `packages/client/src/utils/acoustics/experimentNote.ts` | COMPLETE |
| Component | `packages/client/src/components/shared/acoustics/ExperimentNotesPanel.vue` | COMPLETE |
| Tests | `packages/client/src/utils/acoustics/__tests__/experimentNote.test.ts` | COMPLETE |
| Barrel export | `packages/client/src/components/shared/acoustics/index.ts` | UPDATED |

---

## Architecture

### Type System

```typescript
// Target types that notes can attach to
type ExperimentNoteTargetType =
  | 'archive'           // Measurement archives
  | 'topologyVariant'   // Topology variant records
  | 'residualComparison'// Pairwise residual comparisons
  | 'correlation'       // Computed correlations
  | 'driftRecord'       // Individual drift observations
  | 'driftSynthesis'    // Session-level drift synthesis

// Core note record
interface ExperimentNote {
  noteId: string                    // Unique identifier
  targetType: ExperimentNoteTargetType
  targetId: string                  // ID of target record
  text: string                      // Note content
  createdAt: string                 // ISO timestamp
  updatedAt?: string                // Future expansion
  tags?: string[]                   // Optional categorization
}
```

### Utility Functions

| Function | Purpose |
|----------|---------|
| `createExperimentNote()` | Create and validate a new note |
| `validateExperimentNote()` | Validate note structure |
| `normalizeExperimentNote()` | Immutable normalization |
| `filterNotesByTarget()` | Filter by target type |
| `filterNotesByTargetId()` | Filter by target ID |
| `summarizeExperimentNotes()` | Summarize by target type |
| `dedupeExperimentNotes()` | Remove duplicate IDs |
| `buildExperimentNoteLabel()` | Generate display label |
| `getTargetTypeLabel()` | Human-readable type labels |
| `normalizeTags()` | Parse comma-separated tags |
| `isValidTargetType()` | Type guard |

### Component Features

**ExperimentNotesPanel.vue:**
- Add note form with target type selector
- Note list with filtering by target type
- Summary badges showing note counts
- Tag display and input
- Timestamp formatting
- Empty state handling

---

## Observational Authority Boundary

### Notes Do NOT:

- Establish measurement authority
- Alter raw measurement data
- Imply calibration status
- Provide recommendations
- Validate or prove results
- Create causal relationships

### Notes DO:

- Preserve human observations
- Attach context to records
- Enable categorization via tags
- Support filtering and summarization
- Maintain audit trail via timestamps

### Forbidden Language (enforced in tests)

The following words are forbidden in utility output strings:

```text
improve, improved, improves, improvement
optimize, optimized, optimizes, optimization
better, best
fix, fixed, fixes
recommend, recommended, recommends, recommendation
validate, validated, validates, validation
calibrate, calibrated, calibrates, calibration
prove, proves, proven, proved
cause, causes, caused, causation
correct, corrected, corrects
authority, authoritative
```

---

## Storage Model

**Current:** In-memory only (no persistence backend)

Notes exist only for the duration of the browser session. This is intentional for the initial implementation.

**Future considerations:**
- Local storage persistence
- Export/import with archives
- Server-side storage (requires API endpoint)

---

## Test Coverage

### Test File

`packages/client/src/utils/acoustics/__tests__/experimentNote.test.ts`

### Test Categories (Dev Order 74 + 75)

| Category | Tests | Purpose |
|----------|-------|---------|
| Target type validation | 3 | Valid types accepted, invalid rejected |
| Tag normalization | 5 | Split, trim, dedupe, empty handling |
| Note validation | 7 | Required fields, empty values |
| Note creation | 6 | Valid creation, trimming, tags |
| Note normalization | 7 | Immutable, preserves fields |
| Filtering | 3 | By type, by ID |
| Summarization | 2 | Aggregate by type |
| Deduplication | 2 | Remove duplicate IDs |
| Label generation | 3 | Stable output, truncation |
| Immutability (DO 75) | 4 | Input not mutated |
| Language compliance (DO 75) | 3 | No forbidden words |

### Running Tests

```bash
cd packages/client
npm test -- experimentNote.test.ts
```

---

## Integration Points

### Component Barrel Export

```typescript
// packages/client/src/components/shared/acoustics/index.ts
export { default as ExperimentNotesPanel } from './ExperimentNotesPanel.vue'
```

### Utility Barrel Export

```typescript
// packages/client/src/utils/acoustics/index.ts
export * from './experimentNote'
```

### Usage in Views

```vue
<script setup lang="ts">
import { ExperimentNotesPanel } from '@/components/shared/acoustics'
</script>

<template>
  <ExperimentNotesPanel />
</template>
```

---

## Target Type Mapping

| Target Type | Measurement Lab Component | Dev Order |
|-------------|---------------------------|-----------|
| `archive` | MeasurementArchive* | DO 60 |
| `topologyVariant` | TopologyVariant* | DO 66 |
| `residualComparison` | MeasurementResidualComparisonPanel | DO 63 |
| `correlation` | ExperimentalCorrelationPanel | DO 68 |
| `driftRecord` | ExperimentalDriftTimelinePanel | DO 70 |
| `driftSynthesis` | ExperimentalDriftSynthesisPanel | DO 72 |

---

## Dev Order Lineage

```
DO 60: Measurement Archive Workflow
    |
DO 62: Archive Evidence Index
    |
DO 63: Residual Comparison Panel
    |
DO 66: Topology Variants
    |
DO 68: Experimental Correlations
    |
DO 70: Drift Timeline
    |
DO 72: Drift Synthesis
    |
DO 74: Experiment Notes  <-- YOU ARE HERE
    |
DO 75: QA & Notebook Hardening
    |
DO 76: Evidence Review Panel
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| DO 75 handoff | QA and immutability verification |
| DO 76 handoff | Evidence review panel (uses notes) |
| Measurement Lab architecture | Overall system design |

---

## Known Limitations

1. **No persistence** — Notes are lost on page refresh
2. **No edit/delete** — Notes can only be added, not modified
3. **No attachment to note** — Cannot attach files/images
4. **No search** — Must filter by type, no text search
5. **Single user** — No multi-user collaboration

---

## Future Work

| Item | Priority | Dependency |
|------|----------|------------|
| Edit/delete notes | P2 | None |
| Local storage persistence | P2 | None |
| Export notes with archives | P3 | Archive export format |
| Server-side storage | P3 | API endpoint |
| Text search | P3 | None |
| Rich text/markdown | P3 | Editor component |

---

## Acceptance Criteria

- [x] Types defined for experiment notes
- [x] Utilities for create, validate, filter, summarize
- [x] Vue component for note display and entry
- [x] Tests pass (17+ test cases)
- [x] Immutability verified (DO 75)
- [x] Language compliance verified (DO 75)
- [x] Barrel exports updated
- [x] Notes attach to all 6 target types
- [x] No authority claims in UI text

---

## Developer Notes

### Adding a New Target Type

1. Add to `ExperimentNoteTargetType` in `experimentNote.ts`
2. Add to `VALID_TARGET_TYPES` array
3. Add case to `getTargetTypeLabel()` switch
4. Update tests in `experimentNote.test.ts`
5. Update this handoff document

### Styling

The component uses CSS custom properties for theming:

```css
--color-background-soft
--color-border
--color-text
--color-text-muted
--color-primary
--color-primary-hover
--color-error
--color-error-bg
```

---

*Handoff version: 2026-05-25*  
*Dev Order: 74*  
*Sprint: Measurement Lab*
