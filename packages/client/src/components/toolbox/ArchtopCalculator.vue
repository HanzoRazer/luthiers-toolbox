<template>
  <div class="archtop-calculator">
    <h2 class="calc-title">Archtop Calculator</h2>
    <p class="calc-subtitle">Calculate archtop guitar bridge height and fit parameters</p>

    <form class="calc-form" @submit.prevent="calculate">
      <div class="form-row">
        <label>Scale Length (mm)</label>
        <input v-model.number="params.scale_length_mm" type="number" step="0.1" min="500" max="700" />
      </div>
      <div class="form-row">
        <label>Neck Angle (deg)</label>
        <input v-model.number="params.neck_angle_deg" type="number" step="0.1" min="0" max="10" />
      </div>
      <div class="form-row">
        <label>Body Thickness (mm)</label>
        <input v-model.number="params.body_thickness_mm" type="number" step="0.1" min="50" max="120" />
      </div>
      <div class="form-row">
        <label>Top Arch Height (mm)</label>
        <input v-model.number="params.top_arch_height_mm" type="number" step="0.1" min="10" max="30" />
      </div>
      <div class="form-row">
        <label>Fingerboard Extension (mm)</label>
        <input v-model.number="params.fingerboard_extension_mm" type="number" step="0.1" min="50" max="150" />
      </div>
      <button type="submit" class="calc-btn" :disabled="loading">
        {{ loading ? "Calculating..." : "Calculate Fit" }}
      </button>
    </form>

    <div v-if="error" class="error-box">
      {{ error }}
    </div>

    <div v-if="result" class="results-section">
      <h3 class="results-title">Fit Parameters</h3>
      <div class="results-grid">
        <div class="result-card">
          <span class="result-label">Bridge Height</span>
          <span class="result-value">{{ result.fit_parameters.bridge_height_mm.toFixed(2) }} mm</span>
          <span class="result-range">
            Range: {{ result.fit_parameters.bridge_height_range_mm[0].toFixed(1) }} -
            {{ result.fit_parameters.bridge_height_range_mm[1].toFixed(1) }} mm
          </span>
        </div>
        <div class="result-card">
          <span class="result-label">Saddle Line from Nut</span>
          <span class="result-value">{{ result.fit_parameters.saddle_line_from_nut_mm.toFixed(2) }} mm</span>
        </div>
        <div class="result-card">
          <span class="result-label">Fingerboard Clearance</span>
          <span class="result-value">{{ result.fit_parameters.fingerboard_clearance_mm.toFixed(2) }} mm</span>
        </div>
        <div class="result-card">
          <span class="result-label">Neck Angle</span>
          <span class="result-value">{{ result.fit_parameters.neck_angle_deg.toFixed(1) }} deg</span>
        </div>
      </div>

      <h3 class="results-title">String Compensations</h3>
      <div class="compensations-grid">
        <div v-for="(comp, idx) in result.fit_parameters.string_compensations_mm" :key="idx" class="comp-item">
          <span class="comp-string">String {{ idx + 1 }}</span>
          <span class="comp-value">{{ comp.toFixed(2) }} mm</span>
        </div>
      </div>

      <div v-if="result.notes && result.notes.length > 0" class="notes-section">
        <h3 class="results-title">Notes</h3>
        <ul class="notes-list">
          <li v-for="(note, idx) in result.notes" :key="idx">{{ note }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";

interface ArchtopParams {
  scale_length_mm: number;
  neck_angle_deg: number;
  body_thickness_mm: number;
  top_arch_height_mm: number;
  fingerboard_extension_mm: number;
}

interface FitParameters {
  bridge_height_mm: number;
  bridge_height_range_mm: [number, number];
  saddle_line_from_nut_mm: number;
  string_compensations_mm: number[];
  fingerboard_clearance_mm: number;
  neck_angle_deg: number;
}

interface ArchtopResult {
  ok: boolean;
  input: ArchtopParams;
  fit_parameters: FitParameters;
  notes: string[];
}

const params = reactive<ArchtopParams>({
  scale_length_mm: 628,
  neck_angle_deg: 4,
  body_thickness_mm: 85,
  top_arch_height_mm: 18,
  fingerboard_extension_mm: 100,
});

const loading = ref(false);
const error = ref<string | null>(null);
const result = ref<ArchtopResult | null>(null);

async function calculate() {
  loading.value = true;
  error.value = null;
  result.value = null;

  try {
    const response = await fetch("/api/cam/guitar/archtop/fit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error("HTTP " + response.status + ": " + response.statusText);
    }

    const data = await response.json();
    if (!data.ok) {
      throw new Error(data.error || "Calculation failed");
    }

    result.value = data;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unknown error";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.archtop-calculator {
  padding: 1.5rem;
  background: #1a1a1a;
  color: #e8eaed;
  min-height: 100%;
}

.calc-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.calc-subtitle {
  font-size: 0.875rem;
  color: #9aa0a6;
  margin-bottom: 1.5rem;
}

.calc-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 400px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-row label {
  font-size: 0.875rem;
  color: #9aa0a6;
}

.form-row input {
  padding: 0.5rem 0.75rem;
  background: #2d2d2d;
  border: 1px solid #404040;
  border-radius: 4px;
  color: #e8eaed;
  font-size: 1rem;
}

.form-row input:focus {
  outline: none;
  border-color: #8ab4f8;
}

.calc-btn {
  margin-top: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #8ab4f8;
  color: #1a1a1a;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.calc-btn:hover:not(:disabled) {
  background: #aecbfa;
}

.calc-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-box {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #5c2626;
  border: 1px solid #dc3545;
  border-radius: 4px;
  color: #f8d7da;
}

.results-section {
  margin-top: 2rem;
}

.results-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #8ab4f8;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.result-card {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  background: #2d2d2d;
  border-radius: 8px;
  border: 1px solid #404040;
}

.result-label {
  font-size: 0.75rem;
  color: #9aa0a6;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.result-value {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0.25rem 0;
}

.result-range {
  font-size: 0.75rem;
  color: #81c995;
}

.compensations-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.comp-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: #2d2d2d;
  border-radius: 4px;
  border: 1px solid #404040;
}

.comp-string {
  font-size: 0.75rem;
  color: #9aa0a6;
}

.comp-value {
  font-size: 0.875rem;
  font-weight: 600;
}

.notes-section {
  margin-top: 1rem;
}

.notes-list {
  list-style: disc;
  padding-left: 1.5rem;
  color: #9aa0a6;
  font-size: 0.875rem;
}

.notes-list li {
  margin-bottom: 0.25rem;
}
</style>
