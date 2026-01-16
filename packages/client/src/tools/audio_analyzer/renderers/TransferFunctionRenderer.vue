<template>
  <div class="transfer-function-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
      <div class="controls">
        <label class="toggle">
          <input type="checkbox" v-model="showPhase" />
          <span>Phase</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="logFreq" />
          <span>Log Freq</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="dbScale" />
          <span>dB</span>
        </label>
        <button class="btn" @click="downloadChart">📷 PNG</button>
      </div>
    </div>

    <div v-if="parseError" class="error">
      <strong>Parse Error:</strong> {{ parseError }}
    </div>

    <div v-else-if="!hasData" class="empty">
      No transfer function data found in JSON.
    </div>

    <div v-else class="chart-container">
      <canvas ref="chartCanvas"></canvas>
    </div>

    <div class="stats">
      <span v-if="peakInfo">
        <strong>Peak:</strong> {{ peakInfo.freq.toFixed(1) }} Hz @ {{ peakInfo.mag.toFixed(2) }} {{ dbScale ? 'dB' : '' }}
      </span>
      <span><strong>Points:</strong> {{ dataPoints }}</span>
      <span v-if="freqRange"><strong>Range:</strong> {{ freqRange }}</span>
      <span v-if="odsMetadata" class="metadata-badge">
        {{ odsMetadata }}
      </span>
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
} from "chart.js";
import type { RendererProps } from "./types";

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  Title,
  Tooltip,
  Legend
);

const props = defineProps<RendererProps>();

const chartCanvas = ref<HTMLCanvasElement | null>(null);
const showPhase = ref(true);
const logFreq = ref(true);  // Default to log frequency for Bode plot
const dbScale = ref(true);  // Default to dB scale for Bode plot
const parseError = ref<string | null>(null);

let chartInstance: Chart | null = null;

// ─────────────────────────────────────────────────────────────────────────────
// Data Structures
// ─────────────────────────────────────────────────────────────────────────────

interface TransferFunctionPoint {
  freq: number;
  mag: number;      // Linear magnitude
  phase: number;    // Degrees
}

