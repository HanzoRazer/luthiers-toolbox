<template>
  <div class="wizard-container">
    <div class="wizard-header">
      <h2>Create Manufacturing Job</h2>
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
      <!-- Step 1: Job Type -->
      <div v-if="currentStep === 0" class="step-content">
        <h3>Select Job Type</h3>
        <p>What kind of manufacturing operation?</p>

        <div class="type-grid">
          <button
            v-for="type in jobTypes"
            :key="type.id"
            :class="['type-btn', { selected: job.type === type.id }]"
            @click="job.type = type.id"
          >
            <span class="type-icon">{{ type.icon }}</span>
            <strong>{{ type.name }}</strong>
            <span class="type-desc">{{ type.description }}</span>
          </button>
        </div>
      </div>

      <!-- Step 2: Instrument -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>Instrument Details</h3>

        <div class="form-grid">
          <div class="form-group">
            <label>Instrument Type</label>
            <select v-model="job.instrumentType">
              <option value="acoustic_guitar">Acoustic Guitar</option>
              <option value="electric_guitar">Electric Guitar</option>
              <option value="bass">Bass</option>
              <option value="ukulele">Ukulele</option>
              <option value="mandolin">Mandolin</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div class="form-group">
            <label>Model/Style</label>
            <select v-model="job.model">
              <option value="dreadnought">Dreadnought</option>
              <option value="om">OM/000</option>
              <option value="parlor">Parlor</option>
              <option value="les_paul">Les Paul</option>
              <option value="stratocaster">Stratocaster</option>
              <option value="telecaster">Telecaster</option>
              <option value="custom">Custom</option>
            </select>
          </div>

          <div class="form-group full-width">
            <label>Job Name/Description</label>
            <input type="text" v-model="job.name" placeholder="e.g., Acoustic Dreadnought #42 Body" />
          </div>
        </div>
      </div>

      <!-- Step 3: Materials -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>Material Selection</h3>

        <div class="form-grid">
          <div class="form-group">
            <label>Top Wood</label>
            <select v-model="job.materials.top">
              <option value="">N/A</option>
              <option value="sitka_spruce">Sitka Spruce</option>
              <option value="cedar">Western Red Cedar</option>
              <option value="engelmann">Engelmann Spruce</option>
              <option value="adirondack">Adirondack Spruce</option>
            </select>
          </div>

          <div class="form-group">
            <label>Back/Sides Wood</label>
            <select v-model="job.materials.backSides">
              <option value="">N/A</option>
              <option value="indian_rosewood">Indian Rosewood</option>
              <option value="mahogany">Mahogany</option>
              <option value="maple">Maple</option>
              <option value="koa">Koa</option>
              <option value="walnut">Walnut</option>
            </select>
          </div>

          <div class="form-group">
            <label>Neck Wood</label>
            <select v-model="job.materials.neck">
              <option value="">N/A</option>
              <option value="mahogany">Mahogany</option>
              <option value="maple">Maple</option>
              <option value="walnut">Walnut</option>
            </select>
          </div>

          <div class="form-group">
            <label>Fretboard Wood</label>
            <select v-model="job.materials.fretboard">
              <option value="">N/A</option>
              <option value="ebony">Ebony</option>
              <option value="rosewood">Rosewood</option>
              <option value="maple">Maple</option>
              <option value="pau_ferro">Pau Ferro</option>
            </select>
          </div>
        </div>

        <div class="material-notes">
          <label>Material Notes</label>
          <textarea v-model="job.materials.notes" placeholder="Grade, figure, special considerations..."></textarea>
        </div>
      </div>

      <!-- Step 4: Schedule -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>Priority & Assignment</h3>

        <div class="form-grid">
          <div class="form-group">
            <label>Priority</label>
            <div class="priority-buttons">
              <button
                v-for="p in [1, 2, 3, 4, 5]"
                :key="p"
                :class="['priority-btn', { selected: job.priority === p }]"
                @click="job.priority = p"
              >
                {{ p }}
              </button>
            </div>
            <span class="hint">1 = Urgent, 5 = Low priority</span>
          </div>

          <div class="form-group">
            <label>Customer Reference</label>
            <input type="text" v-model="job.customerRef" placeholder="Optional" />
          </div>

          <div class="form-group full-width">
            <label>Additional Notes</label>
            <textarea v-model="job.notes" placeholder="Any special instructions..."></textarea>
          </div>
        </div>
      </div>

      <!-- Step 5: Review -->
      <div v-if="currentStep === 4" class="step-content">
        <h3>Review & Create</h3>

        <div class="review-card">
          <div class="review-section">
            <h4>Job Details</h4>
            <dl>
              <dt>Name</dt>
              <dd>{{ job.name || 'Untitled Job' }}</dd>
              <dt>Type</dt>
              <dd>{{ getJobTypeName(job.type) }}</dd>
              <dt>Instrument</dt>
              <dd>{{ job.instrumentType }} - {{ job.model }}</dd>
              <dt>Priority</dt>
              <dd>{{ job.priority }} {{ job.priority === 1 ? '(Urgent)' : '' }}</dd>
            </dl>
          </div>

          <div class="review-section">
            <h4>Materials</h4>
            <dl>
              <dt>Top</dt>
              <dd>{{ job.materials.top || 'N/A' }}</dd>
              <dt>Back/Sides</dt>
              <dd>{{ job.materials.backSides || 'N/A' }}</dd>
              <dt>Neck</dt>
              <dd>{{ job.materials.neck || 'N/A' }}</dd>
              <dt>Fretboard</dt>
              <dd>{{ job.materials.fretboard || 'N/A' }}</dd>
            </dl>
          </div>
        </div>

        <div v-if="creating" class="loading">
          <div class="spinner"></div>
          <p>Creating job...</p>
        </div>

        <div v-else-if="created" class="success-message">
          <span class="icon">✓</span>
          <h4>Job Created Successfully!</h4>
          <p>Job ID: <code>{{ created.job_id }}</code></p>
          <button @click="goToJob" class="btn btn-primary">
            Go to Job
          </button>
        </div>
      </div>
    </div>

    <div class="wizard-footer">
      <button
        @click="prevStep"
        :disabled="currentStep === 0 || creating || created"
        class="btn btn-secondary"
      >
        Back
      </button>

      <button
        @click="nextStep"
        :disabled="!canProceed || creating"
        class="btn btn-primary"
      >
        {{ currentStep === steps.length - 1 ? 'Create Job' : 'Next' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const steps = [
  { label: 'Type' },
  { label: 'Instrument' },
  { label: 'Materials' },
  { label: 'Priority' },
  { label: 'Review' },
]

const jobTypes = [
  { id: 'cnc_body', icon: '🎸', name: 'CNC Body', description: 'Body outline, pockets, binding channels' },
  { id: 'cnc_neck', icon: '🎵', name: 'CNC Neck', description: 'Neck carving, fret slots, inlays' },
  { id: 'cnc_bracing', icon: '🔧', name: 'CNC Bracing', description: 'Bracing patterns, scallops' },
  { id: 'assembly', icon: '🔨', name: 'Assembly', description: 'Gluing, binding, setup' },
  { id: 'finishing', icon: '✨', name: 'Finishing', description: 'Sanding, lacquer, buffing' },
  { id: 'custom', icon: '📋', name: 'Custom', description: 'Other operations' },
]

const currentStep = ref(0)
const creating = ref(false)
const created = ref<any>(null)

const job = ref({
  type: '',
  instrumentType: 'acoustic_guitar',
  model: 'dreadnought',
  name: '',
  priority: 2,
  customerRef: '',
  notes: '',
  materials: {
    top: 'sitka_spruce',
    backSides: 'indian_rosewood',
    neck: 'mahogany',
    fretboard: 'ebony',
    notes: '',
  },
})

const canProceed = computed(() => {
  if (currentStep.value === 0) return !!job.value.type
  if (currentStep.value === 1) return !!job.value.instrumentType
  if (currentStep.value === 4) return !created.value
  return true
})

function getJobTypeName(id: string): string {
  return jobTypes.find(t => t.id === id)?.name || id
}

async function createJob() {
  creating.value = true
  try {
    const response = await fetch('/api/v1/jobs/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: job.value.name || `${job.value.model} ${job.value.type}`,
        job_type: job.value.type,
        instrument_type: job.value.instrumentType,
        customer_id: job.value.customerRef || null,
        priority: job.value.priority,
        parameters: {
          model: job.value.model,
          materials: job.value.materials,
          notes: job.value.notes,
        },
      }),
    })
    const result = await response.json()
    if (result.ok) {
      created.value = result.data
    }
  } catch (error) {
    console.error('Failed to create job:', error)
  } finally {
    creating.value = false
  }
}

