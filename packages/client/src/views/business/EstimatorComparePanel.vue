<script setup lang="ts">
/**
 * EstimatorComparePanel - Compare multiple estimates side-by-side
 *
 * Features:
 * - Select 2-3 estimates from history
 * - Visual comparison table
 * - Highlight differences
 * - Clear winner indication
 */
import { ref, computed, onMounted } from "vue";
import type { EstimateRequest, EstimateResult } from "@/types/businessEstimator";

// ============================================================================
// TYPES
// ============================================================================

interface HistoryEntry {
  id: string;
  request: EstimateRequest;
  result: EstimateResult;
  createdAt: string;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STORAGE_KEY = "ltb:estimator:history:v1";
const MAX_COMPARE = 3;

// ============================================================================
// STATE
// ============================================================================

const history = ref<HistoryEntry[]>([]);
const selectedIds = ref<string[]>([]);
const showSelector = ref(true);

// ============================================================================
// COMPUTED
// ============================================================================

const selectedEstimates = computed(() => {
  return selectedIds.value
    .map((id) => history.value.find((e) => e.id === id))
    .filter((e): e is HistoryEntry => e !== undefined);
});

const canCompare = computed(() => selectedIds.value.length >= 2);

const comparisonMetrics = computed(() => {
  if (selectedEstimates.value.length < 2) return [];

  const metrics = [
    {
      key: "total_cost_per_unit",
      label: "Total Cost",
      format: (v: number) => `$${v.toFixed(0)}`,
      lower_better: true,
    },
    {
      key: "total_hours",
      label: "Total Hours",
      format: (v: number) => `${v.toFixed(1)}h`,
      lower_better: true,
    },
    {
      key: "labor_cost_per_unit",
      label: "Labor Cost",
      format: (v: number) => `$${v.toFixed(0)}`,
      lower_better: true,
    },
    {
      key: "material_cost_per_unit",
      label: "Materials",
      format: (v: number) => `$${v.toFixed(0)}`,
      lower_better: true,
    },
    {
      key: "total_complexity_multiplier",
      label: "Complexity",
      format: (v: number) => `${v.toFixed(2)}x`,
      lower_better: true,
    },
    {
      key: "first_unit_hours",
      label: "First Unit Hours",
      format: (v: number) => `${v.toFixed(1)}h`,
      lower_better: true,
    },
  ];

  return metrics.map((metric) => {
    const values = selectedEstimates.value.map((e) => {
      const val = e.result[metric.key as keyof EstimateResult];
      return typeof val === "number" ? val : 0;
    });

    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);

    return {
      ...metric,
      values,
      formatted: values.map((v) => metric.format(v)),
      winners: values.map((v) =>
        metric.lower_better ? v === minVal : v === maxVal
      ),
      hasVariance: minVal !== maxVal,
    };
  });
});

const overallWinners = computed(() => {
  if (selectedEstimates.value.length < 2) return [];

  const scores = selectedEstimates.value.map(() => 0);

  comparisonMetrics.value.forEach((metric) => {
    metric.winners.forEach((isWinner, idx) => {
      if (isWinner && metric.hasVariance) scores[idx]++;
    });
  });

  const maxScore = Math.max(...scores);
  return scores.map((s) => s === maxScore && maxScore > 0);
});

// ============================================================================
// PERSISTENCE
// ============================================================================

function loadHistory(): void {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      history.value = JSON.parse(stored);
    }
  } catch (e) {
    console.warn("[EstimatorComparePanel] Failed to load history:", e);
    history.value = [];
  }
}

// ============================================================================
// ACTIONS
// ============================================================================

function toggleSelection(id: string): void {
  const idx = selectedIds.value.indexOf(id);
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1);
  } else if (selectedIds.value.length < MAX_COMPARE) {
    selectedIds.value.push(id);
  }
}

function isSelected(id: string): boolean {
  return selectedIds.value.includes(id);
}

