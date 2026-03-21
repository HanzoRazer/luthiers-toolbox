<script setup lang="ts">
/**
 * ToolpathPlayer
 *
 * Drop-in animated G-code toolpath player. Composes:
 *   - ToolpathCanvas (canvas renderer)
 *   - Playback controls bar (play/pause, scrub, speed)
 *   - HUD bar (current G-code line, Z depth, feed, elapsed time)
 *
 * Usage:
 *   <ToolpathPlayer :gcode="result.gcode" height="480px" />
 *   <ToolpathPlayer :gcode="exportGcode" :auto-play="false" :show-hud="true" />
 */

import { onMounted, onUnmounted, computed } from "vue";
import ToolpathCanvas from "./ToolpathCanvas.vue";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface Props {
  /** If provided, auto-loads on mount. */
  gcode?: string;
  /** Show HUD info bar (default true). */
  showHud?: boolean;
  /** Show playback controls bar (default true). */
  showControls?: boolean;
  /** Start playing immediately after load (default false). */
  autoPlay?: boolean;
  /** CSS height of the player container (default "500px"). */
  height?: string;
}

const props = withDefaults(defineProps<Props>(), {
  gcode: undefined,
  showHud: true,
  showControls: true,
  autoPlay: false,
  height: "500px",
});

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------
const store = useToolpathPlayerStore();

// ---------------------------------------------------------------------------
// Computed helpers
// ---------------------------------------------------------------------------
const playIcon  = computed(() => store.playState === "playing" ? "⏸" : "▶");
const playLabel = computed(() => store.playState === "playing" ? "Pause" : "Play");
const speeds    = [0.5, 1, 2, 5, 10] as const;

function togglePlay(): void {
  if (store.playState === "playing") {
    store.pause();
  } else {
    store.play();
  }
}

function onScrubInput(e: Event): void {
  const v = parseFloat((e.target as HTMLInputElement).value);
  store.seek(v);
}

// ---------------------------------------------------------------------------
// Time formatter: ms → "M:SS.s"
// ---------------------------------------------------------------------------
function formatTime(ms: number): string {
  const totalSecs = ms / 1000;
  const mins = Math.floor(totalSecs / 60);
  const secs = (totalSecs % 60).toFixed(1);
  return `${mins}:${secs.padStart(4, "0")}`;
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(async () => {
  if (props.gcode) {
    await store.loadGcode(props.gcode);
    if (props.autoPlay) store.play();
  }
});

onUnmounted(() => {
  store.dispose();
});
</script>

<template>
  <div class="toolpath-player" :style="{ height: props.height }">

    <!-- ── Canvas ─────────────────────────────────────────────── -->
    <ToolpathCanvas class="canvas-area" />

    <!-- ── Loading overlay ───────────────────────────────────── -->
    <div v-if="store.loading" class="loading-overlay">
      <svg class="spinner" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="#4A90D9" stroke-width="2" stroke-dasharray="32" stroke-linecap="round"/>
      </svg>
      <span>Parsing G-code…</span>
    </div>

    <!-- ── Error state ───────────────────────────────────────── -->
    <div v-if="store.error && !store.loading" class="error-overlay">
      ⚠ {{ store.error }}
    </div>

    <!-- ── Empty / idle prompt ───────────────────────────────── -->
    <div v-if="!store.loading && !store.error && store.segments.length === 0" class="empty-state">
      <span>No toolpath loaded</span>
    </div>

    <!-- ── Controls bar ──────────────────────────────────────── -->
    <div v-if="props.showControls" class="controls-bar">
      <!-- Step buttons -->
      <button class="ctrl-btn" title="Step back" @click="store.stepBackward()">◀◀</button>

      <button
        class="ctrl-btn play-btn"
        :title="playLabel"
        :disabled="store.segments.length === 0"
        @click="togglePlay()"
      >
        {{ playIcon }}
      </button>

      <button class="ctrl-btn" title="Step forward" @click="store.stepForward()">▶▶</button>

      <button class="ctrl-btn stop-btn" title="Stop" @click="store.stop()">■</button>

      <!-- Scrub bar -->
      <input
        type="range"
        class="scrub-bar"
        min="0"
        max="1"
        step="0.0005"
        :value="store.progress"
        @input="onScrubInput"
      />

      <!-- Progress percent -->
      <span class="progress-pct">{{ (store.progress * 100).toFixed(0) }}%</span>

      <!-- Speed buttons -->
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

    <!-- ── HUD bar ────────────────────────────────────────────── -->
    <div v-if="props.showHud" class="hud-bar">
      <span class="hud-gcode" :title="store.currentSegment?.line_text">
        {{ store.currentSegment?.line_text ?? '—' }}
      </span>
      <span class="hud-divider">│</span>
      <span class="hud-z">Z {{ store.toolPosition[2].toFixed(2) }} mm</span>
      <span class="hud-divider">│</span>
      <span class="hud-feed">
        F{{ store.currentSegment ? Math.round(store.currentSegment.feed) : 0 }}
      </span>
      <span class="hud-divider">│</span>
      <span class="hud-time">
        {{ formatTime(store.currentTimeMs) }} / {{ formatTime(store.totalDurationMs) }}
      </span>
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

/* ── Overlay states ─────────────────────────────────────────────── */
.loading-overlay,
.error-overlay,
.empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 13px;
  color: #888;
  background: rgba(30, 30, 46, 0.75);
  pointer-events: none;
}

.error-overlay {
  color: #e74c3c;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
.spinner {
  width: 22px;
  height: 22px;
  animation: spin 1s linear infinite;
}

/* ── Controls bar ───────────────────────────────────────────────── */
.controls-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  background: #13131f;
  border-top: 1px solid #2a2a4a;
  flex-shrink: 0;
}

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

.play-btn {
  width: 36px;
  font-size: 14px;
  color: #4a90d9;
  border-color: #4a90d9;
}
.play-btn:hover { background: #1a3a6b; color: #fff; }

.stop-btn { color: #e74c3c; border-color: #e74c3c; }
.stop-btn:hover { background: #5c1a1a; color: #fff; }

.scrub-bar {
  flex: 1;
  min-width: 60px;
  accent-color: #4a90d9;
  height: 4px;
  cursor: pointer;
}

.progress-pct {
  font-size: 11px;
  color: #666;
  width: 34px;
  text-align: right;
  flex-shrink: 0;
}

.speed-group {
  display: flex;
  gap: 3px;
  flex-shrink: 0;
}

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
.speed-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}

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

.hud-gcode {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #a0c4e8;
  font-size: 11px;
}

.hud-divider {
  color: #333;
  flex-shrink: 0;
}

.hud-z { color: #2ecc71; flex-shrink: 0; }
.hud-feed { color: #f39c12; flex-shrink: 0; }

.hud-time {
  color: #999;
  flex-shrink: 0;
  min-width: 100px;
  text-align: right;
}
</style>
