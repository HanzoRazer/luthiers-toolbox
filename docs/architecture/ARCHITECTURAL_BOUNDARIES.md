# Architectural Boundaries

**Status:** Stable  
**Date:** 2026-05-14  
**Sprint:** Phase-3B Closure

---

## Overview

This document defines the architectural layer boundaries for the Aperture Workspace and related acoustic subsystems. These boundaries govern where code lives, how contracts evolve, and what guarantees each layer provides.

---

## Layer Definitions

### 1. Canonical Layer

**Characteristics:**
- Stable
- Production-oriented
- Governed
- Non-experimental

**Rules:**
- No experimental acoustic logic
- No observational diagnostics
- No unstable prediction helpers
- Migration by governed extraction only
- Changes require regression verification

**Examples:**
- `SpiralSoundholeDesigner.vue` (canonical spiral implementation)
- `soundhole_facade.py` (production soundhole API)
- `aperture_geometry.py` (normalized geometry output)

---

### 2. Workspace Layer

**Characteristics:**
- Experimental
- Comparative
- Research-oriented
- Iterative

**Rules:**
- May evolve rapidly
- May host diagnostic scaffolding
- May host observational workflows
- Must not destabilize canonical systems
- Must not leak experimental state into canonical contracts

**Examples:**
- `ApertureComparisonPanel.vue` (workspace shell)
- `DiagnosticSnapshotCard.vue` (diagnostic display)
- Comparison tab workflows

---

### 3. Shared Layer

**Characteristics:**
- Contract-oriented
- Minimal
- Stable
- Cross-workspace

**Rules:**
- Shared contracts require governance review
- Avoid workspace-specific assumptions
- Additive evolution preferred
- Breaking changes require migration path
- Types must be serialization-stable

**Examples:**
- `ApertureGeometry` dataclass
- `AcousticState` type
- `DiagnosticSnapshot` schema
- Workflow primitives (`GateBadge`, `DiagnosticCard`)

---

### 4. Diagnostic Layer

**Characteristics:**
- Observational
- Non-calibrated
- Non-predictive
- Provenance-aware

**Rules:**
- Estimates are explicitly not validated predictions
- All diagnostic output must include provenance reminders
- No diagnostic may claim calibration status
- Residual interpretation is observational only

**Explicit Statement:**
```
Estimates are not validated prediction.
Observational diagnostics do not represent calibrated acoustic performance.
```

---

### 5. Snapshot Layer

**Characteristics:**
- Client-side
- Schema-versioned
- Non-restoring
- Non-persistent

**Rules:**
- All operations occur in-browser
- No backend/API calls during export or import
- Import validation validates schema only
- No state mutation occurs during import

**Explicit Statement:**
```
Import validation validates schema only.
No restore or state mutation occurs.
```

**Reference:** [SNAPSHOT_EXCHANGE_ARCHITECTURE.md](./SNAPSHOT_EXCHANGE_ARCHITECTURE.md)

---

## Canonical Reconciliation Layer

The repository now recognizes ontology reconciliation as a formal architectural concern.

Canonical ontology authority exists to:
- preserve semantic coherence,
- prevent parallel ontology drift,
- stabilize lifecycle terminology,
- preserve authority boundaries,
- and maintain deterministic governance semantics under evolution.

**The reconciliation layer does not own runtime execution.**

**The reconciliation layer owns semantic consistency.**

### Reconciliation Principles

1. **Execution consumes intent; execution does not redefine intent.**
2. **Runtime systems consume ontology; runtime systems do not define ontology.**
3. **AI assistance is advisory only; human authority ratifies canonical ontology.**
4. **No subsystem may independently redefine canonical meaning.**
5. **No sandbox may independently freeze ontology.**

### Reconciliation Infrastructure

