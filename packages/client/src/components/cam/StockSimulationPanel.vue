<script setup lang="ts">
/**
 * StockSimulationPanel — P6 Step 15: 2D Stock Material Removal Preview
 *
 * Displays a real-time visualization of material removal:
 * - 2D heightmap view of remaining stock
 * - Volume/percentage removed statistics
 * - Color-coded depth visualization
 * - Playback synced with toolpath animation
 */

import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import type { MoveSegment, SimulateBounds } from "@/sdk/endpoints/cam";
import { StockSimulator, type StockMaterial, type RemovalStats } from "@/util/stockSimulator";

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const props = defineProps<{
  segments: MoveSegment[];
  currentSegmentIndex: number;
  bounds: SimulateBounds | null;
  toolDiameter?: number;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const canvasRef = ref<HTMLCanvasElement | null>(null);
const simulator = ref<StockSimulator | null>(null);
const stats = ref<RemovalStats>({ totalVoxels: 0, removedVoxels: 0, percentRemoved: 0, volumeRemoved: 0 });
const isInitialized = ref(false);
const showDepthView = ref(false);
const resolution = ref(0.5);

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const volumeFormatted = computed(() => {
  const vol = stats.value.volumeRemoved;
  if (vol > 1000) {
    return `${(vol / 1000).toFixed(2)} cm³`;
  }
  return `${vol.toFixed(1)} mm³`;
});

const progressColor = computed(() => {
  const pct = stats.value.percentRemoved;
  if (pct < 25) return "#2ecc71";
  if (pct < 50) return "#3498db";
  if (pct < 75) return "#f39c12";
  return "#e74c3c";
});

// ---------------------------------------------------------------------------
// Methods
// ---------------------------------------------------------------------------

function initializeSimulator(): void {
  if (!props.bounds) return;

  const sim = new StockSimulator();
  sim.initializeFromBounds(props.bounds, {
    resolution: resolution.value,
    margin: 5,
  });
  sim.setToolDiameter(props.toolDiameter ?? 6);

  simulator.value = sim;
  isInitialized.value = true;

  // Initial render
  updateSimulation();
}

function updateSimulation(): void {
  if (!simulator.value || !canvasRef.value) return;

  // Simulate up to current segment
  simulator.value.simulateToSegment(props.segments, props.currentSegmentIndex);
  stats.value = simulator.value.getStats();

  // Render to canvas
  renderCanvas();
}

function renderCanvas(): void {
  const canvas = canvasRef.value;
  const stock = simulator.value?.getStock();
  if (!canvas || !stock) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // Clear canvas
  ctx.fillStyle = "#1a1a2e";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Calculate view transform to fit stock in canvas
  const padding = 10;
  const stockWidth = stock.bounds.x_max - stock.bounds.x_min;
  const stockHeight = stock.bounds.y_max - stock.bounds.y_min;

  const scaleX = (canvas.width - padding * 2) / stockWidth;
  const scaleY = (canvas.height - padding * 2) / stockHeight;
  const scale = Math.min(scaleX, scaleY);

  const offsetX = padding + (canvas.width - padding * 2 - stockWidth * scale) / 2 - stock.bounds.x_min * scale;
  const offsetY = padding + (canvas.height - padding * 2 - stockHeight * scale) / 2 - stock.bounds.y_min * scale;

  // Render stock
  simulator.value?.renderToCanvas(ctx, {
    scale,
    offsetX,
    offsetY,
    canvasWidth: canvas.width,
    canvasHeight: canvas.height,
  }, {
    showRemoved: true,
    materialColor: showDepthView.value ? "#4a90d9" : "#8B4513",
    removedColor: "#1a1a2e",
    opacity: 0.85,
  });

  // Draw border
  ctx.strokeStyle = "#3a3a5c";
  ctx.lineWidth = 1;
  ctx.strokeRect(
    stock.bounds.x_min * scale + offsetX,
    canvas.height - (stock.bounds.y_max * scale + offsetY),
    stockWidth * scale,
    stockHeight * scale
  );
}

function resetSimulation(): void {
  simulator.value?.reset();
  updateSimulation();
}

function changeResolution(newRes: number): void {
  resolution.value = newRes;
  if (props.bounds) {
    initializeSimulator();
  }
}

// ---------------------------------------------------------------------------
// Watchers
// ---------------------------------------------------------------------------

watch(
  () => props.currentSegmentIndex,
  () => {
    if (isInitialized.value) {
      updateSimulation();
    }
  }
);

watch(
  () => props.bounds,
  () => {
    if (props.bounds) {
      initializeSimulator();
    }
  },
  { immediate: true }
);

watch(
  () => props.toolDiameter,
  (newDia) => {
    if (simulator.value && newDia) {
      simulator.value.setToolDiameter(newDia);
    }
  }
);

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => {
  if (props.bounds) {
    initializeSimulator();
  }
});

