<script setup lang="ts">
/**
 * Teaching Loop Panel — LoRA Training Management
 * 
 * Displays training statistics, readiness, and export controls.
 * Wires to /api/teaching/* endpoints.
 * 
 * @package features/ai_images
 */

import { ref, computed, onMounted } from 'vue';
import {
  getTeachingStats,
  checkTrainingReadiness,
  getWorkflowStatus,
  exportTrainingData,
  type TeachingStats,
  type TrainingReadiness,
  type WorkflowStatus,
} from './api';

// =============================================================================
// STATE
// =============================================================================

const stats = ref<TeachingStats | null>(null);
const readiness = ref<TrainingReadiness | null>(null);
const workflow = ref<WorkflowStatus | null>(null);
const isLoading = ref(false);
const isExporting = ref(false);
const error = ref<string | null>(null);

// Export options
const exportFormat = ref<'kohya' | 'dreambooth' | 'lora'>('kohya');
const minRating = ref(4);

// =============================================================================
// COMPUTED
// =============================================================================

const progressPercent = computed(() => {
  if (!workflow.value) return 0;
  return Math.round(workflow.value.progress);
});

const stageLabel = computed(() => {
  if (!workflow.value) return 'Unknown';
  const labels: Record<string, string> = {
    collecting: 'Collecting Feedback',
    preparing: 'Preparing Data',
    training: 'Training Model',
    evaluating: 'Evaluating Results',
    complete: 'Complete',
    idle: 'Idle',
  };
  return labels[workflow.value.stage] ?? workflow.value.stage;
});

const ratingDistribution = computed(() => {
  if (!stats.value) return [];
  return [5, 4, 3, 2, 1].map(rating => ({
    rating,
    count: stats.value?.ratingDistribution[rating] ?? 0,
  }));
});

const maxRatingCount = computed(() => {
  if (!stats.value) return 1;
  return Math.max(...Object.values(stats.value.ratingDistribution), 1);
});

// =============================================================================
// METHODS
// =============================================================================

async function loadData(): Promise<void> {
  isLoading.value = true;
  error.value = null;
  
  try {
    const [statsData, readinessData, workflowData] = await Promise.all([
      getTeachingStats(),
      checkTrainingReadiness({ targetSamples: 100, minQuality: 4 }),
      getWorkflowStatus(),
    ]);
    
    stats.value = statsData;
    readiness.value = readinessData;
    workflow.value = workflowData;
  } catch (err) {
    error.value = `Failed to load: ${err}`;
  } finally {
    isLoading.value = false;
  }
}

