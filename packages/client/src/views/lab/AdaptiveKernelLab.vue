<template>
  <div class="p-3 space-y-3 text-[11px]">
    <h1 class="text-lg font-semibold text-gray-900 mb-2">
      Adaptive Kernel Lab
    </h1>

    <!-- Layout: left controls, right preview -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <!-- LEFT: Controls -->
      <div class="space-y-2">
        <!-- DXF Upload -->
        <div class="border rounded bg-slate-50 p-2 space-y-1">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-semibold text-gray-900 text-[11px]">
                DXF → Adaptive plan
              </div>
              <div class="text-[10px] text-gray-500">
                Upload GEOMETRY DXF, configure tool, and generate adaptive path.
              </div>
            </div>
          </div>

          <div class="mt-1 space-y-1">
            <input
              type="file"
              accept=".dxf"
              class="block w-full text-[10px]"
              @change="onDxfFileChange"
            >

            <div class="grid grid-cols-2 gap-1 text-[10px]">
              <label class="flex flex-col">
                <span class="text-gray-600">Tool Ø (mm)</span>
                <input
                  v-model.number="toolDxf.tool_d"
                  type="number"
                  step="0.1"
                  class="border rounded px-1 py-0.5"
                >
              </label>
              <label class="flex flex-col">
                <span class="text-gray-600">Stepdown</span>
                <input
                  v-model.number="toolDxf.stepdown"
                  type="number"
                  step="0.1"
                  class="border rounded px-1 py-0.5"
                >
              </label>
              <label class="flex flex-col">
                <span class="text-gray-600">Stepover</span>
                <input
                  v-model.number="toolDxf.stepover"
                  type="number"
                  step="0.05"
                  class="border rounded px-1 py-0.5"
                >
              </label>
              <label class="flex flex-col">
                <span class="text-gray-600">Z rough</span>
                <input
                  v-model.number="toolDxf.z_rough"
                  type="number"
                  step="0.1"
                  class="border rounded px-1 py-0.5"
                >
              </label>
            </div>

            <button
              type="button"
              class="mt-1 px-2 py-1 rounded bg-blue-600 text-white text-[10px] hover:bg-blue-700 disabled:opacity-50"
              :disabled="!dxfFile || runningDxf"
              @click="runDxfAdaptive"
            >
              <span v-if="!runningDxf">Run DXF → Adaptive</span>
              <span v-else>Running…</span>
            </button>

            <div
              v-if="dxfError"
              class="mt-1 text-[10px] text-red-600"
            >
              {{ dxfError }}
            </div>
          </div>
        </div>

        <!-- JSON Loops direct input (existing) -->
        <div class="border rounded bg-white p-2 space-y-1">
          <div class="flex items-center justify-between">
            <div class="font-semibold text-gray-900 text-[11px]">
              Loops JSON
            </div>
            <button
              type="button"
              class="px-1.5 py-0.5 rounded border text-[10px] bg-slate-50 hover:bg-slate-100"
              @click="loadDemoRect"
            >
              Load demo rectangle
            </button>
          </div>
          <textarea
            v-model="loopsJson"
            class="w-full h-32 border rounded px-1 py-0.5 font-mono text-[10px]"
          />
          <button
            type="button"
            class="mt-1 px-2 py-1 rounded bg-emerald-600 text-white text-[10px] hover:bg-emerald-700"
            @click="runAdaptiveFromJson"
          >
            Run Adaptive Kernel
          </button>
        </div>

        <!-- Stats -->
        <div
          v-if="planStats"
          class="border rounded bg-slate-50 p-2 text-[10px] space-y-0.5"
        >
          <div class="font-semibold text-gray-900 text-[11px] mb-1">
            Plan stats
          </div>
          <div>Length: <span class="font-mono">{{ planStats.length_mm }}</span> mm</div>
          <div>Area: <span class="font-mono">{{ planStats.area_mm2 }}</span> mm²</div>
          <div>Time: <span class="font-mono">{{ planStats.time_s }}</span> s</div>
          <div>Moves: <span class="font-mono">{{ planStats.move_count }}</span></div>
        </div>
      </div>

      <!-- RIGHT: Preview -->
      <div class="border rounded bg-white p-2 flex flex-col">
        <div class="flex items-center justify-between mb-1">
          <div class="font-semibold text-gray-900 text-[11px]">
            Toolpath Preview
          </div>
          <div class="text-[10px] text-gray-500">
            {{ previewSegments.length }} segments
          </div>
        </div>

        <div class="flex-1 border bg-slate-900 rounded relative overflow-hidden">
          <!-- tiny SVG preview -->
          <svg
            v-if="previewSegments.length"
            viewBox="0 0 100 100"
            preserveAspectRatio="xMidYMid meet"
            class="w-full h-full"
          >
            <!-- boundary -->
            <polyline
              v-for="(seg, idx) in previewSegments"
              :key="idx"
              :points="segToPoints(seg)"
              fill="none"
              stroke="lime"
              stroke-width="0.4"
            />
          </svg>
          <div
            v-else
            class="absolute inset-0 flex items-center justify-center text-[10px] text-gray-400"
          >
            Run adaptive kernel to see preview
          </div>
        </div>

        <!-- Raw JSON toggle -->
        <details
          v-if="lastPlan"
          class="mt-1 text-[10px]"
        >
          <summary class="cursor-pointer text-gray-600">
            Raw plan JSON
          </summary>
          <pre class="mt-1 max-h-48 overflow-auto bg-slate-900 text-slate-100 rounded p-2">
{{ JSON.stringify(lastPlan, null, 2) }}
          </pre>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import axios from "axios";
