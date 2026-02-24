<script setup lang="ts">
/**
 * GcodeOutputPanel - G-code preview with download/copy actions
 * Extracted from PolygonOffsetLab.vue
 */
import { computed } from 'vue'

const props = defineProps<{
  error: string
  gcode: string
  stats: { passes: number; lines: number } | null
}>()

const emit = defineEmits<{
  'download': []
  'copy': []
}>()

const gcodePreview = computed(() => {
  if (!props.gcode) return ''
  const lines = props.gcode.split('\n')
  if (lines.length <= 50) return props.gcode
  return lines.slice(0, 50).join('\n') + '\n... (' + (lines.length - 50) + ' more lines)'
})
</script>

<template>
  <div class="output-panel">
    <h3>G-code Preview</h3>

    <div
      v-if="error"
      class="error-banner"
    >
      <strong>⚠️ Error:</strong> {{ error }}
    </div>

    <div
      v-if="gcode"
      class="gcode-preview"
    >
      <pre>{{ gcodePreview }}</pre>
    </div>

    <div
      v-if="gcode"
      class="actions"
    >
      <button
        class="btn-secondary"
        @click="emit('download')"
      >
        Download
      </button>
      <button
        class="btn-secondary"
        @click="emit('copy')"
      >
        Copy
      </button>
    </div>

    <div
      v-if="stats"
      class="stats"
    >
      <h4>Statistics</h4>
      <div><b>Passes:</b> {{ stats.passes }}</div>
      <div><b>Total Lines:</b> {{ stats.lines }}</div>
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

h4 {
  margin: 0 0 0.5rem 0;
  color: #555;
  font-size: 0.95rem;
  font-weight: 600;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.gcode-preview {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  max-height: 500px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.gcode-preview pre {
  margin: 0;
  white-space: pre-wrap;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: #64748b;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #475569;
}

.stats {
  background: #f1f5f9;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #cbd5e1;
}

.stats h4 {
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.stats div {
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}
</style>
