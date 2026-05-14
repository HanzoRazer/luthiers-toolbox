<script setup lang="ts">
/**
 * CalibrationResidualCard — Display calibration residual preview
 *
 * Dev Order 23: Shows gap between estimated and measured values.
 * Dev Order 29: Added estimate provenance annotation.
 * Does NOT calibrate, fit, correct, or predict.
 */
import { computed } from 'vue'
import { SectionLabel } from '@/components/shared/workflow'
import type { CalibrationResidualPreview, CalibrationResidual } from '@/types/calibrationResiduals'

const props = defineProps<{
  preview: CalibrationResidualPreview
}>()

function formatValue(val: number | undefined, decimals = 1, unit = ''): string {
  if (val === undefined) return '—'
  const suffix = unit ? ` ${unit}` : ''
  return `${val.toFixed(decimals)}${suffix}`
}

function formatResidual(residual: CalibrationResidual): string {
  if (!residual.available || residual.residual === undefined) return '—'

  const sign = residual.residual >= 0 ? '+' : ''
  const unit = residual.unit ? ` ${residual.unit}` : ''
  const base = `${sign}${residual.residual.toFixed(1)}${unit}`

  if (residual.percentResidual !== null && residual.percentResidual !== undefined) {
    const pctSign = residual.percentResidual >= 0 ? '+' : ''
    return `${base} (${pctSign}${residual.percentResidual.toFixed(1)}%)`
  }

  return base
}

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

const availableResiduals = computed(() => props.preview.residuals.filter((r) => r.available))
const unavailableResiduals = computed(() => props.preview.residuals.filter((r) => !r.available))
const showProvenance = computed(
  () => props.preview.hasAvailableResiduals && props.preview.provenance
)
const displayAssumptions = computed(() =>
  (props.preview.provenance?.estimateAssumptions ?? []).slice(0, 3)
)
const displayWarnings = computed(() =>
  (props.preview.provenance?.estimateWarnings ?? []).slice(0, 3)
)
</script>

<template>
  <div :class="$style.card">
    <SectionLabel :text="preview.label" />

    <!-- Available residuals table -->
    <table v-if="preview.hasAvailableResiduals" :class="$style.table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Estimated</th>
          <th>Measured</th>
          <th>Residual</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="residual in availableResiduals" :key="residual.id">
          <td>{{ residual.label }}</td>
          <td>{{ formatValue(residual.estimatedValue, 1, residual.unit) }}</td>
          <td>{{ formatValue(residual.measuredValue, 1, residual.unit) }}</td>
          <td :class="$style.residualCell">{{ formatResidual(residual) }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Estimate Provenance (Dev Order 29) -->
    <div v-if="showProvenance" :class="$style.provenance">
      <span :class="$style.provenanceLabel">Estimate Provenance</span>
      <div :class="$style.provenanceGrid">
        <div :class="$style.provenanceRow">
          <span :class="$style.provenanceKey">Method</span>
          <span :class="$style.provenanceValue">{{ formatMethod(preview.provenance?.estimateMethod) }}</span>
        </div>
        <div :class="$style.provenanceRow">
          <span :class="$style.provenanceKey">Source</span>
          <span :class="$style.provenanceValue">{{ formatSource(preview.provenance?.estimateSource) }}</span>
        </div>
        <div :class="$style.provenanceRow">
          <span :class="$style.provenanceKey">Confidence</span>
          <span :class="[$style.provenanceValue, $style.confidenceLow]">
            {{ formatConfidence(preview.provenance?.estimateConfidence) }}
          </span>
        </div>
      </div>

      <!-- Assumptions -->
      <div v-if="displayAssumptions.length > 0" :class="$style.provenanceList">
        <span :class="$style.provenanceListLabel">Assumptions:</span>
        <ul>
          <li v-for="(assumption, idx) in displayAssumptions" :key="idx">{{ assumption }}</li>
        </ul>
      </div>

      <!-- Warnings -->
      <div v-if="displayWarnings.length > 0" :class="$style.provenanceWarnings">
        <span :class="$style.provenanceListLabel">Warnings:</span>
        <ul>
          <li v-for="(warning, idx) in displayWarnings" :key="idx">{{ warning }}</li>
        </ul>
      </div>
    </div>

    <!-- Unavailable residuals list -->
    <div v-if="unavailableResiduals.length > 0" :class="$style.unavailable">
      <span :class="$style.unavailableLabel">Unavailable:</span>
      <ul>
        <li v-for="residual in unavailableResiduals" :key="residual.id">
          <span :class="$style.metricName">{{ residual.label }}:</span>
          {{ residual.message }}
        </li>
      </ul>
    </div>

    <!-- Notes -->
    <div v-if="preview.notes.length > 0" :class="$style.notes">
      <p v-for="(note, i) in preview.notes" :key="i">{{ note }}</p>
    </div>

    <!-- Explanatory notice -->
    <div :class="$style.notice">
      Residuals compare existing estimates against measured observations. Provenance annotations
      show the estimate assumptions behind each residual. They do not calibrate or correct the model.
    </div>
  </div>
</template>

<style module>
.card {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.table {
  width: 100%;
  margin-top: 0.75rem;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.table th,
.table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #374151;
}

.table th {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #111827;
}

.table td {
  color: #f9fafb;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.residualCell {
  color: #60a5fa;
}

.unavailable {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.unavailableLabel {
  display: block;
  font-size: 0.6875rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.unavailable ul {
  margin: 0;
  padding-left: 1.25rem;
  color: #9ca3af;
}

.unavailable li {
  line-height: 1.5;
}

.metricName {
  font-weight: 500;
  color: #d1d5db;
}

.notes {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
}

.notes p {
  margin: 0;
}

.notice {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-style: italic;
  padding: 0.375rem 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
  margin-top: 0.75rem;
}

/* Estimate Provenance (Dev Order 29) */
.provenance {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(107, 114, 128, 0.1);
  border: 1px solid rgba(107, 114, 128, 0.2);
  border-radius: 0.25rem;
}

.provenanceLabel {
  display: block;
  font-size: 0.6875rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.provenanceGrid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.provenanceRow {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.provenanceKey {
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.provenanceValue {
  font-size: 0.75rem;
  color: #f9fafb;
}

.confidenceLow {
  color: #fbbf24;
}

.provenanceList,
.provenanceWarnings {
  margin-top: 0.375rem;
}

.provenanceListLabel {
  font-size: 0.625rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.provenanceList ul,
.provenanceWarnings ul {
  margin: 0.125rem 0 0 1rem;
  padding: 0;
  font-size: 0.6875rem;
}

.provenanceList li {
  color: #9ca3af;
  line-height: 1.4;
}

.provenanceWarnings li {
  color: #fbbf24;
  line-height: 1.4;
}
</style>
