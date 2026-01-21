<script setup lang="ts">
import { ref, computed } from "vue";
import CamBackplotViewer from "@/components/cam/CamBackplotViewer.vue";
import CamPipelineRunner from "@/components/cam/CamPipelineRunner.vue";
import CamIssuesList from "@/components/cam/CamIssuesList.vue";

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

// --- Design source (DXF path) ---
// You can point this to any headstock DXF you like.
const headstockDxfPath = ref("workspace/art/headstock/demo_headstock_logo.dxf");

// --- Pipeline + backplot state ---
const results = ref<Record<string, any> | null>(null);
const selectedPathOpId = ref<string | null>("headstock_adaptive");
const selectedOverlayOpId = ref<string | null>("headstock_sim");

const showToolpath = ref(true);
const focusPoint = ref<BackplotFocusPoint | null>(null);
const selectedIssueIndex = ref<number | null>(null);
const backplotLoops = ref<BackplotLoop[]>([]);

// --- Risk state ---
const lastRiskAnalytics = ref<RiskAnalytics | null>(null);
const lastRiskReportError = ref<string | null>(null);
const lastRiskReportId = ref<string | null>(null);

// --- Notes state ---
const noteEditorVisible = ref(false);
const noteDraft = ref("");
const noteSaving = ref(false);
const noteSaveError = ref<string | null>(null);

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

// --- Headstock pipeline ops ---
// This follows the same pattern as rosette, but tuned for shallow logo engraving.
const headstockOps: PipelineOp[] = [
  {
    id: "headstock_adaptive",
    op: "AdaptivePocket",
    from_layer: "LOGO",
    input: {
      tool_d: 1.5,
      stepover: 0.3,
      stepdown: 0.4,
      margin: 0.05,
      strategy: "Spiral",
      feed_xy: 600.0,
      safe_z: 3.0,
      z_rough: -0.8,
    },
  } as any,
  {
    id: "headstock_helix",
    op: "HelicalEntry",
    from_op: "headstock_adaptive",
    input: {
      ramp_angle_deg: 3.0,
      pitch_mm: 1.2,
    },
  } as any,
  {
    id: "headstock_post",
    op: "PostProcess",
    from_op: "headstock_helix",
    input: {
      post_preset: "GRBL",
    },
  } as any,
  {
    id: "headstock_sim",
    op: "Simulate",
    from_op: "headstock_post",
    input: {
      stock_thickness: 3.0,
    },
  } as any,
];

// --- Pipeline hooks ---
function handleRun(_payload: PipelineRunIn) {
  // optional no-op
}

// Build backplot snapshot payload for this headstock job
function buildHeadstockBackplotSnapshot(): {
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
      source: "ArtStudioHeadstock",
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
    const simResult = out.results?.["headstock_sim"];
    const issues = (simResult?.issues || []) as (SimIssue & {
      extra_time_s?: number;
    })[];

    const analytics = computeRiskAnalytics(issues);
    lastRiskAnalytics.value = analytics;

    const jobId = `headstock_${Date.now()}`;

    const riskPayload = buildRiskReportPayload({
      jobId,
      pipelineId: "artstudio_headstock_v16",
      opId: "headstock_sim",
      machineProfileId: payload.context?.machine_profile_id || "GUITAR_CNC_01",
      postPreset: payload.context?.post_preset || "GRBL",
      designSource: payload.design?.source || "dxf",
      designPath: payload.design?.dxf_path || headstockDxfPath.value,
      issues,
      analytics,
      meta: {
        source: "ArtStudioHeadstockView",
      },
    });

    const stored = await postRiskReport(riskPayload);
    lastRiskReportId.value = stored.id;

    // Attach backplot snapshot (non-fatal)
    try {
      const snapshot = buildHeadstockBackplotSnapshot();
      if (snapshot) {
        await attachRiskBackplot(stored.id, snapshot);
      }
    } catch (err: any) {
      console.warn("Failed to attach headstock backplot snapshot:", err?.message || err);
    }
  } catch (err: any) {
    console.error("Failed to submit headstock risk report:", err);
    lastRiskReportError.value =
      err?.message || "Failed to submit headstock risk report";
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
    console.error("Failed to save headstock note:", err);
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
        Art Studio – Headstock Logo
      </h1>
      <p class="text-sm text-gray-600">
        Headstock logo engraving pipeline with adaptive pocketing, helical entry, post, simulation,
        and full risk + geometry history.
      </p>
      <div class="text-xs text-gray-500">
        Design DXF:
        <span class="font-mono">{{ headstockDxfPath }}</span>
      </div>
    </header>

    <!-- Pipeline runner -->
    <section class="border rounded bg-white p-4 space-y-3">
      <CamPipelineRunner
        :default-design="{
          source: 'dxf',
          dxf_path: headstockDxfPath,
        }"
        :default-ops="headstockOps"
        :show-gcode="true"
        :show-results="true"
        @run="handleRun"
        @run-success="handleRunSuccess"
        @run-error="handleRunError"
      >
        <template #toolbar>
          <span class="text-[11px] text-gray-500">
            Tune tool, depth, and feeds; this view will log every run to the Job Risk Timeline.
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
          placeholder="Example: Tweaked logo depth to -0.6 mm and slowed feed near nut after small chatter on prior run."
        />
        <div class="flex items-center justify-end gap-2">
          <button
            type="button"
            class="border rounded px-2 py-0.5 bg-white hover:bg-gray-100"
            :disabled="noteSaving"
            @click="cancelNoteEditor"
          >
            Cancel
          </button>
          <button
            type="button"
            class="border rounded px-2 py-0.5 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300"
            :disabled="noteSaving"
            @click="saveNote"
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
            >
            <span>Show toolpath</span>
          </label>
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <CamBackplotViewer
          v-model:show-toolpath="showToolpath"
          :loops="backplotLoops"
          :moves="backplotMoves"
          :overlays="backplotOverlays"
          :focus-point="focusPoint"
          :focus-zoom="0.45"
        />

        <CamIssuesList
          v-model:selected-index="selectedIssueIndex"
          :issues="simIssues"
          title="Simulation Issues"
          @focus-request="handleIssueFocusRequest"
        />
      </div>
    </section>
  </div>
</template>
