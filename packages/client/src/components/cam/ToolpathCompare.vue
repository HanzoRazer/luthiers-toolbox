<script setup lang="ts">
/**
 * ToolpathCompare — P4.3 Multi-Program Comparison
 *
 * Side-by-side toolpath comparison for optimization workflow.
 * Proves new strategy is better with clear metrics.
 *
 * Features:
 * - Synchronized playback
 * - Stats comparison (time, distances, moves)
 * - Difference highlighting
 */

import { ref, computed, watch, onMounted } from "vue";
import ToolpathPlayer from "./ToolpathPlayer.vue";
import { useTimeEstimates } from "@/composables/useTimeEstimates";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import type { MoveSegment } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** Original G-code */
  original: string;
  /** Optimized/Modified G-code */
  optimized: string;
  /** Synchronized playback */
  syncPlayback?: boolean;
  /** Show difference overlay */
  showDiff?: boolean;
  /** Height of each player */
  playerHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  syncPlayback: true,
  showDiff: true,
  playerHeight: "300px",
});

// ---------------------------------------------------------------------------
// Emit
// ---------------------------------------------------------------------------

const emit = defineEmits<{
  (e: "close"): void;
}>();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const originalStore = useToolpathPlayerStore();
const optimizedStore = useToolpathPlayerStore();

const isPlaying = ref(false);
const progress = ref(0);

// ---------------------------------------------------------------------------
// Computed Stats
// ---------------------------------------------------------------------------

interface ToolpathStats {
  totalTime: number;
  cutDistance: number;
  rapidDistance: number;
  totalMoves: number;
  cutMoves: number;
  rapidMoves: number;
  arcMoves: number;
  minZ: number;
  maxFeed: number;
}

function computeStats(segments: MoveSegment[]): ToolpathStats {
  let cutDistance = 0;
  let rapidDistance = 0;
  let cutMoves = 0;
  let rapidMoves = 0;
  let arcMoves = 0;
  let minZ = 0;
  let maxFeed = 0;
  let totalTime = 0;

  for (const seg of segments) {
    const dist = Math.sqrt(
      (seg.to_pos[0] - seg.from_pos[0]) ** 2 +
      (seg.to_pos[1] - seg.from_pos[1]) ** 2 +
      (seg.to_pos[2] - seg.from_pos[2]) ** 2
    );

    totalTime += seg.duration_ms;
    minZ = Math.min(minZ, seg.to_pos[2]);
    maxFeed = Math.max(maxFeed, seg.feed || 0);

    if (seg.type === "rapid") {
      rapidDistance += dist;
      rapidMoves++;
    } else if (seg.type.includes("arc")) {
      cutDistance += dist;
      arcMoves++;
      cutMoves++;
    } else {
      cutDistance += dist;
      cutMoves++;
    }
  }

  return {
    totalTime,
    cutDistance: Math.round(cutDistance * 100) / 100,
    rapidDistance: Math.round(rapidDistance * 100) / 100,
    totalMoves: segments.length,
    cutMoves,
    rapidMoves,
    arcMoves,
    minZ: Math.round(minZ * 100) / 100,
    maxFeed,
  };
}

const originalStats = computed(() => computeStats(originalStore.segments));
const optimizedStats = computed(() => computeStats(optimizedStore.segments));

const improvement = computed(() => {
  const orig = originalStats.value;
  const opt = optimizedStats.value;

  if (orig.totalTime === 0) return null;

  return {
    timeSaved: orig.totalTime - opt.totalTime,
    timePercent: ((orig.totalTime - opt.totalTime) / orig.totalTime) * 100,
    distanceSaved: (orig.cutDistance + orig.rapidDistance) - (opt.cutDistance + opt.rapidDistance),
    rapidReduction: orig.rapidDistance - opt.rapidDistance,
    moveReduction: orig.totalMoves - opt.totalMoves,
  };
});

// ---------------------------------------------------------------------------
// Methods
// ---------------------------------------------------------------------------

