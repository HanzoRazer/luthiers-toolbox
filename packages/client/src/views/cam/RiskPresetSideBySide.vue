<template>
  <div class="p-4 space-y-4">
    <div class="bg-white rounded shadow-sm p-4">
      <h2 class="text-lg font-semibold mb-2">
        Risk Preset A/B Comparison
      </h2>
      <p class="text-sm text-gray-600 mb-4">
        Compare two presets side-by-side in the same pipeline and date range.
      </p>

      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-3 mb-4 pb-3 border-b text-[11px]">
        <!-- Pipeline filter -->
        <label class="flex items-center gap-2">
          <span class="text-gray-700">Pipeline:</span>
          <select
            v-model="pipelineFilter"
            class="px-2 py-1 border rounded text-[11px] bg-white"
          >
            <option value="Any">Any</option>
            <option value="artstudio_relief_v16">Art Studio Relief</option>
            <option value="relief_kernel_lab">Relief Kernel Lab</option>
          </select>
        </label>

        <!-- Date range -->
        <label class="flex items-center gap-2">
          <span class="text-gray-700">From:</span>
          <input
            v-model="fromDate"
            type="date"
            class="px-2 py-1 border rounded text-[11px] bg-white"
          >
        </label>
        <label class="flex items-center gap-2">
          <span class="text-gray-700">To:</span>
          <input
            v-model="toDate"
            type="date"
            class="px-2 py-1 border rounded text-[11px] bg-white"
          >
        </label>

        <!-- Preset A -->
        <label class="flex items-center gap-2">
          <span class="text-gray-700">Preset A:</span>
          <select
            v-model="presetA"
            class="px-2 py-1 border rounded text-[11px] bg-white"
          >
            <option value="Safe">Safe</option>
            <option value="Standard">Standard</option>
            <option value="Aggressive">Aggressive</option>
            <option value="Custom">Custom</option>
          </select>
        </label>

        <!-- Preset B -->
        <label class="flex items-center gap-2">
          <span class="text-gray-700">Preset B:</span>
          <select
            v-model="presetB"
            class="px-2 py-1 border rounded text-[11px] bg-white"
          >
            <option value="Safe">Safe</option>
            <option value="Standard">Standard</option>
            <option value="Aggressive">Aggressive</option>
            <option value="Custom">Custom</option>
          </select>
        </label>

        <!-- Reload -->
        <button
          type="button"
          class="text-[11px] px-2 py-1 border rounded bg-gray-50 hover:bg-gray-100"
          @click="fetchJobs"
        >
          Reload
        </button>

        <!-- Export buttons -->
        <button
          type="button"
          class="text-[11px] px-2 py-1 border rounded bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50"
          :disabled="exporting"
          @click="exportCsv('A')"
        >
          Export A CSV
        </button>
        <button
          type="button"
          class="text-[11px] px-2 py-1 border rounded bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50"
          :disabled="exporting"
          @click="exportCsv('B')"
        >
          Export B CSV
        </button>
        <button
          type="button"
          class="text-[11px] px-2 py-1 border rounded bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50"
          :disabled="exporting"
          @click="exportCsv('Both')"
        >
          Export A+B CSV
        </button>
      </div>

      <!-- Summary cards -->
      <div class="grid grid-cols-2 gap-4 mb-4">
        <!-- Card A -->
        <div class="border rounded p-3 bg-blue-50">
          <div class="text-xs font-bold mb-1">
            Preset A: {{ presetA }}
          </div>
          <div class="text-xs text-gray-600">
            Jobs: {{ summaryA.jobsCount }}
          </div>
          <div class="text-xs text-gray-600">
            Avg Risk: {{ summaryA.avgRisk }}
          </div>
          <div class="text-xs text-gray-600">
            Critical: {{ summaryA.totalCritical }}
          </div>
        </div>

        <!-- Card B -->
        <div class="border rounded p-3 bg-green-50">
          <div class="text-xs font-bold mb-1">
            Preset B: {{ presetB }}
          </div>
          <div class="text-xs text-gray-600">
            Jobs: {{ summaryB.jobsCount }}
          </div>
          <div class="text-xs text-gray-600">
            Avg Risk: {{ summaryB.avgRisk }}
          </div>
          <div class="text-xs text-gray-600">
            Critical: {{ summaryB.totalCritical }}
          </div>
        </div>
      </div>

      <!-- Trend sparklines -->
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div class="border rounded p-2 bg-white">
          <div class="text-xs font-semibold mb-1">
            Preset A Trend
          </div>
          <CamRiskPresetTrend :jobs="jobsA" />
        </div>
        <div class="border rounded p-2 bg-white">
          <div class="text-xs font-semibold mb-1">
            Preset B Trend
          </div>
          <CamRiskPresetTrend :jobs="jobsB" />
        </div>
      </div>

      <!-- Evolution Trendline (Phase 26.6) -->
      <section class="mb-4">
        <CamPresetEvolutionTrend
          :jobs-a="jobsA"
          :jobs-b="jobsB"
          :initial-bucket-mode="bucketMode"
          @export-series-csv="handleSeriesCsv"
        />
      </section>

      <!-- Job lists -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <div class="text-sm font-semibold mb-2">
            Preset A Jobs
          </div>
          <CamRiskJobList :jobs="jobsA" />
        </div>
        <div>
          <div class="text-sm font-semibold mb-2">
            Preset B Jobs
          </div>
          <CamRiskJobList :jobs="jobsB" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import CamRiskJobList from "@/components/cam/CamRiskJobList.vue";
