<script setup lang="ts">
/**
 * Machine profiles: list, edit, create, delete.
 */
import { useConfirm } from '@/composables/useConfirm'
import { ref, computed, onMounted, watch } from 'vue'
import {
  MACHINES_API,
  CONTROLLER_TYPES,
  type MachineProfile,
} from './machineManagerTypes'

const { confirm } = useConfirm()

const props = defineProps<{
  modelValue: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [id: string | null]
  error: [message: string]
  success: [message: string]
}>()

const selectedMachineId = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const machines = ref<MachineProfile[]>([])
const isLoadingMachines = ref(false)
const isSaving = ref(false)
const editingProfile = ref<MachineProfile | null>(null)
const showAddMachineModal = ref(false)

const newMachine = ref({
  id: '',
  title: '',
  controller: 'GRBL',
  x_travel: 300,
  y_travel: 300,
  z_travel: 100,
  max_feed_xy: 5000,
  max_feed_z: 2000,
  rapid: 10000,
  max_rpm: 24000,
  min_rpm: 5000,
})

const selectedMachine = computed(
  () => machines.value.find(m => m.id === selectedMachineId.value) || null,
)

onMounted(() => {
  void loadMachines()
})

watch(
  () => props.modelValue,
  (newId) => {
    if (newId) {
      const machine = machines.value.find(m => m.id === newId)
      if (machine) {
        editingProfile.value = JSON.parse(JSON.stringify(machine))
      }
    } else {
      editingProfile.value = null
    }
  },
)

watch(machines, () => {
  const id = props.modelValue
  if (id) {
    const machine = machines.value.find(m => m.id === id)
    if (machine) {
      editingProfile.value = JSON.parse(JSON.stringify(machine))
    }
  }
})

async function loadMachines() {
  isLoadingMachines.value = true
  emit('error', '')

  try {
    const response = await fetch(`${MACHINES_API}/profiles`)
    if (!response.ok) throw new Error('Failed to load machines')
    machines.value = await response.json()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to load machines'
    emit('error', msg)
  } finally {
    isLoadingMachines.value = false
  }
}

