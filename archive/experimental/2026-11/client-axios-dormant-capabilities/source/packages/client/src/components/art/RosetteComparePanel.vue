<template>
  <div class="flex flex-col gap-3">
    <!-- Controls -->
    <div class="flex flex-wrap items-end gap-3">
      <div class="flex flex-col text-xs">
        <label class="font-semibold text-gray-700 mb-1">Baseline name</label>
        <input
          v-model="baselineName"
          type="text"
          placeholder="e.g. Rosette V1 – Herringbone"
          class="px-2 py-1 border rounded text-xs w-64"
        >
      </div>

      <button
        class="px-3 py-1 rounded bg-emerald-600 text-white text-xs hover:bg-emerald-700 disabled:opacity-50"
        :disabled="!baselineName || !currentGeometry"
        @click="saveBaseline"
      >
        Save baseline
      </button>

      <div class="flex flex-col text-xs">
        <label class="font-semibold text-gray-700 mb-1">Select baseline</label>
        <select
          v-model="selectedBaselineId"
          class="px-2 py-1 border rounded text-xs w-64"
        >
          <option :value="null">
            — choose baseline —
          </option>
          <option
            v-for="b in baselines"
            :key="b.id"
            :value="b.id"
          >
            {{ b.name }} · {{ formatDate(b.created_at) }}
          </option>
        </select>
      </div>

      <div class="flex flex-col text-xs">
        <label class="font-semibold text-gray-700 mb-1">Job ID (optional)</label>
        <input
          v-model="jobId"
          type="text"
          placeholder="e.g. rosette_job_001"
          class="px-2 py-1 border rounded text-xs w-48"
          @input="handleJobIdInput"
        >
      </div>

      <div class="flex flex-col text-xs">
        <label class="font-semibold text-gray-700 mb-1">Preset (optional)</label>
        <input
          v-model="preset"
          type="text"
          placeholder="e.g. Safe, Aggressive"
          class="px-2 py-1 border rounded text-xs w-32"
        >
      </div>

      <button
        class="px-3 py-1 rounded bg-indigo-600 text-white text-xs hover:bg-indigo-700 disabled:opacity-50"
        :disabled="!selectedBaselineId || !currentGeometry"
        @click="runDiff"
      >
        Compare
      </button>
    </div>

    <!-- Stats -->
    <div
      v-if="diffStats"
      class="text-[11px] text-gray-800 flex flex-wrap gap-3"
    >
      <span>
        Baseline paths: <span class="font-mono">{{ diffStats.baseline_path_count }}</span>
      </span>
      <span>
        Current paths: <span class="font-mono">{{ diffStats.current_path_count }}</span>
      </span>
      <span class="text-emerald-700">
        + Added: <span class="font-mono">{{ diffStats.added_paths }}</span>
      </span>
      <span class="text-rose-700">
        – Removed: <span class="font-mono">{{ diffStats.removed_paths }}</span>
      </span>
      <span class="text-gray-700">
        = Unchanged: <span class="font-mono">{{ diffStats.unchanged_paths }}</span>
      </span>
    </div>

    <!-- Legend -->
    <div class="flex flex-wrap items-center gap-3 text-[10px] text-gray-600">
      <div class="flex items-center gap-1">
        <span class="inline-block w-3 h-3 rounded bg-emerald-500 border border-emerald-700" />
        <span>Added (current only)</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="inline-block w-3 h-3 rounded bg-rose-500 border border-rose-700" />
        <span>Removed (baseline only)</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="inline-block w-3 h-3 rounded bg-gray-500 border border-gray-700" />
        <span>Unchanged (both)</span>
      </div>
    </div>

    <!-- Dual Canvas -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
      <!-- Baseline canvas -->
      <div class="border rounded bg-white p-2 flex flex-col">
        <div class="text-[11px] text-gray-600 mb-1 flex items-center justify-between">
          <span class="font-semibold">Baseline</span>
          <span
            v-if="selectedBaseline"
            class="text-[10px]"
          >
            {{ selectedBaseline.name }}
          </span>
        </div>
        <canvas
          ref="baselineCanvasRef"
          class="w-full aspect-square border rounded bg-slate-50"
        />
      </div>

      <!-- Current canvas -->
      <div class="border rounded bg-white p-2 flex flex-col">
        <div class="text-[11px] text-gray-600 mb-1 flex items-center justify-between">
          <span class="font-semibold">Current</span>
          <span class="text-[10px] text-gray-500">Live Rosette</span>
        </div>
        <canvas
          ref="currentCanvasRef"
          class="w-full aspect-square border rounded bg-slate-50"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  useRosetteCompareApi,
  type GeometryPayload,
} from "./rosette-compare/useRosetteCompareApi";

const props = defineProps<{
  currentGeometry: GeometryPayload | null;
  jobId?: string | null;
}>();

const emit = defineEmits<{
  (e: "update:job-id", val: string): void;
}>();

const {
  baselines,
  diffStats,
  baselineGeometry,
  loadBaselines,
  saveBaseline: persistBaseline,
  loadBaselineGeometry,
  runDiff: requestDiff,
  clearDiff,
} = useRosetteCompareApi();

const baselineName = ref("");
const selectedBaselineId = ref<string | null>(null);
const selectedBaseline = computed(() =>
  baselines.value.find((b) => b.id === selectedBaselineId.value) || null
);

// Phase 27.1: job ID for logging into risk/job snapshots
// Phase 27.2: Synced with parent component
const jobId = ref<string>(props.jobId ?? "");

// Phase 27.4: preset label (Safe, Aggressive, etc.)
const preset = ref<string>("");

