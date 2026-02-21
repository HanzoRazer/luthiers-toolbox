<template>
  <section :class="styles.panelSection">
    <h3>Tool Setup</h3>
    <div :class="styles.toolTypeSelector">
      <label
        v-for="tool in toolTypes"
        :key="tool.value"
      >
        <input
          :checked="toolType === tool.value"
          type="radio"
          :value="tool.value"
          @change="emit('update:toolType', tool.value)"
        >
        <span>{{ tool.label }}</span>
      </label>
    </div>

    <div :class="styles.formGroup">
      <label>Tool Diameter (mm)</label>
      <input
        :value="toolDiameter"
        type="number"
        step="0.1"
        min="0.1"
        @input="emit('update:toolDiameter', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Spindle RPM</label>
      <input
        :value="spindleRpm"
        type="number"
        step="100"
        min="100"
        @input="emit('update:spindleRpm', parseInt(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Feed Rate (mm/min)</label>
      <input
        :value="feedRate"
        type="number"
        step="10"
        min="10"
        @input="emit('update:feedRate', parseInt(($event.target as HTMLInputElement).value))"
      >
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  styles: Record<string, string>
  toolType: string
  toolDiameter: number
  spindleRpm: number
  feedRate: number
}>()

const emit = defineEmits<{
  'update:toolType': [value: string]
  'update:toolDiameter': [value: number]
  'update:spindleRpm': [value: number]
  'update:feedRate': [value: number]
}>()

const toolTypes = [
  { value: 'drill', label: 'Drill' },
  { value: 'tap', label: 'Tap' },
  { value: 'spot', label: 'Spot Drill' },
  { value: 'boring', label: 'Boring Bar' }
]
</script>
