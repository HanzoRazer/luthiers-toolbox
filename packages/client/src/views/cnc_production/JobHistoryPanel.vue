<template>
  <section class="job-history-panel">
    <header class="panel-header">
      <h2>Job History</h2>
      <div class="filters">
        <select
          :value="filters.machine_id"
          @change="$emit('update:filters', { ...filters, machine_id: ($event.target as HTMLSelectElement).value })"
        >
          <option value="">
            All Machines
          </option>
          <option
            v-for="m in machines"
            :key="m"
            :value="m"
          >
            {{ m }}
          </option>
        </select>
        <select
          :value="filters.post_id"
          @change="$emit('update:filters', { ...filters, post_id: ($event.target as HTMLSelectElement).value })"
        >
          <option value="">
            All Posts
          </option>
          <option
            v-for="p in posts"
            :key="p"
            :value="p"
          >
            {{ p }}
          </option>
        </select>
        <label class="checkbox-label">
          <input
            :checked="filters.favorites_only"
            type="checkbox"
            @change="$emit('update:filters', { ...filters, favorites_only: ($event.target as HTMLInputElement).checked })"
          >
          Favorites Only
        </label>
      </div>
    </header>

    <div
      v-if="loading"
      class="loading-state"
    >
      <div class="spinner" />
      <p>Loading jobs...</p>
    </div>

    <div
      v-else-if="error"
      class="error-banner"
    >
      {{ error }}
    </div>

    <div
      v-else-if="jobs.length === 0"
      class="empty-state"
    >
      <p>No jobs found. Run a pipeline to create job history.</p>
    </div>

    <table
      v-else
      class="jobs-table"
    >
      <thead>
        <tr>
          <th>
            <input
              type="checkbox"
              :checked="allSelected"
              title="Select all"
              @change="$emit('toggle-select-all')"
            >
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
        <tr
          v-for="job in jobs"
          :key="job.run_id"
          :class="{ selected: isSelected(job.run_id) }"
        >
          <td>
            <input
              type="checkbox"
              :checked="isSelected(job.run_id)"
              @change="$emit('toggle-selection', job.run_id)"
            >
          </td>
          <td>
            <span
              v-if="job.baseline_id"
              class="baseline-badge"
              title="Baseline"
            >📍</span>
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
            <button
              class="icon-button"
              title="View details"
              @click="$emit('view-details', job.run_id)"
            >
              📋
            </button>
            <button
              class="icon-button"
              :title="job.favorite ? 'Remove from favorites' : 'Add to favorites'"
              @click="$emit('toggle-favorite', job.run_id, !job.favorite)"
            >
              {{ job.favorite ? '⭐' : '☆' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
export interface Job {
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

export interface Filters {
  machine_id: string
  post_id: string
  favorites_only: boolean
  limit: number
  offset: number
}

const props = defineProps<{
  jobs: Job[]
  filters: Filters
  loading: boolean
  error: string | null
  selectedRunIds: string[]
  machines: string[]
  posts: string[]
}>()

defineEmits<{
  'update:filters': [filters: Filters]
  'toggle-select-all': []
  'toggle-selection': [runId: string]
  'view-details': [runId: string]
  'toggle-favorite': [runId: string, favorite: boolean]
}>()

const allSelected = computed(() => {
  return props.jobs.length > 0 && props.selectedRunIds.length === props.jobs.length
})

function isSelected(runId: string): boolean {
  return props.selectedRunIds.includes(runId)
}

function formatDate(isoString: string): string {
  if (!isoString) return '—'
  const date = new Date(isoString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

import { computed } from 'vue'
</script>

<style scoped>
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
