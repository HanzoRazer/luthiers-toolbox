<script setup lang="ts">
/**
 * MachineManagerView - CNC Machine Manager
 * Connected to API endpoints:
 *   GET/POST/DELETE /api/machines/profiles
 *   GET/PUT/DELETE /api/machines/{mid}/tools
 *   GET /api/posts
 */
import { useConfirm } from '@/composables/useConfirm'
import { ref, computed, onMounted, watch } from 'vue'

const { confirm } = useConfirm()

// API bases
const MACHINES_API = '/api/machines'
const POSTS_API = '/api/posts'

// Types
interface MachineProfile {
  id: string
  title: string
  controller: string
  axes: {
    x?: { travel: number }
    y?: { travel: number }
    z?: { travel: number }
  }
  limits: {
    max_feed_xy?: number
    max_feed_z?: number
    rapid?: number
  }
  spindle?: {
    max_rpm?: number
    min_rpm?: number
  }
  post_id_default?: string
}

interface Tool {
  t: number
  name: string
  type: string
  dia_mm: number
  len_mm: number
  holder?: string
  spindle_rpm?: number
  feed_mm_min?: number
  plunge_mm_min?: number
}

interface Post {
  id: string
  name: string
  builtin: boolean
  description: string
}

// Data state
const machines = ref<MachineProfile[]>([])
const tools = ref<Tool[]>([])
const posts = ref<Post[]>([])

// UI state
const selectedMachineId = ref<string | null>(null)
const isLoadingMachines = ref(false)
const isLoadingTools = ref(false)
const isLoadingPosts = ref(false)
const isSaving = ref(false)
const error = ref('')
const successMessage = ref('')

// Form state for editing
const editingProfile = ref<MachineProfile | null>(null)
const showAddMachineModal = ref(false)
const showAddToolModal = ref(false)

// New machine form
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

// New tool form
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

// Computed
const selectedMachine = computed(() =>
  machines.value.find(m => m.id === selectedMachineId.value) || null
)

const controllerTypes = ['GRBL', 'Mach3', 'Mach4', 'LinuxCNC', 'PathPilot', 'MASSO', 'Carbide Motion', 'OnefinityOS']
const toolTypes = ['EM', 'BALL', 'VBIT', 'DRILL', 'CHAMFER', 'SLOT', 'FACE']

// Load data on mount
onMounted(async () => {
  await Promise.all([
    loadMachines(),
    loadPosts(),
  ])
})

// Watch for machine selection changes
watch(selectedMachineId, async (newId) => {
  if (newId) {
    await loadTools(newId)
    const machine = machines.value.find(m => m.id === newId)
    if (machine) {
      editingProfile.value = JSON.parse(JSON.stringify(machine))
    }
  } else {
    tools.value = []
    editingProfile.value = null
  }
})

// API calls
async function loadMachines() {
  isLoadingMachines.value = true
  error.value = ''

  try {
    const response = await fetch(`${MACHINES_API}/profiles`)
    if (!response.ok) throw new Error('Failed to load machines')
    machines.value = await response.json()
  } catch (e: any) {
    error.value = e.message || 'Failed to load machines'
  } finally {
    isLoadingMachines.value = false
  }
}

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
  } catch (e) {
    tools.value = []
  } finally {
    isLoadingTools.value = false
  }
}

async function loadPosts() {
  isLoadingPosts.value = true

  try {
    const response = await fetch(`${POSTS_API}/`)
    if (response.ok) {
      const data = await response.json()
      posts.value = data.posts || []
    }
  } catch (e) {
    console.error('Failed to load posts:', e)
  } finally {
    isLoadingPosts.value = false
  }
}

async function saveMachine() {
  if (!editingProfile.value) return

  isSaving.value = true
  error.value = ''

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
    successMessage.value = `Machine ${result.status}: ${result.id}`
    await loadMachines()

    setTimeout(() => successMessage.value = '', 3000)
  } catch (e: any) {
    error.value = e.message || 'Failed to save machine'
  } finally {
    isSaving.value = false
  }
}

async function createMachine() {
  isSaving.value = true
  error.value = ''

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
    successMessage.value = 'Machine created successfully'
    setTimeout(() => successMessage.value = '', 3000)

    // Reset form
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
  } catch (e: any) {
    error.value = e.message || 'Failed to create machine'
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
    successMessage.value = 'Machine deleted'
    setTimeout(() => successMessage.value = '', 3000)
  } catch (e: any) {
    error.value = e.message || 'Failed to delete machine'
  }
}

