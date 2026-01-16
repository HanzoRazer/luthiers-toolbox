# Audio Analyzer Renderer Handoff

> **Status:** Package ready for integration
> **Package Location:** `files (9)/chat_a_spectrum_renderer.zip`
> **Cross-Repo:** Consumes `viewer_pack_v1` from [tap_tone_pi](https://github.com/HanzoRazer/tap_tone_pi)

---

## 1. Current State

The Audio Analyzer Viewer (`packages/client/src/views/tools/AudioAnalyzerViewer.vue`) can load `viewer_pack_v1.zip` files exported from tap_tone_pi. It uses a renderer dispatch system:

```
ZIP dropped → manifest.json parsed → files[].kind → pickRenderer(kind) → Component
```

### Renderer Coverage (Before Package)

| Kind | Renderer | Display |
|------|----------|---------|
| `audio_raw` | AudioRenderer | Waveform + playback |
| `spectrum_csv` | CsvRenderer | **Raw table** |
| `analysis_peaks` | JsonRenderer | JSON tree |
| `coherence` | JsonRenderer | JSON tree |
| `transfer_function` | JsonRenderer | JSON tree |
| `wolf_candidates` | JsonRenderer | JSON tree |
| `wsi_curve` | CsvRenderer | Table |
| `provenance` | JsonRenderer | JSON tree |
| `plot_png` | ImageRenderer | Image |
| `session_meta` | JsonRenderer | JSON tree |

**Gap:** `spectrum_csv` renders as a raw table instead of an interactive chart.

---

## 2. Package Contents (`files (9)/`)

```
files (9)/
├── chat_a_summary.md              # Install instructions
├── SpectrumChartRenderer.vue      # New component (standalone copy)
└── chat_a_spectrum_renderer.zip   # Complete patch
    ├── SpectrumChartRenderer.vue  # Chart.js spectrum visualization
    ├── types.ts                   # Adds "spectrum_chart" category
    ├── pickRenderer.ts            # Registers new renderer
    ├── index.ts                   # Exports new renderer
    └── AudioAnalyzerViewer.vue    # CSS badge for new category
```

### Installation

```bash
cd luthiers-toolbox
unzip "files (9)/chat_a_spectrum_renderer.zip" -d /tmp/chat_a

# Apply files
cp /tmp/chat_a/SpectrumChartRenderer.vue packages/client/src/tools/audio_analyzer/renderers/
cp /tmp/chat_a/types.ts packages/client/src/tools/audio_analyzer/renderers/
cp /tmp/chat_a/pickRenderer.ts packages/client/src/tools/audio_analyzer/renderers/
cp /tmp/chat_a/index.ts packages/client/src/tools/audio_analyzer/renderers/
cp /tmp/chat_a/AudioAnalyzerViewer.vue packages/client/src/views/tools/

# Verify
npm run build --workspace=packages/client
```

### What Changes

| Kind | Before | After |
|------|--------|-------|
| `spectrum_csv` | CsvRenderer (table) | SpectrumChartRenderer (chart) |
| `coherence_csv` | CsvRenderer (table) | SpectrumChartRenderer (chart) |

---

## 3. Followup Work (Not in Package)

Three improvements identified from architectural review:

### 3.1 Pack Sanity Panel

**Purpose:** Debug visibility when viewer packs don't render as expected.

**Location:** `packages/client/src/views/tools/AudioAnalyzerViewer.vue`

**Add a collapsible section showing:**
```vue
<details class="pack-debug">
  <summary>Pack Debug Info</summary>
  <div class="debug-content">
    <p><strong>Schema:</strong> {{ manifest?.schema_id }} {{ manifest?.schema_version }}</p>
    <p><strong>Points:</strong> {{ manifest?.points?.join(', ') }}</p>
    <p><strong>Kinds Present:</strong> {{ uniqueKinds.join(', ') }}</p>
    <table>
      <tr v-for="file in manifest?.files" :key="file.relpath">
        <td>{{ file.kind }}</td>
        <td>{{ file.relpath }}</td>
        <td>{{ file.bytes }} bytes</td>
      </tr>
    </table>
  </div>
</details>
```

**Computed:**
```ts
const uniqueKinds = computed(() => {
  if (!manifest.value?.files) return [];
  return [...new Set(manifest.value.files.map(f => f.kind))].sort();
});
```

**Effort:** ~30 minutes

---

### 3.2 CSV Decimation Guard

**Purpose:** Prevent Chart.js from choking on large datasets.

**Location:** `packages/client/src/tools/audio_analyzer/renderers/SpectrumChartRenderer.vue`

**Add to `parsedData` computed (after line 119):**

```ts
// Decimate if too large for smooth rendering
const MAX_CHART_POINTS = 2000;
if (rows.length > MAX_CHART_POINTS) {
  const step = Math.ceil(rows.length / MAX_CHART_POINTS);
  return rows.filter((_, i) => i % step === 0);
}
return rows;
```

**Also add UI indicator:**
```vue
<span v-if="isDecimated" class="decimation-warning">
  Showing {{ dataPoints }} of {{ originalCount }} points
</span>
```

**Effort:** ~20 minutes

---

### 3.3 Kind Contract Documentation

**Create:** `packages/client/src/tools/audio_analyzer/renderers/RENDERER_KINDS.md`

See Section 5 below for full content.

---

## 4. Cross-Repo Contract

### Producer: tap_tone_pi

**Schema:** `contracts/viewer_pack_v1.schema.json`

**Emitter:** `modes/_shared/emit_manifest.py`

**Output:** ZIP files containing `manifest.json` + evidence files

### Consumer: luthiers-toolbox

**Schema Copy:** `contracts/viewer_pack_v1.schema.json` (should be synced)

**Loader:** `packages/client/src/tools/audio_analyzer/packLoader.ts`

**Dispatcher:** `packages/client/src/tools/audio_analyzer/renderers/pickRenderer.ts`

### Sync Check

```bash
# Compare schemas between repos
diff \
  ../tap_tone_pi/contracts/viewer_pack_v1.schema.json \
  contracts/viewer_pack_v1.schema.json
```

If schemas diverge, tap_tone_pi is authoritative.

---

## 5. RENDERER_KINDS.md (Create This File)

```markdown
# Renderer Kind Mapping

> Auto-generated reference for viewer_pack_v1 kind → renderer mapping

## Contract Source

- **Schema:** `tap_tone_pi/contracts/viewer_pack_v1.schema.json`
- **Dispatcher:** `packages/client/src/tools/audio_analyzer/renderers/pickRenderer.ts`

## Kind → Renderer Map

| Kind | Category | Renderer | Notes |
|------|----------|----------|-------|
| `audio_raw` | audio | AudioRenderer | Waveform + HTML5 audio |
| `spectrum_csv` | spectrum_chart | SpectrumChartRenderer | Freq vs magnitude chart |
| `coherence_csv` | spectrum_chart | SpectrumChartRenderer | Same renderer, dual-axis |
| `analysis_peaks` | json | JsonRenderer | Peak detection results |
| `coherence` | json | JsonRenderer | Coherence metadata |
| `transfer_function` | json | JsonRenderer | H(f) data |
| `wolf_candidates` | json | JsonRenderer | Wolf note analysis |
| `wsi_curve` | csv | CsvRenderer | Wood stiffness index |
| `provenance` | json | JsonRenderer | Data lineage |
| `plot_png` | image | ImageRenderer | Pre-rendered plots |
| `session_meta` | json | JsonRenderer | Session metadata |
| `manifest` | json | JsonRenderer | Pack manifest |
| `unknown` | unknown | UnknownRenderer | Fallback |

## CSV Column Contracts

### spectrum_csv

| Column | Required | Aliases |
|--------|----------|---------|
| `freq_hz` | Yes | `freq` |
| `H_mag` | Yes | `mag` |
| `coherence` | No | `coh` |
| `phase_deg` | No | `phase` |

### wsi_curve

| Column | Required | Notes |
|--------|----------|-------|
| TBD | - | Document when implementing WSI renderer |

## Adding a New Kind

1. **tap_tone_pi:** Add kind to `contracts/viewer_pack_v1.schema.json` enum
2. **tap_tone_pi:** Update emitter in `modes/_shared/emit_manifest.py`
3. **luthiers-toolbox:** Sync schema to `contracts/`
4. **luthiers-toolbox:** Add kind → category in `renderers/types.ts`
5. **luthiers-toolbox:** Create renderer component if new category
6. **luthiers-toolbox:** Register in `renderers/pickRenderer.ts`
7. **luthiers-toolbox:** Export from `renderers/index.ts`
8. **Update this document**

## Scripts Reference

### tap_tone_pi

```bash
# Generate viewer pack from capture
python -m modes.phase2 export-viewer-pack --capdir out/session_XYZ

# Validate manifest
python -m tools.validate_manifest out/session_XYZ/viewer_pack.zip
```

### luthiers-toolbox

```bash
# Build client with new renderers
npm run build --workspace=packages/client

# Type check
npm run type-check --workspace=packages/client
```
```

---

## 6. Test Plan

### After Package Installation

1. Build: `npm run build --workspace=packages/client`
2. Start dev server
3. Navigate to Audio Analyzer Viewer
4. Drop a `viewer_pack_v1.zip` from tap_tone_pi
5. Click any `spectrum_csv` file
6. **Expected:** Interactive chart (not table)

### Test Data Location

```bash
# tap_tone_pi has example outputs
ls ../tap_tone_pi/out/
ls ../tap_tone_pi/fixtures/
```

---

## 7. Future Renderers (Prioritized)

| Priority | Kind | Current | Target | Effort |
|----------|------|---------|--------|--------|
| P1 | `spectrum_csv` | Table | Chart | **Done (package)** |
| P2 | `transfer_function` | JSON | Bode plot | Medium |
| P3 | `analysis_peaks` | JSON | Peak overlay on spectrum | Medium |
| P4 | `wsi_curve` | Table | Line chart | Low |
| P5 | `wolf_candidates` | JSON | Highlighted freq bands | Medium |

---

## 8. Session Context

**Created:** 2026-01-15
**Source Chat:** Exported as `files (9)/`
**Reviewed Against:** Architectural critique recommending contract-first approach
**Decision:** Ship specialized renderers, extract primitives if pattern emerges after 3+ similar components
