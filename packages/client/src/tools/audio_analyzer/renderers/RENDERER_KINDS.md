# Renderer Kind Mapping

> Reference for `viewer_pack_v1` kind → renderer mapping

## Contract Source

- **Producer Schema:** `tap_tone_pi/contracts/viewer_pack_v1.schema.json`
- **Consumer Schema:** `luthiers-toolbox/contracts/viewer_pack_v1.schema.json`
- **Dispatcher:** `pickRenderer.ts` in this directory

## Kind → Renderer Map

| Kind | Category | Renderer | Notes |
|------|----------|----------|-------|
| `audio_raw` | audio | AudioRenderer | Waveform + HTML5 audio playback |
| `spectrum_csv` | spectrum_chart | SpectrumChartRenderer | Freq vs magnitude + coherence |
| `coherence_csv` | spectrum_chart | SpectrumChartRenderer | Same renderer, dual-axis |
| `transfer_function` | bode_plot | TransferFunctionRenderer | **Bode plot: mag(dB) + phase** |
| `analysis_peaks` | json | JsonRenderer | Peak detection results |
| `coherence` | json | JsonRenderer | Coherence metadata |
| `wolf_candidates` | json | JsonRenderer | Wolf note analysis |
| `wsi_curve` | csv | CsvRenderer | Wood stiffness index curve |
| `provenance` | json | JsonRenderer | Data lineage metadata |
| `plot_png` | image | ImageRenderer | Pre-rendered PNG plots |
| `session_meta` | json | JsonRenderer | Session metadata |
| `manifest` | json | JsonRenderer | Pack manifest |
| `unknown` | unknown | UnknownRenderer | Fallback for unrecognized |

## CSV Column Contracts

### spectrum_csv

Parsed by `SpectrumChartRenderer.vue`:

| Column | Required | Accepted Aliases |
|--------|----------|------------------|
| `freq_hz` | Yes | `freq`, any containing "freq" |
| `H_mag` | Yes | `mag`, any containing "mag" |
| `coherence` | No | `coh`, any containing "coh" |
| `phase_deg` | No | `phase`, any containing "phase" |

**Decimation:** If > 2000 points, data is decimated for Chart.js performance.

### wsi_curve

Currently rendered as table. Future chart renderer should handle:

| Column | Required | Notes |
|--------|----------|-------|
| TBD | - | Document when implementing |

### transfer_function (JSON)

Parsed by `TransferFunctionRenderer.vue`. Supports multiple JSON formats:

**Format 1: Parallel Arrays**
```json
{
  "frequencies": [10, 20, 50, 100, 200],
  "magnitude": [0.001, 0.005, 0.02, 0.1, 0.05],
  "phase": [-10, -25, -45, -90, -120]
}
```

**Format 2: Array of Objects**
```json
{
  "data": [
    {"freq": 100, "mag": 0.1, "phase": -45},
    {"freq": 200, "mag": 0.05, "phase": -90}
  ]
}
```

**Format 3: ODS Modal**
```json
{
  "modes": [
    {"freq": 82.4, "amplitude": 1.0, "phase": 0},
    {"freq": 165.0, "amplitude": 0.8, "phase": -30}
  ]
}
```

**Format 4: Complex FRF**
```json
{
  "frequencies": [100, 200, 500],
  "frf": {
    "real": [0.1, 0.05, 0.02],
    "imag": [0.02, 0.04, 0.01]
  }
}
```

**Display Controls:**
- **Phase toggle:** Show/hide phase trace
- **Log Freq:** Logarithmic frequency axis (default: on)
- **dB Scale:** Convert magnitude to decibels (default: on)

## Adding a New Kind

### Step 1: Producer (tap_tone_pi)

```bash
# Edit schema
vim contracts/viewer_pack_v1.schema.json
# Add to: $defs.fileEntry.properties.kind.enum

# Update emitter
vim modes/_shared/emit_manifest.py
# Add kind classification logic
```

### Step 2: Consumer (luthiers-toolbox)

