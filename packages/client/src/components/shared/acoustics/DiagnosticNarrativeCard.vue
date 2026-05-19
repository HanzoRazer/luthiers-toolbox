<script setup lang="ts">
/**
 * DiagnosticNarrativeCard — Human-readable diagnostic summary
 *
 * Dev Order 34: Deterministic rule-based narrative synthesis.
 * Does NOT calibrate, validate, optimize, or predict.
 */
import { GateBadge } from '@/components/shared/workflow'
import type { DiagnosticNarrativeSummary } from '@/types/diagnosticNarrative'
import {
  getNarrativeToneLabel,
  getNarrativeGateColor,
} from '@/utils/acoustics/diagnosticNarrative'

const props = defineProps<{
  summary: DiagnosticNarrativeSummary
}>()
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">{{ summary.label }}</span>
      <GateBadge
        :gate="getNarrativeGateColor(summary.tone)"
        :label="getNarrativeToneLabel(summary.tone)"
      />
    </div>

    <!-- Narrative -->
    <div :class="$style.narrativeBlock">
      <p :class="$style.narrative">{{ summary.narrative }}</p>
    </div>

    <!-- Supporting Observations -->
    <div v-if="summary.supportingObservations.length > 0" :class="$style.observations">
      <span :class="$style.observationsLabel">Supporting Observations</span>
      <ul :class="$style.observationsList">
        <li v-for="(obs, i) in summary.supportingObservations" :key="i">{{ obs }}</li>
      </ul>
    </div>

    <!-- Provenance Reminder -->
    <div :class="$style.provenance">
      {{ summary.provenanceReminder }}
    </div>

    <!-- Caution -->
    <div :class="$style.caution">
      {{ summary.caution }}
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

.narrativeBlock {
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
  border-left: 3px solid #6366f1;
}

.narrative {
  margin: 0;
  font-size: 0.8125rem;
  color: #e5e7eb;
  line-height: 1.5;
}

.observations {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
}

.observationsLabel {
  display: block;
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.observationsList {
  margin: 0;
  padding-left: 1rem;
  font-size: 0.75rem;
  color: #9ca3af;
}

.observationsList li {
  margin-bottom: 0.125rem;
}

.observationsList li:last-child {
  margin-bottom: 0;
}

.provenance {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #a5b4fc;
  font-style: italic;
}

.caution {
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #fbbf24;
}
</style>