async function handleExport(): Promise<void> {
  isExporting.value = true;
  error.value = null;
  
  try {
    const result = await exportTrainingData({
      format: exportFormat.value,
      minRating: minRating.value,
    });
    
    // Download the exported data
    const link = document.createElement('a');
    link.href = result.downloadUrl;
    link.download = `training_data_${exportFormat.value}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (err) {
    error.value = `Export failed: ${err}`;
  } finally {
    isExporting.value = false;
  }
}

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(loadData);
</script>

<template>
  <div class="teaching-panel">
    <!-- Header -->
    <div class="panel-header">
      <h2>🎓 Teaching Loop</h2>
      <button class="refresh-btn" @click="loadData" :disabled="isLoading">
        🔄
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = null">×</button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="loading">
      <span class="spinner"></span>
      Loading training data...
    </div>

    <template v-else>
      <!-- Workflow Status -->
      <div class="section workflow-status">
        <h3>Workflow Status</h3>
        <div class="status-card">
          <div class="stage">
            <span class="stage-label">{{ stageLabel }}</span>
            <span class="stage-step" v-if="workflow?.currentStep">
              {{ workflow.currentStep }}
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <div class="progress-label">{{ progressPercent }}%</div>
          <div class="time-remaining" v-if="workflow?.estimatedTimeRemaining">
            ~{{ formatTime(workflow.estimatedTimeRemaining) }} remaining
          </div>
        </div>
      </div>

      <!-- Training Readiness -->
      <div class="section readiness" v-if="readiness">
        <h3>Training Readiness</h3>
        <div class="readiness-card" :class="{ ready: readiness.ready }">
          <div class="readiness-status">
            <span class="icon">{{ readiness.ready ? '✅' : '⏳' }}</span>
            <span>{{ readiness.ready ? 'Ready to Train' : 'Not Ready' }}</span>
          </div>
          
          <div class="metrics">
            <div class="metric">
              <span class="value">{{ readiness.metrics.totalSamples }}</span>
              <span class="label">Total Samples</span>
            </div>
            <div class="metric">
              <span class="value">{{ readiness.metrics.highQualitySamples }}</span>
              <span class="label">High Quality</span>
            </div>
            <div class="metric">
              <span class="value">{{ (readiness.metrics.diversityScore * 100).toFixed(0) }}%</span>
              <span class="label">Diversity</span>
            </div>
            <div class="metric">
              <span class="value">{{ readiness.metrics.recommendedEpochs }}</span>
              <span class="label">Rec. Epochs</span>
            </div>
          </div>

          <div class="reasons" v-if="!readiness.ready && readiness.reasons.length">
            <p v-for="(reason, i) in readiness.reasons" :key="i">
              ⚠️ {{ reason }}
            </p>
          </div>

          <div class="recommendations" v-if="readiness.recommendations.length">
            <h4>Recommendations</h4>
            <ul>
              <li v-for="(rec, i) in readiness.recommendations" :key="i">
                {{ rec }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Statistics -->
      <div class="section stats" v-if="stats">
        <h3>Learning Statistics</h3>
        
        <div class="stats-grid">
          <div class="stat-card">
            <span class="value">{{ stats.totalFeedback }}</span>
            <span class="label">Total Feedback</span>
          </div>
          <div class="stat-card positive">
            <span class="value">{{ stats.positiveFeedback }}</span>
            <span class="label">Positive</span>
          </div>
          <div class="stat-card negative">
            <span class="value">{{ stats.negativeFeedback }}</span>
            <span class="label">Negative</span>
          </div>
          <div class="stat-card">
            <span class="value">{{ stats.averageRating.toFixed(1) }}</span>
            <span class="label">Avg Rating</span>
          </div>
        </div>

        <!-- Rating Distribution -->
        <div class="rating-distribution">
          <h4>Rating Distribution</h4>
          <div class="distribution-bars">
            <div v-for="item in ratingDistribution" :key="item.rating" class="bar-row">
              <span class="rating">{{ '★'.repeat(item.rating) }}</span>
              <div class="bar-container">
                <div 
                  class="bar" 
                  :style="{ width: `${(item.count / maxRatingCount) * 100}%` }"
                ></div>
              </div>
              <span class="count">{{ item.count }}</span>
            </div>
          </div>
        </div>

        <!-- Top Prompts -->
        <div class="top-prompts" v-if="stats.topPrompts.length">
          <h4>Top Performing Prompts</h4>
          <div class="prompt-list">
            <div v-for="(prompt, i) in stats.topPrompts.slice(0, 5)" :key="i" class="prompt-item">
              <span class="prompt-text">{{ prompt.prompt }}</span>
              <span class="prompt-stats">
                {{ prompt.avgRating.toFixed(1) }}★ ({{ prompt.count }})
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Section -->
      <div class="section export">
        <h3>Export Training Data</h3>
        <div class="export-controls">
          <div class="control-group">
            <label>Format</label>
            <select v-model="exportFormat">
              <option value="kohya">Kohya SS</option>
              <option value="dreambooth">DreamBooth</option>
              <option value="lora">LoRA</option>
            </select>
          </div>
          <div class="control-group">
            <label>Min Rating</label>
            <select v-model="minRating">
              <option :value="5">5 stars only</option>
              <option :value="4">4+ stars</option>
              <option :value="3">3+ stars</option>
              <option :value="2">2+ stars</option>
              <option :value="1">All rated</option>
            </select>
          </div>
          <button 
            class="export-btn"
            @click="handleExport"
            :disabled="isExporting || !readiness?.metrics.totalSamples"
          >
            <template v-if="isExporting">
              <span class="spinner small"></span>
              Exporting...
            </template>
            <template v-else>
              📦 Export Dataset
            </template>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.teaching-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-panel, #16213e);
  color: var(--text, #e0e0e0);
  overflow-y: auto;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border, #2a3f5f);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  background: var(--bg-panel);
  z-index: 10;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
}

.refresh-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.refresh-btn:disabled {
  opacity: 0.5;
}

.section {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

.section h3 {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--text-dim, #8892a0);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section h4 {
  margin: 16px 0 8px;
  font-size: 12px;
  color: var(--text-dim);
}

.error-banner {
  margin: 12px 16px;
  padding: 10px 16px;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid #f44336;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  color: #f44336;
  font-size: 13px;
}

.loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-dim);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid transparent;
  border-top-color: var(--accent, #4fc3f7);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

.spinner.small {
  width: 14px;
  height: 14px;
  margin: 0 8px 0 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Workflow Status */
.status-card {
  background: var(--bg-input, #0f1629);
  border-radius: 8px;
  padding: 16px;
}

.stage {
  margin-bottom: 12px;
}

.stage-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent);
}

.stage-step {
  display: block;
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 4px;
}

.progress-bar {
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #29b6f6);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-label {
  text-align: center;
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 6px;
}

.time-remaining {
  text-align: center;
  font-size: 11px;
  color: var(--text-dim);
  margin-top: 4px;
}

/* Readiness */
.readiness-card {
  background: var(--bg-input);
  border-radius: 8px;
  padding: 16px;
  border: 2px solid var(--border);
}

.readiness-card.ready {
  border-color: #4caf50;
}

.readiness-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.readiness-status .icon {
  font-size: 20px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.metric {
  text-align: center;
}

.metric .value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: var(--accent);
}

.metric .label {
  font-size: 10px;
  color: var(--text-dim);
  text-transform: uppercase;
}

.reasons p {
  margin: 8px 0;
  font-size: 12px;
  color: #ffc107;
}

.recommendations ul {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: var(--text-dim);
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: var(--bg-input);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.stat-card .value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: var(--text);
}

.stat-card .label {
  font-size: 10px;
  color: var(--text-dim);
  text-transform: uppercase;
}

.stat-card.positive .value { color: #4caf50; }
.stat-card.negative .value { color: #f44336; }

/* Rating Distribution */
.distribution-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-row .rating {
  width: 60px;
  font-size: 10px;
  color: #ffc107;
}

.bar-container {
  flex: 1;
  height: 12px;
  background: var(--border);
  border-radius: 6px;
  overflow: hidden;
}

.bar {
  height: 100%;
  background: var(--accent);
  border-radius: 6px;
  min-width: 4px;
}

.bar-row .count {
  width: 40px;
  text-align: right;
  font-size: 11px;
  color: var(--text-dim);
}

/* Top Prompts */
.prompt-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prompt-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-input);
  border-radius: 6px;
  font-size: 12px;
}

.prompt-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 12px;
}

.prompt-stats {
  color: var(--accent);
  white-space: nowrap;
}

/* Export */
.export-controls {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.control-group label {
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
}

.control-group select {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--text);
  font-size: 13px;
  min-width: 120px;
}

.export-btn {
  background: var(--accent);
  color: black;
  border: none;
  border-radius: 6px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.15s;
}

.export-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 195, 247, 0.3);
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