async function addTool() {
  if (!selectedMachineId.value) return

  isSaving.value = true
  error.value = ''

  try {
    const response = await fetch(`${MACHINES_API}/${selectedMachineId.value}/tools`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify([newTool.value]),
    })

    if (!response.ok) throw new Error('Failed to add tool')

    showAddToolModal.value = false
    await loadTools(selectedMachineId.value)
    successMessage.value = `Tool T${newTool.value.t} added`
    setTimeout(() => successMessage.value = '', 3000)

    // Increment tool number for next
    newTool.value.t = tools.value.length + 1
  } catch (e: any) {
    error.value = e.message || 'Failed to add tool'
  } finally {
    isSaving.value = false
  }
}

async function deleteTool(tnum: number) {
  if (!selectedMachineId.value) return
  if (!(await confirm(`Delete tool T${tnum}?`))) return

  try {
    const response = await fetch(`${MACHINES_API}/${selectedMachineId.value}/tools/${tnum}`, {
      method: 'DELETE',
    })

    if (!response.ok) throw new Error('Failed to delete tool')

    await loadTools(selectedMachineId.value)
    successMessage.value = `Tool T${tnum} deleted`
    setTimeout(() => successMessage.value = '', 3000)
  } catch (e: any) {
    error.value = e.message || 'Failed to delete tool'
  }
}

async function exportToolsCsv() {
  if (!selectedMachineId.value) return

  window.open(`${MACHINES_API}/${selectedMachineId.value}/tools.csv`, '_blank')
}

function getWorkArea(machine: MachineProfile): string {
  const x = machine.axes?.x?.travel || 0
  const y = machine.axes?.y?.travel || 0
  return `${x} x ${y} mm`
}
</script>

