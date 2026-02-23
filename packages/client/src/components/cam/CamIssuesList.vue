<!--
  CamIssuesList.vue - Phase 17 Complete Integration
  
  Progressive Enhancement Phases:
  - Phase 17.0: Issues HUD + Camera Jump (click-to-focus)
  - Phase 17.1: Issue Scrubber (Prev/Next navigation)
  - Phase 17.2: Severity Filter (info/low/medium/high/critical toggles)
  - Phase 17.3: Severity Metrics Bar (counts per severity)
  - Phase 17.4: Time-Cost + Risk Score (weighted severity calculation)
  - Phase 17.5: Risk Analytics Footer (JSON/CSV export)
  
  Usage:
  <CamIssuesList
    :issues="simIssues"
    :selectedIndex="selectedIssueIndex"
    @update:selectedIndex="selectedIssueIndex = $event"
    @focus-request="handleFocusRequest"
  />
-->
<script setup lang="ts">
import { computed, ref, toRef } from "vue";
import type { SimIssue } from "@/types/cam";
import {
  useSeverityFilter,
  useIssuesAnalytics,
  useIssuesScrubber,
  SEVERITY_OPTIONS,
} from "./composables";

const props = defineProps<{
  issues: SimIssue[];
  title?: string;
  selectedIndex?: number | null;
}>();

const emit = defineEmits<{
  (e: "update:selectedIndex", value: number | null): void;
  (e: "focus-request", payload: { index: number; issue: SimIssue }): void;
}>();

const selectedIndexLocal = computed({
  get: () => props.selectedIndex ?? null,
  set: (v: number | null) => emit("update:selectedIndex", v),
});

// Composables
const issuesRef = toRef(props, "issues");

const {
  activeSeverities,
  activeSeveritiesSet,
  toggleSeverity,
  selectAllSeverities,
  selectHighCriticalOnly,
  severityChipClass,
  severityLabelShort,
} = useSeverityFilter();

const {
  severityCounts,
  riskScore,
  totalExtraTimeSec,
  formatDuration,
  downloadJson,
  downloadCsv,
} = useIssuesAnalytics(issuesRef);

const {
  filteredIndices,
  hasIssues,
  canPrev,
  canNext,
  currentLabel,
  handleClick,
  jumpPrev,
  jumpNext,
} = useIssuesScrubber({
  issues: issuesRef,
  selectedIndex: selectedIndexLocal,
  activeSeveritiesSet,
  activeSeverities,
  onFocusRequest: (payload) => emit("focus-request", payload),
});

// Expose SEVERITY_OPTIONS for template
const severityOptions = SEVERITY_OPTIONS;
</script>

