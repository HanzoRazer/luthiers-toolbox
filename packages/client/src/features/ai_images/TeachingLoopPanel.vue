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
} from './api/teaching';
import styles from './TeachingLoopPanel.module.css';

// CSS Module class helper
const readinessCardClass = computed(() => {
  return readiness.value?.ready ? styles.readinessCardReady : styles.readinessCard;
});

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
  const values = Object.values(stats.value.ratingDistribution) as number[];
  return Math.max(...values, 1);
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
  <div :class="styles.teachingPanel">
    <!-- Header -->
    <div :class="styles.panelHeader">
      <h2>🎓 Teaching Loop</h2>
      <button
        :class="styles.refreshBtn"
        :disabled="isLoading"
        @click="loadData"
      >
        🔄
      </button>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      :class="styles.errorBanner"
    >
      {{ error }}
      <button @click="error = null">
        ×
      </button>
    </div>

    <!-- Loading -->
    <div
      v-if="isLoading"
      :class="styles.loading"
    >
      <span :class="styles.spinner" />
      Loading training data...
    </div>

    <template v-else>
      <!-- Workflow Status -->
      <div :class="styles.workflowStatus">
        <h3>Workflow Status</h3>
        <div :class="styles.statusCard">
          <div :class="styles.stage">
            <span :class="styles.stageLabel">{{ stageLabel }}</span>
            <span
              v-if="workflow?.currentStep"
              :class="styles.stageStep"
            >
              {{ workflow.currentStep }}
            </span>
          </div>
          <div :class="styles.progressBar">
            <div
              :class="styles.progressFill"
              :style="{ width: `${progressPercent}%` }"
            />
          </div>
          <div :class="styles.progressLabel">
            {{ progressPercent }}%
          </div>
          <div
            v-if="workflow?.estimatedTimeRemaining"
            :class="styles.timeRemaining"
          >
            ~{{ formatTime(workflow.estimatedTimeRemaining) }} remaining
          </div>
        </div>
      </div>

      <!-- Training Readiness -->
      <div
        v-if="readiness"
        :class="styles.readiness"
      >
        <h3>Training Readiness</h3>
        <div :class="readinessCardClass">
          <div :class="styles.readinessStatus">
            <span :class="styles.readinessStatusIcon">{{ readiness.ready ? '✅' : '⏳' }}</span>
            <span>{{ readiness.ready ? 'Ready to Train' : 'Not Ready' }}</span>
          </div>

          <div :class="styles.metrics">
            <div :class="styles.metric">
              <span :class="styles.metricValue">{{ readiness.metrics.totalSamples }}</span>
              <span :class="styles.metricLabel">Total Samples</span>
            </div>
            <div :class="styles.metric">
              <span :class="styles.metricValue">{{ readiness.metrics.highQualitySamples }}</span>
              <span :class="styles.metricLabel">High Quality</span>
            </div>
            <div :class="styles.metric">
              <span :class="styles.metricValue">{{ (readiness.metrics.diversityScore * 100).toFixed(0) }}%</span>
              <span :class="styles.metricLabel">Diversity</span>
            </div>
            <div :class="styles.metric">
              <span :class="styles.metricValue">{{ readiness.metrics.recommendedEpochs }}</span>
              <span :class="styles.metricLabel">Rec. Epochs</span>
            </div>
          </div>

          <div
            v-if="!readiness.ready && readiness.reasons.length"
            :class="styles.reasons"
          >
            <p
              v-for="(reason, i) in readiness.reasons"
              :key="i"
            >
              ⚠️ {{ reason }}
            </p>
          </div>

          <div
            v-if="readiness.recommendations.length"
            :class="styles.recommendations"
          >
            <h4>Recommendations</h4>
            <ul>
              <li
                v-for="(rec, i) in readiness.recommendations"
                :key="i"
              >
                {{ rec }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Statistics -->
      <div
        v-if="stats"
        :class="styles.stats"
      >
        <h3>Learning Statistics</h3>

        <div :class="styles.statsGrid">
          <div :class="styles.statCard">
            <span :class="styles.statValue">{{ stats.totalFeedback }}</span>
            <span :class="styles.statLabel">Total Feedback</span>
          </div>
          <div :class="styles.statCardPositive">
            <span :class="styles.statValue">{{ stats.positiveFeedback }}</span>
            <span :class="styles.statLabel">Positive</span>
          </div>
          <div :class="styles.statCardNegative">
            <span :class="styles.statValue">{{ stats.negativeFeedback }}</span>
            <span :class="styles.statLabel">Negative</span>
          </div>
          <div :class="styles.statCard">
            <span :class="styles.statValue">{{ stats.averageRating.toFixed(1) }}</span>
            <span :class="styles.statLabel">Avg Rating</span>
          </div>
        </div>

        <!-- Rating Distribution -->
        <div :class="styles.ratingDistribution">
          <h4>Rating Distribution</h4>
          <div :class="styles.distributionBars">
            <div
              v-for="item in ratingDistribution"
              :key="item.rating"
              :class="styles.barRow"
            >
              <span :class="styles.barRating">{{ '★'.repeat(item.rating) }}</span>
              <div :class="styles.barContainer">
                <div
                  :class="styles.bar"
                  :style="{ width: `${(item.count / maxRatingCount) * 100}%` }"
                />
              </div>
              <span :class="styles.barCount">{{ item.count }}</span>
            </div>
          </div>
        </div>

        <!-- Top Prompts -->
        <div
          v-if="stats.topPrompts.length"
          :class="styles.topPrompts"
        >
          <h4>Top Performing Prompts</h4>
          <div :class="styles.promptList">
            <div
              v-for="(prompt, i) in stats.topPrompts.slice(0, 5)"
              :key="i"
              :class="styles.promptItem"
            >
              <span :class="styles.promptText">{{ prompt.prompt }}</span>
              <span :class="styles.promptStats">
                {{ prompt.avgRating.toFixed(1) }}★ ({{ prompt.count }})
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Section -->
      <div :class="styles.export">
        <h3>Export Training Data</h3>
        <div :class="styles.exportControls">
          <div :class="styles.controlGroup">
            <label>Format</label>
            <select v-model="exportFormat">
              <option value="kohya">
                Kohya SS
              </option>
              <option value="dreambooth">
                DreamBooth
              </option>
              <option value="lora">
                LoRA
              </option>
            </select>
          </div>
          <div :class="styles.controlGroup">
            <label>Min Rating</label>
            <select v-model="minRating">
              <option :value="5">
                5 stars only
              </option>
              <option :value="4">
                4+ stars
              </option>
              <option :value="3">
                3+ stars
              </option>
              <option :value="2">
                2+ stars
              </option>
              <option :value="1">
                All rated
              </option>
            </select>
          </div>
          <button
            :class="styles.exportBtn"
            :disabled="isExporting || !readiness?.metrics.totalSamples"
            @click="handleExport"
          >
            <template v-if="isExporting">
              <span :class="styles.spinnerSmall" />
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

