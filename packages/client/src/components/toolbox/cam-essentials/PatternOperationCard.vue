<script setup lang="ts">
/* eslint-disable vue/no-mutating-props -- Form editor with v-model on object prop is intentional */
/**
 * PatternOperationCard - Drill pattern operation card
 * Extracted from CAMEssentialsLab.vue
 */
import type { PatternState } from './usePatternOperation'

defineProps<{
  pattern: PatternState
  styles: Record<string, string>
}>()
</script>

<template>
  <div :class="styles['operation-card']">
    <div :class="styles['card-header']">
      <h2>📐 Drill Patterns</h2>
      <span :class="styles.badge">N10</span>
    </div>
    <p>Generate drilling patterns (grid, circle, line)</p>

    <div :class="styles.params">
      <div :class="styles['param-row']">
        <label>Pattern:</label>
        <select v-model="pattern.params.value.type">
          <option value="grid">
            Grid
          </option>
          <option value="circle">
            Circle
          </option>
          <option value="line">
            Line
          </option>
        </select>
      </div>

      <!-- Grid Pattern -->
      <template v-if="pattern.params.value.type === 'grid'">
        <div :class="styles['param-row']">
          <label>Rows:</label>
          <input
            v-model.number="pattern.params.value.grid.rows"
            type="number"
            min="1"
          >
        </div>
        <div :class="styles['param-row']">
          <label>Columns:</label>
          <input
            v-model.number="pattern.params.value.grid.cols"
            type="number"
            min="1"
          >
        </div>
        <div :class="styles['param-row']">
          <label>X Spacing (mm):</label>
          <input
            v-model.number="pattern.params.value.grid.dx"
            type="number"
            step="0.1"
          >
        </div>
        <div :class="styles['param-row']">
          <label>Y Spacing (mm):</label>
          <input
            v-model.number="pattern.params.value.grid.dy"
            type="number"
            step="0.1"
          >
        </div>
      </template>

      <!-- Circle Pattern -->
      <template v-if="pattern.params.value.type === 'circle'">
        <div :class="styles['param-row']">
          <label>Count:</label>
          <input
            v-model.number="pattern.params.value.circle.count"
            type="number"
            min="1"
          >
        </div>
        <div :class="styles['param-row']">
          <label>Radius (mm):</label>
          <input
            v-model.number="pattern.params.value.circle.radius"
            type="number"
            step="0.1"
          >
        </div>
        <div :class="styles['param-row']">
          <label>Start Angle (°):</label>
          <input
            v-model.number="pattern.params.value.circle.start_angle_deg"
            type="number"
            step="1"
          >
        </div>
      </template>

      <!-- Line Pattern -->
      <template v-if="pattern.params.value.type === 'line'">
        <div :class="styles['param-row']">
          <label>Count:</label>
          <input
            v-model.number="pattern.params.value.line.count"
            type="number"
            min="1"
          >
        </div>
        <div :class="styles['param-row']">
          <label>X Increment (mm):</label>
          <input
            v-model.number="pattern.params.value.line.dx"
            type="number"
            step="0.1"
          >
        </div>
        <div :class="styles['param-row']">
          <label>Y Increment (mm):</label>
          <input
            v-model.number="pattern.params.value.line.dy"
            type="number"
            step="0.1"
          >
        </div>
      </template>

      <div :class="styles['param-row']">
        <label>Depth (mm):</label>
        <input
          v-model.number="pattern.params.value.depth"
          type="number"
          step="0.1"
        >
      </div>
      <div :class="styles['param-row']">
        <label>Feed (mm/min):</label>
        <input
          v-model.number="pattern.params.value.feed"
          type="number"
          step="10"
        >
      </div>
    </div>

    <button
      :class="styles['export-btn']"
      @click="pattern.exportGcode"
    >
      Export G-code
    </button>
  </div>
</template>
