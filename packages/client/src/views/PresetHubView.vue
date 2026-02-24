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
      <PresetCard
        v-for="preset in filteredPresets"
        :key="preset.id"
        :preset="preset"
        @show-tooltip="showJobTooltip"
        @hide-tooltip="hideJobTooltip"
        @use-pipeline="useInPipelineLab"
        @use-compare="useInCompareLab"
        @use-neck="useInNeckLab"
        @clone="clonePreset"
        @edit="editPreset"
        @delete="deletePreset"
      />
    </div>

    <!-- Create/Edit Modal -->
    <PresetFormModal
      :show="showCreateModal || !!editingPreset"
      :editing-preset="!!editingPreset"
      :saving="saving"
      :form-data="formData"
      :tags-input="tagsInput"
      :export-template="exportTemplate"
      @close="closeModal"
      @save="savePreset"
      @update:form-data="Object.assign(formData, $event)"
      @update:tags-input="tagsInput = $event"
      @update:export-template="exportTemplate = $event"
    />

    <!-- B20: Enhanced Job Source Tooltip -->
    <JobTooltip
      :visible="!!hoveredPresetId"
      :position="tooltipPosition"
      :job-details="currentJobDetails"
      @view-job="viewJobInHistory"
    />
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import styles from './PresetHubView.module.css'
import PresetCard from './preset_hub/PresetCard.vue'
import PresetFormModal from './preset_hub/PresetFormModal.vue'
import JobTooltip from './preset_hub/JobTooltip.vue'

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
