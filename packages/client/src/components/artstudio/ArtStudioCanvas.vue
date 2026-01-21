<template>
  <div
    ref="containerRef"
    class="artstudio-canvas"
  >
    <canvas
      ref="canvasRef"
      class="artstudio-canvas__surface"
      @wheel="onWheel"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
    />

    <!-- Overlay controls -->
    <div class="artstudio-canvas__controls">
      <button
        title="Reset View"
        @click="resetView"
      >
        ⌂
      </button>
      <button
        title="Zoom In"
        @click="zoomIn"
      >
        +
      </button>
      <button
        title="Zoom Out"
        @click="zoomOut"
      >
        −
      </button>
      <span class="zoom-level">{{ Math.round(zoom * 100) }}%</span>
    </div>

    <!-- Coordinate display -->
    <div
      v-if="mouseCoords"
      class="artstudio-canvas__coords"
    >
      X: {{ mouseCoords.x.toFixed(2) }} Y: {{ mouseCoords.y.toFixed(2) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from "vue";
import type { MLPath, MLPoint } from "@/stores/useArtStudioEngine";
import { useArtStudioEngine } from "@/stores/useArtStudioEngine";

// Props
const props = defineProps<{
  showToolpaths?: boolean;
  showFretboard?: boolean;
  showFretSlots?: boolean;
  gridSize?: number;
}>();

// Refs
const containerRef = ref<HTMLDivElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const ctx = ref<CanvasRenderingContext2D | null>(null);

// Engine
const engine = useArtStudioEngine();

// View state
const zoom = ref(1);
const panX = ref(0);
const panY = ref(0);
const isDragging = ref(false);
const lastMouse = ref({ x: 0, y: 0 });
const mouseCoords = ref<MLPoint | null>(null);

// Colors
const COLORS = {
  background: "#f8f9fa",
  grid: "#e9ecef",
  gridMajor: "#dee2e6",
  path: "#212529",
  pathFill: "rgba(33, 37, 41, 0.05)",
  toolpath: "#0d6efd",
  fretboard: "#6c757d",
  fretSlot: "#dc3545",
  origin: "#198754",
};

// ---------------------------------------------------------------------------
// Drawing
// ---------------------------------------------------------------------------

function draw() {
  if (!ctx.value || !canvasRef.value) return;

  const canvas = canvasRef.value;
  const context = ctx.value;
  const w = canvas.width;
  const h = canvas.height;

  // Clear
  context.fillStyle = COLORS.background;
  context.fillRect(0, 0, w, h);

  context.save();

  // Apply view transform (center origin, flip Y for CAD convention)
  context.translate(w / 2 + panX.value, h / 2 + panY.value);
  context.scale(zoom.value, -zoom.value);

  // Draw grid
  if (props.gridSize) {
    drawGrid(context, w, h);
  }

  // Draw origin crosshair
  drawOrigin(context);

  // Draw fretboard outline
  if (props.showFretboard && engine.fretboardOutline.value.length > 0) {
    drawFretboard(context);
  }

  // Draw fret slots
  if (props.showFretSlots && engine.fretSlots.value.length > 0) {
    drawFretSlots(context);
  }

  // Draw design paths with risk-based coloring (Wave 9)
  for (const path of engine.currentPaths.value) {
    const pathId = path.meta?.id as string | undefined;
    const riskLevel = pathId ? engine.getPathRisk(pathId) : "none";
    const strokeColor = engine.getRiskColor(riskLevel);
    drawPath(context, path, strokeColor, COLORS.pathFill);
  }

  // Draw toolpaths
  if (props.showToolpaths) {
    for (const path of engine.toolpaths.value) {
      drawPath(context, path, COLORS.toolpath, "transparent", [4, 2]);
    }
  }

  context.restore();
}

function drawGrid(context: CanvasRenderingContext2D, w: number, h: number) {
  const gridSize = props.gridSize || 10;
  const viewW = w / zoom.value;
  const viewH = h / zoom.value;

  context.strokeStyle = COLORS.grid;
  context.lineWidth = 0.5 / zoom.value;

  // Vertical lines
  const startX =
    Math.floor((-viewW / 2 - panX.value / zoom.value) / gridSize) * gridSize;
  const endX =
    Math.ceil((viewW / 2 - panX.value / zoom.value) / gridSize) * gridSize;

  for (let x = startX; x <= endX; x += gridSize) {
    const isMajor = x % (gridSize * 10) === 0;
    context.strokeStyle = isMajor ? COLORS.gridMajor : COLORS.grid;
    context.beginPath();
    context.moveTo(x, -viewH);
    context.lineTo(x, viewH);
    context.stroke();
  }

  // Horizontal lines
  const startY =
    Math.floor((-viewH / 2 + panY.value / zoom.value) / gridSize) * gridSize;
  const endY =
    Math.ceil((viewH / 2 + panY.value / zoom.value) / gridSize) * gridSize;

  for (let y = startY; y <= endY; y += gridSize) {
    const isMajor = y % (gridSize * 10) === 0;
    context.strokeStyle = isMajor ? COLORS.gridMajor : COLORS.grid;
    context.beginPath();
    context.moveTo(-viewW, y);
    context.lineTo(viewW, y);
    context.stroke();
  }
}

function drawOrigin(context: CanvasRenderingContext2D) {
  const size = 10 / zoom.value;

  context.strokeStyle = COLORS.origin;
  context.lineWidth = 2 / zoom.value;

  // X axis
  context.beginPath();
  context.moveTo(0, 0);
  context.lineTo(size, 0);
  context.stroke();

  // Y axis
  context.beginPath();
  context.moveTo(0, 0);
  context.lineTo(0, size);
  context.stroke();

  // Origin dot
  context.fillStyle = COLORS.origin;
  context.beginPath();
  context.arc(0, 0, 2 / zoom.value, 0, Math.PI * 2);
  context.fill();
}

function drawPath(
  context: CanvasRenderingContext2D,
  path: MLPath,
  strokeColor: string,
  fillColor: string,
  lineDash: number[] = []
) {
  if (!path.points.length) return;

  context.beginPath();
  context.setLineDash(lineDash.map((d) => d / zoom.value));

  const [first, ...rest] = path.points;
  context.moveTo(first.x, first.y);

  for (const pt of rest) {
    context.lineTo(pt.x, pt.y);
  }

  if (path.closed) {
    context.closePath();
  }

  if (fillColor !== "transparent") {
    context.fillStyle = fillColor;
    context.fill();
  }

  context.strokeStyle = strokeColor;
  context.lineWidth = 1.5 / zoom.value;
  context.stroke();

  context.setLineDash([]);
}

function drawFretboard(context: CanvasRenderingContext2D) {
  const outline = engine.fretboardOutline.value;
  if (outline.length < 3) return;

  context.beginPath();
  context.moveTo(outline[0].x, outline[0].y);

  for (let i = 1; i < outline.length; i++) {
    context.lineTo(outline[i].x, outline[i].y);
  }
  context.closePath();

  context.strokeStyle = COLORS.fretboard;
  context.lineWidth = 2 / zoom.value;
  context.stroke();
}

function drawFretSlots(context: CanvasRenderingContext2D) {
  context.strokeStyle = COLORS.fretSlot;
  context.lineWidth = 1 / zoom.value;

  for (const slot of engine.fretSlots.value) {
    context.beginPath();
    context.moveTo(slot.left.x, slot.left.y);
    context.lineTo(slot.right.x, slot.right.y);
    context.stroke();
  }
}

// ---------------------------------------------------------------------------
// Interaction
// ---------------------------------------------------------------------------

function screenToWorld(screenX: number, screenY: number): MLPoint {
  const canvas = canvasRef.value;
  if (!canvas) return { x: 0, y: 0 };

  const rect = canvas.getBoundingClientRect();
  const x = (screenX - rect.left - canvas.width / 2 - panX.value) / zoom.value;
  const y = -(screenY - rect.top - canvas.height / 2 - panY.value) / zoom.value;

  return { x, y };
}

function onWheel(e: WheelEvent) {
  e.preventDefault();

  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  const newZoom = Math.max(0.1, Math.min(10, zoom.value * delta));

  // Zoom towards mouse position
  const worldBefore = screenToWorld(e.clientX, e.clientY);
  zoom.value = newZoom;
  const worldAfter = screenToWorld(e.clientX, e.clientY);

  panX.value += (worldAfter.x - worldBefore.x) * zoom.value;
  panY.value -= (worldAfter.y - worldBefore.y) * zoom.value;

  draw();
}

function onMouseDown(e: MouseEvent) {
  if (e.button === 0) {
    isDragging.value = true;
    lastMouse.value = { x: e.clientX, y: e.clientY };
  }
}

function onMouseMove(e: MouseEvent) {
  // Update coordinates display
  mouseCoords.value = screenToWorld(e.clientX, e.clientY);

  if (isDragging.value) {
    const dx = e.clientX - lastMouse.value.x;
    const dy = e.clientY - lastMouse.value.y;

    panX.value += dx;
    panY.value += dy;

    lastMouse.value = { x: e.clientX, y: e.clientY };
    draw();
  }
}

function onMouseUp() {
  isDragging.value = false;
}

function resetView() {
  zoom.value = 1;
  panX.value = 0;
  panY.value = 0;
  draw();
}

function zoomIn() {
  zoom.value = Math.min(10, zoom.value * 1.2);
  draw();
}

function zoomOut() {
  zoom.value = Math.max(0.1, zoom.value / 1.2);
  draw();
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

function resize() {
  const canvas = canvasRef.value;
  const container = containerRef.value;
  if (!canvas || !container) return;

  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
  draw();
}

onMounted(() => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const context = canvas.getContext("2d");
  if (!context) return;
  ctx.value = context;

  window.addEventListener("resize", resize);
  resize();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
});

// Watch for data changes
watch(
  () => [
    engine.currentPaths.value,
    engine.toolpaths.value,
    engine.fretboardOutline.value,
    engine.fretSlots.value,
  ],
  () => draw(),
  { deep: true }
);

// Expose methods for parent
defineExpose({
  resetView,
  zoomIn,
  zoomOut,
  draw,
});
</script>

<style scoped>
.artstudio-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  overflow: hidden;
}

.artstudio-canvas__surface {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}

.artstudio-canvas__surface:active {
  cursor: grabbing;
}

.artstudio-canvas__controls {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  padding: 4px 8px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.artstudio-canvas__controls button {
  width: 28px;
  height: 28px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.artstudio-canvas__controls button:hover {
  background: #e9ecef;
}

.zoom-level {
  font-size: 12px;
  color: #6c757d;
  min-width: 40px;
  text-align: center;
}

.artstudio-canvas__coords {
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 11px;
  font-family: monospace;
  color: #6c757d;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 2px;
}
</style>
