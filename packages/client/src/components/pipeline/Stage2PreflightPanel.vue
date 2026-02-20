<template>
  <div class="stage-panel">
    <h2>🔍 Stage 2: Preflight Validation</h2>

    <div
      v-if="report"
      class="preflight-results"
    >
      <!-- Status Badge -->
      <div
        class="status-badge"
        :class="report.passed ? 'passed' : 'failed'"
      >
        <span class="status-icon">{{ report.passed ? '✅' : '❌' }}</span>
        <span class="status-text">{{ report.passed ? 'PASSED' : 'FAILED' }}</span>
      </div>

      <!-- Summary Stats -->
      <div class="summary-grid">
        <div class="stat-card error">
          <div class="stat-value">
            {{ report.summary.errors }}
          </div>
          <div class="stat-label">
            ERRORS
          </div>
        </div>
        <div class="stat-card warning">
          <div class="stat-value">
            {{ report.summary.warnings }}
          </div>
          <div class="stat-label">
            WARNINGS
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">
            {{ report.summary.info }}
          </div>
          <div class="stat-label">
            INFO
          </div>
        </div>
        <div class="stat-card neutral">
          <div class="stat-value">
            {{ report.total_entities }}
          </div>
          <div class="stat-label">
            ENTITIES
          </div>
        </div>
      </div>

      <!-- Issues List -->
      <div
        v-if="report.issues.length > 0"
        class="issues-section"
      >
        <h3>Issues ({{ report.issues.length }})</h3>
        <div
          v-for="(issue, idx) in report.issues"
          :key="idx"
          class="issue-item"
          :class="issue.severity.toLowerCase()"
        >
          <div class="issue-header">
            <span class="issue-badge">{{ issue.severity }}</span>
            <span class="issue-category">[{{ issue.category }}]</span>
            <span
              v-if="issue.layer"
              class="issue-layer"
            >Layer: {{ issue.layer }}</span>
          </div>
          <div class="issue-message">
            {{ issue.message }}
          </div>
          <div
            v-if="issue.suggestion"
            class="issue-suggestion"
          >
            💡 {{ issue.suggestion }}
          </div>
        </div>
      </div>

      <!-- Entity Stats -->
      <div
        v-if="report.stats?.entity_types"
        class="entity-stats"
      >
        <h3>Entity Types</h3>
        <div class="entity-grid">
          <div
            v-for="(count, type) in report.stats.entity_types"
            :key="type"
            class="entity-chip"
          >
            <span class="entity-type">{{ type }}</span>
            <span class="entity-count">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="action-buttons">
        <button
          class="btn btn-secondary"
          @click="emit('download')"
        >
          📄 Download HTML Report
        </button>
        <button
          class="btn btn-primary"
          :disabled="hasErrors"
          @click="emit('continue')"
        >
          {{ hasErrors ? '❌ Fix Errors First' : '➡️ Continue to Reconstruction' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Types
interface PreflightIssue {
  severity: string
  category: string
  layer?: string
  message: string
  suggestion?: string
}

interface PreflightReport {
  passed: boolean
  summary: {
    errors: number
    warnings: number
    info: number
  }
  total_entities: number
  issues: PreflightIssue[]
  stats?: {
    entity_types?: Record<string, number>
  }
}

// Props
interface Props {
  report: PreflightReport | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'download': []
  'continue': []
}>()

// Computed
const hasErrors = computed(() => (props.report?.summary.errors ?? 0) > 0)
</script>

<style scoped>
.stage-panel {
  animation: fadeIn 0.3s;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 1.2em;
  font-weight: bold;
}

.status-badge.passed {
  background: #4CAF50;
  color: white;
}

.status-badge.failed {
  background: #f44336;
  color: white;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.stat-card {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  background: #f5f5f5;
}

.stat-card.error { border-left: 4px solid #f44336; }
.stat-card.warning { border-left: 4px solid #ff9800; }
.stat-card.info { border-left: 4px solid #2196F3; }
.stat-card.neutral { border-left: 4px solid #9e9e9e; }

.stat-value {
  font-size: 2.5em;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  color: #666;
  font-size: 0.9em;
}

.issues-section {
  margin: 20px 0;
}

.issue-item {
  border-left: 4px solid #ccc;
  padding: 15px;
  margin: 10px 0;
  background: #f5f5f5;
  border-radius: 4px;
}

.issue-item.error { border-left-color: #f44336; }
.issue-item.warning { border-left-color: #ff9800; }
.issue-item.info { border-left-color: #2196F3; }

.issue-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.issue-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: bold;
  color: white;
  background: #666;
}

.issue-item.error .issue-badge { background: #f44336; }
.issue-item.warning .issue-badge { background: #ff9800; }
.issue-item.info .issue-badge { background: #2196F3; }

.issue-category {
  color: #666;
  font-size: 0.9em;
}

.issue-layer {
  color: #666;
  font-size: 0.85em;
  margin-left: auto;
}

.issue-message {
  margin-bottom: 5px;
}

.issue-suggestion {
  margin-top: 10px;
  color: #666;
  font-size: 0.95em;
}

.entity-stats {
  margin: 20px 0;
}

.entity-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.entity-chip {
  display: flex;
  gap: 10px;
  padding: 8px 15px;
  background: #e3f2fd;
  border-radius: 20px;
  font-size: 0.9em;
}

.entity-type {
  font-weight: 500;
}

.entity-count {
  color: #666;
}

.action-buttons {
  display: flex;
  gap: 15px;
  margin: 30px 0;
  justify-content: center;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #2196F3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1976D2;
}

.btn-secondary {
  background: #9e9e9e;
  color: white;
}

.btn-secondary:hover {
  background: #757575;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
