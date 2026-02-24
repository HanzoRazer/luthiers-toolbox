<template>
  <div class="border rounded-lg p-3 bg-white space-y-2">
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold text-gray-700">
        Adaptive Parameters
      </h3>
      <button
        class="px-2 py-1 rounded bg-gray-900 text-white text-[11px] disabled:opacity-50"
        :disabled="running"
        @click="$emit('run')"
      >
        <span v-if="!running">Run Adaptive Kernel</span>
        <span v-else>Running…</span>
      </button>
    </div>

    <div class="grid grid-cols-2 gap-2 text-[11px]">
      <label class="flex flex-col gap-1">
        <span>Tool ⌀</span>
        <input
          :value="params.toolD"
          type="number"
          step="0.1"
          min="0.1"
          class="border rounded px-2 py-1"
          @input="emitParam('toolD', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="flex flex-col gap-1">
        <span>Stepover (fraction)</span>
        <input
          :value="params.stepover"
          type="number"
          step="0.01"
          min="0.05"
          max="0.9"
          class="border rounded px-2 py-1"
          @input="emitParam('stepover', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="flex flex-col gap-1">
        <span>Stepdown</span>
        <input
          :value="params.stepdown"
          type="number"
          step="0.1"
          class="border rounded px-2 py-1"
          @input="emitParam('stepdown', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="flex flex-col gap-1">
        <span>Margin</span>
        <input
          :value="params.margin"
          type="number"
          step="0.1"
          class="border rounded px-2 py-1"
          @input="emitParam('margin', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="flex flex-col gap-1">
        <span>Strategy</span>
        <select
          :value="params.strategy"
          class="border rounded px-2 py-1"
          @change="emitParam('strategy', ($event.target as HTMLSelectElement).value)"
        >
          <option value="Spiral">Spiral</option>
          <option value="Lanes">Lanes</option>
        </select>
      </label>

      <label class="flex flex-col gap-1">
        <span>Feed XY</span>
        <input
          :value="params.feedXY"
          type="number"
          step="10"
          class="border rounded px-2 py-1"
          @input="emitParam('feedXY', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="flex flex-col gap-1">
        <span>Safe Z</span>
        <input
          :value="params.safeZ"
          type="number"
          step="0.1"
          class="border rounded px-2 py-1"
          @input="emitParam('safeZ', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="flex flex-col gap-1">
        <span>Rough Z</span>
        <input
          :value="params.zRough"
          type="number"
          step="0.1"
          class="border rounded px-2 py-1"
          @input="emitParam('zRough', Number(($event.target as HTMLInputElement).value))"
        >
      </label>
    </div>

    <p
      v-if="error"
      class="text-[11px] text-red-600"
    >
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
export interface AdaptiveParams {
  toolD: number
  stepover: number
  stepdown: number
  margin: number
  strategy: 'Spiral' | 'Lanes'
  feedXY: number
  safeZ: number
  zRough: number
}

const props = defineProps<{
  params: AdaptiveParams
  running: boolean
  error: string | null
}>()

const emit = defineEmits<{
  'update:params': [params: AdaptiveParams]
  run: []
}>()

function emitParam(key: keyof AdaptiveParams, value: number | string) {
  emit('update:params', { ...props.params, [key]: value })
}
</script>