function formatTime(ms: number): string {
  const secs = ms / 1000;
  const mins = Math.floor(secs / 60);
  const s = (secs % 60).toFixed(1);
  return `${mins}:${s.padStart(4, "0")}`;
}

function formatDistance(mm: number): string {
  if (mm >= 1000) {
    return `${(mm / 1000).toFixed(2)}m`;
  }
  return `${mm.toFixed(1)}mm`;
}

function formatPercent(val: number): string {
  const sign = val >= 0 ? "+" : "";
  return `${sign}${val.toFixed(1)}%`;
}

function togglePlay(): void {
  isPlaying.value = !isPlaying.value;
  if (isPlaying.value) {
    originalStore.play();
    if (props.syncPlayback) {
      optimizedStore.play();
    }
  } else {
    originalStore.pause();
    optimizedStore.pause();
  }
}

function syncSeek(val: number): void {
  progress.value = val;
  originalStore.seek(val);
  if (props.syncPlayback) {
    optimizedStore.seek(val);
  }
}

function reset(): void {
  originalStore.stop();
  optimizedStore.stop();
  progress.value = 0;
  isPlaying.value = false;
}

// Sync progress from original to optimized
watch(() => originalStore.progress, (val) => {
  if (props.syncPlayback && isPlaying.value) {
    progress.value = val;
    // Keep optimized in sync
    if (Math.abs(optimizedStore.progress - val) > 0.01) {
      optimizedStore.seek(val);
    }
  }
});
</script>

