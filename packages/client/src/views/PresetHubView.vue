<template>
  <div class="preset-hub">
    <!-- Header -->
    <div class="hub-header">
      <div class="header-content">
        <h1>🎛️ Preset Hub</h1>
        <p class="subtitle">
          Unified CAM, Export, and Neck preset management
        </p>
      </div>
      <div class="header-actions">
        <button
          class="btn-primary"
          @click="showCreateModal = true"
        >
          <span class="icon">➕</span> New Preset
        </button>
        <button
          class="btn-secondary"
          :disabled="loading"
          @click="refreshPresets"
        >
          <span class="icon">🔄</span> Refresh
        </button>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.kind"
        :class="['tab-button', { active: activeTab === tab.kind }]"
        @click="activeTab = tab.kind"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span
          v-if="getTabCount(tab.kind) > 0"
          class="tab-badge"
        >
          {{ getTabCount(tab.kind) }}
        </span>
      </button>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <div class="filter-group">
        <label>
          <span class="icon">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search presets..."
            class="search-input"
          >
        </label>
      </div>
      <div class="filter-group">
        <label>
          <span class="icon">🏷️</span>
          <select
            v-model="selectedTag"
            class="tag-filter"
          >
            <option value="">All Tags</option>
            <option
              v-for="tag in availableTags"
              :key="tag"
              :value="tag"
            >
              {{ tag }}
            </option>
          </select>
        </label>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="loading-state"
    >
      <div class="spinner" />
      <p>Loading presets...</p>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="filteredPresets.length === 0"
      class="empty-state"
    >
      <div class="empty-icon">
        📦
      </div>
      <h3>No presets found</h3>
      <p v-if="activeTab === 'all'">
        Create your first preset to get started
      </p>
      <p v-else>
        No {{ activeTab }} presets available
      </p>
      <button
        class="btn-primary"
        @click="showCreateModal = true"
      >
        Create Preset
      </button>
    </div>

    <!-- Presets Grid -->
    <div
      v-else
      class="presets-grid"
    >
      <div
        v-for="preset in filteredPresets"
        :key="preset.id"
        class="preset-card"
        :class="[`kind-${preset.kind}`]"
      >
        <!-- Card Header -->
        <div class="card-header">
          <div class="card-title-row">
            <h3 class="card-title">
              {{ preset.name }}
            </h3>
            <span
              class="kind-badge"
              :class="[`kind-${preset.kind}`]"
            >
              {{ preset.kind.toUpperCase() }}
            </span>
          </div>
          <p
            v-if="preset.description"
            class="card-description"
          >
            {{ preset.description }}
          </p>
        </div>

        <!-- Card Metadata -->
        <div class="card-metadata">
          <div
            v-if="preset.machine_id"
            class="metadata-item"
          >
            <span class="icon">🔧</span>
            <span>{{ preset.machine_id }}</span>
          </div>
          <div
            v-if="preset.post_id"
            class="metadata-item"
          >
            <span class="icon">📝</span>
            <span>{{ preset.post_id }}</span>
          </div>
          <div
            v-if="preset.units"
            class="metadata-item"
          >
            <span class="icon">📏</span>
            <span>{{ preset.units }}</span>
          </div>
          <div
            v-if="preset.tags && preset.tags.length > 0"
            class="metadata-item tags"
          >
            <span class="icon">🏷️</span>
            <div class="tag-list">
              <span
                v-for="tag in preset.tags"
                :key="tag"
                class="tag"
              >{{ tag }}</span>
            </div>
          </div>
        </div>

        <!-- Lineage Info (B20) -->
        <div 
          v-if="preset.job_source_id" 
          class="lineage-info"
          @mouseenter="showJobTooltip(preset, $event)"
          @mouseleave="hideJobTooltip"
        >
          <span class="icon">🔗</span>
          <span class="lineage-text">Cloned from job {{ preset.job_source_id.slice(0, 8) }}...</span>
          <span
            class="tooltip-hint"
            title="Hover to see job details"
          >ℹ️</span>
        </div>

        <!-- Card Actions -->
        <div class="card-actions">
          <button
            class="action-btn"
            title="Use in PipelineLab"
            @click="useInPipelineLab(preset)"
          >
            <span class="icon">⚙️</span>
          </button>
          <button
            class="action-btn"
            title="Use in CompareLab"
            @click="useInCompareLab(preset)"
          >
            <span class="icon">🔬</span>
          </button>
          <button
            v-if="preset.kind === 'neck' || preset.kind === 'combo'"
            class="action-btn"
            title="Use in NeckLab"
            @click="useInNeckLab(preset)"
          >
            <span class="icon">🎸</span>
          </button>
          <button
            class="action-btn"
            title="Clone"
            @click="clonePreset(preset)"
          >
            <span class="icon">📋</span>
          </button>
          <button
            class="action-btn"
            title="Edit"
            @click="editPreset(preset)"
          >
            <span class="icon">✏️</span>
          </button>
          <button
            class="action-btn danger"
            title="Delete"
            @click="deletePreset(preset)"
          >
            <span class="icon">🗑️</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal || editingPreset"
        class="modal-overlay"
        @click.self="closeModal"
      >
        <div class="modal-content">
          <div class="modal-header">
            <h2>{{ editingPreset ? 'Edit Preset' : 'Create New Preset' }}</h2>
            <button
              class="close-btn"
              @click="closeModal"
            >
              ✕
            </button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="savePreset">
              <!-- Basic Info -->
              <div class="form-group">
                <label>Name <span class="required">*</span></label>
                <input
                  v-model="formData.name"
                  type="text"
                  required
                  class="form-input"
                >
              </div>

              <div class="form-group">
                <label>Kind <span class="required">*</span></label>
                <select
                  v-model="formData.kind"
                  required
                  class="form-input"
                >
                  <option value="cam">
                    CAM
                  </option>
                  <option value="export">
                    Export
                  </option>
                  <option value="neck">
                    Neck
                  </option>
                  <option value="combo">
                    Combo
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label>Description</label>
                <textarea
                  v-model="formData.description"
                  class="form-input"
                  rows="3"
                />
              </div>

              <div class="form-group">
                <label>Tags (comma-separated)</label>
                <input
                  v-model="tagsInput"
                  type="text"
                  placeholder="roughing, adaptive, baseline"
                  class="form-input"
                >
              </div>

              <!-- Machine/Post (for CAM presets) -->
              <div
                v-if="formData.kind === 'cam' || formData.kind === 'combo'"
                class="form-section"
              >
                <h3>Machine & Post</h3>
                <div class="form-row">
                  <div class="form-group">
                    <label>Machine ID</label>
                    <input
                      v-model="formData.machine_id"
                      type="text"
                      class="form-input"
                    >
                  </div>
                  <div class="form-group">
                    <label>Post ID</label>
                    <input
                      v-model="formData.post_id"
                      type="text"
                      class="form-input"
                    >
                  </div>
                </div>
              </div>

              <!-- Export Template (for export presets) -->
              <div
                v-if="formData.kind === 'export' || formData.kind === 'combo'"
                class="form-section"
              >
                <h3>Export Settings</h3>
                <div class="form-group">
                  <label>Filename Template</label>
                  <input
                    v-model="exportTemplate"
                    type="text"
                    placeholder="{preset}__{post}__{date}.nc"
                    class="form-input"
                  >
                  <small class="help-text">
                    Tokens: {preset}, {machine}, {post}, {neck_profile}, {neck_section}, {date}
                  </small>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="modal-actions">
                <button
                  type="button"
                  class="btn-secondary"
                  @click="closeModal"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  class="btn-primary"
                  :disabled="saving"
                >
                  {{ saving ? 'Saving...' : (editingPreset ? 'Update' : 'Create') }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- B20: Enhanced Job Source Tooltip -->
    <Teleport to="body">
      <div 
        v-if="hoveredPresetId && currentJobDetails"
        class="job-tooltip"
        :style="{ left: tooltipPosition.x + 'px', top: tooltipPosition.y + 'px' }"
      >
        <div class="tooltip-header">
          <span class="icon">📊</span>
          <span class="tooltip-title">Source Job Performance</span>
        </div>
        <div class="tooltip-body">
          <div class="tooltip-row">
            <span class="label">Job Name:</span>
            <span class="value">{{ currentJobDetails.job_name || '(unnamed)' }}</span>
          </div>
          <div class="tooltip-row">
            <span class="label">Run ID:</span>
            <span class="value code">{{ currentJobDetails.run_id.slice(0, 12) }}...</span>
          </div>
          <div class="tooltip-row">
            <span class="label">Machine:</span>
            <span class="value">{{ currentJobDetails.machine_id || '—' }}</span>
          </div>
          <div class="tooltip-row">
            <span class="label">Post:</span>
            <span class="value">{{ currentJobDetails.post_id || '—' }}</span>
          </div>
          <div class="tooltip-row">
            <span class="label">Helical:</span>
            <span
              class="value"
              :class="currentJobDetails.use_helical ? 'success' : 'neutral'"
            >
              {{ currentJobDetails.use_helical ? 'Yes' : 'No' }}
            </span>
          </div>
          <div
            v-if="currentJobDetails.sim_time_s != null"
            class="tooltip-row"
          >
            <span class="label">Cycle Time:</span>
            <span class="value">{{ formatTime(currentJobDetails.sim_time_s) }}</span>
          </div>
          <div
            v-if="currentJobDetails.sim_energy_j != null"
            class="tooltip-row"
          >
            <span class="label">Energy:</span>
            <span class="value">{{ formatEnergy(currentJobDetails.sim_energy_j) }}</span>
          </div>
          <div
            v-if="currentJobDetails.sim_issue_count != null"
            class="tooltip-row"
          >
            <span class="label">Issues:</span>
            <span
              class="value"
              :class="currentJobDetails.sim_issue_count === 0 ? 'success' : 'warning'"
            >
              {{ currentJobDetails.sim_issue_count }}
            </span>
          </div>
          <div
            v-if="currentJobDetails.sim_max_dev_pct != null"
            class="tooltip-row"
          >
            <span class="label">Max Deviation:</span>
            <span class="value">{{ currentJobDetails.sim_max_dev_pct.toFixed(1) }}%</span>
          </div>
          <div class="tooltip-row">
            <span class="label">Created:</span>
            <span class="value">{{ formatDate(currentJobDetails.created_at) }}</span>
          </div>
        </div>
        <div class="tooltip-footer">
          <button
            class="tooltip-link"
            @click="viewJobInHistory(currentJobDetails.run_id)"
          >
            View in Job History →
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// State persistence keys
const STORAGE_KEYS = {
  ACTIVE_TAB: 'presethub.activeTab',
  SEARCH_QUERY: 'presethub.searchQuery',
  SELECTED_TAG: 'presethub.selectedTag'
}

// Tab configuration
const tabs = [
  { kind: 'all', label: 'All', icon: '📚' },
  { kind: 'cam', label: 'CAM', icon: '⚙️' },
  { kind: 'export', label: 'Export', icon: '📤' },
  { kind: 'neck', label: 'Neck', icon: '🎸' },
  { kind: 'combo', label: 'Combo', icon: '🎯' }
]

// State
const activeTab = ref<string>('all')
const presets = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const selectedTag = ref('')
const showCreateModal = ref(false)
const editingPreset = ref<any>(null)
const saving = ref(false)

// Load persisted state
function loadPersistedState() {
  try {
    const savedTab = localStorage.getItem(STORAGE_KEYS.ACTIVE_TAB)
    if (savedTab) activeTab.value = savedTab

    const savedSearch = localStorage.getItem(STORAGE_KEYS.SEARCH_QUERY)
    if (savedSearch) searchQuery.value = savedSearch

    const savedTag = localStorage.getItem(STORAGE_KEYS.SELECTED_TAG)
    if (savedTag) selectedTag.value = savedTag
  } catch (error) {
    console.error('Failed to load persisted state:', error)
  }
}

// Save persisted state
function savePersistedState() {
  try {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_TAB, activeTab.value)
    localStorage.setItem(STORAGE_KEYS.SEARCH_QUERY, searchQuery.value)
    localStorage.setItem(STORAGE_KEYS.SELECTED_TAG, selectedTag.value)
  } catch (error) {
    console.error('Failed to save state:', error)
  }
}

