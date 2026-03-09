<script setup lang="ts">
/**
 * ToolpathCanvas — P2 Enhanced with LOD + Tool Visualization
 *
 * 2D canvas renderer for the animated toolpath player.
 * Pure renderer — reads all state from useToolpathPlayerStore.
 *
 * P2 enhancements:
 * - LOD: only draw visible segments based on viewport culling
 * - LOD: downsample when zoomed out on large files (> 10k segments)
 * - Tool visualization: cutter diameter circle via ToolVisualizer
 * - FPS counter in dev mode
 */

import { ref, watch, onMounted, onUnmounted } from "vue";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import { ToolVisualizer } from "@/util/toolVisualization";
import type { MoveSegment } from "@/sdk/endpoints/cam/simulate";

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------
const store = useToolpathPlayerStore();

// ---------------------------------------------------------------------------
// Tool visualizer (P3)
// ---------------------------------------------------------------------------
const toolViz = new ToolVisualizer();

// ---------------------------------------------------------------------------
// Canvas element ref
// ---------------------------------------------------------------------------
const canvasEl = ref<HTMLCanvasElement | null>(null);

// ---------------------------------------------------------------------------
// Viewport state
// ---------------------------------------------------------------------------
const viewScale = ref(1);
const viewOffX = ref(0);
const viewOffY = ref(0);

// ---------------------------------------------------------------------------
// LOD state
// ---------------------------------------------------------------------------
let _baseScale = 1; // scale at fitToView — used to derive zoom ratio

// ---------------------------------------------------------------------------
// Coordinate helpers
// ---------------------------------------------------------------------------
function toCanvasX(mmX: number): number {
  const b = store.bounds;
  if (!b) return 0;
  return (mmX - b.x_min) * viewScale.value + viewOffX.value;
}

function toCanvasY(mmY: number, ch: number): number {
  const b = store.bounds;
  if (!b) return 0;
  return ch - ((mmY - b.y_min) * viewScale.value + viewOffY.value);
}

// ---------------------------------------------------------------------------
// Viewport fitting
// ---------------------------------------------------------------------------
function fitToView(): void {
  const el = canvasEl.value;
  const b = store.bounds;
  if (!el || !b) return;

  const padFactor = 0.85;
  const rangeX = Math.max(b.x_max - b.x_min, 1);
  const rangeY = Math.max(b.y_max - b.y_min, 1);

  const scaleX = (el.width * padFactor) / rangeX;
  const scaleY = (el.height * padFactor) / rangeY;
  viewScale.value = Math.min(scaleX, scaleY);
  _baseScale = viewScale.value;

  viewOffX.value = (el.width - rangeX * viewScale.value) / 2;
  viewOffY.value = (el.height - rangeY * viewScale.value) / 2;
}

// ---------------------------------------------------------------------------
// Colour helpers
// ---------------------------------------------------------------------------
function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function lerpColour(hexA: string, hexB: string, t: number): string {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  const r = Math.round(a[0] + (b[0] - a[0]) * t);
  const g = Math.round(a[1] + (b[1] - a[1]) * t);
  const bl = Math.round(a[2] + (b[2] - a[2]) * t);
  return `rgb(${r},${g},${bl})`;
}

// ---------------------------------------------------------------------------
// LOD: compute step (draw every Nth segment when zoomed out on large sets)
// ---------------------------------------------------------------------------
function lodStep(): number {
  const count = store.segments.length;
  if (count < 10_000) return 1;
  const zoom = _baseScale > 0 ? viewScale.value / _baseScale : 1;
  if (zoom >= 0.9) return 1;
  if (zoom >= 0.5) return Math.max(1, Math.floor(count / 30_000));
  if (zoom >= 0.2) return Math.max(1, Math.floor(count / 15_000));
  return Math.max(1, Math.floor(count / 5_000));
}

