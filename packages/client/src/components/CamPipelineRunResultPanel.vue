<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
CamPipelineRunResultPanel - Per-op status chips + JSON payload viewer

Repository: HanzoRazer/luthiers-toolbox
Updated: November 2025
-->

<template>
  <div class="border rounded-lg p-3 bg-white text-[11px] space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-xs font-semibold text-gray-700">
          Pipeline Run Result
        </h3>
        <p class="text-[11px] text-gray-500">
          Per-op status, timings, and payloads
        </p>
      </div>
      <div class="text-right text-[10px] text-gray-500">
        <div v-if="runId">
          Run ID: <span class="font-mono">{{ runId }}</span>
        </div>
        <div v-if="durationMs != null">
          Total: {{ durationMs.toFixed(1) }} ms
        </div>
      </div>
    </div>

    <div
      v-if="!ops || !ops.length"
      class="text-[11px] text-gray-500"
    >
      No pipeline steps in this result.
    </div>

    <div
      v-else
      class="space-y-2"
    >
      <div class="flex flex-wrap gap-2">
        <button
          v-for="(op, idx) in ops"
          :key="idx"
          class="px-2 py-1 rounded-full text-[10px] flex items-center gap-1 border"
          :class="chipClass(op)"
          @click="selectedIndex = idx"
        >
          <span
            class="w-1.5 h-1.5 rounded-full"
            :class="dotClass(op)"
          />
          <span class="font-mono">
            {{ op.kind || 'op' }}{{ op.name ? ':' + op.name : '' }}
          </span>
          <span class="uppercase">
            {{ op.status || 'unknown' }}
          </span>
        </button>
      </div>

      <div
        v-if="currentOp"
        class="border rounded p-2 bg-gray-50 space-y-1"
      >
        <div class="flex items-center justify-between">
          <div class="text-[11px] text-gray-700">
            <span class="font-semibold">
              {{ currentOp.kind || 'op' }}
            </span>
            <span
              v-if="currentOp.name"
              class="text-gray-500"
            >
              · {{ currentOp.name }}
            </span>
          </div>
          <div class="text-[10px] text-gray-500">
            <span v-if="currentOp.duration_ms != null">
              {{ currentOp.duration_ms.toFixed(1) }} ms
            </span>
          </div>
        </div>

        <div class="text-[10px] text-gray-500">
          Status:
          <span class="font-mono">
            {{ currentOp.status || 'unknown' }}
          </span>
          <span
            v-if="currentOp.error"
            class="text-rose-600"
          >
            — {{ currentOp.error }}
          </span>
        </div>

        <details
          v-if="currentOp.summary"
          class="text-[10px] text-gray-500"
        >
          <summary class="cursor-pointer">
            Summary
          </summary>
          <pre class="mt-1 bg-white border rounded p-2 whitespace-pre-wrap">{{ summaryText }}</pre>
        </details>

        <details
          v-if="currentOp.result"
          class="text-[10px] text-gray-500"
        >
          <summary class="cursor-pointer">
            Result payload
          </summary>
          <pre class="mt-1 bg-white border rounded p-2 whitespace-pre-wrap">{{ prettyResult }}</pre>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface PipelineOp {
  name?: string | null
  kind?: string | null
  status?: 'ok' | 'error' | 'warning' | string | null
  duration_ms?: number | null
  error?: string | null
  summary?: any
  result?: any
}

const props = defineProps<{
  runId?: string | null
  durationMs?: number | null
  ops: PipelineOp[]
}>()

const selectedIndex = ref(0)

const currentOp = computed<PipelineOp | null>(() => {
  if (!props.ops || !props.ops.length) return null
  const idx = selectedIndex.value
  if (idx < 0 || idx >= props.ops.length) return props.ops[0]
  return props.ops[idx]
})

const summaryText = computed(() => {
  const op = currentOp.value
  if (!op?.summary) return ''
  if (typeof op.summary === 'string') return op.summary
  try {
    return JSON.stringify(op.summary, null, 2)
  } catch {
    return String(op.summary)
  }
})

const prettyResult = computed(() => {
  const op = currentOp.value
  if (!op?.result) return ''
  try {
    return JSON.stringify(op.result, null, 2)
  } catch {
    return String(op.result)
  }
})

function chipClass (op: PipelineOp) {
  const status = (op.status || '').toLowerCase()
  if (status === 'ok' || status === 'done' || status === 'success') {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  }
  if (status === 'error' || status === 'failed') {
    return 'bg-rose-50 text-rose-700 border-rose-200'
  }
  if (status === 'warning') {
    return 'bg-amber-50 text-amber-700 border-amber-200'
  }
  return 'bg-gray-50 text-gray-700 border-gray-200'
}

function dotClass (op: PipelineOp) {
  const status = (op.status || '').toLowerCase()
  if (status === 'ok' || status === 'done' || status === 'success') {
    return 'bg-emerald-500'
  }
  if (status === 'error' || status === 'failed') {
    return 'bg-rose-500'
  }
  if (status === 'warning') {
    return 'bg-amber-400'
  }
  return 'bg-gray-400'
}
</script>
