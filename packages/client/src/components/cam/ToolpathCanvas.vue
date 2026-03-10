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

import { ref, watch, onMounted, onUnmounted, computed } from "vue";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import { ToolVisualizer } from "@/util/toolVisualization";
import { EngagementAnalyzer, type EngagementReport } from "@/util/engagementAnalyzer";
import { MEASUREMENT_COLORS, type Measurement, type Point3D } from "@/util/measurementTool";
import { getToolColor } from "@/util/toolpathTools";
import type { MoveSegment } from "@/sdk/endpoints/cam/simulate";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** Enable heatmap mode */
  showHeatmap?: boolean;
  /** Tool diameter for engagement calculation */
  toolDiameter?: number;
  /** P6: Enable multi-tool color coding (by tool number) */
  colorByTool?: boolean;
  /** P6: Filter to show only this tool (null = show all) */
  toolFilter?: number | null;
}

const props = withDefaults(defineProps<Props>(), {
  showHeatmap: false,
  toolDiameter: 6,
  colorByTool: false,
  toolFilter: null,
});

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------
const store = useToolpathPlayerStore();

// ---------------------------------------------------------------------------
// Tool visualizer (P3)
// ---------------------------------------------------------------------------
const toolViz = new ToolVisualizer();

// ---------------------------------------------------------------------------
// P5: Engagement analyzer for heatmap
// ---------------------------------------------------------------------------
const engagementReport = ref<EngagementReport | null>(null);

const engagementAnalyzer = computed(() => {
  return new EngagementAnalyzer({
    toolDiameter: props.toolDiameter,
  });
});

function updateEngagement(): void {
  if (store.segments.length === 0) {
    engagementReport.value = null;
    return;
  }
  engagementReport.value = engagementAnalyzer.value.analyze(store.segments);
}

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
  isSelected: boolean = false,
  segmentIndex: number = -1,
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

  // P5: Highlight selected segment
  if (isSelected) {
    ctx.globalAlpha = 1;
    ctx.strokeStyle = "#FFD700"; // Gold highlight
    ctx.setLineDash([]);
    ctx.lineWidth = 4;
    ctx.stroke();
    ctx.globalAlpha = 1;
    return;
  }

  // P5: Heatmap mode - color by engagement
  if (props.showHeatmap && engagementReport.value && segmentIndex >= 0) {
    const engData = engagementReport.value.segments[segmentIndex];
    if (engData) {
      ctx.globalAlpha = isPast ? 0.9 : 0.2;
      ctx.strokeStyle = EngagementAnalyzer.getColorInterpolated(engData.engagement);
      ctx.setLineDash(seg.type === "rapid" ? [4, 4] : []);
      ctx.lineWidth = seg.type === "rapid" ? 1 : 2 + engData.engagement * 2;
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = 1;
      return;
    }
  }

  // P6: Tool filter — dim segments for other tools
  const segTool = seg.tool_number ?? 1;
  const isFilteredOut = props.toolFilter !== null && segTool !== props.toolFilter;

  if (isPast) {
    ctx.globalAlpha = isFilteredOut ? 0.1 : 0.4 + (1 - zNorm) * 0.6;
  } else {
    ctx.globalAlpha = isFilteredOut ? 0.05 : 0.12;
  }

  // P6: Color by tool number when enabled
  if (props.colorByTool && seg.type !== "rapid") {
    const toolColor = getToolColor(segTool);
    ctx.strokeStyle = toolColor;
    ctx.setLineDash([]);
    ctx.lineWidth = isFilteredOut ? 1 : 1 + (1 - zNorm) * 3;
  } else {
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
  }

  ctx.stroke();
  ctx.setLineDash([]);
  ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------------------
