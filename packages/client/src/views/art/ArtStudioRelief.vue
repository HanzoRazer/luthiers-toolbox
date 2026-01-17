<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import CamBackplotViewer from "@/components/cam/CamBackplotViewer.vue";
import CamPipelineRunner from "@/components/cam/CamPipelineRunner.vue";
import CamIssuesList from "@/components/cam/CamIssuesList.vue";
import ReliefRiskPresetPanel from "@/components/art/ReliefRiskPresetPanel.vue";

import type {
  PipelineOp,
  PipelineRunIn,
  PipelineRunOut,
} from "@/api/pipeline";

import type {
  BackplotLoop,
  BackplotMove,
  BackplotOverlay,
  BackplotFocusPoint,
  SimIssue,
} from "@/types/cam";

import {
  postRiskReport,
  buildRiskReportPayload,
  patchRiskNotes,
  attachRiskBackplot,
  type RiskAnalytics,
  type RiskBackplotMoveOut,
} from "@/api/camRisk";

// --- Relief design source (heightmap / depthmap) ---
// You can later wire this to an upload flow or to your Relief Mapper UI.
const reliefHeightmapPath = ref("workspace/art/relief/demo_relief_heightmap.png");

// --- Pipeline + backplot state ---
const results = ref<Record<string, any> | null>(null);
const selectedPathOpId = ref<string | null>("relief_finish");
const selectedOverlayOpId = ref<string | null>("relief_sim");

const showToolpath = ref(true);
const focusPoint = ref<BackplotFocusPoint | null>(null);
const selectedIssueIndex = ref<number | null>(null);
const backplotLoops = ref<BackplotLoop[]>([]);

// --- Risk state ---
const lastRiskAnalytics = ref<RiskAnalytics | null>(null);
const lastRiskReportError = ref<string | null>(null);
const lastRiskReportId = ref<string | null>(null);

// --- Snapshot notes state ---
const noteEditorVisible = ref(false);
const noteDraft = ref("");
const noteSaving = ref(false);
const noteSaveError = ref<string | null>(null);

// --- Preset state ---
const activePresetName = ref<string | null>(null);
const activePresetConfig = ref<{
  name: string;
  finishing?: {
    tool_d?: number;
    scallop_height?: number;
    stepdown?: number;
    use_dynamic_scallop?: boolean;
  };
  sim_thresholds?: {
    min_floor_thickness?: number;
    high_load_index?: number;
    med_load_index?: number;
  };
} | null>(null);

// --- Derived backplot data ---
const backplotMoves = computed<BackplotMove[]>(() => {
  if (!results.value || !selectedPathOpId.value) return [];
  const src = results.value[selectedPathOpId.value];
  if (!src || !Array.isArray(src.moves)) return [];
  return src.moves as BackplotMove[];
});

const backplotOverlays = computed<BackplotOverlay[]>(() => {
  const overlays: BackplotOverlay[] = [];
  if (!results.value) return overlays;

  if (selectedPathOpId.value) {
    const src = results.value[selectedPathOpId.value];
    if (src && Array.isArray(src.overlays)) {
      overlays.push(
        ...src.overlays.map((o: any) => ({
          type: o.type || "overlay",
          x: Number(o.x ?? 0),
          y: Number(o.y ?? 0),
          radius: typeof o.radius === "number" ? o.radius : 1.5,
          severity: o.severity,
          feed_pct: o.feed_pct,
        }))
      );
    }
  }

  if (selectedOverlayOpId.value) {
    const simSrc = results.value[selectedOverlayOpId.value];
    const issues = (simSrc?.issues || []) as SimIssue[];
    overlays.push(
      ...issues.map((iss) => ({
        type: iss.type || "sim_issue",
        x: iss.x,
        y: iss.y,
        radius: 2.5,
        severity: iss.severity,
      }))
    );
  }

  return overlays;
});

const simIssues = computed<SimIssue[]>(() => {
  if (!results.value || !selectedOverlayOpId.value) return [];
  const simSrc = results.value[selectedOverlayOpId.value];
  return (simSrc?.issues || []) as SimIssue[];
});

// --- Risk analytics helper ---
const severityOptions = ["info", "low", "medium", "high", "critical"] as const;
type SeverityOption = (typeof severityOptions)[number];

