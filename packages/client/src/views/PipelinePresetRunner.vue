<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
PipelinePresetRunner - Standalone preset runner for saved pipeline configurations

Part of Phase 25.0: Pipeline Preset Integration
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- Run saved pipeline presets by ID
- Query parameter support (?preset_id=...)
- JSON result display
- Error handling for invalid presets
-->

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const presetId = ref('')
const running = ref(false)
const error = ref('')
const result = ref<any>(null)

const prettyResult = computed(() => {
  if (!result.value) return ''
  return JSON.stringify(result.value, null, 2)
})

onMounted(() => {
  // Auto-fill from query param if present
  const queryPresetId = route.query.preset_id as string
  if (queryPresetId) {
    presetId.value = queryPresetId
  }
})

async function runPreset() {
  if (!presetId.value.trim()) {
    error.value = 'Preset ID is required'
    return
  }

  running.value = true
  error.value = ''
  result.value = null

  try {
    const response = await api(`/api/cam/pipeline/presets/${presetId.value.trim()}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    result.value = await response.json()
  } catch (err: any) {
    error.value = `Failed to run preset: ${err.message}`
  } finally {
    running.value = false
  }
}
</script>

<template>
  <div class="pipeline-preset-runner">
    <h1>Pipeline Preset Runner</h1>
    <p class="subtitle">
      Run saved pipeline presets by ID
    </p>

    <div class="form-group">
      <label for="preset-id">Preset ID:</label>
      <input
        id="preset-id"
        v-model="presetId"
        type="text"
        placeholder="e.g., bridge_pocket_6"
        :disabled="running"
      >
    </div>

    <button
      :disabled="running || !presetId.trim()"
      class="primary"
      @click="runPreset"
    >
      {{ running ? 'Running...' : 'Run Pipeline' }}
    </button>

    <div
      v-if="error"
      class="error-message"
    >
      {{ error }}
    </div>

    <div
      v-if="result"
      class="result-section"
    >
      <h3>Result</h3>
      <pre>{{ prettyResult }}</pre>
    </div>
  </div>
</template>

<style scoped>
.pipeline-preset-runner {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 600;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button.primary {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

button.primary:hover:not(:disabled) {
  background: #0056b3;
}

.error-message {
  margin-top: 1rem;
  padding: 0.5rem;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 4px;
  color: #c00;
}

.result-section {
  margin-top: 2rem;
}

.result-section h3 {
  margin-bottom: 0.5rem;
}

.result-section pre {
  background: #f9f9f9;
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.85rem;
}
</style>
