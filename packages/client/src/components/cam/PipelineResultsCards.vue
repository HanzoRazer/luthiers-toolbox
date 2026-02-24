<script setup lang="ts">
/**
 * PipelineResultsCards - Per-operation result cards display
 * Extracted from CamPipelineRunner.vue
 */
import type { PipelineOpResult } from './composables/camPipelineTypes'

defineProps<{
  results: PipelineOpResult[]
  openPayloadIndex: number | null
}>()

const emit = defineEmits<{
  'toggle-payload': [index: number]
}>()

function formatPayload(payload: any): string {
  try {
    const str = JSON.stringify(payload, null, 2)
    const lines = str.split('\n')
    if (lines.length > 48) {
      return lines.slice(0, 48).join('\n') + '\n... (truncated)'
    }
    return str
  } catch {
    return '[Unable to display payload]'
  }
}
</script>

<template>
  <div class="space-y-1">
    <div
      v-for="(op, idx) in results"
      :key="idx"
      class="flex items-start justify-between px-3 py-2 rounded-lg border text-xs bg-gray-50"
    >
      <div class="flex flex-col space-y-1">
        <div class="flex items-center space-x-2">
          <span
            class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
            :class="op.ok && !op.error ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'"
          >
            {{ op.ok && !op.error ? 'OK' : 'FAIL' }}
          </span>
          <span class="font-mono text-[11px] uppercase">
            {{ op.kind }}
          </span>
        </div>

        <p
          v-if="op.error"
          class="text-[11px] text-rose-700"
        >
          {{ op.error }}
        </p>

        <button
          v-if="op.payload"
          class="text-[10px] underline text-gray-600 text-left"
          @click="emit('toggle-payload', idx)"
        >
          {{ openPayloadIndex === idx ? 'Hide payload' : 'Show payload JSON' }}
        </button>
      </div>

      <pre
        v-if="openPayloadIndex === idx && op.payload"
        class="ml-4 max-h-48 overflow-auto bg-white rounded-md p-2 text-[10px] whitespace-pre-wrap w-full md:w-1/2"
      >{{ formatPayload(op.payload) }}</pre>
    </div>
  </div>
</template>
