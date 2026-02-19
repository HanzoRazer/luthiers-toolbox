<script setup lang="ts">
/**
 * BulkDecisionBar - Quick bulk decision buttons for selected candidates
 *
 * Extracted from ManufacturingCandidateList.vue
 */

defineProps<{
  selectedCount: number;
  disabled: boolean;
  undoStackLength: number;
  undoBusy: boolean;
  lastUndoLabel?: string;
}>();

const emit = defineEmits<{
  (e: "bulk-green"): void;
  (e: "bulk-yellow"): void;
  (e: "bulk-red"): void;
  (e: "clear-decision"): void;
  (e: "undo-last"): void;
}>();
</script>

<template>
  <div class="bulkbar">
    <div class="bulk-left">
      <span class="muted">
        Selected: <strong>{{ selectedCount }}</strong>
      </span>
      <span
        v-if="selectedCount === 0"
        class="muted"
      > (select rows to bulk-set decision)</span>
    </div>
    <div class="bulk-actions">
      <button
        class="btn"
        :disabled="disabled || selectedCount === 0"
        title="Set selected to GREEN"
        @click="emit('bulk-green')"
      >
        Bulk GREEN
      </button>
      <button
        class="btn"
        :disabled="disabled || selectedCount === 0"
        title="Set selected to YELLOW"
        @click="emit('bulk-yellow')"
      >
        Bulk YELLOW
      </button>
      <button
        class="btn danger"
        :disabled="disabled || selectedCount === 0"
        title="Set selected to RED"
        @click="emit('bulk-red')"
      >
        Bulk RED
      </button>
      <button
        class="btn ghost"
        :disabled="disabled"
        title="Clear decision for selected candidates"
        @click="emit('clear-decision')"
      >
        Clear decision
      </button>
      <button
        class="btn ghost"
        :disabled="undoBusy || disabled || undoStackLength === 0"
        :title="undoStackLength ? lastUndoLabel : 'Nothing to undo'"
        @click="emit('undo-last')"
      >
        {{ undoBusy ? "Undoing…" : "Undo last" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.bulkbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px;
  border: 1px dashed rgba(0, 0, 0, 0.18);
  border-radius: 10px;
}

.bulk-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.bulk-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.muted {
  opacity: 0.75;
}

.btn {
  padding: 6px 10px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  background: white;
  cursor: pointer;
}

.btn.ghost {
  background: transparent;
}

.btn.danger {
  border-color: rgba(176, 0, 32, 0.35);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