// B20: Job tooltip state
const jobDetailsCache = ref<Record<string, any>>({})
const hoveredPresetId = ref<string | null>(null)
const tooltipPosition = ref({ x: 0, y: 0 })

// Form data
const formData = ref({
  name: '',
  kind: 'cam',
  description: '',
  tags: [],
  machine_id: '',
  post_id: '',
  units: 'mm',
  cam_params: {},
  export_params: {},
  neck_params: {}
})

const tagsInput = ref('')
const exportTemplate = ref('{preset}__{post}__{date}.nc')

// Computed
const availableTags = computed(() => {
  const tagSet = new Set<string>()
  presets.value.forEach(p => {
    if (p.tags) {
      p.tags.forEach((tag: string) => tagSet.add(tag))
    }
  })
  return Array.from(tagSet).sort()
})

const currentJobDetails = computed(() => {
  if (!hoveredPresetId.value) return null
  const preset = presets.value.find(p => p.id === hoveredPresetId.value)
  if (!preset?.job_source_id) return null
  return jobDetailsCache.value[preset.job_source_id] || null
})

const filteredPresets = computed(() => {
  let filtered = presets.value

  // Filter by tab
  if (activeTab.value !== 'all') {
    filtered = filtered.filter(p => p.kind === activeTab.value)
  }

  // Filter by search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p =>
      p.name.toLowerCase().includes(query) ||
      (p.description && p.description.toLowerCase().includes(query))
    )
  }

  // Filter by tag
  if (selectedTag.value) {
    filtered = filtered.filter(p =>
      p.tags && p.tags.includes(selectedTag.value)
    )
  }

  return filtered
})

