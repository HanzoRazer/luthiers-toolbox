<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">
      Neck Relief Workflow
      <span :class="styles.badge">NECK-A v1</span>
    </h4>

    <!-- Input Form -->
    <div :class="styles.formGrid">
      <div :class="shared.inputRow">
        <label>Measured Relief</label>
        <input
          v-model.number="store.reliefMeasurement"
          type="number"
          step="0.01"
          min="0"
          max="1"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">mm</span>
      </div>

      <div :class="shared.inputRow">
        <label>Target Min</label>
        <input
          v-model.number="store.reliefTargetMin"
          type="number"
          step="0.01"
          min="0"
          max="0.5"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">mm</span>
      </div>

      <div :class="shared.inputRow">
        <label>Target Max</label>
        <input
          v-model.number="store.reliefTargetMax"
          type="number"
          step="0.01"
          min="0.1"
          max="1"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">mm</span>
      </div>
    </div>

    <div :class="styles.helpText">
      Measure relief at 7th/8th fret with string pressed at 1st and last fret.
    </div>

    <button
      :disabled="store.reliefWorkflowLoading"
      :class="shared.btnSecondary"
      @click="store.evaluateRelief"
    >
      <span v-if="store.reliefWorkflowLoading">Evaluating...</span>
      <span v-else>Evaluate Relief</span>
    </button>

    <!-- Error -->
    <div
      v-if="store.reliefWorkflowError"
      :class="shared.bannerError"
    >
      {{ store.reliefWorkflowError }}
    </div>

    <!-- Results -->
    <div
      v-if="store.reliefWorkflowResult"
      :class="styles.results"
    >
      <div :class="styles.gateHeader">
        <span
          :class="[styles.gateBadge, gateClass]"
        >{{ store.reliefWorkflowResult.gate.toUpperCase() }}</span>
        <span :class="styles.summary">{{ store.reliefWorkflowResult.message }}</span>
      </div>

      <!-- Measurement Display -->
      <div :class="styles.measurementDisplay">
        <span :class="styles.measurementLabel">Measured:</span>
        <span :class="styles.measurementValue">
          {{ store.reliefWorkflowResult.measurement?.toFixed(2) ?? '—' }} mm
        </span>
        <span :class="styles.measurementRange">
          (target: {{ store.reliefWorkflowResult.target_min?.toFixed(2) }}–{{ store.reliefWorkflowResult.target_max?.toFixed(2) }} mm)
        </span>
      </div>

      <!-- Probable Causes -->
      <div
        v-if="store.reliefWorkflowResult.probable_causes.length > 0"
        :class="styles.causesSection"
      >
        <strong>Probable Causes:</strong>
        <ul>
          <li
            v-for="(cause, idx) in store.reliefWorkflowResult.probable_causes"
            :key="idx"
          >
            {{ cause }}
          </li>
        </ul>
      </div>

      <!-- Recommended Actions -->
      <div
        v-if="store.reliefWorkflowResult.recommended_actions.length > 0"
        :class="styles.actionsSection"
      >
        <strong>Recommended Actions:</strong>
        <ul>
          <li
            v-for="(action, idx) in store.reliefWorkflowResult.recommended_actions"
            :key="idx"
          >
            {{ action }}
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useInstrumentGeometryStore } from "@/stores/instrumentGeometryStore";
import shared from "@/styles/dark-theme-shared.module.css";
import styles from "./SetupWorkflowReliefPanel.module.css";

const store = useInstrumentGeometryStore();

const gateClass = computed(() => {
  switch (store.reliefWorkflowResult?.gate) {
    case "green": return styles.gateGreen;
    case "yellow": return styles.gateYellow;
    case "red": return styles.gateRed;
    default: return "";
  }
});
</script>
