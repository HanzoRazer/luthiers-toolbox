<!-- Patch N11.2 - Rosette Designer View scaffolding -->

<template>
  <div class="rosette-designer-page">
    <h1>Rosette Designer (Scaffolding)</h1>

    <div class="status-bar">
      <button @click="onAddRing">
        Add Ring
      </button>
      <button
        :disabled="!hasRing || loading"
        @click="onSegment"
      >
        Segment Ring
      </button>
      <button
        :disabled="!hasSegmentation || loading"
        @click="onGenerateSlices"
      >
        Generate Slices
      </button>

      <span v-if="loading">Working...</span>
      <span
        v-if="error"
        class="error"
      >Error: {{ error }}</span>
    </div>

    <div class="layout">
      <div class="left-panel">
        <ColumnStripEditor />
        <RingConfigPanel />
      </div>

      <div class="center-panel">
        <TilePreviewCanvas />
        <hr>
        <MultiRingPreviewPanel />
      </div>

      <div class="right-panel">
        <pre class="debug-block">
Segmentation:
{{ segmentation }}

SliceBatch:
{{ sliceBatch }}
        </pre>

        <hr>

        <CNCExportPanel />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ColumnStripEditor from '@/components/rmos/ColumnStripEditor.vue'
import RingConfigPanel from '@/components/rmos/RingConfigPanel.vue'
import TilePreviewCanvas from '@/components/rmos/TilePreviewCanvas.vue'
import MultiRingPreviewPanel from '@/components/rmos/MultiRingPreviewPanel.vue'
import CNCExportPanel from '@/components/rmos/CNCExportPanel.vue'
import { useRosetteDesignerStore } from '@/stores/useRosetteDesignerStore'

const store = useRosetteDesignerStore()

const loading = computed(() => store.loading)
const error = computed(() => store.error)
const segmentation = computed(() => store.segmentation)
const sliceBatch = computed(() => store.sliceBatch)
const hasRing = computed(() => store.rings.length > 0)
const hasSegmentation = computed(() => !!store.segmentation)

function onAddRing() {
  store.addDefaultRing()
}

function onSegment() {
  store.segmentSelectedRing()
}

function onGenerateSlices() {
  store.generateSlicesForSelectedRing()
}
</script>

<style scoped>
.rosette-designer-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
}

.status-bar {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.layout {
  display: grid;
  grid-template-columns: 1.2fr 1.5fr 1.3fr;
  gap: 1rem;
  align-items: stretch;
}

.left-panel,
.center-panel,
.right-panel {
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 0.75rem;
}

.debug-block {
  font-size: 0.75rem;
  max-height: 400px;
  overflow: auto;
  background: #f9f9f9;
}

.error {
  color: #b00020;
}
</style>
