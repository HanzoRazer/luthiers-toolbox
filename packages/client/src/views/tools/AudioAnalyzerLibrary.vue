<template>
  <div class="page">
    <header class="header">
      <h1>Acoustics Library</h1>
      <p class="sub">
        Upload, browse, and open <code>viewer_pack</code> evidence bundles.
      </p>
    </header>

    <!-- Import Panel -->
    <section class="card">
      <h2>Import ZIP</h2>
      <div class="import-form">
        <div class="import-row">
          <input
            type="file"
            accept=".zip"
            ref="fileInput"
            @change="onFileChange"
          />
          <button class="btn" :disabled="!selectedFile || importing" @click="doImport">
            {{ importing ? "Importing..." : "Import" }}
          </button>
        </div>
        <div class="import-options">
          <label>
            <span>Session ID (optional)</span>
            <input v-model="sessionId" type="text" placeholder="session_abc123" />
          </label>
          <label>
            <span>Batch Label (optional)</span>
            <input v-model="batchLabel" type="text" placeholder="batch_001" />
          </label>
        </div>
        <div v-if="importResult" class="import-result">
          Imported <code>{{ importResult.run_id }}</code> —
          {{ importResult.attachments_written }} written,
          {{ importResult.attachments_deduped }} deduped
        </div>
        <div v-if="importError" class="import-error">
          {{ importError }}
        </div>
      </div>
    </section>

    <!-- Facets Panel -->
    <section class="card">
      <h2>Facets</h2>
      <div v-if="facetsLoading" class="muted">Loading facets...</div>
      <div v-else-if="facetsError" class="import-error">{{ facetsError }}</div>
      <div v-else class="facets-grid">
        <div class="facet-group">
          <h3>Kind</h3>
          <div class="facet-chips">
            <button
              v-for="item in facets?.kinds"
              :key="item.kind"
              class="facet-chip"
              :class="{ active: kindFilter === item.kind }"
              @click="toggleKindFilter(item.kind)"
            >
              {{ item.kind }} ({{ item.count }})
            </button>
          </div>
        </div>
        <div class="facet-group">
          <h3>MIME</h3>
          <div class="facet-chips">
            <button
              v-for="item in facets?.mime_exact"
              :key="item.mime"
              class="facet-chip"
              :class="{ active: mimeFilter === item.mime }"
              @click="toggleMimeFilter(item.mime)"
            >
              {{ item.mime }} ({{ item.count }})
            </button>
          </div>
        </div>
        <div class="facet-total">
          Total: {{ facets?.total ?? 0 }} attachments
        </div>
      </div>
    </section>

    <!-- Recent Panel -->
    <section class="card">
      <h2>Recent</h2>
      <div v-if="recentLoading" class="muted">Loading...</div>
      <div v-else-if="recentError" class="import-error">{{ recentError }}</div>
      <div v-else-if="!recentData?.entries?.length" class="muted">
        No recent attachments. Import a viewer_pack to get started.
      </div>
      <div v-else class="recent-list">
        <div
          v-for="entry in recentData.entries"
          :key="entry.sha256"
          class="recent-item"
        >
          <div class="recent-info">
            <span class="recent-filename" :title="entry.filename">{{ entry.filename }}</span>
            <code class="kind-badge">{{ entry.kind }}</code>
            <span class="recent-meta">{{ formatSize(entry.size_bytes) }}</span>
          </div>
          <div class="recent-actions">
            <a
              v-if="isViewerPack(entry)"
              class="btn btn-sm"
              :href="`/tools/audio-analyzer?sha256=${entry.sha256}`"
            >
              Open
            </a>
            <a
              class="btn btn-sm"
              :href="getDownloadUrl(entry.sha256)"
              download
            >
              Download
            </a>
          </div>
        </div>
        <button
          v-if="recentData.next_cursor"
          class="btn"
          @click="loadMoreRecent"
        >
          More
        </button>
      </div>
    </section>

    <!-- Browse Table -->
    <section class="card wide">
      <h2>Browse Attachments</h2>
      <div class="filter-bar">
        <span v-if="kindFilter || mimeFilter" class="active-filters">
          Filters:
          <code v-if="kindFilter">kind={{ kindFilter }}</code>
          <code v-if="mimeFilter">mime={{ mimeFilter }}</code>
          <button class="btn-clear" @click="clearFilters">Clear</button>
        </span>
        <span class="browse-count">
          Showing {{ browseData?.count ?? 0 }} of {{ browseData?.total_in_index ?? 0 }}
        </span>
      </div>

      <div v-if="browseLoading" class="muted">Loading...</div>
      <div v-else-if="browseError" class="import-error">{{ browseError }}</div>
      <table v-else class="tbl">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Kind</th>
            <th>MIME</th>
            <th>Size</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in browseData?.entries" :key="entry.sha256">
            <td class="mono filename-cell" :title="entry.filename">{{ entry.filename }}</td>
            <td><code class="kind-badge">{{ entry.kind }}</code></td>
            <td class="mono">{{ entry.mime }}</td>
            <td class="mono">{{ formatSize(entry.size_bytes) }}</td>
            <td class="actions-cell">
              <a
                v-if="isViewerPack(entry)"
                class="btn"
                :href="`/tools/audio-analyzer?sha256=${entry.sha256}`"
              >
                Open
              </a>
              <a
                class="btn"
                :href="getDownloadUrl(entry.sha256)"
                download
              >
                Download
              </a>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="pagination" v-if="browseData">
        <button
          class="btn"
          :disabled="!browseData.next_cursor"
          @click="loadNextPage"
        >
          Next Page
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  importZip,
  browse,
  getFacets,
  getRecent,
  getDownloadUrl,
  isViewerPack,
  formatSize,
} from "@/sdk/endpoints/rmosAcoustics";
import type {
  ImportResponse,
  BrowseResponse,
  FacetsResponse,
  RecentResponse,
  AttachmentMetaEntry,
} from "@/types/rmosAcoustics";