<template>
  <div class="border rounded p-3 bg-gray-50 text-xs space-y-2">
    <!-- Header: title + scrubber -->
    <div class="flex items-center justify-between mb-1">
      <span class="font-semibold">{{ title || "Issues" }}</span>
      <div class="flex items-center gap-2 text-[10px] text-gray-500">
        <button
          type="button"
          class="border rounded px-1.5 py-0.5"
          :class="[
            'flex items-center gap-1',
            canPrev ? 'bg-white hover:bg-gray-100 cursor-pointer' : 'bg-gray-100 cursor-not-allowed text-gray-400'
          ]"
          :disabled="!canPrev"
          @click="jumpPrev"
        >
          ‹
          <span>Prev</span>
        </button>
        <span class="tabular-nums">{{ currentLabel }}</span>
        <button
          type="button"
          class="border rounded px-1.5 py-0.5"
          :class="[
            'flex items-center gap-1',
            canNext ? 'bg-white hover:bg-gray-100 cursor-pointer' : 'bg-gray-100 cursor-not-allowed text-gray-400'
          ]"
          :disabled="!canNext"
          @click="jumpNext"
        >
          <span>Next</span>
          ›
        </button>
      </div>
    </div>

    <!-- Metrics bar: counts per severity -->
    <div class="flex items-center justify-between text-[10px] text-gray-600 mb-1">
      <div class="flex flex-wrap gap-1.5">
        <template
          v-for="s in severityOptions"
          :key="s"
        >
          <span
            v-if="(severityCounts as Record<string, number>)[s]"
            class="inline-flex items-center"
          >
            <span
              class="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 border tabular-nums"
              :class="[
                activeSeveritiesSet.has(s as any)
                  ? 'bg-gray-900 text-white border-gray-900'
                  : 'bg-white text-gray-700 border-gray-300'
              ]"
            >
              <span>{{ severityLabelShort(s as any) }}:</span>
              <span>{{ (severityCounts as Record<string, number>)[s] }}</span>
            </span>
          </span>
        </template>
      </div>
      <span
        v-if="issues.length"
        class="text-[10px] text-gray-500"
      >
        Total: {{ issues.length }}
      </span>
    </div>

    <!-- Severity filter row -->
    <div class="flex items-center justify-between text-[10px] text-gray-600 mb-1">
      <div class="flex flex-wrap gap-1">
        <button
          type="button"
          class="border rounded px-1.5 py-0.5"
          :class="[
            activeSeverities.length === severityOptions.length
              ? 'bg-gray-800 text-white'
              : 'bg-white hover:bg-gray-100'
          ]"
          @click="selectAllSeverities"
        >
          All
        </button>
        <button
          type="button"
          class="border rounded px-1.5 py-0.5"
          :class="[
            activeSeveritiesSet.has('high') && activeSeveritiesSet.has('critical') &&
              activeSeverities.length === 2
              ? 'bg-red-600 text-white'
              : 'bg-white hover:bg-gray-100'
          ]"
          @click="selectHighCriticalOnly"
        >
          High+Crit
        </button>
      </div>
      <div class="flex flex-wrap gap-1">
        <button
          v-for="s in severityOptions"
          :key="s"
          type="button"
          class="border rounded px-1.5 py-0.5 capitalize"
          :class="[
            activeSeveritiesSet.has(s as any)
              ? 'bg-gray-700 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          ]"
          @click="toggleSeverity(s as any)"
        >
          {{ s }}
        </button>
      </div>
    </div>

    <!-- List content -->
    <div
      v-if="!issues.length"
      class="text-gray-500 text-[11px]"
    >
      No issues reported.
    </div>

    <div
      v-else-if="!filteredIndices.length"
      class="text-gray-500 text-[11px]"
    >
      No issues match the current severity filters.
    </div>

    <ul
      v-else
      class="space-y-1 max-h-64 overflow-auto"
    >
      <li
        v-for="origIdx in filteredIndices"
        :key="origIdx"
        class="border rounded px-2 py-1 bg-white cursor-pointer flex justify-between items-center"
        :class="{
          'ring-1 ring-blue-500': selectedIndexLocal === origIdx,
        }"
        @click="handleClick(origIdx)"
      >
        <div class="flex flex-col">
          <span>
            <b>{{ issues[origIdx].type }}</b>
            <span class="ml-1 text-gray-500">
              ({{ issues[origIdx].severity }})
            </span>
          </span>
          <span class="text-[10px] text-gray-500">
            X: {{ issues[origIdx].x.toFixed(2) }} Y: {{ issues[origIdx].y.toFixed(2) }}
            <span v-if="issues[origIdx].z != null">
              Z: {{ issues[origIdx].z!.toFixed(2) }}
            </span>
          </span>
          <span
            v-if="issues[origIdx].note"
            class="text-[10px] text-gray-600"
          >
            {{ issues[origIdx].note }}
          </span>
        </div>
        <span :class="severityChipClass(issues[origIdx].severity)">
          {{ issues[origIdx].severity }}
        </span>
      </li>
    </ul>

    <!-- Risk analytics footer -->
    <div
      v-if="issues.length"
      class="pt-2 border-t mt-2 text-[10px] text-gray-600 flex flex-wrap items-center justify-between gap-2"
    >
      <div class="flex flex-col">
        <span>
          Risk score:
          <span class="font-semibold">{{ riskScore.toFixed(1) }}</span>
        </span>
        <span>
          Est. extra time:
          <span class="font-semibold">{{ formatDuration(totalExtraTimeSec) }}</span>
        </span>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="border rounded px-2 py-0.5 bg-white hover:bg-gray-100"
          @click="downloadJson"
        >
          JSON
        </button>
        <button
          type="button"
          class="border rounded px-2 py-0.5 bg-white hover:bg-gray-100"
          @click="downloadCsv"
        >
          CSV
        </button>
      </div>
    </div>
  </div>
</template>
