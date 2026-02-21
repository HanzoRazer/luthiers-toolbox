<template>
  <div class="grid grid-cols-4 gap-3 border rounded p-3">
    <div>
      <label class="block text-xs font-medium">Tool Ø ({{ units }})</label>
      <input
        :value="toolD"
        type="number"
        step="0.1"
        class="w-full border rounded px-2 py-1"
        @input="$emit('update:toolD', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
    <div>
      <label class="block text-xs font-medium">Step-down ({{ units }})</label>
      <input
        :value="stepdown"
        type="number"
        step="0.1"
        class="w-full border rounded px-2 py-1"
        @input="$emit('update:stepdown', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
    <div>
      <label class="block text-xs font-medium">Scallop ({{ units }})</label>
      <input
        :value="scallop"
        type="number"
        step="0.01"
        class="w-full border rounded px-2 py-1"
        @input="$emit('update:scallop', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
    <div>
      <label class="block text-xs font-medium">Stock ({{ units }})</label>
      <input
        :value="stockThickness"
        type="number"
        step="0.1"
        class="w-full border rounded px-2 py-1"
        @input="$emit('update:stockThickness', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <!-- Phase 24.6: Dynamic Scallop Control -->
    <div class="col-span-4 flex items-center gap-2 mt-1">
      <label class="flex items-center gap-1 text-xs text-gray-700">
        <input
          :checked="useDynamicScallop"
          type="checkbox"
          class="align-middle"
          @change="$emit('update:useDynamicScallop', ($event.target as HTMLInputElement).checked)"
        >
        <span>Use dynamic scallop (slope-aware spacing)</span>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  toolD: number
  stepdown: number
  scallop: number
  stockThickness: number
  useDynamicScallop: boolean
  units: string
}>()

defineEmits<{
  'update:toolD': [value: number]
  'update:stepdown': [value: number]
  'update:scallop': [value: number]
  'update:stockThickness': [value: number]
  'update:useDynamicScallop': [value: boolean]
}>()
</script>

<style scoped>
input[type="number"] {
  font-variant-numeric: tabular-nums;
}
</style>
