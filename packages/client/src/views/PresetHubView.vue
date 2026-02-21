<template>
  <div :class="styles.presetHub">
    <!-- Header -->
    <div :class="styles.hubHeader">
      <div :class="styles.headerContent">
        <h1>🎛️ Preset Hub</h1>
        <p :class="styles.subtitle">
          Unified CAM, Export, and Neck preset management
        </p>
      </div>
      <div :class="styles.headerActions">
        <button
          :class="styles.btnPrimary"
          @click="showCreateModal = true"
        >
          <span :class="styles.icon">➕</span> New Preset
        </button>
        <button
          :class="styles.btnSecondary"
          :disabled="loading"
          @click="refreshPresets"
        >
          <span :class="styles.icon">🔄</span> Refresh
        </button>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div :class="styles.tabBar">
      <button
        v-for="tab in tabs"
        :key="tab.kind"
        :class="[styles.tabButton, { [styles.tabButtonActive]: activeTab === tab.kind }]"
        @click="activeTab = tab.kind"
      >
        <span :class="styles.tabIcon">{{ tab.icon }}</span>
        <span :class="styles.tabLabel">{{ tab.label }}</span>
        <span
          v-if="getTabCount(tab.kind) > 0"
          :class="styles.tabBadge"
        >
          {{ getTabCount(tab.kind) }}
        </span>
      </button>
    </div>

    <!-- Filters -->
    <div :class="styles.filtersBar">
      <div :class="styles.filterGroup">
        <label>
          <span :class="styles.icon">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search presets..."
            :class="styles.searchInput"
          >
        </label>
      </div>
      <div :class="styles.filterGroup">
        <label>
          <span :class="styles.icon">🏷️</span>
          <select
            v-model="selectedTag"
            :class="styles.tagFilter"
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
      :class="styles.loadingState"
    >
      <div :class="styles.spinner" />
      <p>Loading presets...</p>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="filteredPresets.length === 0"
      :class="styles.emptyState"
    >
      <div :class="styles.emptyIcon">
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
        :class="styles.btnPrimary"
        @click="showCreateModal = true"
      >
        Create Preset
      </button>
    </div>

    <!-- Presets Grid -->
    <div
      v-else
      :class="styles.presetsGrid"
    >
      <div
        v-for="preset in filteredPresets"
        :key="preset.id"
        :class="[styles.presetCard, styles[`presetCardKind${preset.kind.charAt(0).toUpperCase()}${preset.kind.slice(1)}`]]"
      >
        <!-- Card Header -->
        <div :class="styles.cardHeader">
          <div :class="styles.cardTitleRow">
            <h3 :class="styles.cardTitle">
              {{ preset.name }}
            </h3>
            <span
              :class="[styles.kindBadge, styles[`kindBadgeKind${preset.kind.charAt(0).toUpperCase()}${preset.kind.slice(1)}`]]"
            >
              {{ preset.kind.toUpperCase() }}
            </span>
          </div>
          <p
            v-if="preset.description"
            :class="styles.cardDescription"
          >
            {{ preset.description }}
          </p>
        </div>

        <!-- Card Metadata -->
        <div :class="styles.cardMetadata">
          <div
            v-if="preset.machine_id"
            :class="styles.metadataItem"
          >
            <span :class="styles.icon">🔧</span>
            <span>{{ preset.machine_id }}</span>
          </div>
          <div
            v-if="preset.post_id"
            :class="styles.metadataItem"
          >
            <span :class="styles.icon">📝</span>
            <span>{{ preset.post_id }}</span>
          </div>
          <div
            v-if="preset.units"
            :class="styles.metadataItem"
          >
            <span :class="styles.icon">📏</span>
            <span>{{ preset.units }}</span>
          </div>
          <div
            v-if="preset.tags && preset.tags.length > 0"
            :class="styles.metadataItem"
          >
            <span :class="styles.icon">🏷️</span>
            <div :class="styles.tagList">
              <span
                v-for="tag in preset.tags"
                :key="tag"
                :class="styles.tag"
              >{{ tag }}</span>
            </div>
          </div>
        </div>

        <!-- Lineage Info (B20) -->
        <div
          v-if="preset.job_source_id"
          :class="styles.lineageInfo"
          @mouseenter="showJobTooltip(preset, $event)"
          @mouseleave="hideJobTooltip"
        >
          <span :class="styles.icon">🔗</span>
          <span :class="styles.lineageText">Cloned from job {{ preset.job_source_id.slice(0, 8) }}...</span>
          <span
            :class="styles.tooltipHint"
            title="Hover to see job details"
          >ℹ️</span>
        </div>

        <!-- Card Actions -->
        <div :class="styles.cardActions">
          <button
            :class="styles.actionBtn"
            title="Use in PipelineLab"
            @click="useInPipelineLab(preset)"
          >
            <span :class="styles.icon">⚙️</span>
          </button>
          <button
            :class="styles.actionBtn"
            title="Use in CompareLab"
            @click="useInCompareLab(preset)"
          >
            <span :class="styles.icon">🔬</span>
          </button>
          <button
            v-if="preset.kind === 'neck' || preset.kind === 'combo'"
            :class="styles.actionBtn"
            title="Use in NeckLab"
            @click="useInNeckLab(preset)"
          >
            <span :class="styles.icon">🎸</span>
          </button>
          <button
            :class="styles.actionBtn"
            title="Clone"
            @click="clonePreset(preset)"
          >
            <span :class="styles.icon">📋</span>
          </button>
          <button
            :class="styles.actionBtn"
            title="Edit"
            @click="editPreset(preset)"
          >
            <span :class="styles.icon">✏️</span>
          </button>
          <button
            :class="styles.actionBtnDanger"
            title="Delete"
            @click="deletePreset(preset)"
          >
            <span :class="styles.icon">🗑️</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal || editingPreset"
        :class="styles.modalOverlay"
        @click.self="closeModal"
      >
        <div :class="styles.modalContent">
          <div :class="styles.modalHeader">
            <h2>{{ editingPreset ? 'Edit Preset' : 'Create New Preset' }}</h2>
            <button
              :class="styles.closeBtn"
              @click="closeModal"
            >
              ✕
            </button>
          </div>
          <div :class="styles.modalBody">
            <form @submit.prevent="savePreset">
              <!-- Basic Info -->
              <div :class="styles.formGroup">
                <label>Name <span :class="styles.required">*</span></label>
                <input
                  v-model="formData.name"
                  type="text"
                  required
                  :class="styles.formInput"
                >
              </div>

              <div :class="styles.formGroup">
                <label>Kind <span :class="styles.required">*</span></label>
                <select
                  v-model="formData.kind"
                  required
                  :class="styles.formInput"
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

              <div :class="styles.formGroup">
                <label>Description</label>
                <textarea
                  v-model="formData.description"
                  :class="styles.formInput"
                  rows="3"
                />
              </div>

              <div :class="styles.formGroup">
                <label>Tags (comma-separated)</label>
                <input
                  v-model="tagsInput"
                  type="text"
                  placeholder="roughing, adaptive, baseline"
                  :class="styles.formInput"
                >
              </div>

              <!-- Machine/Post (for CAM presets) -->
              <div
                v-if="formData.kind === 'cam' || formData.kind === 'combo'"
                :class="styles.formSection"
              >
                <h3>Machine & Post</h3>
                <div :class="styles.formRow">
                  <div :class="styles.formGroup">
                    <label>Machine ID</label>
                    <input
                      v-model="formData.machine_id"
                      type="text"
                      :class="styles.formInput"
                    >
                  </div>
                  <div :class="styles.formGroup">
                    <label>Post ID</label>
                    <input
                      v-model="formData.post_id"
                      type="text"
                      :class="styles.formInput"
                    >
                  </div>
                </div>
              </div>

              <!-- Export Template (for export presets) -->
              <div
                v-if="formData.kind === 'export' || formData.kind === 'combo'"
                :class="styles.formSection"
              >
                <h3>Export Settings</h3>
                <div :class="styles.formGroup">
                  <label>Filename Template</label>
                  <input
                    v-model="exportTemplate"
                    type="text"
                    placeholder="{preset}__{post}__{date}.nc"
                    :class="styles.formInput"
                  >
                  <small :class="styles.helpText">
                    Tokens: {preset}, {machine}, {post}, {neck_profile}, {neck_section}, {date}
                  </small>
                </div>
              </div>

              <!-- Action Buttons -->
              <div :class="styles.modalActions">
                <button
                  type="button"
                  :class="styles.btnSecondary"
                  @click="closeModal"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :class="styles.btnPrimary"
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
        :class="styles.jobTooltip"
        :style="{ left: tooltipPosition.x + 'px', top: tooltipPosition.y + 'px' }"
      >
        <div :class="styles.tooltipHeader">
          <span :class="styles.icon">📊</span>
          <span>Source Job Performance</span>
        </div>
        <div :class="styles.tooltipBody">
          <div :class="styles.tooltipRow">
            <span :class="styles.label">Job Name:</span>
            <span :class="styles.value">{{ currentJobDetails.job_name || '(unnamed)' }}</span>
          </div>
          <div :class="styles.tooltipRow">
            <span :class="styles.label">Run ID:</span>
            <span :class="styles.valueCode">{{ currentJobDetails.run_id.slice(0, 12) }}...</span>
          </div>
          <div :class="styles.tooltipRow">
            <span :class="styles.label">Machine:</span>
            <span :class="styles.value">{{ currentJobDetails.machine_id || '—' }}</span>
          </div>
          <div :class="styles.tooltipRow">
            <span :class="styles.label">Post:</span>
            <span :class="styles.value">{{ currentJobDetails.post_id || '—' }}</span>
          </div>
          <div :class="styles.tooltipRow">
            <span :class="styles.label">Helical:</span>
            <span
              :class="currentJobDetails.use_helical ? styles.valueSuccess : styles.valueNeutral"
            >
              {{ currentJobDetails.use_helical ? 'Yes' : 'No' }}
            </span>
          </div>
          <div
            v-if="currentJobDetails.sim_time_s != null"
            :class="styles.tooltipRow"
          >
            <span :class="styles.label">Cycle Time:</span>
            <span :class="styles.value">{{ formatTime(currentJobDetails.sim_time_s) }}</span>
          </div>
          <div
            v-if="currentJobDetails.sim_energy_j != null"
            :class="styles.tooltipRow"
          >
            <span :class="styles.label">Energy:</span>
            <span :class="styles.value">{{ formatEnergy(currentJobDetails.sim_energy_j) }}</span>
          </div>
          <div
            v-if="currentJobDetails.sim_issue_count != null"
            :class="styles.tooltipRow"
          >
            <span :class="styles.label">Issues:</span>
            <span
              :class="currentJobDetails.sim_issue_count === 0 ? styles.valueSuccess : styles.valueWarning"
            >
              {{ currentJobDetails.sim_issue_count }}
            </span>
          </div>
          <div
            v-if="currentJobDetails.sim_max_dev_pct != null"
            :class="styles.tooltipRow"
          >
            <span :class="styles.label">Max Deviation:</span>
            <span :class="styles.value">{{ currentJobDetails.sim_max_dev_pct.toFixed(1) }}%</span>
          </div>
          <div :class="styles.tooltipRow">
            <span :class="styles.label">Created:</span>
            <span :class="styles.value">{{ formatDate(currentJobDetails.created_at) }}</span>
          </div>
        </div>
        <div :class="styles.tooltipFooter">
          <button
            :class="styles.tooltipLink"
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
import { api } from '@/services/apiBase'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import styles from './PresetHubView.module.css'

