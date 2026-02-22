<template>
  <div class="p-4 flex flex-col gap-4">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-sm font-semibold text-gray-900">
          Cross-Lab Preset Risk Dashboard
        </h1>
        <p class="text-[11px] text-gray-600">
          Aggregated compare history across lanes (Rosette, Adaptive, Relief, Pipeline)
          grouped by lane &amp; preset. Time window filters apply to this view and
          the JSON snapshot download. Filters are URL-synced and can be saved as named views.
        </p>
      </div>
      <div class="flex items-center gap-2 text-[11px] text-gray-600">
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
          @click="handleRefresh"
        >
          Refresh
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!hasAnyFilter"
          @click="clearAllFilters"
        >
          Clear filters
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!filteredBuckets.length"
          @click="exportCsv"
        >
          Export All CSV
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!selectedBucket"
          @click="exportBucketCsv"
        >
          Export Bucket CSV
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!selectedBucket"
          @click="exportBucketJson"
        >
          Export Bucket JSON
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
          @click="downloadSnapshotJson"
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
      @apply-quick-range="applyQuickRange"
      @apply-lane-preset="applyLanePreset"
    />

    <!-- Saved Views -->
    <SavedViewsPanel
      ref="savedViewsPanelRef"
      storage-key="ltb_crosslab_risk_views"
      :get-current-filters="getCurrentFilters"
      @apply="handleApplyFilters"
    />

    <!-- Summary chips -->
    <div
      v-if="filteredBuckets.length"
      class="text-[11px] text-gray-700 flex flex-wrap gap-3"
    >
      <span>
        Buckets: <span class="font-mono">{{ filteredBuckets.length }}</span>
      </span>
      <span>
        Entries (sum of bucket counts): <span class="font-mono">{{ filteredEntriesCount }}</span>
      </span>
      <span
        v-if="since || until"
        class="text-[10px] text-gray-500"
      >
        Window:
        <span v-if="since">from <span class="font-mono">{{ since }}</span></span>
        <span v-if="since && until"> to </span>
        <span v-if="until"> <span class="font-mono">{{ until }}</span> </span>
      </span>
      <span
        v-if="quickRangeMode"
        class="text-[10px] text-indigo-600"
      >
        Quick range: <span class="font-mono">{{ currentQuickRangeLabel }}</span>
      </span>
    </div>

    <div
      v-else
      class="text-[11px] text-gray-500 italic"
    >
      No buckets match the current filters (or time window).
    </div>

    <!-- Buckets table -->
    <BucketsTable
      :buckets="filteredBuckets"
      @select-bucket="loadBucketDetails"
      @go-to-lab="goToLab"
    />

    <!-- Bucket details panel -->
    <BucketDetailsPanel
      :bucket="selectedBucket"
      :entries="bucketEntries"
      :loading="bucketEntriesLoading"
      :error="bucketEntriesError"
      :job-filter="jobFilter"
      @export-csv="exportBucketCsv"
      @download-json="downloadBucketJson"
      @close="clearBucketDetails"
    />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { SavedViewsPanel } from '@/components/ui'
import { FiltersBar, BucketsTable, BucketDetailsPanel } from '@/components/dashboard'
import {
  useRiskFilters,
  useRiskBuckets,
  useRiskBucketDetails,
  useRiskExports,
  useRiskNavigation
} from './risk-dashboard'

// =============================================================================
// Saved Views Panel Ref
// =============================================================================

const savedViewsPanelRef = ref<InstanceType<typeof SavedViewsPanel> | null>(null)

// =============================================================================
// Composables
// =============================================================================

const {
  laneFilter,
  presetFilter,
  jobFilter,
  since,
  until,
  quickRangeMode,
  hasAnyFilter,
  currentQuickRangeLabel,
  lanePresets,
  applyQuickRange,
  applyLanePreset,
  clearAllFilters: doClearAllFilters,
  getCurrentFilters,
  handleApplyFilters: doHandleApplyFilters,
  applyQueryToFilters,
  filtersAreEmpty
} = useRiskFilters()

const {
  filteredBuckets,
  filteredEntriesCount,
  allLanes,
  allPresets,
  refresh
} = useRiskBuckets({
  laneFilter,
  presetFilter,
  since,
  until
})

const {
  selectedBucket,
  bucketEntries,
  bucketEntriesLoading,
  bucketEntriesError,
  loadBucketDetails,
  clearBucketDetails
} = useRiskBucketDetails({
  jobFilter
})

const {
  exportCsv,
  exportBucketCsv,
  exportBucketJson,
  downloadBucketJson,
  downloadSnapshotJson
} = useRiskExports({
  filteredBuckets,
  selectedBucket,
  bucketEntries,
  jobFilter,
  since,
  until,
  setError: (msg) => {
    bucketEntriesError.value = msg
  }
})

const { goToLab } = useRiskNavigation({ jobFilter })

// =============================================================================
// Methods
// =============================================================================

function clearAllFilters(): void {
  doClearAllFilters()
  clearBucketDetails()
  refresh()
}

function handleApplyFilters(filters: Record<string, string>): void {
  doHandleApplyFilters(filters)
  clearBucketDetails()
  refresh()
}

async function handleRefresh(): Promise<void> {
  clearBucketDetails()
  await refresh()
}

function applyDefaultViewIfNeeded(): void {
  const hasQuery =
    !!laneFilter.value ||
    !!presetFilter.value ||
    !!jobFilter.value ||
    !!since.value ||
    !!until.value

  if (hasQuery) return
  if (!filtersAreEmpty()) return

  // Access default view from the panel component
  const def = savedViewsPanelRef.value?.defaultView
  if (!def) {
    // if no default view, default quick range is "all"
    quickRangeMode.value = 'all'
    return
  }
  handleApplyFilters(def.filters)
}

// =============================================================================
// Lifecycle
// =============================================================================

onMounted(async () => {
  applyQueryToFilters()
  // Wait for panel to mount and load views before applying default
  await nextTick()
  applyDefaultViewIfNeeded()
  refresh()
})
</script>
