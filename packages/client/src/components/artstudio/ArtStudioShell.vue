<template>
  <div class="artstudio-shell">
    <ArtStudioSidebar class="artstudio-shell__sidebar">
      <template #footer>
        <ArtStudioCalculatorDebugPanel />
      </template>
    </ArtStudioSidebar>

    <main class="artstudio-shell__main">
      <header class="artstudio-shell__header">
        <h1>Art Studio</h1>
        <div class="header-controls">
          <label class="toggle">
            <input type="checkbox" v-model="showToolpaths" />
            Toolpaths
          </label>
          <label class="toggle">
            <input type="checkbox" v-model="showFretboard" />
            Fretboard
          </label>
          <label class="toggle">
            <input type="checkbox" v-model="showFretSlots" />
            Fret Slots
          </label>
          <label class="toggle">
            <input type="checkbox" v-model="showGrid" />
            Grid
          </label>
        </div>
      </header>

      <ArtStudioCanvas
        ref="canvasRef"
        class="artstudio-shell__canvas"
        :show-toolpaths="showToolpaths"
        :show-fretboard="showFretboard"
        :show-fret-slots="showFretSlots"
        :grid-size="showGrid ? 10 : 0"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ArtStudioSidebar from "./ArtStudioSidebar.vue";
import ArtStudioCanvas from "./ArtStudioCanvas.vue";
import ArtStudioCalculatorDebugPanel from "./ArtStudioCalculatorDebugPanel.vue";

// Canvas ref for external control
const canvasRef = ref<InstanceType<typeof ArtStudioCanvas> | null>(null);

// View toggles
const showToolpaths = ref(true);
const showFretboard = ref(true);
const showFretSlots = ref(true);
const showGrid = ref(true);

// Expose canvas methods
defineExpose({
  canvas: canvasRef,
});
</script>

<style scoped>
.artstudio-shell {
  display: grid;
  grid-template-columns: 300px 1fr;
  grid-template-rows: 1fr;
  height: 100%;
  width: 100%;
  background: #f8f9fa;
}

.artstudio-shell__sidebar {
  overflow-y: auto;
  max-height: 100%;
}

.artstudio-shell__main {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.artstudio-shell__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: white;
  border-bottom: 1px solid #dee2e6;
}

.artstudio-shell__header h1 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  color: #212529;
}

.header-controls {
  display: flex;
  gap: 1rem;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: #495057;
  cursor: pointer;
}

.toggle input {
  margin: 0;
}

.artstudio-shell__canvas {
  flex: 1;
  min-height: 0;
}
</style>