// ---------------------------------------------------------------------------
// Viewport visibility check (screen-space AABB reject)
// ---------------------------------------------------------------------------
function isSegVisible(seg: MoveSegment, W: number, H: number): boolean {
  const x0 = toCanvasX(seg.from_pos[0]);
  const y0 = toCanvasY(seg.from_pos[1], H);
  const x1 = toCanvasX(seg.to_pos[0]);
  const y1 = toCanvasY(seg.to_pos[1], H);
  const minX = Math.min(x0, x1);
  const maxX = Math.max(x0, x1);
  const minY = Math.min(y0, y1);
  const maxY = Math.max(y0, y1);
  return maxX >= -50 && minX <= W + 50 && maxY >= -50 && minY <= H + 50;
}

// ---------------------------------------------------------------------------
// Draw one segment
// ---------------------------------------------------------------------------
function drawSegment(
  ctx: CanvasRenderingContext2D,
  seg: MoveSegment,
  isPast: boolean,
  zRange: number,
  canvasH: number,
): void {
  const zMin = store.bounds?.z_min ?? 0;
  const zNorm = zRange > 0.001 ? (seg.to_pos[2] - zMin) / zRange : 1;

  const x0 = toCanvasX(seg.from_pos[0]);
  const y0 = toCanvasY(seg.from_pos[1], canvasH);
  const x1 = toCanvasX(seg.to_pos[0]);
  const y1 = toCanvasY(seg.to_pos[1], canvasH);

  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y1);

  if (isPast) {
    ctx.globalAlpha = 0.4 + (1 - zNorm) * 0.6;
  } else {
    ctx.globalAlpha = 0.12;
  }

  switch (seg.type) {
    case "rapid":
      ctx.strokeStyle = "#999999";
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1;
      break;
    case "cut":
      ctx.strokeStyle = lerpColour("#4A90D9", "#1B3A6B", 1 - zNorm);
      ctx.setLineDash([]);
      ctx.lineWidth = 1 + (1 - zNorm) * 3;
      break;
    case "arc_cw":
    case "arc_ccw":
      ctx.strokeStyle = lerpColour("#2ECC71", "#1A7A42", 1 - zNorm);
      ctx.setLineDash([]);
      ctx.lineWidth = 1 + (1 - zNorm) * 3;
      break;
    default:
      ctx.strokeStyle = "#888";
      ctx.setLineDash([]);
      ctx.lineWidth = 1;
  }

  ctx.stroke();
  ctx.setLineDash([]);
  ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------------------
// Full frame draw (with LOD)
// ---------------------------------------------------------------------------
function drawFrame(): void {
  const el = canvasEl.value;
  const ctx = el?.getContext("2d");
  if (!el || !ctx || !store.bounds) return;

  const W = el.width;
  const H = el.height;
  const segs = store.segments;
  const currentIdx = store.currentSegmentIndex;
  const zRange = Math.max(store.bounds.z_max - store.bounds.z_min, 0.001);

  ctx.fillStyle = "#1E1E2E";
  ctx.fillRect(0, 0, W, H);

  if (segs.length === 0) return;

  // LOD: determine draw step
  const step = lodStep();
  let drawn = 0;

  for (let i = 0; i < segs.length; i += step) {
    const seg = segs[i];
    // Viewport cull
    if (!isSegVisible(seg, W, H)) continue;
    drawSegment(ctx, seg, i <= currentIdx, zRange, H);
    drawn++;
  }

  // Always draw segments near the playback head at full resolution
  if (step > 1 && currentIdx >= 0) {
    const lo = Math.max(0, currentIdx - 20);
    const hi = Math.min(segs.length - 1, currentIdx + 20);
    for (let i = lo; i <= hi; i++) {
      if (i % step === 0) continue; // already drawn
      if (!isSegVisible(segs[i], W, H)) continue;
      drawSegment(ctx, segs[i], i <= currentIdx, zRange, H);
      drawn++;
    }
  }

  // Tool visualization (P3)
  const [mx, my] = store.toolPosition;
  const px = toCanvasX(mx);
  const py = toCanvasY(my, H);
  const isCutting =
    store.currentSegment != null && store.currentSegment.type !== "rapid";
  const spindleOn = true; // Assume spindle on during cuts

  toolViz.draw(ctx, px, py, viewScale.value, isCutting, spindleOn && isCutting);

  // Z depth label
  const zVal = store.toolPosition[2];
  ctx.font = "11px 'JetBrains Mono', monospace";
  ctx.fillStyle = "rgba(255,255,255,0.8)";
  ctx.textAlign = "left";
  ctx.fillText(`Z${zVal.toFixed(2)}`, px + 10, py - 4);

  // Dev FPS overlay
  if (import.meta.env.DEV) {
    ctx.font = "10px monospace";
    ctx.fillStyle = "rgba(255,255,255,0.3)";
    ctx.textAlign = "right";
    ctx.fillText(`${drawn}/${segs.length} segs | step ${step}`, W - 8, 16);
  }
}

