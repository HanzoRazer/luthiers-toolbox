<script setup lang="ts">
/**
 * Machine list, delete, and add-machine modal.
 */
import { ref } from 'vue'
import {
  CONTROLLER_TYPES,
  type MachineProfile,
  type NewMachineDraft,
  defaultNewMachineDraft,
} from './machineManagerTypes'

defineProps<{
  modelValue: string | null
  machines: MachineProfile[]
  isLoadingMachines: boolean
  isSaving: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [id: string | null]
  delete: [id: string]
  create: [draft: NewMachineDraft]
}>()

const showAddMachineModal = ref(false)
const newMachine = ref<NewMachineDraft>(defaultNewMachineDraft())

function getWorkArea(machine: MachineProfile): string {
  const x = machine.axes?.x?.travel || 0
  const y = machine.axes?.y?.travel || 0
  return `${x} x ${y} mm`
}

function onCreate() {
  emit('create', { ...newMachine.value })
}

function closeModal() {
  showAddMachineModal.value = false
}

function resetAddModal() {
  showAddMachineModal.value = false
  newMachine.value = defaultNewMachineDraft()
}

defineExpose({ resetAddModal })
</script>

<template>
  <section class="panel machines-panel">
    <div class="panel-header">
      <h2>My Machines</h2>
      <button class="btn-primary btn-sm" type="button" @click="showAddMachineModal = true">
        + Add Machine
      </button>
    </div>

    <div v-if="isLoadingMachines" class="loading">
      Loading machines...
    </div>

    <div v-else-if="machines.length === 0" class="empty-state">
      <p>No machines configured</p>
      <button class="btn-secondary" type="button" @click="showAddMachineModal = true">
        Add your first machine
      </button>
    </div>

    <div v-else class="machine-list">
      <div
        v-for="machine in machines"
        :key="machine.id"
        class="machine-card"
        :class="{ selected: modelValue === machine.id }"
        @click="emit('update:modelValue', machine.id)"
      >
        <div class="machine-icon">
          <span>CNC</span>
        </div>
        <div class="machine-info">
          <h3>{{ machine.title || machine.id }}</h3>
          <div class="machine-meta">
            <span>{{ machine.controller }}</span>
            <span class="separator">|</span>
            <span>{{ getWorkArea(machine) }}</span>
          </div>
        </div>
        <button
          class="btn-icon btn-delete"
          type="button"
          title="Delete"
          @click.stop="emit('delete', machine.id)"
        >
          &times;
        </button>
      </div>
    </div>

    <div v-if="showAddMachineModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>Add New Machine</h3>
          <button class="btn-icon" type="button" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Machine ID (unique)</label>
            <input v-model="newMachine.id" type="text" placeholder="e.g., shapeoko_pro">
          </div>
          <div class="form-group">
            <label>Display Name</label>
            <input v-model="newMachine.title" type="text" placeholder="e.g., Shapeoko Pro XL">
          </div>
          <div class="form-group">
            <label>Controller</label>
            <select v-model="newMachine.controller">
              <option v-for="ct in CONTROLLER_TYPES" :key="ct" :value="ct">{{ ct }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>X Travel (mm)</label>
              <input v-model.number="newMachine.x_travel" type="number">
            </div>
            <div class="form-group">
              <label>Y Travel (mm)</label>
              <input v-model.number="newMachine.y_travel" type="number">
            </div>
            <div class="form-group">
              <label>Z Travel (mm)</label>
              <input v-model.number="newMachine.z_travel" type="number">
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" type="button" @click="closeModal">Cancel</button>
          <button
            class="btn-primary"
            type="button"
            :disabled="!newMachine.id || !newMachine.title || isSaving"
            @click="onCreate"
          >
            {{ isSaving ? 'Creating...' : 'Create Machine' }}
          </button>
        </div>
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

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel h2 {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 1rem;
}

.panel-header h2 {
  margin-bottom: 0;
}

.loading {
  color: #64748b;
  padding: 2rem;
  text-align: center;
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

.machine-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.machine-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.machine-card:hover {
  border-color: #2563eb;
}

.machine-card.selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.machine-icon {
  width: 48px;
  height: 48px;
  background: #f1f5f9;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
}

.machine-info h3 {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.machine-meta {
  font-size: 0.75rem;
  color: #64748b;
}

.machine-meta .separator {
  margin: 0 0.5rem;
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

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
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

.btn-icon {
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;
  background: #fff;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-icon:hover {
  background: #f1f5f9;
}

.btn-delete {
  color: #dc2626;
  border-color: transparent;
}

.btn-delete:hover {
  background: #fef2f2;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 0.5rem;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  font-size: 1rem;
  font-weight: 600;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
}
</style>
