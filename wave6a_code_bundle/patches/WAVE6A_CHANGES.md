# Wave 6A - Integration Notes (apply as edits)

These edits are written to be *mechanical* to apply against your current HEAD.

---

## 1) `packages/client/src/tools/audio_analyzer/AudioAnalyzerViewer.vue`

### a) Import selection utilities

Add near the top of `script setup`:

```ts
import { makeEmptySelection, setFreq, setPoint, type EvidenceSelection } from "./selection";
```

### b) Add viewer-owned selection state

Add in `setup` state declarations:

```ts
const selection = ref<EvidenceSelection>(makeEmptySelection());

function clearFreqCursor(): void {
  selection.value = setFreq(selection.value, null, null);
}
```

### c) Point selection hook (file tree)

Wherever you handle file-tree / active file changes, set point context **only when it is explicitly point-scoped**.

If you already track `activeRelpath`, you can derive point id like:

```ts
function pointIdFromRelpath(relpath: string): string | null {
  // spectra/points/A1/spectrum.csv
  const m = relpath.match(/\/(?:points)\/([^/]+)\//);
  return m?.[1] ?? null;
}
```

When user clicks a point in the tree:

```ts
selection.value = setPoint(selection.value, pointId);
```

**Do not clear `freqHz` here** (per your approved persistence rules).

### d) Receive peak selection from SpectrumChartRenderer

When rendering the active renderer, pass `selection` and handle emitted event:

```vue
<component
  :is="currentRenderer"
  :entry="activeEntry"
  :bytes="activeBytes"
  :peaksBytes="activePeaksBytes"
  :selection="selection"
  @select="(sel) => { selection = sel }"
/>
```

**Recommended event payload:** the renderer emits a complete `EvidenceSelection` object.

### e) Provide UI to clear cursor

Add a small pill/button in the viewer header:

```vue
<button v-if="selection.freqHz != null" @click="clearFreqCursor()">
  Clear cursor ({{ selection.freqHz.toFixed(2) }} Hz)
</button>
```

---

## 2) `packages/client/src/tools/audio_analyzer/renderers/SpectrumChartRenderer.vue`

### a) Add selection prop

The renderer should accept `selection?: EvidenceSelection | null` via `RendererProps` (already updated in this bundle).

### b) Emit selection on peak click

Add in script:

```ts
const emit = defineEmits<{
  (e: "select", sel: EvidenceSelection): void;
}>();
```

When a peak is clicked:

```ts
emit("select", {
  pointId: inferredPointIdFromEntryRelpath(props.entry.relpath),
  freqHz: peak.freq_hz,
  source: "spectrum",
});
```

### c) Hit testing (recommended)

If your current peaks are drawn only via plugin, add an *invisible peaks dataset* to make click selection stable:

- dataset label: `__peaks__`
- `showLine: false`
- points at `(freq_hz, H_mag)`
- `pointRadius` > 0, but fully transparent

Then in `options.onClick`, check if the active element belongs to `__peaks__`.

### d) Draw cursor line

Add a Chart.js plugin that draws a vertical line at `selection.freqHz`.

Important: the line is drawn at **exact** `freqHz` (no snapping). Any numeric readout may use nearest sample but must label it as such.

---

## 3) `packages/client/src/tools/audio_analyzer/renderers/types.ts`

Already included in this bundle:
- adds `selection?: EvidenceSelection | null` to `RendererProps`

---

## 4) Added file: `packages/client/src/tools/audio_analyzer/selection.ts`

Already included in this bundle.

