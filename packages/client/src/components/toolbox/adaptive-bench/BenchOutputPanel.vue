<script setup lang="ts">
/**
 * BenchOutputPanel.vue - Output visualization panel
 * Extracted from AdaptiveBenchLab.vue
 */
import { BenchResultsPanel } from './'
import type { BenchResult } from './useAdaptiveBenchActions'

defineProps<{
  error: string
  svgContent: string
  benchResult: BenchResult | null
}>()
</script>

<template>
  <div class="output-panel">
    <h3>Visualization</h3>

    <div
      v-if="error"
      class="error-banner"
    >
      <strong>Error:</strong> {{ error }}
    </div>

    <div
      v-if="svgContent"
      class="svg-viewer"
      v-html="svgContent"
    />

    <BenchResultsPanel
      v-if="benchResult"
      :result="benchResult"
    />

    <div
      v-if="!svgContent && !benchResult && !error"
      class="placeholder"
    >
      <p>Select an action to visualize spiral or trochoid paths, or run performance benchmark.</p>
    </div>
  </div>
</template>

<style scoped>
.output-panel {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

h3 {
  margin-top: 0;
  color: #333;
  font-size: 1.2rem;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.svg-viewer {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 1rem;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.svg-viewer :deep(svg) {
  max-width: 100%;
  height: auto;
}

.placeholder {
  text-align: center;
  padding: 3rem 1rem;
  color: #64748b;
}
</style>
