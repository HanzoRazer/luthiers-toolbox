<script setup lang="ts">
/**
 * Filters section for ManufacturingCandidateList.
 * Extracted to reduce parent god file size.
 */
import type { DecisionFilter, StatusFilter, SortKey } from './composables/useCandidateFilters'

export interface CandidateSummary {
  total: number
  decisionCounts: Record<string, number>
  statusCounts: Record<string, number>
}

const props = defineProps<{
  // Filter state (v-model)
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
  // Read-only data
  decidedByOptions: string[]
  summary: CandidateSummary
  effectiveOperatorId: string
  filteredCount: number
  selectedCount: number
  totalCount: number
  allFilteredSelected: boolean
  // Disabled state
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

function setDecisionFilter(v: DecisionFilter) {
  emit('update:decisionFilter', v)
}
function setStatusFilter(v: StatusFilter) {
  emit('update:statusFilter', v)
}

function chipClass(active: boolean, variant: 'neutral' | 'muted' | 'good' | 'warn' | 'bad') {
  return ['chip', active ? 'active' : '', variant]
}

function _hotkeyHelp() {
  return [
    'g = Bulk GREEN (selected)',
    'y = Bulk YELLOW (selected)',
    'r = Bulk RED (selected)',
    'u = Bulk NEEDS_DECISION (selected)',
    'b = Bulk clear decision (selected)',
    'e = Edit note (first selected)',
    'a = Select all shown',
    'c = Clear selection',
    'i = Invert selection (shown)',
    'x = Export GREEN zips',
    'h = Toggle bulk history panel',
    'esc = Cancel edit / close history',
  ].join('\n')
}
</script>

<template>
  <div class="filters">
    <div class="filters-left">
      <!-- Quick chips -->
      <div
        v-if="summary.total > 0"
        class="chipsRow"
      >
        <div class="chipsGroup">
          <div class="small muted">Decision:</div>
          <button
            type="button"
            :class="chipClass(decisionFilter === 'ALL', 'neutral')"
            title="Show all decisions"
            @click="setDecisionFilter('ALL')"
          >
            All <span class="count">{{ summary.total }}</span>
          </button>
          <button
            type="button"
            :class="chipClass(decisionFilter === 'UNDECIDED', 'muted')"
            title="Show candidates that still need an explicit decision"
            @click="setDecisionFilter('UNDECIDED')"
          >
            Needs decision <span class="count">{{ summary.decisionCounts.NEEDS_DECISION }}</span>
          </button>
          <button
            type="button"
            :class="chipClass(decisionFilter === 'GREEN', 'good')"
            title="Show GREEN-only"
            @click="setDecisionFilter('GREEN')"
          >
            GREEN <span class="count">{{ summary.decisionCounts.GREEN }}</span>
          </button>
          <button
            type="button"
            :class="chipClass(decisionFilter === 'YELLOW', 'warn')"
            title="Show YELLOW-only"
            @click="setDecisionFilter('YELLOW')"
          >
            YELLOW <span class="count">{{ summary.decisionCounts.YELLOW }}</span>
          </button>
          <button
            type="button"
            :class="chipClass(decisionFilter === 'RED', 'bad')"
            title="Show RED-only"
            @click="setDecisionFilter('RED')"
          >
            RED <span class="count">{{ summary.decisionCounts.RED }}</span>
          </button>
        </div>

        <div class="chipsGroup">
          <div class="small muted">Status:</div>
          <button
            type="button"
            :class="chipClass(statusFilter === 'ALL', 'neutral')"
            title="Show all statuses"
            @click="setStatusFilter('ALL')"
          >
            All <span class="count">{{ summary.total }}</span>
          </button>
          <button
            type="button"
            :class="chipClass(statusFilter === 'PROPOSED', 'muted')"
            title="Show PROPOSED-only"
            @click="setStatusFilter('PROPOSED')"
          >
            PROPOSED <span class="count">{{ summary.statusCounts.PROPOSED }}</span>
          </button>
          <button
            type="button"
            :class="chipClass(statusFilter === 'ACCEPTED', 'good')"
            title="Show ACCEPTED-only"
            @click="setStatusFilter('ACCEPTED')"
          >
            ACCEPTED <span class="count">{{ summary.statusCounts.ACCEPTED }}</span>
          </button>
          <button
            type="button"
            :class="chipClass(statusFilter === 'REJECTED', 'bad')"
            title="Show REJECTED-only"
            @click="setStatusFilter('REJECTED')"
          >
            REJECTED <span class="count">{{ summary.statusCounts.REJECTED }}</span>
          </button>
        </div>
      </div>

      <div class="field">
        <label class="muted">Decision</label>
        <select
          :value="decisionFilter"
          :disabled="disabled"
          @change="emit('update:decisionFilter', ($event.target as HTMLSelectElement).value as DecisionFilter)"
        >
          <option value="ALL">All</option>
          <option value="UNDECIDED">Undecided</option>
          <option value="GREEN">GREEN</option>
          <option value="YELLOW">YELLOW</option>
          <option value="RED">RED</option>
        </select>
      </div>

      <div class="field">
        <label class="muted">Status</label>
        <select
          :value="statusFilter"
          :disabled="disabled"
          @change="emit('update:statusFilter', ($event.target as HTMLSelectElement).value as StatusFilter)"
        >
          <option value="ALL">All</option>
          <option value="PROPOSED">PROPOSED</option>
          <option value="ACCEPTED">ACCEPTED</option>
          <option value="REJECTED">REJECTED</option>
        </select>
      </div>

      <div class="field">
        <label class="muted">Decided by</label>
        <select
          :value="filterDecidedBy"
          :disabled="disabled"
          title="Filter by operator identity"
          @change="emit('update:filterDecidedBy', ($event.target as HTMLSelectElement).value)"
        >
          <option value="ALL">All</option>
          <option
            v-for="op in decidedByOptions"
            :key="op"
            :value="op"
          >
            {{ op }}
          </option>
        </select>
      </div>

      <div class="field grow">
        <label class="muted">Search</label>
        <input
          :value="searchText"
          type="text"
          placeholder="candidate id, advisory id, note, decided_by..."
          :disabled="disabled"
          @input="emit('update:searchText', ($event.target as HTMLInputElement).value)"
        >
      </div>

      <div class="field">
        <label class="muted">Sort</label>
        <select
          :value="sortKey"
          :disabled="disabled"
          @change="emit('update:sortKey', ($event.target as HTMLSelectElement).value as SortKey)"
        >
          <option value="id">ID (up)</option>
          <option value="id_desc">ID (down)</option>
          <option value="created">Created (up)</option>
          <option value="created_desc">Created (down)</option>
          <option value="decided_at">Decided at (up)</option>
          <option value="decided_at_desc">Decided at (down)</option>
          <option value="decided_by">Decided by (A-Z)</option>
          <option value="status">Status</option>
          <option value="decision">Decision</option>
        </select>
      </div>

      <div class="field">
        <label class="muted">My operator id</label>
        <input
          :value="myOperatorId"
          type="text"
          placeholder="e.g., operator_jane"
          title="Stored locally in this browser. Used by 'Only mine' filter."
          :disabled="disabled"
          @input="emit('update:myOperatorId', ($event.target as HTMLInputElement).value)"
        >
      </div>

      <div class="field">
        <label class="muted">Stamp</label>
        <label
          class="inlineCheck"
          :title="stampDecisionsWithOperator
            ? (effectiveOperatorId
              ? `Will send decided_by=${effectiveOperatorId} on decisions`
              : 'Enable stamping, then set an operator id to actually stamp')
            : 'Decisions will not send decided_by (backend may still set it elsewhere)'"
        >
          <input
            :checked="stampDecisionsWithOperator"
            type="checkbox"
            :disabled="disabled"
            @change="emit('update:stampDecisionsWithOperator', ($event.target as HTMLInputElement).checked)"
          >
          decided_by on save
        </label>
      </div>

      <div class="field">
        <label class="muted">Only mine</label>
        <label
          class="inlineCheck"
          title="Show only candidates decided by your operator id"
        >
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
        @click="emit('invertSelectionFiltered')"
      >
        Invert
      </button>

      <label class="check">
        <input
          :checked="showSelectedOnly"
          type="checkbox"
          :disabled="disabled || selectedCount === 0"
          @change="emit('update:showSelectedOnly', ($event.target as HTMLInputElement).checked)"
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
        style="margin-top:4px;"
      >
        <span
          class="kbdhint"
          :title="_hotkeyHelp()"
        >
          Hotkeys: g/y/r - u - b - e - a - c - i - x - h - esc
        </span>
      </div>
      <div style="margin-top:8px;">
        <button
          class="btn small"
          title="Reset filters, density, and sort (persisted)"
          @click="emit('resetViewPrefs')"
        >
          Reset view
        </button>
      </div>
    </div>
  </div>

  <!-- Table header row -->
  <div class="row head">
    <div class="sel">
      <input
        type="checkbox"
        :checked="allFilteredSelected"
        :disabled="disabled || filteredCount === 0"
        title="Toggle select all shown"
        @change="emit('toggleAllFiltered')"
      >
    </div>
    <div>Candidate</div>
    <div>Advisory</div>
    <div>Decision</div>
    <div
      class="audit auditHeader"
      role="button"
      tabindex="0"
      title="Sort by audit fields"
      @click="emit('cycleAuditSort')"
      @keydown.enter="emit('cycleAuditSort')"
      @keydown.space.prevent="emit('cycleAuditSort')"
    >
      Audit
      <span
        v-if="sortKey.startsWith('decided_')"
        class="sortHint"
      >{{ sortKey.endsWith('_desc') ? '\u2193' : '\u2191' }}</span>
    </div>
    <div>History</div>
    <div>Status</div>
    <div class="note">Decision Note</div>
    <div class="copyCol">Copy</div>
    <div class="actions">Actions</div>
  </div>
</template>
