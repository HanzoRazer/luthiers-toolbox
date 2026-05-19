# Snapshot Exchange Architecture

**Status:** Stable  
**Version:** 1.0  
**Date:** 2026-05-14  
**Dev Orders:** 36–51

---

## Overview

Snapshot Exchange is a client-side observational snapshot subsystem within the Aperture Workspace. It enables users to export and validate diagnostic snapshots without server interaction, persistence, or state restoration.

```
Snapshot Exchange
├── Diagnostic Snapshot      — structured observational state
├── Export Metadata          — package metadata and warnings
├── JSON Export              — client-side download
└── Import Validation        — schema compatibility check
```

**Purpose:** Client-side observational snapshot exchange without restore or persistence.

---

## Architectural Constraints

Snapshot Exchange operates under strict observational boundaries:

| Constraint | Description |
|------------|-------------|
| Observational only | Captures diagnostic state, not calibrated results |
| Non-calibrating | Does not perform or store calibration |
| Non-predictive | Does not generate predictions or recommendations |
| Non-restoring | Import validation does not restore application state |
| Non-persistent | No backend storage, no database writes |
| Client-side only | All operations occur in-browser |

**Key statements:**

- Import validation checks schema compatibility only.
- JSON export preserves observational state only.
- No API calls occur during export or import.

---

## Snapshot Schema

### Schema Identifiers

| Field | Value |
|-------|-------|
| `schemaVersion` | `diagnostic-snapshot.v1` |
| `kind` | `aperture-diagnostic-snapshot` |

### Schema Structure

```typescript
interface DiagnosticSnapshot {
  schemaVersion: string           // 'diagnostic-snapshot.v1'
  kind: string                    // 'aperture-diagnostic-snapshot'
  createdAtIso: string            // ISO 8601 timestamp
  readinessLevel: string | null   // diagnostic readiness classification
  exportReady: boolean            // export eligibility flag
  exportWarnings: string[]        // warnings for export package
  narrativeSummary: string | null // human-readable summary
  provenanceReminder: string      // observational-only reminder
  sections: DiagnosticSnapshotSection[]
}

interface DiagnosticSnapshotSection {
  label: string
  summary: string
  available: boolean
}
```

### Export Metadata

```typescript
interface DiagnosticSnapshotExportMetadata {
  schemaVersion: string           // matches snapshot schema
  kind: string                    // matches snapshot kind
  generatedBy: string             // 'aperture-workspace'
  exportStatus: string            // 'prepared_not_exported' | 'exported_json'
  exportPreparedAtIso: string     // ISO 8601 timestamp
}
```

---

## Export Workflow

```
Diagnostic State
    ↓
Diagnostic Snapshot (normalized)
    ↓
Export Metadata (attached)
    ↓
JSON Payload (assembled)
    ↓
Client-side Download (triggered)
```

### Workflow Details

1. **Snapshot normalization** — Current diagnostic state assembled into `DiagnosticSnapshot`
2. **Export metadata** — Package metadata attached with schema version and timestamp
3. **JSON assembly** — Complete payload prepared for download
4. **Client download** — Browser triggers file download via blob URL

**No backend/API calls occur.**

### Export Eligibility

Export requires:
- `exportReady === true`
- Valid schema version
- At least one available section

---

## Import Validation Workflow

```
JSON File Selection
    ↓
File Read (FileReader API)
    ↓
JSON Parse
    ↓
Schema Validation
    ↓
Diagnostic Result (gate + messages)
```

### Workflow Details

1. **File selection** — User selects `.json` file via file input
2. **File read** — Browser reads file content as text
3. **JSON parse** — Content parsed as JSON (parse errors caught)
4. **Schema validation** — Structure validated against expected schema
5. **Diagnostic result** — Validation gate (green/yellow/red) and diagnostic messages

**No restore or state mutation occurs.**

### Validation Checks

| Check | Description |
|-------|-------------|
| Schema version | Must match `diagnostic-snapshot.v1` |
| Kind | Must match `aperture-diagnostic-snapshot` |
| Required fields | `createdAtIso`, `sections` must exist |
| Section structure | Each section must have `label`, `summary`, `available` |

---

## UX Refinement Principles

