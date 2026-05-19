# C1 Inventory: Acoustics/Observational Workstream

**Phase:** C1 — Collection  
**Date:** 2026-05-18  
**Status:** Inventory (no decisions made)  
**Scope:** Acoustics, measurement archives, observational semantics, RMOS pipeline

---

## Purpose

This document inventories acoustics and observational semantic terms. These systems are characterized by strong observational discipline — they preserve what was measured without claiming prediction accuracy.

**Key pattern observed:** The acoustics domain demonstrates "disciplined consumer semantics" — it carefully distinguishes between estimated values and measured values, and maintains explicit provenance for both.

---

## 1. Measurement Archive Vocabulary (Frontend)

**Source:** `packages/client/src/types/acoustics/measurementArchive.ts`  
**Role:** Observational measurement preservation  
**Authority:** Archives preserve observations, not conclusions

### 1.1 MeasurementSource Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `tap_tone` | `measurementArchive.ts:37` | Acoustics | source | Tap tone measurement device |
| `impedance_tube` | `measurementArchive.ts:38` | Acoustics | source | Lab equipment |
| `near_field_mic` | `measurementArchive.ts:39` | Acoustics | source | Close microphone |
| `manual_entry` | `measurementArchive.ts:40` | Acoustics | source | Human-entered value |
| `external_import` | `measurementArchive.ts:41` | Acoustics | source | Imported from file |
| `unknown` | `measurementArchive.ts:42` | Acoustics | source | Fallback |

### 1.2 MeasurementMethod Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `fft_peak_detection` | `measurementArchive.ts:48` | Acoustics | method | FFT-based analysis |
| `swept_sine` | `measurementArchive.ts:49` | Acoustics | method | Swept sine measurement |
| `impulse_response` | `measurementArchive.ts:50` | Acoustics | method | Impulse response capture |
| `manual_reading` | `measurementArchive.ts:51` | Acoustics | method | Human observation |
| `unknown` | `measurementArchive.ts:52` | Acoustics | method | Fallback |

### 1.3 Archive Metadata Literals

| Field | Value | Source | Notes |
|-------|-------|--------|-------|
| `schemaVersion` | `measurement-archive.v1` | `measurementArchive.ts:132` | Schema version pin |
| `kind` | `aperture-measurement-archive` | `measurementArchive.ts:135` | Archive type |
| `generatedBy` | `aperture-workspace` | `measurementArchive.ts:138` | Generator system |
| `observationalOnly` | `true` | `measurementArchive.ts:143` | Hard invariant |

---

## 2. Acoustic State Vocabulary (Frontend)

**Source:** `packages/client/src/types/acoustics.ts`  
**Role:** Descriptive acoustic state model  
**Authority:** Represents known/estimated values without claiming prediction accuracy

### 2.1 AcousticConfidence Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `unknown` | `acoustics.ts:16` | Acoustics | confidence | Confidence not determined |
| `low` | `acoustics.ts:16` | Acoustics | confidence | Geometry-derived estimates |
| `medium` | `acoustics.ts:16` | Acoustics | confidence | Partial validation |
| `high` | `acoustics.ts:16` | Acoustics | confidence | Well-calibrated |

### 2.2 AcousticStateSource Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `geometry_estimate` | `acoustics.ts:22` | Acoustics | source | Derived from geometry |
| `measured` | `acoustics.ts:23` | Acoustics | source | Direct measurement |
| `calibrated` | `acoustics.ts:24` | Acoustics | source | Calibration-adjusted |
| `manual` | `acoustics.ts:25` | Acoustics | source | Manual entry |
| `unknown` | `acoustics.ts:26` | Acoustics | source | Fallback |

### 2.3 AcousticState Key Invariants

| Invariant | Enforcement | Notes |
|-----------|-------------|-------|
| Confidence is mandatory | Schema structure | Prevents overconfidence |
| Assumptions are mandatory | Schema structure | Prevents false certainty |
| Geometry remains separate | Architecture pattern | Not merged into acoustic state |

---

## 3. Measured Response Vocabulary (Frontend)

**Source:** `packages/client/src/types/measurements.ts`  
**Role:** Observed/measured acoustic response (distinct from estimates)

### 3.1 MeasurementSource (measurements.ts variant)

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `manual` | `measurements.ts:12` | Acoustics | Human-entered |
| `tap_tone_pi` | `measurements.ts:13` | Acoustics | tap_tone_pi device |
| `imported_file` | `measurements.ts:14` | Acoustics | File import |
| `unknown` | `measurements.ts:15` | Acoustics | Fallback |

**Collision candidate:** Different MeasurementSource enums in `measurementArchive.ts` vs `measurements.ts`

