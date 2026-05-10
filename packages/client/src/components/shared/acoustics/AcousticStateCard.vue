<script setup lang="ts">
/**
 * AcousticStateCard — Reusable display for AcousticState
 *
 * Dev Order 16: Extracted from ApertureComparisonPanel inline display.
 * Displays acoustic state metadata without prediction logic.
 */
import { computed } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type { AcousticState, AcousticConfidence } from '@/types/acoustics'
import {
  hasEstimatedAcoustics,
  getConfidenceLabel,
  getSourceLabel,
} from '@/utils/acoustics'

const props = defineProps<{
  state: AcousticState
}>()

/**
 * Map confidence to gate color.
 * low/unknown/medium → yellow, high → green
 * No red — red is reserved for diagnostic failures.
 */
function confidenceToGate(confidence: AcousticConfidence): 'green' | 'yellow' {
  return confidence === 'high' ? 'green' : 'yellow'
}

const hasEstimates = computed(() => hasEstimatedAcoustics(props.state))
const gateColor = computed(() => confidenceToGate(props.state.confidence))
</script>

<template>
  <div :class="$style.card">
    <!-- Header -->
    <div :class="$style.header">
      <span :class="$style.label">{{ state.label }}</span>
      <GateBadge :gate="gateColor" :label="getConfidenceLabel(state.confidence)" />
    </div>

    <!-- Metadata -->
    <div :class="$style.meta">
      <div :class="$style.row">
        <span :class="$style.key">Source:</span>
        <span :class="$style.value">{{ getSourceLabel(state.source) }}</span>
      </div>
      <div :class="$style.row">
        <span :class="$style.key">Confidence:</span>
        <span :class="$style.value">{{ getConfidenceLabel(state.confidence) }}</span>
      </div>
      <div v-if="state.apertureType" :class="$style.row">
        <span :class="$style.key">Type:</span>
        <span :class="$style.value">{{ state.apertureType }}</span>
      </div>
    </div>

    <!-- Estimated Values -->
    <div v-if="hasEstimates" :class="$style.estimates">
      <div v-if="state.estimatedHelmholtzHz !== undefined" :class="$style.row">
        <span :class="$style.key">Helmholtz:</span>
        <span :class="$style.value">{{ state.estimatedHelmholtzHz.toFixed(1) }} Hz</span>
      </div>
      <div v-if="state.estimatedEffectiveLengthMm !== undefined" :class="$style.row">
        <span :class="$style.key">Effective length:</span>
        <span :class="$style.value">{{ state.estimatedEffectiveLengthMm.toFixed(1) }} mm</span>
      </div>
      <div v-if="state.qEstimate !== undefined" :class="$style.row">
        <span :class="$style.key">Q estimate:</span>
        <span :class="$style.value">{{ state.qEstimate.toFixed(1) }}</span>
      </div>
      <div v-if="state.lossEstimate !== undefined" :class="$style.row">
        <span :class="$style.key">Loss estimate:</span>
        <span :class="$style.value">{{ state.lossEstimate.toFixed(2) }}</span>
      </div>
    </div>

    <!-- No Estimates Message -->
    <div v-else :class="$style.noEstimates">
      No calibrated acoustic estimates attached.
    </div>

    <!-- Warnings -->
    <div v-if="state.warnings?.length" :class="$style.warnings">
      <span :class="$style.warningsLabel">Warnings:</span>
      <ul>
        <li v-for="(warning, i) in state.warnings" :key="i">
          {{ warning }}
        </li>
      </ul>
    </div>

    <!-- Assumptions -->
    <div v-if="state.assumptions.length" :class="$style.assumptions">
      <span :class="$style.assumptionsLabel">Assumptions:</span>
      <ul>
        <li v-for="(assumption, i) in state.assumptions" :key="i">
          {{ assumption }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style module>
.card {
  background: #111827;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  padding: 0.75rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
}

.label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #f9fafb;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.key {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.value {
  font-size: 0.8125rem;
  color: #d1d5db;
}

.estimates {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.noEstimates {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  padding: 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.warnings {
  font-size: 0.75rem;
  color: #f59e0b;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 0.25rem;
}

.warningsLabel {
  font-weight: 500;
  display: block;
  margin-bottom: 0.25rem;
}

.warnings ul {
  margin: 0;
  padding-left: 1rem;
}

.warnings li {
  line-height: 1.5;
}

.assumptions {
  font-size: 0.75rem;
  color: #9ca3af;
}

.assumptionsLabel {
  font-weight: 500;
  color: #6b7280;
  display: block;
  margin-bottom: 0.25rem;
}

.assumptions ul {
  margin: 0;
  padding-left: 1rem;
}

.assumptions li {
  line-height: 1.5;
}
</style>
