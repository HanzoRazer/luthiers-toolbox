<script setup lang="ts">
/**
 * ResidualCoherenceCard — Consolidated residual coherence summary
 *
 * Dev Order 33: Synthesizes interpretation, trend, and stability
 * into a single observational coherence summary.
 * Does NOT calibrate, validate, or correct the model.
 */
import { GateBadge } from '@/components/shared/workflow'
import type { ResidualCoherenceSummary } from '@/types/residualCoherence'
import {
  getCoherenceLevelLabel,
  getCoherenceGateColor,
} from '@/utils/acoustics/residualCoherence'

const props = defineProps<{
  summary: ResidualCoherenceSummary
}>()
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">{{ summary.label }}</span>
      <GateBadge
        :gate="getCoherenceGateColor(summary.level)"
        :label="getCoherenceLevelLabel(summary.level)"
      />
    </div>

    <!-- Message -->
    <p :class="$style.message">{{ summary.message }}</p>

    <!-- Linked Diagnostic Metadata -->
    <div v-if="summary.interpretationLevel || summary.trendDirection || summary.stabilityLevel" :class="$style.metadata">
      <div v-if="summary.interpretationLevel" :class="$style.metaItem">
        <span :class="$style.metaLabel">Interpretation:</span>
        <span :class="$style.metaValue">{{ summary.interpretationLevel }}</span>
      </div>
      <div v-if="summary.trendDirection" :class="$style.metaItem">
        <span :class="$style.metaLabel">Trend:</span>
        <span :class="$style.metaValue">{{ summary.trendDirection }}</span>
      </div>
      <div v-if="summary.stabilityLevel" :class="$style.metaItem">
        <span :class="$style.metaLabel">Stability:</span>
        <span :class="$style.metaValue">{{ summary.stabilityLevel }}</span>
      </div>
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
      Residual coherence summarizes observational diagnostic layers only. It does not calibrate,
      validate, or correct the model.
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

.metadata {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
}

.metaItem {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
}

.metaLabel {
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metaValue {
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
