<script setup lang="ts">
/**
 * MeasurementPairingStatusCard — Display estimate/measurement pairing status
 *
 * Dev Order 25: Shows which metrics have both estimate and measurement.
 * Does NOT calibrate or predict.
 */
import { computed } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type { MeasurementPairingStatus, PairingStatus } from '@/types/measurementPairing'

const props = defineProps<{
  status: MeasurementPairingStatus
}>()

const gateColor = computed(() => {
  if (props.status.pairedCount > 0) return 'green'
  if (props.status.availableCount > 0) return 'yellow'
  return 'red'
})

const statusLabel = computed(() => {
  if (props.status.pairedCount > 0) return 'Residual Ready'
  if (props.status.availableCount > 0) return 'Partial Data'
  return 'No Data'
})

function getStatusLabel(pairingStatus: PairingStatus): string {
  switch (pairingStatus) {
    case 'paired':
      return 'Paired'
    case 'estimate_only':
      return 'Estimate only'
    case 'measurement_only':
      return 'Measurement only'
    case 'missing':
      return 'Missing'
  }
}

function formatValue(val: number | undefined, unit: string): string {
  if (val === undefined) return '—'
  const formatted = val.toFixed(1)
  return unit ? `${formatted} ${unit}` : formatted
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">{{ status.label }}</span>
      <GateBadge :gate="gateColor" :label="statusLabel" />
    </div>

    <!-- Summary -->
    <div :class="$style.summary">
      <span :class="$style.summaryItem">
        <span :class="$style.count">{{ status.pairedCount }}</span> paired
      </span>
      <span :class="$style.summaryItem">
        <span :class="$style.count">{{ status.availableCount }}</span> available
      </span>
      <span :class="$style.summaryItem">
        <span :class="$style.count">{{ status.missingCount }}</span> missing
      </span>
    </div>

    <!-- Metrics Table -->
    <table :class="$style.table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Status</th>
          <th>Estimate</th>
          <th>Measured</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="metric in status.metrics" :key="metric.id">
          <td>{{ metric.label }}</td>
          <td :class="$style[`status--${metric.status}`]">{{ getStatusLabel(metric.status) }}</td>
          <td>{{ formatValue(metric.estimateValue, metric.unit ?? '') }}</td>
          <td>{{ formatValue(metric.measurementValue, metric.unit ?? '') }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Ready message -->
    <div v-if="status.readyForResidualPreview" :class="$style.readyMessage">
      At least one estimate/measurement pair is available for residual preview.
    </div>

    <!-- Notice -->
    <div :class="$style.notice">
      Pairing status shows whether estimates and measurements exist for the same metric. It does
      not calibrate or predict.
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

.summary {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.75rem;
  color: #9ca3af;
}

.summaryItem {
  display: flex;
  gap: 0.25rem;
}

.count {
  font-weight: 600;
  color: #f9fafb;
}

.table {
  width: 100%;
  margin-bottom: 0.5rem;
  border-collapse: collapse;
  font-size: 0.75rem;
}

.table th,
.table td {
  padding: 0.375rem 0.5rem;
  text-align: left;
  border-bottom: 1px solid #374151;
}

.table th {
  font-size: 0.625rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #1f2937;
}

.table td {
  color: #d1d5db;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.status--paired {
  color: #10b981;
  font-weight: 500;
}

.status--estimate_only {
  color: #fbbf24;
}

.status--measurement_only {
  color: #60a5fa;
}

.status--missing {
  color: #6b7280;
  font-style: italic;
}

.readyMessage {
  font-size: 0.6875rem;
  color: #10b981;
  padding: 0.375rem 0.5rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.notice {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-style: italic;
  padding: 0.375rem 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
}
</style>
