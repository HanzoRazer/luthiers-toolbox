<script setup lang="ts">
/**
 * ExperimentalDriftSynthesisPanel
 *
 * Dev Order 72: Session-level drift synthesis
 *
 * Displays aggregate observational summaries across multiple drift records.
 * Synthesis is observational only — not conclusions, proofs, or recommendations.
 *
 * OBSERVATIONAL ONLY:
 * - Synthesis does NOT imply improvement or optimization
 * - No causal inference
 * - No predictive modeling
 * - No recommendation authority
 */

import { computed } from 'vue'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import type { ExperimentalDriftRecord } from '@/types/acoustics/experimentalDrift'
import type {
  DriftSynthesisResult,
  ExperimentalDriftSynthesis,
  SessionDriftObservation,
  VariantDriftObservation,
  SynthesisDominantDirection,
} from '@/types/acoustics/experimentalDriftSynthesis'
import {
  computeExperimentalDrift,
  hasSufficientDriftData,
} from '@/utils/acoustics/experimentalDrift'
import {
  computeExperimentalDriftSynthesis,
  hasSufficientDriftSynthesisData,
  MINIMUM_SYNTHESIS_RECORDS,
} from '@/utils/acoustics/experimentalDriftSynthesis'

const props = defineProps<{
  archives: MeasurementArchiveRecord[]
}>()

const driftRecords = computed<ExperimentalDriftRecord[]>(() => {
  if (!hasSufficientDriftData(props.archives)) {
    return []
  }
  const result = computeExperimentalDrift(props.archives, 'chronological')
  return result.drifts
})

const synthesisResult = computed<DriftSynthesisResult | null>(() => {
  if (!hasSufficientDriftSynthesisData(driftRecords.value)) {
    return null
  }
  return computeExperimentalDriftSynthesis(driftRecords.value)
})

const overallSynthesis = computed<ExperimentalDriftSynthesis | undefined>(() => {
  return synthesisResult.value?.summary.overallSynthesis
})

const sessionObservations = computed<SessionDriftObservation[]>(() => {
  return synthesisResult.value?.summary.sessionObservations ?? []
})

const variantObservations = computed<VariantDriftObservation[]>(() => {
  return synthesisResult.value?.summary.variantObservations ?? []
})

const insufficientDataMessage = computed<string | null>(() => {
  if (driftRecords.value.length < MINIMUM_SYNTHESIS_RECORDS) {
    return `Drift synthesis requires at least ${MINIMUM_SYNTHESIS_RECORDS} drift records. Currently: ${driftRecords.value.length} (from ${props.archives.length} archives)`
  }
  return null
})

function getDirectionLabel(direction: SynthesisDominantDirection): string {
  switch (direction) {
    case 'upward':
      return 'Upward Drift'
    case 'downward':
      return 'Downward Drift'
    case 'stable':
      return 'Stable'
    case 'variable':
      return 'Variable'
    case 'mixed':
      return 'Mixed Directions'
    default:
      return direction
  }
}

function getDirectionClass(direction: SynthesisDominantDirection): string {
  switch (direction) {
    case 'upward':
      return 'synthesis-upward'
    case 'downward':
      return 'synthesis-downward'
    case 'stable':
      return 'synthesis-stable'
    case 'variable':
      return 'synthesis-variable'
    case 'mixed':
      return 'synthesis-mixed'
    default:
      return ''
  }
}
</script>

