<script setup lang="ts">
/**
 * BackCalcTab - Back-calculate from target price
 *
 * Given a target selling price, calculates:
 * - Required hourly rate to achieve target
 * - Profit margin at current rate
 * - Break-even analysis
 */
import { ref, computed, watch } from "vue";
import type { EstimateResult } from "@/types/businessEstimator";

const props = defineProps<{
  estimate: EstimateResult;
  currentHourlyRate: number;
}>();

const emit = defineEmits<{
  updateHourlyRate: [rate: number];
}>();

// ============================================================================
// STATE
// ============================================================================

const targetPrice = ref<number>(0);
const targetMarginPct = ref<number>(20);

// Initialize target price from estimate
watch(() => props.estimate, (est) => {
  if (est && targetPrice.value === 0) {
    // Default to 20% markup
    targetPrice.value = Math.round(est.total_cost_per_unit * 1.2);
  }
}, { immediate: true });

// ============================================================================
// COMPUTED
// ============================================================================

// Current profit/loss at target price
const profitAtTarget = computed(() => {
  return targetPrice.value - props.estimate.total_cost_per_unit;
});

const marginPctAtTarget = computed(() => {
  if (targetPrice.value === 0) return 0;
  return (profitAtTarget.value / targetPrice.value) * 100;
});

const isProfitable = computed(() => profitAtTarget.value > 0);

// Back-calculate hourly rate to hit target
const requiredHourlyRate = computed(() => {
  if (props.estimate.total_hours === 0) return 0;

  // Target = (hours * rate) + materials
  // rate = (target - materials) / hours
  const laborRequired = targetPrice.value - props.estimate.material_cost_per_unit;
  return laborRequired / props.estimate.total_hours;
});

const hourlyRateDelta = computed(() => {
  return requiredHourlyRate.value - props.currentHourlyRate;
});

// Target price from margin
const priceFromMargin = computed(() => {
  // price = cost / (1 - margin)
  return props.estimate.total_cost_per_unit / (1 - targetMarginPct.value / 100);
});

// Break-even price (cost only)
const breakEvenPrice = computed(() => {
  return props.estimate.total_cost_per_unit;
});

// Minimum viable price (cost + 10%)
const minViablePrice = computed(() => {
  return props.estimate.total_cost_per_unit * 1.1;
});

// ============================================================================
// ACTIONS
// ============================================================================

function applyCalculatedRate() {
  emit("updateHourlyRate", Math.round(requiredHourlyRate.value));
}

function setTargetFromMargin() {
  targetPrice.value = Math.round(priceFromMargin.value);
}

// ============================================================================
// HELPERS
// ============================================================================

function formatCurrency(value: number): string {
  return `$${value.toFixed(0)}`;
}

function formatRate(value: number): string {
  return `$${value.toFixed(2)}/hr`;
}
</script>

<template>
  <div class="backcalc-tab">
    <!-- Target Price Input -->
    <section class="input-section">
      <h3>Target Selling Price</h3>
      <div class="price-input-row">
        <span class="currency">$</span>
        <input
          v-model.number="targetPrice"
          type="number"
          min="0"
          step="50"
          class="price-input"
        />
      </div>
      <div class="quick-targets">
        <button type="button" @click="targetPrice = breakEvenPrice">
          Break-even ({{ formatCurrency(breakEvenPrice) }})
        </button>
        <button type="button" @click="targetPrice = minViablePrice">
          +10% ({{ formatCurrency(minViablePrice) }})
        </button>
        <button type="button" @click="setTargetFromMargin">
          +{{ targetMarginPct }}% margin
        </button>
      </div>
    </section>

    <!-- Margin Calculator -->
    <section class="input-section">
      <h3>Target Margin</h3>
      <div class="margin-row">
        <input
          v-model.number="targetMarginPct"
          type="range"
          min="0"
          max="50"
          step="5"
        />
        <span class="margin-value">{{ targetMarginPct }}%</span>
      </div>
      <p class="margin-hint">
        At {{ targetMarginPct }}% margin: {{ formatCurrency(priceFromMargin) }}
      </p>
    </section>

    <!-- Analysis Results -->
    <section class="results-section">
      <h3>Analysis</h3>

      <div class="result-grid">
        <!-- Profit/Loss -->
        <div class="result-card" :class="isProfitable ? 'positive' : 'negative'">
          <span class="result-label">Profit/Loss</span>
          <span class="result-value">
            {{ isProfitable ? '+' : '' }}{{ formatCurrency(profitAtTarget) }}
          </span>
          <span class="result-detail">
            {{ marginPctAtTarget.toFixed(1) }}% margin
          </span>
        </div>

        <!-- Required Rate -->
        <div class="result-card" :class="hourlyRateDelta >= 0 ? 'warning' : 'positive'">
          <span class="result-label">Required Rate</span>
          <span class="result-value">{{ formatRate(requiredHourlyRate) }}</span>
          <span class="result-detail">
            {{ hourlyRateDelta >= 0 ? '+' : '' }}{{ formatRate(hourlyRateDelta) }} vs current
          </span>
        </div>

        <!-- Current Cost -->
        <div class="result-card neutral">
          <span class="result-label">Current Cost</span>
          <span class="result-value">{{ formatCurrency(estimate.total_cost_per_unit) }}</span>
          <span class="result-detail">
            {{ estimate.total_hours.toFixed(1) }}h @ {{ formatRate(currentHourlyRate) }}
          </span>
        </div>

        <!-- Materials -->
        <div class="result-card neutral">
          <span class="result-label">Materials (Fixed)</span>
          <span class="result-value">{{ formatCurrency(estimate.material_cost_per_unit) }}</span>
          <span class="result-detail">
            Cannot reduce via rate change
          </span>
        </div>
      </div>
    </section>

    <!-- Action -->
    <section v-if="requiredHourlyRate > 0 && requiredHourlyRate !== currentHourlyRate" class="action-section">
      <button
        type="button"
        class="apply-rate-btn"
        @click="applyCalculatedRate"
      >
        Apply {{ formatRate(requiredHourlyRate) }} and Recalculate
      </button>
      <p class="action-hint">
        This will update your hourly rate and re-run the estimate.
      </p>
    </section>

    <!-- Warning for below-cost -->
    <section v-if="targetPrice < breakEvenPrice && targetPrice > 0" class="warning-section">
      <div class="warning-banner">
        <span class="warning-icon">!</span>
        <div class="warning-content">
          <strong>Below Cost Warning</strong>
          <p>
            Target price {{ formatCurrency(targetPrice) }} is below break-even
            ({{ formatCurrency(breakEvenPrice) }}). You would lose
            {{ formatCurrency(breakEvenPrice - targetPrice) }} per unit.
          </p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.backcalc-tab {
  padding: 16px;
}

