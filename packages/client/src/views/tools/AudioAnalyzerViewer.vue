<template>
  <div class="page">
    <header class="header">
      <div class="header-row">
        <h1>🎛️ Audio Analyzer Evidence Viewer</h1>
        <div v-if="cursorFreqHz !== null" class="cursor-pill" :title="`Linked cursor @ ${cursorFreqHz.toFixed(2)} Hz`">
          <span class="cursor-pill-label">Cursor</span>
          <code class="cursor-pill-val">{{ cursorFreqHz.toFixed(2) }} Hz</code>
          <button class="cursor-pill-clear" @click="clearCursorOnly" aria-label="Clear cursor">
            ✕
          </button>
        </div>
      </div>
      <p class="sub">
        Evidence-pack viewer (ZIP). Supports both
        <code>viewer_pack_v1</code> and <code>toolbox_evidence_manifest_v1</code> schemas.
      </p>
    </header>

    <section class="drop" @dragover.prevent @drop.prevent="onDrop">
      <div class="drop-inner">
        <div class="drop-title">Drop an evidence ZIP here</div>
        <div class="drop-sub">or</div>
        <input type="file" accept=".zip" @change="onPick" />
      </div>
    </section>

    <section v-if="err" class="err">
      <strong>Error:</strong> {{ err }}
    </section>

    <section v-if="pack" class="grid">
      <!-- Pack Metadata -->
      <div class="card">
        <h2>Pack Summary</h2>
        <div class="kv">
          <div><span>schema</span><code>{{ pack.schema_id }}</code></div>
          <div><span>created_at_utc</span><code>{{ pack.created_at_utc || "-" }}</code></div>
          <div v-if="pack.source_capdir"><span>source_capdir</span><code>{{ pack.source_capdir }}</code></div>
          <div v-if="pack.detected_phase"><span>detected_phase</span><code>{{ pack.detected_phase }}</code></div>
          <div><span>measurement_only</span><code>{{ pack.measurement_only ? "Yes" : "No" }}</code></div>
          <div v-if="pack.interpretation"><span>interpretation</span><code>{{ pack.interpretation }}</code></div>
          <div><span>files</span><code>{{ pack.files.length }}</code></div>
        </div>
      </div>

      <!-- File List -->
      <div class="card">
        <h2>Files</h2>
        <div class="filter-bar">
          <select v-model="kindFilter" class="filter-select">
            <option value="">All kinds</option>
            <option v-for="k in uniqueKinds" :key="k" :value="k">{{ k }}</option>
          </select>
          <span class="file-count">{{ filteredFiles.length }} file(s)</span>
        </div>
        <table class="tbl">
          <thead>
            <tr>
              <th>kind</th>
              <th>path</th>
              <th>bytes</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="f in filteredFiles"
              :key="f.relpath"
              :class="{ active: activePath === f.relpath }"
            >
              <td><code class="kind-badge" :data-category="getCategory(f.kind)">{{ f.kind }}</code></td>
              <td class="mono path-cell" :title="f.relpath">{{ f.relpath }}</td>
              <td class="mono">{{ formatBytes(f.bytes) }}</td>
              <td>
                <button class="btn" @click="selectFile(f.relpath)">View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Preview Panel -->
      <div class="card wide">
        <h2>Preview</h2>
        <div v-if="activePath && activeEntry" class="preview-container">
          <div class="preview-split">
            <div class="preview-main">
              <component
                :is="currentRenderer"
                :entry="activeEntry"
                :bytes="activeBytes"
                :peaks-bytes="peaksBytes"
                :selected-freq-hz="Number.isFinite(selectedPeak?.freq_hz) ? selectedPeak!.freq_hz : null"
                @peak-selected="onPeakSelected"
              />
            </div>

            <aside class="preview-side">
              <div class="side-header">
                <div class="side-title">Peak Details</div>
                <button class="btn btn-small" :disabled="!selectedPeak" @click="clearSelectedPeak">
                  Clear
                </button>
              </div>

              <div v-if="!selectedPeak" class="side-empty">
                <p class="muted">
                  Click a peak marker in the spectrum chart to inspect it here.
                </p>
              </div>

              <div v-else class="side-body">
                <div class="side-kv">
                  <div><span>point</span><code>{{ selectedPeak.pointId || "—" }}</code></div>
                  <div><span>freq_hz</span><code>{{ selectedPeak.freq_hz.toFixed(2) }}</code></div>
                  <div v-if="selectedPeak.label"><span>label</span><code>{{ selectedPeak.label }}</code></div>
                  <div><span>spectrum</span><code class="mono">{{ selectedPeak.spectrumRelpath }}</code></div>
                  <div><span>analysis</span><code class="mono">{{ selectedPeak.peaksRelpath }}</code></div>
                </div>

                <div class="side-actions">
                  <button class="btn" :disabled="!selectedPeak.pointId" @click="jumpToPointAudio">
                    ▶ Open point audio
                  </button>
                  <div v-if="audioJumpError" class="side-warn">
                    {{ audioJumpError }}
                  </div>
                </div>

                <details class="side-raw" open>
                  <summary class="side-summary">Raw peak JSON</summary>
                  <pre class="side-pre">{{ selectedPeak.rawPretty }}</pre>
                </details>
              </div>
            </aside>
          </div>
        </div>
        <div v-else class="placeholder">
          <p>Select a file from the list above to preview.</p>
        </div>
      </div>

      <!-- Pack Debug Panel -->
      <details class="card wide pack-debug">
        <summary class="debug-summary">🔍 Pack Debug Info</summary>
        <div class="debug-content">
          <div class="debug-grid">
            <div class="debug-section">
              <h3>Schema</h3>
              <div class="debug-kv">
                <span>schema_id</span>
                <code>{{ pack.schema_id }}</code>
              </div>
              <div class="debug-kv">
                <span>bundle_sha256</span>
                <code class="hash">{{ pack.bundle_sha256 || "—" }}</code>
              </div>
            </div>
            <div class="debug-section">
              <h3>Kinds Present ({{ uniqueKinds.length }})</h3>
              <div class="kind-chips">
                <code
                  v-for="k in uniqueKinds"
                  :key="k"
                  class="kind-chip"
                  :data-category="getCategory(k)"
                >
                  {{ k }} ({{ kindCounts[k] }})
                </code>
              </div>
            </div>
          </div>
          <div class="debug-section">
            <h3>All Files ({{ pack.files.length }})</h3>
            <table class="debug-tbl">
              <thead>
                <tr>
                  <th>kind</th>
                  <th>relpath</th>
                  <th>bytes</th>
                  <th>sha256</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="f in pack.files" :key="f.relpath">
                  <td><code class="kind-badge" :data-category="getCategory(f.kind)">{{ f.kind }}</code></td>
                  <td class="mono">{{ f.relpath }}</td>
                  <td class="mono">{{ f.bytes }}</td>
                  <td class="mono hash">{{ f.sha256?.slice(0, 12) || "—" }}…</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </details>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, shallowRef, type Component, watch } from "vue";
