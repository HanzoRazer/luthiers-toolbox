<script setup lang="ts">
/**
 * ResidualInterpretationCard — Qualitative residual magnitude labels
 *
 * Dev Order 30: Interpretive guidance only.
 * Does NOT calibrate, correct, fit, or validate.
 */
import { GateBadge } from '@/components/shared/workflow'
import type { ResidualInterpretationSummary } from '@/types/residualInterpretation'
import {
  getInterpretationLevelLabel,
  getInterpretationGateColor,
} from '@/utils/acoustics/residualInterpretation'

const props = defineProps<{
  summary: ResidualInterpretationSummary
}>()

function formatResidual(residual: number | undefined, unit: string | undefined): string {
  if (residual === undefined) return '—'
  const sign = residual >= 0 ? '+' : ''
  const suffix = unit ? ` ${unit}` : ''
  return `${sign}${residual.toFixed(1)}${suffix}`
}

function formatPercent(pct: number | null | undefined): string {
  if (pct === null || pct === undefined) return '—'
  const sign = pct >= 0 ? '+' : ''
  return `${sign}${pct.toFixed(1)}%`
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">{{ summary.label }}</span>
      <GateBadge
        :gate="getInterpretationGateColor(summary.overallLevel)"
        :label="getInterpretationLevelLabel(summary.overallLevel)"
      />
    </div>

    <!-- Interpretation items -->
    <div :class="$style.items">
      <div
        v-for="item in summary.items"
        :key="item.id"
        :class="[$style.item, $style[`level--${item.level}`]]"
      >
        <div :class="$style.itemHeader">
          <span :class="$style.itemLabel">{{ item.label }}</span>
          <GateBadge
            :gate="getInterpretationGateColor(item.level)"
            :label="getInterpretationLevelLabel(item.level)"
          />
        </div>

        <div v-if="item.level !== 'insufficient_data'" :class="$style.itemValues">
          <span :class="$style.itemValue">
            Residual: {{ formatResidual(item.residual, item.unit) }}
          </span>
          <span :class="$style.itemValue">
            Percent: {{ formatPercent(item.percentResidual) }}
          </span>
        </div>

        <p :class="$style.itemMessage">{{ item.message }}</p>

        <p v-if="item.caution" :class="$style.itemCaution">{{ item.caution }}</p>
      </div>
    </div>

    <!-- Notes -->
    <div :class="$style.notes">
      <p v-for="(note, i) in summary.notes" :key="i">{{ note }}</p>
    </div>

    <!-- Explanatory notice -->
    <div :class="$style.notice">
      Residual interpretation is qualitative guidance only. It does not calibrate, correct, or
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

.items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.item {
  padding: 0.5rem;
  border-radius: 0.25rem;
  border-left: 3px solid transparent;
}

.level--insufficient_data {
  background: rgba(107, 114, 128, 0.1);
  border-left-color: #6b7280;
}

.level--small {
  background: rgba(16, 185, 129, 0.1);
  border-left-color: #10b981;
}

.level--moderate {
  background: rgba(251, 191, 36, 0.1);
  border-left-color: #fbbf24;
}

.level--large {
  background: rgba(239, 68, 68, 0.1);
  border-left-color: #ef4444;
}

.itemHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.itemLabel {
  font-size: 0.75rem;
  font-weight: 500;
  color: #f9fafb;
}

.itemValues {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.25rem;
}

.itemValue {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.itemMessage {
  margin: 0;
  font-size: 0.6875rem;
  color: #d1d5db;
}

.itemCaution {
  margin: 0.25rem 0 0 0;
  font-size: 0.625rem;
  color: #fbbf24;
  font-style: italic;
}

.notes {
  margin-top: 0.5rem;
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
  margin-top: 0.5rem;
}
</style>
