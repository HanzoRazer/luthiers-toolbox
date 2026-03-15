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
import { getAudioEngine, type MoveSegment as AudioMoveSegment } from "@/util/toolpathAudio";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import { annotationManager, type Annotation } from "@/util/toolpathAnnotations";
import type { MoveSegment as CompareMoveSegment } from "@/util/toolpathComparison";
import { useTimeEstimates } from "@/composables/useTimeEstimates";
import { validateGcode, type ValidationResult } from "@/util/gcodeValidator";
import { buildMachineStates, type MachineState } from "@/util/mcodeTracker";
// P4 imports
import { CollisionDetector, type CollisionReport, type Fixture } from "@/util/collisionDetector";
import { GcodeOptimizer, type OptimizationReport } from "@/util/gcodeOptimizer";
// P5 imports
import { AnimationExporter, downloadExport, type ExportConfig, type ExportProgress } from "@/util/animationExporter";
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

// Extracted subcomponents (Phase 2 decomposition)
import {
  PlaybackControlsBar,
  ToolbarButtonGroup,
  PlayerHudBar,
  ExportAnimationPanel,
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

// P5: Keyboard shortcuts
const { shortcuts, showHelp, hideHelp } = useToolpathShortcuts({
  onToggleHeatmap: () => {
    showHeatmap.value = !showHeatmap.value;
  },
  onToggleGcode: () => {
    showGcodePanel.value = !showGcodePanel.value;
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

// P5: G-code viewer panel
const showGcodePanel = ref(false);

// P5: Heatmap mode
const showHeatmap = ref(false);

// P5: Measurements panel
const showMeasurementsPanel = ref(true);

// P5: Statistics panel
const showStatsPanel = ref(false);

// P5: Filter panel
const showFilterPanel = ref(false);
const filterPanelRef = ref<InstanceType<typeof ToolpathFilter> | null>(null);

// P5: Annotations panel
const showAnnotationsPanel = ref(false);

// P5: Compare panel
const showComparePanel = ref(false);
const compareSegments = ref<CompareMoveSegment[]>([]);
const showCompareOverlay = ref(false);

// P5: Audio panel
const showAudioPanel = ref(false);
const audioEngine = getAudioEngine();
// P5: Export animation
const showExportPanel = ref(false);
const isExporting = ref(false);
const exportProgress = ref<ExportProgress | null>(null);
const exportConfig = ref<Partial<ExportConfig>>({
  format: "webm",
  fps: 30,
  quality: 0.8,
  duration: null,
});
const canvas2DRef = ref<InstanceType<typeof ToolpathCanvas> | null>(null);
let exporter: AnimationExporter | null = null;

// P6: Multi-tool legend panel
const showToolLegendPanel = ref(false);
const selectedToolFilter = ref<number | null>(null);
const hasMultipleTools = computed(() => {
  const tools = analyzeToolUsage(store.segments);
  return tools.length > 1;
});

// P6 Step 14: Feed analysis panel
const showFeedAnalysisPanel = ref(false);

// P6 Step 15: Stock simulation panel
const showStockSimulationPanel = ref(false);

// P6 Step 16: Chip load analysis panel
const showChipLoadPanel = ref(false);

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
// P4: Collision Detection
// ---------------------------------------------------------------------------
const collisionReport = ref<CollisionReport | null>(null);
const showCollisionPanel = ref(false);

const hasCollisions = computed(() =>
  collisionReport.value && collisionReport.value.collisions.length > 0
);
const hasCriticalCollisions = computed(() =>
  collisionReport.value && collisionReport.value.criticalCount > 0
);

// Active collisions at current segment
const activeCollisions = computed(() => {
  if (!collisionReport.value) return [];
  const idx = store.currentSegmentIndex;
  return collisionReport.value.collisions.filter(c => c.segmentIndex <= idx);
});

// ---------------------------------------------------------------------------
// P4: Optimization Suggestions
// ---------------------------------------------------------------------------
const optimizationReport = ref<OptimizationReport | null>(null);
const showOptPanel = ref(false);

const hasOptimizations = computed(() =>
  optimizationReport.value && optimizationReport.value.suggestions.length > 0
);

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
// P4: Collision Detection
// ---------------------------------------------------------------------------
function runCollisionDetection(): void {
  const detector = new CollisionDetector({
    toolDiameter: props.toolDiameter,
    safeZ: props.safeZ,
    fixtures: props.fixtures,
    stock: store.bounds ? {
      bounds: store.bounds,
      resolution: 1,
      width: 100,
      height: 100,
      thickness: Math.abs(store.bounds.z_min) + 5,
      voxels: new Uint8Array(10000).fill(255),
      originalVoxels: new Uint8Array(10000).fill(255),
    } : undefined,
  });

  collisionReport.value = detector.checkAll(store.segments);
}

// ---------------------------------------------------------------------------
// P4: Optimization Analysis
// ---------------------------------------------------------------------------
function runOptimizationAnalysis(): void {
  const optimizer = new GcodeOptimizer({
    safeZ: props.safeZ,
    stockTopZ: 0,
    originalTime: store.totalDurationMs,
  });

  optimizationReport.value = optimizer.analyze(store.segments);
}

// ---------------------------------------------------------------------------
// P5: Export Animation
// ---------------------------------------------------------------------------
async function startExport(): Promise<void> {
  if (isExporting.value) return;

  // Get the canvas element - need to access the actual canvas from the component
  let canvasEl: HTMLCanvasElement | null = null;

  if (viewMode.value === "2d" && canvas2DRef.value) {
    // Access the canvas element from ToolpathCanvas component
    canvasEl = (canvas2DRef.value as unknown as { $el: HTMLElement }).$el?.querySelector("canvas");
  } else if (viewMode.value === "3d" && canvas3DRef.value) {
    // Access the canvas element from ToolpathCanvas3D component
    canvasEl = (canvas3DRef.value as unknown as { $el: HTMLElement }).$el?.querySelector("canvas");
  }

  if (!canvasEl) {
    console.error("Cannot find canvas element for export");
    return;
  }

  isExporting.value = true;
  showExportPanel.value = false;

  exporter = new AnimationExporter(exportConfig.value);

  // Calculate duration - full animation or custom
  const durationMs = exportConfig.value.duration
    ? exportConfig.value.duration * 1000
    : store.totalDurationMs;

  // Reset playback to start
  store.stop();

  // Wait a frame for reset
  await new Promise(r => setTimeout(r, 50));

  // Start playback
  store.play();

  const result = await exporter.exportFromCanvas(
    canvasEl,
    durationMs,
    (progress) => {
      exportProgress.value = progress;
    },
    () => {
      // Frame callback - advance animation
      // The store's play() handles animation, we just let it run
    }
  );

  isExporting.value = false;
  store.pause();

  if (result.success) {
    downloadExport(result);
    exportProgress.value = {
      phase: "complete",
      percent: 100,
      message: `Exported ${result.filename}`,
      framesCaptured: exportProgress.value?.totalFrames ?? 0,
      totalFrames: exportProgress.value?.totalFrames ?? 0,
    };

    // Clear progress after 3 seconds
    setTimeout(() => {
      exportProgress.value = null;
    }, 3000);
  } else {
    exportProgress.value = {
      phase: "error",
      percent: 0,
      message: result.error || "Export failed",
      framesCaptured: 0,
      totalFrames: 0,
    };
  }
}

function cancelExport(): void {
  if (exporter) {
    exporter.cancel();
    exporter = null;
  }
  isExporting.value = false;
  exportProgress.value = null;
  store.pause();
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
// P6: Multi-tool support
// ---------------------------------------------------------------------------
function handleToolSelect(toolNumber: number | null): void {
  selectedToolFilter.value = toolNumber;
  // Could emit to canvas to highlight/filter by tool
}

function handleToolChangeClick(marker: ToolChangeMarker): void {
  // Jump to the segment where tool change occurred
  if (marker.segmentIndex >= 0 && marker.segmentIndex < store.segments.length) {
    // Calculate cumulative time up to this segment
    let time = 0;
    for (let i = 0; i < marker.segmentIndex; i++) {
      time += store.segments[i].duration_ms;
    }
    store.seek(time / store.totalDurationMs);
  }
}

// ---------------------------------------------------------------------------
// P6 Step 14: Feed Analysis
// ---------------------------------------------------------------------------
function handleFeedHintClick(hint: FeedHint): void {
  // Jump to the first segment in the hint range
  const [startIdx] = hint.segmentRange;
  if (startIdx >= 0 && startIdx < store.segments.length) {
    let time = 0;
    for (let i = 0; i < startIdx; i++) {
      time += store.segments[i].duration_ms;
    }
    store.seek(time / store.totalDurationMs);
    // Pause so user can inspect
    store.pause();
  }
}

// ---------------------------------------------------------------------------
// P6 Step 16: Chip Load Analysis
// ---------------------------------------------------------------------------
function handleChipLoadIssueClick(issue: ChipLoadIssue): void {
  // Jump to the first segment in the issue range
  const [startIdx] = issue.segmentRange;
  if (startIdx >= 0 && startIdx < store.segments.length) {
    let time = 0;
    for (let i = 0; i < startIdx; i++) {
      time += store.segments[i].duration_ms;
    }
    store.seek(time / store.totalDurationMs);
    // Pause so user can inspect
    store.pause();
  }
}

// ---------------------------------------------------------------------------
// P5: Audio
// ---------------------------------------------------------------------------

// Initialize audio engine bounds when segments load
watch(
  () => store.bounds,
  (bounds) => {
    if (bounds) {
      audioEngine.setBounds(bounds.z_min, bounds.z_max, 100, 3000);
    }
  }
);

// Sync audio with playback state
watch(
  () => store.playState,
  (state) => {
    if (state === "playing") {
      audioEngine.start();
    } else {
      audioEngine.stop();
    }
  }
);

// Update audio based on current segment
watch(
  () => [store.currentSegmentIndex, store.progress] as const,
  ([segIdx, progress]) => {
    const seg = store.segments[segIdx];
    if (seg && store.playState === "playing") {
      const segProgress = (progress * store.totalDurationMs - getSegmentStartTime(segIdx)) / seg.duration_ms;
      audioEngine.updateForSegment(seg as AudioMoveSegment, Math.max(0, Math.min(1, segProgress)));
    }
  }
);

// Helper to get segment start time
function getSegmentStartTime(idx: number): number {
  let time = 0;
  for (let i = 0; i < idx; i++) {
    time += store.segments[i].duration_ms;
  }
  return time;
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
      :show-heatmap="showHeatmap"
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
      :show-heatmap="showHeatmap"
    />

    <!-- ── Loading overlay with progress (P1) ────────────────── -->
    <div
      v-if="store.loading"
      class="loading-overlay"
    >
      <div class="loading-inner">
        <svg
          class="spinner"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            cx="12"
            cy="12"
            r="10"
            stroke="#4A90D9"
            stroke-width="2"
            stroke-dasharray="32"
            stroke-linecap="round"
          />
        </svg>
        <div class="progress-box">
          <span class="progress-label">
            {{ store.parseProgress.stage === "uploading"
              ? "Uploading…"
              : store.parseProgress.stage === "simulating"
                ? "Simulating…"
                : "Loading…" }}
            {{ store.parseProgress.percent }}%
          </span>
          <div class="progress-track">
            <div
              class="progress-fill"
              :style="{ width: store.parseProgress.percent + '%' }"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- ── Memory warning banner (P1) ────────────────────────── -->
    <MemoryWarning
      v-if="showMemBanner"
      :memory-info="store.memoryInfo"
      @close="memDismissed = true"
      @optimize="store.setResolution(50)"
    />

    <!-- ── Validation error overlay (P1) ─────────────────────── -->
    <div
      v-if="hasErrors && !store.loading && store.segments.length === 0"
      class="error-overlay"
    >
      <div class="error-box">
        <span class="error-icon">
          ⚠️
        </span>
        <div class="error-info">
          <strong>G-code has errors</strong>
          <ul class="error-list">
            <li
              v-for="iss in validationErrors.slice(0, 3)"
              :key="iss.code + iss.line"
            >
              Line {{ iss.line }}: {{ iss.message }}
            </li>
          </ul>
        </div>
        <button
          class="btn-retry"
          @click="doLoad"
        >
          Load anyway
        </button>
      </div>
    </div>

    <!-- ── Error state ───────────────────────────────────────── -->
    <div
      v-if="store.error && !store.loading"
      class="error-overlay"
    >
      <span>⚠ {{ store.error }}</span>
    </div>

    <!-- ── Empty / idle prompt ───────────────────────────────── -->
    <div
      v-if="!store.loading && !store.error && store.segments.length === 0 && !hasErrors"
      class="empty-state"
    >
      <span>No toolpath loaded</span>
    </div>

    <!-- ── Controls bar (using extracted subcomponents) ──────── -->
    <div
      v-if="props.showControls"
      class="controls-bar"
    >
      <ToolbarButtonGroup
        :enable3-d="props.enable3D"
        :view-mode="viewMode"
        :show-heatmap="showHeatmap"
        :show-export-panel="showExportPanel"
        :is-exporting="isExporting"
        :measure-mode="store.measureMode"
        :show-help="showHelp"
        :show-stats-panel="showStatsPanel"
        :show-filter-panel="showFilterPanel"
        :has-active-filter="filterPanelRef?.hasActiveFilter ?? false"
        :show-annotations-panel="showAnnotationsPanel"
        :show-compare-panel="showComparePanel"
        :show-compare-overlay="showCompareOverlay"
        :show-audio-panel="showAudioPanel"
        :has-multiple-tools="hasMultipleTools"
        :show-tool-legend-panel="showToolLegendPanel"
        :show-feed-analysis-panel="showFeedAnalysisPanel"
        :show-stock-simulation-panel="showStockSimulationPanel"
        :has-bounds="!!store.bounds"
        :show-chip-load-panel="showChipLoadPanel"
        :segment-count="store.segments.length"
        :memory-info="store.memoryInfo"
        @update:view-mode="viewMode = $event"
        @update:show-heatmap="showHeatmap = $event"
        @update:show-export-panel="showExportPanel = $event"
        @toggle-measure-mode="store.toggleMeasureMode()"
        @update:show-help="showHelp = $event"
        @update:show-stats-panel="showStatsPanel = $event"
        @update:show-filter-panel="showFilterPanel = $event"
        @update:show-annotations-panel="showAnnotationsPanel = $event"
        @update:show-compare-panel="showComparePanel = $event"
        @update:show-audio-panel="showAudioPanel = $event"
        @update:show-tool-legend-panel="showToolLegendPanel = $event"
        @update:show-feed-analysis-panel="showFeedAnalysisPanel = $event"
        @update:show-stock-simulation-panel="showStockSimulationPanel = $event"
        @update:show-chip-load-panel="showChipLoadPanel = $event"
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
      :show-gcode-panel="showGcodePanel"
      :show-collision-panel="showCollisionPanel"
      :show-opt-panel="showOptPanel"
      @update:show-gcode-panel="showGcodePanel = $event"
      @update:show-collision-panel="showCollisionPanel = $event"
      @update:show-opt-panel="showOptPanel = $event"
      @jump-to-selected="store.jumpToSelected()"
    />

    <!-- P4: Collision Panel -->
    <div
      v-if="showCollisionPanel && collisionReport"
      class="p4-panel collision-panel"
    >
      <div class="panel-header">
        <span>{{ collisionReport.summary }}</span>
        <button @click="showCollisionPanel = false">✕</button>
      </div>
      <ul class="panel-list">
        <li
          v-for="(coll, i) in collisionReport.collisions.slice(0, 10)"
          :key="i"
          :class="'severity-' + coll.severity"
        >
          <span class="coll-type">{{ coll.type }}</span>
          <span class="coll-line">L{{ coll.lineNumber }}</span>
          <span class="coll-msg">{{ coll.message }}</span>
        </li>
      </ul>
      <div
        v-if="collisionReport.collisions.length > 10"
        class="panel-more"
      >
        +{{ collisionReport.collisions.length - 10 }} more...
      </div>
    </div>

    <!-- P4: Optimization Panel -->
    <div
      v-if="showOptPanel && optimizationReport"
      class="p4-panel opt-panel"
    >
      <div class="panel-header">
        <span>{{ optimizationReport.summary }}</span>
        <button @click="showOptPanel = false">✕</button>
      </div>
      <div class="opt-stats">
        <span>Potential savings: {{ formatTime(optimizationReport.totalTimeSavings) }}</span>
        <span>({{ optimizationReport.percentImprovement }}%)</span>
      </div>
      <ul class="panel-list">
        <li
          v-for="(sugg, i) in optimizationReport.suggestions.slice(0, 8)"
          :key="i"
          :class="'severity-' + sugg.severity"
        >
          <span class="opt-cat">{{ sugg.category }}</span>
          <span class="opt-save">-{{ formatTime(sugg.timeSavings) }}</span>
          <span class="opt-msg">{{ sugg.message }}</span>
        </li>
      </ul>
      <div
        v-if="optimizationReport.suggestions.length > 8"
        class="panel-more"
      >
        +{{ optimizationReport.suggestions.length - 8 }} more...
      </div>
    </div>

    <!-- P5: G-code Source Panel -->
    <div
      v-if="showGcodePanel && store.sourceGcode"
      class="gcode-panel"
    >
      <div class="panel-header">
        <span>G-code Source</span>
        <div class="panel-header-actions">
          <button
            v-if="store.selectedSegmentIndex !== null"
            class="clear-selection-btn"
            title="Clear selection"
            @click="store.clearSelection()"
          >
            Clear
          </button>
          <button @click="showGcodePanel = false">✕</button>
        </div>
      </div>
      <GcodeViewer
        max-height="250px"
        :show-line-numbers="true"
        :auto-scroll="true"
      />
    </div>

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

    <!-- P5: Measure mode indicator -->
    <div
      v-if="store.measureMode"
      class="measure-indicator"
    >
      <span v-if="!store.pendingMeasureStart">📏 Click first point</span>
      <span v-else>📏 Click second point</span>
      <button
        class="measure-cancel"
        @click="store.cancelMeasurement()"
      >
        Cancel
      </button>
    </div>

    <!-- P5: Keyboard Shortcuts Help Overlay -->
    <div
      v-if="showHelp"
      class="shortcuts-overlay"
      @click.self="hideHelp"
    >
      <div class="shortcuts-panel">
        <div class="panel-header">
          <span>⌨️ Keyboard Shortcuts</span>
          <button @click="hideHelp">✕</button>
        </div>
        <div class="shortcuts-grid">
          <div
            v-for="cat in ['playback', 'view', 'tools', 'navigation']"
            :key="cat"
            class="shortcuts-category"
          >
            <h4 class="shortcuts-cat-title">{{ cat }}</h4>
            <ul class="shortcuts-list">
              <li
                v-for="s in shortcuts.filter(sc => sc.category === cat)"
                :key="s.key"
                class="shortcut-item"
              >
                <kbd class="shortcut-key">{{ s.key }}</kbd>
                <span class="shortcut-desc">{{ s.description }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- P5: Statistics Panel -->
    <div
      v-if="showStatsPanel && store.segments.length > 0"
      class="stats-panel-container"
    >
      <div class="panel-header">
        <span>📊 Toolpath Statistics</span>
        <button @click="showStatsPanel = false">✕</button>
      </div>
      <ToolpathStats :segments="store.segments" />
    </div>

    <!-- P5: Filter Panel -->
    <div
      v-if="showFilterPanel && store.segments.length > 0"
      class="filter-panel-container"
    >
      <div class="panel-header">
        <span>🔍 Segment Filter</span>
        <div class="panel-header-actions">
          <button
            v-if="filterPanelRef?.hasActiveFilter"
            class="reset-filter-btn"
            @click="filterPanelRef?.resetFilter()"
          >
            Reset
          </button>
          <button @click="showFilterPanel = false">✕</button>
        </div>
      </div>
      <ToolpathFilter
        ref="filterPanelRef"
        :segments="store.segments"
      />
    </div>

    <!-- P5: Annotations Panel -->
    <div
      v-if="showAnnotationsPanel && store.segments.length > 0"
      class="annotations-panel-container"
    >
      <ToolpathAnnotations
        :current-segment="store.currentSegmentIndex"
        :current-position="store.toolPosition as [number, number, number]"
        :current-line-number="store.currentSegment?.line_number ?? null"
        @close="showAnnotationsPanel = false"
        @goto="handleAnnotationGoto"
      />
    </div>

    <!-- P5: Compare Panel -->
    <div
      v-if="showComparePanel && store.segments.length > 0"
      class="compare-panel-container"
    >
      <ToolpathComparePanel
        :base-segments="store.segments as CompareMoveSegment[]"
        :base-gcode="store.sourceGcode"
        @close="showComparePanel = false"
        @compare-segments="handleCompareSegments"
        @overlay-toggle="handleCompareOverlayToggle"
      />
    </div>
    <!-- P5: Audio Panel -->
    <div
      v-if="showAudioPanel && store.segments.length > 0"
      class="audio-panel-container"
    >
      <ToolpathAudioPanel
        @close="showAudioPanel = false"
      />
    </div>

    <!-- P6: Tool Legend Panel -->
    <div
      v-if="showToolLegendPanel && store.segments.length > 0"
      class="tool-legend-container"
    >
      <ToolLegendPanel
        :segments="store.segments"
        :current-segment-index="store.currentSegmentIndex"
        @tool-select="handleToolSelect"
        @tool-change-click="handleToolChangeClick"
        @close="showToolLegendPanel = false"
      />
    </div>

    <!-- P6 Step 14: Feed Analysis Panel -->
    <div
      v-if="showFeedAnalysisPanel && store.segments.length > 0"
      class="feed-analysis-container"
    >
      <FeedAnalysisPanel
        :segments="store.segments"
        :tool-diameter="toolDiameter"
        @hint-click="handleFeedHintClick"
        @close="showFeedAnalysisPanel = false"
      />
    </div>

    <!-- P6 Step 15: Stock Simulation Panel -->
    <div
      v-if="showStockSimulationPanel && store.segments.length > 0 && store.bounds"
      class="stock-simulation-container"
    >
      <StockSimulationPanel
        :segments="store.segments"
        :current-segment-index="store.currentSegmentIndex"
        :bounds="store.bounds"
        :tool-diameter="toolDiameter"
        @close="showStockSimulationPanel = false"
      />
    </div>

    <!-- P6 Step 16: Chip Load Panel -->
    <div
      v-if="showChipLoadPanel && store.segments.length > 0"
      class="chipload-panel-container"
    >
      <ChipLoadPanel
        :segments="store.segments"
        :tool-diameter="toolDiameter"
        :flute-count="2"
        :default-rpm="18000"
        @issue-click="handleChipLoadIssueClick"
        @close="showChipLoadPanel = false"
      />
    </div>

    <!-- P5: Measurements Panel -->
    <div
      v-if="store.measurements.length > 0"
      class="measurements-panel"
    >
      <div class="panel-header">
        <span>📏 Measurements</span>
        <div class="panel-header-actions">
          <button
            title="Clear all"
            @click="store.clearMeasurements()"
          >
            Clear
          </button>
          <button @click="showMeasurementsPanel = !showMeasurementsPanel">
            {{ showMeasurementsPanel ? '▼' : '▲' }}
          </button>
        </div>
      </div>
      <ul
        v-if="showMeasurementsPanel"
        class="measurements-list"
      >
        <li
          v-for="m in store.measurements"
          :key="m.id"
        >
          <span class="measure-dist">{{ store.measureTool.formatDistance(m.distance) }}</span>
          <span class="measure-details">
            ΔX: {{ m.deltaX.toFixed(2) }}
            ΔY: {{ m.deltaY.toFixed(2) }}
            ΔZ: {{ m.deltaZ.toFixed(2) }}
          </span>
          <button
            class="measure-remove"
            title="Remove"
            @click="store.removeMeasurement(m.id)"
          >
            ✕
          </button>
        </li>
      </ul>
    </div>
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

/* ── Overlays ───────────────────────────────────────────────────── */
.loading-overlay, .error-overlay, .empty-state {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  gap: 12px; font-size: 13px; color: #888; background: rgba(30, 30, 46, 0.85); pointer-events: none; z-index: 5;
}
.error-overlay { color: #e74c3c; pointer-events: auto; }
.loading-inner { display: flex; flex-direction: column; align-items: center; gap: 16px; min-width: 260px; }

@keyframes spin { to { transform: rotate(360deg); } }
.spinner { width: 28px; height: 28px; animation: spin 1s linear infinite; }

.progress-box { width: 100%; }
.progress-label { display: block; text-align: center; color: #4A90D9; font-size: 12px; margin-bottom: 6px; }
.progress-track { width: 100%; height: 5px; background: #2a2a4a; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #4A90D9, #2ECC71); transition: width 0.2s; }

/* ── Validation error box ───────────────────────────────────── */
.error-box {
  display: flex; align-items: flex-start; gap: 16px; padding: 16px 20px;
  background: #2a1a1a; border: 1px solid #e74c3c; border-radius: 8px; max-width: 460px;
}
.error-icon { font-size: 28px; }
.error-info { flex: 1; }
.error-list { margin: 6px 0 0; padding-left: 18px; font-size: 11px; color: #e74c3c; }
.btn-retry {
  padding: 5px 14px;
  background: #e74c3c;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
  align-self: center;
}
.btn-retry:hover { background: #c0392b; }

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

/* ── P4: Panels ───────────────────────────────────────────────── */
.p4-panel {
  position: absolute;
  right: 10px;
  bottom: 90px;
  width: 360px;
  max-height: 280px;
  background: #1a1a2e;
  border: 1px solid #3a3a5c;
  border-radius: 8px;
  overflow: hidden;
  z-index: 10;
  font-size: 11px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #252538;
  border-bottom: 1px solid #3a3a5c;
  font-weight: 600;
  color: #ddd;
}

.panel-header button {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}
.panel-header button:hover { color: #e74c3c; }

.panel-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 200px;
  overflow-y: auto;
}

.panel-list li {
  display: flex;
  gap: 8px;
  padding: 6px 12px;
  border-bottom: 1px solid #252538;
  color: #aaa;
}
.panel-list li:last-child { border-bottom: none; }

.panel-list li.severity-critical { background: rgba(231, 76, 60, 0.1); }
.panel-list li.severity-high { background: rgba(231, 76, 60, 0.1); }
.panel-list li.severity-warning { background: rgba(243, 156, 18, 0.1); }
.panel-list li.severity-medium { background: rgba(243, 156, 18, 0.1); }
.panel-list li.severity-low { background: transparent; }
.panel-list li.severity-info { background: transparent; }

.coll-type, .opt-cat {
  color: #4a90d9;
  font-weight: 600;
  min-width: 90px;
  white-space: nowrap;
}
.coll-line {
  color: #666;
  min-width: 40px;
}
.coll-msg, .opt-msg {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.opt-save {
  color: #2ecc71;
  min-width: 50px;
  text-align: right;
}

.opt-stats {
  display: flex;
  gap: 8px;
  padding: 6px 12px;
  background: #1a2a1a;
  color: #2ecc71;
  border-bottom: 1px solid #2a4a2a;
}

.panel-more {
  padding: 6px 12px;
  color: #666;
  text-align: center;
  background: #13131f;
}

/* ── HUD selection/toggle styles moved to PlayerHudBar.vue ── */

/* ── P5: G-code panel ────────────────────────────────────────────── */
.gcode-panel {
  position: absolute;
  left: 10px;
  bottom: 90px;
  width: 400px;
  max-height: 320px;
  background: #1a1a2e;
  border: 1px solid #3a3a5c;
  border-radius: 8px;
  overflow: hidden;
  z-index: 10;
  font-size: 11px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.gcode-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #252538;
  border-bottom: 1px solid #3a3a5c;
  font-weight: 600;
  color: #ddd;
}

.panel-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.panel-header-actions button {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}
.panel-header-actions button:hover { color: #e74c3c; }

.clear-selection-btn {
  font-size: 10px !important;
  padding: 2px 6px !important;
  background: #252538 !important;
  border: 1px solid #3a3a5c !important;
  border-radius: 3px;
  color: #888 !important;
}
.clear-selection-btn:hover {
  background: #33334a !important;
  color: #ffd700 !important;
}

/* ── Toolbar button styles moved to ToolbarButtonGroup.vue ── */
/* ── Export styles moved to ExportAnimationPanel.vue ── */

/* ── P5: Measure mode indicator ──────────────────────────────────── */
.measure-indicator {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(0, 255, 255, 0.15);
  border: 1px solid #00ffff;
  border-radius: 6px;
  font-size: 12px;
  color: #00ffff;
  z-index: 15;
  animation: pulse-border 1.5s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 5px rgba(0, 255, 255, 0.3); }
  50% { box-shadow: 0 0 15px rgba(0, 255, 255, 0.6); }
}

.measure-cancel {
  padding: 3px 10px;
  background: transparent;
  border: 1px solid #00ffff;
  border-radius: 4px;
  color: #00ffff;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s;
}

.measure-cancel:hover {
  background: rgba(0, 255, 255, 0.2);
}

/* ── P5: Measurements Panel ──────────────────────────────────────── */
.measurements-panel {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 260px;
  background: #1a1a2e;
  border: 1px solid #00ffff;
  border-radius: 8px;
  overflow: hidden;
  z-index: 12;
  font-size: 11px;
  box-shadow: 0 4px 20px rgba(0, 255, 255, 0.15);
}

.measurements-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 255, 255, 0.1);
  border-bottom: 1px solid #00ffff;
  color: #00ffff;
}

.measurements-panel .panel-header-actions {
  display: flex;
  gap: 6px;
}

.measurements-panel .panel-header-actions button {
  background: transparent;
  border: 1px solid #3a3a5c;
  border-radius: 3px;
  color: #888;
  padding: 2px 6px;
  font-size: 10px;
  cursor: pointer;
}

.measurements-panel .panel-header-actions button:hover {
  border-color: #00ffff;
  color: #00ffff;
}

.measurements-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 200px;
  overflow-y: auto;
}

.measurements-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #252538;
  color: #ccc;
}

.measurements-list li:last-child {
  border-bottom: none;
}

.measure-dist {
  color: #00ffff;
  font-weight: 600;
  min-width: 70px;
}

.measure-details {
  flex: 1;
  color: #666;
  font-size: 10px;
}

.measure-remove {
  background: transparent;
  border: none;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  padding: 2px 6px;
}

.measure-remove:hover {
  color: #e74c3c;
}

/* ── P5: Help button ─────────────────────────────────────────────── */
.help-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #666;
  border-radius: 4px;
  width: 30px;
  height: 28px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  flex-shrink: 0;
}

.help-btn:hover {
  background: #33334a;
  color: #9b59b6;
}

.help-btn.active {
  background: #2a1a3a;
  border-color: #9b59b6;
  color: #9b59b6;
}

/* ── P5: Shortcuts Overlay ───────────────────────────────────────── */
.shortcuts-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.85);
  z-index: 25;
  animation: fade-in 0.15s ease;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.shortcuts-panel {
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  background: #1a1a2e;
  border: 1px solid #9b59b6;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(155, 89, 182, 0.3);
  animation: scale-in 0.2s ease;
}

@keyframes scale-in {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.shortcuts-panel .panel-header {
  background: linear-gradient(135deg, #2a1a3a 0%, #1a1a2e 100%);
  border-bottom: 1px solid #9b59b6;
  padding: 12px 16px;
  color: #9b59b6;
  font-size: 14px;
  font-weight: 600;
}

.shortcuts-panel .panel-header button {
  color: #666;
}

.shortcuts-panel .panel-header button:hover {
  color: #9b59b6;
}

.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  padding: 16px;
  max-height: calc(80vh - 60px);
  overflow-y: auto;
}

.shortcuts-category {
  background: #252538;
  border-radius: 8px;
  padding: 12px;
}

.shortcuts-cat-title {
  margin: 0 0 10px 0;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #9b59b6;
  border-bottom: 1px solid #3a3a5c;
  padding-bottom: 6px;
}

.shortcuts-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 0;
  font-size: 12px;
}

.shortcut-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 8px;
  background: linear-gradient(180deg, #3a3a5c 0%, #252538 100%);
  border: 1px solid #4a4a6c;
  border-radius: 4px;
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  color: #ddd;
  box-shadow: 0 2px 0 #1a1a2e;
}

.shortcut-desc {
  color: #aaa;
  flex: 1;
}

/* ── P5: Stats button ────────────────────────────────────────────────── */
.stats-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #666;
  border-radius: 4px;
  width: 30px;
  height: 28px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  flex-shrink: 0;
}

.stats-btn:hover {
  background: #33334a;
  color: #3498db;
}

.stats-btn.active {
  background: #1a2a4a;
  border-color: #3498db;
  color: #3498db;
}

.stats-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* ── P5: Stats Panel ─────────────────────────────────────────────────── */
.stats-panel-container {
  position: absolute;
  left: 10px;
  top: 10px;
  width: 380px;
  max-height: calc(100% - 120px);
  background: #1a1a2e;
  border: 1px solid #3498db;
  border-radius: 8px;
  overflow: hidden;
  z-index: 12;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(52, 152, 219, 0.2);
}

.stats-panel-container .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: linear-gradient(135deg, #1a2a4a 0%, #1a1a2e 100%);
  border-bottom: 1px solid #3498db;
  color: #3498db;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.stats-panel-container .panel-header button {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}

.stats-panel-container .panel-header button:hover {
  color: #3498db;
}

/* ── P5: Filter button ───────────────────────────────────────────────── */
.filter-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #666;
  border-radius: 4px;
  width: 30px;
  height: 28px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  flex-shrink: 0;
}

.filter-btn:hover {
  background: #33334a;
  color: #f39c12;
}

.filter-btn.active {
  background: #3a2a1a;
  border-color: #f39c12;
  color: #f39c12;
}

.filter-btn.filtering {
  animation: filter-pulse 1.5s ease-in-out infinite;
}

@keyframes filter-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(243, 156, 18, 0.4); }
  50% { box-shadow: 0 0 8px 2px rgba(243, 156, 18, 0.6); }
}

.filter-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  animation: none;
}

/* ── P5: Filter Panel ────────────────────────────────────────────────── */
.filter-panel-container {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 340px;
  max-height: calc(100% - 120px);
  background: #1a1a2e;
  border: 1px solid #f39c12;
  border-radius: 8px;
  overflow: hidden;
  z-index: 13;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(243, 156, 18, 0.2);
}

.filter-panel-container .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: linear-gradient(135deg, #3a2a1a 0%, #1a1a2e 100%);
  border-bottom: 1px solid #f39c12;
  color: #f39c12;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.filter-panel-container .panel-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-panel-container .panel-header button {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}

.filter-panel-container .panel-header button:hover {
  color: #f39c12;
}

.reset-filter-btn {
  font-size: 10px !important;
  padding: 2px 8px !important;
  background: #f39c12 !important;
  border-radius: 4px;
  color: #1a1a2e !important;
  font-weight: 600;
}

.reset-filter-btn:hover {
  background: #e67e22 !important;
}

.filter-panel-container > :deep(.toolpath-filter) {
  flex: 1;
  overflow-y: auto;
}

/* ── P5: Annotations button ──────────────────────────────────────────── */
.annotations-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #666;
  border-radius: 4px;
  width: 30px;
  height: 28px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  flex-shrink: 0;
}

.annotations-btn:hover {
  background: #33334a;
  color: #4a90d9;
}

.annotations-btn.active {
  background: #1a2a4a;
  border-color: #4a90d9;
  color: #4a90d9;
}

.annotations-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* ── P5: Annotations Panel ───────────────────────────────────────────── */
.annotations-panel-container {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 320px;
  max-height: calc(100% - 120px);
  z-index: 14;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(74, 144, 217, 0.2);
}

.annotations-panel-container > :deep(.toolpath-annotations) {
  flex: 1;
  overflow: hidden;
  border: 1px solid #4a90d9;
}

/* ── P5: Compare button ──────────────────────────────────────────────── */
.compare-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #666;
  border-radius: 4px;
  width: 30px;
  height: 28px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  flex-shrink: 0;
}

.compare-btn:hover {
  background: #33334a;
  color: #9b59b6;
}

.compare-btn.active {
  background: #2a1a3a;
  border-color: #9b59b6;
  color: #9b59b6;
}

.compare-btn.comparing {
  animation: compare-pulse 1.5s ease-in-out infinite;
}

@keyframes compare-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(155, 89, 182, 0.4); }
  50% { box-shadow: 0 0 8px 2px rgba(155, 89, 182, 0.6); }
}

