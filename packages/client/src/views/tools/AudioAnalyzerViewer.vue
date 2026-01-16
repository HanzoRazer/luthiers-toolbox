<template>
  <div class="page">
    <header class="header">
      <h1>🎛️ Audio Analyzer Evidence Viewer</h1>
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
          <component
            :is="currentRenderer"
            :entry="activeEntry"
            :bytes="activeBytes"
          />
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
import { ref, computed, shallowRef, type Component } from "vue";
import { loadNormalizedPack, type NormalizedPack, type NormalizedFileEntry } from "@/evidence";
import { pickRenderer, getRendererCategory } from "@/tools/audio_analyzer/renderers";

const pack = shallowRef<NormalizedPack | null>(null);
const err = ref<string>("");
const activePath = ref<string>("");
const kindFilter = ref<string>("");

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
</script>

<style scoped>
.page {
  padding: 16px;
  max-width: 1200px;
  margin: 0 auto;
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

.placeholder {
  padding: 2rem;
  text-align: center;
  opacity: 0.7;
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
