<script setup lang="ts">
/**
 * MeasurementsPanel — Distance measurements panel for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows captured measurements with distance and delta values.
 */

interface Measurement {
  id: string;
  distance: number;
  deltaX: number;
  deltaY: number;
  deltaZ: number;
}

interface MeasureTool {
  formatDistance: (d: number) => string;
}

interface Props {
  measurements: Measurement[];
  measureTool: MeasureTool;
  collapsed?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
});

const emit = defineEmits<{
  remove: [id: string];
  clear: [];
  'update:collapsed': [value: boolean];
}>();
</script>

<template>
  <div
    v-if="measurements.length > 0"
    class="measurements-panel"
  >
    <div class="panel-header">
      <span>Measurements</span>
      <div class="panel-header-actions">
        <button
          title="Clear all"
          @click="emit('clear')"
        >
          Clear
        </button>
        <button @click="emit('update:collapsed', !collapsed)">
          {{ collapsed ? '+' : '-' }}
        </button>
      </div>
    </div>
    <ul
      v-if="!collapsed"
      class="measurements-list"
    >
      <li
        v-for="m in measurements"
        :key="m.id"
      >
        <span class="measure-dist">{{ measureTool.formatDistance(m.distance) }}</span>
        <span class="measure-details">
          dX: {{ m.deltaX.toFixed(2) }}
          dY: {{ m.deltaY.toFixed(2) }}
          dZ: {{ m.deltaZ.toFixed(2) }}
        </span>
        <button
          class="measure-remove"
          title="Remove"
          @click="emit('remove', m.id)"
        >
          x
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.measurements-panel {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 260px;
  background: #1a1a2e;
  border: 1px solid #00ffff;
  border-radius: 8px;
  overflow: hidden;
  z-index: 12;
  font-size: 11px;
  box-shadow: 0 4px 20px rgba(0, 255, 255, 0.15);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 255, 255, 0.1);
  border-bottom: 1px solid #00ffff;
  color: #00ffff;
}

.panel-header-actions {
  display: flex;
  gap: 6px;
}

.panel-header-actions button {
  background: transparent;
  border: 1px solid #3a3a5c;
  border-radius: 3px;
  color: #888;
  padding: 2px 6px;
  font-size: 10px;
  cursor: pointer;
}

.panel-header-actions button:hover {
  border-color: #00ffff;
  color: #00ffff;
}

.measurements-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 200px;
  overflow-y: auto;
}

.measurements-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #252538;
  color: #ccc;
}

.measurements-list li:last-child {
  border-bottom: none;
}

.measure-dist {
  color: #00ffff;
  font-weight: 600;
  min-width: 70px;
}

.measure-details {
  flex: 1;
  color: #666;
  font-size: 10px;
}

.measure-remove {
  background: transparent;
  border: none;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  padding: 2px 6px;
}

.measure-remove:hover {
  color: #e74c3c;
}
</style>
