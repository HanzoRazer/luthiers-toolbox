<script setup lang="ts">
/**
 * EstimateAssumptionSummaryCard — Display estimate provenance and assumptions
 *
 * Dev Order 28: Consolidated assumption summary for first-order estimates.
 * Documents provenance without implying calibration accuracy.
 */
import { GateBadge } from '@/components/shared/workflow'
import type { EstimateAssumptionSummary } from '@/types/estimateAssumptions'

const props = defineProps<{
  summary: EstimateAssumptionSummary
}>()

function formatMethod(method: string | undefined): string {
  if (!method) return '—'
  switch (method) {
    case 'first_order_helmholtz':
      return 'First-Order Helmholtz'
    default:
      return method
  }
}

function formatSource(source: string | undefined): string {
  if (!source) return '—'
  switch (source) {
    case 'geometry_estimate':
      return 'Geometry Estimate'
    case 'measured':
      return 'Measured'
    case 'calibrated':
      return 'Calibrated'
    case 'manual':
      return 'Manual'
    default:
      return source
  }
}

function formatConfidence(confidence: string | undefined): string {
  if (!confidence) return '—'
  return confidence.charAt(0).toUpperCase() + confidence.slice(1)
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">{{ summary.label }}</span>
      <GateBadge
        :gate="summary.estimateAvailable ? 'yellow' : 'red'"
        :label="summary.estimateAvailable ? 'Attached' : 'None'"
      />
    </div>

    <!-- Empty state -->
    <div v-if="!summary.estimateAvailable" :class="$style.emptyState">
      <p>No estimate assumptions available yet.</p>
      <p>Attach a Helmholtz estimate to populate this summary.</p>
    </div>

    <!-- Estimate available -->
    <template v-else>
      <!-- Estimate value -->
      <div :class="$style.estimateRow">
        <span :class="$style.estimateLabel">Estimated Helmholtz</span>
        <span :class="$style.estimateValue">
          {{ summary.estimatedHelmholtzHz?.toFixed(1) ?? '—' }} Hz
        </span>
      </div>

      <!-- Metadata grid -->
      <div :class="$style.metadataGrid">
        <div :class="$style.metadataRow">
          <span :class="$style.metadataLabel">Body Volume</span>
          <span :class="$style.metadataValue">
            {{ summary.bodyVolumeLiters?.toFixed(1) ?? '—' }} L
          </span>
        </div>
        <div :class="$style.metadataRow">
          <span :class="$style.metadataLabel">Effective Length</span>
          <span :class="$style.metadataValue">
            {{ summary.effectiveLengthMm?.toFixed(1) ?? '—' }} mm
          </span>
        </div>
        <div :class="$style.metadataRow">
          <span :class="$style.metadataLabel">Speed of Sound</span>
          <span :class="$style.metadataValue">
            {{ summary.speedOfSoundMps?.toFixed(0) ?? '—' }} m/s
          </span>
        </div>
        <div :class="$style.metadataRow">
          <span :class="$style.metadataLabel">Method</span>
          <span :class="$style.metadataValue">{{ formatMethod(summary.method) }}</span>
        </div>
        <div :class="$style.metadataRow">
          <span :class="$style.metadataLabel">Source</span>
          <span :class="$style.metadataValue">{{ formatSource(summary.source) }}</span>
        </div>
        <div :class="$style.metadataRow">
          <span :class="$style.metadataLabel">Confidence</span>
          <span :class="[$style.metadataValue, $style.confidenceLow]">
            {{ formatConfidence(summary.confidence) }}
          </span>
        </div>
      </div>

      <!-- Assumptions -->
      <div v-if="summary.assumptions.length > 0" :class="$style.assumptionsSection">
        <span :class="$style.sectionLabel">Assumptions</span>
        <ul :class="$style.assumptionsList">
          <li v-for="(assumption, idx) in summary.assumptions" :key="idx">
            {{ assumption }}
          </li>
        </ul>
      </div>

      <!-- Warnings -->
      <div v-if="summary.warnings.length > 0" :class="$style.warningsSection">
        <span :class="$style.sectionLabel">Warnings</span>
        <ul :class="$style.warningsList">
          <li v-for="(warning, idx) in summary.warnings" :key="idx">
            {{ warning }}
          </li>
        </ul>
      </div>
    </template>

    <!-- Provenance notice -->
    <div :class="$style.notice">
      This summary documents the assumptions attached to the current estimate.
      It does not imply calibrated prediction accuracy.
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

.emptyState {
  padding: 0.75rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
  text-align: center;
}

.emptyState p {
  margin: 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.emptyState p + p {
  margin-top: 0.25rem;
  font-style: italic;
}

.estimateRow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 0.25rem;
  margin-bottom: 0.75rem;
}

.estimateLabel {
  font-size: 0.75rem;
  color: #9ca3af;
}

.estimateValue {
  font-size: 1rem;
  font-weight: 600;
  color: #10b981;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.metadataGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.metadataRow {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
}

.metadataLabel {
  font-size: 0.6875rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metadataValue {
  font-size: 0.75rem;
  color: #f9fafb;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.confidenceLow {
  color: #fbbf24;
}

.assumptionsSection,
.warningsSection {
  margin-bottom: 0.5rem;
}

.sectionLabel {
  display: block;
  font-size: 0.6875rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.assumptionsList,
.warningsList {
  margin: 0;
  padding-left: 1rem;
  font-size: 0.6875rem;
}

.assumptionsList li {
  color: #9ca3af;
  line-height: 1.5;
}

.warningsList li {
  color: #fbbf24;
  line-height: 1.5;
}

.notice {
  font-size: 0.6875rem;
  color: #6b7280;
  font-style: italic;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
  margin-top: 0.5rem;
}
</style>