Snapshot Exchange follows these UX principles established through Dev Orders 44–51:

### Visual Hierarchy

| Card | Role | Styling |
|------|------|---------|
| Diagnostic Snapshot | Primary | Accent border, larger heading |
| Export Metadata | Secondary | Muted border, smaller heading |
| Import Validation | Utility | Compact, functional |

### Interaction Philosophy

```
tool-like
structured
observational
non-alarming
diagnostic
```

### Design Tokens

| Property | Value |
|----------|-------|
| Transition duration | `0.15s ease` |
| Focus ring | `box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.5)` |
| Background opacity | `0.08` for diagnostic panels |
| Canonical spacing | `0.375rem` / `0.5rem` / `0.75rem` / `1rem` |

### Information Chunking

Metadata grouped under inline labels:
- **Schema** — version, kind
- **Export State** — readiness, status, timestamp

Sections separated by subtle bottom borders for scanability.

### Density Handling

- Tightened grid gaps (`0.375rem`)
- Bullet prefixes on warnings for scanability
- Reduced diagnostic row margins
- Notices separated from primary content

---

## Warning Ownership

**Final ownership rule:**

```
Export warnings belong to Export Metadata.
```

**Display rules:**

- Warnings appear once (in Export Metadata card only)
- Warning label is "Export Warnings"
- Bullet prefix (•) for each warning
- Warnings are informational, not alarming

**Warning sources:**

- Unavailable sections
- Sparse snapshot state
- Schema compatibility notes

---

## Known Non-Goals

Snapshot Exchange explicitly does **not** implement:

| Non-Goal | Reason |
|----------|--------|
| Session restore | Snapshots are observational, not restorable state |
| Cloud sync | No backend integration |
| Database persistence | Client-side only |
| Report generation | Out of scope for diagnostic scaffolding |
| PDF export | JSON-only for schema validation |
| Calibration | Observational constraints |
| Recommendation engine | Non-predictive |
| Prediction | Non-calibrating |
| Schema migration | Single stable schema version |
| Upload to server | Non-persistent |

---

## Component Files

| Component | Path |
|-----------|------|
| Snapshot Card | `packages/client/src/components/shared/acoustics/DiagnosticSnapshotCard.vue` |
| Export Metadata Card | `packages/client/src/components/shared/acoustics/DiagnosticSnapshotExportMetadataCard.vue` |
| Import Validation Card | `packages/client/src/components/shared/acoustics/DiagnosticSnapshotImportCard.vue` |
| Section Container | `packages/client/src/components/shared/acoustics/SnapshotExchangeSection.vue` |

| Utility | Path |
|---------|------|
| Snapshot utils | `packages/client/src/utils/acoustics/diagnosticSnapshot.ts` |
| Export utils | `packages/client/src/utils/acoustics/diagnosticSnapshotExport.ts` |
| Import utils | `packages/client/src/utils/acoustics/diagnosticSnapshotImport.ts` |

| Types | Path |
|-------|------|
| Snapshot types | `packages/client/src/types/diagnosticSnapshot.ts` |
| Import types | `packages/client/src/types/diagnosticSnapshotImport.ts` |

---

## Dev Order History

| Order | Purpose |
|-------|---------|
| 36 | Diagnostic Session Snapshot scaffold |
| 37 | Export preparation (schema versioning) |
| 38 | JSON export (client-side download) |
| 39 | Import validation |
| 40 | Export/import roundtrip verification |
| 41 | Export metadata review card |
| 42 | Section consolidation |
| 43 | Warning display cleanup |
| 44 | Empty-state refinement |
| 45 | Visual state hierarchy |
| 46 | Typography & spacing harmonization |
| 47 | Interaction state polish |
| 48 | Micro-interaction consistency |
| 49 | State density refinement |
| 50 | Information chunking refinement |
| 51 | Final UX checkpoint |
| 52 | Documentation & architecture consolidation |

---

## References

- Status document: [APERTURE_WORKSPACE_REFACTOR_STATUS.md](./APERTURE_WORKSPACE_REFACTOR_STATUS.md)
- Workflow primitives: `packages/client/src/components/shared/workflow/`
- Acoustics index: `packages/client/src/components/shared/acoustics/index.ts`
