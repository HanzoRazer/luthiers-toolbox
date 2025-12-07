<template>
  <div class="cam-job-insights-panel">
    <div class="header">
      <h3>Job Intelligence Analysis</h3>
      <span class="job-id">Job: {{ jobId }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <p>Analyzing job...</p>
    </div>

    <!-- Analysis Results -->
    <div v-else-if="insights" class="insights">
      <!-- Job Info -->
      <div class="info-section">
        <h4>{{ insights.job_name }}</h4>
        <p>
          <strong>Wood:</strong> {{ insights.wood_type }}
          <span class="spacer">|</span>
          <strong>Actual Time:</strong> {{ formatTime(insights.actual_time_s) }}
          <span class="spacer">|</span>
          <strong>Estimated Time:</strong> {{ formatTime(insights.estimated_time_s) }}
        </p>
      </div>

      <!-- Severity Badge -->
      <div class="severity-section">
        <span :class="['severity-badge', insights.severity]">
          {{ insights.severity.toUpperCase() }}
        </span>
        <span class="classification">{{ formatClassification(insights.classification) }}</span>
      </div>

      <!-- Gate/Review Grid -->
      <div class="metrics-grid">
        <div class="metric-card">
          <h5>Review Threshold</h5>
          <div class="percentage" :class="{ warn: insights.review_pct >= 80 }">
            {{ insights.review_pct }}%
          </div>
          <p>{{ insights.review_pct < 80 ? 'Below threshold' : 'At or over threshold' }}</p>
        </div>
        
        <div class="metric-card">
          <h5>Critical Gate</h5>
          <div class="percentage" :class="{ error: insights.gate_pct >= 100 }">
            {{ insights.gate_pct }}%
          </div>
          <p>{{ insights.gate_pct < 100 ? 'Below gate' : 'Exceeds gate' }}</p>
        </div>
      </div>

      <!-- Time Difference -->
      <div v-if="insights.time_diff_pct !== 0" class="time-diff">
        <p>
          Time difference: 
          <strong :class="{ error: Math.abs(insights.time_diff_pct) > 20 }">
            {{ insights.time_diff_pct > 0 ? '+' : '' }}{{ insights.time_diff_pct }}%
          </strong>
          {{ insights.time_diff_pct > 0 ? 'slower' : 'faster' }} than estimated
        </p>
      </div>

      <!-- Recommendation -->
      <div class="recommendation">
        <h5>💡 Recommendation</h5>
        <p>{{ insights.recommendation }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps<{
  jobId: string
}>()

interface Insights {
  job_id: string
  job_name: string
  wood_type: string
  actual_time_s: number
  estimated_time_s: number
  time_diff_pct: number
  classification: string
  severity: string
  review_pct: number
  gate_pct: number
  recommendation: string
}

const insights = ref<Insights | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

onMounted(loadInsights)

async function loadInsights() {
  loading.value = true
  error.value = null
  
  try {
    const res = await fetch(`/api/cam/job_log/insights/${props.jobId}`)
    if (!res.ok) throw new Error('Failed to load insights')
    
    insights.value = await res.json()
  } catch (err) {
    error.value = String(err)
  } finally {
    loading.value = false
  }
}

function formatTime(seconds: number): string {
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return `${min}m ${sec}s`
}

function formatClassification(classification: string): string {
  return classification.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}
</script>

<style scoped>
.cam-job-insights-panel {
  padding: 20px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h3 {
  margin: 0;
}

.job-id {
  color: #666;
  font-size: 14px;
}

.loading,
.error-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.info-section h4 {
  margin: 0 0 10px 0;
}

.info-section p {
  margin: 0;
  color: #666;
}

.spacer {
  margin: 0 10px;
  color: #ddd;
}

.severity-section {
  margin: 20px 0;
  display: flex;
  align-items: center;
  gap: 15px;
}

.severity-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 14px;
}

.severity-badge.ok {
  background: #d4edda;
  color: #155724;
}

.severity-badge.warn {
  background: #fff3cd;
  color: #856404;
}

.severity-badge.error {
  background: #f8d7da;
  color: #721c24;
}

.classification {
  color: #666;
  font-style: italic;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 20px 0;
}

.metric-card {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.metric-card h5 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #666;
}

.percentage {
  font-size: 32px;
  font-weight: 700;
  color: #28a745;
}

.percentage.warn {
  color: #ffc107;
}

.percentage.error {
  color: #dc3545;
}

.metric-card p {
  margin: 10px 0 0 0;
  font-size: 14px;
  color: #666;
}

.time-diff {
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
  margin: 20px 0;
}

.time-diff p {
  margin: 0;
}

.time-diff strong {
  color: #28a745;
}

.time-diff strong.error {
  color: #dc3545;
}

.recommendation {
  margin-top: 20px;
  padding: 15px;
  background: #e7f3ff;
  border-left: 4px solid #007bff;
  border-radius: 4px;
}

.recommendation h5 {
  margin: 0 0 10px 0;
}

.recommendation p {
  margin: 0;
  line-height: 1.6;
}
</style>