// Composables
import {
  usePresetFilters,
  TAB_CONFIG,
  type Preset,
} from './composables/usePresetFilters'
import { usePresetForm } from './composables/usePresetForm'
import { useJobTooltip } from './composables/useJobTooltip'

const router = useRouter()

// ==========================================================================
// Core State
// ==========================================================================

const presets = ref<Preset[]>([])
const loading = ref(false)

// ==========================================================================
// Composables Setup
// ==========================================================================

// Filters (tab, search, tag) with persistence
const filters = usePresetFilters(() => presets.value)

// Form (create/edit modal)
const form = usePresetForm(async () => {
  await refreshPresets()
})

// Job tooltip (B20 feature)
const tooltip = useJobTooltip(
  () => presets.value,
  (runId) => {
    // TODO: Navigate to Job Intelligence panel
    console.log('View job:', runId)
  }
)

// Tab configuration (exported from composable)
const tabs = TAB_CONFIG

// ==========================================================================
// Convenience Aliases (for template compatibility)
// ==========================================================================

// Filters
const activeTab = filters.activeTab
const searchQuery = filters.searchQuery
const selectedTag = filters.selectedTag
const availableTags = filters.availableTags
const filteredPresets = filters.filteredPresets
const getTabCount = filters.getTabCount

// Form
const showCreateModal = form.showCreateModal
const editingPreset = form.editingPreset
const saving = form.saving
const formData = form.formData
const tagsInput = form.tagsInput
const exportTemplate = form.exportTemplate
const savePreset = form.savePreset
const closeModal = form.closeModal
const editPreset = form.editPreset
const clonePreset = form.clonePreset