.compare-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  animation: none;
}

/* ── P5: Compare Panel ───────────────────────────────────────────────── */
.compare-panel-container {
  position: absolute;
  left: 10px;
  top: 10px;
  width: 360px;
  max-height: calc(100% - 120px);
  z-index: 15;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(155, 89, 182, 0.2);
}

.compare-panel-container > :deep(.toolpath-compare-panel) {
  flex: 1;
  overflow: hidden;
  border: 1px solid #9b59b6;
}
/* ── P5: Audio button ───────────────────────────────────────────────── */
.audio-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 26px;
  padding: 0;
  background: #2a2a3a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.audio-btn:hover {
  background: #3a3a4a;
  color: #e9a840;
  border-color: #555;
}

.audio-btn.active {
  background: rgba(233, 168, 64, 0.2);
  border-color: #e9a840;
  color: #e9a840;
}

.audio-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── P5: Audio Panel ────────────────────────────────────────────────── */
.audio-panel-container {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 320px;
  max-height: calc(100% - 120px);
  z-index: 15;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(233, 168, 64, 0.2);
}

.audio-panel-container > :deep(.audio-panel) {
  flex: 1;
  overflow: hidden;
  border: 1px solid #e9a840;
  border-radius: 8px;
}

/* ── P6: Tools button ────────────────────────────────────────────────── */
.tools-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 26px;
  padding: 0;
  background: #2a2a3a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tools-btn:hover {
  background: #3a3a4a;
  color: #4a90d9;
  border-color: #555;
}

