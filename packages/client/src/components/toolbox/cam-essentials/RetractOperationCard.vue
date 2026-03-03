<script setup lang="ts">
/* eslint-disable vue/no-mutating-props -- Form editor with v-model on object prop is intentional */
/**
 * RetractOperationCard - Retract patterns operation card
 * Extracted from CAMEssentialsLab.vue
 */
import type { RetractState } from './useRetractOperation'

defineProps<{
  retract: RetractState
  styles: Record<string, string>
}>()
</script>

<template>
  <div :class="styles['operation-card']">
    <div :class="styles['card-header']">
      <h2>↑ Retract Patterns</h2>
      <span :class="styles.badge">N08</span>
    </div>
    <p>Safe retract strategies for tool changes</p>

    <div :class="styles.params">
      <div :class="styles['param-row']">
        <label>Strategy:</label>
        <select v-model="retract.params.value.strategy">
          <option value="direct">
            Direct (G0)
          </option>
          <option value="ramped">
            Ramped (Linear)
          </option>
          <option value="helical">
            Helical (Spiral)
          </option>
        </select>
      </div>
      <div :class="styles['param-row']">
        <label>Current Z (mm):</label>
        <input
          v-model.number="retract.params.value.current_z"
          type="number"
          step="0.1"
        >
      </div>
      <div :class="styles['param-row']">
        <label>Safe Z (mm):</label>
        <input
          v-model.number="retract.params.value.safe_z"
          type="number"
          step="0.5"
        >
      </div>
      <div
        v-if="retract.params.value.strategy === 'ramped'"
        :class="styles['param-row']"
      >
        <label>Ramp Feed (mm/min):</label>
        <input
          v-model.number="retract.params.value.ramp_feed"
          type="number"
          step="10"
        >
      </div>
      <div
        v-if="retract.params.value.strategy === 'helical'"
        :class="styles['param-row']"
      >
        <label>Helix Radius (mm):</label>
        <input
          v-model.number="retract.params.value.helix_radius"
          type="number"
          step="0.5"
        >
      </div>
      <div
        v-if="retract.params.value.strategy === 'helical'"
        :class="styles['param-row']"
      >
        <label>Pitch (mm/rev):</label>
        <input
          v-model.number="retract.params.value.helix_pitch"
          type="number"
          step="0.1"
        >
      </div>
    </div>

    <button
      :class="styles['export-btn']"
      @click="retract.exportGcode"
    >
      Export Sample G-code
    </button>
  </div>
</template>
