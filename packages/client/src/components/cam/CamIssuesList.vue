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
import { computed, ref, watch } from "vue";
import type { SimIssue } from "@/types/cam";

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

/**
 * Severity filter state.
 */
const severityOptions = ["info", "low", "medium", "high", "critical"] as const;
type SeverityOption = (typeof severityOptions)[number];

const activeSeverities = ref<SeverityOption[]>([...severityOptions]);

// Toggle a single severity on/off
function toggleSeverity(s: SeverityOption) {
  const current = new Set(activeSeverities.value);
  if (current.has(s)) current.delete(s);
  else current.add(s);
  // Avoid empty filter: if user turns everything off, reset to all
  activeSeverities.value =
    current.size === 0 ? [...severityOptions] : (Array.from(current) as SeverityOption[]);
}

// Quick helpers
function selectAllSeverities() {
  activeSeverities.value = [...severityOptions];
}

function selectHighCriticalOnly() {
  activeSeverities.value = ["high", "critical"];
}

const activeSeveritiesSet = computed(
  () => new Set<SeverityOption>(activeSeverities.value)
);

/**
 * Severity metrics: counts of each severity in the full issues list.
 */
const severityCounts = computed<Record<SeverityOption, number>>(() => {
  const counts: Record<SeverityOption, number> = {
    info: 0,
    low: 0,
    medium: 0,
    high: 0,
    critical: 0,
  };
  for (const iss of props.issues) {
    const sev = (iss.severity || "medium") as SeverityOption;
    if (sev in counts) {
      counts[sev] += 1;
    }
  }
  return counts;
});

/**
 * Risk analytics:
 * - riskScore: weighted severity sum
 * - totalExtraTimeSec: sum of issue.extra_time_s (if numeric)
 */
const riskScore = computed(() => {
  const c = severityCounts.value;
  // Simple heuristic weights – you can tune these
  return (
    c.critical * 5 +
    c.high * 3 +
    c.medium * 2 +
    c.low * 1 +
    c.info * 0.5
  );
});

const totalExtraTimeSec = computed<number>(() => {
  let total = 0;
  for (const iss of props.issues as (SimIssue & { extra_time_s?: number })[]) {
    const extra = typeof iss.extra_time_s === "number" ? iss.extra_time_s : 0;
    total += extra;
  }
  return total;
});

function formatDuration(sec: number): string {
  if (!sec || sec <= 0) return "0 s";
  const whole = Math.round(sec);
  const minutes = Math.floor(whole / 60);
  const seconds = whole % 60;
  if (minutes === 0) return `${seconds} s`;
  return `${minutes} min ${seconds} s`;
}

/**
 * Filtered index list: indices into props.issues that pass current filter.
 */
const filteredIndices = computed<number[]>(() => {
  const indices: number[] = [];
  const set = activeSeveritiesSet.value;
  props.issues.forEach((iss, idx) => {
    const sev = (iss.severity || "medium") as SeverityOption;
    if (set.has(sev)) indices.push(idx);
  });
  return indices;
});

const count = computed(() => filteredIndices.value.length);
const hasIssues = computed(() => count.value > 0);

/**
 * Position of current selection within the filtered indices.
 */
const filteredPosition = computed<number | null>(() => {
  if (!hasIssues.value) return null;
  const idx = selectedIndexLocal.value;
  if (idx == null) return null;
  const list = filteredIndices.value;
  const pos = list.indexOf(idx);
  return pos === -1 ? null : pos;
});

const canPrev = computed(() => {
  if (!hasIssues.value) return false;
  const pos = filteredPosition.value;
  if (pos == null) return false;
  return pos > 0;
});

const canNext = computed(() => {
  if (!hasIssues.value) return false;
  const pos = filteredPosition.value;
  if (pos == null) return false;
  return pos < count.value - 1;
});

const currentLabel = computed(() => {
  if (!hasIssues.value) return "0 / 0";
  const pos = filteredPosition.value ?? 0;
  return `${pos + 1} / ${count.value}`;
});

