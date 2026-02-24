<template>
  <div class="p-4 flex gap-4">
    <!-- Main content area -->
    <div class="flex-1 flex flex-col gap-4">
      <!-- Header -->
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 class="text-base font-semibold text-gray-900">
            Art Studio · Rosette Compare
          </h1>
          <p class="text-xs text-gray-600 max-w-xl">
            Select two saved rosette jobs (A &amp; B), then compare geometry and key parameters.
            This is the first Compare Mode hook — later we can add overlay coloring and analytics.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
            @click="reloadJobs"
          >
            Reload jobs
          </button>
          <button
            v-if="selectedJobIdA && selectedJobIdB"
            class="px-3 py-1 rounded border text-[11px] text-blue-700 hover:bg-blue-50"
            @click="toggleHistorySidebar"
          >
            {{ showHistory ? 'Hide' : 'Show' }} History
          </button>
        </div>
      </div>

      <!-- Job selectors -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div class="border rounded-lg bg-white shadow-sm p-3 text-[11px] text-gray-800">
          <h2 class="text-[12px] font-semibold mb-2 text-gray-900">
            Baseline (A)
          </h2>
          <select
            v-model="selectedJobIdA"
            class="w-full px-2 py-1 border rounded text-[11px]"
          >
            <option value="">
              (select a job)
            </option>
            <option
              v-for="job in jobs"
              :key="job.job_id"
              :value="job.job_id"
            >
              {{ job.name || job.job_id }} · {{ job.preview.preset || 'no preset' }}
            </option>
          </select>
          <p class="text-[10px] text-gray-500 mt-1">
            Pick the baseline rosette you want to compare from your recent jobs.
          </p>
        </div>

        <div class="border rounded-lg bg-white shadow-sm p-3 text-[11px] text-gray-800">
          <h2 class="text-[12px] font-semibold mb-2 text-gray-900">
            Variant (B)
          </h2>
          <select
            v-model="selectedJobIdB"
            class="w-full px-2 py-1 border rounded text-[11px]"
          >
            <option value="">
              (select a job)
            </option>
            <option
              v-for="job in jobs"
              :key="job.job_id"
              :value="job.job_id"
            >
              {{ job.name || job.job_id }} · {{ job.preview.preset || 'no preset' }}
            </option>
          </select>
          <p class="text-[10px] text-gray-500 mt-1">
            Pick the variant rosette to compare against baseline.
          </p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <button
          class="px-3 py-1 rounded bg-indigo-600 text-white text-[11px] hover:bg-indigo-700 disabled:opacity-50"
          :disabled="compareLoading || !selectedJobIdA || !selectedJobIdB"
          @click="runCompare"
        >
          {{ compareLoading ? 'Comparing…' : 'Compare A ↔ B' }}
        </button>
        <!-- Phase 27.2: Save to Risk Timeline button -->
        <button
          v-if="compareResult"
          class="px-3 py-1 rounded bg-blue-600 text-white text-[11px] hover:bg-blue-700 disabled:opacity-50"
          :disabled="saveSnapshotLoading"
          @click="saveSnapshot"
        >
          {{ saveSnapshotLoading ? 'Saving…' : '💾 Save to Risk Timeline' }}
        </button>
        <p
          v-if="statusMessage"
          class="text-[10px]"
          :class="statusClass"
        >
          {{ statusMessage }}
        </p>
      </div>

      <!-- Diff summary -->
      <CompareDiffSummary
        v-if="compareResult"
        :diff-summary="compareResult.diff_summary"
      />

      <!-- Dual canvases with Phase 27.1 coloring -->
      <div
        v-if="compareResult"
        class="grid grid-cols-1 md:grid-cols-2 gap-3"
      >
        <!-- Baseline (A) Canvas -->
        <div class="border rounded-lg bg-white shadow-sm p-3 flex flex-col gap-2 relative">
          <!-- Legend -->
          <div class="absolute top-2 right-2 bg-white/90 p-2 rounded shadow text-[10px] z-10 border border-gray-200">
            <div class="flex items-center gap-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#111827;"
              />
              <span>Unchanged</span>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#10b981;"
              />
              <span>Added in A</span>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#ef4444;"
              />
              <span>Removed from A</span>
            </div>
          </div>
        
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-[12px] font-semibold text-gray-900">
                Baseline (A)
              </h2>
              <p class="text-[10px] text-gray-500">
                {{ compareResult.job_a.name || compareResult.job_a.job_id }} ·
                {{ compareResult.job_a.preset || 'no preset' }}
              </p>
            </div>
            <div class="text-[10px] font-mono text-gray-500">
              {{ compareResult.job_a.segments }} seg
            </div>
          </div>
          <div
            class="border rounded bg-gray-50 flex items-center justify-center"
            style="height: 260px;"
          >
            <svg
              v-if="compareResult.job_a.paths.length"
              :viewBox="viewBoxUnion"
              preserveAspectRatio="xMidYMid meet"
              class="w-full h-full"
            >
              <!-- Unchanged paths (common segment count) -->
              <polyline
                v-for="(path, idx) in unchangedPathsA"
                :key="'a_unchanged_' + idx"
                :points="polylinePoints(path.points)"
                fill="none"
                stroke="#111827"
                stroke-width="0.4"
              />
              <!-- Added paths (A has more segments than B) -->
              <polyline
                v-for="(path, idx) in addedPathsA"
                :key="'a_added_' + idx"
                :points="polylinePoints(path.points)"
                fill="none"
                stroke="#10b981"
                stroke-width="0.7"
              />
            </svg>
            <div
              v-else
              class="text-[10px] text-gray-500 italic"
            >
              No geometry for job A.
            </div>
          </div>
        </div>

        <!-- Variant (B) Canvas -->
        <div class="border rounded-lg bg-white shadow-sm p-3 flex flex-col gap-2 relative">
          <!-- Legend -->
          <div class="absolute top-2 right-2 bg-white/90 p-2 rounded shadow text-[10px] z-10 border border-gray-200">
            <div class="flex items-center gap-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#111827;"
              />
              <span>Unchanged</span>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#10b981;"
              />
              <span>Added in B</span>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#ef4444;"
              />
              <span>Removed from B</span>
            </div>
          </div>
        
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-[12px] font-semibold text-gray-900">
                Variant (B)
              </h2>
              <p class="text-[10px] text-gray-500">
                {{ compareResult.job_b.name || compareResult.job_b.job_id }} ·
                {{ compareResult.job_b.preset || 'no preset' }}
              </p>
            </div>
            <div class="text-[10px] font-mono text-gray-500">
              {{ compareResult.job_b.segments }} seg
            </div>
          </div>
          <div
            class="border rounded bg-gray-50 flex items-center justify-center"
            style="height: 260px;"
          >
            <svg
              v-if="compareResult.job_b.paths.length"
              :viewBox="viewBoxUnion"
              preserveAspectRatio="xMidYMid meet"
              class="w-full h-full"
            >
              <!-- Unchanged paths (common segment count) -->
              <polyline
                v-for="(path, idx) in unchangedPathsB"
                :key="'b_unchanged_' + idx"
                :points="polylinePoints(path.points)"
                fill="none"
                stroke="#111827"
                stroke-width="0.4"
              />
              <!-- Added paths (B has more segments than A) -->
              <polyline
                v-for="(path, idx) in addedPathsB"
                :key="'b_added_' + idx"
                :points="polylinePoints(path.points)"
                fill="none"
                stroke="#10b981"
                stroke-width="0.7"
              />
            </svg>
            <div
              v-else
              class="text-[10px] text-gray-500 italic"
            >
              No geometry for job B.
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="text-[11px] text-gray-500 italic"
      >
        Pick two jobs and run a comparison to see dual canvases and a diff summary.
      </div>
    </div> <!-- End main content area -->

    <!-- History Sidebar -->
    <CompareHistorySidebar
      v-if="showHistory && selectedJobIdA && selectedJobIdB"
      v-model:group-by-preset="groupByPreset"
      :history-snapshots="historySnapshots"
      :history-loading="historyLoading"
      :expanded-groups="expandedGroups"
      :grouped-snapshots="groupedSnapshots"
      :average-risk="averageRisk"
      :low-risk-count="lowRiskCount"
      :medium-risk-count="mediumRiskCount"
      :high-risk-count="highRiskCount"
      @toggle-group="toggleGroup"
      @export-csv="exportHistoryCSV"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import CompareDiffSummary from './rosette_compare/CompareDiffSummary.vue'
