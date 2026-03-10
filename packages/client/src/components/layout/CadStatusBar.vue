<script setup lang="ts">
/**
 * CadStatusBar.vue
 *
 * Bottom status bar for CAD layout showing coordinates, zoom, and status messages.
 */

import { ref, onMounted, onUnmounted } from "vue";

const props = withDefaults(
  defineProps<{
    /** X coordinate to display */
    x?: number | null;
    /** Y coordinate to display */
    y?: number | null;
    /** Z coordinate to display */
    z?: number | null;
    /** Zoom level percentage */
    zoom?: number;
    /** Units (mm or in) */
    units?: "mm" | "in";
    /** Status message */
    message?: string;
    /** Show memory usage */
    showMemory?: boolean;
  }>(),
  {
    x: null,
    y: null,
    z: null,
    zoom: 100,
    units: "mm",
    message: "Ready",
    showMemory: false,
  }
);

const memoryUsage = ref<string>("");

function updateMemory() {
  if (props.showMemory && "memory" in performance) {
    const mem = (performance as any).memory;
    const used = (mem.usedJSHeapSize / 1024 / 1024).toFixed(1);
    memoryUsage.value = `${used} MB`;
  }
}

let memoryInterval: number | null = null;

onMounted(() => {
  if (props.showMemory) {
    updateMemory();
    memoryInterval = window.setInterval(updateMemory, 5000);
  }
});

onUnmounted(() => {
  if (memoryInterval) {
    clearInterval(memoryInterval);
  }
});

function formatCoord(value: number | null): string {
  if (value === null) return "—";
  return value.toFixed(3);
}
</script>

<template>
  <div class="cad-status-bar">
    <!-- Left: Status message -->
    <div class="status-left">
      <span class="status-message">{{ message }}</span>
    </div>

    <!-- Center: Slot for custom content -->
    <div class="status-center">
      <slot />
    </div>

    <!-- Right: Coordinates, Zoom, Units -->
    <div class="status-right">
      <!-- Coordinates -->
      <div v-if="x !== null || y !== null || z !== null" class="coords">
        <span class="coord">
          <span class="coord-label">X:</span>
          <span class="coord-value">{{ formatCoord(x) }}</span>
        </span>
        <span class="coord">
          <span class="coord-label">Y:</span>
          <span class="coord-value">{{ formatCoord(y) }}</span>
        </span>
        <span v-if="z !== null" class="coord">
          <span class="coord-label">Z:</span>
          <span class="coord-value">{{ formatCoord(z) }}</span>
        </span>
      </div>

      <!-- Separator -->
      <span v-if="x !== null || y !== null" class="separator">|</span>

      <!-- Zoom -->
      <span class="zoom">{{ zoom }}%</span>

      <!-- Units -->
      <span class="units">{{ units.toUpperCase() }}</span>

      <!-- Memory -->
      <span v-if="showMemory && memoryUsage" class="memory">{{ memoryUsage }}</span>
    </div>
  </div>
</template>

<style scoped>
.cad-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 12px;
  font-size: 11px;
  font-family: ui-monospace, "SF Mono", Menlo, Monaco, "Cascadia Code", monospace;
}

.status-left {
  flex: 1;
  min-width: 0;
}

.status-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-message {
  color: var(--color-text-secondary, #a0a0a0);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.coords {
  display: flex;
  gap: 12px;
}

.coord {
  display: flex;
  gap: 4px;
}

.coord-label {
  color: var(--color-text-muted, #707070);
}

.coord-value {
  color: var(--color-text-primary, #e0e0e0);
  min-width: 60px;
  text-align: right;
}

.separator {
  color: var(--color-border-panel, #3a3a3a);
}

.zoom {
  color: var(--color-text-secondary, #a0a0a0);
  min-width: 40px;
  text-align: right;
}

.units {
  padding: 2px 6px;
  background: var(--color-bg-panel, #242424);
  border-radius: 3px;
  color: var(--color-accent, #4a9eff);
  font-weight: 500;
}

.memory {
  color: var(--color-text-muted, #707070);
}
</style>