// Import state
const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const sessionId = ref("");
const batchLabel = ref("");
const importing = ref(false);
const importResult = ref<ImportResponse | null>(null);
const importError = ref("");

// Facets state
const facets = ref<FacetsResponse | null>(null);
const facetsLoading = ref(false);
const facetsError = ref("");

// Browse state
const browseData = ref<BrowseResponse | null>(null);
const browseLoading = ref(false);
const browseError = ref("");
const kindFilter = ref("");
const mimeFilter = ref("");
const cursor = ref<string | null>(null);

// Recent state
const recentData = ref<RecentResponse | null>(null);
const recentLoading = ref(false);
const recentError = ref("");
const recentCursor = ref<string | null>(null);

function onFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
  importResult.value = null;
  importError.value = "";
}

async function doImport() {
  if (!selectedFile.value) return;
  importing.value = true;
  importError.value = "";
  importResult.value = null;

  try {
    const result = await importZip(selectedFile.value, {
      session_id: sessionId.value || undefined,
      batch_label: batchLabel.value || undefined,
    });
    importResult.value = result;
    // Refresh facets, recent, and browse after import
    await Promise.all([loadFacets(), loadRecent(), loadBrowse()]);
  } catch (e) {
    importError.value = e instanceof Error ? e.message : String(e);
  } finally {
    importing.value = false;
  }
}

async function loadFacets() {
  facetsLoading.value = true;
  facetsError.value = "";
  try {
    facets.value = await getFacets();
  } catch (e) {
    facetsError.value = e instanceof Error ? e.message : String(e);
  } finally {
    facetsLoading.value = false;
  }
}

async function loadBrowse() {
  browseLoading.value = true;
  browseError.value = "";
  try {
    browseData.value = await browse({
      kind: kindFilter.value || undefined,
      mime_prefix: mimeFilter.value || undefined,
      cursor: cursor.value || undefined,
      limit: 20,
      include_urls: true,
    });
  } catch (e) {
    browseError.value = e instanceof Error ? e.message : String(e);
  } finally {
    browseLoading.value = false;
  }
}