function computeRiskAnalytics(
  issues: (SimIssue & { extra_time_s?: number })[]
): RiskAnalytics {
  const counts: Record<SeverityOption, number> = {
    info: 0,
    low: 0,
    medium: 0,
    high: 0,
    critical: 0,
  };

  let totalExtra = 0;

  for (const iss of issues) {
    const sev = (iss.severity || "medium") as SeverityOption;
    if (sev in counts) counts[sev] += 1;
    const extra =
      typeof (iss as any).extra_time_s === "number" ? (iss as any).extra_time_s : 0;
    totalExtra += extra;
  }

  const riskScore =
    counts.critical * 5 +
    counts.high * 3 +
    counts.medium * 2 +
    counts.low * 1 +
    counts.info * 0.5;

  const totalIssues = issues.length;

  const formatDuration = (sec: number): string => {
    if (!sec || sec <= 0) return "0 s";
    const whole = Math.round(sec);
    const minutes = Math.floor(whole / 60);
    const seconds = whole % 60;
    if (minutes === 0) return `${seconds} s`;
    return `${minutes} min ${seconds} s`;
  };

  return {
    total_issues: totalIssues,
    severity_counts: {
      info: counts.info,
      low: counts.low,
      medium: counts.medium,
      high: counts.high,
      critical: counts.critical,
    },
    risk_score: riskScore,
    total_extra_time_s: totalExtra,
    total_extra_time_human: formatDuration(totalExtra),
  };
}

// --- Relief pipeline ops ---
// These are contracts for your future Relief Mapper / heightfield kernels.
const reliefOps: PipelineOp[] = [
  {
    id: "relief_map",
    op: "ReliefMapFromHeightfield",
    input: {
      heightmap_path: reliefHeightmapPath.value,
      units: "mm",
      // depth scaling
      z_min: 0.0,
      z_max: -3.0,
      // resolution, you can tune later
      sample_pitch_xy: 0.3,
      smooth_sigma: 0.4,
    },
  } as any,
  {
    id: "relief_rough",
    op: "ReliefRoughing",
    from_op: "relief_map",
    input: {
      tool_d: 3.0,          // flat end mill
      stepdown: 0.7,
      stepover: 0.6,
      safe_z: 4.0,
      z_clearance: 1.0,
      feed_xy: 800.0,
      feed_z: 300.0,
    },
  } as any,
  {
    id: "relief_finish",
    op: "ReliefFinishing",
    from_op: "relief_map",
    input: {
      tool_d: 2.0,          // ball nose
      scallop_height: 0.06,
      stepdown: 0.4,
      safe_z: 4.0,
      feed_xy: 600.0,
      feed_z: 250.0,
      pattern: "RasterX",   // RasterX | RasterY | Spiral (future)
    },
  } as any,
  {
    id: "relief_post",
    op: "PostProcess",
    from_op: "relief_finish",
    input: {
      post_preset: "GRBL",
    },
  } as any,
  {
    id: "relief_sim",
    op: "Simulate",
    from_op: "relief_post",
    input: {
      stock_thickness: 5.0,
    },
  } as any,
];

// --- Preset functions ---
function loadReliefPresetFromStorage(showToast = false) {
  try {
    const raw = localStorage.getItem("relief_artstudio_default_preset");
    if (!raw) {
      if (showToast) {
        alert("No Lab preset has been promoted yet.");
      }
      return;
    }
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return;

    activePresetConfig.value = parsed;
    activePresetName.value = parsed.name || null;

    // Apply finishing defaults to reliefOps finishing input
    const finishOp = reliefOps.find((op) => op.id === "relief_finish");
    if (finishOp && (finishOp as any).input) {
      const input = (finishOp as any).input;
      if (parsed.finishing?.scallop_height != null) {
        input.scallop_height = parsed.finishing.scallop_height;
      }
      if (parsed.finishing?.stepdown != null) {
        input.stepdown = parsed.finishing.stepdown;
      }
      if (parsed.finishing?.use_dynamic_scallop != null) {
        input.use_dynamic_scallop = parsed.finishing.use_dynamic_scallop;
      }
      // Optional: tool_d override
      if (parsed.finishing?.tool_d != null) {
        input.tool_d = parsed.finishing.tool_d;
      }
    }

    if (showToast) {
      alert(`Loaded preset "${activePresetName.value}" from Relief Lab.`);
    }
  } catch (err) {
    console.warn("Failed to load Art Studio relief preset:", err);
    if (showToast) {
      alert("Failed to load Lab preset from localStorage.");
    }
  }
}

function applyLocalPreset(payload: { name: string; config: any }) {
  const cfg = payload.config || {};
  activePresetName.value = `Local:${payload.name}`;
  activePresetConfig.value = {
    name: activePresetName.value,
    finishing: {
      scallop_height: cfg.scallop_height,
      stepdown: cfg.stepdown,
      use_dynamic_scallop: true,
      // tool_d: you can set a local default here if you want
    },
    sim_thresholds: {
      min_floor_thickness: cfg.min_floor_thickness,
      high_load_index: cfg.high_load_index,
      med_load_index: 1.0,
    },
  };

  // Immediately apply to the finishing op
  const finishOp = reliefOps.find((op) => op.id === "relief_finish");
  if (finishOp && (finishOp as any).input) {
    const input = (finishOp as any).input;
    if (cfg.scallop_height != null) {
      input.scallop_height = cfg.scallop_height;
    }
    if (cfg.stepdown != null) {
      input.stepdown = cfg.stepdown;
    }
    // Turn on dynamic scallop by default for local presets
    input.use_dynamic_scallop = true;
  }
}