.tools-btn.active {
  background: rgba(74, 144, 217, 0.2);
  border-color: #4a90d9;
  color: #4a90d9;
}

.tools-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── P6: Tool Legend Panel ───────────────────────────────────────────── */
.tool-legend-container {
  position: absolute;
  left: 10px;
  top: 10px;
  width: 280px;
  max-height: calc(100% - 120px);
  z-index: 15;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(74, 144, 217, 0.2);
}

.tool-legend-container > :deep(.tool-legend-panel) {
  flex: 1;
  overflow: hidden;
  border: 1px solid #4a90d9;
  border-radius: 8px;
}

/* ── P6 Step 14: Feed button ─────────────────────────────────────────────── */
.feed-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 26px;
  padding: 0;
  background: #2a2a3a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.feed-btn:hover {
  background: #3a3a4a;
  color: #f39c12;
  border-color: #555;
}

.feed-btn.active {
  background: rgba(243, 156, 18, 0.2);
  border-color: #f39c12;
  color: #f39c12;
}

.feed-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── P6 Step 14: Feed Analysis Panel ─────────────────────────────────────── */
.feed-analysis-container {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 360px;
  max-height: calc(100% - 120px);
  z-index: 16;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(243, 156, 18, 0.2);
}

.feed-analysis-container > :deep(.feed-analysis-panel) {
  flex: 1;
  overflow: hidden;
  border: 1px solid #f39c12;
  border-radius: 8px;
}

