<template>
  <Teleport to="body">
    <div
      v-if="visible && jobDetails"
      :class="styles.jobTooltip"
      :style="{ left: position.x + 'px', top: position.y + 'px' }"
    >
      <div :class="styles.tooltipHeader">
        <span :class="styles.icon">chart</span>
        <span>Source Job Performance</span>
      </div>
      <div :class="styles.tooltipBody">
        <div :class="styles.tooltipRow">
          <span :class="styles.label">Job Name:</span>
          <span :class="styles.value">{{ jobDetails.job_name || '(unnamed)' }}</span>
        </div>
        <div :class="styles.tooltipRow">
          <span :class="styles.label">Run ID:</span>
          <span :class="styles.valueCode">{{ jobDetails.run_id.slice(0, 12) }}...</span>
        </div>
        <div :class="styles.tooltipRow">
          <span :class="styles.label">Machine:</span>
          <span :class="styles.value">{{ jobDetails.machine_id || '—' }}</span>
        </div>
        <div :class="styles.tooltipRow">
          <span :class="styles.label">Post:</span>
          <span :class="styles.value">{{ jobDetails.post_id || '—' }}</span>
        </div>
        <div :class="styles.tooltipRow">
          <span :class="styles.label">Helical:</span>
          <span
            :class="jobDetails.use_helical ? styles.valueSuccess : styles.valueNeutral"
          >
            {{ jobDetails.use_helical ? 'Yes' : 'No' }}
          </span>
        </div>
        <div
          v-if="jobDetails.sim_time_s != null"
          :class="styles.tooltipRow"
        >
          <span :class="styles.label">Cycle Time:</span>
          <span :class="styles.value">{{ formatTime(jobDetails.sim_time_s) }}</span>
        </div>
        <div
          v-if="jobDetails.sim_energy_j != null"
          :class="styles.tooltipRow"
        >
          <span :class="styles.label">Energy:</span>
          <span :class="styles.value">{{ formatEnergy(jobDetails.sim_energy_j) }}</span>
        </div>
        <div
          v-if="jobDetails.sim_issue_count != null"
          :class="styles.tooltipRow"
        >
          <span :class="styles.label">Issues:</span>
          <span
            :class="jobDetails.sim_issue_count === 0 ? styles.valueSuccess : styles.valueWarning"
          >
            {{ jobDetails.sim_issue_count }}
          </span>
        </div>
        <div
          v-if="jobDetails.sim_max_dev_pct != null"
          :class="styles.tooltipRow"
        >
          <span :class="styles.label">Max Deviation:</span>
          <span :class="styles.value">{{ jobDetails.sim_max_dev_pct.toFixed(1) }}%</span>
        </div>
        <div :class="styles.tooltipRow">
          <span :class="styles.label">Created:</span>
          <span :class="styles.value">{{ formatDate(jobDetails.created_at) }}</span>
        </div>
      </div>
      <div :class="styles.tooltipFooter">
        <button
          :class="styles.tooltipLink"
          @click="$emit('viewJob', jobDetails.run_id)"
        >
          View in Job History ->
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import styles from '../PresetHubView.module.css'

interface JobDetails {
  job_name?: string
  run_id: string
  machine_id?: string
  post_id?: string
  use_helical?: boolean
  sim_time_s?: number
  sim_energy_j?: number
  sim_issue_count?: number
  sim_max_dev_pct?: number
  created_at?: string
}

defineProps<{
  visible: boolean
  position: { x: number; y: number }
  jobDetails: JobDetails | null
}>()

defineEmits<{
  viewJob: [runId: string]
}>()

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
}

function formatEnergy(joules: number): string {
  if (joules >= 1000000) return `${(joules / 1000000).toFixed(1)} MJ`
  if (joules >= 1000) return `${(joules / 1000).toFixed(1)} kJ`
  return `${joules.toFixed(0)} J`
}

function formatDate(iso?: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString()
  } catch {
    return iso
  }
}
</script>
