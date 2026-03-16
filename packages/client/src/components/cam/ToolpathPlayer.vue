<script setup lang="ts">
/**
 * ToolpathPlayer — P1-P5 Full Integration
 *
 * Drop-in animated G-code toolpath player. Composes:
 *   - ToolpathCanvas  (LOD canvas renderer + tool viz)
 *   - ToolpathCanvas3D (Three.js 3D renderer) [P5]
 *   - MemoryWarning   (large-file alert banner)
 *   - Controls bar    (play/pause, scrub, speed, resolution slider)
 *   - HUD bar         (G-code line, Z, feed, time, M-code state, estimate)
 *
 * P1: Memory management, progress indicator, G-code validation
 * P2: Caching (sessionStorage), LOD (in canvas)
 * P3: M-code HUD, tool viz (in canvas), time estimates
 * P4: Collision detection, optimization suggestions, stock simulation
 * P5: 3D Three.js visualization with orbit controls
 */

import { onMounted, onUnmounted, computed, ref, watch, type Ref } from "vue";
import ToolpathCanvas from "./ToolpathCanvas.vue";
import ToolpathCanvas3D from "./ToolpathCanvas3D.vue";
import GcodeViewer from "./GcodeViewer.vue";
import MemoryWarning from "./MemoryWarning.vue";
import ToolpathFilter from "./ToolpathFilter.vue";
// Audio engine now managed by useToolpathAudio composable
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import { annotationManager } from "@/util/toolpathAnnotations";
import { useTimeEstimates } from "@/composables/useTimeEstimates";
import { validateGcode, type ValidationResult } from "@/util/gcodeValidator";
// P4 imports (moved to useToolpathAnalysis composable)
import type { Fixture } from "@/util/collisionDetector";
// P5 imports (export logic moved to useToolpathExport composable)
import { useToolpathShortcuts } from "@/composables/useToolpathShortcuts";
// P6 imports: Multi-tool support
import { analyzeToolUsage } from "@/util/toolpathTools";

// Extracted subcomponents (Phase 2-7 decomposition)
import {
  PlayerHudBar,
  ExportAnimationPanel,
  CollisionPanel,
  OptimizationPanel,
  GcodeSourcePanel,
  KeyboardShortcutsOverlay,
  MeasurementsPanel,
  MeasureModeIndicator,
  LoadingOverlay,
  ValidationOverlay,
  EmptyState,
  ResolutionSlider,
  ControlsBarWrapper,
  PanelsLayer,
  useToolpathAnalysis,
  useToolpathExport,
  useToolpathAudio,
  useToolpathNavigation,
  useToolpathPanelState,
  useToolpathViewControls,
  useToolpathEventHandlers,
  useToolpathMachine,
} from "./toolpath-player";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface Props {
  gcode?: string;
  showHud?: boolean;
  showControls?: boolean;
  autoPlay?: boolean;
  height?: string;
  // P4 props
  enableCollisionDetection?: boolean;
  enableOptimization?: boolean;
  toolDiameter?: number;
  fixtures?: Fixture[];
  safeZ?: number;
  // P5 props
  enable3D?: boolean;
  default3D?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  gcode: undefined,
  showHud: true,
  showControls: true,
  autoPlay: false,
  height: "500px",
  // P4 defaults
  enableCollisionDetection: true,
  enableOptimization: true,
  toolDiameter: 6,
  fixtures: () => [],
  safeZ: 5,
  // P5 defaults
  enable3D: true,
  default3D: false,
});

// ---------------------------------------------------------------------------
// Store + composables
// ---------------------------------------------------------------------------
const store = useToolpathPlayerStore();
const { estimates } = useTimeEstimates(computed(() => store.segments));

// P6: Consolidated panel visibility state (must be before shortcuts)
const { panels, showCompareOverlay } = useToolpathPanelState();

// P5: 3D view mode (must be before view controls)
const viewMode = ref<"2d" | "3d">(props.default3D ? "3d" : "2d");
const canvas3DRef = ref<InstanceType<typeof ToolpathCanvas3D> | null>(null);

// P7: View controls (via composable)
const viewControls = useToolpathViewControls({
  viewMode,
  canvas3DRef: canvas3DRef as Ref<{ resetView?: () => void; setView?: (v: string) => void } | null>,
  enable3D: props.enable3D,
});