onUnmounted(() => {
  simulator.value = null;
});
</script>

<template>
  <div class="stock-simulation-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-title">
        <span class="icon">🪵</span>
        <span>Stock Simulation</span>
      </div>
      <div class="header-actions">
        <button
          class="action-btn"
          :class="{ active: showDepthView }"
          title="Toggle depth view"
          @click="showDepthView = !showDepthView"
        >
          🎨
        </button>
        <button
          class="action-btn"
          title="Reset simulation"
          @click="resetSimulation"
        >
          🔄
        </button>
        <button class="close-btn" @click="emit('close')">&times;</button>
      </div>
    </div>

    <!-- Canvas -->
    <div class="canvas-container">
      <canvas
        ref="canvasRef"
        width="300"
        height="220"
        class="stock-canvas"
      />

      <div v-if="!isInitialized" class="loading-overlay">
        <span>Initializing...</span>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-section">
      <div class="stat-row">
        <span class="stat-label">Removed</span>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{
              width: `${Math.min(100, stats.percentRemoved)}%`,
              backgroundColor: progressColor
            }"
          />
        </div>
        <span class="stat-value">{{ stats.percentRemoved.toFixed(1) }}%</span>
      </div>

      <div class="stat-grid">
        <div class="stat-item">
          <span class="stat-label">Volume</span>
          <span class="stat-value">{{ volumeFormatted }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Voxels</span>
          <span class="stat-value">{{ stats.removedVoxels.toLocaleString() }}</span>
        </div>
      </div>
    </div>

    <!-- Resolution Control -->
    <div class="resolution-section">
      <span class="res-label">Resolution:</span>
      <div class="res-buttons">
        <button
          v-for="res in [1, 0.5, 0.25]"
          :key="res"
          class="res-btn"
          :class="{ active: resolution === res }"
          @click="changeResolution(res)"
        >
          {{ res === 1 ? 'Low' : res === 0.5 ? 'Med' : 'High' }}
        </button>
      </div>
    </div>

    <!-- Legend -->
    <div class="legend">
      <div class="legend-item">
        <span class="legend-color material" />
        <span>Material</span>
      </div>
      <div class="legend-item">
        <span class="legend-color removed" />
        <span>Removed</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stock-simulation-panel {
  background: #1e1e2e;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  font-size: 12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #1a1a2a;
  border-bottom: 1px solid #333;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #8B4513;
}

.header-title .icon {
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.action-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #888;
  width: 28px;
  height: 28px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:hover {
  background: #33334a;
  color: #ccc;
}

.action-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
}

.close-btn:hover {
  color: #fff;
}

/* Canvas */
.canvas-container {
  position: relative;
  background: #13131f;
  border-bottom: 1px solid #2a2a4a;
}

.stock-canvas {
  display: block;
  width: 100%;
  height: auto;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(30, 30, 46, 0.9);
  color: #888;
}

/* Stats */
.stats-section {
  padding: 10px 12px;
  border-bottom: 1px solid #2a2a4a;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 10px;
  color: #666;
  text-transform: uppercase;
  min-width: 50px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #2a2a4a;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.2s ease;
}

.stat-value {
  font-family: "JetBrains Mono", monospace;
  color: #ddd;
  min-width: 50px;
  text-align: right;
}

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: #252538;
  border-radius: 4px;
}

.stat-item .stat-value {
  color: #4a90d9;
  font-size: 11px;
}

/* Resolution */
.resolution-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-bottom: 1px solid #2a2a4a;
}

.res-label {
  font-size: 10px;
  color: #666;
  text-transform: uppercase;
}

.res-buttons {
  display: flex;
  gap: 4px;
}

.res-btn {
  padding: 4px 10px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #888;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.res-btn:hover {
  background: #33334a;
  color: #ccc;
}

.res-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}

/* Legend */
.legend {
  display: flex;
  gap: 16px;
  padding: 8px 12px;
  background: #1a1a2a;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: #888;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.material {
  background: #8B4513;
}

.legend-color.removed {
  background: #1a1a2e;
  border: 1px solid #3a3a5c;
}
</style>
