<script setup lang="ts">
/**
 * MachineSelector - Machine profile selection for CAM
 * Extracted from AdaptivePocketLab.vue
 */
import { computed } from 'vue'

interface MachineProfile {
  id: string
  title: string
  limits: {
    feed_xy: number
    accel: number
    jerk: number
    rapid: number
  }
  post_id_default?: string
}

const props = defineProps<{
  machines: MachineProfile[]
  modelValue: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'edit': []
  'compare': []
}>()

const selectedMachine = computed(() =>
  props.machines.find(m => m.id === props.modelValue)
)

function onSelect(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="machine-selector">
    <label class="block text-sm font-medium">Machine Profile</label>
    <select
      :value="modelValue"
      :disabled="disabled"
      class="border px-2 py-1 rounded w-full"
      @change="onSelect"
    >
      <option
        v-for="m in machines"
        :key="m.id"
        :value="m.id"
      >
        {{ m.title }}
      </option>
      <option value="">
        (Custom from knobs)
      </option>
    </select>

    <div
      v-if="selectedMachine"
      class="text-xs text-gray-500 mt-1"
    >
      Feed {{ selectedMachine.limits.feed_xy }} mm/min ·
      Accel {{ selectedMachine.limits.accel }} mm/s² ·
      Jerk {{ selectedMachine.limits.jerk }} mm/s³ ·
      Rapid {{ selectedMachine.limits.rapid }} mm/min
    </div>

    <div class="flex gap-2 mt-2">
      <button
        class="px-2 py-1 text-sm border rounded hover:bg-gray-50"
        :disabled="!selectedMachine || disabled"
        @click="emit('edit')"
      >
        Edit Machine
      </button>
      <button
        class="px-2 py-1 text-sm border rounded hover:bg-gray-50"
        :disabled="disabled"
        @click="emit('compare')"
      >
        Compare Machines
      </button>
    </div>
  </div>
</template>