const getTabCount = (kind: string) => {
  if (kind === 'all') return presets.value.length
  return presets.value.filter(p => p.kind === kind).length
}

// Methods
async function refreshPresets() {
  loading.value = true
  try {
    const response = await fetch('/api/presets')
    presets.value = await response.json()
  } catch (error) {
    console.error('Failed to load presets:', error)
    alert('Failed to load presets. Check console for details.')
  } finally {
    loading.value = false
  }
}

async function fetchJobDetails(runId: string) {
  if (jobDetailsCache.value[runId]) return
  
  try {
    const response = await fetch(`/api/cam/job-int/log/${encodeURIComponent(runId)}`)
    if (response.ok) {
      jobDetailsCache.value[runId] = await response.json()
    }
  } catch (error) {
    console.error('Failed to fetch job details:', error)
  }
}

function showJobTooltip(preset: any, event: MouseEvent) {
  if (!preset.job_source_id) return
  
  hoveredPresetId.value = preset.id
  tooltipPosition.value = {
    x: event.clientX + 15,
    y: event.clientY + 15
  }
  
  fetchJobDetails(preset.job_source_id)
}

function hideJobTooltip() {
  hoveredPresetId.value = null
}

function viewJobInHistory(runId: string) {
  // TODO: Navigate to Job Intelligence panel or open detail view
  console.log('View job:', runId)
  hideJobTooltip()
}

