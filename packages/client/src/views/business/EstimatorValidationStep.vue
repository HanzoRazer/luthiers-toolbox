<script setup lang="ts">
/**
 * EstimatorValidationStep - Intent preview before running estimate
 *
 * Shows a plain-language preview of what the system will calculate:
 * - Complexity factors that will be applied
 * - Experience multiplier
 * - Learning curve parameters (if batch > 1)
 * - Material yield factors
 *
 * This is generated client-side from form state - no API call needed.
 */
import { computed } from "vue";
import type { EstimateRequest, BodyComplexity } from "@/types/businessEstimator";
import RiskBadge from "@/components/ui/RiskBadge.vue";
import {
  instrumentTypes,
  experienceLevels,
  bodyOptions,
  bindingOptions,
  neckOptions,
  inlayOptions,
  finishOptions,
  rosetteOptions,
} from "./estimatorOptions";

const props = defineProps<{
  request: EstimateRequest;
}>();

const emit = defineEmits<{
  proceed: [];
  back: [];
}>();

// ============================================================================
// COMPLEXITY FACTOR ESTIMATES (client-side approximations)
// ============================================================================

const BODY_FACTORS: Record<BodyComplexity, number> = {
  standard: 1.0,
  cutaway_soft: 1.1,
  cutaway_florentine: 1.25,
  cutaway_venetian: 1.2,
  double_cutaway: 1.4,
  arm_bevel: 1.1,
  tummy_cut: 1.1,
  carved_top: 1.6,
};

const EXPERIENCE_FACTORS: Record<string, number> = {
  beginner: 1.5,
  intermediate: 1.2,
  experienced: 1.0,
  master: 0.85,
};

const FINISH_FACTORS: Record<string, number> = {
  oil: 0.5,
  wax: 0.45,
  shellac_wipe: 0.8,
  shellac_french_polish: 2.2,
  nitro_solid: 1.0,
  nitro_burst: 1.45,
  nitro_vintage: 1.6,
  poly_solid: 0.75,
  poly_burst: 1.1,
};

// ============================================================================
// COMPUTED
// ============================================================================

const instrumentLabel = computed(() => {
  return instrumentTypes.find(i => i.value === props.request.instrument_type)?.label ?? props.request.instrument_type;
});

const experienceLabel = computed(() => {
  return experienceLevels.find(e => e.value === props.request.builder_experience)?.label ?? props.request.builder_experience;
});

const experienceFactor = computed(() => {
  return EXPERIENCE_FACTORS[props.request.builder_experience] ?? 1.0;
});

const bodyComplexityArray = computed<BodyComplexity[]>(() => {
  const bc = props.request.body_complexity;
  if (Array.isArray(bc)) return bc;
  return bc ? [bc] : ["standard"];
});

const bodyLabels = computed(() => {
  return bodyComplexityArray.value.map(v =>
    bodyOptions.find(b => b.value === v)?.label ?? v
  );
});

const bodyFactor = computed(() => {
  // Combined body complexity factor (multiplicative)
  return bodyComplexityArray.value.reduce((acc, v) => {
    const factor = BODY_FACTORS[v] ?? 1.0;
    // Only multiply factors > 1 (standard is baseline)
    return v === "standard" ? acc : acc * factor;
  }, 1.0);
});

const finishLabel = computed(() => {
  return finishOptions.find(f => f.value === props.request.finish_type)?.label ?? props.request.finish_type;
});

const finishFactor = computed(() => {
  return FINISH_FACTORS[props.request.finish_type] ?? 1.0;
});

const bindingLabel = computed(() => {
  return bindingOptions.find(b => b.value === props.request.binding_body_complexity)?.label ?? props.request.binding_body_complexity;
});

const neckLabel = computed(() => {
  return neckOptions.find(n => n.value === props.request.neck_complexity)?.label ?? props.request.neck_complexity;
});

const inlayLabel = computed(() => {
  return inlayOptions.find(i => i.value === props.request.fretboard_inlay)?.label ?? props.request.fretboard_inlay;
});

const rosetteLabel = computed(() => {
  return rosetteOptions.find(r => r.value === props.request.rosette_complexity)?.label ?? props.request.rosette_complexity;
});

// Estimated combined complexity
const estimatedComplexity = computed(() => {
  return (bodyFactor.value * experienceFactor.value * finishFactor.value).toFixed(2);
});

// Risk assessment based on complexity
const confidenceLevel = computed((): "GREEN" | "YELLOW" | "RED" => {
  const complexity = parseFloat(estimatedComplexity.value);
  if (complexity <= 1.5) return "GREEN";
  if (complexity <= 2.5) return "YELLOW";
  return "RED";
});

const confidenceText = computed(() => {
  switch (confidenceLevel.value) {
    case "GREEN": return "High confidence - standard build parameters";
    case "YELLOW": return "Medium confidence - elevated complexity factors";
    case "RED": return "Low confidence - high complexity introduces scheduling risk";
  }
});

