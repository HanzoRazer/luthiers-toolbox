<script setup lang="ts">
/**
 * EstimatorInputsPanel - Form inputs for Engineering Estimator
 * Extracted from EngineeringEstimatorView.vue
 */
import type { EstimateRequest } from "@/types/businessEstimator";
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
  modelValue: EstimateRequest;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: EstimateRequest];
}>();

function updateField<K extends keyof EstimateRequest>(key: K, value: EstimateRequest[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}
</script>

<template>
  <aside class="inputs-panel">
    <!-- Instrument Type -->
    <section class="input-section">
      <h3>Instrument</h3>
      <select :value="modelValue.instrument_type" @change="updateField('instrument_type', ($event.target as HTMLSelectElement).value as any)">
        <option v-for="opt in instrumentTypes" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Experience -->
    <section class="input-section">
      <h3>Builder Experience</h3>
      <select :value="modelValue.builder_experience" @change="updateField('builder_experience', ($event.target as HTMLSelectElement).value as any)">
        <option v-for="opt in experienceLevels" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Body Complexity -->
    <section class="input-section">
      <h3>Body Complexity</h3>
      <select :value="modelValue.body_complexity" @change="updateField('body_complexity', ($event.target as HTMLSelectElement).value as any)">
        <option v-for="opt in bodyOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Binding -->
    <section class="input-section">
      <h3>Binding</h3>
      <select :value="modelValue.binding_body_complexity" @change="updateField('binding_body_complexity', ($event.target as HTMLSelectElement).value as any)">
        <option v-for="opt in bindingOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Neck -->
    <section class="input-section">
      <h3>Neck</h3>
      <select :value="modelValue.neck_complexity" @change="updateField('neck_complexity', ($event.target as HTMLSelectElement).value as any)">
        <option v-for="opt in neckOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Inlay -->
    <section class="input-section">
      <h3>Fretboard Inlay</h3>
      <select :value="modelValue.fretboard_inlay" @change="updateField('fretboard_inlay', ($event.target as HTMLSelectElement).value as any)">
        <option v-for="opt in inlayOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Finish -->
    <section class="input-section">
      <h3>Finish Type</h3>
      <select :value="modelValue.finish_type" @change="updateField('finish_type', ($event.target as HTMLSelectElement).value as any)">
        <option v-for="opt in finishOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Rosette -->
    <section class="input-section">
      <h3>Rosette</h3>
      <select :value="modelValue.rosette_complexity" @change="updateField('rosette_complexity', ($event.target as HTMLSelectElement).value as any)">
        <option v-for="opt in rosetteOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </section>

    <!-- Production -->
    <section class="input-section">
      <h3>Production</h3>
      <label class="input-row">
        <span>Batch Size</span>
        <input
          type="number"
          :value="modelValue.batch_size"
          @input="updateField('batch_size', parseInt(($event.target as HTMLInputElement).value) || 1)"
          min="1"
          max="100"
        />
      </label>
      <label class="input-row">
        <span>Labor Rate ($/hr)</span>
        <input
          type="number"
          :value="modelValue.hourly_rate"
          @input="updateField('hourly_rate', parseFloat(($event.target as HTMLInputElement).value) || 0)"
          min="0"
          step="5"
        />
      </label>
    </section>
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
.input-section input {
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

.input-row input {
  width: 80px;
  text-align: right;
}
</style>