/* ── P6 Step 15: Stock button ────────────────────────────────────────────── */
.stock-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 26px;
  padding: 0;
  background: #2a2a3a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.stock-btn:hover {
  background: #3a3a4a;
  color: #8B4513;
  border-color: #555;
}

.stock-btn.active {
  background: rgba(139, 69, 19, 0.2);
  border-color: #8B4513;
  color: #8B4513;
}

.stock-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── P6 Step 15: Stock Simulation Panel ──────────────────────────────────── */
.stock-simulation-container {
  position: absolute;
  left: 10px;
  top: 10px;
  width: 320px;
  max-height: calc(100% - 120px);
  z-index: 17;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(139, 69, 19, 0.2);
}

.stock-simulation-container > :deep(.stock-simulation-panel) {
  flex: 1;
  overflow: hidden;
  border: 1px solid #8B4513;
  border-radius: 8px;
}

/* ── P6 Step 16: Chip Load Panel ──────────────────────────────────────────── */
.chipload-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #888;
  width: 32px;
  height: 32px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chipload-btn:hover:not(:disabled) {
  background: #33334a;
  border-color: #f39c12;
  color: #f39c12;
}

.chipload-btn.active {
  background: rgba(243, 156, 18, 0.2);
  border-color: #f39c12;
  color: #f39c12;
}

.chipload-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.chipload-panel-container {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 340px;
  max-height: calc(100% - 120px);
  z-index: 18;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(243, 156, 18, 0.2);
}

.chipload-panel-container > :deep(.chip-load-panel) {
  flex: 1;
  overflow: hidden;
  border: 1px solid #f39c12;
  border-radius: 8px;
}
</style>