function reloadLabPreset() {
  loadReliefPresetFromStorage(true);
}

onMounted(() => {
  loadReliefPresetFromStorage(false);
});

// --- Pipeline hooks ---
function handleRun(_payload: PipelineRunIn) {
  // optional
}

// Build backplot snapshot payload for relief job
function buildReliefBackplotSnapshot(): {
  moves: RiskBackplotMoveOut[];
  overlays: Record<string, unknown>[];
  meta: Record<string, unknown>;
} | null {
  if (!results.value || !selectedPathOpId.value) return null;
  const src = results.value[selectedPathOpId.value];
  if (!src || !Array.isArray(src.moves)) return null;

  const moves: RiskBackplotMoveOut[] = (src.moves as any[]).map((mv) => ({
    code: mv.code ?? mv.g ?? null,
    x: typeof mv.x === "number" ? mv.x : null,
    y: typeof mv.y === "number" ? mv.y : null,
    z: typeof mv.z === "number" ? mv.z : null,
    f: typeof mv.f === "number" ? mv.f : null,
  }));

  const overlays = Array.isArray(src.overlays) ? (src.overlays as any[]) : [];

  return {
    moves,
    overlays,
    meta: {
      source: "ArtStudioRelief",
      path_op_id: selectedPathOpId.value,
      overlay_op_id: selectedOverlayOpId.value,
    },
  };
}

async function handleRunSuccess(payload: PipelineRunIn, out: PipelineRunOut) {
  results.value = out.results;
  focusPoint.value = null;
  selectedIssueIndex.value = null;
  lastRiskReportError.value = null;
  lastRiskReportId.value = null;
  noteEditorVisible.value = false;
  noteDraft.value = "";
  noteSaveError.value = null;

  try {
    const simResult = out.results?.["relief_sim"];
    const issues = (simResult?.issues || []) as (SimIssue & {
      extra_time_s?: number;
    })[];

    const analytics = computeRiskAnalytics(issues);
    lastRiskAnalytics.value = analytics;

    const jobId = `relief_${Date.now()}`;

    const riskPayload = buildRiskReportPayload({
      jobId,
      pipelineId: "artstudio_relief_v16",
      opId: "relief_sim",
      machineProfileId: payload.context?.machine_profile_id || "GUITAR_CNC_01",
      postPreset: payload.context?.post_preset || "GRBL",
      designSource: payload.design?.source || "heightmap",
      designPath: (payload.design as any)?.heightmap_path || reliefHeightmapPath.value,
      issues,
      analytics,
      meta: {
        source: "ArtStudioReliefView",
      },
    });

    const stored = await postRiskReport(riskPayload);
    lastRiskReportId.value = stored.id;

    // Attach backplot snapshot (non-fatal)
    try {
      const snapshot = buildReliefBackplotSnapshot();
      if (snapshot) {
        await attachRiskBackplot(stored.id, snapshot);
      }
    } catch (err: any) {
      console.warn("Failed to attach relief backplot snapshot:", err?.message || err);
    }
  } catch (err: any) {
    console.error("Failed to submit relief risk report:", err);
    lastRiskReportError.value =
      err?.message || "Failed to submit relief risk report";
  }
}

function handleRunError(_payload: PipelineRunIn, _err: string) {
  // optional
}

// --- Notes UI actions ---
function openNoteEditor() {
  if (!lastRiskReportId.value) return;
  noteEditorVisible.value = true;
  noteSaveError.value = null;
}

function cancelNoteEditor() {
  noteEditorVisible.value = false;
  noteSaveError.value = null;
}

async function saveNote() {
  if (!lastRiskReportId.value) return;
  noteSaving.value = true;
  noteSaveError.value = null;
  try {
    await patchRiskNotes(lastRiskReportId.value, noteDraft.value || "");
    noteEditorVisible.value = false;
  } catch (err: any) {
    console.error("Failed to save relief note:", err);
    noteSaveError.value = err?.message || "Failed to save note";
  } finally {
    noteSaving.value = false;
  }
}

function handleIssueFocusRequest(payload: { index: number; issue: SimIssue }) {
  selectedIssueIndex.value = payload.index;
  focusPoint.value = {
    x: payload.issue.x,
    y: payload.issue.y,
  };
}
</script>

