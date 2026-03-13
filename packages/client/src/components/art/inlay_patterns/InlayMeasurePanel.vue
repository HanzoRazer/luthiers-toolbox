<script setup lang="ts">
/**
 * InlayMeasurePanel — Measurement display for inlay pattern view
 */
import type { Measurement } from "@/util/measurementTool";

defineProps<{
  measurements: Measurement[];
  pendingStart: boolean;
}>();

const emit = defineEmits<{
  remove: [id: string];
  clear: [];
}>();
</script>

<template>
  <div
    v-if="measurements.length > 0"
    class="measurement-panel"
  >
    <h4>Measurements</h4>
    <ul class="measurement-list">
      <li
        v-for="m in measurements"
        :key="m.id"
        class="measurement-item"
      >
        <span>
          {{ m.distance.toFixed(2) }} mm
          <span class="measurement-angle">
            ({{ m.angleXY.toFixed(1) }}°)
          </span>
        </span>
        <span class="measurement-deltas">
          ΔX {{ m.deltaX.toFixed(2) }} · ΔY {{ m.deltaY.toFixed(2) }}
        </span>
        <button
          class="remove-btn"
          title="Remove measurement"
          @click="emit('remove', m.id)"
        >
          ×
        </button>
      </li>
    </ul>
  </div>
  <div
    v-if="pendingStart"
    class="measure-hint"
  >
    Click second point to complete measurement
  </div>
</template>

<style scoped>
.measurement-panel {
  background: var(--color-bg-secondary, #1e1e2e);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
}

.measurement-panel h4 {
  margin: 0 0 0.4rem;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-text-secondary, #aaa);
}

.measurement-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.measurement-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.25rem 0;
  font-size: 0.8rem;
  border-bottom: 1px solid var(--color-border, #333);
}

.measurement-item:last-child {
  border-bottom: none;
}

.measurement-angle {
  color: var(--color-text-secondary, #888);
}

.measurement-deltas {
  color: var(--color-text-secondary, #888);
  font-size: 0.75rem;
}

.remove-btn {
  margin-left: auto;
  background: none;
  border: none;
  color: #f87171;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0 0.3rem;
}

.measure-hint {
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-accent, #3b82f6);
  padding: 0.3rem;
}
</style>
