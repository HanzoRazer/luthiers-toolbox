<script setup lang="ts">
/**
 * BulkDecisionControlsV2 - Dropdown-based bulk decision controls
 *
 * Extracted from ManufacturingCandidateList.vue
 */

export type RiskDecision = "GREEN" | "YELLOW" | "RED";

const props = defineProps<{
  selectedCount: number;
  bulkDecision: RiskDecision | null;
  bulkNote: string;
  bulkClearNoteToo: boolean;
  bulkApplying: boolean;
  bulkProgress: { done: number; total: number } | null;
  saving: boolean;
  exporting: boolean;
  bulkHistoryLength: number;
  showBulkHistory: boolean;
}>();

const emit = defineEmits<{
  (e: "update:bulkDecision", value: RiskDecision | null): void;
  (e: "update:bulkNote", value: string): void;
  (e: "update:bulkClearNoteToo", value: boolean): void;
  (e: "update:showBulkHistory", value: boolean): void;
  (e: "apply"): void;
  (e: "clear"): void;
  (e: "undo"): void;
}>();

function onDecisionChange(event: Event) {
  const val = (event.target as HTMLSelectElement).value;
  emit("update:bulkDecision", val === "" ? null : val as RiskDecision);
}
</script>

<template>
  <div class="bulkbar2">
    <div class="bulk-row">
      <label class="muted">Bulk Decision:</label>
      <select
        :value="bulkDecision ?? ''"
        class="selectSmall"
        :disabled="bulkApplying || saving || exporting"
        @change="onDecisionChange"
      >
        <option value="">
          — pick —
        </option>
        <option value="GREEN">
          GREEN
        </option>
        <option value="YELLOW">
          YELLOW
        </option>
        <option value="RED">
          RED
        </option>
      </select>
      <input
        :value="bulkNote"
        class="inputSmall"
        placeholder="Shared note (optional)"
        :disabled="bulkApplying || saving || exporting"
        @input="emit('update:bulkNote', ($event.target as HTMLInputElement).value)"
      >
      <button
        class="btn small"
        :disabled="bulkApplying || saving || exporting || !bulkDecision"
        @click="emit('apply')"
      >
        {{ bulkApplying ? `Applying… (${bulkProgress?.done ?? 0}/${bulkProgress?.total ?? 0})` : 'Apply' }}
      </button>
      <label
        class="inlineCheck"
        title="When clearing decisions, also clear decision notes"
      >
        <input
          :checked="bulkClearNoteToo"
          type="checkbox"
          :disabled="bulkApplying"
          @change="emit('update:bulkClearNoteToo', ($event.target as HTMLInputElement).checked)"
        >
        clear note too
      </label>
      <button
        class="btn small"
        :disabled="bulkApplying || saving || exporting || selectedCount === 0"
        :title="selectedCount ? 'Clear decision (set to null) for selected candidates (hotkey: b)' : 'Select one or more candidates first'"
        @click="emit('clear')"
      >
        Clear decision
      </button>
      <button
        class="btn ghost small"
        :disabled="bulkApplying || saving || exporting || bulkHistoryLength === 0"
        title="Undo last bulk action"
        @click="emit('undo')"
      >
        Undo
      </button>
      <button
        class="btn ghost small"
        :title="showBulkHistory ? 'Hide bulk history' : 'Show bulk history (hotkey: h)'"
        @click="emit('update:showBulkHistory', !showBulkHistory)"
      >
        {{ showBulkHistory ? 'Hide history' : `History (${bulkHistoryLength})` }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.bulkbar2 {
  padding: 8px;
  border: 1px dashed rgba(0, 0, 0, 0.18);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.02);
}

.bulk-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.muted {
  opacity: 0.75;
}

.selectSmall {
  padding: 4px 8px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 6px;
  font-size: 13px;
}

.inputSmall {
  padding: 4px 8px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 6px;
  font-size: 13px;
  min-width: 160px;
}

.btn {
  padding: 6px 10px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  background: white;
  cursor: pointer;
}

.btn.small {
  padding: 4px 8px;
  font-size: 13px;
}

.btn.ghost {
  background: transparent;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.inlineCheck {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  cursor: pointer;
}
</style>