// Intent bullets
const intentBullets = computed(() => {
  const bullets: string[] = [];

  // Body complexity
  if (bodyComplexityArray.value.length > 1 || bodyComplexityArray.value[0] !== "standard") {
    bullets.push(`Apply ${bodyFactor.value.toFixed(2)}x body complexity multiplier (${bodyLabels.value.join(" + ")})`);
  }

  // Finish
  if (finishFactor.value !== 1.0) {
    bullets.push(`Apply ${finishFactor.value.toFixed(2)}x finish factor (${finishLabel.value})`);
  }

  // Experience
  if (experienceFactor.value !== 1.0) {
    bullets.push(`Apply ${experienceFactor.value.toFixed(2)}x experience modifier (${experienceLabel.value})`);
  }

  // Learning curve
  if ((props.request.batch_size ?? 1) > 1) {
    bullets.push(`Use Crawford learning curve at 85% rate across ${props.request.batch_size} units`);
  }

  // Materials
  if (props.request.include_materials) {
    bullets.push("Include material waste estimates: tops 85%, backs 80%, sides 82%");
  }

  // If no special factors
  if (bullets.length === 0) {
    bullets.push("Standard build with baseline complexity factors");
  }

  return bullets;
});
</script>

<template>
  <div class="validation-step">
    <header class="step-header">
      <h2>Intent Preview</h2>
      <p class="subtitle">Review what the system will calculate before proceeding</p>
    </header>

    <!-- Build Summary -->
    <section class="build-summary">
      <div class="summary-row">
        <span class="label">Instrument</span>
        <span class="value">{{ instrumentLabel }}</span>
      </div>
      <div class="summary-row">
        <span class="label">Builder</span>
        <span class="value">{{ experienceLabel }}</span>
      </div>
      <div class="summary-row">
        <span class="label">Body</span>
        <span class="value">{{ bodyLabels.join(", ") }}</span>
      </div>
      <div class="summary-row">
        <span class="label">Finish</span>
        <span class="value">{{ finishLabel }}</span>
      </div>
      <div v-if="(request.batch_size ?? 1) > 1" class="summary-row">
        <span class="label">Batch</span>
        <span class="value">{{ request.batch_size }} units @ ${{ request.hourly_rate }}/hr</span>
      </div>
    </section>

    <!-- Intent Description -->
    <section class="intent-section">
      <h3>Based on your selections, this estimate will:</h3>
      <ul class="intent-list">
        <li v-for="(bullet, i) in intentBullets" :key="i">{{ bullet }}</li>
      </ul>
    </section>

    <!-- Confidence -->
    <section class="confidence-section">
      <div class="confidence-row">
        <span class="label">Estimated Confidence:</span>
        <RiskBadge :level="confidenceLevel" size="md" />
      </div>
      <p class="confidence-text">{{ confidenceText }}</p>
      <p class="complexity-note">
        Combined complexity estimate: <strong>{{ estimatedComplexity }}x</strong>
      </p>
    </section>

    <!-- Actions -->
    <footer class="step-actions">
      <button type="button" class="btn-secondary" @click="emit('back')">
        Back to Inputs
      </button>
      <button type="button" class="btn-primary" @click="emit('proceed')">
        Run Estimate
      </button>
    </footer>
  </div>
</template>

<style scoped>
.validation-step {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 20px;
}

.step-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #1e2438;
}

.step-header h2 {
  font-size: 14px;
  font-weight: 700;
  color: #f0c060;
  margin: 0 0 4px;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.subtitle {
  font-size: 11px;
  color: #506090;
  margin: 0;
}

/* Build Summary */
.build-summary {
  background: #14192a;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 20px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 12px;
}

.summary-row:not(:last-child) {
  border-bottom: 1px solid #1e2438;
}

.summary-row .label {
  color: #506090;
}

.summary-row .value {
  color: #c0c8e0;
  font-weight: 500;
}

/* Intent Section */
.intent-section {
  margin-bottom: 20px;
}

.intent-section h3 {
  font-size: 11px;
  color: #8090b0;
  margin: 0 0 12px;
  font-weight: 500;
}

.intent-list {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: #a0a8c0;
  line-height: 1.8;
}

.intent-list li::marker {
  color: #4060c0;
}

/* Confidence Section */
.confidence-section {
  background: #14192a;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 20px;
}

.confidence-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.confidence-row .label {
  font-size: 11px;
  color: #506090;
}

.confidence-text {
  font-size: 11px;
  color: #8090b0;
  margin: 0 0 8px;
  font-style: italic;
}

.complexity-note {
  font-size: 11px;
  color: #606888;
  margin: 0;
}

.complexity-note strong {
  color: #80a0d0;
}

/* Actions */
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #1e2438;
}

.btn-secondary,
.btn-primary {
  padding: 8px 16px;
  font-size: 11px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary {
  background: #14192a;
  border: 1px solid #2a3040;
  color: #8090b0;
}

.btn-secondary:hover {
  border-color: #4060c0;
  color: #c0c8e0;
}

.btn-primary {
  background: #2050a0;
  border: 1px solid #3060c0;
  color: #e0e8ff;
}

.btn-primary:hover {
  background: #2860c0;
}
</style>
