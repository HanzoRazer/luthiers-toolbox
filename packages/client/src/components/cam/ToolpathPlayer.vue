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

import { computed, ref, type Ref } from "vue";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import { useTimeEstimates } from "@/composables/useTimeEstimates";
import type { Fixture } from "@/util/collisionDetector";
import { useToolpathShortcuts } from "@/composables/useToolpathShortcuts";
import { analyzeToolUsage } from "@/util/toolpathTools";

// Extracted subcomponents (Phase 2-11 decomposition)
import {
  PlayerHudBar,
  ResolutionSlider,
  ControlsBarWrapper,
  PanelsLayer,
  OverlaysLayer,
  ModalPanelsLayer,
  CanvasLayer,
  useToolpathAnalysis,
  useToolpathAudio,
  useToolpathNavigation,
  useToolpathPanelState,
  useToolpathViewControls,
  useToolpathEventHandlers,
  useToolpathMachine,
  useToolpathCanvasExport,
  useToolpathLifecycle,
} from "./toolpath-player";
import ToolpathCanvas from "./ToolpathCanvas.vue";
import ToolpathCanvas3D from "./ToolpathCanvas3D.vue";

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
const canvas2DRef = ref<InstanceType<typeof ToolpathCanvas> | null>(null);

// P9: Panels layer ref (for accessing filter panel)
const panelsLayerRef = ref<InstanceType<typeof PanelsLayer> | null>(null);

// Computed filter panel ref (via PanelsLayer)
const filterPanelRef = computed(() => panelsLayerRef.value?.filterPanelRef ?? null);

// P5: Compare segments data
const compareSegments = ref<unknown[]>([]);

// P10: Export animation with canvas retrieval (via composable)
const canvasExport = useToolpathCanvasExport({
  viewMode,
  canvas2DRef: canvas2DRef as any,
  canvas3DRef: canvas3DRef as any,
  totalDurationMs: computed(() => store.totalDurationMs),
  onPlayFromStart: () => { store.stop(); store.play(); },
  onPause: () => store.pause(),
});
const { showExportPanel, isExporting, exportProgress, exportConfig } = canvasExport;

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
// NOTE: analysis must be defined before lifecycle (it's passed to lifecycle config)
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
} = analysis;

// ---------------------------------------------------------------------------
// P11: Lifecycle management (via composable)
// ---------------------------------------------------------------------------
const lifecycle = useToolpathLifecycle({
  gcode: props.gcode,
  autoPlay: props.autoPlay,
  enableCollisionDetection: props.enableCollisionDetection,
  enableOptimization: props.enableOptimization,
  store,
  analysis,
  machine,
});
const { validationErrors, hasErrors, doLoad } = lifecycle;

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
</script>

<template>
  <div
    class="toolpath-player"
    :style="{ height: props.height }"
  >
    <!-- P11: Canvas layer (2D or 3D based on viewMode) -->
    <CanvasLayer
      v-model:canvas2-d-ref="canvas2DRef"
      v-model:canvas3-d-ref="canvas3DRef"
      :view-mode="viewMode"
      :show-heatmap="panels.heatmap.value"
      :tool-diameter="toolDiameter"
      :color-by-tool="hasMultipleTools"
      :tool-filter="selectedToolFilter"
    />

    <!-- P10: Consolidated overlays (loading, memory, validation, empty) -->
    <OverlaysLayer
      :loading="store.loading"
      :parse-progress="store.parseProgress"
      :show-mem-banner="showMemBanner"
      :memory-info="store.memoryInfo"
      :has-errors="hasErrors"
      :validation-errors="validationErrors"
      :segment-count="store.segments.length"
      :error="store.error"
      @dismiss-memory="memDismissed = true"
      @optimize-memory="store.setResolution(50)"
      @load-anyway="doLoad"
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

    <!-- P10: Consolidated modal panels -->
    <ModalPanelsLayer
      :show-collision-panel="showCollisionPanel"
      :collision-report="collisionReport"
      :show-opt-panel="showOptPanel"
      :optimization-report="optimizationReport"
      :show-gcode-panel="panels.gcode.value"
      :has-source-gcode="!!store.sourceGcode"
      :has-selection="store.selectedSegmentIndex !== null"
      :show-export-panel="showExportPanel"
      :is-exporting="isExporting"
      :export-config="exportConfig"
      :export-progress="exportProgress"
      :measure-mode="store.measureMode"
      :pending-measure-start="!!store.pendingMeasureStart"
      :show-help="showHelp"
      :shortcuts="shortcuts"
      :measurements="store.measurements"
      :measure-tool="store.measureTool"
      :measurements-collapsed="!panels.measurements.value"
      @update:show-collision-panel="showCollisionPanel = $event"
      @update:show-opt-panel="showOptPanel = $event"
      @update:show-gcode-panel="panels.gcode.value = $event"
      @clear-selection="store.clearSelection()"
      @update:show-export-panel="showExportPanel = $event"
      @update:export-config="Object.assign(exportConfig, $event)"
      @start-export="canvasExport.startCanvasExport()"
      @cancel-export="canvasExport.cancelCanvasExport()"
      @cancel-measurement="store.cancelMeasurement()"
      @hide-help="hideHelp"
      @remove-measurement="store.removeMeasurement($event)"
      @clear-measurements="store.clearMeasurements()"
      @update:measurements-collapsed="panels.measurements.value = !$event"
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

/* P11: canvas-area style moved to CanvasLayer.vue */
</style>
