<template>
  <div class="page">
    <header class="header">
      <h1>Acoustics Runs</h1>
      <p class="sub">
        Browse imports/sessions by run. Click a run to see attachments.
      </p>
    </header>

    <div class="layout">
      <!-- Runs List Panel -->
      <RunsListPanel
        :runs="runsData?.runs ?? null"
        :loading="runsLoading"
        :error="runsError"
        :selected-run-id="selectedRunId"
        :session-id-filter="sessionIdFilter"
        :batch-label-filter="batchLabelFilter"
        :has-more="!!runsData?.next_cursor"
        @select="selectRun"
        @load-more="loadMoreRuns"
        @update:session-id-filter="sessionIdFilter = $event; debouncedLoad()"
        @update:batch-label-filter="batchLabelFilter = $event; debouncedLoad()"
      />

      <!-- Run Detail Panel -->
      <RunDetailPanel
        :run-id="selectedRunId"
        :data="detailData"
        :loading="detailLoading"
        :error="detailError"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import {
  browseRuns,
  getRun,
} from "@/sdk/endpoints/rmosAcoustics";
import type {
  RunsBrowseResponse,
  RunDetailResponse,
} from "@/types/rmosAcoustics";
import RunsListPanel from "./audio_analyzer_runs/RunsListPanel.vue";
import RunDetailPanel from "./audio_analyzer_runs/RunDetailPanel.vue";

// Runs list state
const runsData = ref<RunsBrowseResponse | null>(null);
const runsLoading = ref(false);
const runsError = ref("");
const sessionIdFilter = ref("");
const batchLabelFilter = ref("");

// Detail state
const selectedRunId = ref<string | null>(null);
const detailData = ref<RunDetailResponse | null>(null);
const detailLoading = ref(false);
const detailError = ref("");

// Debounce timer
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function debouncedLoad() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    loadRuns();
  }, 300);
}

async function loadRuns() {
  runsLoading.value = true;
  runsError.value = "";
  try {
    runsData.value = await browseRuns({
      limit: 20,
      session_id: sessionIdFilter.value || undefined,
      batch_label: batchLabelFilter.value || undefined,
    });
  } catch (e) {
    runsError.value = e instanceof Error ? e.message : String(e);
  } finally {
    runsLoading.value = false;
  }
}

async function loadMoreRuns() {
  if (!runsData.value?.next_cursor) return;
  runsLoading.value = true;
  try {
    const more = await browseRuns({
      limit: 20,
      cursor: runsData.value.next_cursor,
      session_id: sessionIdFilter.value || undefined,
      batch_label: batchLabelFilter.value || undefined,
    });
    runsData.value = {
      ...more,
      runs: [...(runsData.value?.runs ?? []), ...more.runs],
    };
  } catch (e) {
    runsError.value = e instanceof Error ? e.message : String(e);
  } finally {
    runsLoading.value = false;
  }
}

async function selectRun(runId: string) {
  selectedRunId.value = runId;
  detailLoading.value = true;
  detailError.value = "";
  detailData.value = null;
  try {
    detailData.value = await getRun(runId, { include_urls: true });
  } catch (e) {
    detailError.value = e instanceof Error ? e.message : String(e);
  } finally {
    detailLoading.value = false;
  }
}

onMounted(() => {
  loadRuns();
});

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer);
});
</script>

<style scoped>
.page {
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
}

.header h1 {
  margin: 0;
}

.sub {
  opacity: 0.8;
  margin-top: 6px;
}

.layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 16px;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