import { loadNormalizedPack, type NormalizedPack, type NormalizedFileEntry } from "@/evidence";
import { pickRenderer, getRendererCategory } from "@/tools/audio_analyzer/renderers";
import { findSiblingPeaksRelpath } from "@/tools/audio_analyzer/packHelpers";

const pack = shallowRef<NormalizedPack | null>(null);
const err = ref<string>("");
const activePath = ref<string>("");
const kindFilter = ref<string>("");

type SelectedPeak = {
  pointId: string | null;
  spectrumRelpath: string;
  peaksRelpath: string;
  peakIndex: number;
  freq_hz: number;
  label?: string;
  raw: unknown;
  rawPretty: string;
};
const selectedPeak = ref<SelectedPeak | null>(null);
const audioJumpError = ref<string>("");

// Wave 6A "linked cursor" pill should persist across file changes
const cursorFreqHz = computed<number | null>(() => {
  const f = selectedPeak.value?.freq_hz;
  return Number.isFinite(f) ? f! : null;
});

// Current active file entry
const activeEntry = computed<NormalizedFileEntry | null>(() => {
  if (!pack.value || !activePath.value) return null;
  return pack.value.files.find((f) => f.relpath === activePath.value) ?? null;
});

// Current active file bytes
const activeBytes = computed<Uint8Array>(() => {
  if (!pack.value || !activePath.value) return new Uint8Array(0);
  return pack.value.resolveFile(activePath.value) ?? new Uint8Array(0);
});

