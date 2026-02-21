<template>
  <div :class="styles.patternControls">
    <div :class="styles.formGroup">
      <label>Start Position</label>
      <div :class="styles.inputGroup">
        <input
          :value="startX"
          type="number"
          step="1"
          placeholder="X"
          @input="emit('update:startX', Number(($event.target as HTMLInputElement).value))"
        >
        <input
          :value="startY"
          type="number"
          step="1"
          placeholder="Y"
          @input="emit('update:startY', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>
    <div :class="styles.formGroup">
      <label>Spacing</label>
      <div :class="styles.inputGroup">
        <input
          :value="spacingX"
          type="number"
          step="1"
          placeholder="X"
          @input="emit('update:spacingX', Number(($event.target as HTMLInputElement).value))"
        >
        <input
          :value="spacingY"
          type="number"
          step="1"
          placeholder="Y"
          @input="emit('update:spacingY', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>
    <div :class="styles.formGroup">
      <label>Grid Size</label>
      <div :class="styles.inputGroup">
        <input
          :value="countX"
          type="number"
          step="1"
          min="1"
          placeholder="Cols"
          @input="emit('update:countX', Number(($event.target as HTMLInputElement).value))"
        >
        <input
          :value="countY"
          type="number"
          step="1"
          min="1"
          placeholder="Rows"
          @input="emit('update:countY', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
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
  startX: number
  startY: number
  spacingX: number
  spacingY: number
  countX: number
  countY: number
}>()

const emit = defineEmits<{
  'update:startX': [value: number]
  'update:startY': [value: number]
  'update:spacingX': [value: number]
  'update:spacingY': [value: number]
  'update:countX': [value: number]
  'update:countY': [value: number]
  'generate': []
}>()
</script>
