<script setup lang="ts">
/**
 * Engineering Estimator View (Pro Feature)
 *
 * Thin wrapper that calls backend API for all estimation logic.
 * UI-only component - no business logic duplication.
 */
import { ref, computed, watch } from "vue";
import { businessEstimator } from "@/sdk/endpoints";
import type {
  EstimateRequest,
  EstimateResult,
  ComplexityFactors,
  LearningCurveProjection,
} from "@/types/businessEstimator";
import EstimatorInputsPanel from "./EstimatorInputsPanel.vue";

// ============================================================================
// STATE
// ============================================================================

const loading = ref(false);
const error = ref<string | null>(null);
const factors = ref<ComplexityFactors | null>(null);
const estimate = ref<EstimateResult | null>(null);
const learningCurve = ref<LearningCurveProjection | null>(null);
const activeTab = ref<"wbs" | "learning" | "materials" | "summary">("summary");

// Form state
const form = ref<EstimateRequest>({
  instrument_type: "acoustic_dreadnought",
  builder_experience: "intermediate",
  body_complexity: "standard",
  binding_body_complexity: "none",
  neck_complexity: "standard",
  fretboard_inlay: "dots",
  finish_type: "nitro_solid",
  rosette_complexity: "simple_rings",
  batch_size: 1,
  hourly_rate: 45,
  include_materials: true,
});

// ============================================================================
// COMPUTED
// ============================================================================

const totalPrice = computed(() => {
  if (!estimate.value) return null;
  return businessEstimator.formatCurrency(estimate.value.total_cost_per_unit);
});

const priceRange = computed(() => {
  if (!estimate.value) return null;
  return `${businessEstimator.formatCurrency(estimate.value.estimate_range_low)} – ${businessEstimator.formatCurrency(estimate.value.estimate_range_high)}`;
});

// ============================================================================
// ACTIONS
// ============================================================================

async function loadFactors() {
  try {
    factors.value = await businessEstimator.getComplexityFactors();
  } catch (e) {
    console.error("Failed to load complexity factors:", e);
  }
}

async function runEstimate() {
  loading.value = true;
  error.value = null;
  try {
    estimate.value = await businessEstimator.createEstimate(form.value);

    // Also load learning curve if batch > 1
    if (form.value.batch_size && form.value.batch_size > 1) {
      learningCurve.value = await businessEstimator.getLearningCurveProjection({
        first_unit_hours: estimate.value.first_unit_hours,
        quantity: form.value.batch_size,
        learning_rate: 0.85,
        hourly_rate: form.value.hourly_rate,
      });
    } else {
      learningCurve.value = null;
    }
  } catch (e: any) {
    error.value = e.message || "Estimation failed";
    estimate.value = null;
  } finally {
    loading.value = false;
  }
}

// Auto-run estimate when form changes (debounced)
let debounceTimer: ReturnType<typeof setTimeout>;
watch(
  form,
  () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runEstimate, 500);
  },
  { deep: true }
);

// Initial load
loadFactors();
runEstimate();
</script>