async function loadRecent() {
  recentLoading.value = true;
  recentError.value = "";
  recentCursor.value = null;
  try {
    recentData.value = await getRecent({
      limit: 10,
      include_urls: true,
    });
  } catch (e) {
    recentError.value = e instanceof Error ? e.message : String(e);
  } finally {
    recentLoading.value = false;
  }
}

async function loadMoreRecent() {
  if (!recentData.value?.next_cursor) return;
  recentLoading.value = true;
  try {
    const more = await getRecent({
      limit: 10,
      cursor: recentData.value.next_cursor,
      include_urls: true,
    });
    // Append entries
    recentData.value = {
      ...more,
      entries: [...(recentData.value?.entries ?? []), ...more.entries],
    };
  } catch (e) {
    recentError.value = e instanceof Error ? e.message : String(e);
  } finally {
    recentLoading.value = false;
  }
}

function toggleKindFilter(kind: string) {
  kindFilter.value = kindFilter.value === kind ? "" : kind;
  cursor.value = null;
  loadBrowse();
}

function toggleMimeFilter(mime: string) {
  mimeFilter.value = mimeFilter.value === mime ? "" : mime;
  cursor.value = null;
  loadBrowse();
}

function clearFilters() {
  kindFilter.value = "";
  mimeFilter.value = "";
  cursor.value = null;
  loadBrowse();
}

function loadNextPage() {
  if (browseData.value?.next_cursor) {
    cursor.value = browseData.value.next_cursor;
    loadBrowse();
  }
}

onMounted(() => {
  loadFacets();
  loadRecent();
  loadBrowse();
});
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

.card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 12px;
  margin-top: 12px;
}

.card.wide {
  margin-top: 12px;
}

.card h2 {
  margin: 0 0 12px 0;
  font-size: 1rem;
}

/* Import Form */
.import-form {
  display: grid;
  gap: 12px;
}

.import-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.import-options {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.import-options label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
}

.import-options label span {
  opacity: 0.75;
}

.import-options input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
}

.import-result {
  padding: 8px 12px;
  background: rgba(66, 184, 131, 0.15);
  border: 1px solid rgba(66, 184, 131, 0.25);
  border-radius: 8px;
  font-size: 0.9rem;
}

.import-error {
  padding: 8px 12px;
  background: rgba(255, 0, 0, 0.12);
  border: 1px solid rgba(255, 0, 0, 0.25);
  border-radius: 8px;
  font-size: 0.9rem;
}

/* Facets */
.facets-grid {
  display: grid;
  gap: 12px;
}

.facet-group h3 {
  margin: 0 0 8px 0;
  font-size: 0.85rem;
  opacity: 0.75;
}

.facet-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.facet-chip {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}

.facet-chip:hover {
  background: rgba(255, 255, 255, 0.1);
}

.facet-chip.active {
  background: rgba(66, 184, 131, 0.2);
  border-color: rgba(66, 184, 131, 0.4);
}

.facet-total {
  font-size: 0.85rem;
  opacity: 0.7;
}

/* Recent Panel */
.recent-list {
  display: grid;
  gap: 8px;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  gap: 12px;
}

.recent-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.recent-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.recent-filename {
  font-family: monospace;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 280px;
}

.recent-meta {
  font-size: 0.8rem;
  opacity: 0.6;
  white-space: nowrap;
}

.recent-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 0.8rem;
}

/* Browse Table */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.active-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.active-filters code {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.btn-clear {
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: transparent;
  color: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}

.btn-clear:hover {
  background: rgba(255, 255, 255, 0.1);
}

.browse-count {
  font-size: 0.85rem;
  opacity: 0.7;
}

.tbl {
  width: 100%;
  border-collapse: collapse;
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

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85rem;
}

.filename-cell {
  max-width: 250px;
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

.actions-cell {
  display: flex;
  gap: 6px;
}

.btn {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  cursor: pointer;
  color: inherit;
  text-decoration: none;
  font-size: 0.85rem;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.muted {
  opacity: 0.7;
  padding: 8px 0;
}
</style>