// P5: Heatmap legend
// ---------------------------------------------------------------------------
function drawHeatmapLegend(ctx: CanvasRenderingContext2D, W: number, H: number): void {
  const legendW = 120;
  const legendH = 16;
  const padding = 10;
  const x = W - legendW - padding;
  const y = H - legendH - padding - 20;

  // Background
  ctx.fillStyle = "rgba(19, 19, 31, 0.85)";
  ctx.fillRect(x - 8, y - 20, legendW + 16, legendH + 36);

  // Title
  ctx.font = "10px 'JetBrains Mono', monospace";
  ctx.fillStyle = "#888";
  ctx.textAlign = "left";
  ctx.fillText("Engagement", x, y - 6);

  // Gradient bar
  const gradient = ctx.createLinearGradient(x, y, x + legendW, y);
  gradient.addColorStop(0, "#333333");
  gradient.addColorStop(0.2, "#1a4a9e");
  gradient.addColorStop(0.4, "#2ecc71");
  gradient.addColorStop(0.6, "#f1c40f");
  gradient.addColorStop(0.8, "#e67e22");
  gradient.addColorStop(1, "#e74c3c");

  ctx.fillStyle = gradient;
  ctx.fillRect(x, y, legendW, legendH);

  // Border
  ctx.strokeStyle = "#3a3a5c";
  ctx.lineWidth = 1;
  ctx.strokeRect(x, y, legendW, legendH);

  // Labels
  ctx.fillStyle = "#666";
  ctx.font = "9px 'JetBrains Mono', monospace";
  ctx.textAlign = "left";
  ctx.fillText("Low", x, y + legendH + 10);
  ctx.textAlign = "right";
  ctx.fillText("High", x + legendW, y + legendH + 10);

  // Hotspot count
  if (engagementReport.value && engagementReport.value.stats.hotspotCount > 0) {
    ctx.fillStyle = "#e74c3c";
    ctx.textAlign = "center";
    ctx.fillText(
      `${engagementReport.value.stats.hotspotCount} hotspots`,
      x + legendW / 2,
      y + legendH + 10
    );
  }
}

// ---------------------------------------------------------------------------
// P5: Measurement rendering
// ---------------------------------------------------------------------------
function drawMeasurementPoint(ctx: CanvasRenderingContext2D, x: number, y: number, color: string): void {
  ctx.beginPath();
  ctx.arc(x, y, 6, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawMeasurement(ctx: CanvasRenderingContext2D, m: Measurement, canvasH: number): void {
  const x0 = toCanvasX(m.start.x);
  const y0 = toCanvasY(m.start.y, canvasH);
  const x1 = toCanvasX(m.end.x);
  const y1 = toCanvasY(m.end.y, canvasH);

  // Draw line
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y1);
  ctx.strokeStyle = MEASUREMENT_COLORS.line;
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 4]);
  ctx.stroke();
  ctx.setLineDash([]);

  // Draw endpoints
  drawMeasurementPoint(ctx, x0, y0, MEASUREMENT_COLORS.point);
  drawMeasurementPoint(ctx, x1, y1, MEASUREMENT_COLORS.point);

  // Draw label at midpoint
  const midX = (x0 + x1) / 2;
  const midY = (y0 + y1) / 2;
  const label = store.measureTool.formatDistance(m.distance);

  // Label background
  ctx.font = "bold 11px 'JetBrains Mono', monospace";
  const textWidth = ctx.measureText(label).width;
  const padding = 4;

  ctx.fillStyle = "rgba(0, 0, 0, 0.75)";
  ctx.fillRect(midX - textWidth / 2 - padding, midY - 8 - padding, textWidth + padding * 2, 16 + padding);

  // Label text
  ctx.fillStyle = MEASUREMENT_COLORS.text;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label, midX, midY);
}

function drawPendingMeasurement(ctx: CanvasRenderingContext2D, start: Point3D, mouseX: number, mouseY: number, canvasH: number): void {
  const x0 = toCanvasX(start.x);
  const y0 = toCanvasY(start.y, canvasH);

  // Draw line to mouse
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(mouseX, mouseY);
  ctx.strokeStyle = MEASUREMENT_COLORS.pending;
  ctx.lineWidth = 2;
  ctx.setLineDash([4, 4]);
  ctx.stroke();
  ctx.setLineDash([]);

  // Draw start point
  drawMeasurementPoint(ctx, x0, y0, MEASUREMENT_COLORS.pending);

  // Draw pending cursor point
  ctx.beginPath();
  ctx.arc(mouseX, mouseY, 4, 0, Math.PI * 2);
  ctx.fillStyle = MEASUREMENT_COLORS.pending;
  ctx.fill();
}