function severityChipClass(sev: SimIssue["severity"]): string {
  const base =
    "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold";
  switch (sev) {
    case "critical":
    case "high":
      return base + " bg-red-500 text-white";
    case "medium":
      return base + " bg-orange-500 text-white";
    case "low":
      return base + " bg-yellow-400 text-black";
    case "info":
    default:
      return base + " bg-gray-300 text-gray-800";
  }
}

function severityLabelShort(s: SeverityOption): string {
  switch (s) {
    case "critical":
      return "C";
    case "high":
      return "H";
    case "medium":
      return "M";
    case "low":
      return "L";
    case "info":
    default:
      return "I";
  }
}

/**
 * Helper: select a given index into props.issues,
 * optionally emitting a focus-request event.
 */
function selectIndex(idx: number | null, emitFocus: boolean) {
  if (idx == null || idx < 0 || idx >= props.issues.length) {
    selectedIndexLocal.value = null;
    return;
  }
  const issue = props.issues[idx];
  selectedIndexLocal.value = idx;
  if (emitFocus && issue) {
    emit("focus-request", { index: idx, issue });
  }
}

// Click from list item
function handleClick(idx: number, issue: SimIssue) {
  selectIndex(idx, true);
}

// Prev/Next scrubber
function jumpPrev() {
  if (!canPrev.value) return;
  const list = filteredIndices.value;
  const pos = filteredPosition.value;
  if (pos == null || pos <= 0) return;
  const nextIdx = list[pos - 1];
  selectIndex(nextIdx, true);
}

function jumpNext() {
  if (!canNext.value) return;
  const list = filteredIndices.value;
  const pos = filteredPosition.value;
  if (pos == null || pos >= list.length - 1) return;
  const nextIdx = list[pos + 1];
  selectIndex(nextIdx, true);
}

/**
 * If the filter changes and the current selection is outside of the
 * filtered set, gently move the selection to the first filtered item.
 */
watch(
  () => activeSeverities.value,
  () => {
    if (!hasIssues.value) {
      selectedIndexLocal.value = null;
      return;
    }
    const pos = filteredPosition.value;
    if (pos == null) {
      const firstIdx = filteredIndices.value[0];
      selectIndex(firstIdx, false);
    }
  }
);

/**
 * Export helpers: JSON + CSV
 */
const analyticsJson = computed(() => {
  return JSON.stringify(
    {
      total_issues: props.issues.length,
      severity_counts: severityCounts.value,
      risk_score: riskScore.value,
      total_extra_time_s: totalExtraTimeSec.value,
      total_extra_time_human: formatDuration(totalExtraTimeSec.value),
    },
    null,
    2
  );
});

const analyticsCsv = computed(() => {
  // Simple per-issue CSV
  const header = [
    "index",
    "type",
    "severity",
    "x",
    "y",
    "z",
    "extra_time_s",
    "note",
  ];
  const rows: string[] = [];
  rows.push(header.join(","));

  (props.issues as (SimIssue & { extra_time_s?: number })[]).forEach(
    (iss, idx) => {
      const extra =
        typeof iss.extra_time_s === "number" ? iss.extra_time_s : "";
      const row = [
        idx.toString(),
        (iss.type || "").replace(/,/g, " "),
        (iss.severity || "").toString(),
        iss.x.toFixed(4),
        iss.y.toFixed(4),
        iss.z != null ? iss.z.toFixed(4) : "",
        extra.toString(),
        (iss.note || "").replace(/[\r\n,]/g, " "),
      ];
      rows.push(row.join(","));
    }
  );

  return rows.join("\n");
});

function downloadBlob(content: string, mime: string, filename: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function downloadJson() {
  if (!props.issues.length) return;
  downloadBlob(analyticsJson.value, "application/json", "cam_issues_analytics.json");
}

function downloadCsv() {
  if (!props.issues.length) return;
  downloadBlob(analyticsCsv.value, "text/csv", "cam_issues_analytics.csv");
}
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
        <template v-for="s in severityOptions" :key="s">
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
        @click="handleClick(origIdx, issues[origIdx])"
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
