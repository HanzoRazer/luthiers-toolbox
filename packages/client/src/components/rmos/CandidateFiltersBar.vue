<script setup lang="ts">
/**
 * CandidateFiltersBar - Filter controls for candidate list
 * Extracted from ManufacturingCandidateList.vue
 */
import type { DecisionFilter, StatusFilter } from './composables/useCandidateFilters'

defineProps<{
  decisionFilter: DecisionFilter
  statusFilter: StatusFilter
  searchText: string
  filterDecidedBy: string
  filterOnlyMine: boolean
  decidedByOptions: string[]
  myOperatorId: string
  compact: boolean
  filteredCount: number
  totalCount: number
  selectedCount: number
  disabled: boolean
}>()

const emit = defineEmits<{
  'update:decisionFilter': [value: DecisionFilter]
  'update:statusFilter': [value: StatusFilter]
  'update:searchText': [value: string]
  'update:filterDecidedBy': [value: string]
  'update:filterOnlyMine': [value: boolean]
  'update:compact': [value: boolean]
  selectAllFiltered: []
  clearAllFiltered: []
  invertSelection: []
  clearFilters: []
  quickUndecided: []
  resetView: []
}>()

function hotkeyHelp(): string {
  return [
    'Hotkeys:',
    'g/y/r = Bulk decision GREEN/YELLOW/RED',
    'u = Clear decision (NEEDS_DECISION)',
    'b = Bulk clear decision (selected)',
    'e = Export GREEN-only (all must be decided)',
    'a = Select shown (post-filter)',
    'c = Clear shown (post-filter)',
    'i = Invert selection (shown rows)',
    'x = Clear all selection',
    'h = Toggle bulk history panel',
    'esc = Clear selection',
  ].join('\n')
}
</script>

<template>
  <div class="filters">
    <div class="filters-left">
      <select
        :value="decisionFilter"
        :disabled="disabled"
        @change="emit('update:decisionFilter', ($event.target as HTMLSelectElement).value as DecisionFilter)"
      >
        <option value="ALL">All decisions</option>
        <option value="UNDECIDED">Undecided</option>
        <option value="GREEN">GREEN</option>
        <option value="YELLOW">YELLOW</option>
        <option value="RED">RED</option>
      </select>

      <select
        :value="statusFilter"
        :disabled="disabled"
        @change="emit('update:statusFilter', ($event.target as HTMLSelectElement).value as StatusFilter)"
      >
        <option value="ALL">All statuses</option>
        <option value="PROPOSED">Proposed</option>
        <option value="ACCEPTED">Accepted</option>
        <option value="REJECTED">Rejected</option>
      </select>

      <input
        :value="searchText"
        type="text"
        placeholder="Search..."
        :disabled="disabled"
        @input="emit('update:searchText', ($event.target as HTMLInputElement).value)"
      >

      <select
        v-if="decidedByOptions.length > 0"
        :value="filterDecidedBy"
        :disabled="disabled"
        @change="emit('update:filterDecidedBy', ($event.target as HTMLSelectElement).value)"
      >
        <option value="ALL">All operators</option>
        <option
          v-for="op in decidedByOptions"
          :key="op"
          :value="op"
        >
          {{ op }}
        </option>
      </select>

      <div class="check-group">
        <label class="check">
          <input
            :checked="filterOnlyMine"
            type="checkbox"
            :disabled="!myOperatorId.trim() || disabled"
            @change="emit('update:filterOnlyMine', ($event.target as HTMLInputElement).checked)"
          >
          my decisions
        </label>
      </div>
    </div>

    <div class="filters-right">
      <button
        class="btn ghost"
        :disabled="disabled || filteredCount === 0"
        title="Select all shown rows"
        @click="emit('selectAllFiltered')"
      >
        Select shown
      </button>
      <button
        class="btn ghost"
        :disabled="disabled || filteredCount === 0"
        title="Clear selection for shown rows"
        @click="emit('clearAllFiltered')"
      >
        Clear shown
      </button>
      <button
        class="btn ghost"
        :disabled="disabled || filteredCount === 0"
        title="Invert selection (shown rows)"
        @click="emit('invertSelection')"
      >
        Invert
      </button>

      <label class="check">
        <input
          type="checkbox"
          :disabled="disabled || selectedCount === 0"
        >
        <span class="muted">Selected only</span>
      </label>

      <button
        class="btn ghost"
        :disabled="disabled"
        title="Jump to undecided candidates"
        @click="emit('quickUndecided')"
      >
        Undecided-only
      </button>
      <button
        class="btn ghost"
        :disabled="disabled"
        title="Clear all filters"
        @click="emit('clearFilters')"
      >
        Clear filters
      </button>

      <div class="muted small">
        Showing <strong>{{ filteredCount }}</strong> / {{ totalCount }}
      </div>

      <label
        class="check"
        :title="compact ? 'Compact rows (more visible)' : 'Comfortable rows (more spacing)'"
      >
        <input
          :checked="compact"
          type="checkbox"
          @change="emit('update:compact', ($event.target as HTMLInputElement).checked)"
        >
        <span class="muted">{{ compact ? 'Compact' : 'Comfortable' }}</span>
      </label>

      <div
        class="small muted"
        style="margin-top: 4px"
      >
        <span
          class="kbdhint"
          :title="hotkeyHelp()"
        >
          Hotkeys: g/y/r · u · b · e · a · c · i · x · h · esc
        </span>
      </div>

      <div style="margin-top: 8px">
        <button
          class="btn small"
          title="Reset filters, density, and sort (persisted)"
          @click="emit('resetView')"
        >
          Reset view
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--color-surface-elevated, #f8f9fa);
  border-radius: var(--radius-md, 6px);
  margin-bottom: 0.5rem;
}

.filters-left,
.filters-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.filters-left {
  flex: 1;
}

.filters-right {
  justify-content: flex-end;
}

.check-group {
  display: flex;
  gap: 0.75rem;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
}

.check input[type="checkbox"] {
  margin: 0;
}

.btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface, #fff);
  cursor: pointer;
  font-size: 0.875rem;
}

.btn:hover:not(:disabled) {
  background: var(--color-surface-hover, #e9ecef);
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

.btn.small {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.muted {
  color: var(--color-text-muted, #6c757d);
}

.small {
  font-size: 0.75rem;
}

.kbdhint {
  cursor: help;
  border-bottom: 1px dotted var(--color-text-muted, #6c757d);
}

select,
input[type="text"] {
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: var(--radius-sm, 4px);
  font-size: 0.875rem;
}
</style>