// P5: Keyboard shortcuts
const { shortcuts, showHelp, hideHelp } = useToolpathShortcuts({
  onToggleHeatmap: () => { panels.heatmap.value = !panels.heatmap.value; },
  onToggleGcode: () => { panels.gcode.value = !panels.gcode.value; },
  onToggleViewMode: viewControls.toggleViewMode,
  onResetView: viewControls.resetView,
  onSetViewTop: viewControls.setViewTop,
  onSetViewFront: viewControls.setViewFront,
  onSetViewSide: viewControls.setViewSide,
  enabled: true,
});

// ---------------------------------------------------------------------------
// Local state
// ---------------------------------------------------------------------------
const memDismissed = ref(false);
const validation = ref<ValidationResult | null>(null);
const canvas2DRef = ref<InstanceType<typeof ToolpathCanvas> | null>(null);

// P9: Panels layer ref (for accessing filter panel)
const panelsLayerRef = ref<InstanceType<typeof PanelsLayer> | null>(null);

// Computed filter panel ref (via PanelsLayer)
const filterPanelRef = computed(() => panelsLayerRef.value?.filterPanelRef ?? null);

// P5: Compare segments data
const compareSegments = ref<unknown[]>([]);

// P5: Export animation (via composable)
const exportState = useToolpathExport();
const { showExportPanel, isExporting, exportProgress, exportConfig } = exportState;

// P6: Multi-tool filter
const selectedToolFilter = ref<number | null>(null);
const hasMultipleTools = computed(() => {
  const tools = analyzeToolUsage(store.segments);
  return tools.length > 1;
});

// ---------------------------------------------------------------------------
// P9: Machine state tracking (via composable)
// ---------------------------------------------------------------------------
const machine = useToolpathMachine({
  currentSegmentIndex: computed(() => store.currentSegmentIndex),
});
const { currentMachine } = machine;

// ---------------------------------------------------------------------------
// P4: Collision Detection & Optimization (via composable)
// ---------------------------------------------------------------------------
const analysis = useToolpathAnalysis({
  enableCollisionDetection: props.enableCollisionDetection,
  enableOptimization: props.enableOptimization,
  toolDiameter: props.toolDiameter,
  safeZ: props.safeZ,
  fixtures: props.fixtures,
});

const {
  collisionReport,
  optimizationReport,
  showCollisionPanel,
  showOptPanel,
  hasCollisions,
  hasCriticalCollisions,
  hasOptimizations,
} = analysis;

// Active collisions at current segment
const activeCollisions = computed(() =>
  analysis.activeCollisions(store.currentSegmentIndex)
);

// ---------------------------------------------------------------------------
// P5: Audio sync (via composable)
// ---------------------------------------------------------------------------
useToolpathAudio({
  segments: computed(() => store.segments),
  bounds: computed(() => store.bounds),
  playState: computed(() => store.playState),
  currentSegmentIndex: computed(() => store.currentSegmentIndex),
  progress: computed(() => store.progress),
  totalDurationMs: computed(() => store.totalDurationMs),
});

// ---------------------------------------------------------------------------
// P6: Navigation helpers (via composable)
// ---------------------------------------------------------------------------
const navigation = useToolpathNavigation({
  segments: computed(() => store.segments),
  totalDurationMs: computed(() => store.totalDurationMs),
  seek: (p) => store.seek(p),
  pause: () => store.pause(),
});

// ---------------------------------------------------------------------------
// P8: Event handlers (via composable)
// ---------------------------------------------------------------------------
const eventHandlers = useToolpathEventHandlers({
  segments: store.segments,
  compareSegments,
  showCompareOverlay,
  selectedToolFilter,
  navigation,
  seek: (p) => store.seek(p),
});

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------
const showMemBanner = computed(
  () =>
    store.memoryInfo.isWarning &&
    !store.loading &&
    store.segments.length > 0 &&
    !memDismissed.value,
);

const validationErrors = computed(
  () => validation.value?.issues.filter((i) => i.severity === "error") ?? [],
);
const hasErrors = computed(() => validationErrors.value.length > 0);

// ---------------------------------------------------------------------------
// Methods
// ---------------------------------------------------------------------------
async function doLoad(): Promise<void> {
  if (!props.gcode) return;
  await store.loadGcode(props.gcode, { arc_resolution_deg: 5 });
  machine.buildStates(store.segments);

  // P5: Initialize annotations for this G-code
  annotationManager.init(props.gcode);

  // P4: Run collision detection
  if (props.enableCollisionDetection && store.segments.length > 0) {
    runCollisionDetection();
  }

  // P4: Run optimization analysis
  if (props.enableOptimization && store.segments.length > 0) {
    runOptimizationAnalysis();
  }

  if (props.autoPlay) store.play();
}