```bash
# Sync schema (if changed)
cp ../tap_tone_pi/contracts/viewer_pack_v1.schema.json contracts/

# Add category mapping
vim packages/client/src/tools/audio_analyzer/renderers/types.ts
# Add case in kindToCategory()

# Create renderer (if new category)
vim packages/client/src/tools/audio_analyzer/renderers/NewRenderer.vue

# Register renderer
vim packages/client/src/tools/audio_analyzer/renderers/pickRenderer.ts
# Import and add to rendererMap

# Export
vim packages/client/src/tools/audio_analyzer/renderers/index.ts
# Add export line

# Update this file
```

### Step 3: Verify

```bash
npm run type-check --workspace=packages/client
npm run build --workspace=packages/client
```

## Scripts Reference

### tap_tone_pi (Producer)

```bash
# Generate viewer pack from a capture session
python -m modes.phase2 export-viewer-pack --capdir out/session_XYZ

# Validate a viewer pack manifest
python -m tools.validate_manifest path/to/viewer_pack.zip

# List kinds in a pack
unzip -p viewer_pack.zip manifest.json | jq '.files[].kind' | sort | uniq -c
```

### luthiers-toolbox (Consumer)

```bash
# Build client
npm run build --workspace=packages/client

# Type check renderers
npm run type-check --workspace=packages/client

# Dev server (for testing)
npm run dev --workspace=packages/client
```

## Debugging

### Check kind mapping at runtime

In browser console while viewing Audio Analyzer:
```js
// Injected by AudioAnalyzerViewer
console.log(window.__DEBUG_PACK_MANIFEST__)
```

### Verify renderer dispatch

```ts
import { kindToCategory } from './types';
import { pickRenderer } from './pickRenderer';

console.log(kindToCategory('spectrum_csv'));  // → 'spectrum_chart'
console.log(pickRenderer('spectrum_csv'));    // → SpectrumChartRenderer
```

## Version History

| Date | Change |
|------|--------|
| 2026-01-16 | Added `bode_plot` category, TransferFunctionRenderer for `transfer_function` kind |
| 2026-01-15 | Added schema parity CLI test to gate |
| 2026-01-15 | Added decimation guard (2000 point limit) to SpectrumChartRenderer |
| 2026-01-15 | Added Pack Debug Panel to AudioAnalyzerViewer |
| 2026-01-15 | Added `spectrum_chart` category, routed `spectrum_csv` and `coherence_csv` |
| 2026-01-03 | Initial renderer system with 6 categories |

---

## Contract Governance

### Schema Locations

| Repo | Path | Role |
|------|------|------|
| tap_tone_pi | `contracts/viewer_pack_v1.schema.json` | **Source of truth** |
| luthiers-toolbox | `contracts/viewer_pack_v1.schema.json` | Vendored copy |

### CI Gates

```bash
# Schema parity check (run by pytest gate)
python scripts/validate/check_viewer_pack_schema_parity.py --mode check

# Fixture validation (run by pytest gate)
python scripts/validate/validate_viewer_pack_v1.py --pack services/api/tests/fixtures/viewer_packs/session_minimal.zip
```

### Test Gate Location

```
services/api/tests/test_viewer_pack_v1_ingestion_gate.py
├── TestViewerPackV1IngestionGate
│   ├── test_validator_cli_exists
│   ├── test_schema_exists
│   ├── test_schema_has_required_structure
│   ├── test_validate_fixture_zips      ← validates all fixtures
│   └── test_validator_rejects_invalid_pack
└── TestViewerPackSchemaParityGate
    ├── test_schema_parity_check_passes  ← calls parity CLI
    ├── test_schema_version_is_v1
    ├── test_schema_id_is_viewer_pack_v1
    ├── test_kind_vocabulary_coverage    ← warns on new kinds
    └── test_toolbox_types_cover_schema_kinds
```

### Updating When tap_tone_pi Schema Changes

1. **Producer** updates `tap_tone_pi/contracts/viewer_pack_v1.schema.json`
2. **Consumer** syncs:
   ```bash
   cp ../tap_tone_pi/contracts/viewer_pack_v1.schema.json contracts/
   python scripts/validate/check_viewer_pack_schema_parity.py --mode print
   # Update PINNED_SCHEMA_HASH in check_viewer_pack_schema_parity.py
   ```
3. **Consumer** updates `renderers/types.ts` if new kinds were added
4. **Consumer** runs gate: `pytest services/api/tests/test_viewer_pack_v1_ingestion_gate.py`