// Tooltip
const hoveredPresetId = tooltip.hoveredPresetId
const tooltipPosition = tooltip.tooltipPosition
const currentJobDetails = tooltip.currentJobDetails
const showJobTooltip = tooltip.showJobTooltip
const hideJobTooltip = tooltip.hideJobTooltip
const viewJobInHistory = tooltip.viewJobInHistory
const formatTime = tooltip.formatTime
const formatEnergy = tooltip.formatEnergy
const formatDate = tooltip.formatDate

// ==========================================================================
// Methods
// ==========================================================================

async function refreshPresets() {
  loading.value = true
  try {
    const response = await api('/api/presets')
    presets.value = await response.json()
  } catch (error) {
    console.error('Failed to load presets:', error)
    alert('Failed to load presets. Check console for details.')
  } finally {
    loading.value = false
  }
}

async function deletePreset(preset: Preset) {
  if (!confirm(`Delete preset "${preset.name}"? This cannot be undone.`)) {
    return
  }

  try {
    const response = await api(`/api/presets/${preset.id}`, {
      method: 'DELETE',
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

function useInPipelineLab(preset: Preset) {
  router.push({
    path: '/lab/pipeline',
    query: { preset_id: preset.id },
  })
}

function useInCompareLab(preset: Preset) {
  router.push({
    path: '/lab/compare',
    query: { preset_id: preset.id },
  })
}

function useInNeckLab(preset: Preset) {
  router.push({
    path: '/lab/neck',
    query: { preset_id: preset.id },
  })
}

// ==========================================================================
// Lifecycle
// ==========================================================================

onMounted(() => {
  filters.loadPersistedState()
  refreshPresets()
})
</script>
