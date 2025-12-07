<template>
  <section class="svg-viewer" v-if="hasGeometry">
    <header class="viewer-header">
      <div>
        <h3>SVG Dual Display</h3>
        <p class="hint">Baseline vs Current overlay with quick stats.</p>
      </div>
      <div class="header-actions">
        <div class="stats" v-if="diff">
          <span
            >Δ Added: <strong>{{ diff.summary.added }}</strong></span
          >
          <span
            >Δ Removed: <strong>{{ diff.summary.removed }}</strong></span
          >
        </div>
        <button
          class="export-btn"
          @click="onExportDiffReport"
          :disabled="exporting || !diff"
          title="Export comparison screenshots as ZIP"
        >
          <span v-if="exporting">Exporting…</span>
          <span v-else>📦 Export Diff Report</span>
        </button>
      </div>
    </header>

    <div class="canvases" ref="canvasesContainer">
      <div class="canvas">
        <p class="label">Baseline</p>
        <svg
          ref="baselineSvgRef"
          :viewBox="viewBox"
          preserveAspectRatio="xMidYMid meet"
        >
          <line
            v-for="(seg, idx) in baselineSegments"
            :key="`base-${idx}`"
            :x1="seg.x1"
            :y1="-seg.y1"
            :x2="seg.x2"
            :y2="-seg.y2"
            stroke="#6b7280"
            stroke-width="0.8"
          />
        </svg>
      </div>
      <div class="canvas">
        <p class="label">Current</p>
        <svg
          ref="currentSvgRef"
          :viewBox="viewBox"
          preserveAspectRatio="xMidYMid meet"
        >
          <line
            v-for="(seg, idx) in currentSegments"
            :key="`curr-${idx}`"
            :x1="seg.x1"
            :y1="-seg.y1"
            :x2="seg.x2"
            :y2="-seg.y2"
            :stroke="seg.color"
            stroke-width="1"
          />
        </svg>
      </div>
      <div class="canvas">
        <p class="label">Diff Overlay</p>
        <svg
          ref="diffSvgRef"
          :viewBox="viewBox"
          preserveAspectRatio="xMidYMid meet"
        >
          <!-- Baseline in gray -->
          <line
            v-for="(seg, idx) in baselineSegments"
            :key="`diff-base-${idx}`"
            :x1="seg.x1"
            :y1="-seg.y1"
            :x2="seg.x2"
            :y2="-seg.y2"
            stroke="#4b5563"
            stroke-width="0.6"
            opacity="0.5"
          />
          <!-- Current in green -->
          <line
            v-for="(seg, idx) in currentSegments"
            :key="`diff-curr-${idx}`"
            :x1="seg.x1"
            :y1="-seg.y1"
            :x2="seg.x2"
            :y2="-seg.y2"
            stroke="#22c55e"
            stroke-width="1"
          />
        </svg>
      </div>
    </div>
  </section>
  <p v-else class="hint">Load geometry to preview the SVG overlay.</p>
</template>

<script setup lang="ts">
import { computed, watch, ref } from "vue";
import type { CanonicalGeometry } from "@/utils/geometry";

interface DiffSummary {
  added: number;
  removed: number;
}

interface DiffResult {
  summary: DiffSummary;
  baseline_geometry?: CanonicalGeometry;
  current_geometry?: CanonicalGeometry;
}

interface SegmentLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color?: string;
}

const props = defineProps<{
  diff: DiffResult | null;
}>();

const baselineSegments = ref<SegmentLine[]>([]);
const currentSegments = ref<SegmentLine[]>([]);
const bounds = ref({ minX: 0, minY: 0, maxX: 100, maxY: 100 });
const exporting = ref(false);

// Template refs for SVG elements
const baselineSvgRef = ref<SVGSVGElement | null>(null);
const currentSvgRef = ref<SVGSVGElement | null>(null);
const diffSvgRef = ref<SVGSVGElement | null>(null);

const hasGeometry = computed(() =>
  Boolean(baselineSegments.value.length || currentSegments.value.length)
);

const viewBox = computed(() => {
  const { minX, minY, maxX, maxY } = bounds.value;
  const width = Math.max(maxX - minX, 1);
  const height = Math.max(maxY - minY, 1);
  return `${minX - 5} ${-maxY - 5} ${width + 10} ${height + 10}`;
});