// canvas refs
const baselineCanvasRef = ref<HTMLCanvasElement | null>(null);
const currentCanvasRef = ref<HTMLCanvasElement | null>(null);

function formatDate(dt: string): string {
  try {
    const d = new Date(dt);
    return d.toLocaleString();
  } catch {
    return dt;
  }
}

async function saveBaseline() {
  if (!baselineName.value || !props.currentGeometry) return;
  const id = await persistBaseline(baselineName.value, props.currentGeometry);
  if (id) selectedBaselineId.value = id;
}

async function runDiff() {
  if (!selectedBaselineId.value || !props.currentGeometry) return;

  const baselineId = selectedBaselineId.value;
  const currentGeometry = props.currentGeometry;

  // Phase 27.1 / 27.2: store and emit the trimmed job id before the request.
  if (jobId.value.trim()) {
    const trimmedJob = jobId.value.trim();
    localStorage.setItem("ltb:compare:lastJobId", trimmedJob);
    emit("update:job-id", trimmedJob);
  }

  const result = await requestDiff(baselineId, currentGeometry, {
    jobId: jobId.value,
    preset: preset.value,
  });
  if (!result || selectedBaselineId.value !== baselineId) return;
  drawCanvases(result.current_geometry || props.currentGeometry || null);
}

/**
 * Phase 27.1: Map meta.color or color strings to actual stroke colors.
 */
function colorForPath(path: any, fallback: string): string {
  const metaColor = path?.meta?.color || path?.color;
  switch (metaColor) {
    case "green":
      return "#22c55e"; // added
    case "red":
      return "#ef4444"; // removed
    case "gray":
      return "#6b7280"; // unchanged
    default:
      return fallback;
  }
}

function drawCanvases(currentGeomOverride: GeometryPayload | null = null) {
  drawGeometryOnCanvas(
    baselineCanvasRef.value,
    baselineGeometry.value || null,
    "#111827" // fallback baseline color
  );
  drawGeometryOnCanvas(
    currentCanvasRef.value,
    currentGeomOverride || props.currentGeometry || null,
    "#2563eb" // fallback current color
  );
}

function drawGeometryOnCanvas(
  canvas: HTMLCanvasElement | null,
  geometry: GeometryPayload | null,
  defaultStroke: string
) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.save();
  ctx.fillStyle = "#f9fafb";
  ctx.fillRect(0, 0, w, h);

  // No geometry: leave the canvas blank rather than keep the previous drawing.
  if (!geometry) {
    ctx.restore();
    return;
  }
  const paths = geometry.paths || geometry.loops || [];

  // compute bounding box
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;

  for (const path of paths) {
    const pts = path.points || path.pts || [];
    for (const p of pts) {
      if (!Array.isArray(p) || p.length < 2) continue;
      const x = Number(p[0]);
      const y = Number(p[1]);
      if (!isFinite(x) || !isFinite(y)) continue;
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    }
  }

  if (!isFinite(minX) || !isFinite(minY) || !isFinite(maxX) || !isFinite(maxY)) {
    ctx.restore();
    return;
  }

  const dx = maxX - minX || 1;
  const dy = maxY - minY || 1;

  const margin = 10;
  const scale = Math.min((w - 2 * margin) / dx, (h - 2 * margin) / dy);

  ctx.translate(w / 2, h / 2);
  // flip Y axis
  ctx.scale(scale, -scale);
  ctx.translate(-(minX + maxX) / 2, -(minY + maxY) / 2);

  for (const path of paths) {
    const pts = path.points || path.pts || [];
    let started = false;
    ctx.beginPath();

    // Phase 27.1: set color per path based on meta.color or fallback
    ctx.strokeStyle = colorForPath(path, defaultStroke);
    ctx.lineWidth = ctx.strokeStyle === "#6b7280" ? 1 : 1.5;

    for (const p of pts) {
      if (!Array.isArray(p) || p.length < 2) continue;
      const x = Number(p[0]);
      const y = Number(p[1]);
      if (!started) {
        ctx.moveTo(x, y);
        started = true;
      } else {
        ctx.lineTo(x, y);
      }
    }
    if (started) {
      ctx.closePath();
      ctx.stroke();
    }
  }

  ctx.restore();
}

function handleJobIdInput() {
  // Phase 27.2: Emit updates to parent
  emit("update:job-id", jobId.value);
}

onMounted(() => {
  loadBaselines();
  // Phase 27.2: load last job id if present
  const lastJob = localStorage.getItem("ltb:compare:lastJobId");
  if (lastJob) {
    jobId.value = lastJob;
    emit("update:job-id", lastJob);
  }
  // initial draw for current geometry only
  drawCanvases();
});

// Phase 27.2: Sync jobId from parent
watch(
  () => props.jobId,
  (val) => {
    if (val !== undefined && val !== null && val !== jobId.value) {
      jobId.value = val;
    }
  }
);

// A comparison describes the geometry it was run against. When the current
// geometry changes, drop a pending comparison and remove the shown statistics.
watch(
  () => props.currentGeometry,
  () => {
    clearDiff();
    drawCanvases();
  },
  { deep: true }
);

watch(
  () => selectedBaselineId.value,
  async () => {
    const requestedId = selectedBaselineId.value;
    // loadBaselineGeometry synchronously drops any comparison for another
    // baseline and the other baseline's geometry, so draw that cleared state now.
    const pending = loadBaselineGeometry(requestedId ?? "");
    drawCanvases();
    const geometry = await pending;
    if (!requestedId || selectedBaselineId.value !== requestedId || geometry == null) return;
    drawCanvases();
  }
);
</script>
