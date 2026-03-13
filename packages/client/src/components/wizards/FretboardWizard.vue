<template>
  <div class="wizard-container">
    <div class="wizard-header">
      <h2>Fretboard Calculator Wizard</h2>
      <div class="step-indicator">
        <div
          v-for="(step, idx) in steps"
          :key="idx"
          :class="['step', { active: currentStep === idx, completed: currentStep > idx }]"
        >
          <span class="step-number">{{ idx + 1 }}</span>
          <span class="step-label">{{ step.label }}</span>
        </div>
      </div>
    </div>

    <div class="wizard-content">
      <!-- Step 1: Scale Length -->
      <div v-if="currentStep === 0" class="step-content">
        <h3>Select Scale Length</h3>
        <p>Choose a preset or enter a custom scale length.</p>

        <div class="preset-grid">
          <button
            v-for="preset in scalePresets"
            :key="preset.id"
            :class="['preset-btn', { selected: selectedPreset === preset.id }]"
            @click="selectPreset(preset)"
          >
            <strong>{{ preset.name }}</strong>
            <span>{{ preset.mm }}mm ({{ preset.inches }}")</span>
          </button>
        </div>

        <div class="custom-input">
          <label>Or enter custom scale length (mm):</label>
          <input
            type="number"
            v-model.number="params.scaleLength"
            step="0.1"
            min="100"
            max="1000"
          />
        </div>
      </div>

      <!-- Step 2: Fret Count -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>Configure Frets</h3>

        <div class="form-grid">
          <div class="form-group">
            <label>Number of Frets</label>
            <input type="number" v-model.number="params.fretCount" min="12" max="36" />
            <span class="hint">Standard guitars: 19-24 frets</span>
          </div>

          <div class="form-group">
            <label>Temperament</label>
            <select v-model="params.temperament">
              <option value="equal_12">12-TET (Standard)</option>
              <option value="pythagorean">Pythagorean</option>
              <option value="just_major">Just Intonation</option>
              <option value="meantone">Meantone</option>
            </select>
            <span class="hint">Use 12-TET for 99% of applications</span>
          </div>

          <div class="form-group">
            <label>Nut Width (mm)</label>
            <input type="number" v-model.number="params.nutWidth" step="0.5" min="30" max="60" />
          </div>
        </div>
      </div>

      <!-- Step 3: Slot Parameters -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>Fret Slot Parameters</h3>
        <p>Configure slot dimensions for CNC cutting.</p>

        <div class="form-grid">
          <div class="form-group">
            <label>Slot Width (mm)</label>
            <input type="number" v-model.number="params.slotWidth" step="0.05" min="0.3" max="1.5" />
            <span class="hint">Standard: 0.58mm (0.023")</span>
          </div>

          <div class="form-group">
            <label>Slot Depth (mm)</label>
            <input type="number" v-model.number="params.slotDepth" step="0.1" min="0.5" max="3" />
            <span class="hint">Standard: 1.5mm</span>
          </div>

          <div class="form-group">
            <label>Fretboard Radius (mm)</label>
            <input type="number" v-model.number="params.radius" step="1" min="0" max="1000" />
            <span class="hint">0 = flat, 254 = 10", 305 = 12"</span>
          </div>
        </div>

        <div class="tool-recommendation">
          <h4>Recommended Tool:</h4>
          <p>{{ getToolRecommendation() }}</p>
        </div>
      </div>

      <!-- Step 4: Results -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>Fret Positions</h3>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>Calculating...</p>
        </div>

        <div v-else-if="results" class="results">
          <div class="summary">
            <div class="stat">
              <span class="label">Scale Length</span>
              <span class="value">{{ params.scaleLength }}mm</span>
            </div>
            <div class="stat">
              <span class="label">Frets</span>
              <span class="value">{{ params.fretCount }}</span>
            </div>
            <div class="stat">
              <span class="label">12th Fret</span>
              <span class="value">{{ (params.scaleLength / 2).toFixed(2) }}mm</span>
            </div>
          </div>

          <div class="fret-table">
            <table>
              <thead>
                <tr>
                  <th>Fret</th>
                  <th>From Nut (mm)</th>
                  <th>From Saddle (mm)</th>
                  <th>Slot Width</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="fret in results.data?.frets?.slice(0, 12)" :key="fret.fret">
                  <td>{{ fret.fret }}</td>
                  <td>{{ fret.distance_from_nut_mm?.toFixed(3) }}</td>
                  <td>{{ fret.distance_from_saddle_mm?.toFixed(3) }}</td>
                  <td>{{ params.slotWidth }}mm</td>
                </tr>
              </tbody>
            </table>
            <p class="table-note" v-if="params.fretCount > 12">
              Showing frets 1-12 of {{ params.fretCount }}
            </p>
          </div>

          <div class="actions">
            <button @click="downloadCSV" class="btn btn-secondary">
              Download CSV
            </button>
            <button @click="downloadDXF" class="btn btn-primary">
              Download DXF Template
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="wizard-footer">
      <button
        @click="prevStep"
        :disabled="currentStep === 0"
        class="btn btn-secondary"
      >
        Back
      </button>

      <button
        @click="nextStep"
        :disabled="!canProceed"
        class="btn btn-primary"
      >
        {{ currentStep === steps.length - 1 ? 'Finish' : 'Next' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const steps = [
  { label: 'Scale Length' },
  { label: 'Fret Count' },
  { label: 'Slots' },
  { label: 'Results' },
]

const scalePresets = [
  { id: 'fender', name: 'Fender', mm: 648, inches: 25.5 },
  { id: 'gibson', name: 'Gibson', mm: 628.65, inches: 24.75 },
  { id: 'prs', name: 'PRS', mm: 635, inches: 25.0 },
  { id: 'classical', name: 'Classical', mm: 650, inches: 25.6 },
  { id: 'bass', name: 'Bass', mm: 863.6, inches: 34.0 },
  { id: 'baritone', name: 'Baritone', mm: 698.5, inches: 27.5 },
]

const currentStep = ref(0)
const selectedPreset = ref('')
const loading = ref(false)
const results = ref<any>(null)

const params = ref({
  scaleLength: 648,
  fretCount: 22,
  temperament: 'equal_12',
  nutWidth: 43,
  slotWidth: 0.58,
  slotDepth: 1.5,
  radius: 305,
})

const canProceed = computed(() => {
  if (currentStep.value === 0) return params.value.scaleLength > 0
  if (currentStep.value === 1) return params.value.fretCount >= 12
  if (currentStep.value === 2) return params.value.slotWidth > 0
  return true
})

function selectPreset(preset: typeof scalePresets[0]) {
  selectedPreset.value = preset.id
  params.value.scaleLength = preset.mm
}

function getToolRecommendation(): string {
  const width = params.value.slotWidth
  if (width <= 0.58) return '0.023" (0.58mm) fret saw blade or slot cutter'
  if (width <= 0.64) return '0.025" (0.64mm) fret saw blade'
  if (width <= 0.76) return '0.030" (0.76mm) fret saw blade'
  return `${width}mm slot cutter`
}

async function calculateFrets() {
  loading.value = true
  try {
    const response = await fetch('/api/v1/frets/positions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scale_length_mm: params.value.scaleLength,
        fret_count: params.value.fretCount,
        temperament: params.value.temperament,
        nut_width_mm: 0,
      }),
    })
    results.value = await response.json()
  } catch (error) {
    results.value = { ok: false, error: 'Calculation failed' }
  } finally {
    loading.value = false
  }
}

function downloadCSV() {
  if (!results.value?.data?.frets) return

  const lines = ['Fret,From Nut (mm),From Saddle (mm),Slot Width (mm),Slot Depth (mm)']
  for (const fret of results.value.data.frets) {
    lines.push(`${fret.fret},${fret.distance_from_nut_mm?.toFixed(3)},${fret.distance_from_saddle_mm?.toFixed(3)},${params.value.slotWidth},${params.value.slotDepth}`)
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `fretboard_${params.value.scaleLength}mm_${params.value.fretCount}frets.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function downloadDXF() {
  // In a real implementation, this would generate a proper DXF
  // For now, show a message
  alert('DXF generation would be implemented via the CAM API')
}

async function nextStep() {
  if (currentStep.value === 2) {
    currentStep.value++
    await calculateFrets()
  } else if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}
</script>

<style scoped>
.wizard-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  background: var(--color-bg-secondary, #f5f5f5);
  border-radius: 8px;
}

.wizard-header h2 {
  margin: 0 0 1.5rem;
  text-align: center;
}

.step-indicator {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.step::after {
  content: '';
  position: absolute;
  top: 15px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--color-border, #ddd);
}

.step:last-child::after {
  display: none;
}

.step.completed::after {
  background: var(--color-success, #22c55e);
}

.step-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-border, #ddd);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  z-index: 1;
}

.step.active .step-number {
  background: var(--color-primary, #3b82f6);
  color: white;
}

.step.completed .step-number {
  background: var(--color-success, #22c55e);
  color: white;
}

.step-label {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #666);
}

.wizard-content {
  min-height: 350px;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.step-content h3 {
  margin: 0 0 0.5rem;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin: 1rem 0;
}

.preset-btn {
  padding: 1rem;
  border: 2px solid var(--color-border, #ddd);
  border-radius: 8px;
  background: white;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}

.preset-btn:hover {
  border-color: var(--color-primary, #3b82f6);
}

.preset-btn.selected {
  border-color: var(--color-primary, #3b82f6);
  background: var(--color-primary-light, #eff6ff);
}

.preset-btn strong {
  display: block;
  margin-bottom: 0.25rem;
}

.preset-btn span {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #666);
}

.custom-input {
  margin-top: 1.5rem;
}

.custom-input label {
  display: block;
  margin-bottom: 0.5rem;
}

.custom-input input {
  width: 200px;
  padding: 0.5rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-group input,
.form-group select {
  padding: 0.5rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
}

.form-group .hint {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #666);
  margin-top: 0.25rem;
}

.tool-recommendation {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--color-bg-secondary, #f5f5f5);
  border-radius: 4px;
}

.tool-recommendation h4 {
  margin: 0 0 0.5rem;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border, #ddd);
  border-top-color: var(--color-primary, #3b82f6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.summary {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat .label {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #666);
}

.stat .value {
  font-size: 1.25rem;
  font-weight: bold;
}

.fret-table {
  margin: 1rem 0;
  overflow: auto;
}

.fret-table table {
  width: 100%;
  border-collapse: collapse;
}

.fret-table th,
.fret-table td {
  padding: 0.5rem;
  border: 1px solid var(--color-border, #ddd);
  text-align: left;
}

.fret-table th {
  background: var(--color-bg-secondary, #f5f5f5);
  font-weight: 600;
}

.table-note {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #666);
  margin-top: 0.5rem;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.wizard-footer {
  display: flex;
  justify-content: space-between;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-primary, #3b82f6);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark, #2563eb);
}

.btn-secondary {
  background: var(--color-bg-secondary, #e5e7eb);
  color: var(--color-text, #374151);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg-tertiary, #d1d5db);
}
</style>
