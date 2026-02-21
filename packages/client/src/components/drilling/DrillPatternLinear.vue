<template>
  <div :class="styles.patternControls">
    <div :class="styles.formGroup">
      <label>Direction</label>
      <select
        :value="direction"
        @change="emit('update:direction', ($event.target as HTMLSelectElement).value)"
      >
        <option value="x">
          Horizontal (X)
        </option>
        <option value="y">
          Vertical (Y)
        </option>
      </select>
    </div>
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
      <label>Spacing (mm)</label>
      <input
        :value="spacing"
        type="number"
        step="1"
        min="1"
        @input="emit('update:spacing', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
    <div :class="styles.formGroup">
      <label>Count</label>
      <input
        :value="count"
        type="number"
        step="1"
        min="1"
        @input="emit('update:count', Number(($event.target as HTMLInputElement).value))"
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
  direction: string
  startX: number
  startY: number
  spacing: number
  count: number
}>()

const emit = defineEmits<{
  'update:direction': [value: string]
  'update:startX': [value: number]
  'update:startY': [value: number]
  'update:spacing': [value: number]
  'update:count': [value: number]
  'generate': []
}>()
</script>
