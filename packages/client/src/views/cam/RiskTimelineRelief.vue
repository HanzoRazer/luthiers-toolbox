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
import { api } from '@/services/apiBase';
import { ref, computed, onMounted } from "vue";
import CamRiskJobList from "@/components/cam/CamRiskJobList.vue";
import CamRiskPresetTrend from "@/components/cam/CamRiskPresetTrend.vue";
import CamRiskCompareBars from "@/components/cam/CamRiskCompareBars.vue";

type PresetFilter = "Any" | "Safe" | "Standard" | "Aggressive" | "Custom";

interface SeverityCounts {
  info?: number;
  low?: number;
  medium?: number;
  high?: number;
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

const jobs = ref<RiskJob[]>([]);
const loading = ref(false);
const exporting = ref(false);

// filters
const presetFilter = ref<PresetFilter>("Any");
const pipelineFilter = ref<string>("Any");
const comparePrev = ref(false);

// classify preset name into one of the canonical buckets
function classifyPresetName(name: string | undefined): PresetFilter {
  if (!name) return "Custom";
  const n = name.toLowerCase();
  if (n.includes("safe")) return "Safe";
  if (n.includes("standard") || n.includes("std")) return "Standard";
  if (n.includes("agg") || n.includes("aggressive")) return "Aggressive";
  return "Custom";
}

// Helper to get job date
function jobDate(job: RiskJob): Date | null {
  const ts = job.created_at || job.timestamp;
  if (!ts) return null;
  return new Date(ts);
}

// Compute a previous window based on current from/to
function computePrevWindow(fromStr: string, toStr: string): { from: Date | null; to: Date | null } {
  // If both from & to present → mirror duration immediately before
  if (fromStr && toStr) {
    const from = new Date(fromStr + "T00:00:00");
    const to = new Date(toStr + "T23:59:59.999");
    const spanMs = to.getTime() - from.getTime() + 1;
    const prevTo = new Date(from.getTime() - 1);
    const prevFrom = new Date(prevTo.getTime() - spanMs + 1);
    return { from: prevFrom, to: prevTo };
  }

  // If only to present → use same length as 30 days before
  if (!fromStr && toStr) {
    const to = new Date(toStr + "T23:59:59.999");
    const prevTo = new Date(to.getTime() - 24 * 3600 * 1000); // end prior day
    const prevFrom = new Date(prevTo.getTime() - 29 * 24 * 3600 * 1000); // 30-day window
    return { from: prevFrom, to: prevTo };
  }

  // If only from present → 30 days ending at from-1
  if (fromStr && !toStr) {
    const from = new Date(fromStr + "T00:00:00");
    const prevTo = new Date(from.getTime() - 1);
    const prevFrom = new Date(prevTo.getTime() - 29 * 24 * 3600 * 1000);
    return { from: prevFrom, to: prevTo };
  }

  // No dates → previous window disabled (use nulls)
  return { from: null, to: null };
}

function jobInDateRange(job: RiskJob, from: Date | null, to: Date | null): boolean {
  if (!from && !to) return true;
  const d = jobDate(job);
  if (!d) return false;
  if (from && d < from) return false;
  if (to && d > to) return false;
  return true;
}

const filteredJobs = computed(() => {
  return jobs.value.filter((job) => {
    // pipeline filter
    const pipelineId = job.pipeline_id || job.pipelineId || "";
    if (
      pipelineFilter.value !== "Any" &&
      pipelineId !== pipelineFilter.value
    ) {
      return false;
    }

    // preset filter
    if (presetFilter.value === "Any") return true;

    const preset = job.meta?.preset;
    const category = classifyPresetName(preset?.name);
    return category === presetFilter.value;
  });
});

// summary over filtered jobs
const summary = computed(() => {
  const list = filteredJobs.value;
  const jobsCount = list.length;
  if (!jobsCount) {
    return {
      jobsCount: 0,
      avgRisk: 0,
      totalCritical: 0,
    };
  }

  let riskSum = 0;
  let criticalSum = 0;

  for (const job of list) {
    const risk = job.analytics?.risk_score ?? 0;
    riskSum += risk;

    const crit =
      job.analytics?.severity_counts?.critical != null
        ? job.analytics.severity_counts.critical
        : 0;
    criticalSum += crit || 0;
  }

  return {
    jobsCount,
    avgRisk: riskSum / jobsCount,
    totalCritical: criticalSum,
  };
});

// Previous window logic
const prevWindow = computed(() => computePrevWindow("", ""));

const filteredJobsPrev = computed(() => {
  const from = prevWindow.value.from;
  const to = prevWindow.value.to;

  return jobs.value.filter((job) => {
    // same pipeline filter
    const pipelineId = job.pipeline_id || job.pipelineId || "";
    if (pipelineFilter.value !== "Any" && pipelineId !== pipelineFilter.value) {
      return false;
    }
    // same preset filter
    if (presetFilter.value !== "Any") {
      const preset = job.meta?.preset;
      const category = classifyPresetName(preset?.name);
      if (category !== presetFilter.value) {
        return false;
      }
    }
    // previous date window
    return jobInDateRange(job, from, to);
  });
});

const summaryPrev = computed(() => {
  const list = filteredJobsPrev.value;
  const jobsCount = list.length;
  if (!jobsCount) {
    return { jobsCount: 0, avgRisk: 0, totalCritical: 0 };
  }
  let riskSum = 0;
  let criticalSum = 0;
  for (const job of list) {
    const risk = job.analytics?.risk_score ?? 0;
    riskSum += risk;
    const crit =
      job.analytics?.severity_counts?.critical != null
        ? job.analytics.severity_counts.critical
        : 0;
    criticalSum += crit || 0;
  }
  return {
    jobsCount,
    avgRisk: riskSum / jobsCount,
    totalCritical: criticalSum,
  };
});

async function fetchJobs() {
  loading.value = true;
  try {
    // Adjust endpoint to match your backend if needed
    const res = await api("/api/cam/jobs/risk_report");
    if (!res.ok) {
      console.error("Failed to fetch risk jobs:", await res.text());
      jobs.value = [];
      return;
    }
    const data = await res.json();
    jobs.value = Array.isArray(data) ? data : [];
  } catch (err) {
    console.error("Risk jobs fetch error:", err);
    jobs.value = [];
  } finally {
    loading.value = false;
  }
}

function reload() {
  fetchJobs();
}

// --- CSV Export Functions ---
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

function buildCsvFromJobsWithWindow(jobsList: RiskJob[], windowLabel: string): string[] {
  const rows: string[] = [];
  for (const job of jobsList) {
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

    const stats =
      job.meta?.relief_sim_bridge || job.meta?.sim_stats || null;

    const avgFloor =
      stats && typeof stats.avg_floor_thickness === "number"
        ? stats.avg_floor_thickness
        : "";
    const minFloor =
      stats && typeof stats.min_floor_thickness === "number"
        ? stats.min_floor_thickness
        : "";
    const maxLoad =
      stats && typeof stats.max_load_index === "number"
        ? stats.max_load_index
        : "";
    const avgLoad =
      stats && typeof stats.avg_load_index === "number"
        ? stats.avg_load_index
        : "";
    const totalVol =
      stats && typeof stats.total_removed_volume === "number"
        ? stats.total_removed_volume
        : "";

    const stockThickness =
      job.meta && typeof job.meta.stock_thickness === "number"
        ? job.meta.stock_thickness
        : "";

    const row = [
      csvEscape(windowLabel),
      csvEscape(job.id),
      csvEscape(pipelineId),
      csvEscape(opId),
      csvEscape(created),
      csvEscape(presetName),
      csvEscape(presetSource),
      csvEscape(riskScore),
      csvEscape(totalIssues),
      csvEscape(criticalCount),
      csvEscape(avgFloor),
      csvEscape(minFloor),
      csvEscape(maxLoad),
      csvEscape(avgLoad),
      csvEscape(totalVol),
      csvEscape(stockThickness),
    ].join(",");
    rows.push(row);
  }
  return rows;
}

async function exportCompareCsv() {
  exporting.value = true;
  try {
    const header = [
      "window_label",
      "job_id",
      "pipeline_id",
      "op_id",
      "created_at",
      "preset_name",
      "preset_source",
      "risk_score",
      "total_issues",
      "critical_count",
      "avg_floor_thickness",
      "min_floor_thickness",
      "max_load_index",
      "avg_load_index",
      "total_removed_volume",
      "stock_thickness",
    ].join(",");

    const currentRows = buildCsvFromJobsWithWindow(filteredJobs.value, "current");
    const prevRows = buildCsvFromJobsWithWindow(filteredJobsPrev.value, "previous");

    const csv = [header, ...currentRows, ...prevRows].join("\r\n");

    const presetLabel =
      presetFilter.value === "Any" ? "mixed" : presetFilter.value.toLowerCase();
    const pipeLabel =
      pipelineFilter.value === "Any" ? "all" : pipelineFilter.value.toLowerCase();
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `relief_risk_compare_${presetLabel}_${pipeLabel}_${ts}.csv`;

    downloadCsv(csv, filename);
  } catch (err) {
    console.error("Compare CSV export failed:", err);
    alert("Compare CSV export failed. See console for details.");
  } finally {
    exporting.value = false;
  }
}

onMounted(() => {
  fetchJobs();
});
</script>
