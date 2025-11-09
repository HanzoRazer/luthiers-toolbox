<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  planAdaptive,
  type AdaptivePlanIn,
  type AdaptivePlanOut,
  type Loop,
} from "@/api/adaptive";

const ADAPTIVE_PIPELINE_PRESET_KEY = "ltb_pipeline_adaptive_preset_v1";

const units = ref<"mm" | "inch">("mm");
const toolD = ref(6.0);
const stepover = ref(0.45);
const stepdown = ref(2.0);
const margin = ref(0.5);
const strategy = ref<"Spiral" | "Lanes">("Spiral");
const feedXY = ref(1200);
const safeZ = ref(5.0);
const zRough = ref(-1.5);

const cornerRadiusMin = ref(1.0);
const targetStepover = ref(0.45);
const slowdownFeedPct = ref(60.0);

const useTrochoids = ref(false);
const trochoidRadius = ref(1.5);
const trochoidPitch = ref(3.0);

const loopsText = ref<string>("");
const lastRequest = ref<AdaptivePlanIn | null>(null);
const result = ref<AdaptivePlanOut | null>(null);
const errorMsg = ref<string | null>(null);
const busy = ref(false);

const showPipelineSnippet = ref(false);
const sentToPipeline = ref(false);
const showToolpathPreview = ref(true);

// Demo rectangle loop (100x60 with one island)
function loadDemoLoops() {
  const demo: Loop[] = [
    {
      pts: [
        [0, 0],
        [100, 0],
        [100, 60],
        [0, 60],
      ],
    },
    {
      pts: [
        [30, 15],
        [70, 15],
        [70, 45],
        [30, 45],
      ],
    },
  ];
  loopsText.value = JSON.stringify(demo, null, 2);
}

function buildPayload(): AdaptivePlanIn {
  let loops: Loop[];
  try {
    const parsed = JSON.parse(loopsText.value || "[]");
    if (!Array.isArray(parsed)) throw new Error("loops must be an array");
    loops = parsed;
  } catch (e: any) {
    throw new Error(
      'Invalid loops JSON. It must be an array like: [{"pts": [[0,0],[100,0],...]}]\n' +
        (e?.message || String(e))
    );
  }

  if (!loops.length) {
    throw new Error("At least one loop is required.");
  }

  return {
    loops,
    units: units.value,
    tool_d: toolD.value,
    stepover: stepover.value,
    stepdown: stepdown.value,
    margin: margin.value,
    strategy: strategy.value,
    smoothing: 0.5,
    climb: true,
    feed_xy: feedXY.value,
    safe_z: safeZ.value,
    z_rough: zRough.value,
    corner_radius_min: cornerRadiusMin.value,
    target_stepover: targetStepover.value,
    slowdown_feed_pct: slowdownFeedPct.value,
    use_trochoids: useTrochoids.value,
    trochoid_radius: trochoidRadius.value,
    trochoid_pitch: trochoidPitch.value,
    jerk_aware: false,
    machine_feed_xy: feedXY.value,
    machine_rapid: 3000,
    machine_accel: 800,
    machine_jerk: 2000,
    corner_tol_mm: 0.2,
    machine_profile_id: null,
    adopt_overrides: false,
    session_override_factor: null,
  };
}

async function runAdaptive() {
  errorMsg.value = null;
  busy.value = true;
  result.value = null;
  try {
    const payload = buildPayload();
    lastRequest.value = payload;
    const res = await planAdaptive(payload);
    result.value = res;
  } catch (e: any) {
    errorMsg.value = e?.message || String(e);
  } finally {
    busy.value = false;
  }
}

