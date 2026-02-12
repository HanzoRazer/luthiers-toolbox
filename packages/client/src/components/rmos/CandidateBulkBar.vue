<script setup lang="ts">
/**
 * CandidateBulkBar - Bulk action controls for candidate list
 * Extracted from ManufacturingCandidateList.vue
 */
import type { RiskLevel } from '@/sdk/rmos/runs'

defineProps<{
  selectedCount: number
  disabled: boolean
  canClearDecision: boolean
  clearDecisionBlockedReason: string
  undoStackLength: number
  undoLastTitle: string
  undoBusy: boolean
}>()

const emit = defineEmits<{
  bulkSetDecision: [decision: RiskLevel]
  bulkClearDecision: []
  undoLast: []
}>()
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
      >
        (select rows to bulk-set decision)
      </span>
    </div>

    <div class="bulk-actions">
      <button
        class="btn btn-green"
        :disabled="disabled || selectedCount === 0"
        title="Set selected to GREEN"
        @click="emit('bulkSetDecision', 'GREEN')"
      >
        Bulk GREEN
      </button>
      <button
        class="btn btn-yellow"
        :disabled="disabled || selectedCount === 0"
        title="Set selected to YELLOW"
        @click="emit('bulkSetDecision', 'YELLOW')"
      >
        Bulk YELLOW
      </button>
      <button
        class="btn btn-red"
        :disabled="disabled || selectedCount === 0"
        title="Set selected to RED"
        @click="emit('bulkSetDecision', 'RED')"
      >
        Bulk RED
      </button>
      <button
        class="btn ghost"
        :disabled="disabled || !canClearDecision"
        :title="clearDecisionBlockedReason || 'Clear decision for selected'"
        @click="emit('bulkClearDecision')"
      >
        Clear decision
      </button>
      <button
        class="btn ghost"
        :disabled="undoBusy || disabled || undoStackLength === 0"
        :title="undoLastTitle"
        @click="emit('undoLast')"
      >
        {{ undoBusy ? 'Undoing…' : 'Undo last' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.bulkbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface-elevated, #f8f9fa);
  border-radius: var(--radius-md, 6px);
  margin-bottom: 0.5rem;
}

.bulk-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bulk-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface, #fff);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
}

.btn:hover:not(:disabled) {
  filter: brightness(0.95);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.ghost {
  border-color: transparent;
  background: transparent;
}

.btn.ghost:hover:not(:disabled) {
  background: var(--color-surface-hover, #e9ecef);
}

.btn-green {
  background: var(--color-risk-green, #22c55e);
  border-color: var(--color-risk-green, #22c55e);
  color: #fff;
}

.btn-yellow {
  background: var(--color-risk-yellow, #eab308);
  border-color: var(--color-risk-yellow, #eab308);
  color: #000;
}

.btn-red {
  background: var(--color-risk-red, #ef4444);
  border-color: var(--color-risk-red, #ef4444);
  color: #fff;
}

.muted {
  color: var(--color-text-muted, #6c757d);
}
</style>
