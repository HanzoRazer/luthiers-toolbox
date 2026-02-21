<template>
  <div class="comparison-table-wrapper">
    <table class="comparison-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th
            v-for="(job, idx) in result.jobs"
            :key="job.run_id"
          >
            Job {{ idx + 1 }}
            <div class="job-id">
              {{ job.job_name || job.run_id.slice(0, 8) }}
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="metric-name">
            Machine
          </td>
          <td
            v-for="(val, idx) in result.comparison.machine?.values"
            :key="idx"
          >
            {{ val }}
          </td>
        </tr>
        <tr>
          <td class="metric-name">
            Material
          </td>
          <td
            v-for="(val, idx) in result.comparison.material?.values"
            :key="idx"
          >
            {{ val }}
          </td>
        </tr>
        <tr>
          <td class="metric-name">
            Post Processor
          </td>
          <td
            v-for="(val, idx) in result.comparison.post?.values"
            :key="idx"
          >
            {{ val }}
          </td>
        </tr>
        <tr v-if="result.comparison.predicted_time_s">
          <td class="metric-name">
            Predicted Time
          </td>
          <td
            v-for="(val, idx) in result.comparison.predicted_time_s.values"
            :key="idx"
            :class="winnerClass(idx, result.comparison.predicted_time_s.winner)"
          >
            {{ val !== null ? formatTime(val) : '—' }}
            <span
              v-if="idx === result.comparison.predicted_time_s.winner"
              class="winner-badge"
            >✓</span>
          </td>
        </tr>
        <tr v-if="result.comparison.energy_j">
          <td class="metric-name">
            Energy (J)
          </td>
          <td
            v-for="(val, idx) in result.comparison.energy_j.values"
            :key="idx"
            :class="winnerClass(idx, result.comparison.energy_j.winner)"
          >
            {{ val !== null ? val.toFixed(1) : '—' }}
            <span
              v-if="idx === result.comparison.energy_j.winner"
              class="winner-badge"
            >✓</span>
          </td>
        </tr>
        <tr v-if="result.comparison.move_count">
          <td class="metric-name">
            Move Count
          </td>
          <td
            v-for="(val, idx) in result.comparison.move_count.values"
            :key="idx"
            :class="winnerClass(idx, result.comparison.move_count.winner)"
          >
            {{ val !== null ? val : '—' }}
            <span
              v-if="idx === result.comparison.move_count.winner"
              class="winner-badge"
            >✓</span>
          </td>
        </tr>
        <tr v-if="result.comparison.issue_count">
          <td class="metric-name">
            Issue Count
          </td>
          <td
            v-for="(val, idx) in result.comparison.issue_count.values"
            :key="idx"
            :class="winnerClass(idx, result.comparison.issue_count.winner)"
          >
            {{ val !== null ? val : '—' }}
            <span
              v-if="idx === result.comparison.issue_count.winner"
              class="winner-badge"
            >✓</span>
          </td>
        </tr>
        <tr v-if="result.comparison.max_deviation_pct">
          <td class="metric-name">
            Max Deviation (%)
          </td>
          <td
            v-for="(val, idx) in result.comparison.max_deviation_pct.values"
            :key="idx"
            :class="winnerClass(idx, result.comparison.max_deviation_pct.winner)"
          >
            {{ val !== null ? val.toFixed(2) : '—' }}
            <span
              v-if="idx === result.comparison.max_deviation_pct.winner"
              class="winner-badge"
            >✓</span>
          </td>
        </tr>
        <tr>
          <td class="metric-name">
            Notes
          </td>
          <td
            v-for="(val, idx) in result.comparison.notes?.values"
            :key="idx"
            class="notes-cell"
          >
            {{ val || '—' }}
          </td>
        </tr>
        <tr>
          <td class="metric-name">
            Tags
          </td>
          <td
            v-for="(val, idx) in result.comparison.tags?.values"
            :key="idx"
          >
            <span v-if="val.length === 0">—</span>
            <span
              v-else
              class="tag-list"
            >
              <span
                v-for="tag in val"
                :key="tag"
                class="tag"
              >#{{ tag }}</span>
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
interface ComparisonMetric {
  values: any[]
  winner?: number | null
}

interface ComparisonResult {
  jobs: Array<{ run_id: string; job_name?: string }>
  comparison: {
    machine?: ComparisonMetric
    material?: ComparisonMetric
    post?: ComparisonMetric
    predicted_time_s?: ComparisonMetric
    energy_j?: ComparisonMetric
    move_count?: ComparisonMetric
    issue_count?: ComparisonMetric
    max_deviation_pct?: ComparisonMetric
    notes?: ComparisonMetric
    tags?: { values: string[][] }
  }
}

defineProps<{
  result: ComparisonResult
}>()

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}m ${secs}s`
}

function winnerClass(idx: number, winnerIdx: number | null | undefined): string {
  return idx === winnerIdx ? 'winner' : ''
}
</script>

<style scoped>
.comparison-table-wrapper {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.comparison-table th {
  background: #f9fafb;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #e5e7eb;
}

.comparison-table td {
  padding: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.metric-name {
  font-weight: 500;
  background: #fafafa;
  white-space: nowrap;
}

.job-id {
  font-size: 11px;
  color: #6b7280;
  font-weight: normal;
  margin-top: 2px;
}

.winner {
  background: #d1fae5;
  font-weight: 600;
  position: relative;
}

.winner-badge {
  color: #059669;
  margin-left: 4px;
  font-weight: bold;
}

.notes-cell {
  max-width: 200px;
  white-space: normal;
  word-wrap: break-word;
  font-size: 13px;
}

.tag-list {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag {
  background: #e0e7ff;
  color: #4338ca;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}
</style>