async function saveMachine() {
  if (!editingProfile.value) return

  isSaving.value = true
  emit('error', '')

  try {
    const response = await fetch(`${MACHINES_API}/profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editingProfile.value),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to save machine')
    }

    const result = await response.json()
    emit('success', `Machine ${result.status}: ${result.id}`)
    await loadMachines()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to save machine'
    emit('error', msg)
  } finally {
    isSaving.value = false
  }
}

async function createMachine() {
  isSaving.value = true
  emit('error', '')

  try {
    const profile: MachineProfile = {
      id: newMachine.value.id.toLowerCase().replace(/\s+/g, '_'),
      title: newMachine.value.title,
      controller: newMachine.value.controller,
      axes: {
        x: { travel: newMachine.value.x_travel },
        y: { travel: newMachine.value.y_travel },
        z: { travel: newMachine.value.z_travel },
      },
      limits: {
        max_feed_xy: newMachine.value.max_feed_xy,
        max_feed_z: newMachine.value.max_feed_z,
        rapid: newMachine.value.rapid,
      },
      spindle: {
        max_rpm: newMachine.value.max_rpm,
        min_rpm: newMachine.value.min_rpm,
      },
    }

    const response = await fetch(`${MACHINES_API}/profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to create machine')
    }

    showAddMachineModal.value = false
    await loadMachines()
    emit('success', 'Machine created successfully')

    newMachine.value = {
      id: '',
      title: '',
      controller: 'GRBL',
      x_travel: 300,
      y_travel: 300,
      z_travel: 100,
      max_feed_xy: 5000,
      max_feed_z: 2000,
      rapid: 10000,
      max_rpm: 24000,
      min_rpm: 5000,
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to create machine'
    emit('error', msg)
  } finally {
    isSaving.value = false
  }
}

async function deleteMachine(id: string) {
  if (!(await confirm(`Delete machine "${id}"? This cannot be undone.`))) return

  try {
    const response = await fetch(`${MACHINES_API}/profiles/${id}`, {
      method: 'DELETE',
    })

    if (!response.ok) throw new Error('Failed to delete machine')

    if (selectedMachineId.value === id) {
      selectedMachineId.value = null
    }
    await loadMachines()
    emit('success', 'Machine deleted')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to delete machine'
    emit('error', msg)
  }
}

function getWorkArea(machine: MachineProfile): string {
  const x = machine.axes?.x?.travel || 0
  const y = machine.axes?.y?.travel || 0
  return `${x} x ${y} mm`
}

</script>

<template>
  <div class="profile-panels-row">
    <section class="panel machines-panel">
      <div class="panel-header">
        <h2>My Machines</h2>
        <button class="btn-primary btn-sm" type="button" @click="showAddMachineModal = true">
          + Add Machine
        </button>
      </div>

      <div v-if="isLoadingMachines" class="loading">Loading machines...</div>

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
          :class="{ selected: selectedMachineId === machine.id }"
          @click="selectedMachineId = machine.id"
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
            @click.stop="deleteMachine(machine.id)"
          >
            &times;
          </button>
        </div>
      </div>
    </section>

    <section class="panel config-panel">
      <h2>Machine Configuration</h2>
      <div v-if="!selectedMachine" class="empty-state">
        <p>Select a machine to configure</p>
      </div>
      <div v-else-if="editingProfile" class="config-form">
        <div class="form-section">
          <h3>Basic Settings</h3>
          <div class="form-group">
            <label>Machine Name</label>
            <input v-model="editingProfile.title" type="text" />
          </div>
          <div class="form-group">
            <label>Controller Type</label>
            <select v-model="editingProfile.controller">
              <option v-for="ct in CONTROLLER_TYPES" :key="ct" :value="ct">{{ ct }}</option>
            </select>
          </div>
        </div>

        <div class="form-section">
          <h3>Work Envelope</h3>
          <div class="form-row">
            <div class="form-group">
              <label>X Travel (mm)</label>
              <input v-model.number="editingProfile.axes.x!.travel" type="number" />
            </div>
            <div class="form-group">
              <label>Y Travel (mm)</label>
              <input v-model.number="editingProfile.axes.y!.travel" type="number" />
            </div>
            <div class="form-group">
              <label>Z Travel (mm)</label>
              <input v-model.number="editingProfile.axes.z!.travel" type="number" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3>Feed Rates</h3>
          <div class="form-row">
            <div class="form-group">
              <label>Max Feed XY (mm/min)</label>
              <input v-model.number="editingProfile.limits.max_feed_xy" type="number" />
            </div>
            <div class="form-group">
              <label>Max Feed Z (mm/min)</label>
              <input v-model.number="editingProfile.limits.max_feed_z" type="number" />
            </div>
            <div class="form-group">
              <label>Rapid (mm/min)</label>
              <input v-model.number="editingProfile.limits.rapid" type="number" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3>Spindle</h3>
          <div class="form-row">
            <div class="form-group">
              <label>Max RPM</label>
              <input v-model.number="editingProfile.spindle!.max_rpm" type="number" />
            </div>
            <div class="form-group">
              <label>Min RPM</label>
              <input v-model.number="editingProfile.spindle!.min_rpm" type="number" />
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button
            class="btn-secondary"
            type="button"
            @click="editingProfile = JSON.parse(JSON.stringify(selectedMachine))"
          >
            Reset
          </button>
          <button class="btn-primary" type="button" :disabled="isSaving" @click="saveMachine">
            {{ isSaving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </section>

    <div v-if="showAddMachineModal" class="modal-overlay" @click.self="showAddMachineModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Add New Machine</h3>
          <button class="btn-icon" type="button" @click="showAddMachineModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Machine ID (unique)</label>
            <input v-model="newMachine.id" type="text" placeholder="e.g., shapeoko_pro" />
          </div>
          <div class="form-group">
            <label>Display Name</label>
            <input v-model="newMachine.title" type="text" placeholder="e.g., Shapeoko Pro XL" />
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
              <input v-model.number="newMachine.x_travel" type="number" />
            </div>
            <div class="form-group">
              <label>Y Travel (mm)</label>
              <input v-model.number="newMachine.y_travel" type="number" />
            </div>
            <div class="form-group">
              <label>Z Travel (mm)</label>
              <input v-model.number="newMachine.z_travel" type="number" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" type="button" @click="showAddMachineModal = false">Cancel</button>
          <button
            class="btn-primary"
            type="button"
            :disabled="!newMachine.id || !newMachine.title || isSaving"
            @click="createMachine"
          >
            {{ isSaving ? 'Creating...' : 'Create Machine' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-panels-row {
  display: contents;
}

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
