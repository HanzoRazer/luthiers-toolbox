<template>
  <div class="spectrum-chart-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
      <div class="controls">
        <label class="toggle">
          <input type="checkbox" v-model="showCoherence" />
          <span>Coherence</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="logScale" />
          <span>Log Scale</span>
        </label>
        <label v-if="parsedPeaks.length > 0" class="toggle">
          <input type="checkbox" v-model="showPeaks" />
          <span>Peaks ({{ parsedPeaks.length }})</span>
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
      <span v-if="peakFreq !== null">
        <strong>Peak:</strong> {{ peakFreq.toFixed(1) }} Hz @ {{ peakMag.toFixed(4) }}
      </span>
      <span><strong>Points:</strong> {{ dataPoints }}</span>
      <span v-if="isDecimated" class="decimation-warning">
        ⚠️ Decimated from {{ originalRowCount }} points
      </span>
      <span v-if="freqRange"><strong>Range:</strong> {{ freqRange }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import type { RendererProps } from "./types";
import type { EvidenceSelection } from "../selection";

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

const props = defineProps<RendererProps>();
const emit = defineEmits<{
  (e: "select", sel: EvidenceSelection): void;
}>();

// Wave 6A: Extract point ID from spectrum relpath
function pointIdFromSpectrumRelpath(relpath: string): string | null {
  const m = relpath.match(/^spectra\/points\/([^/]+)\/spectrum\.csv$/);
  return m?.[1] ?? null;
}

const chartCanvas = ref<HTMLCanvasElement | null>(null);
const showCoherence = ref(true);
const logScale = ref(false);
const showPeaks = ref(true);
const parseError = ref<string | null>(null);

let chartInstance: Chart | null = null;

// Parse CSV data
interface SpectrumRow {
  freq_hz: number;
  H_mag: number;
  coherence: number;
  phase_deg: number;
}

// Decimation constants
const MAX_CHART_POINTS = 2000;
const originalRowCount = ref(0);

const parsedData = computed<SpectrumRow[]>(() => {
  parseError.value = null;
  originalRowCount.value = 0;
  try {
    const text = new TextDecoder("utf-8").decode(props.bytes);
    const lines = text.trim().split(/\r?\n/);
    if (lines.length < 2) {
      parseError.value = "CSV has no data rows";
      return [];
    }

    // Parse header
    const header = lines[0].toLowerCase().split(",").map((h) => h.trim());
    const freqIdx = header.findIndex((h) => h.includes("freq"));
    const magIdx = header.findIndex((h) => h.includes("mag") || h === "h_mag");
    const cohIdx = header.findIndex((h) => h.includes("coh"));
    const phaseIdx = header.findIndex((h) => h.includes("phase"));

    if (freqIdx === -1 || magIdx === -1) {
      parseError.value = `Missing required columns. Found: ${header.join(", ")}`;
      return [];
    }

    // Parse data rows
    const rows: SpectrumRow[] = [];
    for (let i = 1; i < lines.length; i++) {
      const cells = lines[i].split(",");
      const freq = parseFloat(cells[freqIdx]);
      const mag = parseFloat(cells[magIdx]);
      const coh = cohIdx >= 0 ? parseFloat(cells[cohIdx]) : 0;
      const phase = phaseIdx >= 0 ? parseFloat(cells[phaseIdx]) : 0;

      if (!isNaN(freq) && !isNaN(mag)) {
        rows.push({ freq_hz: freq, H_mag: mag, coherence: coh, phase_deg: phase });
      }
    }

    // Track original count before decimation
    originalRowCount.value = rows.length;

    // Decimate if too large for smooth Chart.js rendering
    if (rows.length > MAX_CHART_POINTS) {
      const step = Math.ceil(rows.length / MAX_CHART_POINTS);
      return rows.filter((_, i) => i % step === 0);
    }

    return rows;
  } catch (e) {
    parseError.value = e instanceof Error ? e.message : String(e);
    return [];
  }
});

// Decimation state
const isDecimated = computed(() => originalRowCount.value > MAX_CHART_POINTS);

// Parse peaks from sibling analysis.json (peaksBytes)
interface PeakData {
  freq_hz: number;
  mag: number;
  label?: string;
}

const parsedPeaks = computed<PeakData[]>(() => {
  if (!props.peaksBytes || props.peaksBytes.length === 0) return [];
  try {
    const text = new TextDecoder("utf-8").decode(props.peaksBytes);
    const json = JSON.parse(text);
    // Support various analysis.json structures:
    // 1. { peaks: [{ freq_hz, ... }] }
    // 2. { peaks: [{ frequency_hz, ... }] }
    // 3. [{ freq_hz, ... }] (direct array)
    const arr = Array.isArray(json) ? json : (json.peaks ?? []);
    return arr
      .filter((p: any) => typeof p.freq_hz === "number" || typeof p.frequency_hz === "number")
      .map((p: any, i: number) => ({
        freq_hz: p.freq_hz ?? p.frequency_hz,
        mag: p.H_mag ?? p.mag ?? p.amplitude ?? 0,
        label: p.label ?? p.note ?? `P${i + 1}`,
      }));
  } catch {
    return [];
  }
});

// Computed stats
const dataPoints = computed(() => parsedData.value.length);

const peakFreq = computed<number | null>(() => {
  if (parsedData.value.length === 0) return null;
  let maxRow = parsedData.value[0];
  for (const row of parsedData.value) {
    if (row.H_mag > maxRow.H_mag) maxRow = row;
  }
  return maxRow.freq_hz;
});

const peakMag = computed<number>(() => {
  if (parsedData.value.length === 0) return 0;
  return Math.max(...parsedData.value.map((r) => r.H_mag));
});

const freqRange = computed<string | null>(() => {
  if (parsedData.value.length === 0) return null;
  const freqs = parsedData.value.map((r) => r.freq_hz);
  const min = Math.min(...freqs);
  const max = Math.max(...freqs);
  return `${min.toFixed(0)}–${max.toFixed(0)} Hz`;
});

// Chart rendering
function createChart() {
  if (!chartCanvas.value || parsedData.value.length === 0) return;

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  const data = parsedData.value;
  const labels = data.map((r) => r.freq_hz);
  const magData = data.map((r) => r.H_mag);
  const cohData = data.map((r) => r.coherence);

  const datasets: any[] = [
    {
      label: "Magnitude",
      data: magData,
      borderColor: "#42b883",
      backgroundColor: "rgba(66, 184, 131, 0.1)",
      borderWidth: 1.5,
      pointRadius: 0,
      fill: true,
      tension: 0.1,
      yAxisID: "y",
    },
  ];

  if (showCoherence.value && cohData.some((c) => c > 0)) {
    datasets.push({
      label: "Coherence (γ²)",
      data: cohData,
      borderColor: "#f59e0b",
      backgroundColor: "rgba(245, 158, 11, 0.05)",
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0.1,
      yAxisID: "y1",
    });
  }

  // Wave 6A: Invisible peaks dataset for click detection
  const peaks = parsedPeaks.value;
  if (peaks.length > 0) {
    datasets.push({
      label: "__peaks__",
      showLine: false,
      data: peaks.map((p) => ({ x: p.freq_hz, y: p.mag })),
      pointRadius: 6,
      pointHitRadius: 10,
      pointHoverRadius: 8,
      pointBackgroundColor: "rgba(0,0,0,0)",
      pointBorderColor: "rgba(0,0,0,0)",
      yAxisID: "y",
    });
  }

  // Custom plugin to draw vertical lines at peak frequencies
  const peaksOverlayPlugin = {
    id: "peaksOverlay",
    afterDraw(chart: Chart) {
      if (!showPeaks.value || parsedPeaks.value.length === 0) return;
      const { ctx, chartArea, scales } = chart;
      const xScale = scales.x;
      if (!xScale || !chartArea) return;

      ctx.save();
      ctx.strokeStyle = "rgba(239, 68, 68, 0.7)"; // red-500
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);

      for (const peak of parsedPeaks.value) {
        const x = xScale.getPixelForValue(peak.freq_hz);
        if (x >= chartArea.left && x <= chartArea.right) {
          ctx.beginPath();
          ctx.moveTo(x, chartArea.top);
          ctx.lineTo(x, chartArea.bottom);
          ctx.stroke();

          // Draw label at top
          ctx.fillStyle = "rgba(239, 68, 68, 0.9)";
          ctx.font = "10px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText(`${peak.freq_hz.toFixed(0)}`, x, chartArea.top - 4);
        }
      }
      ctx.restore();
    },
  };

  // Wave 6A: Cursor plugin to draw selection highlight
  const cursorPlugin = {
    id: "wave6a_cursor",
    afterDraw(chart: Chart) {
      const f = props.selection?.freqHz;
      if (typeof f !== "number") return;
      const xScale = chart.scales.x;
      if (!xScale || !chart.chartArea) return;
      const x = xScale.getPixelForValue(f);
      const { top, bottom } = chart.chartArea;
      const ctx = chart.ctx;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, bottom);
      ctx.lineWidth = 2;
      ctx.strokeStyle = "rgba(255, 255, 255, 0.7)";
      ctx.stroke();
      ctx.restore();
    },
  };

  // Wave 6A: onClick handler for peak selection
  const handleClick = (_e: any, active: any[], chart: any) => {
    const hit = active?.[0];
    if (!hit) return;
    const ds = chart.data.datasets?.[hit.datasetIndex];
    if (ds?.label !== "__peaks__") return;
    const peak = peaks[hit.index];
    if (!peak) return;

    emit("select", {
      pointId: pointIdFromSpectrumRelpath(props.entry.relpath),
      freqHz: Number(peak.freq_hz),
      source: "spectrum",
    });
  };

  chartInstance = new Chart(chartCanvas.value, {
    type: "line",
    data: {
      labels,
      datasets,
    },
    plugins: [peaksOverlayPlugin, cursorPlugin],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onClick: handleClick,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: "#ccc",
            usePointStyle: true,
            padding: 16,
            filter: (item: any) => item.text !== "__peaks__",
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
              if (items.length > 0) {
                return `${Number(items[0].label).toFixed(1)} Hz`;
              }
              return "";
            },
            label: (item) => {
              const val = Number(item.raw);
              if (item.dataset.label?.includes("Coherence")) {
                return `Coherence: ${val.toFixed(3)}`;
              }
              return `Magnitude: ${val.toFixed(6)}`;
            },
          },
        },
      },
      scales: {
        x: {
          type: "linear",
          title: {
            display: true,
            text: "Frequency (Hz)",
            color: "#aaa",
          },
          ticks: { color: "#888" },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
        y: {
          type: logScale.value ? "logarithmic" : "linear",
          position: "left",
          title: {
            display: true,
            text: "Magnitude",
            color: "#42b883",
          },
          ticks: { color: "#42b883" },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
        y1: {
          type: "linear",
          position: "right",
          min: 0,
          max: 1,
          title: {
            display: true,
            text: "Coherence (γ²)",
            color: "#f59e0b",
          },
          ticks: { color: "#f59e0b" },
          grid: { drawOnChartArea: false },
        },
      },
    },
  });
}

function downloadChart() {
  if (!chartCanvas.value) return;
  const link = document.createElement("a");
  link.download = `spectrum_${Date.now()}.png`;
  link.href = chartCanvas.value.toDataURL("image/png");
  link.click();
}

// Lifecycle
onMounted(() => {
  nextTick(() => createChart());
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
});

// Watch for changes
watch([showCoherence, logScale, showPeaks, () => props.bytes, () => props.peaksBytes, () => props.selection], () => {
  nextTick(() => createChart());
});
</script>

<style scoped>
.spectrum-chart-renderer {
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
  background: rgba(66, 184, 131, 0.2);
  color: #42b883;
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
  accent-color: #42b883;
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
  gap: 1.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--vt-c-divider-light, #333);
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #aaa);
}

.stats strong {
  color: var(--vt-c-text-1, #ddd);
}

.decimation-warning {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.15);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.error {
  padding: 1rem;
  color: var(--vt-c-red, #f44);
  background: rgba(255, 68, 68, 0.1);
  margin: 1rem;
  border-radius: 6px;
}
</style>
