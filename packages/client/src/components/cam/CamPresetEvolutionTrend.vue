<!-- CamPresetEvolutionTrend.vue - Phase 26.6 -->
<!-- Self-contained SVG time-series chart (zero deps) for preset evolution tracking -->
<template>
  <div class="border rounded bg-white p-3 text-xs">
    <div class="flex items-center justify-between mb-2">
      <div class="font-semibold text-gray-700">
        Preset Evolution Trend — {{ modeLabel }}
      </div>
      <div class="flex items-center gap-2">
        <select
          v-model="bucketMode"
          class="border rounded px-2 py-1 text-[11px]"
        >
          <option value="week">
            Week
          </option>
          <option value="version">
            Version
          </option>
        </select>
        <button
          type="button"
          class="text-[11px] px-2 py-1 border rounded bg-gray-50 hover:bg-gray-100"
          @click="$emit('export-series-csv', csvText)"
        >
          Export Series CSV
        </button>
      </div>
    </div>

    <div
      v-if="points.A.length === 0"
      class="text-[11px] text-gray-500"
    >
      Not enough data to plot.
    </div>

    <div
      v-else
      class="w-full h-48"
    >
      <svg
        class="w-full h-full"
        viewBox="0 0 100 60"
        preserveAspectRatio="none"
      >
        <!-- Plot area box -->
        <rect
          x="8"
          y="6"
          width="86"
          height="46"
          fill="#ffffff"
          stroke="#e5e7eb"
          stroke-width="0.4"
        />

        <!-- Y grid lines -->
        <g
          v-for="(gy, i) in yGridLines"
          :key="'y'+i"
        >
          <line
            :x1="8"
            :x2="94"
            :y1="gy"
            :y2="gy"
            stroke="#f1f5f9"
            stroke-width="0.3"
          />
        </g>

        <!-- A line (blue) -->
        <polyline
          v-if="polyA"
          :points="polyA"
          fill="none"
          stroke="#2563eb"
          stroke-width="0.9"
        />
        <!-- B line (rose) -->
        <polyline
          v-if="polyB"
          :points="polyB"
          fill="none"
          stroke="#e11d48"
          stroke-width="0.9"
        />

        <!-- Last point markers -->
        <circle
          v-if="lastA"
          :cx="lastA.x"
          :cy="lastA.y"
          r="1.1"
          fill="#1d4ed8"
        />
        <circle
          v-if="lastB"
          :cx="lastB.x"
          :cy="lastB.y"
          r="1.1"
          fill="#be123c"
        />

        <!-- X labels -->
        <g
          v-for="(t, idx) in tickLabels"
          :key="'t'+idx"
        >
          <text
            :x="t.x"
            y="56.3"
            text-anchor="middle"
            font-size="2.1"
            fill="#6b7280"
          >
            {{ t.label }}
          </text>
        </g>

        <!-- Y labels -->
        <g
          v-for="(ly, idx) in yLabelObjs"
          :key="'ly'+idx"
        >
          <text
            x="5.8"
            :y="ly.y"
            text-anchor="end"
            font-size="2.1"
            fill="#6b7280"
          >{{ ly.text }}</text>
        </g>

        <!-- Legend -->
        <g>
          <rect
            x="8"
            y="2.5"
            width="86"
            height="3.5"
            fill="transparent"
          />
          <circle
            cx="14"
            cy="4.2"
            r="0.9"
            fill="#2563eb"
          />
          <text
            x="16.5"
            y="4.7"
            font-size="2.4"
            fill="#1f2937"
          >A risk</text>
          <circle
            cx="30"
            cy="4.2"
            r="0.9"
            fill="#e11d48"
          />
          <text
            x="32.5"
            y="4.7"
            font-size="2.4"
            fill="#1f2937"
          >B risk</text>
          <text
            x="88"
            y="4.7"
            font-size="2.2"
            text-anchor="end"
            :fill="deltaColor"
          >
            Δ (B−A): {{ lastDeltaStr }}
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

type SeverityCounts = { critical?: number };
interface RiskJob {
  id: string;
  analytics?: { risk_score?: number; severity_counts?: SeverityCounts };
  meta?: { preset?: { name?: string }; version?: string };
  pipeline_id?: string;
  created_at?: string;
  timestamp?: string;
}

const props = defineProps<{
  jobsA: RiskJob[];
  jobsB: RiskJob[];
  initialBucketMode?: "week" | "version";
}>();
defineEmits<{
  (e: "export-series-csv", csv: string): void;
}>();

const bucketMode = ref<"week" | "version">(props.initialBucketMode ?? "week");
const modeLabel = computed(() => (bucketMode.value === "week" ? "Weekly" : "Versioned"));

// --- helpers
function jobDate(j: RiskJob) {
  const raw = j.created_at || j.timestamp;
  if (!raw) return null;
  const d = new Date(raw);
  return Number.isNaN(d.getTime()) ? null : d;
}

