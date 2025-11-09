<template>
  <div class="adaptive-preview">
    <h3>Adaptive Toolpath Preview</h3>
    
    <div class="preview-grid">
      <!-- Spiral Preview -->
      <div class="preview-panel">
        <h4>Spiral Pocket</h4>
        <div class="params">
          <label>
            Width (mm):
            <input v-model.number="spiral.width" type="number" step="1" />
          </label>
          <label>
            Height (mm):
            <input v-model.number="spiral.height" type="number" step="1" />
          </label>
          <label>
            Step (mm):
            <input v-model.number="spiral.step" type="number" step="0.1" />
          </label>
          <button @click="plotSpiral" :disabled="loadingSpiral">
            {{ loadingSpiral ? 'Plotting...' : 'Plot Spiral' }}
          </button>
        </div>
        <div v-if="spiralError" class="error">{{ spiralError }}</div>
        <div v-if="spiralSvg" class="svg-container" v-html="spiralSvg" />
      </div>

      <!-- Trochoid Preview -->
      <div class="preview-panel">
        <h4>Trochoidal Slot</h4>
        <div class="params">
          <label>
            Width (mm):
            <input v-model.number="trochoid.width" type="number" step="1" />
          </label>
          <label>
            Height (mm):
            <input v-model.number="trochoid.height" type="number" step="1" />
          </label>
          <label>
            Pitch (mm):
            <input v-model.number="trochoid.pitch" type="number" step="0.1" />
          </label>
          <label>
            Amplitude (mm):
            <input v-model.number="trochoid.amp" type="number" step="0.1" />
          </label>
          <label>
            Direction:
            <select v-model="trochoid.feed_dir">
              <option value="x">Horizontal</option>
              <option value="y">Vertical</option>
            </select>
          </label>
          <button @click="plotTrochoid" :disabled="loadingTrochoid">
            {{ loadingTrochoid ? 'Plotting...' : 'Plot Trochoid' }}
          </button>
        </div>
        <div v-if="trochoidError" class="error">{{ trochoidError }}</div>
        <div v-if="trochoidSvg" class="svg-container" v-html="trochoidSvg" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const spiral = ref({
  width: 60,
  height: 40,
  step: 2.0,
  turns: 30,
  center_x: 0,
  center_y: 0
})

const trochoid = ref({
  width: 50,
  height: 30,
  pitch: 3.0,
  amp: 0.6,
  feed_dir: 'x' as 'x' | 'y'
})

const spiralSvg = ref<string>('')
const trochoidSvg = ref<string>('')
const spiralError = ref<string>('')
const trochoidError = ref<string>('')
const loadingSpiral = ref<boolean>(false)
const loadingTrochoid = ref<boolean>(false)

async function plotSpiral() {
  loadingSpiral.value = true
  spiralError.value = ''
  
  try {
    const res = await fetch('/api/cam/adaptive/spiral.svg', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spiral.value)
    })
    
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    
    spiralSvg.value = await res.text()
  } catch (err: any) {
    spiralError.value = `Failed to generate spiral: ${err.message}`
  } finally {
    loadingSpiral.value = false
  }
}

async function plotTrochoid() {
  loadingTrochoid.value = true
  trochoidError.value = ''
  
  try {
    const res = await fetch('/api/cam/adaptive/trochoid.svg', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(trochoid.value)
    })
    
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    
    trochoidSvg.value = await res.text()
  } catch (err: any) {
    trochoidError.value = `Failed to generate trochoid: ${err.message}`
  } finally {
    loadingTrochoid.value = false
  }
}
</script>

<style scoped>
.adaptive-preview {
  padding: 1rem;
}

.preview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-top: 1rem;
}

.preview-panel {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  background: #fafafa;
}

.preview-panel h4 {
  margin-top: 0;
  color: #333;
}

.params {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.params label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.params input,
.params select {
  width: 100px;
  padding: 0.25rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 0.5rem 1rem;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.5rem;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  color: #d32f2f;
  background: #ffebee;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.svg-container {
  margin-top: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1rem;
  background: white;
  min-height: 200px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.svg-container :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>