// Pipeline snippet generation
const pipelineSnippet = computed<string>(() => {
  try {
    const plan = buildPayload();

    // Strip loops for pipeline input (loops come from DXF in pipeline world)
    const {
      loops, // eslint-disable-line @typescript-eslint/no-unused-vars
      ...inputForPipeline
    } = plan as any;

    const skeleton = {
      design: {
        source: "dxf",
        dxf_path: "workspace/bodies/body01.dxf", // change per job
        units: plan.units,
      },
      context: {
        machine_profile_id: "GUITAR_CNC_01",
        post_preset: "GRBL",
        workspace_id: "body01_session",
      },
      ops: [
        {
          id: "body_adaptive_pocket",
          op: "AdaptivePocket",
          from_layer: "GEOMETRY",
          input: {
            tool_d: inputForPipeline.tool_d,
            stepover: inputForPipeline.stepover,
            stepdown: inputForPipeline.stepdown,
            margin: inputForPipeline.margin,
            strategy: inputForPipeline.strategy,
            smoothing: inputForPipeline.smoothing,
            climb: inputForPipeline.climb,
            feed_xy: inputForPipeline.feed_xy,
            safe_z: inputForPipeline.safe_z,
            z_rough: inputForPipeline.z_rough,
            corner_radius_min: inputForPipeline.corner_radius_min,
            target_stepover: inputForPipeline.target_stepover,
            slowdown_feed_pct: inputForPipeline.slowdown_feed_pct,
            use_trochoids: inputForPipeline.use_trochoids,
            trochoid_radius: inputForPipeline.trochoid_radius,
            trochoid_pitch: inputForPipeline.trochoid_pitch,
            jerk_aware: inputForPipeline.jerk_aware,
            machine_feed_xy: inputForPipeline.machine_feed_xy,
            machine_rapid: inputForPipeline.machine_rapid,
            machine_accel: inputForPipeline.machine_accel,
            machine_jerk: inputForPipeline.machine_jerk,
            corner_tol_mm: inputForPipeline.corner_tol_mm,
            machine_profile_id: inputForPipeline.machine_profile_id,
            adopt_overrides: inputForPipeline.adopt_overrides,
            session_override_factor: inputForPipeline.session_override_factor,
          },
        },
      ],
    };

    return JSON.stringify(skeleton, null, 2);
  } catch (e: any) {
    return (
      "// Unable to build pipeline snippet.\n" +
      "// Fix loops JSON or parameters first.\n" +
      "// Error: " +
      (e?.message || String(e))
    );
  }
});

function sendToPipelineLab() {
  const snippet = pipelineSnippet.value;
  if (!snippet || snippet.startsWith("// Unable to build")) {
    sentToPipeline.value = false;
    errorMsg.value =
      "Cannot send to PipelineLab: fix loops / params so the pipeline snippet is valid first.";
    return;
  }
  try {
    localStorage.setItem(ADAPTIVE_PIPELINE_PRESET_KEY, snippet);
    sentToPipeline.value = true;
  } catch (e: any) {
    sentToPipeline.value = false;
    errorMsg.value =
      "Failed to store preset in localStorage: " + (e?.message || String(e));
  }
}

// ---------- Simple 2D preview ----------

type PreviewLoop = { pts: [number, number][] };

const previewLoops = computed<PreviewLoop[]>(() => {
  try {
    const parsed = JSON.parse(loopsText.value || "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed.map((l: any) => ({
      pts: (l.pts || []).map((p: any) => [Number(p[0]), Number(p[1])]) as [
        number,
        number
      ][],
    }));
  } catch {
    return [];
  }
});

const previewOverlays = computed(() => result.value?.overlays || []);

const viewBox = computed(() => {
  const loops = previewLoops.value;
  if (!loops.length) return { x: 0, y: 0, w: 100, h: 60 };

  const xs: number[] = [];
  const ys: number[] = [];
  loops.forEach((l) =>
    l.pts.forEach(([x, y]) => {
      xs.push(x);
      ys.push(y);
    })
  );
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const pad = 5;
  return {
    x: minX - pad,
    y: minY - pad,
    w: maxX - minX + 2 * pad,
    h: maxY - minY + 2 * pad,
  };
});

function overlayColor(o: any): string {
  if (o.type === "tight_radius") {
    if (o.severity === "high") return "#ef4444";
    if (o.severity === "medium") return "#f97316";
    return "#facc15";
  }
  if (o.type === "slowdown") return "#3b82f6";
  return "#22c55e";
}

