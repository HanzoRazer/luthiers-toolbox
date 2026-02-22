<template>
  <div class="p-4 space-y-3">
    <header class="flex flex-col gap-1">
      <h2 class="text-lg font-semibold">
        Relief Risk Timeline
      </h2>
      <p class="text-xs text-gray-500">
        Filter recorded jobs by preset personality to study how Safe / Standard / Aggressive
        behave on real parts.
      </p>
    </header>

    <!-- Filter bar -->
    <section
      class="flex flex-wrap items-center gap-3 text-xs border rounded px-3 py-2 bg-white"
    >
      <div class="flex items-center gap-2">
        <span class="font-semibold text-gray-700">Preset:</span>
        <select
          v-model="presetFilter"
          class="border rounded px-2 py-1 text-xs"
        >
          <option value="Any">
            Any
          </option>
          <option value="Safe">
            Safe
          </option>
          <option value="Standard">
            Standard
          </option>
          <option value="Aggressive">
            Aggressive
          </option>
          <option value="Custom">
            Custom
          </option>
        </select>
      </div>

      <div class="flex items-center gap-2">
        <span class="font-semibold text-gray-700">Pipeline:</span>
        <select
          v-model="pipelineFilter"
          class="border rounded px-2 py-1 text-xs"
        >
          <option value="Any">
            Any
          </option>
          <option value="artstudio_relief_v16">
            Art Studio Relief
          </option>
          <option value="relief_kernel_lab">
            Relief Kernel Lab
          </option>
        </select>
      </div>

      <!-- Compare toggle -->
      <label class="flex items-center gap-2 ml-2">
        <input
          v-model="comparePrev"
          type="checkbox"
        >
        <span>Compare with previous window</span>
      </label>

      <button
        v-if="comparePrev"
        type="button"
        class="text-[11px] px-2 py-1 border rounded bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50"
        :disabled="exporting"
        @click="exportCompareCsv"
      >
        {{ exporting ? "Exporting…" : "Export Compare CSV" }}
      </button>

      <button
        type="button"
        class="ml-auto text-[11px] px-2 py-1 border rounded bg-gray-50 hover:bg-gray-100"
        @click="reload"
      >
        Reload
      </button>
    </section>

    <!-- Summary bar (preset scorecard) -->
    <section
      class="text-xs border rounded px-3 py-2 bg-slate-50 flex flex-wrap items-center gap-3"
    >
      <div>
        <span class="font-semibold text-gray-700">Preset view:</span>
        <span class="ml-1">
          <span v-if="presetFilter === 'Any'">Mixed presets</span>
          <span v-else>{{ presetFilter }}</span>
        </span>
      </div>

      <div>
        <span class="font-semibold text-gray-700">Jobs:</span>
        <span class="ml-1">{{ summary.jobsCount }}</span>
      </div>

      <div>
        <span class="font-semibold text-gray-700">Avg risk:</span>
        <span class="ml-1">
          {{ summary.jobsCount ? summary.avgRisk.toFixed(2) : "—" }}
        </span>
      </div>

      <div>
        <span class="font-semibold text-gray-700">Critical incidents:</span>
        <span class="ml-1">
          {{ summary.totalCritical }}
        </span>
      </div>
    </section>

    <!-- Trend sparkline over filtered jobs -->
    <section>
      <CamRiskPresetTrend :jobs="filteredJobs" />
    </section>

    <!-- Comparison against previous window -->
    <section v-if="comparePrev">
      <CamRiskCompareBars
        :curr="summary"
        :prev="summaryPrev"
      />
      <p class="mt-1 text-[10px] text-gray-500">
        Previous window is auto-derived as the same length immediately before the current date range.
        If no date range is set, comparison is disabled.
      </p>
    </section>

    <!-- Jobs list -->
    <section>
      <div
        v-if="loading"
        class="text-xs text-gray-500"
      >
        Loading jobs…
      </div>
      <div
        v-else-if="filteredJobs.length === 0"
        class="text-xs text-gray-500"
      >
        No jobs match the current filters.
      </div>
      <CamRiskJobList
        v-else
        :jobs="filteredJobs"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * RiskTimelineRelief - Relief Risk Timeline View
 *
 * Filter recorded jobs by preset personality to study how Safe / Standard / Aggressive
 * behave on real parts.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import CamRiskJobList from '@/components/cam/CamRiskJobList.vue'
import CamRiskPresetTrend from '@/components/cam/CamRiskPresetTrend.vue'
import CamRiskCompareBars from '@/components/cam/CamRiskCompareBars.vue'
import {
  useRiskTimelineState,
  useRiskTimelineFiltering,
  useRiskTimelineActions
} from './composables'

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
  jobs,
  loading,
  exporting,
  presetFilter,
  pipelineFilter,
  comparePrev
} = useRiskTimelineState()

// Filtering
const { filteredJobs, filteredJobsPrev, summary, summaryPrev } = useRiskTimelineFiltering(
  jobs,
  presetFilter,
  pipelineFilter
)

// Actions
const { reload, exportCompareCsv } = useRiskTimelineActions(
  jobs,
  loading,
  exporting,
  presetFilter,
  pipelineFilter,
  filteredJobs,
  filteredJobsPrev
)
</script>