import CamPresetEvolutionTrend from "@/components/cam/CamPresetEvolutionTrend.vue";
import CamRiskPresetTrend from "@/components/cam/CamRiskPresetTrend.vue";

type PresetName = "Safe" | "Standard" | "Aggressive" | "Custom";

interface SeverityCounts {
  critical?: number;
  [key: string]: number | undefined;
}

interface RiskPresetMeta {
  name?: string;
  source?: string;
  config?: unknown;
}

interface ReliefSimStats {
  avg_floor_thickness?: number;
  min_floor_thickness?: number;
  max_load_index?: number;
  avg_load_index?: number;
  total_removed_volume?: number;
}

interface RiskJob {
  id: string;
  pipeline_id?: string;
  pipelineId?: string;
  op_id?: string;
  opId?: string;
  created_at?: string;
  timestamp?: string;
  analytics?: {
    risk_score?: number;
    total_issues?: number;
    severity_counts?: SeverityCounts;
  };
  meta?: {
    preset?: RiskPresetMeta;
    relief_sim_bridge?: ReliefSimStats;
    sim_stats?: ReliefSimStats;
    stock_thickness?: number;
    [key: string]: unknown;
  };
}

// State
const jobs = ref<RiskJob[]>([]);
const exporting = ref(false);

// Filters
const pipelineFilter = ref<string>("Any");
const fromDate = ref<string>("");
const toDate = ref<string>("");
const presetA = ref<PresetName>("Safe");
const presetB = ref<PresetName>("Aggressive");
const bucketMode = ref<"week" | "version">("week");
const lastSeriesCsv = ref<string>("");

// Helpers
function classifyPresetName(name?: string): PresetName {
  if (!name) return "Custom";
  const n = name.toLowerCase();
  if (n.includes("safe")) return "Safe";
  if (n.includes("standard") || n.includes("std")) return "Standard";
  if (n.includes("agg") || n.includes("aggressive")) return "Aggressive";
  return "Custom";
}

function jobDate(job: RiskJob): Date | null {
  const ts = job.created_at || job.timestamp;
  if (!ts) return null;
  return new Date(ts);
}

function inWindow(job: RiskJob): boolean {
  const d = jobDate(job);
  if (!d) return false;
  if (fromDate.value) {
    const from = new Date(fromDate.value);
    if (d < from) return false;
  }
  if (toDate.value) {
    const to = new Date(toDate.value);
    to.setHours(23, 59, 59, 999);
    if (d > to) return false;
  }
  return true;
}

function summarize(list: RiskJob[]) {
  const jobsCount = list.length;
  const totalRisk = list.reduce((s, j) => s + (j.analytics?.risk_score ?? 0), 0);
  const avgRisk = jobsCount > 0 ? (totalRisk / jobsCount).toFixed(1) : "0.0";
  const totalCritical = list.reduce(
    (s, j) => s + (j.analytics?.severity_counts?.critical ?? 0),
    0
  );
  return { jobsCount, avgRisk, totalCritical };
}

