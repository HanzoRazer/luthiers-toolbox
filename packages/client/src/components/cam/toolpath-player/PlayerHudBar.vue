<script setup lang="ts">
/**
 * PlayerHudBar — Heads-up display for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows current G-code line, machine state, position, feed, time, and badges.
 */
import { computed } from 'vue';
import type { MachineState } from '@/util/mcodeTracker';
import type { CollisionReport } from '@/util/collisionDetector';
import type { OptimizationReport } from '@/util/gcodeOptimizer';

interface TimeEstimate {
  seconds: number;
  formatted: string;
}

interface Props {
  // Current segment info
  currentLineText: string | null;
  currentFeed: number;
  toolPosition: [number, number, number];
  currentTimeMs: number;
  totalDurationMs: number;
  // Machine state
  machineState: MachineState | null;
  // Time estimates
  estimates: {
    realistic: TimeEstimate;
    machine: TimeEstimate;
    withSetup: TimeEstimate;
  };
  // Collision/optimization reports
  collisionReport: CollisionReport | null;
  optimizationReport: OptimizationReport | null;
  // Selection
  selectedSegmentIndex: number | null;
  selectedGcodeLine: { lineNumber: number } | null;
  // Panel states
  showGcodePanel: boolean;
  showCollisionPanel: boolean;
  showOptPanel: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:showGcodePanel': [value: boolean];
  'update:showCollisionPanel': [value: boolean];
  'update:showOptPanel': [value: boolean];
  jumpToSelected: [];
}>();

function formatTime(ms: number): string {
  const totalSecs = ms / 1000;
  const mins = Math.floor(totalSecs / 60);
  const secs = (totalSecs % 60).toFixed(1);
  return `${mins}:${secs.padStart(4, '0')}`;
}

const hasCollisions = computed(() =>
  props.collisionReport && props.collisionReport.collisions.length > 0
);

const hasCriticalCollisions = computed(() =>
  props.collisionReport && props.collisionReport.criticalCount > 0
);

const hasOptimizations = computed(() =>
  props.optimizationReport && props.optimizationReport.suggestions.length > 0
);
</script>

<template>
  <div class="hud-bar">
    <!-- Current G-code line -->
    <span
      class="hud-gcode"
      :title="currentLineText ?? undefined"
    >
      {{ currentLineText ?? '—' }}
    </span>

    <!-- M-code state indicators -->
    <template v-if="machineState">
      <span
        v-if="machineState.spindleOn"
        class="hud-m"
        title="Spindle"
      >
        ⚡{{ machineState.spindleDir.toUpperCase() }} S{{ machineState.spindleSpeed }}
      </span>
      <span
        v-if="machineState.coolant !== 'off'"
        class="hud-m"
        :title="'Coolant: ' + machineState.coolant"
      >
        {{ machineState.coolant === 'flood' ? '💧' : '🌫️' }}
      </span>
      <span
        v-if="machineState.currentTool > 0"
        class="hud-m"
        title="Tool"
      >
        🔧T{{ machineState.currentTool }}
      </span>
    </template>

    <span class="hud-div">│</span>

    <!-- Z position -->
    <span class="hud-z">
      Z {{ toolPosition[2].toFixed(2) }} mm
    </span>

    <span class="hud-div">│</span>

    <!-- Feed rate -->
    <span class="hud-feed">
      F{{ Math.round(currentFeed) }}
    </span>

    <span class="hud-div">│</span>

    <!-- Time -->
    <span class="hud-time">
      {{ formatTime(currentTimeMs) }} / {{ formatTime(totalDurationMs) }}
    </span>

    <!-- Time estimate badge -->
    <span
      v-if="estimates.realistic.seconds > 0"
      class="hud-est"
      :title="'Machine: ' + estimates.machine.formatted + ' | With setup: ' + estimates.withSetup.formatted"
    >
      ⏱️ {{ estimates.realistic.formatted }}
    </span>

    <!-- Collision warning badge -->
    <button
      v-if="hasCollisions"
      class="hud-collision"
      :class="{ critical: hasCriticalCollisions }"
      :title="collisionReport?.summary"
      @click="emit('update:showCollisionPanel', !showCollisionPanel)"
    >
      {{ hasCriticalCollisions ? '⛔' : '⚠️' }}
      {{ collisionReport?.collisions.length }}
    </button>

    <!-- Optimization badge -->
    <button
      v-if="hasOptimizations"
      class="hud-opt"
      :title="optimizationReport?.summary"
      @click="emit('update:showOptPanel', !showOptPanel)"
    >
      💡 {{ optimizationReport?.suggestions.length }}
    </button>

    <!-- Selection info -->
    <span
      v-if="selectedSegmentIndex !== null"
      class="hud-selection"
      :title="'Click to jump to segment ' + selectedSegmentIndex"
      @click="emit('jumpToSelected')"
    >
      📍 Seg {{ selectedSegmentIndex }}
      <template v-if="selectedGcodeLine">
        (L{{ selectedGcodeLine.lineNumber }})
      </template>
    </span>

    <!-- G-code panel toggle -->
    <button
      class="hud-gcode-toggle"
      :class="{ active: showGcodePanel }"
      title="Toggle G-code source panel"
      @click="emit('update:showGcodePanel', !showGcodePanel)"
    >
      { }
    </button>
  </div>
</template>

<style scoped>
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

.hud-m {
  color: #f39c12;
  font-size: 11px;
}

.hud-div {
  color: #333;
  flex-shrink: 0;
}

.hud-z {
  color: #2ecc71;
  flex-shrink: 0;
}

.hud-feed {
  color: #f39c12;
  flex-shrink: 0;
}

.hud-time {
  color: #999;
  flex-shrink: 0;
  min-width: 100px;
  text-align: right;
}

.hud-est {
  color: #4a90d9;
  font-size: 11px;
  padding: 1px 6px;
  background: #1a3a6b;
  border-radius: 4px;
  cursor: help;
  flex-shrink: 0;
}

/* Collision & Optimization badges */
.hud-collision,
.hud-opt {
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

.hud-collision:hover {
  background: #6c5a2a;
}

.hud-collision.critical:hover {
  background: #7c2a2a;
}

.hud-opt {
  background: #1a4a3a;
  color: #2ecc71;
}

.hud-opt:hover {
  background: #2a5a4a;
}

/* Selection indicator */
.hud-selection {
  color: #ffd700;
  font-size: 11px;
  padding: 1px 8px;
  background: rgba(255, 215, 0, 0.15);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 4px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}

.hud-selection:hover {
  background: rgba(255, 215, 0, 0.25);
}

/* G-code toggle button */
.hud-gcode-toggle {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid #3a3a5c;
  background: #252538;
  color: #888;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}

.hud-gcode-toggle:hover {
  background: #33334a;
  color: #ccc;
}

.hud-gcode-toggle.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}
</style>
