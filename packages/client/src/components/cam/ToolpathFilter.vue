<script setup lang="ts">
/**
 * ToolpathFilter — P5 Segment Filtering Panel
 *
 * Provides UI for filtering and highlighting toolpath segments:
 * - Quick presets (cuts only, rapids only, etc.)
 * - Move type toggles (rapid, linear, arc)
 * - Z depth range slider
 * - Feed rate range slider
 * - Display mode (hide vs dim)
 */

import { computed } from "vue";
import {
  useSegmentFilter,
  FILTER_PRESETS,
  type MoveSegment,
} from "@/composables/useSegmentFilter";
import type { Ref } from "vue";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface Props {
  segments: MoveSegment[];
}

const props = defineProps<Props>();

// ---------------------------------------------------------------------------
// Filter composable
// ---------------------------------------------------------------------------
// Create a ref-like wrapper for the segments prop
const segmentsRef = computed(() => props.segments) as unknown as Ref<MoveSegment[]>;

const {
  filterState,
  activePresetId,
  segmentBounds,
  filterStats,
  hasActiveFilter,
  presets,
  applyPreset,
  resetFilter,
  setTypeFilter,
  setZFilter,
  setFeedFilter,
  setDisplayMode,
  setDimOpacity,
} = useSegmentFilter(segmentsRef);

// ---------------------------------------------------------------------------
// Expose for parent
// ---------------------------------------------------------------------------
defineExpose({
  filterState,
  hasActiveFilter,
  filterStats,
  resetFilter,
});
</script>