interface ParsedODS {
  points: TransferFunctionPoint[];
  metadata?: {
    analysisType?: string;
    nModes?: number;
    freqMin?: number;
    freqMax?: number;
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Parsing Logic — handles multiple JSON formats from tap_tone_pi
// ─────────────────────────────────────────────────────────────────────────────

const parsedData = computed<ParsedODS>(() => {
  parseError.value = null;
  try {
    const text = new TextDecoder("utf-8").decode(props.bytes);
    const json = JSON.parse(text);
    return parseTransferFunction(json);
  } catch (e) {
    parseError.value = e instanceof Error ? e.message : String(e);
    return { points: [] };
  }
});

function parseTransferFunction(json: unknown): ParsedODS {
  if (!json || typeof json !== "object") {
    throw new Error("Invalid JSON: expected object");
  }

  const obj = json as Record<string, unknown>;
  let points: TransferFunctionPoint[] = [];
  let metadata: ParsedODS["metadata"] = {};

  // ─── Format 1: Arrays (freq, mag, phase as parallel arrays) ───
  if (Array.isArray(obj.frequencies) || Array.isArray(obj.freq)) {
    const freqs = (obj.frequencies || obj.freq || obj.f) as number[];
    const mags = (obj.magnitude || obj.mag || obj.H_mag || obj.amplitude) as number[];
    const phases = (obj.phase || obj.phase_deg || obj.phi) as number[];

    if (!Array.isArray(freqs) || !Array.isArray(mags)) {
      throw new Error("Missing frequency or magnitude arrays");
    }

    points = freqs.map((freq, i) => ({
      freq,
      mag: mags[i] ?? 0,
      phase: phases?.[i] ?? 0,
    }));
  }

  // ─── Format 2: Array of objects [{freq, mag, phase}, ...] ───
  else if (Array.isArray(obj.data) || Array.isArray(obj.points) || Array.isArray(obj.transfer_function)) {
    const arr = (obj.data || obj.points || obj.transfer_function) as Record<string, unknown>[];
    
    points = arr.map((item) => ({
      freq: Number(item.freq ?? item.frequency ?? item.f ?? 0),
      mag: Number(item.mag ?? item.magnitude ?? item.H_mag ?? item.amplitude ?? 0),
      phase: Number(item.phase ?? item.phase_deg ?? item.phi ?? 0),
    }));
  }

  // ─── Format 3: ODS snapshot with modes ───
  else if (obj.modes && Array.isArray(obj.modes)) {
    const modes = obj.modes as Record<string, unknown>[];
    points = modes.map((mode) => ({
      freq: Number(mode.freq ?? mode.frequency ?? 0),
      mag: Number(mode.amplitude ?? mode.mag ?? mode.H ?? 1),
      phase: Number(mode.phase ?? 0),
    }));
    
    metadata.analysisType = "ODS Modal";
    metadata.nModes = modes.length;
  }

  // ─── Format 4: FRF (Frequency Response Function) ───
  else if (obj.frf || obj.H) {
    const frf = (obj.frf || obj.H) as Record<string, unknown>;
    if (Array.isArray(frf.real) && Array.isArray(frf.imag)) {
      const real = frf.real as number[];
      const imag = frf.imag as number[];
      const freqs = (frf.freq || obj.freq || obj.frequencies) as number[];
      
      if (!Array.isArray(freqs)) {
        throw new Error("FRF format requires frequencies array");
      }
      
      points = freqs.map((freq, i) => {
        const r = real[i] ?? 0;
        const im = imag[i] ?? 0;
        return {
          freq,
          mag: Math.sqrt(r * r + im * im),
          phase: Math.atan2(im, r) * (180 / Math.PI),
        };
      });
    }
  }

  // ─── Fallback: Try to find any array with freq-like data ───
  if (points.length === 0) {
    // Last resort: look for any arrays that might be data
    const keys = Object.keys(obj);
    for (const key of keys) {
      if (Array.isArray(obj[key]) && (obj[key] as unknown[]).length > 0) {
        const arr = obj[key] as unknown[];
        if (typeof arr[0] === "object" && arr[0] !== null) {
          const first = arr[0] as Record<string, unknown>;
          if ("freq" in first || "frequency" in first || "f" in first) {
            points = arr.map((item) => {
              const it = item as Record<string, unknown>;
              return {
                freq: Number(it.freq ?? it.frequency ?? it.f ?? 0),
                mag: Number(it.mag ?? it.magnitude ?? it.H_mag ?? it.amplitude ?? 1),
                phase: Number(it.phase ?? it.phase_deg ?? 0),
              };
            });
            break;
          }
        }
      }
    }
  }

  // Extract metadata if present
  if (obj.analysis_type) metadata.analysisType = String(obj.analysis_type);
  if (obj.n_modes) metadata.nModes = Number(obj.n_modes);
  if (obj.freq_min) metadata.freqMin = Number(obj.freq_min);
  if (obj.freq_max) metadata.freqMax = Number(obj.freq_max);

  // Filter out invalid points and sort by frequency
  points = points
    .filter((p) => !isNaN(p.freq) && !isNaN(p.mag) && p.freq > 0)
    .sort((a, b) => a.freq - b.freq);

  return { points, metadata };
}

// ─────────────────────────────────────────────────────────────────────────────
// Computed Values
// ─────────────────────────────────────────────────────────────────────────────

const hasData = computed(() => parsedData.value.points.length > 0);
const dataPoints = computed(() => parsedData.value.points.length);

// Convert to dB if enabled
function toDb(linear: number): number {
  if (linear <= 0) return -100;  // Floor for log(0)
  return 20 * Math.log10(linear);
}

const chartData = computed(() => {
  const points = parsedData.value.points;
  if (dbScale.value) {
    return points.map((p) => ({
      freq: p.freq,
      mag: toDb(p.mag),
      phase: p.phase,
    }));
  }
  return points;
});

const peakInfo = computed(() => {
  const data = chartData.value;
  if (data.length === 0) return null;
  
  let maxIdx = 0;
  for (let i = 1; i < data.length; i++) {
    if (data[i].mag > data[maxIdx].mag) maxIdx = i;
  }
  return { freq: data[maxIdx].freq, mag: data[maxIdx].mag };
});

const freqRange = computed(() => {
  const points = parsedData.value.points;
  if (points.length === 0) return null;
  const min = points[0].freq;
  const max = points[points.length - 1].freq;
  return `${min.toFixed(0)}–${max.toFixed(0)} Hz`;
});

const odsMetadata = computed(() => {
  const meta = parsedData.value.metadata;
  if (!meta) return null;
  const parts: string[] = [];
  if (meta.analysisType) parts.push(meta.analysisType);
  if (meta.nModes) parts.push(`${meta.nModes} modes`);
  return parts.length > 0 ? parts.join(" · ") : null;
});

// ─────────────────────────────────────────────────────────────────────────────
// Chart Rendering
// ─────────────────────────────────────────────────────────────────────────────

function createChart() {
  if (!chartCanvas.value || chartData.value.length === 0) return;

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  const data = chartData.value;
  const labels = data.map((p) => p.freq);
  const magData = data.map((p) => p.mag);
  const phaseData = data.map((p) => p.phase);

  const datasets: any[] = [
    {
      label: dbScale.value ? "Magnitude (dB)" : "Magnitude",
      data: magData,
      borderColor: "#3b82f6",
      backgroundColor: "rgba(59, 130, 246, 0.1)",
      borderWidth: 2,
      pointRadius: data.length < 100 ? 3 : 0,
      fill: false,
      tension: 0.1,
      yAxisID: "y",
    },
  ];

  if (showPhase.value) {
    datasets.push({
      label: "Phase (°)",
      data: phaseData,
      borderColor: "#ef4444",
      backgroundColor: "rgba(239, 68, 68, 0.05)",
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0.1,
      yAxisID: "y1",
    });
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: "line",
    data: {
      labels,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
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
          },
        },
        title: {
          display: true,
          text: "Transfer Function (Bode Plot)",
          color: "#ddd",
          font: { size: 14, weight: "normal" },
          padding: { bottom: 16 },
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
              if (item.dataset.label?.includes("Phase")) {
                return `Phase: ${val.toFixed(1)}°`;
              }
              if (dbScale.value) {
                return `Magnitude: ${val.toFixed(2)} dB`;
              }
              return `Magnitude: ${val.toFixed(6)}`;
            },
          },
        },
      },
      scales: {
        x: {
          type: logFreq.value ? "logarithmic" : "linear",
          title: {
            display: true,
            text: "Frequency (Hz)",
            color: "#aaa",
          },
          ticks: {
            color: "#888",
            callback: function(value) {
              // Better tick labels for log scale
              if (logFreq.value) {
                const v = Number(value);
                if ([10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000].includes(v)) {
                  return v >= 1000 ? `${v / 1000}k` : v;
                }
                return null;
              }
              return value;
            },
          },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
        y: {
          type: "linear",
          position: "left",
          title: {
            display: true,
            text: dbScale.value ? "Magnitude (dB)" : "Magnitude",
            color: "#3b82f6",
          },
          ticks: { color: "#3b82f6" },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
        y1: {
          type: "linear",
          position: "right",
          min: -180,
          max: 180,
          title: {
            display: showPhase.value,
            text: "Phase (°)",
            color: "#ef4444",
          },
          ticks: {
            color: "#ef4444",
            callback: (value) => `${value}°`,
          },
          grid: { drawOnChartArea: false },
          display: showPhase.value,
        },
      },
    },
  });
}

function downloadChart() {
  if (!chartCanvas.value) return;
  const link = document.createElement("a");
  link.download = `bode_plot_${Date.now()}.png`;
  link.href = chartCanvas.value.toDataURL("image/png");
  link.click();
}

// ─────────────────────────────────────────────────────────────────────────────
// Lifecycle
// ─────────────────────────────────────────────────────────────────────────────

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
watch([showPhase, logFreq, dbScale, () => props.bytes], () => {
  nextTick(() => createChart());
});
</script>

<style scoped>
.transfer-function-renderer {
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
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
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
  accent-color: #3b82f6;
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
  flex-wrap: wrap;
}

.stats strong {
  color: var(--vt-c-text-1, #ddd);
}

.metadata-badge {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
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

.empty {
  padding: 2rem;
  text-align: center;
  color: var(--vt-c-text-2, #888);
}
</style>