// ---------------------------------------------------------------------------
// Reactive redraw triggers
// ---------------------------------------------------------------------------
watch(
  () => store.currentTimeMs,
  () => requestAnimationFrame(drawFrame),
);

watch(
  () => store.segments,
  () => {
    fitToView();
    requestAnimationFrame(drawFrame);
  },
);

// ---------------------------------------------------------------------------
// Mouse interaction — zoom (around cursor), pan, double-click reset
// ---------------------------------------------------------------------------
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let panOffXStart = 0;
let panOffYStart = 0;

function onWheel(e: WheelEvent): void {
  e.preventDefault();
  const rect = canvasEl.value?.getBoundingClientRect();
  if (!rect || !store.bounds) return;

  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  // World coord under mouse before zoom
  const worldX =
    (mouseX - viewOffX.value) / viewScale.value + store.bounds.x_min;
  const worldY =
    (canvasEl.value!.height - mouseY - viewOffY.value) / viewScale.value +
    store.bounds.y_min;

  const factor = e.deltaY < 0 ? 1.1 : 0.9;
  const newScale = Math.max(0.01, viewScale.value * factor);

  // Adjust pan so world point stays under mouse
  viewOffX.value = mouseX - (worldX - store.bounds.x_min) * newScale;
  viewOffY.value =
    canvasEl.value!.height - mouseY - (worldY - store.bounds.y_min) * newScale;

  viewScale.value = newScale;
  requestAnimationFrame(drawFrame);
}

function onMouseDown(e: MouseEvent): void {
  isPanning = true;
  panStartX = e.clientX;
  panStartY = e.clientY;
  panOffXStart = viewOffX.value;
  panOffYStart = viewOffY.value;
}

function onMouseMove(e: MouseEvent): void {
  if (!isPanning) return;
  viewOffX.value = panOffXStart + (e.clientX - panStartX);
  viewOffY.value = panOffYStart - (e.clientY - panStartY);
  requestAnimationFrame(drawFrame);
}

function onMouseUp(): void {
  isPanning = false;
}

function onDblClick(): void {
  fitToView();
  requestAnimationFrame(drawFrame);
}

// ---------------------------------------------------------------------------
// ResizeObserver
// ---------------------------------------------------------------------------
let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  const el = canvasEl.value;
  if (!el) return;

  resizeObserver = new ResizeObserver(() => {
    el.width = el.offsetWidth;
    el.height = el.offsetHeight;
    fitToView();
    requestAnimationFrame(drawFrame);
  });
  resizeObserver.observe(el);

  el.width = el.offsetWidth;
  el.height = el.offsetHeight;
});

onUnmounted(() => {
  resizeObserver?.disconnect();
});
</script>

<template>
  <canvas
    ref="canvasEl"
    class="toolpath-canvas"
    @wheel.prevent="onWheel"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
    @mouseleave="onMouseUp"
    @dblclick="onDblClick"
  />
</template>

<style scoped>
.toolpath-canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: grab;
  background: #1e1e2e;
}
.toolpath-canvas:active {
  cursor: grabbing;
}
</style>
