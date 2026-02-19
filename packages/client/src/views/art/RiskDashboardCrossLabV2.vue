<template>
  <div class="p-4 flex flex-col gap-4">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-sm font-semibold text-gray-900">Cross-Lab Preset Risk Dashboard</h1>
        <p class="text-[11px] text-gray-600">
          Aggregated compare history across lanes (Rosette, Adaptive, Relief, Pipeline) grouped by lane &amp; preset.
          Time window filters apply to this view and the JSON snapshot download. Filters are URL-synced and can be
          saved as named views.
        </p>
      </div>
      <div class="flex items-center gap-2 text-[11px] text-gray-600">
        <button class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50" @click="handleRefresh">
          Refresh
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!hasAnyFilter"
          @click="handleClearFilters"
        >
          Clear filters
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!computedFilteredBuckets.length"
          @click="handleExportCsv"
        >
          Export All CSV
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!selectedBucket"
          @click="handleExportBucketCsv"
        >
          Export Bucket CSV
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!selectedBucket"
          @click="handleExportBucketJson"
        >
          Export Bucket JSON
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
          @click="handleDownloadSnapshot"
        >
          Download JSON snapshot
        </button>
      </div>
    </div>

    <!-- Filters -->
    <FiltersBar
      v-model:lane="laneFilter"
      v-model:preset="presetFilter"
      v-model:job-hint="jobFilter"
      v-model:since="since"
      v-model:until="until"
      v-model:quick-range="quickRangeMode"
      :all-lanes="allLanes"
      :all-presets="allPresets"
      :lane-presets="lanePresets"
      @apply-quick-range="handleApplyQuickRange"
      @apply-lane-preset="handleApplyLanePreset"
    />

    <!-- Saved Views -->
    <SavedViewsPanel
      ref="savedViewsPanelRef"
      storage-key="ltb_crosslab_risk_views"
      :get-current-filters="getCurrentFilters"
      @apply="handleApplyFilters"
    />

    <!-- Summary chips -->
    <div v-if="computedFilteredBuckets.length" class="text-[11px] text-gray-700 flex flex-wrap gap-3">
      <span>Buckets: <span class="font-mono">{{ computedFilteredBuckets.length }}</span></span>
      <span>Entries (sum of bucket counts): <span class="font-mono">{{ computedEntriesCount }}</span></span>
      <span v-if="since || until" class="text-[10px] text-gray-500">
        Window:
        <span v-if="since">from <span class="font-mono">{{ since }}</span></span>
        <span v-if="since && until"> to </span>
        <span v-if="until"><span class="font-mono">{{ until }}</span></span>
      </span>
      <span v-if="quickRangeMode" class="text-[10px] text-indigo-600">
        Quick range: <span class="font-mono">{{ currentQuickRangeLabel }}</span>
      </span>
    </div>

    <div v-else class="text-[11px] text-gray-500 italic">
      No buckets match the current filters (or time window).
    </div>

    <!-- Buckets table -->
    <BucketsTable :buckets="computedFilteredBuckets" @select-bucket="handleSelectBucket" @go-to-lab="handleGoToLab" />

    <!-- Bucket details panel -->
    <BucketDetailsPanel
      :bucket="selectedBucket"
      :entries="bucketEntries"
      :loading="bucketEntriesLoading"
      :error="bucketEntriesError"
      :job-filter="jobFilter"
      @export-csv="handleExportBucketCsv"
      @download-json="handleDownloadBucketJson"
      @close="clearBucketDetails"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { SavedViewsPanel } from '@/components/ui'
import { FiltersBar, BucketsTable, BucketDetailsPanel } from '@/components/dashboard'
import { useRiskFilters, useRiskBuckets, useRiskExport, type QuickRangeMode } from './composables'

// Filters composable
const {
  laneFilter,
  presetFilter,
  jobFilter,
  since,
  until,
  quickRangeMode,
  lanePresets,
  hasAnyFilter,
  currentQuickRangeLabel,
  getCurrentFilters,
  applyFilters,
  applyQuickRange,
  applyLanePreset,
  clearAllFilters,
  applyQueryToFilters,
  syncFiltersToQuery,
  filtersAreEmpty,
} = useRiskFilters()

// Buckets composable
const {
  bucketsRaw,
  selectedBucket,
  bucketEntries,
  bucketEntriesLoading,
  bucketEntriesError,
  allLanes,
  allPresets,
  filteredBuckets,
  filteredEntriesCount,
  refresh,
  loadBucketDetails,
  clearBucketDetails,
  goToLab,
} = useRiskBuckets()

// Export composable
const { exportCsv, exportBucketCsv, exportBucketJson, downloadBucketJson, downloadSnapshotJson } = useRiskExport()

// Saved views panel ref
const savedViewsPanelRef = ref<InstanceType<typeof SavedViewsPanel> | null>(null)
const route = useRoute()

// Computed filtered buckets (using filter state)
const computedFilteredBuckets = computed(() => filteredBuckets(laneFilter.value, presetFilter.value))
const computedEntriesCount = computed(() => filteredEntriesCount(laneFilter.value, presetFilter.value))

// Event handlers
function handleRefresh() {
  refresh(since.value, until.value)
}

function handleClearFilters() {
  clearAllFilters()
  clearBucketDetails()
  handleRefresh()
}

function handleApplyQuickRange(mode: QuickRangeMode) {
  applyQuickRange(mode)
  clearBucketDetails()
  handleRefresh()
}

function handleApplyLanePreset(id: string) {
  applyLanePreset(id)
  clearBucketDetails()
  handleRefresh()
}

function handleApplyFilters(filters: Record<string, string>) {
  applyFilters(filters)
  clearBucketDetails()
  handleRefresh()
}

function handleSelectBucket(bucket: (typeof bucketsRaw.value)[0]) {
  loadBucketDetails(bucket, jobFilter.value)
}

function handleGoToLab(bucket: (typeof bucketsRaw.value)[0]) {
  goToLab(bucket, jobFilter.value)
}

function handleExportCsv() {
  exportCsv(computedFilteredBuckets.value, since.value, until.value)
}

function handleExportBucketCsv() {
  exportBucketCsv(selectedBucket.value)
}

function handleExportBucketJson() {
  exportBucketJson(selectedBucket.value)
}

function handleDownloadBucketJson() {
  downloadBucketJson(selectedBucket.value, bucketEntries.value, jobFilter.value, since.value, until.value)
}

function handleDownloadSnapshot() {
  downloadSnapshotJson(since.value, until.value)
}

function applyDefaultViewIfNeeded() {
  const hasQuery =
    typeof route.query.lane === 'string' ||
    typeof route.query.preset === 'string' ||
    typeof route.query.job_hint === 'string' ||
    typeof route.query.since === 'string' ||
    typeof route.query.until === 'string'

  if (hasQuery) return
  if (!filtersAreEmpty()) return

  const def = savedViewsPanelRef.value?.defaultView
  if (!def) {
    quickRangeMode.value = 'all'
    return
  }
  handleApplyFilters(def.filters)
}

// Watchers for filter sync
watch([laneFilter, presetFilter, jobFilter], () => {
  syncFiltersToQuery()
  clearBucketDetails()
})

watch([since, until], () => {
  if (since.value || until.value) {
    quickRangeMode.value = ''
  } else {
    quickRangeMode.value = 'all'
  }
  syncFiltersToQuery()
  clearBucketDetails()
  handleRefresh()
})

onMounted(async () => {
  applyQueryToFilters()
  await nextTick()
  applyDefaultViewIfNeeded()
  handleRefresh()
})
</script>