// Toolpath preview from result.moves
type ToolpathSegment = {
  pts: [number, number][];
  kind: "rapid" | "cut";
};

const previewToolpathSegments = computed<ToolpathSegment[]>(() => {
  const r = result.value;
  if (!r || !Array.isArray(r.moves)) return [];

  const segments: ToolpathSegment[] = [];
  let current: [number, number][] = [];
  let currentKind: "rapid" | "cut" | null = null;

  const moves = r.moves as any[];

  for (const mv of moves) {
    const x = mv.x;
    const y = mv.y;

    if (typeof x !== "number" || typeof y !== "number") {
      // break path when there's no XY
      if (current.length > 1 && currentKind) {
        segments.push({ pts: current, kind: currentKind });
      }
      current = [];
      currentKind = null;
      continue;
    }

    // classify move kind: simple heuristic
    const code = (mv.code || "").toUpperCase();
    const z = typeof mv.z === "number" ? mv.z : null;

    let kind: "rapid" | "cut";
    if (code === "G0" || (z !== null && z > 0)) {
      kind = "rapid";
    } else {
      kind = "cut";
    }

    // if kind changes, finalize previous segment
    if (currentKind !== null && kind !== currentKind && current.length > 1) {
      segments.push({ pts: current, kind: currentKind });
      current = [];
    }

    currentKind = kind;
    current.push([x, y]);
  }

  if (current.length > 1 && currentKind) {
    segments.push({ pts: current, kind: currentKind });
  }

  return segments;
});