<template>
  <div class="machine-manager-view">
    <header class="view-header">
      <h1>Machine Manager</h1>
      <p class="subtitle">Configure and manage your CNC machines, tools, and post-processors</p>
    </header>

    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = ''" class="dismiss-btn">&times;</button>
    </div>

    <div v-if="successMessage" class="success-banner">
      {{ successMessage }}
    </div>

    <div class="content-grid">
      <!-- Machines List -->
      <section class="panel machines-panel">
        <div class="panel-header">
          <h2>My Machines</h2>
          <button class="btn-primary btn-sm" @click="showAddMachineModal = true">+ Add Machine</button>
        </div>

        <div v-if="isLoadingMachines" class="loading">Loading machines...</div>

        <div v-else-if="machines.length === 0" class="empty-state">
          <p>No machines configured</p>
          <button class="btn-secondary" @click="showAddMachineModal = true">Add your first machine</button>
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
              title="Delete"
              @click.stop="deleteMachine(machine.id)"
            >
              &times;
            </button>
          </div>
        </div>
      </section>

      <!-- Machine Configuration -->
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
              <input type="text" v-model="editingProfile.title" />
            </div>
            <div class="form-group">
              <label>Controller Type</label>
              <select v-model="editingProfile.controller">
                <option v-for="ct in controllerTypes" :key="ct" :value="ct">{{ ct }}</option>
              </select>
            </div>
          </div>

          <div class="form-section">
            <h3>Work Envelope</h3>
            <div class="form-row">
              <div class="form-group">
                <label>X Travel (mm)</label>
                <input type="number" v-model.number="editingProfile.axes.x!.travel" />
              </div>
              <div class="form-group">
                <label>Y Travel (mm)</label>
                <input type="number" v-model.number="editingProfile.axes.y!.travel" />
              </div>
              <div class="form-group">
                <label>Z Travel (mm)</label>
                <input type="number" v-model.number="editingProfile.axes.z!.travel" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3>Feed Rates</h3>
            <div class="form-row">
              <div class="form-group">
                <label>Max Feed XY (mm/min)</label>
                <input type="number" v-model.number="editingProfile.limits.max_feed_xy" />
              </div>
              <div class="form-group">
                <label>Max Feed Z (mm/min)</label>
                <input type="number" v-model.number="editingProfile.limits.max_feed_z" />
              </div>
              <div class="form-group">
                <label>Rapid (mm/min)</label>
                <input type="number" v-model.number="editingProfile.limits.rapid" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3>Spindle</h3>
            <div class="form-row">
              <div class="form-group">
                <label>Max RPM</label>
                <input type="number" v-model.number="editingProfile.spindle!.max_rpm" />
              </div>
              <div class="form-group">
                <label>Min RPM</label>
                <input type="number" v-model.number="editingProfile.spindle!.min_rpm" />
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button class="btn-secondary" @click="editingProfile = JSON.parse(JSON.stringify(selectedMachine))">Reset</button>
            <button class="btn-primary" :disabled="isSaving" @click="saveMachine">
              {{ isSaving ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </div>
      </section>

      <!-- Post-Processors -->
      <section class="panel posts-panel">
        <h2>Post-Processors</h2>
        <div v-if="isLoadingPosts" class="loading">Loading posts...</div>
        <div v-else class="post-list">
          <div v-for="post in posts" :key="post.id" class="post-item">
            <span class="post-name">{{ post.name }}</span>
            <span v-if="post.builtin" class="post-badge">Built-in</span>
            <span v-else class="post-badge custom">Custom</span>
          </div>
        </div>
      </section>

      <!-- Tool Library -->
      <section class="panel tools-panel">
        <div class="panel-header">
          <h2>Tool Library</h2>
          <div class="tool-actions" v-if="selectedMachine">
            <button class="btn-icon" title="Export CSV" @click="exportToolsCsv">CSV</button>
            <button class="btn-primary btn-sm" @click="showAddToolModal = true">+ Add Tool</button>
          </div>
        </div>

        <div v-if="!selectedMachine" class="empty-state small">
          <p>Select a machine to view tools</p>
        </div>
        <div v-else-if="isLoadingTools" class="loading">Loading tools...</div>
        <div v-else-if="tools.length === 0" class="empty-state small">
          <p>No tools configured</p>
          <button class="btn-secondary btn-sm" @click="showAddToolModal = true">Add first tool</button>
        </div>
        <div v-else class="tool-list">
          <div v-for="tool in tools" :key="tool.t" class="tool-item">
            <span class="tool-num">T{{ tool.t }}</span>
            <span class="tool-desc">{{ tool.name }}</span>
            <span class="tool-dia">{{ tool.dia_mm }}mm</span>
            <button class="btn-icon btn-delete" title="Delete" @click="deleteTool(tool.t)">&times;</button>
          </div>
        </div>
      </section>
    </div>

    <!-- Add Machine Modal -->
    <div v-if="showAddMachineModal" class="modal-overlay" @click.self="showAddMachineModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Add New Machine</h3>
          <button class="btn-icon" @click="showAddMachineModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Machine ID (unique)</label>
            <input type="text" v-model="newMachine.id" placeholder="e.g., shapeoko_pro" />
          </div>
          <div class="form-group">
            <label>Display Name</label>
            <input type="text" v-model="newMachine.title" placeholder="e.g., Shapeoko Pro XL" />
          </div>
          <div class="form-group">
            <label>Controller</label>
            <select v-model="newMachine.controller">
              <option v-for="ct in controllerTypes" :key="ct" :value="ct">{{ ct }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>X Travel (mm)</label>
              <input type="number" v-model.number="newMachine.x_travel" />
            </div>
            <div class="form-group">
              <label>Y Travel (mm)</label>
              <input type="number" v-model.number="newMachine.y_travel" />
            </div>
            <div class="form-group">
              <label>Z Travel (mm)</label>
              <input type="number" v-model.number="newMachine.z_travel" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAddMachineModal = false">Cancel</button>
          <button class="btn-primary" :disabled="!newMachine.id || !newMachine.title || isSaving" @click="createMachine">
            {{ isSaving ? 'Creating...' : 'Create Machine' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Add Tool Modal -->
    <div v-if="showAddToolModal" class="modal-overlay" @click.self="showAddToolModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Add New Tool</h3>
          <button class="btn-icon" @click="showAddToolModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Tool Number</label>
              <input type="number" v-model.number="newTool.t" min="1" />
            </div>
            <div class="form-group">
              <label>Type</label>
              <select v-model="newTool.type">
                <option v-for="tt in toolTypes" :key="tt" :value="tt">{{ tt }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Tool Name</label>
            <input type="text" v-model="newTool.name" placeholder="e.g., 6mm Flat Endmill" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Diameter (mm)</label>
              <input type="number" v-model.number="newTool.dia_mm" step="0.1" />
            </div>
            <div class="form-group">
              <label>Length (mm)</label>
              <input type="number" v-model.number="newTool.len_mm" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Spindle RPM</label>
              <input type="number" v-model.number="newTool.spindle_rpm" />
            </div>
            <div class="form-group">
              <label>Feed (mm/min)</label>
              <input type="number" v-model.number="newTool.feed_mm_min" />
            </div>
            <div class="form-group">
              <label>Plunge (mm/min)</label>
              <input type="number" v-model.number="newTool.plunge_mm_min" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAddToolModal = false">Cancel</button>
          <button class="btn-primary" :disabled="!newTool.name || isSaving" @click="addTool">
            {{ isSaving ? 'Adding...' : 'Add Tool' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.machine-manager-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.success-banner {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #059669;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.dismiss-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: inherit;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
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

.empty-state.small {
  padding: 1rem;
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

.post-list,
.tool-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.post-item,
.tool-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.post-name {
  flex: 1;
  color: #1e293b;
}

.post-badge {
  font-size: 0.625rem;
  padding: 0.125rem 0.5rem;
  background: #e2e8f0;
  color: #64748b;
  border-radius: 1rem;
  text-transform: uppercase;
}

.post-badge.custom {
  background: #dbeafe;
  color: #2563eb;
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

/* Modal */
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
