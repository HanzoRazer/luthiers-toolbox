<script setup lang="ts">
/**
 * Editable machine profile: envelope, feeds, spindle.
 */
import { CONTROLLER_TYPES, type MachineProfile } from './machineManagerTypes'

defineProps<{
  modelValue: MachineProfile | null
  selectedMachine: MachineProfile | null
  isSaving: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [v: MachineProfile | null]
  save: []
  reset: []
}>()
</script>

<template>
  <section class="panel config-panel">
    <h2>Machine Configuration</h2>
    <div v-if="!selectedMachine" class="empty-state">
      <p>Select a machine to configure</p>
    </div>
    <div v-else-if="modelValue" class="config-form">
      <div class="form-section">
        <h3>Basic Settings</h3>
        <div class="form-group">
          <label>Machine Name</label>
          <input
            :value="modelValue.title"
            type="text"
            @input="emit('update:modelValue', { ...modelValue, title: ($event.target as HTMLInputElement).value })"
          >
        </div>
        <div class="form-group">
          <label>Controller Type</label>
          <select
            :value="modelValue.controller"
            @change="emit('update:modelValue', { ...modelValue, controller: ($event.target as HTMLSelectElement).value })"
          >
            <option v-for="ct in CONTROLLER_TYPES" :key="ct" :value="ct">{{ ct }}</option>
          </select>
        </div>
      </div>

      <div class="form-section">
        <h3>Work Envelope</h3>
        <div class="form-row">
          <div class="form-group">
            <label>X Travel (mm)</label>
            <input
              :value="modelValue.axes.x?.travel"
              type="number"
              @input="emit('update:modelValue', {
                ...modelValue,
                axes: { ...modelValue.axes, x: { travel: Number(($event.target as HTMLInputElement).value) } },
              })"
            >
          </div>
          <div class="form-group">
            <label>Y Travel (mm)</label>
            <input
              :value="modelValue.axes.y?.travel"
              type="number"
              @input="emit('update:modelValue', {
                ...modelValue,
                axes: { ...modelValue.axes, y: { travel: Number(($event.target as HTMLInputElement).value) } },
              })"
            >
          </div>
          <div class="form-group">
            <label>Z Travel (mm)</label>
            <input
              :value="modelValue.axes.z?.travel"
              type="number"
              @input="emit('update:modelValue', {
                ...modelValue,
                axes: { ...modelValue.axes, z: { travel: Number(($event.target as HTMLInputElement).value) } },
              })"
            >
          </div>
        </div>
      </div>

      <div class="form-section">
        <h3>Feed Rates</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Max Feed XY (mm/min)</label>
            <input
              :value="modelValue.limits.max_feed_xy"
              type="number"
              @input="emit('update:modelValue', {
                ...modelValue,
                limits: { ...modelValue.limits, max_feed_xy: Number(($event.target as HTMLInputElement).value) },
              })"
            >
          </div>
          <div class="form-group">
            <label>Max Feed Z (mm/min)</label>
            <input
              :value="modelValue.limits.max_feed_z"
              type="number"
              @input="emit('update:modelValue', {
                ...modelValue,
                limits: { ...modelValue.limits, max_feed_z: Number(($event.target as HTMLInputElement).value) },
              })"
            >
          </div>
          <div class="form-group">
            <label>Rapid (mm/min)</label>
            <input
              :value="modelValue.limits.rapid"
              type="number"
              @input="emit('update:modelValue', {
                ...modelValue,
                limits: { ...modelValue.limits, rapid: Number(($event.target as HTMLInputElement).value) },
              })"
            >
          </div>
        </div>
      </div>

      <div class="form-section">
        <h3>Spindle</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Max RPM</label>
            <input
              :value="modelValue.spindle?.max_rpm"
              type="number"
              @input="emit('update:modelValue', {
                ...modelValue,
                spindle: { ...modelValue.spindle, max_rpm: Number(($event.target as HTMLInputElement).value) },
              })"
            >
          </div>
          <div class="form-group">
            <label>Min RPM</label>
            <input
              :value="modelValue.spindle?.min_rpm"
              type="number"
              @input="emit('update:modelValue', {
                ...modelValue,
                spindle: { ...modelValue.spindle, min_rpm: Number(($event.target as HTMLInputElement).value) },
              })"
            >
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn-secondary" type="button" @click="emit('reset')">
          Reset
        </button>
        <button class="btn-primary" type="button" :disabled="isSaving" @click="emit('save')">
          {{ isSaving ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.panel h2 {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #94a3b8;
  gap: 1rem;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-section h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.75rem;
}

.form-group {
  margin-bottom: 0.75rem;
}

.form-group label {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.btn-secondary:hover {
  background: #e2e8f0;
}
</style>
