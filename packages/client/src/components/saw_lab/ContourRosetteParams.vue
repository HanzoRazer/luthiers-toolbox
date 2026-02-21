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
      <label>Outer Radius (mm)</label>
      <input
        :value="outerRadius"
        type="number"
        step="1"
        min="1"
        @input="emit('update:outerRadius', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Inner Radius (mm)</label>
      <input
        :value="innerRadius"
        type="number"
        step="1"
        min="1"
        @input="emit('update:innerRadius', Number(($event.target as HTMLInputElement).value))"
      >
      <div
        v-if="radiusValidation"
        :class="[styles.validationHint, styles[`validationHint${radiusValidation.status.charAt(0).toUpperCase()}${radiusValidation.status.slice(1)}`]]"
      >
        {{ radiusValidation.message }}
      </div>
    </div>

    <div :class="styles.formGroup">
      <label>Number of Petals</label>
      <input
        :value="petalCount"
        type="number"
        step="1"
        min="3"
        max="24"
        @input="emit('update:petalCount', Number(($event.target as HTMLInputElement).value))"
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
  outerRadius: number
  innerRadius: number
  petalCount: number
  radiusValidation: RadiusValidation | null
}>()

const emit = defineEmits<{
  'update:centerX': [value: number]
  'update:centerY': [value: number]
  'update:outerRadius': [value: number]
  'update:innerRadius': [value: number]
  'update:petalCount': [value: number]
}>()
</script>
