<template>
  <div :class="styles.patternControls">
    <div :class="styles.formGroup">
      <label>Center Position</label>
      <div :class="styles.inputGroup">
        <input
          :value="centerX"
          type="number"
          step="1"
          placeholder="X"
          @input="emit('update:centerX', Number(($event.target as HTMLInputElement).value))"
        >
        <input
          :value="centerY"
          type="number"
          step="1"
          placeholder="Y"
          @input="emit('update:centerY', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
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
    </div>
    <div :class="styles.formGroup">
      <label>Count</label>
      <input
        :value="count"
        type="number"
        step="1"
        min="3"
        @input="emit('update:count', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
    <div :class="styles.formGroup">
      <label>Start Angle (°)</label>
      <input
        :value="startAngle"
        type="number"
        step="1"
        @input="emit('update:startAngle', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
    <button
      :class="styles.btnGenerate"
      @click="emit('generate')"
    >
      Generate
    </button>
  </div>
</template>

<script setup lang="ts">
import styles from '../DrillingLab.module.css'

defineProps<{
  centerX: number
  centerY: number
  radius: number
  count: number
  startAngle: number
}>()

const emit = defineEmits<{
  'update:centerX': [value: number]
  'update:centerY': [value: number]
  'update:radius': [value: number]
  'update:count': [value: number]
  'update:startAngle': [value: number]
  'generate': []
}>()
</script>
