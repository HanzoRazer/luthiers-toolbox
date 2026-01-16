# tap-tone-pi ↔ luthiers-toolbox Integration Handoff

**Version:** 1.0.0
**Date:** 2026-01-16
**Status:** Production Ready

---

## Executive Summary

This document provides complete scaffolding for developers connecting **tap-tone-pi** (acoustic measurement system) to **luthiers-toolbox** (CNC/design workbench). The integration uses **viewer_pack_v1** as the canonical interchange format.

**Data Flow:**
```
tap-tone-pi                          luthiers-toolbox
┌─────────────────┐                  ┌─────────────────┐
│ Phase 2 Session │                  │ AudioAnalyzer   │
│ (audio capture) │                  │ Viewer          │
└────────┬────────┘                  └────────▲────────┘
         │                                    │
         ▼                                    │
┌─────────────────┐    viewer_pack_v1.zip    │
│ Export Script   │ ──────────────────────►  │
│ (SHA256 hashes) │                          │
└─────────────────┘                          │
                                    ┌────────┴────────┐
                                    │ Evidence Loader │
                                    │ (validate+norm) │
                                    └─────────────────┘
```

---

## Table of Contents

1. [Contract: viewer_pack_v1 Schema](#1-contract-viewer_pack_v1-schema)
2. [Producer: tap-tone-pi Export](#2-producer-tap-tone-pi-export)
3. [Consumer: luthiers-toolbox Ingestion](#3-consumer-luthiers-toolbox-ingestion)
4. [File Kinds Reference](#4-file-kinds-reference)
5. [Data Format Specifications](#5-data-format-specifications)
6. [Renderer Architecture](#6-renderer-architecture)
7. [Integrity & Validation](#7-integrity--validation)
8. [Implementation Checklist](#8-implementation-checklist)
9. [Testing & CI Gates](#9-testing--ci-gates)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Contract: viewer_pack_v1 Schema

### Schema Location (Source of Truth)

| Repository | Path | Role |
|------------|------|------|
| tap-tone-pi | `contracts/viewer_pack_v1.schema.json` | **Producer (canonical)** |
| luthiers-toolbox | `contracts/viewer_pack_v1.schema.json` | Consumer (vendored copy) |

### Required Manifest Fields

```json
{
  "schema_version": "v1",
  "schema_id": "viewer_pack_v1",
  "created_at_utc": "2026-01-16T07:33:00Z",
  "source_capdir": "session_20260116T073300Z",
  "detected_phase": "phase2",
  "measurement_only": true,
  "interpretation": "deferred",
  "points": ["A1", "A2", "A3", "B1", "B2"],
  "contents": {
    "audio": true,
    "spectra": true,
    "coherence": true,
    "ods": true,
    "wolf": true,
    "plots": true,
    "provenance": true
  },
  "files": [
    {
      "relpath": "spectra/points/A1/spectrum.csv",
      "sha256": "abc123...64chars",
      "bytes": 12345,
      "mime": "text/csv",
      "kind": "spectrum_csv"
    }
  ],
  "bundle_sha256": "def456...64chars"
}
```

### Hard Assertions

| Field | Value | Meaning |
|-------|-------|---------|
| `measurement_only` | `true` | No design advice or tone scoring |
| `interpretation` | `"deferred"` | Interpretation happens in consumer |

---

## 2. Producer: tap-tone-pi Export

### Export Command

```bash
python scripts/export/viewer_pack_v1_export.py \
    --session runs_phase2/session_20260116T073300Z \
    --out out/viewer_packs/session_20260116T073300Z.zip \
    [--keep-unzipped]
```

### Export Pipeline (4 Layers)

```
Layer A: Discovery
├── Detect session phase (phase1, phase2, unknown)
├── Enumerate point IDs from session/points/point_*
└── Validate session structure

Layer B: Copy & Structure
├── Map session artifacts to viewer pack hierarchy
├── Flatten nested directories
└── Apply canonical naming

Layer C: Hashing & Manifest
├── Compute SHA-256 for each file
├── Build canonical file entry list (sorted by relpath)
├── Compute deterministic bundle_sha256
└── Generate manifest.json

Layer D: Packaging
├── Create ZIP archive
└── Optionally keep unzipped directory
```

### Directory Mapping (Phase 2 → viewer_pack_v1)

| Source (session/) | Destination (pack/) | Kind |
|-------------------|---------------------|------|
| `grid.json` | `meta/grid.json` | `session_meta` |
| `metadata.json` | `meta/metadata.json` | `session_meta` |
| `points/point_A1/audio.wav` | `audio/points/A1.wav` | `audio_raw` |
| `points/point_A1/spectrum.csv` | `spectra/points/A1/spectrum.csv` | `spectrum_csv` |
| `points/point_A1/analysis.json` | `spectra/points/A1/analysis.json` | `analysis_peaks` |
| `points/point_A1/capture_meta.json` | `provenance/points/A1/capture_meta.json` | `provenance` |
| `derived/ods_snapshot.json` | `ods/ods_snapshot.json` | `transfer_function` |
| `derived/wolf_candidates.json` | `wolf/wolf_candidates.json` | `wolf_candidates` |
| `derived/wsi_curve.csv` | `wolf/wsi_curve.csv` | `wsi_curve` |
| `plots/*.png` | `plots/*.png` | `plot_png` |

### Example Pack Structure

```
viewer_pack.zip
├── manifest.json
├── README.txt
├── meta/
│   ├── grid.json
│   └── metadata.json
├── audio/points/
│   ├── A1.wav
│   ├── A2.wav
│   └── ...
├── spectra/points/
│   ├── A1/
│   │   ├── spectrum.csv
│   │   └── analysis.json
│   └── ...
├── provenance/points/
│   ├── A1/capture_meta.json
│   └── ...
├── ods/
│   └── ods_snapshot.json
├── wolf/
│   ├── wolf_candidates.json
│   └── wsi_curve.csv
└── plots/
    ├── coherence_187.5Hz.png
    ├── ods_mag_187.5Hz.png
    └── wsi_curve.png
```

---

## 3. Consumer: luthiers-toolbox Ingestion

### Core Module

**Location:** `packages/client/src/evidence/`

| File | Purpose |
|------|---------|
| `types.ts` | Type definitions for schemas + normalized model |
| `validate.ts` | Schema validators + SHA256 integrity checks |
| `zip_loader.ts` | ZIP unpacking + auto-detection + normalization |
| `index.ts` | Public API export |

### Public API

```typescript
import { loadNormalizedPack, type NormalizedPack } from "@/evidence";

// Load and normalize a viewer pack ZIP
const pack: NormalizedPack = await loadNormalizedPack(zipFile);

// Access normalized data
console.log(pack.schema_id);        // "viewer_pack_v1"
console.log(pack.files.length);     // File count
console.log(pack.measurement_only); // true

// Resolve file bytes by path
const bytes = pack.resolveFile("spectra/points/A1/spectrum.csv");
```

### NormalizedPack Interface

```typescript
interface NormalizedPack {
  schema_id: string;
  created_at_utc: string;
  source_capdir?: string;
  detected_phase?: string;
  measurement_only: boolean;
  interpretation?: string;
  bundle_sha256?: string;
  files: NormalizedFileEntry[];
  resolveFile(relpath: string): Uint8Array | null;
}

interface NormalizedFileEntry {
  relpath: string;
  kind: string;
  mime: string;
  bytes: number;
  sha256?: string;
}
```

### Schema Auto-Detection

```typescript
// Detection priority:
// 1. Check schema_id field → "viewer_pack_v1"
// 2. Check schema_version field → "toolbox_evidence_manifest_v1"
// 3. Return "unknown"

const schema = detectSchema(manifest);
```

---

## 4. File Kinds Reference

### Kind Vocabulary (Canonical)

| Kind | Content | Path Pattern | MIME Type |
|------|---------|--------------|-----------|
| `audio_raw` | 2-channel WAV | `audio/points/*.wav` | `audio/wav` |
| `audio_wav` | WAV file | `*.wav` | `audio/wav` |
| `audio_flac` | FLAC file | `*.flac` | `audio/flac` |
| `spectrum_csv` | Frequency response | `spectra/points/*/spectrum.csv` | `text/csv` |
| `coherence_csv` | Coherence data | `*/coherence.csv` | `text/csv` |
| `analysis_peaks` | FFT summary | `spectra/points/*/analysis.json` | `application/json` |
| `transfer_function` | ODS snapshot | `ods/ods_snapshot.json` | `application/json` |
| `coherence` | Coherence metadata | (in ODS) | `application/json` |
| `wolf_candidates` | Stress indices | `wolf/wolf_candidates.json` | `application/json` |
| `wsi_curve` | WSI vs frequency | `wolf/wsi_curve.csv` | `text/csv` |
| `provenance` | Capture metadata | `provenance/points/*/capture_meta.json` | `application/json` |
| `plot_png` | Visualization | `plots/*.png` | `image/png` |
| `image_png` | PNG image | `*.png` | `image/png` |
| `image_jpg` | JPEG image | `*.jpg` | `image/jpeg` |
| `session_meta` | Grid/session info | `meta/*.json` | `application/json` |
| `notes_md` | Markdown notes | `*.md` | `text/markdown` |
| `manifest` | Package manifest | `manifest.json` | `application/json` |
| `unknown` | Unclassified | (fallback) | `application/octet-stream` |

### Kind → Renderer Category Mapping

| Kind | Category | Renderer Component |
|------|----------|-------------------|
| `audio_raw`, `audio_wav`, `audio_flac` | `audio` | AudioRenderer |
| `spectrum_csv`, `coherence_csv` | `spectrum_chart` | SpectrumChartRenderer |
| `transfer_function` | `bode_plot` | TransferFunctionRenderer |
| `plot_png`, `image_png`, `image_jpg` | `image` | ImageRenderer |
| `peaks_csv`, `waveform_csv`, `wsi_curve` | `csv` | CsvRenderer |
| `analysis_peaks`, `coherence`, `provenance`, `session_meta`, `wolf_candidates` | `json` | JsonRenderer |
| `notes_md` | `markdown` | MarkdownRenderer |
| `unknown` | `unknown` | UnknownRenderer |

---

## 5. Data Format Specifications

### spectrum_csv (Frequency Response)

**Columns (required):**
```csv
freq_hz,H_mag,coherence,phase_deg
10.546875,0.000123,0.95,-10.5
21.09375,0.000456,0.92,-25.3
...
```

| Column | Type | Description |
|--------|------|-------------|
| `freq_hz` | float | Frequency in Hz |
| `H_mag` | float | Transfer function magnitude |
| `coherence` | float | Coherence (γ²), 0-1 |
| `phase_deg` | float | Phase in degrees |

**Sibling Resolution:** For `spectra/points/A1/spectrum.csv`, the peaks overlay fetches `spectra/points/A1/analysis.json`.

### analysis_peaks (FFT Summary)

```json
{
  "peaks": [
    {
      "freq_hz": 187.5,
      "H_mag": 0.0234,
      "label": "Mode 1"
    }
  ],
  "summary": {
    "peak_count": 5,
    "dominant_freq_hz": 187.5
  }
}
```

### transfer_function (ODS Snapshot)

**Format 1: Parallel Arrays**
```json
{
  "frequencies": [100.0, 150.0, 200.0],
  "magnitude": [0.5, 0.7, 0.3],
  "phase": [45.0, -30.0, 90.0]
}
```

**Format 2: Array of Objects**
```json
{
  "data": [
    {"freq": 100.0, "mag": 0.5, "phase": 45.0},
    {"freq": 150.0, "mag": 0.7, "phase": -30.0}
  ]
}
```

**Format 3: ODS Modal**
```json
{
  "schema_version": "phase2_ods_snapshot_v2",
  "analysis_type": "ODS",
  "freqs_hz": [100.0, 150.0, 200.0],
  "points": [
    {
      "point_id": "A1",
      "x_mm": 50.0,
      "y_mm": 100.0,
      "H_mag": [0.5, 0.7, 0.3],
      "H_phase_deg": [45.0, -30.0, 90.0],
      "coherence": [0.95, 0.88, 0.92]
    }
  ]
}
```

**Format 4: Complex FRF**
```json
{
  "frequencies": [100.0, 150.0, 200.0],
  "frf": {
    "real": [0.3, 0.5, 0.2],
    "imag": [0.4, 0.5, 0.2]
  }
}
```

### wsi_curve (Wolf Stress Index)

```csv
freq_hz,wsi,loc,grad,phase_disorder,coh_mean,admissible
35.15625,0.165971,1.091843,0.066627,0.000311,0.984706,True
46.875,0.167153,1.093653,0.067028,0.000284,0.972296,True
```

| Column | Type | Description |
|--------|------|-------------|
| `freq_hz` | float | Frequency in Hz |
| `wsi` | float | Wood Stiffness Index |
| `loc` | float | Localization metric |
| `grad` | float | Gradient |
| `phase_disorder` | float | Phase disorder |
| `coh_mean` | float | Mean coherence |
| `admissible` | bool | True/False filter flag |

### wolf_candidates (Stress Candidates)

```json
{
  "schema_version": "phase2_wolf_candidates_v2",
  "candidates": [
    {
      "freq_hz": 187.5,
      "localization_index": 2.4,
      "energy_gradient": 0.18,
      "phase_disorder": 0.12,
      "wsi": 0.65,
      "top_points": [
        {"point_id": "A1", "H_mag": 0.8},
        {"point_id": "A2", "H_mag": 0.7}
      ]
    }
  ],
  "provenance": {
    "algo_id": "phase2_wsi_wolf",
    "algo_version": "1.0.0",
    "computed_at_utc": "2026-01-16T07:33:00Z"
  }
}
```

---

## 6. Renderer Architecture

### Location

`packages/client/src/tools/audio_analyzer/renderers/`

### Dispatch Flow

```
File selected in AudioAnalyzerViewer
         │
         ▼
┌─────────────────┐
│ pickRenderer()  │  ← entry.kind
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ kindToCategory()│  → "spectrum_chart"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ rendererMap     │  → SpectrumChartRenderer
└────────┬────────┘
         │
         ▼
<component :is="renderer" :entry :bytes :peaks-bytes />
```

### Renderer Props

```typescript
interface RendererProps {
  entry: NormalizedFileEntry;
  bytes: Uint8Array;
  peaksBytes?: Uint8Array | null;  // Sibling peaks data
}
```

### Adding a New Renderer

1. **Create component:** `renderers/MyRenderer.vue`
2. **Add kind mapping:** `types.ts` → `kindToCategory()`
3. **Register renderer:** `pickRenderer.ts` → `rendererMap`
4. **Add tests:** `__tests__/pickRenderer.spec.ts`

---

## 7. Integrity & Validation

### SHA-256 Verification

**Per-File Integrity:**
```typescript
import { verifyFileIntegrity } from "@/evidence/validate";

const result = verifyFileIntegrity(entry, actualBytes);
// { valid: boolean, errors: string[] }
```

**Bundle Hash:**
```typescript
import { verifyBundleHash } from "@/evidence/validate";

const result = await verifyBundleHash(manifest);
// { valid: boolean, expected: string, actual: string }
```

### Bundle Hash Computation

```python
# tap-tone-pi export logic:
import hashlib
import json

def compute_bundle_hash(manifest_dict):
    # 1. Remove bundle_sha256 field
    m = {k: v for k, v in manifest_dict.items() if k != "bundle_sha256"}

    # 2. Canonical JSON (sorted keys, 2-space indent)
    canonical = json.dumps(m, sort_keys=True, indent=2)

    # 3. SHA-256 hex
    return hashlib.sha256(canonical.encode()).hexdigest()
```

### Validation Rules

| Rule | Enforcement |
|------|-------------|
| All file entries have `relpath` and `kind` | Schema validation |
| SHA-256 is 64 lowercase hex chars | Regex validation |
| `measurement_only` must be `true` | Hard assertion |
| No extra fields in schema | Strict validation |
| Vector fields are always arrays | Runtime check |

---

## 8. Implementation Checklist

### Producer (tap-tone-pi)

- [ ] Session capture creates point directories
- [ ] DSP pipeline outputs spectrum.csv + analysis.json
- [ ] Derived artifacts (ODS, wolf, WSI) generated
- [ ] Export script maps to viewer_pack_v1 structure
- [ ] SHA-256 computed for all files
- [ ] Bundle hash computed from canonical JSON
- [ ] manifest.json includes all required fields
- [ ] ZIP created with correct hierarchy

### Consumer (luthiers-toolbox)

- [ ] ZIP drop zone accepts viewer packs
- [ ] Schema auto-detection works
- [ ] Normalization produces unified model
- [ ] File kind dispatch routes to correct renderer
- [ ] Spectrum chart renders CSV with coherence
- [ ] Peaks overlay shows analysis.json data
- [ ] Bode plot supports all JSON formats
- [ ] Integrity verification available
- [ ] Pack debug panel shows diagnostics

---

## 9. Testing & CI Gates

### tap-tone-pi Tests

```bash
# Schema validation
pytest tests/test_viewer_pack_v1_gate.py

# Export golden test
pytest scripts/phase2/test_export_viewer_pack_v1_golden.py
```

### luthiers-toolbox Tests

```bash
# Evidence loader
npm run test -- src/evidence/__tests__/zip_loader.spec.ts

# Renderer dispatch
npm run test -- src/tools/audio_analyzer/renderers/__tests__/pickRenderer.spec.ts

# Kind mapping
npm run test -- src/tools/audio_analyzer/renderers/__tests__/types.spec.ts

# Peaks helper
npm run test -- src/tools/audio_analyzer/__tests__/packHelpers.spec.ts
```

### CI Workflows

| Workflow | Purpose |
|----------|---------|
| `Client Lint & Build` | TypeScript + build verification |
| `API Tests` | Backend validation |
| `Core CI (Consolidated)` | Full test suite |

---

## 10. Troubleshooting

### "Unknown schema" Error

**Cause:** Manifest missing `schema_id` field.

**Fix:** Ensure manifest includes:
```json
"schema_id": "viewer_pack_v1"
```

### "Missing required columns" in Spectrum Chart

**Cause:** CSV missing `freq_hz` or `H_mag` columns.

**Fix:** Ensure CSV header matches:
```csv
freq_hz,H_mag,coherence,phase_deg
```

### Peaks Overlay Not Showing

**Cause:** Missing sibling `analysis.json` file.

**Fix:** For `spectra/points/A1/spectrum.csv`, include `spectra/points/A1/analysis.json` with peaks array.

### Bundle Hash Mismatch

**Cause:** Non-canonical JSON serialization.

**Fix:** Use `json.dumps(m, sort_keys=True, indent=2)` for hash computation.

### Renderer Shows "Unknown"

**Cause:** File `kind` not in vocabulary.

**Fix:** Use exact kind strings from Section 4. Check `types.ts` → `kindToCategory()`.

---

## Quick Reference

### Minimum Viable Pack

```
pack.zip
├── manifest.json
└── spectra/points/A1/spectrum.csv
```

**manifest.json:**
```json
{
  "schema_version": "v1",
  "schema_id": "viewer_pack_v1",
  "created_at_utc": "2026-01-16T00:00:00Z",
  "measurement_only": true,
  "files": [
    {
      "relpath": "spectra/points/A1/spectrum.csv",
      "kind": "spectrum_csv",
      "mime": "text/csv",
      "bytes": 1234,
      "sha256": "..."
    }
  ]
}
```

### Key Files

| Purpose | tap-tone-pi | luthiers-toolbox |
|---------|-------------|------------------|
| Schema | `contracts/viewer_pack_v1.schema.json` | `contracts/viewer_pack_v1.schema.json` |
| Export | `scripts/export/viewer_pack_v1_export.py` | — |
| Loader | — | `packages/client/src/evidence/zip_loader.ts` |
| Renderer | — | `packages/client/src/tools/audio_analyzer/renderers/` |
| Viewer | — | `packages/client/src/views/tools/AudioAnalyzerViewer.vue` |

---

*Document generated as part of tap-tone-pi ↔ luthiers-toolbox integration.*