// Initialize with demo loops on mount
onMounted(() => {
  if (!loopsText.value) {
    loadDemoLoops();
  }
});
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold">Adaptive Kernel Dev Lab</h1>
    <p class="text-sm text-gray-600">
      Direct playground for
      <code>/api/cam/pocket/adaptive/plan</code>. Edit loops, adjust parameters,
      inspect stats, and view overlays before wiring into the unified pipeline.
    </p>

    <!-- Controls -->
    <section class="border rounded p-4 bg-white space-y-4">
      <div class="flex items-center justify-between gap-2">
        <h2 class="font-semibold text-lg">Parameters</h2>
        <button
          class="border rounded px-3 py-1 text-xs hover:bg-gray-50"
          type="button"
          @click="loadDemoLoops"
        >
          Load Demo Rectangle
        </button>
      </div>

      <div class="grid gap-3 md:grid-cols-4 text-sm">
        <label class="flex flex-col gap-1">
          Units
          <select v-model="units" class="border rounded px-2 py-1">
            <option value="mm">mm</option>
            <option value="inch">inch</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          Tool Ø
          <input
            v-model.number="toolD"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex flex-col gap-1">
          Stepover
          <input
            v-model.number="stepover"
            type="number"
            step="0.01"
            class="border rounded px-2 py-1"
          />
          <span class="text-[10px] text-gray-500">fraction of tool_d</span>
        </label>
        <label class="flex flex-col gap-1">
          Stepdown
          <input
            v-model.number="stepdown"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex flex-col gap-1">
          Margin
          <input
            v-model.number="margin"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex flex-col gap-1">
          Strategy
          <select v-model="strategy" class="border rounded px-2 py-1">
            <option value="Spiral">Spiral</option>
            <option value="Lanes">Lanes</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          Feed XY
          <input
            v-model.number="feedXY"
            type="number"
            step="10"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex flex-col gap-1">
          Safe Z
          <input
            v-model.number="safeZ"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex flex-col gap-1">
          Rough Z
          <input
            v-model.number="zRough"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          />
        </label>
      </div>

      <div class="grid gap-3 md:grid-cols-4 text-sm pt-2">
        <label class="flex flex-col gap-1">
          Corner R min
          <input
            v-model.number="cornerRadiusMin"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex flex-col gap-1">
          Target stepover
          <input
            v-model.number="targetStepover"
            type="number"
            step="0.01"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex flex-col gap-1">
          Slowdown feed %
          <input
            v-model.number="slowdownFeedPct"
            type="number"
            step="1"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex items-center gap-2 mt-6 text-sm">
          <input type="checkbox" v-model="useTrochoids" />
          Use trochoids
        </label>
        <label class="flex flex-col gap-1">
          Trochoid R
          <input
            v-model.number="trochoidRadius"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          />
        </label>
        <label class="flex flex-col gap-1">
          Trochoid pitch
          <input
            v-model.number="trochoidPitch"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          />
        </label>
      </div>

      <button
        class="border rounded px-4 py-2 text-sm font-semibold hover:bg-gray-50"
        :disabled="busy"
        type="button"
        @click="runAdaptive"
      >
        {{ busy ? "Running..." : "Run Adaptive Kernel" }}
      </button>

      <p v-if="errorMsg" class="text-sm text-red-600">
        {{ errorMsg }}
      </p>
    </section>

    <!-- Loops JSON editor + preview -->
    <section class="border rounded p-4 bg-white space-y-4">
      <h2 class="font-semibold text-lg">Loops & Overlays</h2>
      <div class="grid gap-4 md:grid-cols-2">
        <div class="flex flex-col gap-2 text-sm">
          <label class="font-semibold">Loops JSON</label>
          <p class="text-[11px] text-gray-500">
            Array of <code>{ pts: [[x,y], ...] }</code>. Demo button above
            fills in a rectangular pocket with an island.
          </p>
          <textarea
            v-model="loopsText"
            class="border rounded px-2 py-1 text-xs font-mono min-h-[220px]"
          ></textarea>
        </div>

        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label class="font-semibold text-sm">2D Preview</label>
            <div class="flex items-center gap-3 text-[11px] text-gray-600">
              <label class="inline-flex items-center gap-1">
                <input type="checkbox" v-model="showToolpathPreview" />
                <span>Show toolpath preview</span>
              </label>
            </div>
          </div>
          <div
            class="border rounded bg-gray-50 flex items-center justify-center min-h-[220px]"
          >
            <svg
              v-if="previewLoops.length"
              :viewBox="`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`"
              class="w-full h-full"
            >
              <!-- pocket loops -->
              <g fill="none" stroke="#0f766e" stroke-width="0.3">
                <polyline
                  v-for="(loop, idx) in previewLoops"
                  :key="idx"
                  :points="loop.pts.map(([x,y]: any) => `${x},${y}`).join(' ')"
                />
              </g>

              <!-- toolpath preview -->
              <g
                v-if="showToolpathPreview && previewToolpathSegments.length"
                fill="none"
              >
                <polyline
                  v-for="(seg, idx) in previewToolpathSegments"
                  :key="`tp-${idx}`"
                  :points="seg.pts.map(([x,y]) => `${x},${y}`).join(' ')"
                  :stroke="seg.kind === 'rapid' ? '#9ca3af' : '#1d4ed8'"
                  :stroke-width="seg.kind === 'rapid' ? 0.2 : 0.35"
                  :stroke-dasharray="seg.kind === 'rapid' ? '1,1' : 'none'"
                />
              </g>

              <!-- overlays -->
              <g v-if="previewOverlays.length">
                <circle
                  v-for="(o, idx) in previewOverlays"
                  :key="`ov-${idx}`"
                  :cx="o.x"
                  :cy="o.y"
                  :r="(o.radius || 2)"
                  :fill="overlayColor(o)"
                  fill-opacity="0.35"
                  stroke="#111827"
                  stroke-width="0.2"
                />
              </g>
            </svg>
            <div v-else class="text-xs text-gray-500">
              No loops to display. Load demo or paste JSON.
            </div>
          </div>
          
          <div class="flex gap-3 text-[11px] text-gray-500">
            <div class="inline-flex items-center gap-1">
              <span class="inline-block w-4 h-[2px] bg-[#0f766e]"></span>
              <span>Boundary loops</span>
            </div>
            <div class="inline-flex items-center gap-1">
              <span class="inline-block w-4 h-[2px] bg-[#1d4ed8]"></span>
              <span>Cut moves</span>
            </div>
            <div class="inline-flex items-center gap-1">
              <span
                class="inline-block w-4 h-[2px]"
                style="border-bottom:1px dashed #9ca3af"
              ></span>
              <span>Rapid moves</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats + raw JSON -->
    <section v-if="result" class="border rounded p-4 bg-white space-y-4">
      <h2 class="font-semibold text-lg">Kernel Output</h2>
      <div class="grid gap-4 md:grid-cols-2 text-xs">
        <div class="space-y-1">
          <h3 class="font-semibold text-sm">Stats</h3>
          <p v-if="result.stats.length_mm != null">
            <b>Length:</b> {{ result.stats.length_mm.toFixed?.(1) ?? result.stats.length_mm }}
            mm
          </p>
          <p v-if="result.stats.area_mm2 != null">
            <b>Area:</b> {{ result.stats.area_mm2.toFixed?.(1) ?? result.stats.area_mm2 }}
            mm²
          </p>
          <p v-if="result.stats.time_s != null">
            <b>Time:</b> {{ result.stats.time_s.toFixed?.(1) ?? result.stats.time_s }}
            s
          </p>
          <p v-if="result.stats.time_jerk_s != null">
            <b>Time (jerk-aware):</b> {{ result.stats.time_jerk_s.toFixed?.(1) ?? result.stats.time_jerk_s }}
            s
          </p>
          <p v-if="result.stats.volume_mm3 != null">
            <b>Volume:</b> {{ result.stats.volume_mm3.toFixed?.(1) ?? result.stats.volume_mm3 }}
            mm³
          </p>
          <p v-if="result.stats.move_count != null">
            <b>Moves:</b> {{ result.stats.move_count }}
          </p>
          <p v-if="result.stats.tight_count != null">
            <b>Tight segments:</b> {{ result.stats.tight_count }}
          </p>
          <p v-if="result.stats.trochoid_count != null">
            <b>Trochoid arcs:</b> {{ result.stats.trochoid_count }}
          </p>
        </div>
        <div>
          <details>
            <summary class="cursor-pointer text-sm font-semibold">
              Raw Output JSON
            </summary>
            <pre class="bg-gray-50 p-2 rounded mt-2 whitespace-pre-wrap text-[10px]">
{{ JSON.stringify(result, null, 2) }}
            </pre>
          </details>
          <details v-if="lastRequest">
            <summary class="cursor-pointer text-sm font-semibold mt-2">
              Last Request JSON
            </summary>
            <pre class="bg-gray-50 p-2 rounded mt-2 whitespace-pre-wrap text-[10px]">
{{ JSON.stringify(lastRequest, null, 2) }}
            </pre>
          </details>
        </div>
      </div>
    </section>

    <!-- Pipeline op export -->
    <section class="border rounded p-4 bg-white space-y-2">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-lg">Export as Pipeline Op</h2>
        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" v-model="showPipelineSnippet" />
          <span>Show pipeline snippet</span>
        </label>
      </div>

      <p class="text-xs text-gray-600">
        When enabled, this shows a ready-to-paste JSON skeleton for
        <code>/api/pipeline/run</code> using an
        <code>AdaptivePocket</code> op. Update
        <code>dxf_path</code>, <code>machine_profile_id</code>, and
        <code>workspace_id</code> per job.
      </p>

      <div v-if="showPipelineSnippet" class="space-y-2">
        <textarea
          readonly
          class="border rounded px-2 py-1 text-xs font-mono w-full min-h-[180px] bg-gray-50"
        >{{ pipelineSnippet }}</textarea>

        <div class="flex items-center justify-between mt-1">
          <button
            type="button"
            class="border rounded px-3 py-1 text-xs font-semibold hover:bg-gray-50"
            @click="sendToPipelineLab"
          >
            Send to PipelineLab
          </button>
          <span
            v-if="sentToPipeline"
            class="text-[11px] text-green-600"
          >
            Preset sent. Open <code>/lab/pipeline</code> to use it.
          </span>
        </div>
      </div>
    </section>
  </div>
</template>