function formatTime(seconds: number): string {
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)} ms`
  if (seconds < 60) return `${seconds.toFixed(2)} s`
  const m = Math.floor(seconds / 60)
  const s = seconds - m * 60
  return `${m}m ${s.toFixed(0)}s`
}

function formatEnergy(joules: number): string {
  if (joules < 1000) return `${joules.toFixed(0)} J`
  return `${(joules / 1000).toFixed(2)} kJ`
}

function formatDate(isoString: string): string {
  if (!isoString) return '—'
  try {
    const date = new Date(isoString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  } catch {
    return isoString
  }
}

async function savePreset() {
  saving.value = true
  try {
    // Parse tags
    (formData.value as any).tags = tagsInput.value
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0)

    // Set export params
    if (formData.value.kind === 'export' || formData.value.kind === 'combo') {
      formData.value.export_params = {
        filename_template: exportTemplate.value
      }
    }

    const url = editingPreset.value
      ? `/api/presets/${editingPreset.value.id}`
      : '/api/presets'
    
    const method = editingPreset.value ? 'PATCH' : 'POST'

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData.value)
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    await refreshPresets()
    closeModal()
  } catch (error) {
    console.error('Failed to save preset:', error)
    alert('Failed to save preset. Check console for details.')
  } finally {
    saving.value = false
  }
}

function closeModal() {
  showCreateModal.value = false
  editingPreset.value = null
  formData.value = {
    name: '',
    kind: 'cam',
    description: '',
    tags: [],
    machine_id: '',
    post_id: '',
    units: 'mm',
    cam_params: {},
    export_params: {},
    neck_params: {}
  }
  tagsInput.value = ''
  exportTemplate.value = '{preset}__{post}__{date}.nc'
}

function editPreset(preset: any) {
  editingPreset.value = preset
  formData.value = {
    name: preset.name,
    kind: preset.kind,
    description: preset.description || '',
    tags: preset.tags || [],
    machine_id: preset.machine_id || '',
    post_id: preset.post_id || '',
    units: preset.units || 'mm',
    cam_params: preset.cam_params || {},
    export_params: preset.export_params || {},
    neck_params: preset.neck_params || {}
  }
  tagsInput.value = (preset.tags || []).join(', ')
  exportTemplate.value = preset.export_params?.filename_template || '{preset}__{post}__{date}.nc'
}

async function clonePreset(preset: any) {
  formData.value = {
    name: `${preset.name} (Copy)`,
    kind: preset.kind,
    description: preset.description || '',
    tags: preset.tags || [],
    machine_id: preset.machine_id || '',
    post_id: preset.post_id || '',
    units: preset.units || 'mm',
    cam_params: preset.cam_params || {},
    export_params: preset.export_params || {},
    neck_params: preset.neck_params || {}
  }
  tagsInput.value = (preset.tags || []).join(', ')
  exportTemplate.value = preset.export_params?.filename_template || '{preset}__{post}__{date}.nc'
  showCreateModal.value = true
}

async function deletePreset(preset: any) {
  if (!confirm(`Delete preset "${preset.name}"? This cannot be undone.`)) {
    return
  }

  try {
    const response = await fetch(`/api/presets/${preset.id}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    await refreshPresets()
  } catch (error) {
    console.error('Failed to delete preset:', error)
    alert('Failed to delete preset. Check console for details.')
  }
}