import CompareHistorySidebar from './rosette_compare/CompareHistorySidebar.vue'
import {
  useRosetteCompareState,
  useRosetteCompareHelpers,
  useRosetteComparePaths,
  useRosetteCompareActions,
  useRosetteCompareHistory
} from './rosette_compare/composables'

const route = useRoute()

// State
const {
  jobs,
  jobsLoading,
  jobsError,
  selectedJobIdA,
  selectedJobIdB,
  compareResult,
  compareLoading,
  statusMessage,
  statusIsError,
  statusClass,
  saveSnapshotLoading,
  showHistory,
  historySnapshots,
  historyLoading,
  groupByPreset,
  expandedGroups
} = useRosetteCompareState()

// Helpers
const { setStatus } = useRosetteCompareHelpers(statusMessage, statusIsError)

// Paths
const {
  viewBoxUnion,
  unchangedPathsA,
  addedPathsA,
  unchangedPathsB,
  addedPathsB,
  polylinePoints
} = useRosetteComparePaths(compareResult)

// Actions
const { reloadJobs, runCompare, saveSnapshot } = useRosetteCompareActions(
  jobs,
  jobsLoading,
  jobsError,
  selectedJobIdA,
  selectedJobIdB,
  compareResult,
  compareLoading,
  saveSnapshotLoading,
  setStatus
)

// History
const {
  groupedSnapshots,
  averageRisk,
  lowRiskCount,
  mediumRiskCount,
  highRiskCount,
  toggleHistorySidebar,
  toggleGroup,
  exportHistoryCSV
} = useRosetteCompareHistory(
  selectedJobIdA,
  selectedJobIdB,
  showHistory,
  historySnapshots,
  historyLoading,
  expandedGroups,
  setStatus
)

// Lifecycle
onMounted(async () => {
  await reloadJobs()

  // Optional: pre-fill from query params
  const jobA = route.query.jobA as string | undefined
  const jobB = route.query.jobB as string | undefined
  if (jobA) selectedJobIdA.value = jobA
  if (jobB) selectedJobIdB.value = jobB
})
</script>
