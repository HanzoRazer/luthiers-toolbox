<script setup lang="ts">
/**
 * EstimatorInputsPanel - Form inputs for Engineering Estimator
 *
 * Phase 2 features:
 * - Chip multi-select for body complexity
 * - Progressive disclosure for advanced options
 * - Persistent draft state via useEstimatorDraft
 */
import { ref, computed, watch, onMounted } from "vue";
import type { EstimateRequest, BodyComplexity } from "@/types/businessEstimator";
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

// ============================================================================
// PROPS & EMITS
// ============================================================================

const props = defineProps<{
  modelValue: EstimateRequest;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: EstimateRequest];
}>();

// ============================================================================
// STATE
// ============================================================================

const ADVANCED_TOGGLE_KEY = "ltb:estimator:showAdvanced:v1";
const showAdvanced = ref(false);

// Load advanced toggle state from localStorage
onMounted(() => {
  try {
    showAdvanced.value = localStorage.getItem(ADVANCED_TOGGLE_KEY) === "true";
  } catch {
    // Ignore
  }
});

// Persist advanced toggle state
watch(showAdvanced, (val) => {
  try {
    localStorage.setItem(ADVANCED_TOGGLE_KEY, String(val));
  } catch {
    // Ignore
  }
});

// ============================================================================
// COMPUTED
// ============================================================================

const bodyComplexityArray = computed<BodyComplexity[]>(() => {
  const bc = props.modelValue.body_complexity;
  if (Array.isArray(bc)) return bc;
  return bc ? [bc] : ["standard"];
});

// ============================================================================
// ACTIONS
// ============================================================================