// Computed
const jobsA = computed(() => {
  let list = jobs.value;
  if (pipelineFilter.value !== "Any") {
    list = list.filter((j) => {
      const pid = j.pipeline_id || j.pipelineId || "";
      return pid === pipelineFilter.value;
    });
  }
  list = list.filter(inWindow);
  list = list.filter((j) => {
    const name = j.meta?.preset?.name;
    return classifyPresetName(name) === presetA.value;
  });
  return list.sort((a, b) => {
    const da = jobDate(a);
    const db = jobDate(b);
    if (!da || !db) return 0;
    return db.getTime() - da.getTime();
  });
});

const jobsB = computed(() => {
  let list = jobs.value;
  if (pipelineFilter.value !== "Any") {
    list = list.filter((j) => {
      const pid = j.pipeline_id || j.pipelineId || "";
      return pid === pipelineFilter.value;
    });
  }
  list = list.filter(inWindow);
  list = list.filter((j) => {
    const name = j.meta?.preset?.name;
    return classifyPresetName(name) === presetB.value;
  });
  return list.sort((a, b) => {
    const da = jobDate(a);
    const db = jobDate(b);
    if (!da || !db) return 0;
    return db.getTime() - da.getTime();
  });
});

const summaryA = computed(() => summarize(jobsA.value));
const summaryB = computed(() => summarize(jobsB.value));

// CSV Export
function csvEscape(value: unknown): string {
  if (value === null || value === undefined) return "";
  const s = String(value).replace(/"/g, '""');
  return /[",\n]/.test(s) ? `"${s}"` : s;
}

function downloadCsv(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function buildRows(label: string, list: RiskJob[]): string[] {
  const rows: string[] = [];
  for (const job of list) {
    const pipelineId = job.pipeline_id || job.pipelineId || "";
    const opId = job.op_id || job.opId || "";
    const created = job.created_at || job.timestamp || "";
    const preset = job.meta?.preset;
    const presetName = preset?.name || "";
    const presetSource = preset?.source || "";
    const riskScore = job.analytics?.risk_score ?? "";
    const totalIssues = job.analytics?.total_issues ?? "";
    const criticalCount =
      job.analytics?.severity_counts?.critical != null
        ? job.analytics.severity_counts.critical
        : "";

    const row = [
      csvEscape(label),
      csvEscape(job.id),
      csvEscape(pipelineId),
      csvEscape(opId),
      csvEscape(created),
      csvEscape(presetName),
      csvEscape(presetSource),
      csvEscape(riskScore),
      csvEscape(totalIssues),
      csvEscape(criticalCount),
    ].join(",");
    rows.push(row);
  }
  return rows;
}

async function exportCsv(which: "A" | "B" | "Both") {
  exporting.value = true;
  try {
    const header = [
      "preset_label",
      "job_id",
      "pipeline_id",
      "op_id",
      "created_at",
      "preset_name",
      "preset_source",
      "risk_score",
      "total_issues",
      "critical_count",
    ].join(",");

    let rows: string[] = [];
    if (which === "A" || which === "Both") {
      rows = rows.concat(buildRows("A", jobsA.value));
    }
    if (which === "B" || which === "Both") {
      rows = rows.concat(buildRows("B", jobsB.value));
    }

    const csv = [header, ...rows].join("\r\n");

    const pipeLabel =
      pipelineFilter.value === "Any" ? "all" : pipelineFilter.value.toLowerCase();
    const dateRange =
      fromDate.value && toDate.value
        ? `${fromDate.value}_${toDate.value}`
        : "alltime";
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `preset_compare_${presetA.value}_vs_${presetB.value}_${pipeLabel}_${dateRange}_${ts}.csv`;

    downloadCsv(csv, filename);
  } catch (err) {
    console.error("Preset comparison CSV export failed:", err);
    alert("CSV export failed. See console for details.");
  } finally {
    exporting.value = false;
  }
}

// API
async function fetchJobs() {
  try {
    const response = await fetch("/api/cam/jobs/risk_report");
    if (!response.ok) {
      console.error("Failed to fetch risk jobs:", response.statusText);
      return;
    }
    const data = await response.json();
    jobs.value = data.jobs || [];
  } catch (err) {
    console.error("Failed to fetch risk jobs:", err);
  }
}

function handleSeriesCsv(csv: string) {
  lastSeriesCsv.value = csv;
  // download immediately
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const ts = new Date().toISOString().replace(/[:.]/g, "-");
  a.href = url;
  a.download = `preset_evolution_${presetA.value}_vs_${presetB.value}_${bucketMode.value}_${ts}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

onMounted(() => {
  fetchJobs();
});
</script>