<template>
  <div class="toolpath-compare">
    <!-- Header -->
    <div class="compare-header">
      <h3>Toolpath Comparison</h3>
      <div class="header-controls">
        <label class="sync-toggle">
          <input
            type="checkbox"
            :checked="syncPlayback"
          >
          Sync Playback
        </label>
        <button
          class="btn-close"
          title="Close"
          @click="emit('close')"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Players -->
    <div class="compare-players">
      <!-- Original -->
      <div class="player-panel original">
        <div class="panel-header">
          <span class="panel-label">Original</span>
          <span class="panel-time">{{ formatTime(originalStats.totalTime) }}</span>
        </div>
        <ToolpathPlayer
          :gcode="original"
          :show-controls="false"
          :show-hud="false"
          :height="playerHeight"
        />
        <div class="panel-stats">
          <div class="stat">
            <span class="stat-label">Cut:</span>
            <span class="stat-value">{{ formatDistance(originalStats.cutDistance) }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Rapid:</span>
            <span class="stat-value">{{ formatDistance(originalStats.rapidDistance) }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Moves:</span>
            <span class="stat-value">{{ originalStats.totalMoves }}</span>
          </div>
        </div>
      </div>

      <!-- Optimized -->
      <div class="player-panel optimized">
        <div class="panel-header">
          <span class="panel-label">Optimized</span>
          <span class="panel-time">{{ formatTime(optimizedStats.totalTime) }}</span>
        </div>
        <ToolpathPlayer
          :gcode="optimized"
          :show-controls="false"
          :show-hud="false"
          :height="playerHeight"
        />
        <div class="panel-stats improvement">
          <div class="stat">
            <span class="stat-label">Cut:</span>
            <span class="stat-value">{{ formatDistance(optimizedStats.cutDistance) }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Rapid:</span>
            <span class="stat-value">{{ formatDistance(optimizedStats.rapidDistance) }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Moves:</span>
            <span class="stat-value">{{ optimizedStats.totalMoves }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Improvement Summary -->
    <div
      v-if="improvement"
      class="improvement-summary"
      :class="{
        positive: improvement.timePercent > 0,
        negative: improvement.timePercent < 0,
      }"
    >
      <div class="improvement-main">
        <span class="improvement-label">Time Saved:</span>
        <span class="improvement-value">
          {{ formatTime(improvement.timeSaved) }}
          ({{ formatPercent(improvement.timePercent) }})
        </span>
      </div>
      <div class="improvement-details">
        <span v-if="improvement.rapidReduction > 0">
          Rapid: -{{ formatDistance(improvement.rapidReduction) }}
        </span>
        <span v-if="improvement.moveReduction > 0">
          Moves: -{{ improvement.moveReduction }}
        </span>
      </div>
    </div>

    <!-- Shared Controls -->
    <div class="compare-controls">
      <button
        class="ctrl-btn play-btn"
        @click="togglePlay"
      >
        {{ isPlaying ? '⏸' : '▶' }}
      </button>
      <input
        type="range"
        class="scrub-bar"
        min="0"
        max="1"
        step="0.001"
        :value="progress"
        @input="syncSeek(parseFloat(($event.target as HTMLInputElement).value))"
      >
      <span class="progress-pct">{{ (progress * 100).toFixed(0) }}%</span>
      <button
        class="ctrl-btn"
        @click="reset"
      >
        ■
      </button>
    </div>
  </div>
</template>

<style scoped>
.toolpath-compare {
  display: flex;
  flex-direction: column;
  background: #1e1e2e;
  border-radius: 8px;
  border: 1px solid #2a2a4a;
  overflow: hidden;
}

.compare-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #13131f;
  border-bottom: 1px solid #2a2a4a;
}

.compare-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #e0e0e0;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sync-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #888;
  cursor: pointer;
}

.sync-toggle input {
  accent-color: #4a90d9;
}

.btn-close {
  background: transparent;
  border: none;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
}

.btn-close:hover {
  color: #e74c3c;
}

.compare-players {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: #2a2a4a;
}

.player-panel {
  display: flex;
  flex-direction: column;
  background: #1e1e2e;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #252538;
}

.panel-label {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
}

.original .panel-label { color: #888; }
.optimized .panel-label { color: #2ecc71; }

.panel-time {
  font-family: monospace;
  font-size: 13px;
  color: #4a90d9;
}

.panel-stats {
  display: flex;
  gap: 16px;
  padding: 8px 12px;
  background: #13131f;
  font-size: 11px;
}

.stat {
  display: flex;
  gap: 4px;
}

.stat-label {
  color: #666;
}

.stat-value {
  color: #aaa;
  font-family: monospace;
}

.panel-stats.improvement .stat-value {
  color: #2ecc71;
}

.improvement-summary {
  padding: 12px 16px;
  background: #1a2a1a;
  border-top: 1px solid #2a4a2a;
  text-align: center;
}

.improvement-summary.positive {
  background: #1a2a1a;
  border-color: #2ecc71;
}

.improvement-summary.negative {
  background: #2a1a1a;
  border-color: #e74c3c;
}

.improvement-main {
  font-size: 14px;
  margin-bottom: 4px;
}

.improvement-label {
  color: #888;
  margin-right: 8px;
}

.improvement-value {
  font-weight: 600;
  color: #2ecc71;
  font-family: monospace;
}

.improvement-summary.negative .improvement-value {
  color: #e74c3c;
}

.improvement-details {
  font-size: 11px;
  color: #666;
  display: flex;
  gap: 16px;
  justify-content: center;
}

.compare-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #13131f;
  border-top: 1px solid #2a2a4a;
}

.ctrl-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #ccc;
  border-radius: 4px;
  width: 32px;
  height: 28px;
  font-size: 12px;
  cursor: pointer;
}

.ctrl-btn:hover {
  background: #33334a;
  color: #fff;
}

.play-btn {
  color: #4a90d9;
  border-color: #4a90d9;
}

.play-btn:hover {
  background: #1a3a6b;
}

.scrub-bar {
  flex: 1;
  accent-color: #4a90d9;
  height: 4px;
}

.progress-pct {
  font-size: 11px;
  color: #666;
  min-width: 36px;
  text-align: right;
  font-family: monospace;
}

@media (max-width: 768px) {
  .compare-players {
    grid-template-columns: 1fr;
  }
}
</style>
