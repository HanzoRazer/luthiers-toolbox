<script setup lang="ts">
/**
 * EstimatorHistoryPanel - Browse past estimates
 *
 * Features:
 * - Auto-saves completed estimates
 * - Browse and filter history
 * - Load historical estimate to view details
 * - Clear history
 */
import { ref, computed, onMounted, watch } from "vue";
import type { EstimateRequest, EstimateResult } from "@/types/businessEstimator";

const props = defineProps<{
  currentEstimate: EstimateResult | null;
  currentRequest: EstimateRequest;
}>();

const emit = defineEmits<{
  viewEstimate: [entry: HistoryEntry];
}>();

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
const MAX_HISTORY_ENTRIES = 50;

// ============================================================================
// STATE
// ============================================================================

const history = ref<HistoryEntry[]>([]);
const filterInstrument = ref<string>("all");
const showClearConfirm = ref(false);
const selectedEntryId = ref<string | null>(null);

// ============================================================================
// COMPUTED
// ============================================================================

const instrumentTypes = computed(() => {
  const types = new Set(history.value.map((e) => e.request.instrument_type));
  return ["all", ...Array.from(types).sort()];
});

const filteredHistory = computed(() => {
  let entries = [...history.value];

  if (filterInstrument.value !== "all") {
    entries = entries.filter(
      (e) => e.request.instrument_type === filterInstrument.value
    );
  }

  return entries.sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );
});

const totalSaved = computed(() => {
  return history.value.reduce((sum, e) => sum + e.result.total_cost_per_unit, 0);
});

const averageCost = computed(() => {
  if (history.value.length === 0) return 0;
  return totalSaved.value / history.value.length;
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
    console.warn("[EstimatorHistoryPanel] Failed to load history:", e);
    history.value = [];
  }
}

