<script setup lang="ts">
/**
 * CandidateFiltersSection.vue - SIMPLIFIED
 * 
 * Collapsed by default. Shows compact summary + toggle for advanced.
 */
import { ref } from 'vue'
import type { DecisionFilter, StatusFilter, SortKey } from './composables/useCandidateFilters'

export interface CandidateSummary {
  total: number
  decisionCounts: Record<string, number>
  statusCounts: Record<string, number>
}

const props = defineProps<{
  decisionFilter: DecisionFilter
  statusFilter: StatusFilter
  filterDecidedBy: string
  searchText: string
  sortKey: SortKey
  myOperatorId: string
  stampDecisionsWithOperator: boolean
  filterOnlyMine: boolean
  showSelectedOnly: boolean
  compact: boolean
  decidedByOptions: string[]
  summary: CandidateSummary
  effectiveOperatorId: string
  filteredCount: number
  selectedCount: number
  totalCount: number
  allFilteredSelected: boolean
  disabled: boolean
}>()

const emit = defineEmits<{
  'update:decisionFilter': [value: DecisionFilter]
  'update:statusFilter': [value: StatusFilter]
  'update:filterDecidedBy': [value: string]
  'update:searchText': [value: string]
  'update:sortKey': [value: SortKey]
  'update:myOperatorId': [value: string]
  'update:stampDecisionsWithOperator': [value: boolean]
  'update:filterOnlyMine': [value: boolean]
  'update:showSelectedOnly': [value: boolean]
  'update:compact': [value: boolean]
  selectAllFiltered: []
  clearAllFiltered: []
  invertSelectionFiltered: []
  quickUndecided: []
  clearFilters: []
  resetViewPrefs: []
  toggleAllFiltered: []
  cycleAuditSort: []
}>()

const showAdvanced = ref(false)

function setDecisionFilter(v: DecisionFilter) {
  emit('update:decisionFilter', v)
}

function chipClass(active: boolean, variant: 'neutral' | 'good' | 'warn' | 'bad') {
  return ['chip', active ? 'active' : '', variant]
}
</script>

<template>
  <div class="filters-simple">
    <!-- Compact summary row -->
    <div class="summary-row">
      <span class="stat">
        <strong>{{ summary.total }}</strong> total
      </span>
      <button
        type="button"
        :class="chipClass(decisionFilter === 'GREEN', 'good')"
        @click="setDecisionFilter(decisionFilter === 'GREEN' ? 'ALL' : 'GREEN')"
      >
        GREEN {{ summary.decisionCounts.GREEN || 0 }}
      </button>
      <button
        type="button"
        :class="chipClass(decisionFilter === 'YELLOW', 'warn')"
        @click="setDecisionFilter(decisionFilter === 'YELLOW' ? 'ALL' : 'YELLOW')"
      >
        YELLOW {{ summary.decisionCounts.YELLOW || 0 }}
      </button>
      <button
        type="button"
        :class="chipClass(decisionFilter === 'RED', 'bad')"
        @click="setDecisionFilter(decisionFilter === 'RED' ? 'ALL' : 'RED')"
      >
        RED {{ summary.decisionCounts.RED || 0 }}
      </button>
      <button
        type="button"
        :class="chipClass(decisionFilter === 'UNDECIDED', 'neutral')"
        @click="setDecisionFilter(decisionFilter === 'UNDECIDED' ? 'ALL' : 'UNDECIDED')"
      >
        Undecided {{ summary.decisionCounts.NEEDS_DECISION || 0 }}
      </button>
      
      <button
        type="button"
        class="toggle-advanced"
        @click="showAdvanced = !showAdvanced"
      >
        {{ showAdvanced ? '▼ Hide filters' : '▶ More filters' }}
      </button>
    </div>

    <!-- Advanced filters (hidden by default) -->
    <div v-if="showAdvanced" class="advanced-filters">
      <div class="filter-row">
        <input
          :value="searchText"
          type="text"
          placeholder="Search..."
          class="search-input"
          @input="emit('update:searchText', ($event.target as HTMLInputElement).value)"
        />
        
        <select
          :value="sortKey"
          class="sort-select"
          @change="emit('update:sortKey', ($event.target as HTMLSelectElement).value as SortKey)"
        >
          <option value="id">Sort: ID ↑</option>
          <option value="id_desc">Sort: ID ↓</option>
          <option value="created_desc">Sort: Newest</option>
          <option value="created">Sort: Oldest</option>
        </select>

        <button
          type="button"
          class="btn-small"
          :disabled="disabled"
          @click="emit('selectAllFiltered')"
        >
          Select all
        </button>
        <button
          type="button"
          class="btn-small"
          :disabled="disabled"
          @click="emit('clearAllFiltered')"
        >
          Clear
        </button>
        <button
          type="button"
          class="btn-small"
          :disabled="disabled"
          @click="emit('clearFilters')"
        >
          Reset
        </button>
      </div>
      
      <div class="filter-row muted-row">
        <span>Showing {{ filteredCount }} / {{ totalCount }}</span>
        <span v-if="selectedCount > 0">• {{ selectedCount }} selected</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filters-simple {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
  margin-bottom: 8px;
}

.summary-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.stat {
  font-size: 0.9rem;
  color: #666;
}

.chip {
  padding: 4px 10px;
  border: 1px solid #ccc;
  border-radius: 16px;
  background: #f5f5f5;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
}

.chip:hover { background: #e8e8e8; }
.chip.active { border-width: 2px; }
.chip.good { border-color: #28a745; color: #28a745; }
.chip.good.active { background: #d4edda; }
.chip.warn { border-color: #ffc107; color: #856404; }
.chip.warn.active { background: #fff3cd; }
.chip.bad { border-color: #dc3545; color: #dc3545; }
.chip.bad.active { background: #f8d7da; }
.chip.neutral { border-color: #6c757d; color: #6c757d; }
.chip.neutral.active { background: #e2e3e5; }

.toggle-advanced {
  margin-left: auto;
  padding: 4px 8px;
  border: none;
  background: none;
  color: #0066cc;
  cursor: pointer;
  font-size: 0.8rem;
}

.toggle-advanced:hover {
  text-decoration: underline;
}

.advanced-filters {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: #f9f9f9;
  border-radius: 8px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.search-input {
  padding: 6px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  width: 180px;
}

.sort-select {
  padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 6px;
}

.btn-small {
  padding: 4px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 0.8rem;
}

.btn-small:hover:not(:disabled) {
  background: #f0f0f0;
}

.btn-small:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.muted-row {
  font-size: 0.8rem;
  color: #888;
}
</style>