function geometryToSegments(
  geometry?: CanonicalGeometry,
  color = "#22c55e"
): SegmentLine[] {
  if (!geometry?.paths) {
    return [];
  }
  const segments: SegmentLine[] = [];
  geometry.paths.forEach((path) => {
    path.segments?.forEach((segment) => {
      if (segment.type === "line") {
        segments.push({
          x1: Number(segment.x1) || 0,
          y1: Number(segment.y1) || 0,
          x2: Number(segment.x2) || 0,
          y2: Number(segment.y2) || 0,
          color,
        });
      }
    });
  });
  return segments;
}

function updateBounds(): void {
  const all = [...baselineSegments.value, ...currentSegments.value];
  if (!all.length) {
    bounds.value = { minX: 0, minY: 0, maxX: 100, maxY: 100 };
    return;
  }
  let minX = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  all.forEach((seg) => {
    minX = Math.min(minX, seg.x1, seg.x2);
    maxX = Math.max(maxX, seg.x1, seg.x2);
    minY = Math.min(minY, seg.y1, seg.y2);
    maxY = Math.max(maxY, seg.y1, seg.y2);
  });
  bounds.value = {
    minX: Number.isFinite(minX) ? minX : 0,
    maxX: Number.isFinite(maxX) ? maxX : 100,
    minY: Number.isFinite(minY) ? minY : 0,
    maxY: Number.isFinite(maxY) ? maxY : 100,
  };
}

// Capture SVG as data URL using canvas
function captureSvgDataUrl(
  svgElement: SVGSVGElement | null
): Promise<string | null> {
  if (!svgElement) return Promise.resolve(null);

  try {
    const canvas = document.createElement("canvas");
    canvas.width = 800;
    canvas.height = 600;
    const ctx = canvas.getContext("2d");

    if (!ctx) {
      console.warn("Failed to get canvas context");
      return Promise.resolve(null);
    }

    // Serialize SVG to string
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);

    // Create blob from SVG
    const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    return new Promise<string | null>((resolve) => {
      const img = new Image();
      img.onload = () => {
        ctx.fillStyle = "#080808";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        URL.revokeObjectURL(url);
        resolve(canvas.toDataURL("image/png"));
      };
      img.onerror = () => {
        console.warn("Failed to load SVG image");
        URL.revokeObjectURL(url);
        resolve(null);
      };
      img.src = url;
    });
  } catch (err) {
    console.warn("Failed to capture SVG", err);
    return Promise.resolve(null);
  }
}

async function onExportDiffReport() {
  if (!props.diff) return;

  exporting.value = true;
  try {
    const beforeDataUrl = await captureSvgDataUrl(baselineSvgRef.value);
    const afterDataUrl = await captureSvgDataUrl(currentSvgRef.value);
    const diffDataUrl = await captureSvgDataUrl(diffSvgRef.value);

    if (!beforeDataUrl || !afterDataUrl || !diffDataUrl) {
      alert("Unable to capture one or more canvases.");
      return;
    }

    const payload = {
      mode: "overlay",
      layers: ["base", "current"],
      screenshotBefore: beforeDataUrl,
      screenshotAfter: afterDataUrl,
      screenshotDiff: diffDataUrl,
      beforeLabel: "baseline",
      afterLabel: "current",
      diffLabel: "diff-overlay",
    };

    const resp = await fetch("/export/diff-report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      console.error("Export failed", resp.status, await resp.text());
      alert("Export failed. Check console for details.");
      return;
    }

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "diff-report.zip";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Export failed", err);
    alert("Export failed due to an unexpected error.");
  } finally {
    exporting.value = false;
  }
}

watch(
  () => props.diff,
  (value) => {
    baselineSegments.value = geometryToSegments(
      value?.baseline_geometry,
      "#6b7280"
    );
    currentSegments.value = geometryToSegments(
      value?.current_geometry,
      "#22c55e"
    );
    updateBounds();
  },
  { deep: true }
);
</script>

<style scoped>
.svg-viewer {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.export-btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid #4b5563;
  background: #1f2937;
  color: #e5e7eb;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.export-btn:hover:not(:disabled) {
  background: #374151;
  border-color: #6b7280;
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.canvases {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.canvas {
  border: 1px solid #252525;
  border-radius: 8px;
  padding: 0.5rem;
  background: #0b0b0b;
}

.canvas svg {
  width: 100%;
  height: 280px;
  background: #080808;
}

.label {
  font-size: 0.85rem;
  color: #a0a0a0;
  margin-bottom: 0.25rem;
}

.stats {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #d1d5db;
}

.hint {
  color: #8c8c8c;
}
</style>