function saveHistory(): void {
  try {
    // Keep only the most recent entries
    const toSave = history.value.slice(0, MAX_HISTORY_ENTRIES);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch (e) {
    console.warn("[EstimatorHistoryPanel] Failed to save history:", e);
  }
}

// ============================================================================
// ACTIONS
// ============================================================================

function addToHistory(request: EstimateRequest, result: EstimateResult): void {
  const entry: HistoryEntry = {
    id: `hist_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    request: { ...request },
    result: { ...result },
    createdAt: new Date().toISOString(),
  };

  // Add to beginning of history
  history.value.unshift(entry);

  // Trim to max entries
  if (history.value.length > MAX_HISTORY_ENTRIES) {
    history.value = history.value.slice(0, MAX_HISTORY_ENTRIES);
  }

  saveHistory();
}

function selectEntry(entry: HistoryEntry): void {
  selectedEntryId.value = entry.id;
  emit("viewEstimate", entry);
}

function deleteEntry(entryId: string): void {
  history.value = history.value.filter((e) => e.id !== entryId);
  saveHistory();
  if (selectedEntryId.value === entryId) {
    selectedEntryId.value = null;
  }
}

function confirmClearHistory(): void {
  showClearConfirm.value = true;
}

function cancelClear(): void {
  showClearConfirm.value = false;
}

function clearHistory(): void {
  history.value = [];
  saveHistory();
  showClearConfirm.value = false;
  selectedEntryId.value = null;
}

function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  } else if (diffDays === 1) {
    return "Yesterday";
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  }
}

function formatInstrumentType(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatCurrency(value: number): string {
  return `$${value.toFixed(0)}`;
}

// ============================================================================
// WATCHERS
// ============================================================================

// Auto-save when estimate changes
watch(
  () => props.currentEstimate,
  (newEstimate) => {
    if (newEstimate) {
      // Check if this is a meaningfully different estimate
      const lastEntry = history.value[0];
      if (
        !lastEntry ||
        lastEntry.result.total_cost_per_unit !== newEstimate.total_cost_per_unit ||
        lastEntry.request.instrument_type !== props.currentRequest.instrument_type
      ) {
        addToHistory(props.currentRequest, newEstimate);
      }
    }
  }
);

// ============================================================================
// LIFECYCLE
// ============================================================================

onMounted(() => {
  loadHistory();
});

// Expose for parent to trigger save
defineExpose({
  addToHistory,
});
</script>

<template>
  <div class="history-panel">
    <header class="panel-header">
      <h3>History</h3>
      <div class="header-actions">
        <span
          v-if="history.length > 0"
          class="entry-count"
        >
          {{ history.length }} estimate{{ history.length !== 1 ? 's' : '' }}
        </span>
        <button
          v-if="history.length > 0 && !showClearConfirm"
          type="button"
          class="btn-clear"
          @click="confirmClearHistory"
        >
          Clear
        </button>
        <template v-if="showClearConfirm">
          <button
            type="button"
            class="btn-confirm-clear"
            @click="clearHistory"
          >
            Confirm
          </button>
          <button
            type="button"
            class="btn-cancel-clear"
            @click="cancelClear"
          >
            Cancel
          </button>
        </template>
      </div>
    </header>

    <!-- Filter -->
    <div
      v-if="instrumentTypes.length > 2"
      class="filter-row"
    >
      <select
        v-model="filterInstrument"
        class="filter-select"
      >
        <option
          v-for="type in instrumentTypes"
          :key="type"
          :value="type"
        >
          {{ type === 'all' ? 'All Instruments' : formatInstrumentType(type) }}
        </option>
      </select>
    </div>

    <!-- Stats -->
    <div
      v-if="history.length > 0"
      class="stats-row"
    >
      <div class="stat">
        <span class="stat-value">{{ formatCurrency(averageCost) }}</span>
        <span class="stat-label">Avg Cost</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ history.length }}</span>
        <span class="stat-label">Estimates</span>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="history.length === 0"
      class="empty-state"
    >
      <p>No estimate history yet.</p>
      <p class="hint">
        Run an estimate to start building your history.
      </p>
    </div>

    <!-- History List -->
    <div
      v-else
      class="history-list"
    >
      <div
        v-for="entry in filteredHistory"
        :key="entry.id"
        class="history-card"
        :class="{ selected: selectedEntryId === entry.id }"
        @click="selectEntry(entry)"
      >
        <div class="entry-info">
          <div class="entry-instrument">
            {{ formatInstrumentType(entry.request.instrument_type) }}
          </div>
          <div class="entry-meta">
            <span class="entry-cost">{{ formatCurrency(entry.result.total_cost_per_unit) }}</span>
            <span class="separator">·</span>
            <span class="entry-hours">{{ entry.result.total_hours.toFixed(1) }}h</span>
            <span class="separator">·</span>
            <span class="entry-date">{{ formatDate(entry.createdAt) }}</span>
          </div>
        </div>
        <button
          type="button"
          class="btn-delete"
          title="Remove from history"
          @click.stop="deleteEntry(entry.id)"
        >
          ×
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-panel {
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.entry-count {
  font-size: 10px;
  color: #506090;
}

.btn-clear,
.btn-confirm-clear,
.btn-cancel-clear {
  padding: 4px 8px;
  font-size: 9px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-radius: 3px;
  cursor: pointer;
}

.btn-clear {
  background: transparent;
  border: 1px solid #2a3040;
  color: #6080b0;
}

.btn-confirm-clear {
  background: #802020;
  border: 1px solid #a03030;
  color: #ffb0b0;
}

.btn-cancel-clear {
  background: transparent;
  border: 1px solid #2a3040;
  color: #6080b0;
}

/* Filter */
.filter-row {
  margin-bottom: 12px;
}

.filter-select {
  width: 100%;
  padding: 6px 10px;
  font-size: 11px;
  font-family: inherit;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #c0c8e0;
  border-radius: 3px;
  cursor: pointer;
}

/* Stats */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  padding: 10px;
  background: #14192a;
  border-radius: 4px;
}

.stat {
  text-align: center;
  flex: 1;
}

.stat-value {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #60e0a0;
}

.stat-label {
  display: block;
  font-size: 9px;
  color: #506090;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 2px;
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

/* History List */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 250px;
  overflow-y: auto;
}

.history-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #14192a;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.history-card:hover {
  border-color: #3060c0;
}

.history-card.selected {
  border-color: #4080f0;
  background: #1a2040;
}

.entry-info {
  flex: 1;
  min-width: 0;
}

.entry-instrument {
  font-size: 11px;
  font-weight: 600;
  color: #c0c8e0;
  margin-bottom: 2px;
}

.entry-meta {
  font-size: 10px;
  color: #506090;
}

.entry-cost {
  color: #60e0a0;
  font-weight: 600;
}

.entry-hours {
  color: #80a0d0;
}

.separator {
  margin: 0 4px;
  color: #2a3040;
}

.btn-delete {
  width: 20px;
  height: 20px;
  padding: 0;
  font-size: 14px;
  font-family: inherit;
  background: transparent;
  border: none;
  color: #404870;
  cursor: pointer;
  opacity: 0;
  transition: all 0.15s;
}

.history-card:hover .btn-delete {
  opacity: 1;
}

.btn-delete:hover {
  color: #f06060;
}
</style>
