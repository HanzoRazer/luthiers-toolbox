<script setup lang="ts">
/**
 * JerkAwareSettings - L.3 Jerk-aware time estimation parameters
 * Extracted from AdaptivePocketLab.vue
 */

const props = defineProps<{
  jerkAware: boolean
  machineAccel: number
  machineJerk: number
  cornerTol: number
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:jerkAware': [value: boolean]
  'update:machineAccel': [value: number]
  'update:machineJerk': [value: number]
  'update:cornerTol': [value: number]
}>()
</script>

<template>
  <div class="jerk-aware-settings border-t pt-4 space-y-2">
    <h3 class="font-semibold text-sm">
      Jerk-Aware Time (L.3)
    </h3>
    <label class="flex items-center gap-2 text-sm">
      <input
        :checked="jerkAware"
        type="checkbox"
        :disabled="disabled"
        @change="emit('update:jerkAware', ($event.target as HTMLInputElement).checked)"
      >
      <span>Jerk-aware time</span>
    </label>

    <div
      v-if="jerkAware"
      class="grid grid-cols-2 gap-2 pl-4"
    >
      <div>
        <label class="block text-xs">Accel (mm/s²)</label>
        <input
          :value="machineAccel"
          type="number"
          step="10"
          min="100"
          :disabled="disabled"
          class="border px-2 py-1 rounded w-full"
          @input="emit('update:machineAccel', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div>
        <label class="block text-xs">Jerk (mm/s³)</label>
        <input
          :value="machineJerk"
          type="number"
          step="100"
          min="100"
          :disabled="disabled"
          class="border px-2 py-1 rounded w-full"
          @input="emit('update:machineJerk', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="col-span-2">
        <label class="block text-xs">Corner tol (mm)</label>
        <input
          :value="cornerTol"
          type="number"
          step="0.05"
          min="0.05"
          max="1.0"
          :disabled="disabled"
          class="border px-2 py-1 rounded w-full"
          @input="emit('update:cornerTol', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>
  </div>
</template>
