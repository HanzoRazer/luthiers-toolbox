<script setup lang="ts">
/**
 * ToolpathCanvas
 *
 * 2D canvas renderer for the animated toolpath player.
 * Pure renderer — reads all state from useToolpathPlayerStore.
 * Viewport transform, zoom, and pan are local view-only state.
 *
 * Color coding:
 *   rapid    → #999 dashed
 *   cut      → blue gradient (light = shallow, dark = deep)
 *   arc_cw/ccw → green gradient
 *   future   → same colour, alpha 0.12
 *   tool dot → red fill, white stroke
 *
 * Depth shading formula:
 *   z_norm = (z - z_min) / z_range   (0 = deepest, 1 = shallowest)
 *   line_width = 1 + (1 - z_norm) * 3
 *   opacity    = 0.4 + (1 - z_norm) * 0.6
 */

import { ref, watch, onMounted, onUnmounted } from "vue";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import type { MoveSegment } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------
const store = useToolpathPlayerStore();

// ---------------------------------------------------------------------------
// Canvas element ref
// ---------------------------------------------------------------------------
const canvasEl = ref<HTMLCanvasElement | null>(null);

// ---------------------------------------------------------------------------
// Viewport state (view-only — not in Pinia)
// ---------------------------------------------------------------------------
const viewScale  = ref(1);
const viewOffX   = ref(0);
const viewOffY   = ref(0);

// ---------------------------------------------------------------------------
// Coordinate helpers
// ---------------------------------------------------------------------------
function toCanvasX(mmX: number, cw: number): number {
  const b = store.bounds;
  if (!b) return 0;
  return (mmX - b.x_min) * viewScale.value + viewOffX.value;
}

function toCanvasY(mmY: number, ch: number): number {
  const b = store.bounds;
  if (!b) return 0;
  // Flip Y: CNC Y is up, canvas Y is down
  return ch - ((mmY - b.y_min) * viewScale.value + viewOffY.value);
}

// ---------------------------------------------------------------------------
// Viewport fitting
// ---------------------------------------------------------------------------
function fitToView(): void {
  const el = canvasEl.value;
  const b  = store.bounds;
  if (!el || !b) return;

  const padFactor = 0.85;
  const rangeX = Math.max(b.x_max - b.x_min, 1);
  const rangeY = Math.max(b.y_max - b.y_min, 1);

  const scaleX = (el.width  * padFactor) / rangeX;
  const scaleY = (el.height * padFactor) / rangeY;
  viewScale.value = Math.min(scaleX, scaleY);

  // Centre the toolpath
  viewOffX.value = (el.width  - rangeX * viewScale.value) / 2;
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
// Draw one segment
// ---------------------------------------------------------------------------
function drawSegment(
  ctx: CanvasRenderingContext2D,
  seg: MoveSegment,
  isPast: boolean,
  zRange: number,
  canvasW: number,
  canvasH: number,
): void {
  const zMin = store.bounds?.z_min ?? 0;
  const zNorm = zRange > 0.001 ? (seg.to_pos[2] - zMin) / zRange : 1; // 0=deep, 1=shallow

  const x0 = toCanvasX(seg.from_pos[0], canvasW);
  const y0 = toCanvasY(seg.from_pos[1], canvasH);
  const x1 = toCanvasX(seg.to_pos[0],  canvasW);
  const y1 = toCanvasY(seg.to_pos[1],  canvasH);

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
// Full frame draw
// ---------------------------------------------------------------------------
function drawFrame(): void {
  const el  = canvasEl.value;
  const ctx = el?.getContext("2d");
  if (!el || !ctx || !store.bounds) return;

  const W = el.width;
  const H = el.height;
  const segs       = store.segments;
  const currentIdx = store.currentSegmentIndex;
  const zRange     = Math.max(store.bounds.z_max - store.bounds.z_min, 0.001);

  // 1. Clear with dark background
  ctx.fillStyle = "#1E1E2E";
  ctx.fillRect(0, 0, W, H);

  if (segs.length === 0) return;

  // 2. Draw all segments
  for (let i = 0; i < segs.length; i++) {
    drawSegment(ctx, segs[i], i <= currentIdx, zRange, W, H);
  }

  // 3. Tool dot at interpolated position
  const [mx, my] = store.toolPosition;
  const px = toCanvasX(mx, W);
  const py = toCanvasY(my, H);

  ctx.beginPath();
  ctx.arc(px, py, 6, 0, Math.PI * 2);
  ctx.fillStyle   = "#E74C3C";
  ctx.fill();
  ctx.strokeStyle = "#FFFFFF";
  ctx.lineWidth   = 1.5;
  ctx.stroke();

  // 4. Z depth indicator next to tool dot
  const zVal = store.toolPosition[2];
  ctx.font         = "11px 'JetBrains Mono', monospace";
  ctx.fillStyle    = "rgba(255,255,255,0.8)";
  ctx.textAlign    = "left";
  ctx.fillText(`Z${zVal.toFixed(2)}`, px + 10, py - 4);
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
// Mouse interaction — zoom, pan, double-click reset
// ---------------------------------------------------------------------------
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let panOffXStart = 0;
let panOffYStart = 0;

function onWheel(e: WheelEvent): void {
  e.preventDefault();
  const factor = e.deltaY < 0 ? 1.1 : 0.9;
  viewScale.value = Math.max(0.1, viewScale.value * factor);
  requestAnimationFrame(drawFrame);
}

function onMouseDown(e: MouseEvent): void {
  isPanning      = true;
  panStartX      = e.clientX;
  panStartY      = e.clientY;
  panOffXStart   = viewOffX.value;
  panOffYStart   = viewOffY.value;
}

function onMouseMove(e: MouseEvent): void {
  if (!isPanning) return;
  viewOffX.value = panOffXStart + (e.clientX - panStartX);
  viewOffY.value = panOffYStart + (e.clientY - panStartY);
  requestAnimationFrame(drawFrame);
}

function onMouseUp(): void { isPanning = false; }

function onDblClick(): void {
  fitToView();
  requestAnimationFrame(drawFrame);
}

// ---------------------------------------------------------------------------
// ResizeObserver — keep canvas size in sync with container
// ---------------------------------------------------------------------------
let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  const el = canvasEl.value;
  if (!el) return;

  resizeObserver = new ResizeObserver(() => {
    el.width  = el.offsetWidth;
    el.height = el.offsetHeight;
    fitToView();
    requestAnimationFrame(drawFrame);
  });
  resizeObserver.observe(el);

  el.width  = el.offsetWidth;
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