<template>
  <div class="toolpath-filter">
    <!-- Filter Stats Bar -->
    <div class="filter-stats" :class="{ active: hasActiveFilter }">
      <span class="stats-label">
        <template v-if="hasActiveFilter">
          🔍 {{ filterStats.visible.toLocaleString() }} / {{ filterStats.total.toLocaleString() }}
          ({{ filterStats.percent.toFixed(0) }}%)
        </template>
        <template v-else>
          Showing all {{ filterStats.total.toLocaleString() }} segments
        </template>
      </span>
      <button
        v-if="hasActiveFilter"
        class="reset-btn"
        title="Reset filter"
        @click="resetFilter"
      >
        Reset
      </button>
    </div>

    <!-- Quick Presets -->
    <div class="filter-section">
      <h4 class="section-title">Quick Presets</h4>
      <div class="preset-grid">
        <button
          v-for="preset in presets"
          :key="preset.id"
          class="preset-btn"
          :class="{ active: activePresetId === preset.id }"
          :title="preset.description"
          @click="applyPreset(preset.id)"
        >
          <span class="preset-icon">{{ preset.icon }}</span>
          <span class="preset-name">{{ preset.name }}</span>
        </button>
      </div>
    </div>

    <!-- Move Type Toggles -->
    <div class="filter-section">
      <h4 class="section-title">Move Types</h4>
      <div class="type-toggles">
        <label class="type-toggle rapid">
          <input
            type="checkbox"
            :checked="filterState.showRapid"
            @change="setTypeFilter('rapid', ($event.target as HTMLInputElement).checked)"
          >
          <span class="toggle-label">
            <span class="toggle-color" />
            Rapid (G0)
          </span>
        </label>
        <label class="type-toggle linear">
          <input
            type="checkbox"
            :checked="filterState.showLinear"
            @change="setTypeFilter('linear', ($event.target as HTMLInputElement).checked)"
          >
          <span class="toggle-label">
            <span class="toggle-color" />
            Linear (G1)
          </span>
        </label>
        <label class="type-toggle arc-cw">
          <input
            type="checkbox"
            :checked="filterState.showArcCW"
            @change="setTypeFilter('arcCW', ($event.target as HTMLInputElement).checked)"
          >
          <span class="toggle-label">
            <span class="toggle-color" />
            Arc CW (G2)
          </span>
        </label>
        <label class="type-toggle arc-ccw">
          <input
            type="checkbox"
            :checked="filterState.showArcCCW"
            @change="setTypeFilter('arcCCW', ($event.target as HTMLInputElement).checked)"
          >
          <span class="toggle-label">
            <span class="toggle-color" />
            Arc CCW (G3)
          </span>
        </label>
      </div>
    </div>

    <!-- Z Depth Filter -->
    <div class="filter-section">
      <div class="section-header">
        <h4 class="section-title">Z Depth Range</h4>
        <label class="enable-toggle">
          <input
            type="checkbox"
            :checked="filterState.zFilterEnabled"
            @change="setZFilter(($event.target as HTMLInputElement).checked)"
          >
          <span>Enable</span>
        </label>
      </div>
      <div class="range-control" :class="{ disabled: !filterState.zFilterEnabled }">
        <div class="range-inputs">
          <div class="range-input-group">
            <label>Min</label>
            <input
              type="number"
              :value="filterState.zMin.toFixed(1)"
              :disabled="!filterState.zFilterEnabled"
              step="0.5"
              @input="setZFilter(true, parseFloat(($event.target as HTMLInputElement).value), undefined)"
            >
          </div>
          <div class="range-slider-container">
            <input
              type="range"
              class="range-slider z-slider"
              :min="segmentBounds.zMin"
              :max="segmentBounds.zMax"
              step="0.1"
              :value="filterState.zMin"
              :disabled="!filterState.zFilterEnabled"
              @input="setZFilter(true, parseFloat(($event.target as HTMLInputElement).value), undefined)"
            >
            <input
              type="range"
              class="range-slider z-slider"
              :min="segmentBounds.zMin"
              :max="segmentBounds.zMax"
              step="0.1"
              :value="filterState.zMax"
              :disabled="!filterState.zFilterEnabled"
              @input="setZFilter(true, undefined, parseFloat(($event.target as HTMLInputElement).value))"
            >
          </div>
          <div class="range-input-group">
            <label>Max</label>
            <input
              type="number"
              :value="filterState.zMax.toFixed(1)"
              :disabled="!filterState.zFilterEnabled"
              step="0.5"
              @input="setZFilter(true, undefined, parseFloat(($event.target as HTMLInputElement).value))"
            >
          </div>
        </div>
        <div class="range-labels">
          <span>{{ segmentBounds.zMin.toFixed(1) }} mm</span>
          <span>{{ segmentBounds.zMax.toFixed(1) }} mm</span>
        </div>
      </div>
    </div>

    <!-- Feed Rate Filter -->
    <div class="filter-section">
      <div class="section-header">
        <h4 class="section-title">Feed Rate Range</h4>
        <label class="enable-toggle">
          <input
            type="checkbox"
            :checked="filterState.feedFilterEnabled"
            @change="setFeedFilter(($event.target as HTMLInputElement).checked)"
          >
          <span>Enable</span>
        </label>
      </div>
      <div class="range-control" :class="{ disabled: !filterState.feedFilterEnabled }">
        <div class="range-inputs">
          <div class="range-input-group">
            <label>Min</label>
            <input
              type="number"
              :value="Math.round(filterState.feedMin)"
              :disabled="!filterState.feedFilterEnabled"
              step="100"
              @input="setFeedFilter(true, parseFloat(($event.target as HTMLInputElement).value), undefined)"
            >
          </div>
          <div class="range-slider-container">
            <input
              type="range"
              class="range-slider feed-slider"
              :min="segmentBounds.feedMin"
              :max="segmentBounds.feedMax"
              step="10"
              :value="filterState.feedMin"
              :disabled="!filterState.feedFilterEnabled"
              @input="setFeedFilter(true, parseFloat(($event.target as HTMLInputElement).value), undefined)"
            >
            <input
              type="range"
              class="range-slider feed-slider"
              :min="segmentBounds.feedMin"
              :max="segmentBounds.feedMax"
              step="10"
              :value="filterState.feedMax"
              :disabled="!filterState.feedFilterEnabled"
              @input="setFeedFilter(true, undefined, parseFloat(($event.target as HTMLInputElement).value))"
            >
          </div>
          <div class="range-input-group">
            <label>Max</label>
            <input
              type="number"
              :value="Math.round(filterState.feedMax)"
              :disabled="!filterState.feedFilterEnabled"
              step="100"
              @input="setFeedFilter(true, undefined, parseFloat(($event.target as HTMLInputElement).value))"
            >
          </div>
        </div>
        <div class="range-labels">
          <span>{{ Math.round(segmentBounds.feedMin) }} mm/min</span>
          <span>{{ Math.round(segmentBounds.feedMax) }} mm/min</span>
        </div>
      </div>
    </div>

    <!-- Display Mode -->
    <div class="filter-section">
      <h4 class="section-title">Non-Matching Display</h4>
      <div class="display-mode-options">
        <label class="mode-option" :class="{ active: filterState.displayMode === 'dim' }">
          <input
            type="radio"
            name="displayMode"
            value="dim"
            :checked="filterState.displayMode === 'dim'"
            @change="setDisplayMode('dim')"
          >
          <span class="mode-label">
            <span class="mode-icon">👁️</span>
            Dim
          </span>
        </label>
        <label class="mode-option" :class="{ active: filterState.displayMode === 'hide' }">
          <input
            type="radio"
            name="displayMode"
            value="hide"
            :checked="filterState.displayMode === 'hide'"
            @change="setDisplayMode('hide')"
          >
          <span class="mode-label">
            <span class="mode-icon">🚫</span>
            Hide
          </span>
        </label>
      </div>
      <div v-if="filterState.displayMode === 'dim'" class="opacity-control">
        <label>Dim Opacity:</label>
        <input
          type="range"
          min="0.05"
          max="0.5"
          step="0.05"
          :value="filterState.dimOpacity"
          @input="setDimOpacity(parseFloat(($event.target as HTMLInputElement).value))"
        >
        <span>{{ Math.round(filterState.dimOpacity * 100) }}%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolpath-filter {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  font-size: 11px;
  color: #ccc;
}

