<template>
  <section :class="styles.panelSection">
    <h3>Cycle Type</h3>
    <div :class="styles.cycleSelector">
      <label
        v-for="cycle in cycleTypes"
        :key="cycle.value"
      >
        <input
          :checked="cycleValue === cycle.value"
          type="radio"
          :value="cycle.value"
          @change="emit('update:cycleValue', cycle.value)"
        >
        <span>{{ cycle.label }}</span>
        <small>{{ cycle.description }}</small>
      </label>
    </div>

    <div
      v-if="cycleValue === 'G83'"
      :class="styles.formGroup"
    >
      <label>Peck Depth (mm)</label>
      <input
        :value="peckDepth"
        type="number"
        step="1"
        min="1"
        @input="emit('update:peckDepth', parseInt(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div
      v-if="cycleValue === 'G84'"
      :class="styles.formGroup"
    >
      <label>Thread Pitch (mm)</label>
      <input
        :value="threadPitch"
        type="number"
        step="0.1"
        min="0.1"
        @input="emit('update:threadPitch', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  styles: Record<string, string>
  cycleValue: string
  peckDepth: number
  threadPitch: number
}>()

const emit = defineEmits<{
  'update:cycleValue': [value: string]
  'update:peckDepth': [value: number]
  'update:threadPitch': [value: number]
}>()

const cycleTypes = [
  { value: 'G81', label: 'G81', description: 'Simple Drill' },
  { value: 'G83', label: 'G83', description: 'Peck Drill' },
  { value: 'G73', label: 'G73', description: 'Chip Break' },
  { value: 'G84', label: 'G84', description: 'Tapping' },
  { value: 'G85', label: 'G85', description: 'Boring' }
]
</script>
