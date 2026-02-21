<template>
  <div :class="styles.page">
    <header :class="styles.header">
      <h1>Acoustics Library</h1>
      <p :class="styles.sub">
        Upload, browse, and open <code>viewer_pack</code> evidence bundles.
      </p>
    </header>

    <!-- Import Panel -->
    <section :class="styles.card">
      <h2>Import ZIP</h2>
      <div :class="styles.importForm">
        <div :class="styles.importRow">
          <input
            ref="fileInput"
            type="file"
            accept=".zip"
            @change="onFileChange"
          >
          <button
            :class="styles.btn"
            :disabled="!selectedFile || importing"
            @click="doImport"
          >
            {{ importing ? "Importing..." : "Import" }}
          </button>
        </div>
        <div :class="styles.importOptions">
          <label>
            <span>Session ID (optional)</span>
            <input
              v-model="sessionId"
              type="text"
              placeholder="session_abc123"
            >
          </label>
          <label>
            <span>Batch Label (optional)</span>
            <input
              v-model="batchLabel"
              type="text"
              placeholder="batch_001"
            >
          </label>
        </div>
        <div
          v-if="importResult"
          :class="styles.importResult"
        >
          Imported <code>{{ importResult.run_id }}</code> —
          {{ importResult.attachments_written }} written,
          {{ importResult.attachments_deduped }} deduped
        </div>
        <div
          v-if="importError"
          :class="styles.importError"
        >
          {{ importError }}
        </div>
      </div>
    </section>

    <!-- Facets Panel -->
    <section :class="styles.card">
      <h2>Facets</h2>
      <div
        v-if="facetsLoading"
        :class="styles.muted"
      >
        Loading facets...
      </div>
      <div
        v-else-if="facetsError"
        :class="styles.importError"
      >
        {{ facetsError }}
      </div>
      <div
        v-else
        :class="styles.facetsGrid"
      >
        <div :class="styles.facetGroup">
          <h3>Kind</h3>
          <div :class="styles.facetChips">
            <button
              v-for="item in facets?.kinds"
              :key="item.kind"
              :class="kindFilter === item.kind ? styles.facetChipActive : styles.facetChip"
              @click="toggleKindFilter(item.kind)"
            >
              {{ item.kind }} ({{ item.count }})
            </button>
          </div>
        </div>
        <div :class="styles.facetGroup">
          <h3>MIME</h3>
          <div :class="styles.facetChips">
            <button
              v-for="item in facets?.mime_exact"
              :key="item.mime"
              :class="mimeFilter === item.mime ? styles.facetChipActive : styles.facetChip"
              @click="toggleMimeFilter(item.mime)"
            >
              {{ item.mime }} ({{ item.count }})
            </button>
          </div>
        </div>
        <div :class="styles.facetTotal">
          Total: {{ facets?.total ?? 0 }} attachments
        </div>
      </div>
    </section>

    <!-- Recent Panel -->
    <section :class="styles.card">
      <h2>Recent</h2>
      <div
        v-if="recentLoading"
        :class="styles.muted"
      >
        Loading...
      </div>
      <div
        v-else-if="recentError"
        :class="styles.importError"
      >
        {{ recentError }}
      </div>
      <div
        v-else-if="!recentData?.entries?.length"
        :class="styles.muted"
      >
        No recent attachments. Import a viewer_pack to get started.
      </div>
      <div
        v-else
        :class="styles.recentList"
      >
        <div
          v-for="entry in recentData.entries"
          :key="entry.sha256"
          :class="styles.recentItem"
        >
          <div :class="styles.recentInfo">
            <span
              :class="styles.recentFilename"
              :title="entry.filename"
            >{{ entry.filename }}</span>
            <code :class="styles.kindBadge">{{ entry.kind }}</code>
            <span :class="styles.recentMeta">{{ formatSize(entry.size_bytes) }}</span>
          </div>
          <div :class="styles.recentActions">
            <a
              v-if="isViewerPack(entry)"
              :class="[styles.btn, styles.btnSm]"
              :href="`/tools/audio-analyzer?sha256=${entry.sha256}`"
            >
              Open
            </a>
            <a
              :class="[styles.btn, styles.btnSm]"
              :href="getDownloadUrl(entry.sha256)"
              download
            >
              Download
            </a>
          </div>
        </div>
        <button
          v-if="recentData.next_cursor"
          :class="styles.btn"
          @click="loadMoreRecent"
        >
          More
        </button>
      </div>
    </section>

    <!-- Browse Table -->
    <section :class="styles.cardWide">
      <h2>Browse Attachments</h2>
      <div :class="styles.filterBar">
        <span
          v-if="kindFilter || mimeFilter"
          :class="styles.activeFilters"
        >
          Filters:
          <code v-if="kindFilter">kind={{ kindFilter }}</code>
          <code v-if="mimeFilter">mime={{ mimeFilter }}</code>
          <button
            :class="styles.btnClear"
            @click="clearFilters"
          >Clear</button>
        </span>
        <span :class="styles.browseCount">
          Showing {{ browseData?.count ?? 0 }} of {{ browseData?.total_in_index ?? 0 }}
        </span>
      </div>

      <div
        v-if="browseLoading"
        :class="styles.muted"
      >
        Loading...
      </div>
      <div
        v-else-if="browseError"
        :class="styles.importError"
      >
        {{ browseError }}
      </div>
      <table
        v-else
        :class="styles.tbl"
      >
        <thead>
          <tr>
            <th>Filename</th>
            <th>Kind</th>
            <th>Validation</th>
            <th>MIME</th>
            <th>Size</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in browseData?.entries"
            :key="entry.sha256"
          >
            <td
              :class="[styles.mono, styles.filenameCell]"
              :title="entry.filename"
            >
              {{ entry.filename }}
            </td>
            <td><code :class="styles.kindBadge">{{ entry.kind }}</code></td>
            <td>
              <span
                v-if="isViewerPack(entry)"
                :class="[styles.validationBadge, {
                  [styles.badgePass]: entry.validation_passed === true,
                  [styles.badgeFail]: entry.validation_passed === false,
                  [styles.badgeUnknown]: entry.validation_passed === undefined
                }]"
                :title="getValidationTooltip(entry)"
              >
                {{ getValidationLabel(entry) }}
              </span>
              <span
                v-else
                :class="styles.validationNa"
              >—</span>
            </td>
            <td :class="styles.mono">
              {{ entry.mime }}
            </td>
            <td :class="styles.mono">
              {{ formatSize(entry.size_bytes) }}
            </td>
            <td :class="styles.actionsCell">
              <a
                v-if="isViewerPack(entry)"
                :class="styles.btn"
                :href="`/tools/audio-analyzer?sha256=${entry.sha256}`"
              >
                Open
              </a>
              <a
                :class="styles.btn"
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
      <div
        v-if="browseData"
        :class="styles.pagination"
      >
        <button
          :class="styles.btn"
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
import styles from "./AudioAnalyzerLibrary.module.css";

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

// Validation badge helpers
function getValidationLabel(entry: AttachmentMetaEntry): string {
  if (entry.validation_passed === true) return "PASS";
  if (entry.validation_passed === false) return "FAIL";
  return "UNKNOWN";
}

function getValidationTooltip(entry: AttachmentMetaEntry): string {
  if (entry.validation_passed === undefined) {
    return "No validation report (legacy pack)";
  }
  const errors = entry.validation_errors ?? 0;
  const warnings = entry.validation_warnings ?? 0;
  return `${entry.validation_passed ? "Passed" : "Failed"}: ${errors} errors, ${warnings} warnings`;
}

onMounted(() => {
  loadFacets();
  loadRecent();
  loadBrowse();
});
</script>
