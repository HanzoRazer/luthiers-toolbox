<script setup lang="ts">
/**
 * Per-machine tool library CRUD and CSV export.
 */
import { useConfirm } from '@/composables/useConfirm'
import { ref, watch } from 'vue'
import { MACHINES_API, TOOL_TYPES, type Tool } from './machineManagerTypes'

const { confirm } = useConfirm()

const props = defineProps<{
  selectedMachineId: string | null
}>()

const emit = defineEmits<{
  error: [message: string]
  success: [message: string]
}>()

const tools = ref<Tool[]>([])
const isLoadingTools = ref(false)
const isSaving = ref(false)
const showAddToolModal = ref(false)

const newTool = ref({
  t: 1,
  name: '',
  type: 'EM',
  dia_mm: 6,
  len_mm: 50,
  spindle_rpm: 18000,
  feed_mm_min: 1500,
  plunge_mm_min: 500,
})

watch(
  () => props.selectedMachineId,
  async (newId) => {
    if (newId) {
      await loadTools(newId)
    } else {
      tools.value = []
    }
  },
  { immediate: true },
)

async function loadTools(machineId: string) {
  isLoadingTools.value = true

  try {
    const response = await fetch(`${MACHINES_API}/${machineId}/tools`)
    if (response.ok) {
      const data = await response.json()
      tools.value = data.tools || []
    } else {
      tools.value = []
    }
  } catch {
    tools.value = []
  } finally {
    isLoadingTools.value = false
  }
}

async function addTool() {
  if (!props.selectedMachineId) return

  isSaving.value = true
  emit('error', '')

  try {
    const response = await fetch(`${MACHINES_API}/${props.selectedMachineId}/tools`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify([newTool.value]),
    })

    if (!response.ok) throw new Error('Failed to add tool')

    showAddToolModal.value = false
    await loadTools(props.selectedMachineId)
    emit('success', `Tool T${newTool.value.t} added`)

    newTool.value.t = tools.value.length + 1
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to add tool'
    emit('error', msg)
  } finally {
    isSaving.value = false
  }
}

async function deleteTool(tnum: number) {
  if (!props.selectedMachineId) return
  if (!(await confirm(`Delete tool T${tnum}?`))) return

  try {
    const response = await fetch(`${MACHINES_API}/${props.selectedMachineId}/tools/${tnum}`, {
      method: 'DELETE',
    })

    if (!response.ok) throw new Error('Failed to delete tool')

    await loadTools(props.selectedMachineId)
    emit('success', `Tool T${tnum} deleted`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to delete tool'
    emit('error', msg)
  }
}

function exportToolsCsv() {
  if (!props.selectedMachineId) return
  window.open(`${MACHINES_API}/${props.selectedMachineId}/tools.csv`, '_blank')
}

</script>

<template>
  <section class="panel tools-panel">
    <div class="panel-header">
      <h2>Tool Library</h2>
      <div v-if="selectedMachineId" class="tool-actions">
        <button class="btn-icon" type="button" title="Export CSV" @click="exportToolsCsv">CSV</button>
        <button class="btn-primary btn-sm" type="button" @click="showAddToolModal = true">+ Add Tool</button>
      </div>
    </div>

    <div v-if="!selectedMachineId" class="empty-state small">
      <p>Select a machine to view tools</p>
    </div>
    <div v-else-if="isLoadingTools" class="loading">Loading tools...</div>
    <div v-else-if="tools.length === 0" class="empty-state small">
      <p>No tools configured</p>
      <button class="btn-secondary btn-sm" type="button" @click="showAddToolModal = true">Add first tool</button>
    </div>
    <div v-else class="tool-list">
      <div v-for="tool in tools" :key="tool.t" class="tool-item">
        <span class="tool-num">T{{ tool.t }}</span>
        <span class="tool-desc">{{ tool.name }}</span>
        <span class="tool-dia">{{ tool.dia_mm }}mm</span>
        <button class="btn-icon btn-delete" type="button" title="Delete" @click="deleteTool(tool.t)">
          &times;
        </button>
      </div>
    </div>

    <div v-if="showAddToolModal" class="modal-overlay" @click.self="showAddToolModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Add New Tool</h3>
          <button class="btn-icon" type="button" @click="showAddToolModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Tool Number</label>
              <input v-model.number="newTool.t" type="number" min="1" />
            </div>
            <div class="form-group">
              <label>Type</label>
              <select v-model="newTool.type">
                <option v-for="tt in TOOL_TYPES" :key="tt" :value="tt">{{ tt }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Tool Name</label>
            <input v-model="newTool.name" type="text" placeholder="e.g., 6mm Flat Endmill" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Diameter (mm)</label>
              <input v-model.number="newTool.dia_mm" type="number" step="0.1" />
            </div>
            <div class="form-group">
              <label>Length (mm)</label>
              <input v-model.number="newTool.len_mm" type="number" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Spindle RPM</label>
              <input v-model.number="newTool.spindle_rpm" type="number" />
            </div>
            <div class="form-group">
              <label>Feed (mm/min)</label>
              <input v-model.number="newTool.feed_mm_min" type="number" />
            </div>
            <div class="form-group">
              <label>Plunge (mm/min)</label>
              <input v-model.number="newTool.plunge_mm_min" type="number" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" type="button" @click="showAddToolModal = false">Cancel</button>
          <button
            class="btn-primary"
            type="button"
            :disabled="!newTool.name || isSaving"
            @click="addTool"
          >
            {{ isSaving ? 'Adding...' : 'Add Tool' }}
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

.empty-state.small {
  padding: 1rem;
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.tool-num {
  font-weight: 600;
  color: #2563eb;
  min-width: 2rem;
}

.tool-desc {
  flex: 1;
  color: #475569;
}

.tool-dia {
  color: #64748b;
  font-size: 0.75rem;
}

.tool-actions {
  display: flex;
  gap: 0.5rem;
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
