<script setup lang="ts">
/**
 * BulkDecisionPanel - Bulk decision controls for manufacturing candidates
 * Extracted from ManufacturingCandidateList.vue
 */
import { computed } from 'vue'

type RiskDecision = 'GREEN' | 'YELLOW' | 'RED'

interface BulkProgress {
  total: number
  done: number
  fail: number
}

interface BulkHistoryRecord {
  id: string
  at_utc: string
  decision: RiskDecision | null
  note: string | null
  selected_count: number
  applied_count: number
  failed_count: number
}

const props = defineProps<{
  selectedCount: number
  bulkDecision: RiskDecision | null
  bulkNote: string
  bulkApplying: boolean
  bulkProgress: BulkProgress | null
  bulkHistory: BulkHistoryRecord[]
  showBulkHistory: boolean
  bulkClearNoteToo: boolean
  canClearDecision: boolean
  clearBlockedReason?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:bulkDecision': [value: RiskDecision | null]
  'update:bulkNote': [value: string]
  'update:showBulkHistory': [value: boolean]
  'update:bulkClearNoteToo': [value: boolean]
  'apply': []
  'undo': []
  'clear': []
}>()

const progressPct = computed(() => {
  if (!props.bulkProgress) return 0
  return Math.round((props.bulkProgress.done / Math.max(1, props.bulkProgress.total)) * 100)
})

const hasSelection = computed(() => props.selectedCount > 0)
const hasHistory = computed(() => props.bulkHistory.length > 0)
</script>

<template>
  <div class="bulk-decision-panel border rounded p-3 bg-gray-50 space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-sm">
        Bulk Decision
        <span
          v-if="selectedCount > 0"
          class="text-xs text-gray-500"
        >
          ({{ selectedCount }} selected)
        </span>
      </h3>
      <button
        v-if="hasHistory"
        class="text-xs px-2 py-1 border rounded hover:bg-white"
        :class="{ 'bg-blue-50': showBulkHistory }"
        @click="emit('update:showBulkHistory', !showBulkHistory)"
      >
        {{ showBulkHistory ? 'Hide' : 'Show' }} History ({{ bulkHistory.length }})
      </button>
    </div>

    <!-- Decision selector + note -->
    <div class="flex items-center gap-2 flex-wrap">
      <select
        :value="bulkDecision ?? ''"
        :disabled="!hasSelection || bulkApplying || disabled"
        class="border px-2 py-1 rounded text-sm"
        @change="emit('update:bulkDecision', ($event.target as HTMLSelectElement).value as RiskDecision || null)"
      >
        <option value="">Choose decision…</option>
        <option value="GREEN">GREEN</option>
        <option value="YELLOW">YELLOW</option>
        <option value="RED">RED</option>
      </select>

      <input
        :value="bulkNote"
        type="text"
        placeholder="Optional note…"
        :disabled="!hasSelection || bulkApplying || disabled"
        class="border px-2 py-1 rounded text-sm flex-1 min-w-[150px]"
        @input="emit('update:bulkNote', ($event.target as HTMLInputElement).value)"
      >

      <button
        class="px-3 py-1 rounded text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
        :disabled="!hasSelection || !bulkDecision || bulkApplying || disabled"
        @click="emit('apply')"
      >
        Apply
      </button>

      <button
        v-if="hasHistory"
        class="px-3 py-1 rounded text-sm border border-orange-500 text-orange-600 hover:bg-orange-50 disabled:opacity-50"
        :disabled="bulkApplying || disabled"
        @click="emit('undo')"
      >
        Undo
      </button>
    </div>

    <!-- Clear decision row -->
    <div class="flex items-center gap-2 text-sm">
      <button
        class="px-2 py-1 rounded border border-gray-400 text-gray-600 hover:bg-gray-100 disabled:opacity-50"
        :disabled="!canClearDecision || bulkApplying || disabled"
        :title="clearBlockedReason || 'Clear decision for selected candidates'"
        @click="emit('clear')"
      >
        Clear Decision
      </button>
      <label class="flex items-center gap-1 text-xs text-gray-500">
        <input
          :checked="bulkClearNoteToo"
          type="checkbox"
          :disabled="!canClearDecision || bulkApplying || disabled"
          @change="emit('update:bulkClearNoteToo', ($event.target as HTMLInputElement).checked)"
        >
        Clear note too
      </label>
    </div>

    <!-- Progress bar -->
    <div
      v-if="bulkProgress"
      class="space-y-1"
    >
      <div class="h-2 bg-gray-200 rounded overflow-hidden">
        <div
          class="h-full transition-all duration-200"
          :class="bulkProgress.fail > 0 ? 'bg-orange-500' : 'bg-blue-500'"
          :style="{ width: progressPct + '%' }"
        />
      </div>
      <div class="text-xs text-gray-500">
        {{ bulkProgress.done }}/{{ bulkProgress.total }}
        <span v-if="bulkProgress.fail > 0" class="text-orange-600">
          ({{ bulkProgress.fail }} failed)
        </span>
      </div>
    </div>

    <!-- History panel -->
    <div
      v-if="showBulkHistory && bulkHistory.length > 0"
      class="border rounded p-2 bg-white max-h-48 overflow-auto text-xs space-y-1"
    >
      <div
        v-for="h in bulkHistory"
        :key="h.id"
        class="flex items-center gap-2 py-1 border-b border-gray-100 last:border-b-0"
      >
        <span
          class="px-1.5 py-0.5 rounded text-white text-xs font-medium"
          :class="{
            'bg-green-600': h.decision === 'GREEN',
            'bg-yellow-500': h.decision === 'YELLOW',
            'bg-red-600': h.decision === 'RED',
            'bg-gray-400': !h.decision,
          }"
        >
          {{ h.decision || 'CLEAR' }}
        </span>
        <span class="text-gray-600">
          {{ h.applied_count }}/{{ h.selected_count }}
        </span>
        <span
          v-if="h.failed_count > 0"
          class="text-orange-600"
        >
          ({{ h.failed_count }} failed)
        </span>
        <span class="text-gray-400 ml-auto">
          {{ h.at_utc.slice(11, 19) }}
        </span>
      </div>
    </div>
  </div>
</template>
