<template>
  <div>
    <div :class="styles.formGroup">
      <label>Center X (mm)</label>
      <input
        :value="centerX"
        type="number"
        step="0.1"
        @input="emit('update:centerX', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Center Y (mm)</label>
      <input
        :value="centerY"
        type="number"
        step="0.1"
        @input="emit('update:centerY', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Radius (mm)</label>
      <input
        :value="radius"
        type="number"
        step="1"
        min="1"
        @input="emit('update:radius', Number(($event.target as HTMLInputElement).value))"
      >
      <div
        v-if="radiusValidation"
        :class="[styles.validationHint, styles[`validationHint${radiusValidation.status.charAt(0).toUpperCase()}${radiusValidation.status.slice(1)}`]]"
      >
        {{ radiusValidation.message }}
      </div>
    </div>

    <div :class="styles.formGroup">
      <label>Start Angle (degrees)</label>
      <input
        :value="startAngle"
        type="number"
        step="15"
        min="0"
        max="360"
        @input="emit('update:startAngle', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>End Angle (degrees)</label>
      <input
        :value="endAngle"
        type="number"
        step="15"
        min="0"
        max="360"
        @input="emit('update:endAngle', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from './SawContourPanel.module.css'

interface RadiusValidation {
  status: string
  message: string
  min_radius?: number
  requested_radius?: number
  safety_margin?: number
}

defineProps<{
  centerX: number
  centerY: number
  radius: number
  startAngle: number
  endAngle: number
  radiusValidation: RadiusValidation | null
}>()

const emit = defineEmits<{
  'update:centerX': [value: number]
  'update:centerY': [value: number]
  'update:radius': [value: number]
  'update:startAngle': [value: number]
  'update:endAngle': [value: number]
}>()
</script>
