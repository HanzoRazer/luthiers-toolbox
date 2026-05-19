<script setup lang="ts">
/**
 * MeasuredResponseDeltaCard — Compare measured response values
 *
 * Dev Order 21: Display-only measured response delta.
 * Shows differences between reference and candidate measured values.
 * No calibration, no prediction — observational comparison only.
 */
import { computed } from 'vue'
import { SectionLabel } from '@/components/shared/workflow'
import type { MeasuredResponse } from '@/types/measurements'
import { hasMeasuredResponseData } from '@/utils/acoustics/measuredResponse'

const props = defineProps<{
  reference: MeasuredResponse
  candidate: MeasuredResponse
}>()

const hasReferenceData = computed(() => hasMeasuredResponseData(props.reference))
const hasCandidateData = computed(() => hasMeasuredResponseData(props.candidate))
const hasComparableData = computed(() => hasReferenceData.value && hasCandidateData.value)

interface DeltaRow {
  metric: string
  reference: string
  candidate: string
  delta: string
}

function formatValue(val: number | undefined, decimals = 1): string {
  if (val === undefined) return '—'
  return val.toFixed(decimals)
}

function formatDelta(
  refVal: number | undefined,
  candVal: number | undefined,
  decimals = 1
): string {
  if (refVal === undefined || candVal === undefined) return '—'
  const diff = candVal - refVal
  const sign = diff >= 0 ? '+' : ''
  if (refVal === 0) {
    return `${sign}${diff.toFixed(decimals)}`
  }
  const pct = (diff / refVal) * 100
  return `${sign}${diff.toFixed(decimals)} (${sign}${pct.toFixed(1)}%)`
}

const deltaTable = computed<DeltaRow[]>(() => {
  const ref = props.reference
  const cand = props.candidate

  return [
    {
      metric: 'Helmholtz (Hz)',
      reference: formatValue(ref.measuredHelmholtzHz),
      candidate: formatValue(cand.measuredHelmholtzHz),
      delta: formatDelta(ref.measuredHelmholtzHz, cand.measuredHelmholtzHz),
    },
    {
      metric: 'Q Factor',
      reference: formatValue(ref.measuredQ),
      candidate: formatValue(cand.measuredQ),
      delta: formatDelta(ref.measuredQ, cand.measuredQ),
    },
    {
      metric: 'Dominant Peak (Hz)',
      reference: formatValue(ref.dominantPeakHz),
      candidate: formatValue(cand.dominantPeakHz),
      delta: formatDelta(ref.dominantPeakHz, cand.dominantPeakHz),
    },
  ]
})

const hasAnyComparableMetric = computed(() => {
  const ref = props.reference
  const cand = props.candidate
  return (
    (ref.measuredHelmholtzHz !== undefined && cand.measuredHelmholtzHz !== undefined) ||
    (ref.measuredQ !== undefined && cand.measuredQ !== undefined) ||
    (ref.dominantPeakHz !== undefined && cand.dominantPeakHz !== undefined)
  )
})
</script>

<template>
  <div :class="$style.card">
    <SectionLabel text="Measured Response Delta" />

    <!-- No comparable data message -->
    <div v-if="!hasAnyComparableMetric" :class="$style.noData">
      Enter measurements for both reference and candidate apertures to display measured deltas.
    </div>

    <!-- Delta table -->
    <table v-else :class="$style.deltaTable">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Reference</th>
          <th>Candidate</th>
          <th>Delta</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in deltaTable" :key="row.metric">
          <td>{{ row.metric }}</td>
          <td>{{ row.reference }}</td>
          <td>{{ row.candidate }}</td>
          <td :class="$style.deltaCell">{{ row.delta }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Informational notice -->
    <div :class="$style.notice">
      Measured deltas compare manually entered observations only. They are not calibrated predictions.
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

.noData {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  padding: 0.75rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
  margin: 0.75rem 0;
}

.deltaTable {
  width: 100%;
  margin-top: 0.75rem;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.deltaTable th,
.deltaTable td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #374151;
}

.deltaTable th {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #111827;
}

.deltaTable td {
  color: #f9fafb;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.deltaCell {
  color: #60a5fa;
}

.notice {
  font-size: 0.6875rem;
  color: #fbbf24;
  font-style: italic;
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 0.25rem;
  margin-top: 0.75rem;
}
</style>