function goToJob() {
  if (created.value?.job_id) {
    window.location.href = `/jobs/${created.value.job_id}`
  }
}

async function nextStep() {
  if (currentStep.value === steps.length - 1) {
    await createJob()
  } else {
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
  font-size: 0.75rem;
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

.type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin: 1rem 0;
}

.type-btn {
  padding: 1rem;
  border: 2px solid var(--color-border, #ddd);
  border-radius: 8px;
  background: white;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}

.type-btn:hover {
  border-color: var(--color-primary, #3b82f6);
}

.type-btn.selected {
  border-color: var(--color-primary, #3b82f6);
  background: var(--color-primary-light, #eff6ff);
}

.type-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
}

.type-btn strong {
  display: block;
  margin-bottom: 0.25rem;
}

.type-desc {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #666);
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

.form-group.full-width {
  grid-column: span 2;
}

.form-group label {
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.5rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
}

.form-group textarea {
  min-height: 80px;
  resize: vertical;
}

.form-group .hint {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #666);
  margin-top: 0.25rem;
}

.material-notes {
  margin-top: 1rem;
}

.material-notes label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.material-notes textarea {
  width: 100%;
  min-height: 60px;
  padding: 0.5rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
}

.priority-buttons {
  display: flex;
  gap: 0.5rem;
}

.priority-btn {
  width: 40px;
  height: 40px;
  border: 2px solid var(--color-border, #ddd);
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-weight: bold;
}

.priority-btn:hover {
  border-color: var(--color-primary, #3b82f6);
}

.priority-btn.selected {
  border-color: var(--color-primary, #3b82f6);
  background: var(--color-primary, #3b82f6);
  color: white;
}

.review-card {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin: 1rem 0;
}

.review-section h4 {
  margin: 0 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border, #ddd);
}

.review-section dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.25rem 1rem;
  margin: 0;
}

.review-section dt {
  color: var(--color-text-secondary, #666);
}

.review-section dd {
  margin: 0;
  font-weight: 500;
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

.success-message {
  text-align: center;
  padding: 2rem;
}

.success-message .icon {
  display: inline-block;
  width: 60px;
  height: 60px;
  line-height: 60px;
  border-radius: 50%;
  background: var(--color-success-bg, #dcfce7);
  color: var(--color-success, #22c55e);
  font-size: 2rem;
}

.success-message h4 {
  margin: 1rem 0 0.5rem;
}

.success-message code {
  background: var(--color-bg-secondary, #f5f5f5);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
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
