<script setup lang="ts">
/**
 * ResidualStabilityCard — Residual pattern stability classification
 *
 * Dev Order 32: Qualitative and observational only.
 * Does NOT validate, calibrate, correct, or recommend changes.
 */
import { GateBadge } from '@/components/shared/workflow'
import type { ResidualStabilitySummary } from '@/types/residualStability'
import {
  getStabilityLevelLabel,
  getStabilityGateColor,
} from '@/utils/acoustics/residualStability'
import { getTrendDirectionLabel } from '@/utils/acoustics/residualTrend'
import type { ResidualTrendDirection } from '@/types/residualTrend'

const props = defineProps<{
  summary: ResidualStabilitySummary
}>()
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">{{ summary.label }}</span>
      <GateBadge
        :gate="getStabilityGateColor(summary.level)"
        :label="getStabilityLevelLabel(summary.level)"
      />
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
        <span :class="[$style.countValue, $style.countSmall]">
          {{ summary.smallResidualCount }}
        </span>
        <span :class="$style.countLabel">Small</span>
      </div>
      <div :class="$style.countItem">
        <span :class="[$style.countValue, $style.countModerate]">
          {{ summary.moderateResidualCount }}
        </span>
        <span :class="$style.countLabel">Moderate</span>
      </div>
      <div :class="$style.countItem">
        <span :class="[$style.countValue, $style.countLarge]">
          {{ summary.largeResidualCount }}
        </span>
        <span :class="$style.countLabel">Large</span>
      </div>
    </div>

    <!-- Trend direction -->
    <div v-if="summary.availableResidualCount > 0" :class="$style.trendInfo">
      <span :class="$style.trendLabel">Trend Direction:</span>
      <span :class="$style.trendValue">
        {{ getTrendDirectionLabel(summary.trendDirection as ResidualTrendDirection) }}
      </span>
    </div>

    <!-- Caution -->
    <div :class="$style.caution">
      {{ summary.caution }}
    </div>

    <!-- Notes -->
    <div :class="$style.notes">
      <p v-for="(note, i) in summary.notes" :key="i">{{ note }}</p>
    </div>

    <!-- Notice -->
    <div :class="$style.notice">
      Stability classification is qualitative and observational only. It does not validate or
      calibrate the model.
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

.countSmall {
  color: #10b981;
}

.countModerate {
  color: #fbbf24;
}

.countLarge {
  color: #ef4444;
}

.countLabel {
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trendInfo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
}

.trendLabel {
  font-size: 0.6875rem;
  color: #6b7280;
}

.trendValue {
  font-size: 0.75rem;
  font-weight: 500;
  color: #f9fafb;
}

.caution {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #fbbf24;
}

.notes {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
}

.notes p {
  margin: 0;
  font-size: 0.625rem;
  color: #6b7280;
}

.notes p + p {
  margin-top: 0.125rem;
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