// Sibling peaks bytes for spectrum CSV files (analysis.json)
const peaksBytes = computed<Uint8Array | null>(() => {
  if (!pack.value || !activePath.value) return null;
  const siblingPath = findSiblingPeaksRelpath(activePath.value);
  if (!siblingPath) return null;
  return pack.value.resolveFile(siblingPath) ?? null;
});

// Dynamically pick renderer based on file kind
const currentRenderer = computed<Component | null>(() => {
  if (!activeEntry.value) return null;
  return pickRenderer(activeEntry.value.kind);
});

// Unique kinds for filter dropdown
const uniqueKinds = computed<string[]>(() => {
  if (!pack.value) return [];
  const kinds = new Set(pack.value.files.map((f) => f.kind));
  return Array.from(kinds).sort();
});

// Kind counts for debug panel
const kindCounts = computed<Record<string, number>>(() => {
  if (!pack.value) return {};
  const counts: Record<string, number> = {};
  for (const f of pack.value.files) {
    counts[f.kind] = (counts[f.kind] || 0) + 1;
  }
  return counts;
});

// Filtered file list
const filteredFiles = computed<NormalizedFileEntry[]>(() => {
  if (!pack.value) return [];
  if (!kindFilter.value) return pack.value.files;
  return pack.value.files.filter((f) => f.kind === kindFilter.value);
});

