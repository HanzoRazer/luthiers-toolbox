<script setup lang="ts">
/**
 * ToolpathPlayer — P1-P4 Full Integration
 *
 * Drop-in animated G-code toolpath player. Composes:
 *   - ToolpathCanvas  (LOD canvas renderer + tool viz)
 *   - MemoryWarning   (large-file alert banner)
 *   - Controls bar    (play/pause, scrub, speed, resolution slider)
 *   - HUD bar         (G-code line, Z, feed, time, M-code state, estimate)
 *
 * P1: Memory management, progress indicator, G-code validation
 * P2: Caching (sessionStorage), LOD (in canvas)
 * P3: M-code HUD, tool viz (in canvas), time estimates
 * P4: Collision detection, optimization suggestions, stock simulation
 */

import { onMounted, onUnmounted, computed, ref, watch } from "vue";
import ToolpathCanvas from "./ToolpathCanvas.vue";
import MemoryWarning from "./MemoryWarning.vue";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import { useTimeEstimates } from "@/composables/useTimeEstimates";
import { validateGcode, type ValidationResult } from "@/util/gcodeValidator";
import { buildMachineStates, type MachineState } from "@/util/mcodeTracker";
// P4 imports
import { CollisionDetector, type CollisionReport, type Fixture } from "@/util/collisionDetector";
import { GcodeOptimizer, type OptimizationReport } from "@/util/gcodeOptimizer";

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
});

// ---------------------------------------------------------------------------
// Store + composables
// ---------------------------------------------------------------------------
const store = useToolpathPlayerStore();
const { estimates } = useTimeEstimates(computed(() => store.segments));

// ---------------------------------------------------------------------------
// Local state
// ---------------------------------------------------------------------------
const memDismissed = ref(false);
const resSlider = ref(100);
const validation = ref<ValidationResult | null>(null);

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
    <!-- ── Canvas ─────────────────────────────────────────────── -->
    <ToolpathCanvas class="canvas-area" />

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

    <!-- ── Controls bar ──────────────────────────────────────── -->
    <div
      v-if="props.showControls"
      class="controls-bar"
    >
      <!-- Memory badge -->
      <div
        v-if="store.memoryInfo.segmentCount > 0"
        class="mem-badge"
        :class="{
          warning: store.memoryInfo.isWarning,
          critical: store.memoryInfo.isCritical,
        }"
      >
        {{ store.memoryInfo.segmentCount.toLocaleString() }}
      </div>

      <button
        class="ctrl-btn"
        title="Step back"
        @click="store.stepBackward()"
      >
        ◀◀
      </button>

      <button
        class="ctrl-btn play-btn"
        :title="playLabel"
        :disabled="store.segments.length === 0"
        @click="togglePlay()"
      >
        {{ playIcon }}
      </button>

      <button
        class="ctrl-btn"
        title="Step forward"
        @click="store.stepForward()"
      >
        ▶▶
      </button>
      <button
        class="ctrl-btn stop-btn"
        title="Stop"
        @click="store.stop()"
      >
        ■
      </button>

      <input
        type="range"
        class="scrub-bar"
        min="0"
        max="1"
        step="0.0005"
        :value="store.progress"
        @input="onScrubInput"
      >

      <span class="pct">{{ (store.progress * 100).toFixed(0) }}%</span>

      <div class="speed-group">
        <button
          v-for="s in speeds"
          :key="s"
          class="speed-btn"
          :class="{ active: store.speed === s }"
          @click="store.setSpeed(s)"
        >
          {{ s }}×
        </button>
      </div>
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

    <!-- ── HUD bar (P3: M-code state + time estimate) ────────── -->
    <div
      v-if="props.showHud"
      class="hud-bar"
    >
      <span
        class="hud-gcode"
        :title="store.currentSegment?.line_text"
      >
        {{ store.currentSegment?.line_text ?? '—' }}
      </span>

      <!-- M-code state indicators -->
      <template v-if="currentMachine">
        <span
          v-if="currentMachine.spindleOn"
          class="hud-m"
          title="Spindle"
        >
          ⚡{{ currentMachine.spindleDir.toUpperCase() }} S{{ currentMachine.spindleSpeed }}
        </span>
        <span
          v-if="currentMachine.coolant !== 'off'"
          class="hud-m"
          :title="'Coolant: ' + currentMachine.coolant"
        >
          {{ currentMachine.coolant === 'flood' ? '💧' : '🌫️' }}
        </span>
        <span
          v-if="currentMachine.currentTool > 0"
          class="hud-m"
          title="Tool"
        >
          🔧T{{ currentMachine.currentTool }}
        </span>
      </template>

      <span class="hud-div">│</span>
      <span class="hud-z">
        Z {{ store.toolPosition[2].toFixed(2) }} mm
      </span>
      <span class="hud-div">│</span>
      <span class="hud-feed">
        F{{ store.currentSegment ? Math.round(store.currentSegment.feed) : 0 }}
      </span>
      <span class="hud-div">│</span>
      <span class="hud-time">
        {{ formatTime(store.currentTimeMs) }} / {{ formatTime(store.totalDurationMs) }}
      </span>

      <!-- Time estimate badge -->
      <span
        v-if="estimates.realistic.seconds > 0"
        class="hud-est"
        :title="'Machine: ' + estimates.machine.formatted + ' | With setup: ' + estimates.withSetup.formatted"
      >
        ⏱️ {{ estimates.realistic.formatted }}
      </span>

      <!-- P4: Collision warning badge -->
      <button
        v-if="hasCollisions"
        class="hud-collision"
        :class="{ critical: hasCriticalCollisions }"
        :title="collisionReport?.summary"
        @click="showCollisionPanel = !showCollisionPanel"
      >
        {{ hasCriticalCollisions ? '⛔' : '⚠️' }}
        {{ collisionReport?.collisions.length }}
      </button>

      <!-- P4: Optimization badge -->
      <button
        v-if="hasOptimizations"
        class="hud-opt"
        :title="optimizationReport?.summary"
        @click="showOptPanel = !showOptPanel"
      >
        💡 {{ optimizationReport?.suggestions.length }}
      </button>
    </div>

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

