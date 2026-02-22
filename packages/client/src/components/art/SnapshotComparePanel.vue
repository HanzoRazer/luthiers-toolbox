<script setup lang="ts">
/**
 * SnapshotComparePanel - Compare snapshots with delta visualization.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { useRosetteStore } from '@/stores/rosetteStore'
import CompareOpenPanel from './snapshot_compare/CompareOpenPanel.vue'
import {
  useSnapshotCompareState,
  useSnapshotCompareLogic,
  useSnapshotCompareNavigation,
  useSnapshotCompareKeyboard
} from './snapshot_compare/composables'

// =============================================================================
// STORES
// =============================================================================

const store = useRosetteStore()

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
  leftId,
  rightId,
  left,
  right,
  loading,
  error,
  isOpen,
  autoComparedOnce,
  liveCompare,
  showKeyboardHints,
  canCompare
} = useSnapshotCompareState()

// Compare logic
const {
  deltaRows,
  scoreDelta,
  warningDelta,
  confidenceLevel,
  confidenceTrend,
  confidenceTooltip,
  loadSnapshotsForCompare
} = useSnapshotCompareLogic(
  leftId,
  rightId,
  left,
  right,
  loading,
  error,
  canCompare
)

// Navigation
const {
  pickBaselineLeft,
  swapSides,
  clearCompare,
  stepRight,
  stepLeft
} = useSnapshotCompareNavigation(
  leftId,
  rightId,
  left,
  right,
  error,
  isOpen,
  autoComparedOnce,
  liveCompare,
  () => store.snapshots || [],
  loadSnapshotsForCompare
)

// Keyboard (handles lifecycle internally)
useSnapshotCompareKeyboard(isOpen, stepLeft, stepRight)
</script>

<template>
  <div class="card">
    <div class="row">
      <h3 style="display:flex; align-items:center; gap:8px; margin:0;">
        <button
          class="btn"
          style="padding:6px 10px;"
          @click="isOpen = !isOpen"
        >
          {{ isOpen ? "▾" : "▸" }}
        </button>
        Snapshot Compare
      </h3>
      <div class="actions">
        <button
          class="btn"
          :disabled="store.snapshotsLoading"
          @click="store.loadRecentSnapshots()"
        >
          Refresh list
        </button>
      </div>
    </div>

    <CompareOpenPanel
      v-if="isOpen"
      v-model:left-id="leftId"
      v-model:right-id="rightId"
      v-model:live-compare="liveCompare"
      v-model:show-keyboard-hints="showKeyboardHints"
      :snapshots="store.snapshots"
      :loading="loading"
      :error="error"
      :left="left"
      :right="right"
      :can-compare="canCompare"
      :delta-rows="deltaRows"
      :confidence-level="confidenceLevel"
      :confidence-trend="confidenceTrend"
      :confidence-tooltip="confidenceTooltip"
      :score-delta="scoreDelta"
      :warning-delta="warningDelta"
      @pick-baseline-left="pickBaselineLeft"
      @swap-sides="swapSides"
      @compare="loadSnapshotsForCompare"
      @clear="clearCompare"
      @load-snapshot="store.loadSnapshot"
    />
  </div>
</template>

<style scoped>
.card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.row {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  margin: 8px 0;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #ccc;
  background: #f7f7f7;
  cursor: pointer;
}

.actions {
  display: flex;
  gap: 8px;
}
</style>
