<script setup lang="ts">
/**
 * ExperimentalDriftTimelinePanel
 *
 * Dev Order 70: Experimental drift timeline workspace
 *
 * Displays drift observations across sequential measurement archives.
 * Drift is observational only — describes temporal patterns without implying
 * causation, optimization, or design superiority.
 *
 * OBSERVATIONAL ONLY:
 * - Drift does NOT imply improvement or degradation
 * - No optimization, recommendation, or prediction semantics
 * - No authority claims about acoustic behavior
 */

import { ref, computed, watch } from 'vue'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import type {
  DriftContextType,
  DriftComputeResult,
  ExperimentalDriftRecord,
  ExperimentalDriftSummary,
} from '@/types/acoustics/experimentalDrift'
import {
  computeExperimentalDrift,
  hasSufficientDriftData,
  MINIMUM_DRIFT_SAMPLE_SIZE,
  DRIFT_TRACKABLE_FIELDS,
  filterDriftsByField,
  filterDriftsByDirection,
} from '@/utils/acoustics/experimentalDrift'

const props = defineProps<{
  archives: MeasurementArchiveRecord[]
}>()

const selectedContextType = ref<DriftContextType>('chronological')
const selectedField = ref<string | null>(null)
const selectedDirection = ref<string | null>(null)

const driftResult = computed<DriftComputeResult | null>(() => {
  if (!hasSufficientDriftData(props.archives)) {
    return null
  }
  return computeExperimentalDrift(props.archives, selectedContextType.value)
})

const filteredDrifts = computed<ExperimentalDriftRecord[]>(() => {
  if (!driftResult.value) return []

  let drifts = driftResult.value.drifts

  if (selectedField.value) {
    drifts = filterDriftsByField(drifts, selectedField.value as any)
  }

  if (selectedDirection.value) {
    drifts = filterDriftsByDirection(drifts, selectedDirection.value as any)
  }

  return drifts
})

const summaries = computed<ExperimentalDriftSummary[]>(() => {
  return driftResult.value?.summaries ?? []
})

const insufficientDataMessage = computed<string | null>(() => {
  if (props.archives.length < MINIMUM_DRIFT_SAMPLE_SIZE) {
    return `Drift analysis requires at least ${MINIMUM_DRIFT_SAMPLE_SIZE} archives. Currently: ${props.archives.length}`
  }
  return null
})

const contextTypeOptions = [
  { value: 'chronological', label: 'Chronological (all archives)' },
  { value: 'variant', label: 'By Topology Variant' },
  { value: 'session', label: 'By Session Context' },
] as const

function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

function getDirectionLabel(direction: string): string {
  switch (direction) {
    case 'upward':
      return 'Shifted Upward'
    case 'downward':
      return 'Shifted Downward'
    case 'stable':
      return 'Remained Stable'
    case 'variable':
      return 'Variable'
    default:
      return direction
  }
}

function getDirectionClass(direction: string): string {
  switch (direction) {
    case 'upward':
      return 'drift-upward'
    case 'downward':
      return 'drift-downward'
    case 'stable':
      return 'drift-stable'
    case 'variable':
      return 'drift-variable'
    default:
      return ''
  }
}

watch(selectedContextType, () => {
  selectedField.value = null
  selectedDirection.value = null
})
</script>