### 3.2 MeasurementMethod (measurements.ts variant)

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `tap_test` | `measurements.ts:21` | Acoustics | Physical tap test |
| `sine_sweep` | `measurements.ts:22` | Acoustics | Swept sine |
| `impulse_response` | `measurements.ts:23` | Acoustics | Impulse capture |
| `manual_observation` | `measurements.ts:24` | Acoustics | Human reading |
| `unknown` | `measurements.ts:25` | Acoustics | Fallback |

**Collision candidate:** Different MeasurementMethod enums vs `measurementArchive.ts`

### 3.3 Attachment Target

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `reference` | `measurements.ts:65` | Acoustics | Reference aperture |
| `candidate` | `measurements.ts:65` | Acoustics | Candidate aperture |
| `comparison` | `measurements.ts:65` | Acoustics | Comparison context |
| `unknown` | `measurements.ts:65` | Acoustics | Fallback |

---

## 4. Calibration Residuals Vocabulary (Frontend)

**Source:** `packages/client/src/types/calibrationResiduals.ts`  
**Role:** Gap display between estimated and measured values  
**Authority:** Does NOT calibrate, fit, correct, or predict

### 4.1 Estimate Provenance Fields

| Field | Type | Purpose |
|-------|------|---------|
| `estimateMethod` | string | Method used for estimate |
| `estimateSource` | string | Source of estimate |
| `estimateConfidence` | string | Confidence level |
| `estimateAssumptions` | string[] | Assumptions applied |
| `estimateWarnings` | string[] | Warnings about estimate |

---

## 5. TapTone Bundle Manifest (Backend)

**Source:** `services/api/app/rmos/acoustics/schemas_manifest_v1.py`  
**Role:** Canonical import contract from tap_tone_pi  
**Authority:** RMOS ingests from THIS contract, not folder semantics

### 5.1 ManifestVersion Vocabulary

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `TapToneBundleManifestV1` | `schemas_manifest_v1.py:9` | Acoustics | Schema version literal |

### 5.2 Mode/Units Literals

| Field | Value | Source | Notes |
|-------|-------|--------|-------|
| `mode` | `acoustics` | `schemas_manifest_v1.py:97` | Bundle mode |
| `units` | `mm` | `schemas_manifest_v1.py:100` | Unit declaration |

### 5.3 ManifestFile Kind Values (Implicit)

| Term | Usage | Notes |
|------|-------|-------|
| `audio_raw` | Raw audio file | From tap capture |
| `analysis_summary` | Summary file | Analysis output |
| `plot` | Plot image | Visualization |
| `grid` | Grid data | Roving grid pattern |
| `point_audio_raw` | Per-point audio | Multi-point capture |

---

## 6. RMOS Pipeline Vocabulary (Backend)

**Source:** `services/api/app/rmos/`  
**Role:** Manufacturing operation state machine

### 6.1 RiskStatus Vocabulary

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `GREEN` | `engines/base.py:14` | RMOS | No risk |
| `YELLOW` | `engines/base.py:14` | RMOS | Warning level |
| `RED` | `engines/base.py:14` | RMOS | High risk |
| `ERROR` | `engines/base.py:14` | RMOS | Error state |

**Collision candidate:** Similar to CAM `green/yellow/red` gate vocabulary

### 6.2 CutType Vocabulary

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `saw` | `context.py:17` | RMOS | Saw cut |
| `route` | `context.py:18` | RMOS | Router operation |
| `drill` | `context.py:19` | RMOS | Drill operation |
| `mill` | `context.py:20` | RMOS | Mill operation |
| `sand` | `context.py:21` | RMOS | Sanding operation |

### 6.3 WoodSpecies Vocabulary (RMOS)

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `maple` | `context.py:26` | RMOS | Hard maple |
| `mahogany` | `context.py:27` | RMOS | Mahogany |
| `rosewood` | `context.py:28` | RMOS | Rosewood |
| `ebony` | `context.py:29` | RMOS | Ebony |
| `spruce` | `context.py:30` | RMOS | Spruce |
| `cedar` | `context.py:31` | RMOS | Cedar |
| `walnut` | `context.py:32` | RMOS | Walnut |
| `ash` | `context.py:33` | RMOS | Ash |
| `alder` | `context.py:34` | RMOS | Alder |
| `koa` | `context.py:35` | RMOS | Koa |
| `basswood` | `context.py:36` | RMOS | Basswood |
| `unknown` | `context.py:37` | RMOS | Fallback |

**Collision candidate:** Multiple WoodSpecies/MaterialType enums exist across codebase

### 6.4 RmosSeverity Vocabulary

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `info` | `messages.py:18` | RMOS | Informational |
| `warning` | `messages.py:18` | RMOS | Warning level |
| `error` | `messages.py:18` | RMOS | Error level |
| `fatal` | `messages.py:18` | RMOS | Fatal error |

### 6.5 GateMode Vocabulary

