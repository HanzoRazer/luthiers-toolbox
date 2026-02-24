<template>
  <div class="flex flex-wrap items-center gap-3 mb-4 pb-3 border-b text-[11px]">
    <!-- Pipeline filter -->
    <label class="flex items-center gap-2">
      <span class="text-gray-700">Pipeline:</span>
      <select
        :value="pipelineFilter"
        class="px-2 py-1 border rounded text-[11px] bg-white"
        @change="$emit('update:pipelineFilter', ($event.target as HTMLSelectElement).value)"
      >
        <option value="Any">Any</option>
        <option value="artstudio_relief_v16">Art Studio Relief</option>
        <option value="relief_kernel_lab">Relief Kernel Lab</option>
      </select>
    </label>

    <!-- Date range -->
    <label class="flex items-center gap-2">
      <span class="text-gray-700">From:</span>
      <input
        :value="fromDate"
        type="date"
        class="px-2 py-1 border rounded text-[11px] bg-white"
        @input="$emit('update:fromDate', ($event.target as HTMLInputElement).value)"
      >
    </label>
    <label class="flex items-center gap-2">
      <span class="text-gray-700">To:</span>
      <input
        :value="toDate"
        type="date"
        class="px-2 py-1 border rounded text-[11px] bg-white"
        @input="$emit('update:toDate', ($event.target as HTMLInputElement).value)"
      >
    </label>

    <!-- Preset A -->
    <label class="flex items-center gap-2">
      <span class="text-gray-700">Preset A:</span>
      <select
        :value="presetA"
        class="px-2 py-1 border rounded text-[11px] bg-white"
        @change="$emit('update:presetA', ($event.target as HTMLSelectElement).value as PresetName)"
      >
        <option value="Safe">Safe</option>
        <option value="Standard">Standard</option>
        <option value="Aggressive">Aggressive</option>
        <option value="Custom">Custom</option>
      </select>
    </label>

    <!-- Preset B -->
    <label class="flex items-center gap-2">
      <span class="text-gray-700">Preset B:</span>
      <select
        :value="presetB"
        class="px-2 py-1 border rounded text-[11px] bg-white"
        @change="$emit('update:presetB', ($event.target as HTMLSelectElement).value as PresetName)"
      >
        <option value="Safe">Safe</option>
        <option value="Standard">Standard</option>
        <option value="Aggressive">Aggressive</option>
        <option value="Custom">Custom</option>
      </select>
    </label>

    <!-- Reload -->
    <button
      type="button"
      class="text-[11px] px-2 py-1 border rounded bg-gray-50 hover:bg-gray-100"
      @click="$emit('reload')"
    >
      Reload
    </button>

    <!-- Export buttons -->
    <button
      type="button"
      class="text-[11px] px-2 py-1 border rounded bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50"
      :disabled="exporting"
      @click="$emit('export', 'A')"
    >
      Export A CSV
    </button>
    <button
      type="button"
      class="text-[11px] px-2 py-1 border rounded bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50"
      :disabled="exporting"
      @click="$emit('export', 'B')"
    >
      Export B CSV
    </button>
    <button
      type="button"
      class="text-[11px] px-2 py-1 border rounded bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50"
      :disabled="exporting"
      @click="$emit('export', 'Both')"
    >
      Export A+B CSV
    </button>
  </div>
</template>

<script setup lang="ts">
export type PresetName = 'Safe' | 'Standard' | 'Aggressive' | 'Custom'

defineProps<{
  pipelineFilter: string
  fromDate: string
  toDate: string
  presetA: PresetName
  presetB: PresetName
  exporting: boolean
}>()

defineEmits<{
  'update:pipelineFilter': [value: string]
  'update:fromDate': [value: string]
  'update:toDate': [value: string]
  'update:presetA': [value: PresetName]
  'update:presetB': [value: PresetName]
  'reload': []
  'export': [which: 'A' | 'B' | 'Both']
}>()
</script>
