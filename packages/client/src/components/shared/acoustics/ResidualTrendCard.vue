<script setup lang="ts">
/**
 * ResidualTrendCard — Residual consistency trend indicators
 *
 * Dev Order 31: Observational only.
 * Does NOT calibrate, correct, fit, or recommend changes.
 */
import { GateBadge } from '@/components/shared/workflow'
import type { ResidualTrendSummary } from '@/types/residualTrend'
import { getTrendDirectionLabel } from '@/utils/acoustics/residualTrend'

const props = defineProps<{
  summary: ResidualTrendSummary
}>()
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">{{ summary.label }}</span>
      <GateBadge gate="yellow" :label="getTrendDirectionLabel(summary.direction)" />
    </div>

    <!-- Message -->
    <p :class="$style.message">{{ summary.message }}</p>

    <!-- Counts -->
    <div v-if="summary.availableResidualCount > 0" :class="$style.counts">
      <div :class="$style.countItem">
        <span :class="$style.countValue">{{ summary.availableResidualCount }}</span>
        <span :class="$style.countLabel">Available</span>
      </div>
      <div :class="$style.countItem">
        <span :class="[$style.countValue, $style.countPositive]">
          {{ summary.positiveResidualCount }}
        </span>
        <span :class="$style.countLabel">Positive</span>
      </div>
      <div :class="$style.countItem">
        <span :class="[$style.countValue, $style.countNegative]">
          {{ summary.negativeResidualCount }}
        </span>
        <span :class="$style.countLabel">Negative</span>
      </div>
      <div :class="$style.countItem">
        <span :class="$style.countValue">{{ summary.zeroResidualCount }}</span>
        <span :class="$style.countLabel">Zero</span>
      </div>
    </div>

    <!-- Sign explanation -->
    <div v-if="summary.availableResidualCount > 0" :class="$style.signExplanation">
      <p>Positive: measured &gt; estimated (estimate low)</p>
      <p>Negative: measured &lt; estimated (estimate high)</p>
    </div>

    <!-- Caution -->
    <div :class="$style.caution">
      {{ summary.caution }}
    </div>

    <!-- Notice -->
    <div :class="$style.notice">
      Trend indicators summarize residual direction only. They do not calibrate, correct, or
      validate the model.
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

.message {
  margin: 0 0 0.5rem 0;
  font-size: 0.8125rem;
  color: #d1d5db;
}

.counts {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
}

.countItem {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
}

.countValue {
  font-size: 1rem;
  font-weight: 600;
  color: #f9fafb;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.countPositive {
  color: #10b981;
}

.countNegative {
  color: #ef4444;
}

.countLabel {
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.signExplanation {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
}

.signExplanation p {
  margin: 0;
  font-size: 0.625rem;
  color: #6b7280;
}

.signExplanation p + p {
  margin-top: 0.125rem;
}

.caution {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #fbbf24;
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
