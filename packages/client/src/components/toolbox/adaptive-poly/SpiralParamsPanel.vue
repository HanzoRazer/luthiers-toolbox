<script setup lang="ts">
/**
 * SpiralParamsPanel - Feed rate and cutting depth for N18 spiral mode
 * Extracted from AdaptivePoly.vue
 */
defineProps<{
  baseFeed: number
  z: number
  busy: boolean
}>()

const emit = defineEmits<{
  'update:baseFeed': [value: number]
  'update:z': [value: number]
}>()
</script>

<template>
  <div class="grid grid-cols-2 gap-3">
    <div>
      <label class="block text-xs font-medium text-gray-700 mb-1">
        Feed Rate (mm/min)
      </label>
      <input
        :value="baseFeed"
        type="number"
        step="50"
        min="100"
        class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
        :disabled="busy"
        @input="emit('update:baseFeed', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-700 mb-1">
        Cutting Depth (mm)
      </label>
      <input
        :value="z"
        type="number"
        step="0.1"
        max="0"
        class="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
        :disabled="busy"
        @input="emit('update:z', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>
  </div>
</template>