function getCategory(kind: string): string {
  return getRendererCategory(kind);
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function resetError() {
  err.value = "";
}

async function loadZip(f: File) {
  resetError();
  try {
    pack.value = await loadNormalizedPack(f);
    // Default preview: first CSV if present, else first file
    const firstCsv = pack.value.files.find((x) => x.kind.endsWith("_csv"));
    activePath.value = (firstCsv ?? pack.value.files[0])?.relpath ?? "";
    kindFilter.value = "";
    selectedPeak.value = null;
    audioJumpError.value = "";
  } catch (e: unknown) {
    pack.value = null;
    activePath.value = "";
    err.value = e instanceof Error ? e.message : String(e);
  }
}

async function onPick(ev: Event) {
  const input = ev.target as HTMLInputElement;
  const f = input.files?.[0];
  if (f) await loadZip(f);
}

async function onDrop(ev: DragEvent) {
  const f = ev.dataTransfer?.files?.[0];
  if (f) await loadZip(f);
}

function selectFile(relpath: string) {
  activePath.value = relpath;
}

function clearSelectedPeak() {
  selectedPeak.value = null;
  audioJumpError.value = "";
}

function clearCursorOnly() {
  // Keep details panel context but clear the linked cursor frequency.
  if (!selectedPeak.value) return;
  selectedPeak.value = { ...selectedPeak.value, freq_hz: NaN };
  // We treat NaN as "no cursor" in the renderer binding below by mapping to null.
}

function pointIdFromSpectrumRelpath(relpath: string): string | null {
  // spectra/points/{POINT_ID}/spectrum.csv
  const m = relpath.match(/^spectra\/points\/([^/]+)\/spectrum\.csv$/);
  return m?.[1] ?? null;
}

function audioRelpathForPoint(pointId: string): string {
  // Contracted path for point audio in viewer_pack_v1
  return `audio/points/${pointId}.wav`;
}

function onPeakSelected(payload: any) {
  audioJumpError.value = "";
  const spectrumRelpath = typeof payload?.spectrumRelpath === "string" ? payload.spectrumRelpath : activePath.value;
  const peaksRelpath = findSiblingPeaksRelpath(spectrumRelpath) ?? "";
  const pointId = pointIdFromSpectrumRelpath(spectrumRelpath);
  const freq_hz = Number(payload?.freq_hz);
  if (!Number.isFinite(freq_hz)) return;

  const raw = payload?.raw ?? payload;
  let rawPretty = "";
  try {
    rawPretty = JSON.stringify(raw, null, 2);
  } catch {
    rawPretty = String(raw);
  }

  selectedPeak.value = {
    pointId,
    spectrumRelpath,
    peaksRelpath,
    peakIndex: Number(payload?.peakIndex ?? -1),
    freq_hz,
    label: typeof payload?.label === "string" ? payload.label : undefined,
    raw,
    rawPretty,
  };
}

function jumpToPointAudio() {
  audioJumpError.value = "";
  if (!pack.value || !selectedPeak.value?.pointId) return;
  const audioRel = audioRelpathForPoint(selectedPeak.value.pointId);
  const exists = pack.value.files.some((f) => f.relpath === audioRel);
  if (!exists) {
    audioJumpError.value = `Audio missing for point ${selectedPeak.value.pointId}: expected ${audioRel}`;
    return;
  }
  activePath.value = audioRel;
}

// If user navigates away from the source spectrum, keep selection but make sure
// details stay coherent: if activePath is not a spectrum.csv, we keep selectedPeak as-is.
// (This is Wave 3 behavior; Wave 6A persistence rules can extend later.)
watch(activePath, () => {
  audioJumpError.value = "";
});
</script>

<style scoped>
.page {
  padding: 16px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.header h1 {
  margin: 0;
}

.sub {
  opacity: 0.8;
  margin-top: 6px;
}

.sub code {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.125rem 0.35rem;
  border-radius: 3px;
  font-size: 0.9em;
}

.cursor-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
}
.cursor-pill-label {
  font-size: 0.8rem;
  opacity: 0.75;
}
.cursor-pill-val {
  font-size: 0.85rem;
  padding: 0.1rem 0.35rem;
  border-radius: 6px;
  background: rgba(147, 197, 253, 0.12);
  border: 1px solid rgba(147, 197, 253, 0.18);
}
.cursor-pill-clear {
  appearance: none;
  border: 0;
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  border-radius: 999px;
  padding: 2px 7px;
  cursor: pointer;
  line-height: 1.2;
}
.cursor-pill-clear:hover {
  background: rgba(255, 255, 255, 0.12);
}

@media (max-width: 720px) {
  .cursor-pill {
    width: 100%;
    justify-content: space-between;
  }
}

.drop {
  border: 2px dashed rgba(255, 255, 255, 0.25);
  border-radius: 14px;
  padding: 18px;
  margin: 14px 0;
}

.drop-inner {
  display: grid;
  gap: 8px;
  justify-items: start;
}

.drop-title {
  font-weight: 700;
}

.drop-sub {
  opacity: 0.75;
}

.err {
  background: rgba(255, 0, 0, 0.12);
  border: 1px solid rgba(255, 0, 0, 0.25);
  padding: 10px;
  border-radius: 10px;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-items: start;
}

.card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 12px;
}

.card.wide {
  grid-column: 1 / -1;
}

.kv {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}

.kv > div {
  display: grid;
  grid-template-columns: 170px 1fr;
  gap: 10px;
  align-items: center;
}

.kv span {
  opacity: 0.75;
}

.kv code {
  word-break: break-all;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 8px 0;
}

.filter-select {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  font-size: 0.9rem;
}

.file-count {
  font-size: 0.85rem;
  opacity: 0.7;
}

.tbl {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}