import { usePresetQueryBootstrap } from '@/composables/usePresetQueryBootstrap';

type PreviewSegment = {
  x1: number; y1: number;
  x2: number; y2: number;
};

const loopsJson = ref<string>("");
const planStats = ref<any | null>(null);
const lastPlan = ref<any | null>(null);
const previewSegments = ref<PreviewSegment[]>([]);

/* DXF state */
const dxfFile = ref<File | null>(null);
const runningDxf = ref(false);
const dxfError = ref<string | null>(null);

const toolDxf = ref({
  tool_d: 6.0,
  stepover: 0.45,
  stepdown: 2.0,
  z_rough: -1.5
});

function onDxfFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0] || null;
  dxfFile.value = file;
  dxfError.value = null;
}

/* Helper to map moves into preview segments (very simple XY connect) */
function movesToSegments(moves: any[]): PreviewSegment[] {
  const segs: PreviewSegment[] = [];
  let last = { x: 0, y: 0, has: false };

  for (const m of moves) {
    const x = typeof m.x === "number" ? m.x : last.x;
    const y = typeof m.y === "number" ? m.y : last.y;

    if (last.has) {
      segs.push({ x1: last.x, y1: last.y, x2: x, y2: y });
    }
    last = { x, y, has: true };
  }
  return segs;
}

function normalizeSegmentsToView(segs: PreviewSegment[]): PreviewSegment[] {
  if (!segs.length) return [];
  let minX = segs[0].x1, maxX = segs[0].x1;
  let minY = segs[0].y1, maxY = segs[0].y1;

  for (const s of segs) {
    minX = Math.min(minX, s.x1, s.x2);
    maxX = Math.max(maxX, s.x1, s.x2);
    minY = Math.min(minY, s.y1, s.y2);
    maxY = Math.max(maxY, s.y1, s.y2);
  }

  const dx = maxX - minX || 1;
  const dy = maxY - minY || 1;
  const scale = 90 / Math.max(dx, dy);
  const offsetX = (100 - dx * scale) / 2;
  const offsetY = (100 - dy * scale) / 2;

  return segs.map(s => ({
    x1: (s.x1 - minX) * scale + offsetX,
    y1: 100 - ((s.y1 - minY) * scale + offsetY),
    x2: (s.x2 - minX) * scale + offsetX,
    y2: 100 - ((s.y2 - minY) * scale + offsetY),
  }));
}

function segToPoints(seg: PreviewSegment): string {
  return `${seg.x1},${seg.y1} ${seg.x2},${seg.y2}`;
}

/* Run from JSON loops (existing style) */
async function runAdaptiveFromJson() {
  try {
    const body = JSON.parse(loopsJson.value || "{}");
    const res = await axios.post("/api/cam/pocket/adaptive/plan", body);
    const data = res.data;
    lastPlan.value = data;
    planStats.value = data.stats || null;
    const segs = movesToSegments(data.moves || []);
    previewSegments.value = normalizeSegmentsToView(segs);
  } catch (err: any) {
    console.error("Adaptive error", err);
  }
}

/* Run from DXF upload via /plan_from_dxf */
async function runDxfAdaptive() {
  if (!dxfFile.value) return;
  runningDxf.value = true;
  dxfError.value = null;
  try {
    const form = new FormData();
    form.append("file", dxfFile.value);
    form.append("tool_d", String(toolDxf.value.tool_d));
    form.append("stepover", String(toolDxf.value.stepover));
    form.append("stepdown", String(toolDxf.value.stepdown));
    form.append("z_rough", String(toolDxf.value.z_rough));

    const res = await axios.post("/api/cam/pocket/adaptive/plan_from_dxf", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    const data = res.data;
    // data.request = PlanIn JSON
    // data.plan = actual /plan response
    lastPlan.value = data.plan;
    planStats.value = data.plan?.stats || null;

    const segs = movesToSegments(data.plan?.moves || []);
    previewSegments.value = normalizeSegmentsToView(segs);

    // Optionally reflect request into loopsJson
    loopsJson.value = JSON.stringify(data.request, null, 2);
  } catch (err: any) {
    console.error("DXF adaptive error", err);
    dxfError.value = err?.response?.data?.detail || String(err);
  } finally {
    runningDxf.value = false;
  }
}

/* Demo JSON rectangle */
function loadDemoRect() {
  const demo = {
    loops: [
      { pts: [[0, 0], [100, 0], [100, 60], [0, 60]] }
    ],
    tool_d: 6.0,
  };
  loopsJson.value = JSON.stringify(demo, null, 2);
}

// Phase 28.2: Consume query params for deep linking (preset tracking if needed)
const adaptivePreset = ref<string>("");
const adaptiveLane = ref<string>("adaptive");

usePresetQueryBootstrap({
  onPreset: (p) => {
    adaptivePreset.value = p;
  },
  onLane: (lane) => {
    adaptiveLane.value = lane;
  },
});
</script>
