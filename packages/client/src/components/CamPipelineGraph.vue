<template>
  <div class="p-3 border rounded-lg space-y-2">
    <div class="flex items-center justify-between">
      <h4 class="text-xs font-semibold text-gray-700">Pipeline Graph</h4>
      <span class="text-[10px] text-gray-500">{{ ops.length }} stage(s)</span>
    </div>

    <div class="flex items-center flex-wrap gap-3">
      <template v-for="(op, idx) in ops" :key="idx">
        <div
          class="w-8 h-8 rounded-full flex items-center justify-center text-[9px] font-mono border"
          :class="nodeClass(op)"
          :title="`${op.kind}: ${op.ok ? 'OK' : 'Failed'}`"
        >
          {{ shortLabel(op.kind) }}
        </div>
        <div v-if="idx < ops.length - 1" class="w-6 h-px bg-gray-300 mx-1" />
      </template>
    </div>

    <div class="flex flex-wrap gap-3 text-[10px] text-gray-600">
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
        <span>OK</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-rose-500"></span>
        <span>Failed</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-gray-300 border border-gray-400"></span>
        <span>Pending/Not run</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type PipelineOpKind =
  | 'dxf_preflight'
  | 'adaptive_plan'
  | 'adaptive_plan_run'
  | 'export_post'
  | 'simulate_gcode'

interface PipelineOpResult {
  kind: PipelineOpKind
  ok: boolean
  error?: string | null
  payload?: any
}

const props = defineProps<{
  results: PipelineOpResult[] | null
}>()

const ops = computed(() => props.results ?? [])

function shortLabel(kind: PipelineOpKind): string {
  switch (kind) {
    case 'dxf_preflight':
      return 'PRE'
    case 'adaptive_plan':
      return 'PLAN'
    case 'adaptive_plan_run':
      return 'RUN'
    case 'export_post':
      return 'POST'
    case 'simulate_gcode':
      return 'SIM'
    default:
      return 'OP'
  }
}

function nodeClass(op: PipelineOpResult) {
  if (op.ok && !op.error) {
    return 'bg-emerald-500 text-white border-transparent'
  }
  if (!op.ok || op.error) {
    return 'bg-rose-500 text-white border-transparent'
  }
  return 'bg-gray-100 text-gray-700 border-gray-400'
}
</script>
