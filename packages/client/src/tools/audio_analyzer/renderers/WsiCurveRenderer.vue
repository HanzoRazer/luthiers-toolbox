<template>
  <div class="wsi-curve-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
      <div class="controls">
        <label class="toggle">
          <input type="checkbox" v-model="showCohMean" />
          <span>coh_mean</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="showPhaseDisorder" />
          <span>phase_disorder</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="shadeAdmissible" />
          <span>Admissible shading</span>
        </label>
        <button class="btn" @click="downloadChart">📷 PNG</button>
      </div>
    </div>

    <div v-if="parseError" class="error">
      <strong>Parse Error:</strong> {{ parseError }}
    </div>
    <div v-else class="chart-container">
      <canvas ref="chartCanvas"></canvas>
    </div>

    <div class="stats">
      <span v-if="rows.length > 0"><strong>Rows:</strong> {{ rows.length }}</span>
      <span v-if="freqRange"><strong>Range:</strong> {{ freqRange }}</span>
      <span v-if="maxWsiHz !== null"><strong>Max WSI:</strong> {{ maxWsi.toFixed(3) }} @ {{ maxWsiHz.toFixed(1) }} Hz</span>
      <span v-if="selectedNearest !== null" class="selected">
        <strong>Nearest:</strong> {{ selectedNearest.freq_hz.toFixed(2) }} Hz → wsi {{ selectedNearest.wsi.toFixed(3) }}
      </span>
      <span v-if="selectedNearest !== null" class="selected muted">
        (exporter fields; nearest sample)
      </span>
    </div>

    <details class="raw" v-if="rows.length > 0">
      <summary class="raw-summary">Raw rows (first 25)</summary>
      <pre class="raw-pre">{{ rawPreview }}</pre>
    </details>
  </div>
</template>