function clearSelection(): void {
  selectedIds.value = [];
}

function startComparison(): void {
  if (canCompare.value) {
    showSelector.value = false;
  }
}

function backToSelector(): void {
  showSelector.value = true;
}

// ============================================================================
// FORMATTERS
// ============================================================================

function formatInstrumentType(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function getSelectionIndex(id: string): number {
  return selectedIds.value.indexOf(id) + 1;
}

// ============================================================================
// LIFECYCLE
// ============================================================================

onMounted(() => {
  loadHistory();
});
</script>

<template>
  <div class="compare-panel">
    <header class="panel-header">
      <h3>Compare Estimates</h3>
      <div v-if="!showSelector" class="header-actions">
        <button type="button" class="btn-back" @click="backToSelector">
          &larr; Select Different
        </button>
      </div>
    </header>

    <!-- Selector View -->
    <template v-if="showSelector">
      <p class="instructions">
        Select 2-3 estimates to compare side-by-side.
      </p>

      <!-- Empty State -->
      <div v-if="history.length === 0" class="empty-state">
        <p>No estimates in history.</p>
        <p class="hint">Run some estimates first to enable comparison.</p>
      </div>

      <!-- Selection List -->
      <div v-else class="selection-list">
        <div
          v-for="entry in history"
          :key="entry.id"
          class="selection-card"
          :class="{
            selected: isSelected(entry.id),
            disabled: !isSelected(entry.id) && selectedIds.length >= MAX_COMPARE,
          }"
          @click="toggleSelection(entry.id)"
        >
          <div class="selection-index" v-if="isSelected(entry.id)">
            {{ getSelectionIndex(entry.id) }}
          </div>
          <div class="selection-info">
            <div class="selection-instrument">
              {{ formatInstrumentType(entry.request.instrument_type) }}
            </div>
            <div class="selection-meta">
              ${{ entry.result.total_cost_per_unit.toFixed(0) }}
              <span class="separator">·</span>
              {{ entry.result.total_hours.toFixed(1) }}h
              <span class="separator">·</span>
              {{ formatDate(entry.createdAt) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="selector-actions" v-if="history.length > 0">
        <button
          type="button"
          class="btn-secondary"
          :disabled="selectedIds.length === 0"
          @click="clearSelection"
        >
          Clear
        </button>
        <button
          type="button"
          class="btn-primary"
          :disabled="!canCompare"
          @click="startComparison"
        >
          Compare ({{ selectedIds.length }})
        </button>
      </div>
    </template>

    <!-- Comparison View -->
    <template v-else>
      <!-- Column Headers -->
      <div class="compare-grid">
        <div class="metric-label header"></div>
        <div
          v-for="(entry, idx) in selectedEstimates"
          :key="entry.id"
          class="compare-header"
          :class="{ winner: overallWinners[idx] }"
        >
          <div class="header-instrument">
            {{ formatInstrumentType(entry.request.instrument_type) }}
          </div>
          <div class="header-date">{{ formatDate(entry.createdAt) }}</div>
          <div v-if="overallWinners[idx]" class="winner-badge">Best</div>
        </div>
      </div>

      <!-- Metric Rows -->
      <div
        v-for="metric in comparisonMetrics"
        :key="metric.key"
        class="compare-grid metric-row"
      >
        <div class="metric-label">{{ metric.label }}</div>
        <div
          v-for="(value, idx) in metric.formatted"
          :key="idx"
          class="metric-value"
          :class="{ winner: metric.winners[idx] && metric.hasVariance }"
        >
          {{ value }}
        </div>
      </div>

      <!-- Experience Row -->
      <div class="compare-grid metric-row">
        <div class="metric-label">Experience</div>
        <div
          v-for="entry in selectedEstimates"
          :key="entry.id"
          class="metric-value"
        >
          {{ entry.result.experience_level }}
        </div>
      </div>

      <!-- Confidence Row -->
      <div class="compare-grid metric-row">
        <div class="metric-label">Confidence</div>
        <div
          v-for="entry in selectedEstimates"
          :key="entry.id"
          class="metric-value"
        >
          {{ entry.result.confidence_level }}
        </div>
      </div>

      <!-- Range Row -->
      <div class="compare-grid metric-row">
        <div class="metric-label">Range</div>
        <div
          v-for="entry in selectedEstimates"
          :key="entry.id"
          class="metric-value range"
        >
          ${{ entry.result.estimate_range_low.toFixed(0) }} -
          ${{ entry.result.estimate_range_high.toFixed(0) }}
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.compare-panel {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel-header h3 {
  font-size: 10px;
  letter-spacing: 2px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0;
}

.btn-back {
  padding: 4px 10px;
  font-size: 9px;
  font-family: inherit;
  background: transparent;
  border: 1px solid #2a3040;
  color: #6080b0;
  border-radius: 3px;
  cursor: pointer;
}

.btn-back:hover {
  border-color: #4060c0;
  color: #80a0d0;
}

.instructions {
  font-size: 11px;
  color: #506090;
  margin: 0 0 12px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 24px 16px;
  color: #506090;
}

.empty-state p {
  margin: 0;
  font-size: 12px;
}

.empty-state .hint {
  font-size: 11px;
  color: #404870;
  margin-top: 8px;
}

/* Selection List */
.selection-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.selection-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #14192a;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.selection-card:hover:not(.disabled) {
  border-color: #3060c0;
}

.selection-card.selected {
  border-color: #4080f0;
  background: #1a2040;
}

.selection-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.selection-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #4080f0;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
}

.selection-info {
  flex: 1;
  min-width: 0;
}

.selection-instrument {
  font-size: 12px;
  font-weight: 600;
  color: #c0c8e0;
  margin-bottom: 2px;
}

.selection-meta {
  font-size: 10px;
  color: #506090;
}

.separator {
  margin: 0 4px;
  color: #2a3040;
}

/* Selector Actions */
.selector-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #1e2438;
}