<template>
  <div class="drift-timeline-panel">
    <header class="drift-header">
      <h3>Experimental Drift Timeline</h3>
      <p class="drift-subtitle">
        Observational drift patterns across sequential archives
      </p>
    </header>

    <div v-if="insufficientDataMessage" class="drift-insufficient">
      <span class="drift-icon">📊</span>
      <p>{{ insufficientDataMessage }}</p>
    </div>

    <template v-else>
      <div class="drift-controls">
        <div class="control-group">
          <label for="context-type">Group By</label>
          <select id="context-type" v-model="selectedContextType">
            <option
              v-for="opt in contextTypeOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div class="control-group">
          <label for="field-filter">Field</label>
          <select id="field-filter" v-model="selectedField">
            <option :value="null">All Fields</option>
            <option
              v-for="field in DRIFT_TRACKABLE_FIELDS"
              :key="field"
              :value="field"
            >
              {{ field }}
            </option>
          </select>
        </div>

        <div class="control-group">
          <label for="direction-filter">Direction</label>
          <select id="direction-filter" v-model="selectedDirection">
            <option :value="null">All Directions</option>
            <option value="upward">Shifted Upward</option>
            <option value="downward">Shifted Downward</option>
            <option value="stable">Remained Stable</option>
            <option value="variable">Variable</option>
          </select>
        </div>
      </div>

      <div v-if="summaries.length > 0" class="drift-summaries">
        <h4>Context Summaries</h4>
        <div class="summary-cards">
          <div
            v-for="summary in summaries"
            :key="summary.contextId"
            class="summary-card"
            :class="getDirectionClass(summary.dominantDirection)"
          >
            <div class="summary-label">{{ summary.contextLabel }}</div>
            <div class="summary-stats">
              <span>{{ summary.archiveCount }} archives</span>
              <span>{{ summary.driftCount }} drift observations</span>
            </div>
            <div class="summary-direction">
              {{ getDirectionLabel(summary.dominantDirection) }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="driftResult?.insufficientContexts.length" class="drift-warnings">
        <p>
          Insufficient data for contexts:
          {{ driftResult.insufficientContexts.join(', ') }}
        </p>
      </div>

      <div class="drift-records">
        <h4>Drift Observations ({{ filteredDrifts.length }})</h4>

        <div v-if="filteredDrifts.length === 0" class="drift-empty">
          No drift observations match the current filters.
        </div>

        <div
          v-for="drift in filteredDrifts"
          :key="drift.driftId"
          class="drift-record"
          :class="getDirectionClass(drift.direction)"
        >
          <div class="drift-record-header">
            <span class="drift-field">{{ drift.observedField }}</span>
            <span class="drift-direction-badge">
              {{ getDirectionLabel(drift.direction) }}
            </span>
          </div>

          <p class="drift-narrative">{{ drift.narrative }}</p>

          <div class="drift-timeline">
            <div class="timeline-header">
              <span>Archive</span>
              <span>Value</span>
              <span>Delta</span>
              <span>% Change</span>
            </div>
            <div
              v-for="point in drift.timelinePoints"
              :key="point.archiveId"
              class="timeline-point"
            >
              <span class="point-archive">{{ point.archiveId.slice(0, 12) }}...</span>
              <span class="point-value">{{ point.value.toFixed(2) }}</span>
              <span class="point-delta">
                {{ point.deltaFromPrevious !== undefined ? point.deltaFromPrevious.toFixed(2) : '—' }}
              </span>
              <span class="point-percent">
                {{ point.percentDeltaFromPrevious !== undefined ? formatPercentage(point.percentDeltaFromPrevious) : '—' }}
              </span>
            </div>
          </div>

          <div class="drift-meta">
            <span>{{ drift.sampleCount }} observations</span>
            <span v-if="drift.contextId">Context: {{ drift.contextId }}</span>
          </div>
        </div>
      </div>
    </template>

    <footer class="drift-footer">
      <p class="drift-disclaimer">
        Drift observations describe temporal patterns only.
        No causation, optimization, or design superiority is implied.
      </p>
    </footer>
  </div>
</template>

<style scoped>
.drift-timeline-panel {
  padding: 1rem;
  background: var(--color-background-soft, #f8f8f8);
  border-radius: 8px;
}

.drift-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
}

.drift-subtitle {
  margin: 0 0 1rem 0;
  color: var(--color-text-muted, #666);
  font-size: 0.875rem;
}

.drift-insufficient {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--color-warning-bg, #fff3cd);
  border-radius: 4px;
}

.drift-icon {
  font-size: 1.5rem;
}

.drift-controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.control-group label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-muted, #666);
}

.control-group select {
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
  font-size: 0.875rem;
}

.drift-summaries {
  margin-bottom: 1.5rem;
}

.drift-summaries h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
}

.summary-cards {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.summary-card {
  padding: 0.75rem;
  background: white;
  border-radius: 4px;
  border-left: 4px solid var(--color-border, #ddd);
  min-width: 180px;
}

.summary-card.drift-upward {
  border-left-color: var(--color-info, #17a2b8);
}

.summary-card.drift-downward {
  border-left-color: var(--color-warning, #ffc107);
}

.summary-card.drift-stable {
  border-left-color: var(--color-success, #28a745);
}

.summary-card.drift-variable {
  border-left-color: var(--color-secondary, #6c757d);
}

.summary-label {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.summary-stats {
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
  display: flex;
  gap: 0.5rem;
}

.summary-direction {
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

.drift-warnings {
  padding: 0.5rem 0.75rem;
  background: var(--color-warning-bg, #fff3cd);
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.drift-records h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
}

.drift-empty {
  padding: 1rem;
  text-align: center;
  color: var(--color-text-muted, #666);
  font-style: italic;
}

.drift-record {
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 4px;
  border-left: 4px solid var(--color-border, #ddd);
}

.drift-record.drift-upward {
  border-left-color: var(--color-info, #17a2b8);
}

.drift-record.drift-downward {
  border-left-color: var(--color-warning, #ffc107);
}

.drift-record.drift-stable {
  border-left-color: var(--color-success, #28a745);
}

.drift-record.drift-variable {
  border-left-color: var(--color-secondary, #6c757d);
}

.drift-record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.drift-field {
  font-weight: 600;
  font-family: monospace;
}

.drift-direction-badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  background: var(--color-background-soft, #f0f0f0);
}

.drift-narrative {
  margin: 0.5rem 0;
  font-size: 0.875rem;
  color: var(--color-text, #333);
}

.drift-timeline {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  font-family: monospace;
}

.timeline-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 0.5rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--color-border, #ddd);
  font-weight: 600;
  color: var(--color-text-muted, #666);
}

.timeline-point {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 0.5rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--color-border-light, #eee);
}

.drift-meta {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
  display: flex;
  gap: 1rem;
}

.drift-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #ddd);
}

.drift-disclaimer {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #999);
  font-style: italic;
  text-align: center;
}
</style>