| Document | Purpose |
|----------|---------|
| [CANONICAL_ONTOLOGY_VOCABULARY.md](../governance/CANONICAL_ONTOLOGY_VOCABULARY.md) | Vocabulary definitions |
| [CANONICAL_AUTHORITY_MAP.md](../governance/CANONICAL_AUTHORITY_MAP.md) | Ownership declarations |
| [ONTOLOGY_RECONCILIATION_WORKFLOW.md](../governance/ONTOLOGY_RECONCILIATION_WORKFLOW.md) | Ratification process |
| [ONTOLOGY_DRIFT_CLASSIFICATIONS.md](../governance/ONTOLOGY_DRIFT_CLASSIFICATIONS.md) | Drift detection |

### AI Constraints

AI systems may assist with:
- terminology collection
- drift pattern detection
- reconciliation proposal drafting
- documentation generation

AI systems may not:
- ratify canonical definitions
- assign authority ownership
- resolve authority conflicts
- independently freeze ontology

---

## Stable Contract Declaration

The following contracts are declared stable as of Phase-3B closure:

| Contract | Layer | Status | Notes |
|----------|-------|--------|-------|
| `ApertureGeometry` | Shared | **Stable** | Normalized aperture output model |
| `AcousticState` | Shared | **Stable** | Measurement/estimate container |
| `MeasuredResponse` | Shared | **Stable** | Observed frequency response |
| `CalibrationResidual` | Diagnostic | **Stable** | Estimate vs measurement delta |
| `ResidualInterpretation` | Diagnostic | **Stable** | Human-readable residual meaning |
| `ResidualTrend` | Diagnostic | **Stable** | Multi-session trend classification |
| `ResidualStability` | Diagnostic | **Stable** | Stability classification |
| `ResidualCoherence` | Diagnostic | **Stable** | Cross-metric coherence summary |
| `DiagnosticNarrative` | Diagnostic | **Stable** | Human-readable diagnostic summary |
| `DiagnosticSnapshot` | Snapshot | **Stable** | Schema-versioned snapshot container |
| `DiagnosticSnapshotExportMetadata` | Snapshot | **Stable** | Export package metadata |
| `DiagnosticSnapshotImportValidation` | Snapshot | **Stable** | Import validation result |

### Future Extension Contracts

| Contract | Layer | Status | Notes |
|----------|-------|--------|-------|
| `CalibrationSession` | — | **Future** | Not implemented |
| `PredictedResponse` | — | **Future** | Not implemented |
| `RecommendationSet` | — | **Future** | Not implemented |
| `MeasurementArchive` | — | **Future** | Not implemented |

---

## Boundary Enforcement

### Layer Isolation

```
Canonical ← Shared → Workspace
              ↓
          Diagnostic
              ↓
           Snapshot
```

- Canonical layer may consume Shared contracts
- Workspace layer may consume Shared contracts and Diagnostic layer
- Diagnostic layer may consume Shared contracts
- Snapshot layer may consume Diagnostic and Shared contracts
- No layer may depend on Workspace-specific state

### Import Direction

```
canonical/ ← imports ← shared/
workspace/ ← imports ← shared/, diagnostic/
diagnostic/ ← imports ← shared/
snapshot/ ← imports ← shared/, diagnostic/
```

Reverse imports are prohibited.

---

## Governance Requirements

### Contract Changes

| Change Type | Requirement |
|-------------|-------------|
| Additive field | Allowed with default value |
| Breaking change | Migration path required |
| New contract | Governance review |
| Contract removal | Deprecation period + migration |

### Layer Promotion

Moving code from Workspace to Canonical requires:
1. Stability verification
2. Test coverage
3. Governance review
4. Parity verification (if replacing existing implementation)

---

## References

- [SNAPSHOT_EXCHANGE_ARCHITECTURE.md](./SNAPSHOT_EXCHANGE_ARCHITECTURE.md)
- [APERTURE_WORKSPACE_REFACTOR_STATUS.md](./APERTURE_WORKSPACE_REFACTOR_STATUS.md)
- [FEATURE_PARITY_MIGRATION_POLICY.md](../../FEATURE_PARITY_MIGRATION_POLICY.md)