<template>
  <div class="p-6 space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Art Studio – Relief Carving
      </h1>
      <p class="text-sm text-gray-600">
        Relief carving pipeline from heightmap to roughing, finishing, post, and simulation,
        with full risk and geometry history.
      </p>
      <div class="text-xs text-gray-500">
        Heightmap:
        <span class="font-mono">{{ reliefHeightmapPath }}</span>
      </div>
      
      <!-- Preset controls -->
      <section class="mt-2 flex flex-wrap items-center gap-3">
        <ReliefRiskPresetPanel @update="(p: any) => applyLocalPreset(p)" />

        <button
          type="button"
          class="text-xs px-2 py-1 border rounded bg-white hover:bg-gray-50"
          @click="reloadLabPreset"
        >
          Reload Lab preset
        </button>

        <p v-if="activePresetName" class="text-xs text-gray-500">
          Active preset:
          <span class="font-semibold">{{ activePresetName }}</span>
        </p>
      </section>
    </header>

    <!-- Relief pipeline runner -->
    <section class="border rounded bg-white p-4 space-y-3">
      <CamPipelineRunner
        :default-design="{
          source: 'heightmap',
          heightmap_path: reliefHeightmapPath,
        }"
        :default-ops="reliefOps"
        :show-gcode="true"
        :show-results="true"
        @run="handleRun"
        @run-success="handleRunSuccess"
        @run-error="handleRunError"
      >
        <template #toolbar>
          <span class="text-[11px] text-gray-500">
            Use this lane to prototype relief strategies; every run will log a snapshot into the Job Risk Timeline.
          </span>
        </template>
      </CamPipelineRunner>

      <!-- Risk summary line -->
      <div
        v-if="lastRiskAnalytics || lastRiskReportError"
        class="text-[11px] mt-2 flex flex-wrap items-center justify-between gap-2"
      >
        <div
          v-if="lastRiskAnalytics"
          class="text-gray-600"
        >
          Risk score:
          <span class="font-semibold">
            {{ lastRiskAnalytics.risk_score.toFixed(1) }}
          </span>
          · Extra time:
          <span class="font-semibold">
            {{ lastRiskAnalytics.total_extra_time_human }}
          </span>
          · Issues:
          <span class="font-semibold">
            {{ lastRiskAnalytics.total_issues }}
          </span>
          <span
            v-if="lastRiskReportId"
            class="ml-2 text-gray-400"
          >
            (snapshot {{ lastRiskReportId.slice(0, 8) }}…)
          </span>
        </div>
        <div
          v-if="lastRiskReportError"
          class="text-red-600"
        >
          {{ lastRiskReportError }}
        </div>
      </div>
    </section>

    <!-- Snapshot notes -->
    <section
      v-if="lastRiskReportId"
      class="border rounded p-3 bg-white text-[11px] space-y-2"
    >
      <div class="flex items-center justify-between">
        <span class="font-semibold text-gray-700">
          Snapshot notes
        </span>
        <button
          type="button"
          class="border rounded px-2 py-0.5 bg-white hover:bg-gray-100"
          @click="openNoteEditor"
        >
          Attach / edit note
        </button>
      </div>

      <div
        v-if="noteEditorVisible"
        class="space-y-2 mt-1"
      >
        <textarea
          v-model="noteDraft"
          rows="3"
          class="w-full border rounded px-2 py-1 text-[11px] font-mono"
          placeholder="Example: Switched to RasterX finishing, reduced scallop height, slowed feed in high curvature zones."
        />
        <div class="flex items-center justify-end gap-2">
          <button
            type="button"
            class="border rounded px-2 py-0.5 bg-white hover:bg-gray-100"
            @click="cancelNoteEditor"
            :disabled="noteSaving"
          >
            Cancel
          </button>
          <button
            type="button"
            class="border rounded px-2 py-0.5 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300"
            @click="saveNote"
            :disabled="noteSaving"
          >
            {{ noteSaving ? "Saving…" : "Save note" }}
          </button>
        </div>
        <div
          v-if="noteSaveError"
          class="text-[10px] text-red-600"
        >
          {{ noteSaveError }}
        </div>
      </div>
    </section>

    <!-- Backplot + issues -->
    <section
      v-if="results"
      class="border rounded p-4 bg-white space-y-3"
    >
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-lg">
          Backplot & Issues
        </h2>
        <div class="flex items-center gap-2 text-[11px] text-gray-600">
          <label class="flex items-center gap-1">
            <input
              v-model="showToolpath"
              type="checkbox"
              class="align-middle"
            />
            <span>Show toolpath</span>
          </label>
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <CamBackplotViewer
          :loops="backplotLoops"
          :moves="backplotMoves"
          :overlays="backplotOverlays"
          v-model:showToolpath="showToolpath"
          :focus-point="focusPoint"
          :focus-zoom="0.4"
        />

        <CamIssuesList
          :issues="simIssues"
          v-model:selectedIndex="selectedIssueIndex"
          title="Simulation Issues"
          @focus-request="handleIssueFocusRequest"
        />
      </div>
    </section>
  </div>
</template>
