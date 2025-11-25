<template>
  <div class="cnc-production-view">
    <header class="view-header">
      <div>
        <h1>CNC Production Hub</h1>
        <p class="subtitle">Job history, comparison, and preset management</p>
      </div>
    </header>

    <div class="view-grid">
      <!-- Job History Table with Multi-Select -->
      <section class="job-history-panel">
        <header class="panel-header">
          <h2>Job History</h2>
          <div class="filters">
            <select v-model="filters.machine_id" @change="loadJobs">
              <option value="">All Machines</option>
              <option v-for="m in machines" :key="m" :value="m">{{ m }}</option>
            </select>
            <select v-model="filters.post_id" @change="loadJobs">
              <option value="">All Posts</option>
              <option v-for="p in posts" :key="p" :value="p">{{ p }}</option>
            </select>
            <label class="checkbox-label">
              <input type="checkbox" v-model="filters.favorites_only" @change="loadJobs" />
              Favorites Only
            </label>
          </div>
        </header>

        <div v-if="loadingJobs" class="loading-state">
          <div class="spinner"></div>
          <p>Loading jobs...</p>
        </div>

        <div v-else-if="jobsError" class="error-banner">
          {{ jobsError }}
        </div>

        <div v-else-if="jobs.length === 0" class="empty-state">
          <p>No jobs found. Run a pipeline to create job history.</p>
        </div>

        <table v-else class="jobs-table">
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  :checked="allSelected"
                  @change="toggleSelectAll"
                  title="Select all"
                />
              </th>
              <th>Job Name</th>
              <th>Machine</th>
              <th>Post</th>
              <th>Time (s)</th>
              <th>Moves</th>
              <th>Issues</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="job in jobs" :key="job.run_id" :class="{ selected: isSelected(job.run_id) }">
              <td>
                <input
                  type="checkbox"
                  :checked="isSelected(job.run_id)"
                  @change="toggleSelection(job.run_id)"
                />
              </td>
              <td>
                <span v-if="job.baseline_id" class="baseline-badge" title="Baseline">📍</span>
                {{ job.job_name || job.run_id.slice(0, 8) }}
              </td>
              <td>{{ job.machine_id || '—' }}</td>
              <td>{{ job.post_id || '—' }}</td>
              <td>{{ job.sim_time_s?.toFixed(2) || '—' }}</td>
              <td>{{ job.sim_move_count || '—' }}</td>
              <td :class="{ warning: job.sim_issue_count && job.sim_issue_count > 0 }">
                {{ job.sim_issue_count || 0 }}
              </td>
              <td>{{ formatDate(job.created_at) }}</td>
              <td>
                <button class="icon-button" @click="viewDetails(job.run_id)" title="View details">
                  📋
                </button>
                <button
                  class="icon-button"
                  @click="toggleFavorite(job.run_id, !job.favorite)"
                  :title="job.favorite ? 'Remove from favorites' : 'Add to favorites'"
                >
                  {{ job.favorite ? '⭐' : '☆' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

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
import { ref, computed, onMounted } from 'vue'
import CompareRunsPanel from '@/components/compare/CompareRunsPanel.vue'

interface Job {
  run_id: string
  job_name?: string
  machine_id?: string
  post_id?: string
  gcode_key?: string
  use_helical: boolean
  favorite: boolean
  baseline_id?: string | null
  sim_time_s?: number
  sim_energy_j?: number
  sim_move_count?: number
  sim_issue_count?: number
  sim_max_dev_pct?: number
  created_at: string
  source: string
}

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

const allSelected = computed(() => {
  return jobs.value.length > 0 && selectedRunIds.value.length === jobs.value.length
})

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

    const response = await fetch(`/api/jobint/log?${params}`)

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

function isSelected(runId: string): boolean {
  return selectedRunIds.value.includes(runId)
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
    const response = await fetch(`/api/jobint/favorites/${runId}`, {
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

function formatDate(isoString: string): string {
  if (!isoString) return '—'
  const date = new Date(isoString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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

.job-history-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.filters {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.filters select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #6b7280;
}

.spinner {
  margin: 0 auto 1rem;
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-banner {
  background: #fee2e2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.jobs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.jobs-table th,
.jobs-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.jobs-table thead th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.jobs-table tbody tr:hover {
  background: #f9fafb;
}

.jobs-table tbody tr.selected {
  background: #dbeafe;
}

.jobs-table td.warning {
  color: #dc2626;
  font-weight: 600;
}

.baseline-badge {
  display: inline-block;
  background: #fef3c7;
  color: #92400e;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  margin-right: 0.5rem;
}

.icon-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1.25rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.icon-button:hover {
  opacity: 1;
}
</style>
