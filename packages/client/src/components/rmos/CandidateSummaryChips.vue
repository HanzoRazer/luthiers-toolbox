<script setup lang="ts">
/**
 * CandidateSummaryChips - Summary counts with clickable filter chips
 * Extracted from ManufacturingCandidateList.vue
 */

interface DecisionCounts {
  NEEDS_DECISION: number
  GREEN: number
  YELLOW: number
  RED: number
  OTHER: number
}

interface StatusCounts {
  PROPOSED: number
  ACCEPTED: number
  REJECTED: number
  OTHER: number
}

const props = defineProps<{
  decisionCounts: DecisionCounts
  statusCounts: StatusCounts
  total: number
  activeDecisionFilter: string
  activeStatusFilter: string
}>()

const emit = defineEmits<{
  'setDecisionFilter': [value: string]
  'setStatusFilter': [value: string]
}>()

function chipClass(active: boolean, kind: 'neutral' | 'good' | 'warn' | 'bad' | 'muted' = 'neutral') {
  return {
    'chip': true,
    'active': active,
    'chip-neutral': kind === 'neutral',
    'chip-good': kind === 'good',
    'chip-warn': kind === 'warn',
    'chip-bad': kind === 'bad',
    'chip-muted': kind === 'muted',
  }
}
</script>

<template>
  <div class="summary-chips space-y-2">
    <!-- Decision chips -->
    <div class="flex flex-wrap gap-1 text-xs">
      <span class="text-gray-500 mr-1">Decision:</span>
      <button
        :class="chipClass(activeDecisionFilter === 'all', 'neutral')"
        @click="emit('setDecisionFilter', 'all')"
      >
        All ({{ total }})
      </button>
      <button
        :class="chipClass(activeDecisionFilter === 'undecided', 'muted')"
        @click="emit('setDecisionFilter', 'undecided')"
      >
        Needs Decision ({{ decisionCounts.NEEDS_DECISION }})
      </button>
      <button
        :class="chipClass(activeDecisionFilter === 'green', 'good')"
        @click="emit('setDecisionFilter', 'green')"
      >
        GREEN ({{ decisionCounts.GREEN }})
      </button>
      <button
        :class="chipClass(activeDecisionFilter === 'yellow', 'warn')"
        @click="emit('setDecisionFilter', 'yellow')"
      >
        YELLOW ({{ decisionCounts.YELLOW }})
      </button>
      <button
        :class="chipClass(activeDecisionFilter === 'red', 'bad')"
        @click="emit('setDecisionFilter', 'red')"
      >
        RED ({{ decisionCounts.RED }})
      </button>
    </div>

    <!-- Status chips -->
    <div class="flex flex-wrap gap-1 text-xs">
      <span class="text-gray-500 mr-1">Status:</span>
      <button
        :class="chipClass(activeStatusFilter === 'all', 'neutral')"
        @click="emit('setStatusFilter', 'all')"
      >
        All
      </button>
      <button
        :class="chipClass(activeStatusFilter === 'proposed', 'muted')"
        @click="emit('setStatusFilter', 'proposed')"
      >
        Proposed ({{ statusCounts.PROPOSED }})
      </button>
      <button
        :class="chipClass(activeStatusFilter === 'accepted', 'good')"
        @click="emit('setStatusFilter', 'accepted')"
      >
        Accepted ({{ statusCounts.ACCEPTED }})
      </button>
      <button
        :class="chipClass(activeStatusFilter === 'rejected', 'bad')"
        @click="emit('setStatusFilter', 'rejected')"
      >
        Rejected ({{ statusCounts.REJECTED }})
      </button>
    </div>
  </div>
</template>

<style scoped>
.chip {
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  border: 1px solid #d1d5db;
  background: white;
  cursor: pointer;
  transition: all 0.15s;
}

.chip:hover {
  background: #f3f4f6;
}

.chip.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.chip-neutral.active {
  border-color: #6b7280;
  background: #f3f4f6;
}

.chip-good {
  border-color: #86efac;
}
.chip-good.active {
  background: #dcfce7;
  border-color: #22c55e;
}

.chip-warn {
  border-color: #fde047;
}
.chip-warn.active {
  background: #fef9c3;
  border-color: #eab308;
}

.chip-bad {
  border-color: #fca5a5;
}
.chip-bad.active {
  background: #fee2e2;
  border-color: #ef4444;
}

.chip-muted {
  border-color: #d1d5db;
  color: #6b7280;
}
.chip-muted.active {
  background: #f3f4f6;
  border-color: #9ca3af;
}
</style>