function useInPipelineLab(preset: any) {
  router.push({
    path: '/lab/pipeline',
    query: { preset_id: preset.id }
  })
}

function useInCompareLab(preset: any) {
  router.push({
    path: '/lab/compare',
    query: { preset_id: preset.id }
  })
}

function useInNeckLab(preset: any) {
  router.push({
    path: '/lab/neck',
    query: { preset_id: preset.id }
  })
}

// Lifecycle
onMounted(() => {
  loadPersistedState()
  refreshPresets()
})

// Watch for state changes and persist
watch([activeTab, searchQuery, selectedTag], () => {
  savePersistedState()
})
</script>

<style scoped>
/* B20: Job Tooltip Styles */
.job-tooltip {
  position: fixed;
  z-index: 9999;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 0;
  min-width: 320px;
  max-width: 400px;
  pointer-events: auto;
  transform: translate(10px, -50%);
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px 8px 0 0;
  font-weight: 600;
  font-size: 14px;
}

.tooltip-header .icon {
  font-size: 16px;
}

.tooltip-body {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.tooltip-row .label {
  color: #666;
  font-weight: 500;
  min-width: 100px;
}

.tooltip-row .value {
  color: #1a1a1a;
  font-weight: 600;
  text-align: right;
}

.tooltip-row .value.code {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 11px;
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
}

.tooltip-row .value.success {
  color: #10b981;
}

.tooltip-row .value.warning {
  color: #f59e0b;
}

.tooltip-row .value.neutral {
  color: #6b7280;
}

.tooltip-footer {
  padding: 12px 16px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
}

.tooltip-link {
  background: transparent;
  border: none;
  color: #667eea;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}

.tooltip-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* Enhanced hover styles for lineage info */
.lineage-info {
  cursor: help;
  transition: background-color 0.2s;
  border-radius: 4px;
  padding: 2px 4px;
}

.lineage-info:hover {
  background-color: rgba(102, 126, 234, 0.1);
}

.tooltip-hint {
  font-size: 12px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.lineage-info:hover .tooltip-hint {
  opacity: 1;
}

/* Existing Styles */
.preset-hub {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

/* Header */
.hub-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.header-content h1 {
  margin: 0;
  font-size: 2rem;
  color: #333;
}

.subtitle {
  margin: 0.25rem 0 0;
  color: #666;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #e0e0e0;
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-size: 1rem;
  color: #666;
  transition: all 0.2s;
}

.tab-button:hover {
  color: #333;
  background: #f5f5f5;
}

.tab-button.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  font-weight: 600;
}

.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.5rem;
  background: #e0e0e0;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.tab-button.active .tab-badge {
  background: #2563eb;
  color: white;
}

/* Filters */
.filters-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  flex: 1;
}

.filter-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.search-input,
.tag-filter {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}

/* States */
.loading-state,
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #666;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid #e0e0e0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem;
  color: #333;
}

