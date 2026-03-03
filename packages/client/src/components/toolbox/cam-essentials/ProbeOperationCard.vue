<script setup lang="ts">
/* eslint-disable vue/no-mutating-props -- Form editor with v-model on object prop is intentional */
/**
 * ProbeOperationCard - Probe patterns operation card
 * Extracted from CAMEssentialsLab.vue
 */
import type { ProbeState } from './useProbeOperation'

defineProps<{
  probe: ProbeState
  styles: Record<string, string>
}>()
</script>

<template>
  <div :class="styles['operation-card']">
    <div :class="styles['card-header']">
      <h2>🎯 Probe Patterns</h2>
      <span :class="styles.badge">N09</span>
    </div>
    <p>Work offset establishment with touch probes</p>

    <div :class="styles.params">
      <div :class="styles['param-row']">
        <label>Pattern:</label>
        <select v-model="probe.params.value.pattern">
          <option value="corner_outside">
            Corner (Outside)
          </option>
          <option value="corner_inside">
            Corner (Inside)
          </option>
          <option value="boss_circular">
            Boss (Circular)
          </option>
          <option value="hole_circular">
            Hole (Circular)
          </option>
          <option value="surface_z">
            Surface Z
          </option>
        </select>
      </div>
      <div :class="styles['param-row']">
        <label>Probe Feed (mm/min):</label>
        <input
          v-model.number="probe.params.value.feed_probe"
          type="number"
          step="10"
        >
      </div>
      <div :class="styles['param-row']">
        <label>Safe Z (mm):</label>
        <input
          v-model.number="probe.params.value.safe_z"
          type="number"
          step="0.5"
        >
      </div>
      <div
        v-if="probe.params.value.pattern.includes('circular')"
        :class="styles['param-row']"
      >
        <label>Est. Diameter (mm):</label>
        <input
          v-model.number="probe.params.value.diameter"
          type="number"
          step="1"
        >
      </div>
      <div :class="styles['param-row']">
        <label>Work Offset:</label>
        <select v-model="probe.params.value.work_offset">
          <option value="1">
            G54 (1)
          </option>
          <option value="2">
            G55 (2)
          </option>
          <option value="3">
            G56 (3)
          </option>
          <option value="4">
            G57 (4)
          </option>
          <option value="5">
            G58 (5)
          </option>
          <option value="6">
            G59 (6)
          </option>
        </select>
      </div>
    </div>

    <div :class="styles['button-group']">
      <button
        :class="[styles['export-btn'], styles.half]"
        @click="probe.exportGcode"
      >
        Export G-code
      </button>
      <button
        :class="[styles['export-btn'], styles.half, styles.secondary]"
        @click="probe.exportSVG"
      >
        Export Setup Sheet
      </button>
    </div>
  </div>
</template>