<template>
  <div class="synthesis-panel">
    <header class="synthesis-header">
      <h3>Experimental Drift Synthesis</h3>
      <p class="synthesis-subtitle">
        Aggregate observational patterns across experimental sequences
      </p>
    </header>

    <div v-if="insufficientDataMessage" class="synthesis-insufficient">
      <span class="synthesis-icon">📊</span>
      <p>{{ insufficientDataMessage }}</p>
    </div>

    <template v-else-if="synthesisResult">
      <!-- Overall Synthesis -->
      <div v-if="overallSynthesis" class="synthesis-overall">
        <h4>Overall Synthesis</h4>
        <div
          class="synthesis-card"
          :class="getDirectionClass(overallSynthesis.dominantDirection)"
        >
          <div class="synthesis-card-header">
            <span class="synthesis-direction-badge">
              {{ getDirectionLabel(overallSynthesis.dominantDirection) }}
            </span>
            <span class="synthesis-stats">
              {{ overallSynthesis.driftRecordCount }} drift records •
              {{ overallSynthesis.archiveCount }} archives
            </span>
          </div>

          <p class="synthesis-narrative">{{ overallSynthesis.narrative }}</p>

          <div
            v-if="overallSynthesis.dominantPatterns.length > 0"
            class="synthesis-patterns"
          >
            <span class="patterns-label">Patterns:</span>
            <ul class="patterns-list">
              <li
                v-for="(pattern, idx) in overallSynthesis.dominantPatterns"
                :key="idx"
              >
                {{ pattern }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Session Observations -->
      <div v-if="sessionObservations.length > 0" class="synthesis-section">
        <h4>By Session ({{ sessionObservations.length }})</h4>
        <div class="observation-grid">
          <div
            v-for="obs in sessionObservations"
            :key="obs.sessionContext"
            class="observation-card"
            :class="getDirectionClass(obs.dominantDirection)"
          >
            <div class="observation-header">
              <span class="observation-label">{{ obs.sessionContext }}</span>
              <span class="observation-badge">
                {{ getDirectionLabel(obs.dominantDirection) }}
              </span>
            </div>
            <div class="observation-stats">
              {{ obs.driftRecordCount }} records • {{ obs.archiveCount }} archives
            </div>
            <ul v-if="obs.patterns.length > 0" class="observation-patterns">
              <li v-for="(pattern, idx) in obs.patterns.slice(0, 2)" :key="idx">
                {{ pattern }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Variant Observations -->
      <div v-if="variantObservations.length > 0" class="synthesis-section">
        <h4>By Topology Variant ({{ variantObservations.length }})</h4>
        <div class="observation-grid">
          <div
            v-for="obs in variantObservations"
            :key="obs.variantId"
            class="observation-card"
            :class="getDirectionClass(obs.dominantDirection)"
          >
            <div class="observation-header">
              <span class="observation-label">{{ obs.variantId }}</span>
              <span class="observation-badge">
                {{ getDirectionLabel(obs.dominantDirection) }}
              </span>
            </div>
            <div class="observation-stats">
              {{ obs.driftRecordCount }} records • {{ obs.archiveCount }} archives
            </div>
            <ul v-if="obs.patterns.length > 0" class="observation-patterns">
              <li v-for="(pattern, idx) in obs.patterns.slice(0, 2)" :key="idx">
                {{ pattern }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Insufficient Contexts -->
      <div
        v-if="
          synthesisResult.summary.insufficientSessions.length > 0 ||
          synthesisResult.summary.insufficientVariants.length > 0
        "
        class="synthesis-warnings"
      >
        <p v-if="synthesisResult.summary.insufficientSessions.length > 0">
          Sessions with insufficient data:
          {{ synthesisResult.summary.insufficientSessions.join(', ') }}
        </p>
        <p v-if="synthesisResult.summary.insufficientVariants.length > 0">
          Variants with insufficient data:
          {{ synthesisResult.summary.insufficientVariants.join(', ') }}
        </p>
      </div>

      <!-- Processing Info -->
      <div v-if="synthesisResult.warnings.length > 0" class="synthesis-info">
        <p>
          Analyzed {{ synthesisResult.totalDriftRecordsAnalyzed }} of
          {{ synthesisResult.totalDriftRecordsProvided }} drift records.
        </p>
      </div>
    </template>

    <footer class="synthesis-footer">
      <p class="synthesis-disclaimer">
        Drift synthesis summarizes repeated observational patterns across experimental sequences and does not imply causation, optimization, or design superiority.
      </p>
    </footer>
  </div>
</template>

<style scoped>
.synthesis-panel {
  padding: 1rem;
  background: var(--color-background-soft, #f8f8f8);
  border-radius: 8px;
}

.synthesis-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
}

.synthesis-subtitle {
  margin: 0 0 1rem 0;
  color: var(--color-text-muted, #666);
  font-size: 0.875rem;
}

.synthesis-insufficient {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--color-warning-bg, #fff3cd);
  border-radius: 4px;
}

.synthesis-icon {
  font-size: 1.5rem;
}

.synthesis-overall {
  margin-bottom: 1.5rem;
}

.synthesis-overall h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
}

.synthesis-card {
  padding: 1rem;
  background: white;
  border-radius: 4px;
  border-left: 4px solid var(--color-border, #ddd);
}

.synthesis-card.synthesis-upward {
  border-left-color: var(--color-info, #17a2b8);
}

.synthesis-card.synthesis-downward {
  border-left-color: var(--color-warning, #ffc107);
}

.synthesis-card.synthesis-stable {
  border-left-color: var(--color-success, #28a745);
}

.synthesis-card.synthesis-variable {
  border-left-color: var(--color-secondary, #6c757d);
}

.synthesis-card.synthesis-mixed {
  border-left-color: var(--color-primary, #6366f1);
}

.synthesis-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.synthesis-direction-badge {
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  background: var(--color-background-soft, #f0f0f0);
}

.synthesis-stats {
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
}

.synthesis-narrative {
  margin: 0.5rem 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

.synthesis-patterns {
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border-light, #eee);
}

.patterns-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted, #666);
}

.patterns-list {
  margin: 0.25rem 0 0 1rem;
  padding: 0;
  font-size: 0.8125rem;
}

.patterns-list li {
  margin-bottom: 0.25rem;
}

.synthesis-section {
  margin-bottom: 1.5rem;
}

.synthesis-section h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
}

.observation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.75rem;
}

.observation-card {
  padding: 0.75rem;
  background: white;
  border-radius: 4px;
  border-left: 3px solid var(--color-border, #ddd);
}

.observation-card.synthesis-upward {
  border-left-color: var(--color-info, #17a2b8);
}

.observation-card.synthesis-downward {
  border-left-color: var(--color-warning, #ffc107);
}

.observation-card.synthesis-stable {
  border-left-color: var(--color-success, #28a745);
}

.observation-card.synthesis-variable {
  border-left-color: var(--color-secondary, #6c757d);
}

.observation-card.synthesis-mixed {
  border-left-color: var(--color-primary, #6366f1);
}

.observation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.observation-label {
  font-weight: 600;
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
}

.observation-badge {
  font-size: 0.6875rem;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  background: var(--color-background-soft, #f0f0f0);
}

.observation-stats {
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
  margin-bottom: 0.5rem;
}

.observation-patterns {
  margin: 0;
  padding: 0 0 0 1rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
}

.observation-patterns li {
  margin-bottom: 0.125rem;
}

.synthesis-warnings {
  padding: 0.5rem 0.75rem;
  background: var(--color-warning-bg, #fff3cd);
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.synthesis-warnings p {
  margin: 0.25rem 0;
}

.synthesis-info {
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
  margin-bottom: 1rem;
}

.synthesis-info p {
  margin: 0;
}

.synthesis-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #ddd);
}

.synthesis-disclaimer {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #999);
  font-style: italic;
  text-align: center;
}
</style>