// ---------------------------------------------------------------------------
// P4: Collision Detection & Optimization - now via composable
// ---------------------------------------------------------------------------
function runCollisionDetection(): void {
  analysis.runCollisionDetection(store.segments, store.bounds);
}

function runOptimizationAnalysis(): void {
  analysis.runOptimizationAnalysis(store.segments, store.totalDurationMs);
}

// ---------------------------------------------------------------------------
// P5: Export Animation - now via composable
// ---------------------------------------------------------------------------
async function startExport(): Promise<void> {
  // Get the canvas element from the component
  let canvasEl: HTMLCanvasElement | null = null;

  if (viewMode.value === "2d" && canvas2DRef.value) {
    canvasEl = (canvas2DRef.value as unknown as { $el: HTMLElement }).$el?.querySelector("canvas");
  } else if (viewMode.value === "3d" && canvas3DRef.value) {
    canvasEl = (canvas3DRef.value as unknown as { $el: HTMLElement }).$el?.querySelector("canvas");
  }

  if (!canvasEl) {
    console.error("Cannot find canvas element for export");
    return;
  }

  await exportState.startExport(
    canvasEl,
    store.totalDurationMs,
    () => { store.stop(); store.play(); },
    () => { store.pause(); }
  );
}

function cancelExport(): void {
  exportState.cancelExport(() => { store.pause(); });
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(async () => {
  if (props.gcode) {
    validation.value = validateGcode(props.gcode);
    if (!hasErrors.value) await doLoad();
  }
});

onUnmounted(() => {
  store.dispose();
});
</script>

<template>
  <div
    class="toolpath-player"
    :style="{ height: props.height }"
  >
    <!-- ── Canvas (2D or 3D based on viewMode) ─────────────────── -->
    <ToolpathCanvas
      v-if="viewMode === '2d'"
      ref="canvas2DRef"
      class="canvas-area"
      :show-heatmap="panels.heatmap.value"
      :tool-diameter="toolDiameter"
      :color-by-tool="hasMultipleTools"
      :tool-filter="selectedToolFilter"
    />
    <ToolpathCanvas3D
      v-else
      ref="canvas3DRef"
      class="canvas-area"
      :tool-diameter="toolDiameter"
      :show-stock="true"
      :show-grid="true"
      :show-heatmap="panels.heatmap.value"
    />

    <!-- ── Loading overlay with progress (P1) - extracted ───── -->
    <LoadingOverlay
      v-if="store.loading"
      :progress="store.parseProgress"
    />

    <!-- ── Memory warning banner (P1) ────────────────────────── -->
    <MemoryWarning
      v-if="showMemBanner"
      :memory-info="store.memoryInfo"
      @close="memDismissed = true"
      @optimize="store.setResolution(50)"
    />

    <!-- ── Validation error overlay (P1) - extracted ────────── -->
    <ValidationOverlay
      v-if="hasErrors && !store.loading && store.segments.length === 0"
      :errors="validationErrors"
      @load-anyway="doLoad"
    />

    <!-- ── Error / Empty state - extracted ───────────────────── -->
    <EmptyState
      v-if="!store.loading && !hasErrors && store.segments.length === 0"
      :error="store.error"
    />

    <!-- ── Controls bar (using extracted P8 wrapper) ──────────── -->
    <ControlsBarWrapper
      v-if="props.showControls"
      :enable3-d="props.enable3D"
      :view-mode="viewMode"
      :panels="panels"
      :show-export-panel="showExportPanel"
      :show-compare-overlay="showCompareOverlay"
      :is-exporting="isExporting"
      :measure-mode="store.measureMode"
      :show-help="showHelp"
      :has-active-filter="filterPanelRef?.hasActiveFilter ?? false"
      :has-multiple-tools="hasMultipleTools"
      :has-bounds="!!store.bounds"
      :segment-count="store.segments.length"
      :memory-info="store.memoryInfo"
      :play-state="store.playState"
      :progress="store.progress"
      :speed="store.speed"
      @update:view-mode="viewMode = $event"
      @update:show-export-panel="showExportPanel = $event"
      @update:show-help="showHelp = $event"
      @toggle-measure-mode="store.toggleMeasureMode()"
      @play="store.play()"
      @pause="store.pause()"
      @stop="store.stop()"
      @step-forward="store.stepForward()"
      @step-backward="store.stepBackward()"
      @seek="store.seek($event)"
      @set-speed="store.setSpeed($event)"
    />

    <!-- ── Resolution slider (shown when memory warning) - extracted ── -->
    <ResolutionSlider
      :visible="store.memoryInfo.isWarning && !store.loading"
      @apply="store.setResolution($event)"
    />

    <!-- ── HUD bar (using extracted subcomponent) ────────────── -->
    <PlayerHudBar
      v-if="props.showHud"
      :current-line-text="store.currentSegment?.line_text ?? null"
      :current-feed="store.currentSegment?.feed ?? 0"
      :tool-position="store.toolPosition"
      :current-time-ms="store.currentTimeMs"
      :total-duration-ms="store.totalDurationMs"
      :machine-state="currentMachine"
      :estimates="estimates"
      :collision-report="collisionReport"
      :optimization-report="optimizationReport"
      :selected-segment-index="store.selectedSegmentIndex"
      :selected-gcode-line="store.selectedGcodeLine"
      :show-gcode-panel="panels.gcode.value"
      :show-collision-panel="showCollisionPanel"
      :show-opt-panel="showOptPanel"
      @update:show-gcode-panel="panels.gcode.value = $event"
      @update:show-collision-panel="showCollisionPanel = $event"
      @update:show-opt-panel="showOptPanel = $event"
      @jump-to-selected="store.jumpToSelected()"
    />

    <!-- P4: Collision Panel (extracted) -->
    <CollisionPanel
      v-if="showCollisionPanel && collisionReport"
      :report="collisionReport"
      @close="showCollisionPanel = false"
    />

    <!-- P4: Optimization Panel (extracted) -->
    <OptimizationPanel
      v-if="showOptPanel && optimizationReport"
      :report="optimizationReport"
      @close="showOptPanel = false"
    />

    <!-- P5: G-code Source Panel (extracted) -->
    <GcodeSourcePanel
      v-if="panels.gcode.value && store.sourceGcode"
      :has-selection="store.selectedSegmentIndex !== null"
      @close="panels.gcode.value = false"
      @clear-selection="store.clearSelection()"
    />

    <!-- P5: Export Panel (using extracted subcomponent) -->
    <ExportAnimationPanel
      v-if="showExportPanel"
      :is-exporting="isExporting"
      :config="exportConfig"
      :export-progress="exportProgress"
      @close="showExportPanel = false"
      @update:config="Object.assign(exportConfig, $event)"
      @start-export="startExport"
      @cancel-export="cancelExport"
    />

    <!-- P5: Measure mode indicator (extracted) -->
    <MeasureModeIndicator
      v-if="store.measureMode"
      :pending-start="!!store.pendingMeasureStart"
      @cancel="store.cancelMeasurement()"
    />

    <!-- P5: Keyboard Shortcuts Help Overlay (extracted) -->
    <KeyboardShortcutsOverlay
      v-if="showHelp"
      :shortcuts="shortcuts"
      @close="hideHelp"
    />

    <!-- P9: Consolidated floating panels -->
    <PanelsLayer
      ref="panelsLayerRef"
      :panels="panels"
      :segments="(store.segments as any)"
      :segment-count="store.segments.length"
      :source-gcode="store.sourceGcode"
      :current-segment-index="store.currentSegmentIndex"
      :tool-position="store.toolPosition as [number, number, number]"
      :current-line-number="store.currentSegment?.line_number ?? null"
      :tool-diameter="toolDiameter"
      :bounds="store.bounds"
      :event-handlers="eventHandlers"
    />

    <!-- P5: Measurements Panel (extracted) -->
    <MeasurementsPanel
      v-if="store.measurements.length > 0"
      :measurements="store.measurements"
      :measure-tool="store.measureTool"
      :collapsed="!panels.measurements.value"
      @remove="store.removeMeasurement($event)"
      @clear="store.clearMeasurements()"
      @update:collapsed="panels.measurements.value = !$event"
    />
  </div>
</template>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────── */
.toolpath-player {
  position: relative;
  display: flex;
  flex-direction: column;
  background: #1e1e2e;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #2a2a4a;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
}

.canvas-area {
  flex: 1;
  min-height: 0;
}

/* ── Overlays moved to ValidationOverlay.vue and EmptyState.vue ───── */
/* ── Controls bar moved to ControlsBarWrapper.vue ── */
</style>
