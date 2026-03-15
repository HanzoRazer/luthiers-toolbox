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

import { onMounted, onUnmounted, computed, ref, watch } from "vue";
import ToolpathCanvas from "./ToolpathCanvas.vue";
import ToolpathCanvas3D from "./ToolpathCanvas3D.vue";
import GcodeViewer from "./GcodeViewer.vue";
import MemoryWarning from "./MemoryWarning.vue";
import ToolpathStats from "./ToolpathStats.vue";
import ToolpathFilter from "./ToolpathFilter.vue";
import ToolpathAnnotations from "./ToolpathAnnotations.vue";
import ToolpathComparePanel from "./ToolpathComparePanel.vue";
import ToolpathAudioPanel from "./ToolpathAudioPanel.vue";
// Audio engine now managed by useToolpathAudio composable
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import { annotationManager, type Annotation } from "@/util/toolpathAnnotations";
import type { MoveSegment as CompareMoveSegment } from "@/util/toolpathComparison";
import { useTimeEstimates } from "@/composables/useTimeEstimates";
import { validateGcode, type ValidationResult } from "@/util/gcodeValidator";
import { buildMachineStates, type MachineState } from "@/util/mcodeTracker";
// P4 imports (moved to useToolpathAnalysis composable)
import type { Fixture } from "@/util/collisionDetector";
// P5 imports (export logic moved to useToolpathExport composable)
import { useToolpathShortcuts } from "@/composables/useToolpathShortcuts";
// P6 imports: Multi-tool support
import ToolLegendPanel from "./ToolLegendPanel.vue";
import { analyzeToolUsage, type ToolChangeMarker } from "@/util/toolpathTools";
// P6 Step 14: Feed optimization hints
import FeedAnalysisPanel from "./FeedAnalysisPanel.vue";
import type { FeedHint } from "@/util/feedOptimizer";
// P6 Step 15: Stock simulation preview
import StockSimulationPanel from "./StockSimulationPanel.vue";
// P6 Step 16: Chip load analysis
import ChipLoadPanel from "./ChipLoadPanel.vue";
import type { ChipLoadIssue } from "@/util/chipLoadAnalyzer";