.input-section,
.results-section,
.action-section,
.warning-section {
  margin-bottom: 20px;
}

h3 {
  font-size: 10px;
  letter-spacing: 2px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0 0 12px;
}

/* Price Input */
.price-input-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 10px;
}

.currency {
  font-size: 18px;
  color: #60e0a0;
  font-weight: 700;
}

.price-input {
  width: 120px;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #60e0a0;
  padding: 8px 12px;
  font-size: 18px;
  font-weight: 700;
  font-family: inherit;
  border-radius: 3px;
}

.quick-targets {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-targets button {
  padding: 6px 10px;
  font-size: 10px;
  font-family: inherit;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #8090b0;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.quick-targets button:hover {
  border-color: #4060c0;
  color: #c0c8e0;
}

/* Margin Slider */
.margin-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.margin-row input[type="range"] {
  flex: 1;
  accent-color: #4080f0;
}

.margin-value {
  font-size: 14px;
  font-weight: 700;
  color: #80a0d0;
  min-width: 40px;
}

.margin-hint {
  font-size: 11px;
  color: #606888;
  margin: 8px 0 0;
}

/* Result Grid */
.result-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.result-card {
  background: #14192a;
  border-radius: 4px;
  padding: 12px;
  border-left: 3px solid #2a3040;
}

.result-card.positive {
  border-left-color: #60e0a0;
}

.result-card.negative {
  border-left-color: #f06060;
}

.result-card.warning {
  border-left-color: #f0a060;
}

.result-card.neutral {
  border-left-color: #4060c0;
}

.result-label {
  display: block;
  font-size: 9px;
  letter-spacing: 1px;
  color: #506090;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.result-value {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #c0c8e0;
  margin-bottom: 2px;
}

.result-card.positive .result-value {
  color: #60e0a0;
}

.result-card.negative .result-value {
  color: #f06060;
}

.result-card.warning .result-value {
  color: #f0a060;
}

.result-detail {
  display: block;
  font-size: 10px;
  color: #606888;
}

/* Action Section */
.apply-rate-btn {
  width: 100%;
  padding: 12px;
  font-size: 11px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  background: #2050a0;
  border: 1px solid #3060c0;
  color: #e0e8ff;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.apply-rate-btn:hover {
  background: #2860c0;
}

.action-hint {
  font-size: 10px;
  color: #506090;
  text-align: center;
  margin: 8px 0 0;
}

/* Warning Banner */
.warning-banner {
  display: flex;
  gap: 12px;
  background: #2a1a10;
  border: 1px solid #804020;
  border-radius: 4px;
  padding: 12px;
}

.warning-icon {
  font-size: 18px;
  font-weight: 700;
  color: #f0a060;
  line-height: 1;
}

.warning-content {
  flex: 1;
}

.warning-content strong {
  display: block;
  font-size: 11px;
  color: #f0a060;
  margin-bottom: 4px;
}

.warning-content p {
  font-size: 11px;
  color: #c0a080;
  margin: 0;
  line-height: 1.4;
}
</style>