.btn-secondary,
.btn-primary {
  padding: 8px 16px;
  font-size: 10px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary {
  background: #14192a;
  border: 1px solid #2a3040;
  color: #8090b0;
}

.btn-secondary:hover:not(:disabled) {
  border-color: #4060c0;
  color: #c0c8e0;
}

.btn-primary {
  background: #2050a0;
  border: 1px solid #3060c0;
  color: #e0e8ff;
}

.btn-primary:hover:not(:disabled) {
  background: #2860c0;
}

.btn-secondary:disabled,
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Comparison Grid */
.compare-grid {
  display: grid;
  grid-template-columns: 120px repeat(3, 1fr);
  gap: 1px;
}

.compare-grid.metric-row {
  border-top: 1px solid #1e2438;
}

.metric-label {
  padding: 10px 8px;
  font-size: 10px;
  color: #6080b0;
  text-transform: uppercase;
  letter-spacing: 1px;
  background: #0d1020;
}

.metric-label.header {
  padding: 0;
}

.compare-header {
  padding: 12px 8px;
  background: #14192a;
  text-align: center;
  position: relative;
}

.compare-header.winner {
  background: #1a2840;
  border-top: 2px solid #60e0a0;
}

.header-instrument {
  font-size: 11px;
  font-weight: 600;
  color: #c0c8e0;
  margin-bottom: 2px;
}

.header-date {
  font-size: 9px;
  color: #506090;
}

.winner-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  padding: 2px 6px;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  background: #60e0a0;
  color: #0d1020;
  border-radius: 2px;
}

.metric-value {
  padding: 10px 8px;
  font-size: 12px;
  color: #c0c8e0;
  text-align: center;
  background: #14192a;
}

.metric-value.winner {
  color: #60e0a0;
  font-weight: 700;
  background: #162028;
}

.metric-value.range {
  font-size: 10px;
  color: #8090b0;
}
</style>
