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
| `analysis_peaks` | json | JsonRenderer | Peak detection results |
| `coherence` | json | JsonRenderer | Coherence metadata |
| `transfer_function` | json | JsonRenderer | H(f) transfer function data |
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
| 2026-01-15 | Added decimation guard (2000 point limit) to SpectrumChartRenderer |
| 2026-01-15 | Added Pack Debug Panel to AudioAnalyzerViewer |
| 2026-01-15 | Added `spectrum_chart` category, routed `spectrum_csv` and `coherence_csv` |
| 2026-01-03 | Initial renderer system with 6 categories |