<script setup lang="ts">
/**
 * GOVERNANCE NOTE — WSI CURVE RENDERER
 *
 * This renderer displays the exported Wolf Stress Index (WSI) curve exactly
 * as provided by tap-tone-pi. Its role is visual correlation only.
 *
 * Allowed:
 * - Plotting exporter-provided fields (freq_hz, wsi, coh_mean, phase_disorder, etc.)
 * - Shading using the exporter-provided `admissible` boolean
 * - Emitting a frequency cursor on click (freqHz only; no point context)
 *
 * Prohibited:
 * - Computing thresholds, scores, rankings, or "risk" indicators
 * - Comparing WSI values to peaks, modes, or other datasets
 * - Inferring wolf likelihood, severity, or recommendations
 *
 * Any logic that derives meaning beyond displaying exported measurements
 * constitutes interpretation and is OUT OF SCOPE for Wave 6B.1.
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import type { RendererProps } from "./types";

Chart.register(LineController, LineElement, PointElement, LinearScale, Title, Tooltip, Legend, Filler);

type PeakSelectedPayload = {
  spectrumRelpath: string; // for viewer compatibility (still used even though this isn't a spectrum file)
  peakIndex: number;       // -1 for WSI
  freq_hz: number;
  label?: string;
  raw: unknown;
};

const props = defineProps<RendererProps & { selectedFreqHz?: number | null }>();
const emit = defineEmits<{
  (e: "peak-selected", payload: PeakSelectedPayload): void;
}>();

const chartCanvas = ref<HTMLCanvasElement | null>(null);
let chartInstance: Chart | null = null;

const showCohMean = ref(true);
const showPhaseDisorder = ref(true);
const shadeAdmissible = ref(true);
const parseError = ref<string | null>(null);
const emphasizeSelectionPoint = ref(true);

type WsiRow = {
  freq_hz: number;
  wsi: number;
  loc: number;
  grad: number;
  phase_disorder: number;
  coh_mean: number;
  admissible: boolean;
};

function parseBool(v: string): boolean {
  const s = (v ?? "").trim().toLowerCase();
  return s === "true" || s === "1" || s === "yes" || s === "y";
}

const rows = computed<WsiRow[]>(() => {
  parseError.value = null;
  try {
    const text = new TextDecoder("utf-8").decode(props.bytes);
    const lines = text.trim().split(/\r?\n/);
    if (lines.length < 2) {
      parseError.value = "CSV has no data rows";
      return [];
    }

    const header = lines[0].split(",").map((h) => h.trim().toLowerCase());
    const idx = (name: string) => header.findIndex((h) => h === name);

    const freqIdx = idx("freq_hz");
    const wsiIdx = idx("wsi");
    const locIdx = idx("loc");
    const gradIdx = idx("grad");
    const phaseIdx = idx("phase_disorder");
    const cohIdx = idx("coh_mean");
    const admIdx = idx("admissible");

    // Only freq_hz and wsi are required for charting
    if (freqIdx === -1 || wsiIdx === -1) {
      parseError.value = `Missing required columns. Found: ${header.join(", ")}`;
      return [];
    }

    const out: WsiRow[] = [];
    for (let i = 1; i < lines.length; i++) {
      const cells = lines[i].split(",");
      const freq = parseFloat(cells[freqIdx]);
      const wsi = parseFloat(cells[wsiIdx]);
      if (!Number.isFinite(freq) || !Number.isFinite(wsi)) continue;

      const loc = locIdx >= 0 ? parseFloat(cells[locIdx]) : 0;
      const grad = gradIdx >= 0 ? parseFloat(cells[gradIdx]) : 0;
      const phase_disorder = phaseIdx >= 0 ? parseFloat(cells[phaseIdx]) : 0;
      const coh_mean = cohIdx >= 0 ? parseFloat(cells[cohIdx]) : 0;
      const admissible = admIdx >= 0 ? parseBool(cells[admIdx]) : false;

      out.push({
        freq_hz: freq,
        wsi: wsi,
        loc: Number.isFinite(loc) ? loc : 0,
        grad: Number.isFinite(grad) ? grad : 0,
        phase_disorder: Number.isFinite(phase_disorder) ? phase_disorder : 0,
        coh_mean: Number.isFinite(coh_mean) ? coh_mean : 0,
        admissible,
      });
    }

    // Ensure increasing freq for sane charting
    out.sort((a, b) => a.freq_hz - b.freq_hz);
    return out;
  } catch (e: unknown) {
    parseError.value = e instanceof Error ? e.message : String(e);
    return [];
  }
});

const freqRange = computed(() => {
  if (rows.value.length === 0) return null;
  const min = rows.value[0].freq_hz;
  const max = rows.value[rows.value.length - 1].freq_hz;
  return `${min.toFixed(0)}–${max.toFixed(0)} Hz`;
});

const maxWsiHz = computed<number | null>(() => {
  if (rows.value.length === 0) return null;
  let best = rows.value[0];
  for (const r of rows.value) if (r.wsi > best.wsi) best = r;
  return best.freq_hz;
});
const maxWsi = computed<number>(() => {
  if (rows.value.length === 0) return 0;
  return Math.max(...rows.value.map((r) => r.wsi));
});

function nearestRowByFreq(freqHz: number): WsiRow | null {
  const r = rows.value;
  if (r.length === 0) return null;
  let best = r[0];
  let bestD = Math.abs(r[0].freq_hz - freqHz);
  for (const row of r) {
    const d = Math.abs(row.freq_hz - freqHz);
    if (d < bestD) {
      bestD = d;
      best = row;
    }
  }
  return best;
}

const selectedNearest = computed<WsiRow | null>(() => {
  const f = props.selectedFreqHz ?? null;
  if (!f || !Number.isFinite(f)) return null;
  return nearestRowByFreq(f);
});

function boolText(v: boolean): string {
  return v ? "true" : "false";
}

function nearestRowByLabel(label: any): WsiRow | null {
  const f = Number(label);
  if (!Number.isFinite(f)) return null;
  return nearestRowByFreq(f);
}

const rawPreview = computed(() => {
  const slice = rows.value.slice(0, 25);
  return JSON.stringify(slice, null, 2);
});

function createChart() {
  if (!chartCanvas.value) return;
  if (rows.value.length === 0) return;

  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  const xs = rows.value.map((r) => r.freq_hz);
  const wsiData = rows.value.map((r) => r.wsi);
  const cohData = rows.value.map((r) => r.coh_mean);
  const phaseData = rows.value.map((r) => r.phase_disorder);

  const datasets: any[] = [
    {
      label: "WSI",
      data: wsiData,
      borderColor: "#22c55e",
      backgroundColor: "rgba(34, 197, 94, 0.10)",
      borderWidth: 1.8,
      pointRadius: 0,
      fill: true,
      tension: 0.1,
      yAxisID: "y",
    },
  ];

  if (showCohMean.value && cohData.some((v) => v > 0)) {
    datasets.push({
      label: "coh_mean",
      data: cohData,
      borderColor: "#f59e0b",
      backgroundColor: "rgba(245, 158, 11, 0.06)",
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0.1,
      yAxisID: "y",
    });
  }

  if (showPhaseDisorder.value && phaseData.some((v) => v > 0)) {
    datasets.push({
      label: "phase_disorder",
      data: phaseData,
      borderColor: "#60a5fa",
      backgroundColor: "rgba(96, 165, 250, 0.06)",
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0.1,
      yAxisID: "y",
    });
  }

  // Optional: add a single emphasized point at the nearest sample to selectedFreqHz.
  // Cursor line remains at exact selectedFreqHz (no snapping of the cursor itself).
  const sel = selectedNearest.value;
  if (emphasizeSelectionPoint.value && sel) {
    datasets.push({
      label: "__selection_point__",
      data: [{ x: sel.freq_hz, y: sel.wsi }],
      parsing: false,
      showLine: false,
      pointRadius: 5,
      pointHoverRadius: 6,
      pointHitRadius: 10,
      borderWidth: 0,
      pointBackgroundColor: "rgba(147, 197, 253, 0.95)",
      pointBorderColor: "rgba(147, 197, 253, 0.95)",
      yAxisID: "y",
    });
  }

  // Shading plugin: shade admissible zones (from exporter field "admissible")
  const admissibleShadePlugin = {
    id: "admissibleShade",
    beforeDatasetsDraw(chart: Chart) {
      if (!shadeAdmissible.value) return;
      const { ctx, chartArea, scales } = chart;
      const xScale = scales.x as any;
      if (!chartArea || !xScale) return;

      ctx.save();
      ctx.fillStyle = "rgba(34, 197, 94, 0.06)"; // subtle green

      // Shade contiguous runs of admissible=true.
      let runStartIdx: number | null = null;
      const r = rows.value;
      for (let i = 0; i < r.length; i++) {
        const ok = !!r[i].admissible;
        if (ok && runStartIdx === null) runStartIdx = i;
        if ((!ok || i === r.length - 1) && runStartIdx !== null) {
          const runEndIdx = ok && i === r.length - 1 ? i : i - 1;
          const x1 = xScale.getPixelForValue(r[runStartIdx].freq_hz);
          const x2 = xScale.getPixelForValue(r[runEndIdx].freq_hz);
          const left = Math.min(x1, x2);
          const right = Math.max(x1, x2);
          if (right >= chartArea.left && left <= chartArea.right) {
            ctx.fillRect(
              Math.max(left, chartArea.left),
              chartArea.top,
              Math.min(right, chartArea.right) - Math.max(left, chartArea.left),
              chartArea.bottom - chartArea.top
            );
          }
          runStartIdx = null;
        }
      }
      ctx.restore();
    },
  };

  // Cursor plugin: draw vertical line at exact selectedFreqHz (no snapping of the cursor line)
  const selectionCursorPlugin = {
    id: "selectionCursor",
    afterDraw(chart: Chart) {
      const freqHz = props.selectedFreqHz ?? null;
      if (!freqHz || !Number.isFinite(freqHz)) return;
      const { ctx, chartArea, scales } = chart;
      const xScale = scales.x as any;
      if (!chartArea || !xScale) return;
      const x = xScale.getPixelForValue(freqHz);
      if (x < chartArea.left || x > chartArea.right) return;
      ctx.save();
      ctx.strokeStyle = "rgba(147, 197, 253, 0.85)";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(x, chartArea.top);
      ctx.lineTo(x, chartArea.bottom);
      ctx.stroke();
      ctx.restore();
    },
  };

  chartInstance = new Chart(chartCanvas.value, {
    type: "line",
    data: {
      labels: xs,
      datasets,
    },
    plugins: [admissibleShadePlugin, selectionCursorPlugin],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      onClick: (event: any) => {
        if (!chartInstance) return;
        const xScale = (chartInstance as any).scales?.x;
        const chartArea = (chartInstance as any).chartArea;
        if (!xScale || !chartArea) return;
        const xPx = event?.x ?? 0;
        if (xPx < chartArea.left || xPx > chartArea.right) return;
        const freqGuess = xScale.getValueForPixel(xPx);
        if (!Number.isFinite(freqGuess)) return;
        const nearest = nearestRowByFreq(Number(freqGuess));
        if (!nearest) return;

        emit("peak-selected", {
          spectrumRelpath: props.entry.relpath, // "wolf/wsi_curve.csv"
          peakIndex: -1,
          freq_hz: nearest.freq_hz,
          label: undefined,
          raw: nearest,
        });
      },
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: "#ccc",
            usePointStyle: true,
            padding: 16,
            filter: (item: any) => item.text !== "__selection_point__",
          },
        },
        tooltip: {
          backgroundColor: "rgba(30, 30, 30, 0.95)",
          titleColor: "#fff",
          bodyColor: "#ccc",
          borderColor: "#444",
          borderWidth: 1,
          padding: 12,
          callbacks: {
            title: (items) => {
              if (items.length > 0) return `${Number(items[0].label).toFixed(2)} Hz`;
              return "";
            },
            // Consolidated tooltip: show exporter fields for nearest row at hovered freq.
            // No derived metrics, no thresholds, no interpretation.
            label: (item) => {
              if (item.dataset?.label === "__selection_point__") return "";
              const row = nearestRowByLabel(item.label);
              if (!row) return "";
              return `wsi ${row.wsi.toFixed(3)} | coh_mean ${row.coh_mean.toFixed(3)} | phase_disorder ${row.phase_disorder.toFixed(3)} | admissible ${boolText(row.admissible)}`;
            },
          },
        },
      },
      scales: {
        x: {
          type: "linear",
          title: { display: true, text: "Frequency (Hz)", color: "#aaa" },
          ticks: { color: "#888" },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
        y: {
          type: "linear",
          min: 0,
          max: 1,
          title: { display: true, text: "WSI / Metrics", color: "#22c55e" },
          ticks: { color: "#9bd5b0" },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
      },
    },
  });
}

function downloadChart() {
  if (!chartCanvas.value) return;
  const link = document.createElement("a");
  link.download = `wsi_${Date.now()}.png`;
  link.href = chartCanvas.value.toDataURL("image/png");
  link.click();
}

onMounted(() => nextTick(createChart));
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
});

watch(
  [showCohMean, showPhaseDisorder, shadeAdmissible, emphasizeSelectionPoint, () => props.bytes, () => props.selectedFreqHz],
  () => nextTick(createChart)
);
</script>

<style scoped>
.wsi-curve-renderer {
  background: var(--vt-c-bg-soft, #1e1e1e);
  border-radius: 8px;
  overflow: hidden;
}
.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--vt-c-divider-light, #333);
  flex-wrap: wrap;
}
.label {
  font-family: monospace;
  background: rgba(34, 197, 94, 0.18);
  color: #22c55e;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}
.path {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--vt-c-text-2, #aaa);
}
.controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
}
.toggle {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #ccc);
  cursor: pointer;
}
.toggle input {
  accent-color: #22c55e;
}
.btn {
  padding: 0.35rem 0.6rem;
  font-size: 0.8rem;
  background: var(--vt-c-bg-mute, #2a2a2a);
  border: 1px solid var(--vt-c-divider-light, #444);
  border-radius: 4px;
  cursor: pointer;
  color: inherit;
}
.btn:hover {
  background: var(--vt-c-bg, #333);
}
.chart-container {
  position: relative;
  height: 400px;
  padding: 1rem;
}
.stats {
  display: flex;
  gap: 1.25rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--vt-c-divider-light, #333);
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #aaa);
  flex-wrap: wrap;
}
.stats strong {
  color: var(--vt-c-text-1, #ddd);
}
.selected {
  color: #93c5fd;
}
.muted {
  opacity: 0.7;
}
.error {
  padding: 1rem;
  color: var(--vt-c-red, #f44);
  background: rgba(255, 68, 68, 0.1);
  margin: 1rem;
  border-radius: 6px;
}
.raw {
  margin: 10px 0 0 0;
  padding: 0 1rem 1rem 1rem;
}
.raw-summary {
  cursor: pointer;
  user-select: none;
  opacity: 0.85;
  padding: 0.35rem 0;
}
.raw-pre {
  max-height: 240px;
  overflow: auto;
  font-size: 0.8rem;
  line-height: 1.35;
  margin: 0;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px;
}
</style>
