<template>
  <div class="p-3 space-y-3 text-[11px]">
    <h1 class="text-lg font-semibold text-gray-900 mb-2">
      Relief Kernel Lab
    </h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <!-- LEFT: Controls -->
      <div class="space-y-2">
        <div class="border rounded bg-slate-50 p-2 space-y-1">
          <div class="font-semibold text-gray-900 text-[11px]">
            Heightmap → Relief plan
          </div>
          <div class="text-[10px] text-gray-500">
            Upload a grayscale heightmap and run the relief kernel.
          </div>

          <div class="mt-2 mb-2">
            <ReliefRiskPresetPanel @update="applyPreset" />
          </div>

          <input
            type="file"
            accept="image/*"
            @change="onHeightmapChange"
            class="mt-1 block w-full text-[10px]"
          />

          <div class="grid grid-cols-2 gap-1 text-[10px] mt-1">
            <label class="flex flex-col">
              <span class="text-gray-600">Tool Ø (mm)</span>
              <input
                type="number"
                step="0.1"
                v-model.number="cfg.tool_d"
                class="border rounded px-1 py-0.5"
              />
            </label>
            <label class="flex flex-col">
              <span class="text-gray-600">Stepover</span>
              <input
                type="number"
                step="0.05"
                v-model.number="cfg.stepover"
                class="border rounded px-1 py-0.5"
              />
            </label>
            <label class="flex flex-col">
              <span class="text-gray-600">Stepdown</span>
              <input
                type="number"
                step="0.05"
                v-model.number="cfg.stepdown"
                class="border rounded px-1 py-0.5"
              />
            </label>
            <label class="flex flex-col">
              <span class="text-gray-600">Max depth</span>
              <input
                type="number"
                step="0.1"
                v-model.number="cfg.max_depth"
                class="border rounded px-1 py-0.5"
              />
            </label>
            <label class="flex flex-col">
              <span class="text-gray-600">Scallop (mm)</span>
              <input
                type="number"
                step="0.05"
                v-model.number="cfg.scallop_mm"
                class="border rounded px-1 py-0.5"
              />
            </label>
          </div>

          <button
            type="button"
            class="mt-1 px-2 py-1 rounded bg-blue-600 text-white text-[10px] hover:bg-blue-700 disabled:opacity-50"
            :disabled="!heightmapFile || running"
            @click="runReliefKernel"
          >
            <span v-if="!running">Run Relief Kernel</span>
            <span v-else>Running…</span>
          </button>

          <div v-if="error" class="mt-1 text-[10px] text-red-600">
            {{ error }}
          </div>

          <div v-if="stats" class="mt-2 text-[10px] space-y-0.5">
            <div class="font-semibold text-gray-900 text-[11px]">
              Plan stats
            </div>
            <div>Moves: <span class="font-mono">{{ stats.move_count }}</span></div>
            <div>Area px: <span class="font-mono">{{ stats.area_px }}</span></div>
            <div>High slope hotspots: <span class="font-mono">{{ stats.high_slope_hotspots }}</span></div>
          </div>
        </div>
      </div>

      <!-- RIGHT: Preview -->
      <div class="border rounded bg-white p-2 flex flex-col">
        <div class="flex items-center justify-between mb-1">
          <div class="font-semibold text-gray-900 text-[11px]">
            Relief Toolpath Preview
          </div>
          <div class="text-[10px] text-gray-500">
            {{ previewSegments.length }} segments · {{ overlays.length }} hotspots
          </div>
        </div>

        <div class="flex-1 border bg-slate-900 rounded relative overflow-hidden">
          <svg
            v-if="previewSegments.length"
            viewBox="0 0 100 100"
            preserveAspectRatio="xMidYMid meet"
            class="w-full h-full"
          >
            <polyline
              v-for="(seg, idx) in previewSegments"
              :key="idx"
              :points="segToPoints(seg)"
              fill="none"
              stroke="deepskyblue"
              stroke-width="0.4"
            />
            <!-- hotspots -->
            <circle
              v-for="(o, idx) in overlays"
              :key="'hs-'+idx"
              :cx="o.x"
              :cy="100 - o.y"
              r="1"
              fill="red"
            />
          </svg>

          <div
            v-else
            class="absolute inset-0 flex items-center justify-center text-[10px] text-gray-400"
          >
            Run relief kernel to see preview
          </div>
        </div>

        <details v-if="plan" class="mt-1 text-[10px]">
          <summary class="cursor-pointer text-gray-600">
            Raw plan JSON
          </summary>
          <pre class="mt-1 max-h-48 overflow-auto bg-slate-900 text-slate-100 rounded p-2">
{{ JSON.stringify(plan, null, 2) }}
          </pre>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import axios from "axios";
import ReliefRiskPresetPanel from "@/components/art/ReliefRiskPresetPanel.vue";

type Segment = { x1: number; y1: number; x2: number; y2: number };

const heightmapFile = ref<File | null>(null);
const running = ref(false);
const error = ref<string | null>(null);

const cfg = ref({
  tool_d: 6.0,
  stepover: 0.5,
  stepdown: 0.5,
  max_depth: -3.0,
  scallop_mm: 0.3,
});

const simPreset = ref<any>({});
const stockThickness = ref(5.0);
const scallop = ref(0.3);
const stepdown = ref(0.5);

const stats = ref<any | null>(null);
const plan = ref<any | null>(null);

function applyPreset(payload: { name: string; config: any }) {
  const preset = payload.config || {};
  simPreset.value = { ...preset };

  scallop.value = preset.scallop_height ?? scallop.value;
  stepdown.value = preset.stepdown ?? stepdown.value;
  
  // Update cfg values with preset values
  cfg.value.scallop_mm = preset.scallop_height ?? cfg.value.scallop_mm;
  cfg.value.stepdown = preset.stepdown ?? cfg.value.stepdown;

  // Small visual cue: stockThickness loosely tied to min floor
  if (typeof preset.min_floor_thickness === "number") {
    stockThickness.value = Math.max(
      3,
      Math.round(preset.min_floor_thickness * 8 * 10) / 10
    );
  }
}
const previewSegments = ref<Segment[]>([]);
const overlays = ref<any[]>([]);

function onHeightmapChange(e: Event) {
  const input = e.target as HTMLInputElement;
  heightmapFile.value = input.files?.[0] || null;
  error.value = null;
}

function movesToSegments(moves: any[]): Segment[] {
  const segs: Segment[] = [];
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

function normalizeSegments(segs: Segment[]): Segment[] {
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

function segToPoints(seg: Segment): string {
  return `${seg.x1},${seg.y1} ${seg.x2},${seg.y2}`;
}

async function runReliefKernel() {
  if (!heightmapFile.value) return;
  running.value = true;
  error.value = null;
  try {
    const form = new FormData();
    form.append("file", heightmapFile.value);
    form.append("tool_d", String(cfg.value.tool_d));
    form.append("stepover", String(cfg.value.stepover));
    form.append("stepdown", String(cfg.value.stepdown));
    form.append("max_depth", String(cfg.value.max_depth));
    form.append("scallop_mm", String(cfg.value.scallop_mm));

    const res = await axios.post("/api/cam/relief/heightfield_plan", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    const data = res.data;
    plan.value = data.plan;
    stats.value = data.plan?.stats || null;
    overlays.value = data.plan?.overlays || [];

    const segs = movesToSegments(data.plan?.moves || []);
    previewSegments.value = normalizeSegments(segs);
  } catch (err: any) {
    console.error("Relief kernel error", err);
    error.value = err?.response?.data?.detail || String(err);
  } finally {
    running.value = false;
  }
}
</script>