/* Presets Grid */
.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.preset-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.25rem;
  transition: all 0.2s;
  border-left: 4px solid #ddd;
}

.preset-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.preset-card.kind-cam {
  border-left-color: #2563eb;
}

.preset-card.kind-export {
  border-left-color: #16a34a;
}

.preset-card.kind-neck {
  border-left-color: #dc2626;
}

.preset-card.kind-combo {
  border-left-color: #9333ea;
}

/* Card Header */
.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.card-title {
  margin: 0;
  font-size: 1.1rem;
  color: #333;
  word-break: break-word;
}

.kind-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}

.kind-badge.kind-cam {
  background: #dbeafe;
  color: #1e40af;
}

.kind-badge.kind-export {
  background: #dcfce7;
  color: #15803d;
}

.kind-badge.kind-neck {
  background: #fee2e2;
  color: #b91c1c;
}

.kind-badge.kind-combo {
  background: #f3e8ff;
  color: #7e22ce;
}

.card-description {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

/* Card Metadata */
.card-metadata {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 1rem 0;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 4px;
}

.metadata-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #555;
}

.metadata-item .icon {
  font-size: 1rem;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.tag {
  padding: 0.125rem 0.5rem;
  background: #e0e0e0;
  border-radius: 12px;
  font-size: 0.75rem;
  color: #555;
}

/* Lineage Info */
.lineage-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
  border-radius: 4px;
  margin: 0.75rem 0;
  font-size: 0.85rem;
  color: #92400e;
}

/* Card Actions */
.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.action-btn {
  flex: 1;
  padding: 0.5rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.25rem;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #e5e7eb;
  transform: scale(1.05);
}

.action-btn.danger:hover {
  background: #fee2e2;
  border-color: #dc2626;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
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
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f3f4f6;
}

.modal-body {
  padding: 1.5rem;
}

/* Form */
.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.required {
  color: #dc2626;
}

.form-input {
  width: 100%;
  padding: 0.625rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}

.form-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.help-text {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: #666;
}

.form-section {
  margin: 1.5rem 0;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 4px;
}

.form-section h3 {
  margin: 0 0 1rem;
  font-size: 1rem;
  color: #333;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}
</style>
