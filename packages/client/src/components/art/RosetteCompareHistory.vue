<template>
  <div class="mt-4 border rounded bg-white p-3">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-xs font-semibold text-gray-800">
        Compare History
      </h3>
      <div class="flex items-center gap-2">
        <button
          class="px-2 py-1 rounded border text-[10px] text-gray-600 hover:bg-gray-50"
          @click="refresh"
        >
          Refresh
        </button>
        <button
          class="px-2 py-1 rounded border text-[10px] text-gray-600 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!entries.length"
          @click="exportCsv"
        >
          Export CSV
        </button>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2 mb-2 text-[11px] text-gray-600">
      <span class="font-semibold">Lane:</span>
      <span class="font-mono">{{ lane }}</span>
      <span class="mx-1 text-gray-400">•</span>
      <span class="font-semibold">Job ID:</span>
      <span class="font-mono">
        {{ effectiveJobId || "— none —" }}
      </span>
    </div>

    <!-- Summary bar + sparkline -->
    <div
      v-if="entries.length"
      class="mb-2 flex flex-col gap-2"
    >
      <div class="flex flex-wrap items-center gap-3">
        <div class="text-[11px] text-gray-700 flex flex-wrap gap-3">
          <span>
            Entries: <span class="font-mono">{{ entries.length }}</span>
          </span>
          <span class="text-emerald-700">
            Avg Added: <span class="font-mono">{{ avgAdded }}</span>
          </span>
          <span class="text-rose-700">
            Avg Removed: <span class="font-mono">{{ avgRemoved }}</span>
          </span>
          <span class="text-gray-700">
            Avg Unchanged: <span class="font-mono">{{ avgUnchanged }}</span>
          </span>
        </div>

        <!-- Compare presets toggle -->
        <label class="flex items-center gap-1 text-[10px] text-gray-600 cursor-pointer">
          <input
            v-model="comparePresets"
            type="checkbox"
            class="h-3 w-3"
          >
          <span>Compare presets</span>
        </label>
      </div>

      <!-- Global sparklines (default mode) -->
      <GlobalSparklines
        v-if="!comparePresets"
        :spark-width="sparkWidth"
        :spark-height="sparkHeight"
        :added-spark-path="addedSparkPath"
        :removed-spark-path="removedSparkPath"
      />

      <!-- Per-preset sparklines (compare mode) -->
      <PresetSparklines
        v-else
        :spark-width="sparkWidth"
        :spark-height="sparkHeight"
        :preset-sparklines="presetSparklines"
      />

      <!-- Phase 27.5: Two-preset A/B overlay compare -->
      <div
        v-if="comparePresets && presetBuckets.length >= 2"
        class="mt-2 border rounded bg-gray-50 p-2 flex flex-col gap-2"
      >
        <div class="flex flex-wrap items-center gap-2 text-[10px] text-gray-700">
          <span class="font-semibold">A/B Overlay:</span>
          <select
            v-model="presetCompareA"
            class="border rounded px-1 py-0.5 text-[10px]"
          >
            <option
              v-for="bucket in presetBuckets"
              :key="bucket.name"
              :value="bucket.name"
            >
              {{ bucket.name }}
            </option>
          </select>
          <span class="text-gray-500">vs</span>
          <select
            v-model="presetCompareB"
            class="border rounded px-1 py-0.5 text-[10px]"
          >
            <option
              v-for="bucket in presetBuckets"
              :key="bucket.name"
              :value="bucket.name"
            >
              {{ bucket.name }}
            </option>
          </select>
        </div>

        <div class="flex items-center gap-3 text-[10px]">
          <div class="flex items-center gap-1">
            <span class="font-semibold text-gray-700">Added:</span>
            <svg
              :width="sparkWidth"
              :height="sparkHeight"
              viewBox="0 0 60 20"
            >
              <polyline
                v-if="pairAddedOverlay.a"
                :points="pairAddedOverlay.a"
                fill="none"
                stroke="#22c55e"
                stroke-width="1.5"
              />
              <polyline
                v-if="pairAddedOverlay.b"
                :points="pairAddedOverlay.b"
                fill="none"
                stroke="#f97316"
                stroke-width="1.5"
              />
            </svg>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-emerald-500" />
              <span class="text-gray-600">A</span>
            </div>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-orange-500" />
              <span class="text-gray-600">B</span>
            </div>
          </div>

          <div class="flex items-center gap-1">
            <span class="font-semibold text-gray-700">Removed:</span>
            <svg
              :width="sparkWidth"
              :height="sparkHeight"
              viewBox="0 0 60 20"
            >
              <polyline
                v-if="pairRemovedOverlay.a"
                :points="pairRemovedOverlay.a"
                fill="none"
                stroke="#ef4444"
                stroke-width="1.5"
              />
              <polyline
                v-if="pairRemovedOverlay.b"
                :points="pairRemovedOverlay.b"
                fill="none"
                stroke="#6366f1"
                stroke-width="1.5"
              />
            </svg>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-red-500" />
              <span class="text-gray-600">A</span>
            </div>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-indigo-500" />
              <span class="text-gray-600">B</span>
            </div>
          </div>
        </div>

        <!-- Phase 27.6: Numeric delta badges -->
        <PairStatsBadges
          v-if="pairStats"
          :pair-stats="pairStats"
        />
      </div>
    </div>

    <div
      v-else
      class="text-[11px] text-gray-500 italic"
    >
      No compare history yet for this lane/job.
    </div>

    <!-- History table -->
    <HistoryTable
      v-if="entries.length"
      :entries="entries"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * RosetteCompareHistory - Compare history panel with sparklines.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { onMounted, watch } from 'vue'
import GlobalSparklines from './rosette_compare_history/GlobalSparklines.vue'
import PresetSparklines from './rosette_compare_history/PresetSparklines.vue'
import PairStatsBadges from './rosette_compare_history/PairStatsBadges.vue'
import HistoryTable from './rosette_compare_history/HistoryTable.vue'

import {
  useRosetteCompareState,
  useRosetteCompareStats,
  useRosetteComparePresets,
  useRosetteCompareSparklines,
  useRosetteCompareActions
} from './rosette_compare_history/composables'

// =============================================================================
// PROPS
// =============================================================================

const props = defineProps<{
  lane?: string
  jobId?: string | null
}>()

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
  entries,
  comparePresets,
  presetCompareA,
  presetCompareB,
  lane,
  effectiveJobId
} = useRosetteCompareState(
  () => props.lane,
  () => props.jobId
)

// Stats
const { avgAdded, avgRemoved, avgUnchanged } = useRosetteCompareStats(entries)

// Presets
const {
  presetBuckets,
  presetCompareAEntries,
  presetCompareBEntries,
  pairStats
} = useRosetteComparePresets(entries, presetCompareA, presetCompareB)

// Sparklines
const {
  sparkWidth,
  sparkHeight,
  addedSparkPath,
  removedSparkPath,
  presetSparklines,
  pairAddedOverlay,
  pairRemovedOverlay
} = useRosetteCompareSparklines(
  entries,
  presetBuckets,
  presetCompareAEntries,
  presetCompareBEntries
)

// Actions
const { refresh, exportCsv } = useRosetteCompareActions(
  entries,
  lane,
  effectiveJobId
)

// =============================================================================
// LIFECYCLE & WATCHERS
// =============================================================================

onMounted(refresh)

watch(() => effectiveJobId.value, refresh)
watch(() => lane.value, refresh)
</script>