.mem-badge {
  padding: 1px 7px;
  border-radius: 10px;
  font-size: 10px;
  background: #1a3a6b;
  color: #4A90D9;
  margin-right: 4px;
}
.mem-badge.warning { background: #5c4a1a; color: #f39c12; }
.mem-badge.critical { background: #5c1a1a; color: #e74c3c; }

.ctrl-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #ccc;
  border-radius: 4px;
  width: 30px;
  height: 28px;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}
.ctrl-btn:hover { background: #33334a; color: #fff; }
.ctrl-btn:disabled { opacity: 0.35; cursor: default; }

.play-btn { width: 36px; font-size: 14px; color: #4a90d9; border-color: #4a90d9; }
.play-btn:hover { background: #1a3a6b; color: #fff; }

.stop-btn { color: #e74c3c; border-color: #e74c3c; }
.stop-btn:hover { background: #5c1a1a; color: #fff; }

.scrub-bar { flex: 1; min-width: 60px; accent-color: #4a90d9; height: 4px; cursor: pointer; }

.pct { font-size: 11px; color: #666; width: 34px; text-align: right; flex-shrink: 0; }

.speed-group { display: flex; gap: 3px; flex-shrink: 0; }
.speed-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #888;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.speed-btn:hover { background: #33334a; color: #ccc; }
.speed-btn.active { background: #1a3a6b; border-color: #4a90d9; color: #4a90d9; }

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

/* ── HUD bar ────────────────────────────────────────────────────── */
.hud-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 10px;
  background: rgba(0, 0, 0, 0.75);
  border-top: 1px solid #1a1a2e;
  font-size: 12px;
  color: #ddd;
  flex-shrink: 0;
  min-height: 26px;
  white-space: nowrap;
  overflow: hidden;
}

.hud-gcode { flex: 1; overflow: hidden; text-overflow: ellipsis; color: #a0c4e8; font-size: 11px; }
.hud-m { color: #f39c12; font-size: 11px; }
.hud-div { color: #333; flex-shrink: 0; }
.hud-z { color: #2ecc71; flex-shrink: 0; }
.hud-feed { color: #f39c12; flex-shrink: 0; }
.hud-time { color: #999; flex-shrink: 0; min-width: 100px; text-align: right; }

.hud-est {
  color: #4a90d9;
  font-size: 11px;
  padding: 1px 6px;
  background: #1a3a6b;
  border-radius: 4px;
  cursor: help;
  flex-shrink: 0;
}

/* ── P4: Collision & Optimization badges ───────────────────────── */
.hud-collision, .hud-opt {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 4px;
  cursor: pointer;
  border: none;
  flex-shrink: 0;
  transition: background 0.15s;
}

.hud-collision {
  background: #5c4a1a;
  color: #f39c12;
}
.hud-collision.critical {
  background: #5c1a1a;
  color: #e74c3c;
}
.hud-collision:hover { background: #6c5a2a; }
.hud-collision.critical:hover { background: #7c2a2a; }

.hud-opt {
  background: #1a4a3a;
  color: #2ecc71;
}
.hud-opt:hover { background: #2a5a4a; }

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
</style>
