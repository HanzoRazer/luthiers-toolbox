<script setup lang="ts">
/**
 * TrochoidSettings - L.3 Trochoid insertion parameters
 * Extracted from AdaptivePocketLab.vue
 */

const props = defineProps<{
  useTrochoids: boolean
  trochoidRadius: number
  trochoidPitch: number
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:useTrochoids': [value: boolean]
  'update:trochoidRadius': [value: number]
  'update:trochoidPitch': [value: number]
}>()
</script>

<template>
  <div class="trochoid-settings border-t pt-4 space-y-2">
    <h3 class="font-semibold text-sm">
      Trochoids (L.3)
    </h3>
    <label class="flex items-center gap-2 text-sm">
      <input
        :checked="useTrochoids"
        type="checkbox"
        :disabled="disabled"
        @change="emit('update:useTrochoids', ($event.target as HTMLInputElement).checked)"
      >
      <span>Use trochoids</span>
    </label>

    <div
      v-if="useTrochoids"
      class="grid grid-cols-2 gap-2 pl-4"
    >
      <div>
        <label class="block text-xs">Trochoid radius (mm)</label>
        <input
          :value="trochoidRadius"
          type="number"
          step="0.1"
          min="0.3"
          :disabled="disabled"
          class="border px-2 py-1 rounded w-full"
          @input="emit('update:trochoidRadius', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div>
        <label class="block text-xs">Trochoid pitch (mm)</label>
        <input
          :value="trochoidPitch"
          type="number"
          step="0.1"
          min="0.6"
          :disabled="disabled"
          class="border px-2 py-1 rounded w-full"
          @input="emit('update:trochoidPitch', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>
  </div>
</template>