function updateField<K extends keyof EstimateRequest>(key: K, value: EstimateRequest[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

function toggleBodyComplexity(value: BodyComplexity) {
  const current = bodyComplexityArray.value;
  const idx = current.indexOf(value);

  let newValue: BodyComplexity[];
  if (idx >= 0) {
    // Remove if already selected (but keep at least one)
    if (current.length > 1) {
      newValue = current.filter((v) => v !== value);
    } else {
      return; // Can't remove the last one
    }
  } else {
    // Add to selection
    newValue = [...current, value];
  }

  updateField("body_complexity", newValue);
}

function isBodySelected(value: BodyComplexity): boolean {
  return bodyComplexityArray.value.includes(value);
}
</script>

<template>
  <aside class="inputs-panel">
    <!-- Instrument Type -->
    <section class="input-section">
      <h3>Instrument</h3>
      <select
        :value="modelValue.instrument_type"
        @change="updateField('instrument_type', ($event.target as HTMLSelectElement).value as any)"
      >
        <option
          v-for="opt in instrumentTypes"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Experience -->
    <section class="input-section">
      <h3>Builder Experience</h3>
      <select
        :value="modelValue.builder_experience"
        @change="updateField('builder_experience', ($event.target as HTMLSelectElement).value as any)"
      >
        <option
          v-for="opt in experienceLevels"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Body Complexity - CHIP MULTI-SELECT -->
    <section class="input-section">
      <h3>Body Complexity</h3>
      <p class="hint">
        Select all that apply
      </p>
      <div class="chip-group">
        <button
          v-for="opt in bodyOptions"
          :key="opt.value"
          type="button"
          class="chip"
          :class="{ 'chip--active': isBodySelected(opt.value) }"
          @click="toggleBodyComplexity(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </section>

    <!-- Binding -->
    <section class="input-section">
      <h3>Binding</h3>
      <select
        :value="modelValue.binding_body_complexity"
        @change="updateField('binding_body_complexity', ($event.target as HTMLSelectElement).value as any)"
      >
        <option
          v-for="opt in bindingOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Neck -->
    <section class="input-section">
      <h3>Neck</h3>
      <select
        :value="modelValue.neck_complexity"
        @change="updateField('neck_complexity', ($event.target as HTMLSelectElement).value as any)"
      >
        <option
          v-for="opt in neckOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Inlay -->
    <section class="input-section">
      <h3>Fretboard Inlay</h3>
      <select
        :value="modelValue.fretboard_inlay"
        @change="updateField('fretboard_inlay', ($event.target as HTMLSelectElement).value as any)"
      >
        <option
          v-for="opt in inlayOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Finish -->
    <section class="input-section">
      <h3>Finish Type</h3>
      <select
        :value="modelValue.finish_type"
        @change="updateField('finish_type', ($event.target as HTMLSelectElement).value as any)"
      >
        <option
          v-for="opt in finishOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Rosette -->
    <section class="input-section">
      <h3>Rosette</h3>
      <select
        :value="modelValue.rosette_complexity"
        @change="updateField('rosette_complexity', ($event.target as HTMLSelectElement).value as any)"
      >
        <option
          v-for="opt in rosetteOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- ADVANCED OPTIONS - Progressive Disclosure -->
    <section class="input-section advanced-toggle">
      <button
        type="button"
        class="toggle-btn"
        @click="showAdvanced = !showAdvanced"
      >
        <span class="toggle-icon">{{ showAdvanced ? '▾' : '▸' }}</span>
        Advanced Options
      </button>
    </section>

    <template v-if="showAdvanced">
      <!-- Production -->
      <section class="input-section advanced">
        <h3>Production</h3>
        <label class="input-row">
          <span>Batch Size</span>
          <input
            type="number"
            :value="modelValue.batch_size"
            min="1"
            max="100"
            @input="updateField('batch_size', parseInt(($event.target as HTMLInputElement).value) || 1)"
          >
        </label>
        <label class="input-row">
          <span>Labor Rate ($/hr)</span>
          <input
            type="number"
            :value="modelValue.hourly_rate"
            min="0"
            step="5"
            @input="updateField('hourly_rate', parseFloat(($event.target as HTMLInputElement).value) || 0)"
          >
        </label>
        <label class="input-row checkbox-row">
          <input
            type="checkbox"
            :checked="modelValue.include_materials"
            @change="updateField('include_materials', ($event.target as HTMLInputElement).checked)"
          >
          <span>Include Material Costs</span>
        </label>
      </section>
    </template>
  </aside>
</template>

<style scoped>
.inputs-panel {
  flex: 0 0 280px;
  border-right: 1px solid #1e2438;
  padding-right: 16px;
}

.input-section {
  margin-bottom: 16px;
}

.input-section h3 {
  font-size: 9px;
  letter-spacing: 3px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #1e2438;
}

.input-section select,
.input-section input[type="number"] {
  width: 100%;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #e0e8ff;
  padding: 8px 10px;
  font-size: 12px;
  font-family: inherit;
  border-radius: 3px;
}

.input-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.input-row span {
  font-size: 11px;
  color: #8890a8;
}

.input-row input[type="number"] {
  width: 80px;
  text-align: right;
}

/* Hint text */
.hint {
  font-size: 10px;
  color: #506090;
  margin: 0 0 8px;
  font-style: italic;
}

/* Chip multi-select */
.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  padding: 6px 10px;
  font-size: 11px;
  font-family: inherit;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #8890a8;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip:hover {
  border-color: #4060c0;
  color: #c0c8e0;
}

.chip--active {
  background: #1a2a50;
  border-color: #4080f0;
  color: #80c0ff;
}

.chip--active:hover {
  background: #203060;
}

/* Advanced toggle */
.advanced-toggle {
  margin-top: 24px;
  border-top: 1px solid #1e2438;
  padding-top: 16px;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 0;
  background: none;
  border: none;
  color: #6080b0;
  font-size: 11px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
  transition: color 0.15s;
}

.toggle-btn:hover {
  color: #80a0d0;
}

.toggle-icon {
  font-size: 10px;
  width: 12px;
}

/* Advanced section styling */
.input-section.advanced {
  padding-left: 12px;
  border-left: 2px solid #1e2438;
}

/* Checkbox row */
.checkbox-row {
  justify-content: flex-start;
  gap: 8px;
}

.checkbox-row input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: #4080f0;
}
</style>