.tbl th,
.tbl td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 8px;
  text-align: left;
}

.tbl tbody tr:hover {
  background: rgba(255, 255, 255, 0.04);
}

.tbl tbody tr.active {
  background: rgba(66, 184, 131, 0.15);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.path-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kind-badge {
  display: inline-block;
  padding: 0.125rem 0.35rem;
  border-radius: 4px;
  font-size: 0.8rem;
  background: rgba(255, 255, 255, 0.1);
}

.kind-badge[data-category="audio"] {
  background: rgba(66, 184, 131, 0.2);
  color: #42b883;
}

.kind-badge[data-category="image"] {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.kind-badge[data-category="csv"] {
  background: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.kind-badge[data-category="spectrum_chart"] {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.kind-badge[data-category="json"] {
  background: rgba(156, 39, 176, 0.2);
  color: #ce93d8;
}

.kind-badge[data-category="markdown"] {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.btn {
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  cursor: pointer;
  color: inherit;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.1);
}
.preview-container {
  margin-top: 12px;
}
.preview-split {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 12px;
  align-items: start;
}
.preview-main {
  min-width: 0;
}
.preview-side {
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  padding-left: 12px;
}
.side-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}
.side-title {
  font-weight: 650;
}
.btn-small {
  padding: 5px 8px;
  border-radius: 8px;
  font-size: 0.8rem;
}
.side-empty {
  padding: 10px 0;
}
.muted {
  opacity: 0.75;
}
.side-body {
  display: grid;
  gap: 12px;
}
.side-kv {
  display: grid;
  gap: 6px;
}
.side-kv > div {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 10px;
  align-items: center;
}
.side-kv span {
  opacity: 0.75;
}
.side-actions {
  display: grid;
  gap: 8px;
}
.side-warn {
  font-size: 0.85rem;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.2);
  padding: 8px 10px;
  border-radius: 10px;
}
.side-raw {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px;
}
.side-summary {
  cursor: pointer;
  user-select: none;
  opacity: 0.9;
  margin-bottom: 8px;
}
.side-pre {
  max-height: 280px;
  overflow: auto;
  font-size: 0.8rem;
  line-height: 1.35;
  margin: 0;
}
.placeholder {
  padding: 2rem;
  text-align: center;
  opacity: 0.7;
}

@media (max-width: 980px) {
  .preview-split {
    grid-template-columns: 1fr;
  }
  .preview-side {
    border-left: none;
    padding-left: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 12px;
  }
}

/* Pack Debug Panel */
.pack-debug {
  margin-top: 8px;
}

.debug-summary {
  cursor: pointer;
  font-weight: 600;
  padding: 8px 0;
  user-select: none;
}

.debug-summary:hover {
  color: #42b883;
}

.debug-content {
  margin-top: 12px;
}

.debug-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.debug-section h3 {
  font-size: 0.9rem;
  margin: 0 0 8px 0;
  opacity: 0.8;
}

.debug-kv {
  display: flex;
  gap: 8px;
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.debug-kv span {
  opacity: 0.6;
  min-width: 100px;
}

.debug-kv code {
  word-break: break-all;
}

.hash {
  font-size: 0.75rem;
  opacity: 0.7;
}

.kind-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.kind-chip {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  background: rgba(255, 255, 255, 0.1);
}

.kind-chip[data-category="audio"] {
  background: rgba(66, 184, 131, 0.2);
  color: #42b883;
}

.kind-chip[data-category="spectrum_chart"] {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.kind-chip[data-category="csv"] {
  background: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.kind-chip[data-category="json"] {
  background: rgba(156, 39, 176, 0.2);
  color: #ce93d8;
}

.kind-chip[data-category="image"] {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.debug-tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.debug-tbl th,
.debug-tbl td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 6px 8px;
  text-align: left;
}

.debug-tbl th {
  opacity: 0.6;
  font-weight: 500;
}

.debug-tbl tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}
</style>
