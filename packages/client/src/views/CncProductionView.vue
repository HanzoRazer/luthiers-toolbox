<template>
  <div class="cnc-production-view">
    <header class="view-header">
      <div>
        <h1>CNC Production Hub</h1>
        <p class="subtitle">
          Job history, comparison, and preset management
        </p>
      </div>
    </header>

    <div class="view-grid">
      <!-- Job History Table with Multi-Select -->
      <JobHistoryPanel
        :jobs="jobs"
        :filters="filters"
        :loading="loadingJobs"
        :error="jobsError"
        :selected-run-ids="selectedRunIds"
        :machines="machines"
        :posts="posts"
        @update:filters="handleFiltersUpdate"
        @toggle-select-all="toggleSelectAll"
        @toggle-selection="toggleSelection"
        @view-details="viewDetails"
        @toggle-favorite="toggleFavorite"
      />

      <!-- Compare Runs Panel -->
      <CompareRunsPanel
        :selected-run-ids="selectedRunIds"
        @clear-selection="clearSelection"
        @set-baseline="handleSetBaseline"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted } from 'vue'
import CompareRunsPanel from '@/cnc_production/CompareRunsPanel.vue'
import JobHistoryPanel, { type Job, type Filters } from './cnc_production/JobHistoryPanel.vue'

const jobs = ref<Job[]>([])
const selectedRunIds = ref<string[]>([])
const loadingJobs = ref(false)
const jobsError = ref<string | null>(null)

const filters = ref({
  machine_id: '',
  post_id: '',
  favorites_only: false,
  limit: 50,
  offset: 0,
})

const machines = ref<string[]>(['GRBL', 'Mach4', 'LinuxCNC', 'PathPilot', 'MASSO'])
const posts = ref<string[]>(['GRBL', 'Mach4', 'LinuxCNC', 'PathPilot', 'MASSO', 'Haas'])

const allSelected = computed(() => jobs.value.length > 0 && selectedRunIds.value.length === jobs.value.length)

function handleFiltersUpdate(newFilters: Filters) {
  filters.value = newFilters
  loadJobs()
}

onMounted(() => {
  loadJobs()
})

async function loadJobs() {
  loadingJobs.value = true
  jobsError.value = null

  try {
    const params = new URLSearchParams()
    if (filters.value.machine_id) params.append('machine_id', filters.value.machine_id)
    if (filters.value.post_id) params.append('post_id', filters.value.post_id)
    if (filters.value.favorites_only) params.append('favorites_only', 'true')
    params.append('limit', filters.value.limit.toString())
    params.append('offset', filters.value.offset.toString())

    const response = await api(`/api/jobint/log?${params}`)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()
    jobs.value = data.items || []
  } catch (e: any) {
    jobsError.value = `Failed to load jobs: ${e.message}`
    console.error(e)
  } finally {
    loadingJobs.value = false
  }
}

function toggleSelection(runId: string) {
  const idx = selectedRunIds.value.indexOf(runId)
  if (idx >= 0) {
    selectedRunIds.value.splice(idx, 1)
  } else {
    if (selectedRunIds.value.length >= 4) {
      alert('Maximum 4 jobs can be compared at once')
      return
    }
    selectedRunIds.value.push(runId)
  }
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedRunIds.value = []
  } else {
    selectedRunIds.value = jobs.value.slice(0, 4).map((j: Job) => j.run_id)
  }
}

function clearSelection() {
  selectedRunIds.value = []
}

async function toggleFavorite(runId: string, favorite: boolean) {
  try {
    const response = await api(`/api/jobint/favorites/${runId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ favorite }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    // Reload jobs to reflect change
    await loadJobs()
  } catch (e: any) {
    alert(`Failed to update favorite: ${e.message}`)
  }
}

function viewDetails(runId: string) {
  // Navigate to job details view (to be implemented)
  console.log('View details for', runId)
}

async function handleSetBaseline(runId: string) {
  // Reload jobs to show updated baseline indicator
  await loadJobs()
}

</script>

<style scoped>
.cnc-production-view {
  min-height: 100vh;
  background: #f3f4f6;
  padding: 2rem;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.subtitle {
  color: #6b7280;
  margin-top: 0.5rem;
}

.view-grid {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}
</style>
