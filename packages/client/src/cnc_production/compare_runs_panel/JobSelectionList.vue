<template>
  <div class="job-list">
    <div
      v-for="job in jobs"
      :key="job.run_id"
      class="job-row"
      :class="{ selected: modelValue.includes(job.run_id) }"
    >
      <label class="checkbox-label">
        <input
          type="checkbox"
          :checked="modelValue.includes(job.run_id)"
          :disabled="modelValue.length >= 4 && !modelValue.includes(job.run_id)"
          @change="toggleJob(job.run_id)"
        >
        <div class="job-info">
          <div class="job-name">{{ job.job_name || job.run_id }}</div>
          <div class="job-meta">
            <span>{{ job.machine_id || '—' }}</span>
            <span>{{ job.material || '—' }}</span>
            <span>{{ job.post_id || '—' }}</span>
            <span v-if="job.sim_time_s">{{ formatTime(job.sim_time_s) }}</span>
            <span
              v-if="job.sim_issue_count !== undefined"
              :class="issueClass(job.sim_issue_count)"
            >
              {{ job.sim_issue_count }} issues
            </span>
          </div>
        </div>
      </label>
    </div>

    <p
      v-if="!loading && jobs.length === 0"
      class="empty"
    >
      No jobs found. Run some adaptive pocket or pipeline operations first.
    </p>
  </div>
</template>

<script setup lang="ts">
interface Job {
  run_id: string
  job_name?: string
  machine_id?: string
  material?: string
  post_id?: string
  sim_time_s?: number
  sim_issue_count?: number
}

const props = defineProps<{
  jobs: Job[]
  modelValue: string[]
  loading: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

function toggleJob(runId: string) {
  const current = [...props.modelValue]
  const idx = current.indexOf(runId)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(runId)
  }
  emit('update:modelValue', current)
}

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}m ${secs}s`
}

function issueClass(count: number): string {
  if (count === 0) return 'no-issues'
  if (count <= 2) return 'minor-issues'
  return 'major-issues'
}
</script>

<style scoped>
.job-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.job-row {
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.2s;
}

.job-row.selected {
  border-color: #4f46e5;
  background: #f0f0ff;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  cursor: pointer;
  gap: 12px;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 4px;
  cursor: pointer;
}

.job-info {
  flex: 1;
}

.job-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.job-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.no-issues { color: #059669; font-weight: 500; }
.minor-issues { color: #d97706; }
.major-issues { color: #dc2626; font-weight: 500; }

.empty {
  text-align: center;
  color: #9ca3af;
  padding: 40px 20px;
  font-style: italic;
}
</style>