<template>
  <div class="estimator">
    <!-- Header -->
    <header class="estimator-header">
      <div class="header-left">
        <h1>Engineering Estimator</h1>
        <p class="subtitle">WBS · Complexity Factors · Learning Curve · Material Yield</p>
      </div>
      <div class="header-right" v-if="estimate">
        <div class="price-display">{{ totalPrice }}</div>
        <div class="price-label">Estimated Cost</div>
        <div class="price-range">{{ priceRange }}</div>
      </div>
    </header>

    <div class="estimator-body">
      <!-- Left: Inputs -->
      <EstimatorInputsPanel v-model="form" />

      <!-- Right: Results -->
      <main class="results-panel">
        <!-- Loading -->
        <div v-if="loading" class="loading">Calculating...</div>

        <!-- Error -->
        <div v-else-if="error" class="error">{{ error }}</div>

        <!-- Results -->
        <template v-else-if="estimate">
          <!-- KPI Strip -->
          <div class="kpi-strip">
            <div class="kpi">
              <div class="kpi-value">{{ estimate.total_hours.toFixed(1) }}h</div>
              <div class="kpi-label">Total Hours</div>
            </div>
            <div class="kpi">
              <div class="kpi-value">${{ estimate.labor_cost_per_unit.toFixed(0) }}</div>
              <div class="kpi-label">Labor Cost</div>
            </div>
            <div class="kpi">
              <div class="kpi-value">${{ estimate.material_cost_per_unit.toFixed(0) }}</div>
              <div class="kpi-label">Materials</div>
            </div>
            <div class="kpi">
              <div class="kpi-value">{{ estimate.total_complexity_multiplier.toFixed(2) }}×</div>
              <div class="kpi-label">Complexity</div>
            </div>
          </div>

          <!-- Tabs -->
          <div class="tabs">
            <button :class="{ active: activeTab === 'summary' }" @click="activeTab = 'summary'">Summary</button>
            <button :class="{ active: activeTab === 'wbs' }" @click="activeTab = 'wbs'">WBS Breakdown</button>
            <button :class="{ active: activeTab === 'materials' }" @click="activeTab = 'materials'">Materials</button>
            <button :class="{ active: activeTab === 'learning' }" @click="activeTab = 'learning'">Learning Curve</button>
          </div>

          <!-- Summary Tab -->
          <div v-if="activeTab === 'summary'" class="tab-content">
            <div class="summary-grid">
              <div class="summary-item">
                <span class="label">Instrument</span>
                <span class="value">{{ estimate.instrument_type }}</span>
              </div>
              <div class="summary-item">
                <span class="label">Experience</span>
                <span class="value">{{ estimate.experience_level }} ({{ estimate.experience_multiplier }}×)</span>
              </div>
              <div class="summary-item">
                <span class="label">First Unit Hours</span>
                <span class="value">{{ estimate.first_unit_hours.toFixed(1) }}h</span>
              </div>
              <div class="summary-item">
                <span class="label">Avg Hours/Unit</span>
                <span class="value">{{ estimate.average_hours_per_unit.toFixed(1) }}h</span>
              </div>
              <div class="summary-item">
                <span class="label">Confidence</span>
                <span class="value">{{ estimate.confidence_level }}</span>
              </div>
              <div class="summary-item highlight">
                <span class="label">Total Cost</span>
                <span class="value">${{ estimate.total_cost_per_unit.toFixed(0) }}</span>
              </div>
            </div>

            <div v-if="estimate.notes.length" class="notes">
              <h4>Notes</h4>
              <ul>
                <li v-for="(note, i) in estimate.notes" :key="i">{{ note }}</li>
              </ul>
            </div>

            <div v-if="estimate.risk_factors.length" class="risks">
              <h4>Risk Factors</h4>
              <ul>
                <li v-for="(risk, i) in estimate.risk_factors" :key="i">{{ risk }}</li>
              </ul>
            </div>
          </div>

          <!-- WBS Tab -->
          <div v-if="activeTab === 'wbs'" class="tab-content">
            <table class="wbs-table">
              <thead>
                <tr>
                  <th>Task</th>
                  <th class="num">Base</th>
                  <th class="num">Adjusted</th>
                  <th class="num">Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="task in estimate.wbs_tasks" :key="task.task_id">
                  <td>
                    <span
                      class="group-indicator"
                      :style="{ background: businessEstimator.getGroupColor(task.notes) }"
                    ></span>
                    {{ task.task_name }}
                  </td>
                  <td class="num">{{ task.base_hours.toFixed(1) }}h</td>
                  <td class="num">{{ task.adjusted_hours.toFixed(1) }}h</td>
                  <td class="num">${{ task.labor_cost.toFixed(0) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td><strong>Total</strong></td>
                  <td class="num">—</td>
                  <td class="num"><strong>{{ estimate.total_hours.toFixed(1) }}h</strong></td>
                  <td class="num"><strong>${{ estimate.labor_cost_per_unit.toFixed(0) }}</strong></td>
                </tr>
              </tfoot>
            </table>
          </div>

          <!-- Materials Tab -->
          <div v-if="activeTab === 'materials'" class="tab-content">
            <table class="materials-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th class="num">Base Cost</th>
                  <th class="num">Waste Factor</th>
                  <th class="num">Adjusted</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(mat, i) in estimate.material_breakdown" :key="i">
                  <td>{{ mat.category }}</td>
                  <td class="num">${{ mat.base_cost.toFixed(0) }}</td>
                  <td class="num">{{ mat.waste_factor.toFixed(2) }}×</td>
                  <td class="num">${{ mat.adjusted_cost.toFixed(0) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="3"><strong>Total Materials</strong></td>
                  <td class="num"><strong>${{ estimate.material_cost_per_unit.toFixed(0) }}</strong></td>
                </tr>
              </tfoot>
            </table>
          </div>

          <!-- Learning Curve Tab -->
          <div v-if="activeTab === 'learning'" class="tab-content">
            <p v-if="!learningCurve" class="muted">
              Set batch size > 1 to see learning curve projection.
            </p>
            <template v-else>
              <div class="lc-stats">
                <div class="stat">
                  <span class="value">{{ learningCurve.first_unit_hours.toFixed(1) }}h</span>
                  <span class="label">First Unit</span>
                </div>
                <div class="stat">
                  <span class="value">{{ learningCurve.average_hours_per_unit.toFixed(1) }}h</span>
                  <span class="label">Average/Unit</span>
                </div>
                <div class="stat">
                  <span class="value">{{ learningCurve.efficiency_gain_pct.toFixed(1) }}%</span>
                  <span class="label">Efficiency Gain</span>
                </div>
              </div>
              <div class="lc-chart">
                <div
                  v-for="point in learningCurve.points"
                  :key="point.unit_number"
                  class="lc-bar"
                  :style="{
                    height: `${(point.hours_per_unit / learningCurve.first_unit_hours) * 100}%`,
                  }"
                  :title="`Unit ${point.unit_number}: ${point.hours_per_unit.toFixed(1)}h`"
                >
                  <span class="unit-label">{{ point.unit_number }}</span>
                </div>
              </div>
            </template>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<style scoped>
.estimator {
  font-family: "Courier New", monospace;
  background: #0a0d14;
  color: #c8ccd4;
  min-height: 100vh;
}

.estimator-header {
  background: #0d1020;
  border-bottom: 1px solid #1e2438;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.estimator-header h1 {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 4px;
  color: #f0c060;
  margin: 0;
}

.subtitle {
  font-size: 9px;
  letter-spacing: 3px;
  color: #4060c0;
  margin: 4px 0 0;
  text-transform: uppercase;
}

.header-right {
  text-align: right;
}

.price-display {
  font-size: 24px;
  font-weight: 700;
  color: #60e0a0;
}

.price-label {
  font-size: 9px;
  color: #404870;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.price-range {
  font-size: 11px;
  color: #506090;
  margin-top: 2px;
}

.estimator-body {
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
  gap: 16px;
}

.results-panel {
  flex: 1;
}

.loading,
.error {
  padding: 40px;
  text-align: center;
  color: #506090;
}

.error {
  color: #f06060;
}

.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.kpi {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 3px;
  padding: 12px;
  text-align: center;
}

.kpi-value {
  font-size: 18px;
  font-weight: 700;
  color: #60e0a0;
}

.kpi-label {
  font-size: 9px;
  color: #404870;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-top: 4px;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #1e2438;
  margin-bottom: 16px;
}

.tabs button {
  padding: 8px 16px;
  font-size: 10px;
  letter-spacing: 2px;
  text-transform: uppercase;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #506090;
  cursor: pointer;
  font-family: inherit;
}

.tabs button.active {
  color: #f0c060;
  border-bottom-color: #f0c060;
  background: #14192a;
}

.tab-content {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 3px;
  padding: 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.summary-item {
  padding: 8px;
  background: #14192a;
  border-radius: 3px;
}

.summary-item .label {
  display: block;
  font-size: 9px;
  color: #506090;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.summary-item .value {
  display: block;
  font-size: 14px;
  color: #c0c8e0;
  margin-top: 4px;
}

.summary-item.highlight {
  background: #1a2030;
  border: 1px solid #304080;
}

.summary-item.highlight .value {
  color: #60e0a0;
  font-weight: 700;
}

.notes,
.risks {
  margin-top: 16px;
}

.notes h4,
.risks h4 {
  font-size: 10px;
  color: #506090;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin: 0 0 8px;
}

.notes ul,
.risks ul {
  margin: 0;
  padding-left: 16px;
  font-size: 11px;
  color: #8890a8;
}

.risks ul li {
  color: #f0c060;
}

.wbs-table,
.materials-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.wbs-table th,
.materials-table th {
  text-align: left;
  font-size: 9px;
  letter-spacing: 2px;
  color: #404870;
  text-transform: uppercase;
  padding: 8px 4px;
  border-bottom: 1px solid #1e2438;
}

.wbs-table td,
.materials-table td {
  padding: 6px 4px;
  border-bottom: 1px solid #13172a;
  color: #a0a8c0;
}

.wbs-table .num,
.materials-table .num {
  text-align: right;
  color: #7080a0;
}

.wbs-table tfoot td,
.materials-table tfoot td {
  border-top: 1px solid #2a3040;
  color: #60e0a0;
}

.group-indicator {
  display: inline-block;
  width: 3px;
  height: 12px;
  margin-right: 8px;
  border-radius: 1px;
  vertical-align: middle;
}

.muted {
  color: #506090;
  font-style: italic;
}

.lc-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.lc-stats .stat {
  text-align: center;
}

.lc-stats .value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #60e0a0;
}

.lc-stats .label {
  font-size: 9px;
  color: #506090;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.lc-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 120px;
  padding: 8px;
  background: #14192a;
  border-radius: 3px;
}

.lc-bar {
  flex: 1;
  background: linear-gradient(to top, #34d399, #60e0a0);
  border-radius: 2px 2px 0 0;
  min-height: 4px;
  position: relative;
  cursor: default;
}

.lc-bar .unit-label {
  position: absolute;
  bottom: -18px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 8px;
  color: #506090;
}
</style>