/* ── Stats Bar ─────────────────────────────────────────────────────── */
.filter-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 6px;
}

.filter-stats.active {
  background: rgba(243, 156, 18, 0.1);
  border-color: #f39c12;
}

.stats-label {
  color: #aaa;
}

.filter-stats.active .stats-label {
  color: #f39c12;
}

.reset-btn {
  padding: 3px 10px;
  background: #f39c12;
  border: none;
  border-radius: 4px;
  color: #1a1a2e;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
}

.reset-btn:hover {
  background: #e67e22;
}

/* ── Sections ──────────────────────────────────────────────────────── */
.filter-section {
  background: #1a1a2e;
  border: 1px solid #2a2a4a;
  border-radius: 6px;
  padding: 10px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-title {
  margin: 0 0 10px 0;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #888;
}

.section-header .section-title {
  margin: 0;
}

/* ── Presets ───────────────────────────────────────────────────────── */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.preset-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #888;
  cursor: pointer;
  transition: all 0.15s;
}

.preset-btn:hover {
  background: #33334a;
  color: #ccc;
  border-color: #4a4a6c;
}

.preset-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}

.preset-icon {
  font-size: 12px;
}

.preset-name {
  font-size: 10px;
  font-weight: 500;
}

/* ── Type Toggles ──────────────────────────────────────────────────── */
.type-toggles {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.type-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.type-toggle:hover {
  background: #33334a;
}

.type-toggle input {
  display: none;
}

.type-toggle input:checked + .toggle-label {
  color: #fff;
}

.type-toggle input:not(:checked) + .toggle-label {
  opacity: 0.5;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  transition: opacity 0.15s;
}

.toggle-color {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.type-toggle.rapid .toggle-color { background: #e74c3c; }
.type-toggle.linear .toggle-color { background: #2ecc71; }
.type-toggle.arc-cw .toggle-color { background: #3498db; }
.type-toggle.arc-ccw .toggle-color { background: #9b59b6; }

/* ── Enable Toggle ─────────────────────────────────────────────────── */
.enable-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: #888;
  cursor: pointer;
}

.enable-toggle input {
  accent-color: #4a90d9;
}

.enable-toggle input:checked + span {
  color: #4a90d9;
}

/* ── Range Controls ────────────────────────────────────────────────── */
.range-control {
  transition: opacity 0.15s;
}

.range-control.disabled {
  opacity: 0.4;
  pointer-events: none;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-input-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.range-input-group label {
  font-size: 9px;
  color: #666;
  text-transform: uppercase;
}

.range-input-group input {
  width: 60px;
  padding: 4px 6px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #ccc;
  font-size: 10px;
  text-align: center;
}

.range-input-group input:focus {
  outline: none;
  border-color: #4a90d9;
}

.range-slider-container {
  flex: 1;
  position: relative;
  height: 20px;
}

.range-slider {
  position: absolute;
  width: 100%;
  height: 4px;
  top: 8px;
  -webkit-appearance: none;
  background: transparent;
  pointer-events: none;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #4a90d9;
  cursor: pointer;
  pointer-events: auto;
  border: 2px solid #1a1a2e;
}

.range-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #4a90d9;
  cursor: pointer;
  pointer-events: auto;
  border: 2px solid #1a1a2e;
}

.range-slider:first-child {
  background: linear-gradient(90deg, #3a3a5c 0%, #3a3a5c 100%);
  border-radius: 2px;
}

.z-slider::-webkit-slider-thumb { background: #e67e22; }
.z-slider::-moz-range-thumb { background: #e67e22; }

.feed-slider::-webkit-slider-thumb { background: #2ecc71; }
.feed-slider::-moz-range-thumb { background: #2ecc71; }

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 9px;
  color: #666;
}

/* ── Display Mode ──────────────────────────────────────────────────── */
.display-mode-options {
  display: flex;
  gap: 8px;
}

.mode-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.mode-option:hover {
  background: #33334a;
}

.mode-option.active {
  background: #1a3a6b;
  border-color: #4a90d9;
}

.mode-option input {
  display: none;
}

.mode-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #888;
}

.mode-option.active .mode-label {
  color: #4a90d9;
}

.mode-icon {
  font-size: 14px;
}

/* ── Opacity Control ───────────────────────────────────────────────── */
.opacity-control {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #2a2a4a;
}

.opacity-control label {
  color: #666;
  font-size: 10px;
}

.opacity-control input[type="range"] {
  flex: 1;
  accent-color: #4a90d9;
  height: 4px;
}

.opacity-control span {
  min-width: 30px;
  text-align: right;
  color: #4a90d9;
  font-size: 10px;
}
</style>