| Term | Source File | Domain | Notes |
|------|-------------|--------|-------|
| `block` | `gates/policy.py:15` | RMOS | Hard block |
| `soft_block` | `gates/policy.py:15` | RMOS | Soft block |

---

## 7. Observational Discipline Patterns

### 7.1 Explicit Separation of Estimate vs Measurement

| System | Estimate Type | Measured Type | Separation |
|--------|---------------|---------------|------------|
| Frontend | `AcousticState` | `MeasuredResponse` | Explicit |
| Frontend | `geometry_estimate` source | `measured` source | Enum value |
| Archive | `estimateSource` field | Direct measurement | Provenance |

### 7.2 Mandatory Provenance Fields

| System | Provenance Fields | Purpose |
|--------|-------------------|---------|
| MeasurementArchive | `source`, `method`, `diagnosticSnapshotReference` | Trace measurement origin |
| AcousticState | `source`, `confidence`, `assumptions` | Trace estimate origin |
| TapTone Manifest | `provenance` block, `domain.acoustics` block | Trace capture context |

### 7.3 Hard Invariants (Observational Only)

| System | Invariant | Enforcement |
|--------|-----------|-------------|
| MeasurementArchiveMetadata | `observationalOnly: true` | Schema literal |
| AcousticState | Confidence mandatory | Type structure |
| AcousticState | Assumptions mandatory | Type structure |
| CalibrationResidualPreview | Does NOT calibrate/predict | Documentation |

---

## 8. Semantic Collision Summary (Acoustics)

### 8.1 Duplicate Vocabulary Patterns

| Vocabulary | Location A | Location B | Values Aligned? |
|------------|-----------|-----------|-----------------|
| MeasurementSource | `measurementArchive.ts` | `measurements.ts` | Partial |
| MeasurementMethod | `measurementArchive.ts` | `measurements.ts` | Partial |
| WoodSpecies | `rmos/context.py` | `rosette/pattern_schemas.py` | Different |
| RiskStatus | `rmos/engines/base.py` | CAM gate vocabulary | Similar concept |

### 8.2 Cross-Reference to Other Inventories

| Term | Acoustics Usage | CAM Usage | Collision Type |
|------|-----------------|-----------|----------------|
| `GREEN/YELLOW/RED` | RiskStatus | CamGate | Same concept, different domain |
| `unknown` | Fallback values | Fallback values | Standard pattern |
| WoodSpecies/MaterialType | RMOS context | CAM/rosette | Namespace collision |

---

## 9. Authority Flow Analysis

### 9.1 Acoustics Authority Boundaries

| System | Owns | Consumes | Does NOT Own |
|--------|------|----------|--------------|
| MeasurementArchive | Measurement records | Geometry summary | Calibration outputs |
| AcousticState | Estimate description | Aperture geometry | Prediction accuracy |
| TapTone Manifest | Import contract | Raw capture data | Analysis conclusions |
| RMOS Pipeline | Risk assessment | Material profiles | Acoustic state |

### 9.2 Key Semantic Discipline

| Pattern | Evidence | Implication |
|---------|----------|-------------|
| Estimate ≠ Measurement | Separate types | Clear epistemic boundary |
| Assumptions mandatory | Schema enforcement | No hidden assumptions |
| Confidence explicit | Enum field | No false certainty |
| Provenance preserved | Multiple fields | Full traceability |

---

## 10. Constitutional Observations

### 10.1 Disciplined Semantic Patterns Worth Preserving

| Pattern | Location | Why It's Good |
|---------|----------|---------------|
| Observational-only invariant | Archives | Prevents scope creep |
| Mandatory assumptions | AcousticState | Explicit epistemic state |
| Separate estimate/measured types | Frontend | Clear semantic boundary |
| Schema version pins | Manifests | Forward compatibility |

### 10.2 Minor Consolidation Candidates

| Issue | Files | Priority |
|-------|-------|----------|
| MeasurementSource/Method duplication | Two frontend files | LOW |
| WoodSpecies proliferation | Multiple locations | MEDIUM |
| RiskStatus ↔ CamGate alignment | RMOS ↔ CAM | MEDIUM |

---

## 11. Related Documents

- `docs/governance/coordination/C1_RUNTIME_CAM_INVENTORY.md`
- `docs/governance/coordination/C1_GEOMETRY_TOPOLOGY_INVENTORY.md`
- `docs/governance/coordination/SEMANTIC_COLLISION_LOG.md`
- `docs/architecture/MEASUREMENT_ARCHIVE_ARCHITECTURE.md`

---

## C1 Status

**Collected:** Yes  
**Vocabularies Inventoried:** 15 type definitions  
**Terms Inventoried:** 65+ terms  
**Observational Discipline:** Strong — explicit estimate/measurement separation  
**Decisions Made:** None  
**Next Phase:** C2 reconciliation (not this document)
