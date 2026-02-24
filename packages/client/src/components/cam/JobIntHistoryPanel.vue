<!-- File: client/src/components/cam/JobIntHistoryPanel.vue -->
<!-- NEW – Job Intelligence history panel with stats header, filters, and pagination -->

<template>
  <div class="flex flex-col h-full text-xs gap-3">
    <header class="flex items-center justify-between">
      <div>
        <h3 class="text-xs font-semibold">
          Job Intelligence History
        </h3>
        <p class="text-[11px] text-gray-500">
          Recent pipeline runs with sim time, energy, and deviation.
        </p>
      </div>

      <button
        type="button"
        class="px-2 py-1 rounded border border-slate-300 text-[11px] hover:bg-slate-50"
        @click="reload"
      >
        Reload
      </button>
    </header>

    <!-- Quick Stats Header -->
    <section class="border rounded-lg p-2 bg-white flex flex-col gap-1 text-[11px]">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <span class="text-gray-500">Current page:</span>
          <span class="font-mono">{{ items.length }}</span>
          <span class="text-gray-400">jobs</span>
        </div>

        <div class="flex items-center gap-2">
          <span
            class="px-2 py-0.5 rounded-full border text-[10px] border-emerald-200 bg-emerald-50 text-emerald-700"
          >
            Helical:
            <span class="font-mono">
              {{ helicalCount }} ({{ helicalPct.toFixed(0) }}%)
            </span>
          </span>
          <span
            class="px-2 py-0.5 rounded-full border text-[10px] border-slate-200 bg-slate-50 text-slate-700"
          >
            Non-helical:
            <span class="font-mono">
              {{ nonHelicalCount }} ({{ nonHelicalPct.toFixed(0) }}%)
            </span>
          </span>
        </div>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1">
            <span class="text-gray-500">Avg time:</span>
            <span class="font-mono">
              {{ avgTimeLabel }}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <span class="text-gray-500">Avg max dev:</span>
            <span class="font-mono">
              <span v-if="avgMaxDevPct != null">
                {{ avgMaxDevPct.toFixed(1) }}%
              </span>
              <span v-else>—</span>
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Filters -->
    <section class="border rounded-lg p-2 bg-slate-50 flex flex-col gap-2">
      <div class="grid grid-cols-3 gap-2 text-[11px]">
        <label class="flex flex-col gap-1">
          <span>Machine</span>
          <input
            v-model="filters.machine_id"
            type="text"
            class="border rounded px-2 py-1"
            placeholder="haas_vf2, shopbot, ..."
          >
        </label>

        <label class="flex flex-col gap-1">
          <span>Post</span>
          <input
            v-model="filters.post_id"
            type="text"
            class="border rounded px-2 py-1"
            placeholder="haas_ngc, grbl, ..."
          >
        </label>

        <div class="flex flex-col gap-1 mt-1">
          <label class="flex items-center gap-2">
            <input
              v-model="filters.helical_only"
              type="checkbox"
              class="w-3 h-3"
            >
            <span>Helical only</span>
          </label>

          <label class="flex items-center gap-2">
            <input
              v-model="filters.favorites_only"
              type="checkbox"
              class="w-3 h-3"
            >
            <span>⭐ Favorites only</span>
          </label>
        </div>
      </div>

      <div class="flex items-center gap-2 text-[11px]">
        <label class="flex items-center gap-2">
          <input
            v-model="filters.favorites_only"
            type="checkbox"
            class="w-3 h-3"
          >
          <span>⭐ Favorites only</span>
        </label>
      </div>

      <div class="flex items-center justify-between mt-1 text-[11px]">
        <span class="text-gray-500">
          Total:
          <span class="font-mono">{{ total }}</span>
        </span>

        <div class="flex items-center gap-2">
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-300 hover:bg-slate-100"
            @click="applyFilters"
          >
            Apply
          </button>
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-300 hover:bg-slate-100"
            @click="resetFilters"
          >
            Reset
          </button>
        </div>
      </div>
    </section>

    <!-- Table -->
    <section class="flex-1 border rounded-lg overflow-hidden flex flex-col">
      <div class="border-b bg-slate-50 px-2 py-1 text-[11px] font-semibold flex">
        <div class="w-[22%]">
          Job
        </div>
        <div class="w-[12%]">
          Machine
        </div>
        <div class="w-[12%]">
          Post
        </div>
        <div class="w-[9%] text-center">
          Helical
        </div>
        <div class="w-[12%] text-right">
          Time
        </div>
        <div class="w-[9%] text-right">
          Issues
        </div>
        <div class="w-[9%] text-right">
          Max dev
        </div>
        <div class="w-[15%] text-right pr-1">
          Actions
        </div>
      </div>

      <div class="flex-1 overflow-auto">
        <div
          v-for="entry in items"
          :key="entry.run_id"
          class="px-2 py-1 text-[11px] flex items-center border-b hover:bg-slate-50"
        >
          <div class="w-[22%] truncate">
            <div class="flex items-center gap-1">
              <button
                type="button"
                class="text-[12px] leading-none"
                :title="entry.favorite ? 'Unmark favorite' : 'Mark as favorite'"
                @click.stop="toggleFavorite(entry)"
              >
                <span v-if="entry.favorite">⭐</span>
                <span v-else>☆</span>
              </button>
              <div
                class="truncate flex-1 cursor-pointer"
                @click="selectEntry(entry)"
              >
                <div class="font-semibold">
                  {{ entry.job_name || "(unnamed job)" }}
                </div>
                <div class="text-[10px] text-gray-500">
                  {{ entry.run_id }}
                </div>
              </div>
            </div>
          </div>

          <div class="w-[12%] truncate">
            {{ entry.machine_id || "—" }}
          </div>

          <div class="w-[12%] truncate">
            {{ entry.post_id || "—" }}
          </div>

          <div class="w-[9%] text-center">
            <span
              :class="[
                'px-2 py-0.5 rounded-full text-[10px]',
                entry.use_helical
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-slate-50 text-slate-500 border border-slate-200',
              ]"
            >
              {{ entry.use_helical ? "Yes" : "No" }}
            </span>
          </div>

          <div class="w-[12%] text-right font-mono">
            {{ formatTime(entry.sim_time_s) }}
          </div>

          <div class="w-[9%] text-right font-mono">
            {{ entry.sim_issue_count ?? 0 }}
          </div>

          <div class="w-[9%] text-right font-mono">
            <span v-if="entry.sim_max_dev_pct != null">
              {{ entry.sim_max_dev_pct.toFixed(1) }}%
            </span>
            <span v-else>—</span>
          </div>

          <div class="w-[15%] text-right pr-1">
            <button
              type="button"
              class="px-2 py-1 rounded border border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100 text-[10px]"
              title="Clone as preset (B19)"
              @click.stop="openCloneModal(entry)"
            >
              📋 Clone
            </button>
          </div>
        </div>

        <div
          v-if="!loading && items.length === 0"
          class="px-3 py-4 text-[11px] text-gray-400"
        >
          No jobs found. Run a pipeline or relax the filters.
        </div>
      </div>

      <div class="border-t px-2 py-1 flex items-center justify-between text-[11px] bg-slate-50">
        <span class="text-gray-500">
          Showing
          <span class="font-mono">{{ items.length }}</span>
          of
          <span class="font-mono">{{ total }}</span>
        </span>

        <div class="flex items-center gap-2">
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-300 hover:bg-slate-100 disabled:opacity-40"
            :disabled="offset === 0 || loading"
            @click="prevPage"
          >
            Prev
          </button>
          <button
            type="button"
            class="px-2 py-1 rounded border border-slate-300 hover:bg-slate-100 disabled:opacity-40"
            :disabled="offset + limit >= total || loading"
            @click="nextPage"
          >
            Next
          </button>
        </div>
      </div>
    </section>

    <p
      v-if="errorMessage"
      class="text-[11px] text-rose-600"
    >
      {{ errorMessage }}
    </p>

    <!-- Clone as Preset Modal -->
    <div
      v-if="showCloneModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
      @click.self="closeCloneModal"
    >
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto">
        <div class="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between">
          <h3 class="text-sm font-semibold">
            📋 Clone Job as Preset (B19)
          </h3>
          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 text-lg leading-none"
            @click="closeCloneModal"
          >
            ✕
          </button>
        </div>

        <div class="p-4">
          <CloneToPresetForm
            v-if="selectedEntry"
            :entry="selectedEntry"
            :form="cloneForm"
            :cloning="cloning"
            :success="cloneSuccess"
            :error="cloneError"
            @close="closeCloneModal"
            @execute="executeClone"
            @update:form="Object.assign(cloneForm, $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import {
  useJobIntHistoryState,
  useJobIntHistoryStats,
  useJobIntHistoryLoad,
  useJobIntHistoryActions,
  useJobIntHistoryClone,
  useJobIntHistoryHelpers
} from './composables'
import { CloneToPresetForm } from './job-int-history'

// State
const {
  items,
  total,
  loading,
  errorMessage,
  filters,
  limit,
  offset,
  showCloneModal,
  selectedEntry,
  cloning,
  cloneSuccess,
  cloneError,
  cloneForm
} = useJobIntHistoryState()

// Stats
const {
  helicalCount,
  nonHelicalCount,
  helicalPct,
  nonHelicalPct,
  avgTimeLabel,
  avgMaxDevPct
} = useJobIntHistoryStats(items)

// Load/pagination
const { load, reload, applyFilters, resetFilters, prevPage, nextPage } = useJobIntHistoryLoad(
  items,
  total,
  loading,
  errorMessage,
  filters,
  limit,
  offset
)

// Entry actions
const { selectEntry, toggleFavorite } = useJobIntHistoryActions(errorMessage)

// Clone modal
const { openCloneModal, closeCloneModal, executeClone } = useJobIntHistoryClone(
  showCloneModal,
  selectedEntry,
  cloning,
  cloneSuccess,
  cloneError,
  cloneForm
)

// Helpers
const { formatTime } = useJobIntHistoryHelpers()

onMounted(load)
</script>
