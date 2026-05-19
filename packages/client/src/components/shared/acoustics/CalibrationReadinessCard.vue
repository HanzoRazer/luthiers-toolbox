<script setup lang="ts">
/**
 * CalibrationReadinessCard — Display calibration readiness status
 *
 * Dev Order 22: Calibration readiness layer.
 * Shows whether data is sufficient for future calibration.
 * Does NOT perform calibration or prediction.
 */
import { computed } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import type { CalibrationReadiness } from '@/types/calibration'

const props = defineProps<{
  readiness: CalibrationReadiness
}>()

const statusLabel = computed(() => {
  switch (props.readiness.overallGate) {
    case 'green':
      return 'Ready for future calibration'
    case 'yellow':
      return 'Partially ready'
    case 'red':
      return 'Not ready for calibration'
    default:
      return 'Unknown'
  }
})

const hasDiagnostics = computed(() => props.readiness.diagnostics.length > 0)
const hasMissingFields = computed(() => props.readiness.missingFields.length > 0)
const hasWarnings = computed(() => props.readiness.warnings.length > 0)
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <SectionLabel text="Calibration Readiness" />
      <GateBadge :gate="readiness.overallGate" :label="statusLabel" />
    </div>

    <!-- Diagnostics -->
    <div v-if="hasDiagnostics" :class="$style.diagnostics">
      <div
        v-for="diag in readiness.diagnostics"
        :key="diag.id"
        :class="[$style.diagnostic, $style[`diagnostic--${diag.gate}`]]"
      >
        <span :class="$style.diagMessage">{{ diag.message }}</span>
        <span v-if="diag.recommendedAction" :class="$style.diagAction">
          {{ diag.recommendedAction }}
        </span>
      </div>
    </div>

    <!-- Missing Fields -->
    <div v-if="hasMissingFields" :class="$style.section">
      <span :class="$style.sectionLabel">Missing:</span>
      <ul :class="$style.list">
        <li v-for="field in readiness.missingFields" :key="field">{{ field }}</li>
      </ul>
    </div>

    <!-- Warnings -->
    <div v-if="hasWarnings" :class="$style.section">
      <span :class="$style.sectionLabel">Warnings:</span>
      <ul :class="$style.list">
        <li v-for="warning in readiness.warnings" :key="warning">{{ warning }}</li>
      </ul>
    </div>

    <!-- Green status message -->
    <div v-if="readiness.readyForCalibration" :class="$style.readyMessage">
      All required data is present. Calibration can proceed when implemented.
    </div>

    <!-- Explanatory notice -->
    <div :class="$style.notice">
      Calibration readiness only checks data completeness and provenance. It does not perform
      calibration or prediction.
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

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
}

.diagnostics {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.diagnostic {
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.diagnostic--red {
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid #ef4444;
}

.diagnostic--yellow {
  background: rgba(251, 191, 36, 0.1);
  border-left: 3px solid #fbbf24;
}

.diagnostic--green {
  background: rgba(16, 185, 129, 0.1);
  border-left: 3px solid #10b981;
}

.diagMessage {
  display: block;
  color: #f9fafb;
  font-weight: 500;
}

.diagAction {
  display: block;
  color: #9ca3af;
  font-size: 0.6875rem;
  margin-top: 0.25rem;
}

.section {
  margin-bottom: 0.75rem;
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

.list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.75rem;
  color: #d1d5db;
}

.list li {
  line-height: 1.5;
}

.readyMessage {
  font-size: 0.75rem;
  color: #10b981;
  padding: 0.5rem 0.75rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.75rem;
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