// Extracted subcomponents (Phase 2 + Phase 3 + Phase 4 + Phase 5 + Phase 6 decomposition)
import {
  PlaybackControlsBar,
  ToolbarButtonGroup,
  PlayerHudBar,
  ExportAnimationPanel,
  CollisionPanel,
  OptimizationPanel,
  GcodeSourcePanel,
  KeyboardShortcutsOverlay,
  MeasurementsPanel,
  MeasureModeIndicator,
  PanelContainer,
  LoadingOverlay,
  ValidationOverlay,
  FloatingPanel,
  EmptyState,
  useToolpathAnalysis,
  useToolpathExport,
  useToolpathAudio,
  useToolpathNavigation,
  useToolpathPanelState,
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

// P5: Keyboard shortcuts
const { shortcuts, showHelp, hideHelp } = useToolpathShortcuts({
  onToggleHeatmap: () => {
    panels.heatmap.value = !panels.heatmap.value;
  },
  onToggleGcode: () => {
    panels.gcode.value = !panels.gcode.value;
  },
  onToggleViewMode: () => {
    if (props.enable3D) {
      viewMode.value = viewMode.value === "2d" ? "3d" : "2d";
    }
  },
  onResetView: () => {
    if (viewMode.value === "3d" && canvas3DRef.value) {
      (canvas3DRef.value as unknown as { resetView?: () => void }).resetView?.();
    }
  },
  onSetViewTop: () => {
    if (viewMode.value === "3d" && canvas3DRef.value) {
      (canvas3DRef.value as unknown as { setView?: (v: string) => void }).setView?.("top");
    }
  },
  onSetViewFront: () => {
    if (viewMode.value === "3d" && canvas3DRef.value) {
      (canvas3DRef.value as unknown as { setView?: (v: string) => void }).setView?.("front");
    }
  },
  onSetViewSide: () => {
    if (viewMode.value === "3d" && canvas3DRef.value) {
      (canvas3DRef.value as unknown as { setView?: (v: string) => void }).setView?.("side");
    }
  },
  enabled: true,
});

// ---------------------------------------------------------------------------
// Local state
// ---------------------------------------------------------------------------
const memDismissed = ref(false);
const resSlider = ref(100);
const validation = ref<ValidationResult | null>(null);

// P5: 3D view mode
const viewMode = ref<"2d" | "3d">(props.default3D ? "3d" : "2d");
const canvas3DRef = ref<InstanceType<typeof ToolpathCanvas3D> | null>(null);
const canvas2DRef = ref<InstanceType<typeof ToolpathCanvas> | null>(null);

// P5: Filter panel ref (for hasActiveFilter)
const filterPanelRef = ref<InstanceType<typeof ToolpathFilter> | null>(null);

// P5: Compare segments data
const compareSegments = ref<CompareMoveSegment[]>([]);

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
// Machine state array (P3 M-code tracking)
// ---------------------------------------------------------------------------
const machineStates = ref<MachineState[]>([]);

// Rebuild machine states when segments change
const currentMachine = computed<MachineState | null>(() => {
  const idx = store.currentSegmentIndex;
  if (idx < 0 || idx >= machineStates.value.length) return null;
  return machineStates.value[idx];
});

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
// Computed
// ---------------------------------------------------------------------------
const playIcon = computed(() =>
  store.playState === "playing" ? "⏸" : "▶",
);
const playLabel = computed(() =>
  store.playState === "playing" ? "Pause" : "Play",
);
const speeds = [0.5, 1, 2, 5, 10] as const;

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
function togglePlay(): void {
  if (store.playState === "playing") store.pause();
  else store.play();
}

function onScrubInput(e: Event): void {
  store.seek(parseFloat((e.target as HTMLInputElement).value));
}

function applyResolution(): void {
  store.setResolution(resSlider.value);
}

function formatTime(ms: number): string {
  const totalSecs = ms / 1000;
  const mins = Math.floor(totalSecs / 60);
  const secs = (totalSecs % 60).toFixed(1);
  return `${mins}:${secs.padStart(4, "0")}`;
}

async function doLoad(): Promise<void> {
  if (!props.gcode) return;
  await store.loadGcode(props.gcode, { arc_resolution_deg: 5 });
  machineStates.value = buildMachineStates(store.segments);

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
// P5: Annotations
// ---------------------------------------------------------------------------
function handleAnnotationGoto(annotation: Annotation): void {
  if (annotation.segmentIndex !== null) {
    // Jump to the segment
    const progress = annotation.segmentIndex / Math.max(1, store.segments.length - 1);
    store.seek(Math.min(1, Math.max(0, progress)));
  }
}

// ---------------------------------------------------------------------------
// P5: Compare
// ---------------------------------------------------------------------------
function handleCompareSegments(segments: CompareMoveSegment[]): void {
  compareSegments.value = segments;
}

function handleCompareOverlayToggle(enabled: boolean): void {
  showCompareOverlay.value = enabled;
}

// ---------------------------------------------------------------------------
// P6: Multi-tool support — now uses navigation composable
// ---------------------------------------------------------------------------
function handleToolSelect(toolNumber: number | null): void {
  selectedToolFilter.value = toolNumber;
}

function handleToolChangeClick(marker: ToolChangeMarker): void {
  navigation.jumpToSegment(marker.segmentIndex);
}

// ---------------------------------------------------------------------------
// P6 Step 14: Feed Analysis — now uses navigation composable
// ---------------------------------------------------------------------------
function handleFeedHintClick(hint: FeedHint): void {
  navigation.jumpToSegmentRange(hint.segmentRange[0], true);
}

// ---------------------------------------------------------------------------
// P6 Step 16: Chip Load Analysis — now uses navigation composable
// ---------------------------------------------------------------------------
function handleChipLoadIssueClick(issue: ChipLoadIssue): void {
  navigation.jumpToSegmentRange(issue.segmentRange[0], true);
}

// ---------------------------------------------------------------------------
// P5: Audio — now handled by useToolpathAudio composable
// ---------------------------------------------------------------------------

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

    <!-- ── Controls bar (using extracted subcomponents) ──────── -->
    <div
      v-if="props.showControls"
      class="controls-bar"
    >
      <ToolbarButtonGroup
        :enable3-d="props.enable3D"
        :view-mode="viewMode"
        :show-heatmap="panels.heatmap.value"
        :show-export-panel="showExportPanel"
        :is-exporting="isExporting"
        :measure-mode="store.measureMode"
        :show-help="showHelp"
        :show-stats-panel="panels.stats.value"
        :show-filter-panel="panels.filter.value"
        :has-active-filter="filterPanelRef?.hasActiveFilter ?? false"
        :show-annotations-panel="panels.annotations.value"
        :show-compare-panel="panels.compare.value"
        :show-compare-overlay="showCompareOverlay"
        :show-audio-panel="panels.audio.value"
        :has-multiple-tools="hasMultipleTools"
        :show-tool-legend-panel="panels.toolLegend.value"
        :show-feed-analysis-panel="panels.feedAnalysis.value"
        :show-stock-simulation-panel="panels.stockSimulation.value"
        :has-bounds="!!store.bounds"
        :show-chip-load-panel="panels.chipLoad.value"
        :segment-count="store.segments.length"
        :memory-info="store.memoryInfo"
        @update:view-mode="viewMode = $event"
        @update:show-heatmap="panels.heatmap.value = $event"
        @update:show-export-panel="showExportPanel = $event"
        @toggle-measure-mode="store.toggleMeasureMode()"
        @update:show-help="showHelp = $event"
        @update:show-stats-panel="panels.stats.value = $event"
        @update:show-filter-panel="panels.filter.value = $event"
        @update:show-annotations-panel="panels.annotations.value = $event"
        @update:show-compare-panel="panels.compare.value = $event"
        @update:show-audio-panel="panels.audio.value = $event"
        @update:show-tool-legend-panel="panels.toolLegend.value = $event"
        @update:show-feed-analysis-panel="panels.feedAnalysis.value = $event"
        @update:show-stock-simulation-panel="panels.stockSimulation.value = $event"
        @update:show-chip-load-panel="panels.chipLoad.value = $event"
      />
      <PlaybackControlsBar
        :play-state="store.playState"
        :progress="store.progress"
        :speed="store.speed"
        :segment-count="store.segments.length"
        @play="store.play()"
        @pause="store.pause()"
        @stop="store.stop()"
        @step-forward="store.stepForward()"
        @step-backward="store.stepBackward()"
        @seek="store.seek($event)"
        @set-speed="store.setSpeed($event)"
      />
    </div>

    <!-- ── Resolution slider (shown when memory warning) ─────── -->
    <div
      v-if="store.memoryInfo.isWarning && !store.loading"
      class="res-bar"
    >
      <span class="res-label">
        Resolution:
      </span>
      <input
        v-model.number="resSlider"
        type="range"
        class="res-slider"
        min="10"
        max="100"
      >
      <span class="res-val">{{ resSlider }}%</span>
      <button
        class="res-apply"
        @click="applyResolution"
      >
        Apply
      </button>
    </div>

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

    <!-- P5: Statistics Panel (using PanelContainer) -->
    <PanelContainer
      v-if="panels.stats.value && store.segments.length > 0"
      title="📊 Toolpath Statistics"
      accent="blue"
      position="top-left"
      @close="panels.stats.value = false"
    >
      <ToolpathStats :segments="store.segments" />
    </PanelContainer>

    <!-- P5: Filter Panel (using PanelContainer) -->
    <PanelContainer
      v-if="panels.filter.value && store.segments.length > 0"
      title="🔍 Segment Filter"
      accent="orange"
      position="top-right"
      width="340px"
      :z-index="13"
      @close="panels.filter.value = false"
    >
      <template #actions>
        <button
          v-if="filterPanelRef?.hasActiveFilter"
          class="action-btn"
          @click="filterPanelRef?.resetFilter()"
        >
          Reset
        </button>
      </template>
      <ToolpathFilter
        ref="filterPanelRef"
        :segments="store.segments"
      />
    </PanelContainer>

    <!-- P5: Annotations Panel -->
    <FloatingPanel
      v-if="panels.annotations.value && store.segments.length > 0"
      position="top-right"
      :z-index="14"
      accent="#4a90d9"
    >
      <ToolpathAnnotations
        :current-segment="store.currentSegmentIndex"
        :current-position="store.toolPosition as [number, number, number]"
        :current-line-number="store.currentSegment?.line_number ?? null"
        @close="panels.annotations.value = false"
        @goto="handleAnnotationGoto"
      />
    </FloatingPanel>

    <!-- P5: Compare Panel -->
    <FloatingPanel
      v-if="panels.compare.value && store.segments.length > 0"
      position="top-left"
      width="360px"
      :z-index="15"
      accent="#9b59b6"
    >
      <ToolpathComparePanel
        :base-segments="store.segments as CompareMoveSegment[]"
        :base-gcode="store.sourceGcode"
        @close="panels.compare.value = false"
        @compare-segments="handleCompareSegments"
        @overlay-toggle="handleCompareOverlayToggle"
      />
    </FloatingPanel>

    <!-- P5: Audio Panel -->
    <FloatingPanel
      v-if="panels.audio.value && store.segments.length > 0"
      position="top-right"
      :z-index="15"
      accent="#e9a840"
    >
      <ToolpathAudioPanel
        @close="panels.audio.value = false"
      />
    </FloatingPanel>

    <!-- P6: Tool Legend Panel -->
    <FloatingPanel
      v-if="panels.toolLegend.value && store.segments.length > 0"
      position="top-left"
      width="280px"
      :z-index="15"
      accent="#4a90d9"
    >
      <ToolLegendPanel
        :segments="store.segments"
        :current-segment-index="store.currentSegmentIndex"
        @tool-select="handleToolSelect"
        @tool-change-click="handleToolChangeClick"
        @close="panels.toolLegend.value = false"
      />
    </FloatingPanel>

    <!-- P6 Step 14: Feed Analysis Panel -->
    <FloatingPanel
      v-if="panels.feedAnalysis.value && store.segments.length > 0"
      position="top-right"
      width="360px"
      :z-index="16"
      accent="#f39c12"
    >
      <FeedAnalysisPanel
        :segments="store.segments"
        :tool-diameter="toolDiameter"
        @hint-click="handleFeedHintClick"
        @close="panels.feedAnalysis.value = false"
      />
    </FloatingPanel>

    <!-- P6 Step 15: Stock Simulation Panel -->
    <FloatingPanel
      v-if="panels.stockSimulation.value && store.segments.length > 0 && store.bounds"
      position="top-left"
      :z-index="17"
      accent="#8B4513"
    >
      <StockSimulationPanel
        :segments="store.segments"
        :current-segment-index="store.currentSegmentIndex"
        :bounds="store.bounds"
        :tool-diameter="toolDiameter"
        @close="panels.stockSimulation.value = false"
      />
    </FloatingPanel>

    <!-- P6 Step 16: Chip Load Panel -->
    <FloatingPanel
      v-if="panels.chipLoad.value && store.segments.length > 0"
      position="top-right"
      width="340px"
      :z-index="18"
      accent="#f39c12"
    >
      <ChipLoadPanel
        :segments="store.segments"
        :tool-diameter="toolDiameter"
        :flute-count="2"
        :default-rpm="18000"
        @issue-click="handleChipLoadIssueClick"
        @close="panels.chipLoad.value = false"
      />
    </FloatingPanel>

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

/* ── Controls bar ───────────────────────────────────────────────── */
.controls-bar {
  display: flex; align-items: center; gap: 6px; padding: 7px 10px;
  background: #13131f; border-top: 1px solid #2a2a4a; flex-shrink: 0;
}

/* ── View toggle + playback controls moved to ToolbarButtonGroup.vue and PlaybackControlsBar.vue ── */

/* ── Resolution bar ─────────────────────────────────────────────── */
.res-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: #1a1a2e;
  border-top: 1px solid #2a2a4a;
  font-size: 11px;
  color: #aaa;
}
.res-label { color: #666; }
.res-slider { flex: 1; accent-color: #4a90d9; height: 4px; }
.res-val { min-width: 36px; color: #4a90d9; }
.res-apply {
  padding: 2px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #ccc;
  border-radius: 4px;
  cursor: pointer;
}
.res-apply:hover { background: #33334a; color: #fff; }

/* ── HUD bar styles moved to PlayerHudBar.vue ── */

/* ── P4: Panel styles moved to CollisionPanel.vue and OptimizationPanel.vue ── */
/* ── P5: G-code panel styles moved to GcodeSourcePanel.vue ── */
/* ── P5: Measure mode/measurements styles moved to MeasureModeIndicator.vue and MeasurementsPanel.vue ── */

/* ── Shared panel header — now handled by PanelContainer ── */

/* ── P5: Help button — moved to ToolbarButtonGroup.vue ────────────── */

/* ── P5: Shortcuts Overlay styles moved to KeyboardShortcutsOverlay.vue ── */

/* ── P5: Stats button — moved to ToolbarButtonGroup.vue ────────────── */

/* ── P5: Stats Panel — now uses PanelContainer ─────────────────────── */

/* ── P5: Filter button — moved to ToolbarButtonGroup.vue ─────────── */

/* ── P5: Filter Panel — now uses PanelContainer ────────────────────── */

/* ── P5/P6: Panel containers now use FloatingPanel component ─────────── */
</style>