// ISO year-week label "YYYY-Www"
function isoWeekLabel(d: Date): string {
  const date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  // Thursday of this week used to determine week number
  const dayNum = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil((((date as any) - (yearStart as any)) / 86400000 + 1) / 7);
  return `${date.getUTCFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

type Bucket = { key: string; ts?: number; aVals: number[]; bVals: number[] };
function bucketize(jobsA: RiskJob[], jobsB: RiskJob[], mode: "week" | "version"): Bucket[] {
  const map = new Map<string, Bucket>();

  function add(j: RiskJob, which: "A" | "B") {
    let key = "unknown";
    let ts: number | undefined = undefined;
    if (mode === "week") {
      const d = jobDate(j);
      if (d) {
        key = isoWeekLabel(d);
        ts = +new Date(d.getFullYear(), d.getMonth(), d.getDate());
      } else {
        key = "unknown";
      }
    } else {
      key = j.meta?.version || "v0";
    }
    if (!map.has(key)) map.set(key, { key, ts, aVals: [], bVals: [] });
    const b = map.get(key)!;
    const risk = j.analytics?.risk_score ?? 0;
    if (which === "A") b.aVals.push(risk);
    else b.bVals.push(risk);
  }

  for (const ja of jobsA) add(ja, "A");
  for (const jb of jobsB) add(jb, "B");

  const buckets = Array.from(map.values());
  // sort by ts if present, else key
  buckets.sort((u, v) => {
    if (u.ts != null && v.ts != null) return u.ts - v.ts;
    return u.key.localeCompare(v.key);
  });
  return buckets;
}

const series = computed(() => {
  const bks = bucketize(props.jobsA, props.jobsB, bucketMode.value);
  // produce merged series with avg A, avg B, delta
  return bks.map((b) => {
    const aAvg = b.aVals.length ? b.aVals.reduce((s, v) => s + v, 0) / b.aVals.length : 0;
    const bAvg = b.bVals.length ? b.bVals.reduce((s, v) => s + v, 0) / b.bVals.length : 0;
    return { key: b.key, a: aAvg, b: bAvg, d: bAvg - aAvg };
  });
});

const yDomain = computed(() => {
  let min = Number.POSITIVE_INFINITY;
  let max = Number.NEGATIVE_INFINITY;
  for (const r of series.value) {
    min = Math.min(min, r.a, r.b);
    max = Math.max(max, r.a, r.b);
  }
  if (!isFinite(min) || !isFinite(max)) return { min: 0, max: 1 };
  if (min === max) {
    min -= 0.5;
    max += 0.5;
  }
  return { min, max };
});

const points = computed(() => {
  const N = series.value.length;
  if (!N) return { A: [], B: [], ticks: [] as { x: number; label: string }[] };

  const x0 = 8,
    x1 = 94,
    y0 = 52,
    y1 = 6;
  const xrange = x1 - x0;
  const yrange = y0 - y1;
  const { min, max } = yDomain.value;

  function xy(i: number, val: number) {
    const x = x0 + (N === 1 ? xrange / 2 : (i / (N - 1)) * xrange);
    const yNorm = (val - min) / (max - min);
    const y = y0 - yNorm * yrange;
    return { x, y };
  }

  const A = series.value.map((r, i) => xy(i, r.a));
  const B = series.value.map((r, i) => xy(i, r.b));
  const ticks = series.value.map((r, i) => ({
    x: x0 + (N === 1 ? xrange / 2 : (i / (N - 1)) * xrange),
    label: r.key,
  }));
  return { A, B, ticks };
});

const polyA = computed(() => points.value.A.map((p) => `${p.x},${p.y}`).join(" "));
const polyB = computed(() => points.value.B.map((p) => `${p.x},${p.y}`).join(" "));

const lastA = computed(() => points.value.A.slice(-1)[0] || null);
const lastB = computed(() => points.value.B.slice(-1)[0] || null);
const lastDelta = computed(() => {
  const r = series.value.slice(-1)[0];
  return r ? r.d : 0;
});
const lastDeltaStr = computed(() => {
  const d = lastDelta.value;
  const s = d.toFixed(2);
  return (d > 0 ? "+" : d < 0 ? "" : "±") + s;
});
const deltaColor = computed(() =>
  lastDelta.value > 0 ? "#dc2626" : lastDelta.value < 0 ? "#16a34a" : "#6b7280"
);

// Y grid & labels
const yGridLines = computed(() => {
  const lines: number[] = [];
  const steps = 4;
  for (let i = 1; i <= steps; i++) {
    const frac = i / (steps + 1);
    // back-project y
    const y = 52 - frac * (52 - 6);
    lines.push(y);
  }
  return lines;
});
const yLabelObjs = computed(() => {
  const out: { y: number; text: string }[] = [];
  const { min, max } = yDomain.value;
  const steps = 4;
  for (let i = 0; i <= steps; i++) {
    const frac = i / steps;
    const y = 52 - frac * (52 - 6);
    const val = min + frac * (max - min);
    out.push({ y: y + 0.8, text: val.toFixed(1) });
  }
  return out;
});

const tickLabels = computed(() => {
  // show at most ~8 labels to avoid clutter
  const ticks = points.value.ticks;
  if (ticks.length <= 8) return ticks;
  const stride = Math.ceil(ticks.length / 8);
  return ticks
    .map((t, i) => ({ ...t, keep: i % stride === 0 }))
    .filter((t) => (t as any).keep)
    .map(({ x, label }) => ({ x, label }));
});

// CSV exporter
const csvText = computed(() => {
  const header = ["bucket", "avg_risk_A", "avg_risk_B", "delta_B_minus_A"];
  const rows = series.value.map((r) =>
    [r.key, r.a.toFixed(4), r.b.toFixed(4), (r.d >= 0 ? "+" : "") + r.d.toFixed(4)].join(",")
  );
  return [header.join(","), ...rows].join("\r\n");
});

// keep chart mode in sync with parent toggles if needed
watch(
  () => props.initialBucketMode,
  (m) => {
    if (m) bucketMode.value = m;
  }
);
</script>