function drawAllMeasurements(ctx: CanvasRenderingContext2D, canvasH: number): void {
  // Draw completed measurements
  for (const m of store.measurements) {
    drawMeasurement(ctx, m, canvasH);
  }

  // Draw pending measurement
  if (store.pendingMeasureStart && lastMousePos.x !== -1) {
    drawPendingMeasurement(ctx, store.pendingMeasureStart, lastMousePos.x, lastMousePos.y, canvasH);
  }
}

// Track mouse position for pending measurement
const lastMousePos = { x: -1, y: -1 };

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

  const selectedIdx = store.selectedSegmentIndex;

  for (let i = 0; i < segs.length; i += step) {
    const seg = segs[i];
    // Viewport cull
    if (!isSegVisible(seg, W, H)) continue;
    drawSegment(ctx, seg, i <= currentIdx, zRange, H, i === selectedIdx, i);
    drawn++;
  }

  // Always draw segments near the playback head at full resolution
  if (step > 1 && currentIdx >= 0) {
    const lo = Math.max(0, currentIdx - 20);
    const hi = Math.min(segs.length - 1, currentIdx + 20);
    for (let i = lo; i <= hi; i++) {
      if (i % step === 0) continue; // already drawn
      if (!isSegVisible(segs[i], W, H)) continue;
      drawSegment(ctx, segs[i], i <= currentIdx, zRange, H, i === selectedIdx, i);
      drawn++;
    }
  }

  // P5: Draw selected segment on top for visibility
  if (selectedIdx !== null && selectedIdx >= 0 && selectedIdx < segs.length) {
    const seg = segs[selectedIdx];
    if (isSegVisible(seg, W, H)) {
      drawSegment(ctx, seg, selectedIdx <= currentIdx, zRange, H, true, selectedIdx);
    }
  }

  // P5: Draw heatmap legend when in heatmap mode
  if (props.showHeatmap && engagementReport.value) {
    drawHeatmapLegend(ctx, W, H);
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

  // P5: Draw measurements on top
  drawAllMeasurements(ctx, H);

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
    updateEngagement();
    requestAnimationFrame(drawFrame);
  },
);

// P5: Recompute engagement when heatmap toggled
watch(
  () => props.showHeatmap,
  (show) => {
    if (show && !engagementReport.value) {
      updateEngagement();
    }
    requestAnimationFrame(drawFrame);
  },
);

// P5: Redraw when selection changes
watch(
  () => store.selectedSegmentIndex,
  () => requestAnimationFrame(drawFrame),
);

// P5: Redraw when measurements change
watch(
  () => [store.measurements, store.pendingMeasureStart, store.measureMode],
  () => requestAnimationFrame(drawFrame),
  { deep: true }
);

// P6: Redraw when tool coloring or filter changes
watch(
  () => [props.colorByTool, props.toolFilter],
  () => requestAnimationFrame(drawFrame),
);

// ---------------------------------------------------------------------------
// Mouse interaction — zoom (around cursor), pan, double-click reset
// ---------------------------------------------------------------------------
let isPanning = false;
let hasDragged = false; // P5: Track if we actually dragged (vs just clicked)
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
  hasDragged = false;
  panStartX = e.clientX;
  panStartY = e.clientY;
  panOffXStart = viewOffX.value;
  panOffYStart = viewOffY.value;
}

function onMouseMove(e: MouseEvent): void {
  const el = canvasEl.value;
  if (el) {
    const rect = el.getBoundingClientRect();
    lastMousePos.x = e.clientX - rect.left;
    lastMousePos.y = e.clientY - rect.top;

    // P5: Redraw if we have a pending measurement (to show the line to cursor)
    if (store.pendingMeasureStart) {
      requestAnimationFrame(drawFrame);
    }
  }

  if (!isPanning) return;

  // P5: Check if we've moved enough to consider it a drag
  const dx = e.clientX - panStartX;
  const dy = e.clientY - panStartY;
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
    hasDragged = true;
  }

  viewOffX.value = panOffXStart + dx;
  viewOffY.value = panOffYStart - dy;
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
// P5: Click to select segment
// ---------------------------------------------------------------------------
function screenToWorld(screenX: number, screenY: number, canvasH: number): [number, number] {
  const b = store.bounds;
  if (!b) return [0, 0];
  const worldX = (screenX - viewOffX.value) / viewScale.value + b.x_min;
  const worldY = (canvasH - screenY - viewOffY.value) / viewScale.value + b.y_min;
  return [worldX, worldY];
}

/** Distance from point to line segment (2D) */
function pointToSegmentDist(
  px: number, py: number,
  x1: number, y1: number,
  x2: number, y2: number
): number {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const lenSq = dx * dx + dy * dy;

  if (lenSq === 0) {
    // Segment is a point
    return Math.sqrt((px - x1) ** 2 + (py - y1) ** 2);
  }

  // Project point onto line, clamped to segment
  let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));

  const projX = x1 + t * dx;
  const projY = y1 + t * dy;

  return Math.sqrt((px - projX) ** 2 + (py - projY) ** 2);
}

function findNearestSegment(worldX: number, worldY: number, maxDist: number = 5): number | null {
  const segs = store.segments;
  if (segs.length === 0) return null;

  let bestIdx: number | null = null;
  let bestDist = maxDist; // Max selection distance in world units (mm)

  for (let i = 0; i < segs.length; i++) {
    const seg = segs[i];
    const dist = pointToSegmentDist(
      worldX, worldY,
      seg.from_pos[0], seg.from_pos[1],
      seg.to_pos[0], seg.to_pos[1]
    );

    if (dist < bestDist) {
      bestDist = dist;
      bestIdx = i;
    }
  }

  return bestIdx;
}

function onClick(e: MouseEvent): void {
  const el = canvasEl.value;
  if (!el || !store.bounds) return;

  // Don't select if we were dragging (panning)
  if (hasDragged) return;

  const rect = el.getBoundingClientRect();
  const screenX = e.clientX - rect.left;
  const screenY = e.clientY - rect.top;

  const [worldX, worldY] = screenToWorld(screenX, screenY, el.height);

  // P5: Handle measure mode
  if (store.measureMode) {
    // Find nearest segment to snap to, or use raw click position
    const maxDistWorld = 8 / viewScale.value;
    const segIdx = findNearestSegment(worldX, worldY, maxDistWorld);

    let measurePoint: Point3D;
    if (segIdx !== null) {
      // Snap to segment endpoint
      const seg = store.segments[segIdx];
      // Use the endpoint closer to click
      const distToStart = Math.sqrt(
        (worldX - seg.from_pos[0]) ** 2 + (worldY - seg.from_pos[1]) ** 2
      );
      const distToEnd = Math.sqrt(
        (worldX - seg.to_pos[0]) ** 2 + (worldY - seg.to_pos[1]) ** 2
      );
      if (distToStart < distToEnd) {
        measurePoint = { x: seg.from_pos[0], y: seg.from_pos[1], z: seg.from_pos[2] };
      } else {
        measurePoint = { x: seg.to_pos[0], y: seg.to_pos[1], z: seg.to_pos[2] };
      }
    } else {
      // Use raw click position
      measurePoint = { x: worldX, y: worldY, z: 0 };
    }

    store.addMeasurePoint(measurePoint);
    requestAnimationFrame(drawFrame);
    return;
  }

  // Convert max click distance from screen pixels to world units
  const maxDistWorld = 8 / viewScale.value;

  const segIdx = findNearestSegment(worldX, worldY, maxDistWorld);
  store.selectSegment(segIdx);

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
    @click="onClick"
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
