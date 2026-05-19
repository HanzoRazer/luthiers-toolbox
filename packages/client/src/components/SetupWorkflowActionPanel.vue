<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">
      Action Height Workflow
      <span :class="styles.badge">NECK-A v2</span>
    </h4>

    <!-- Input Form -->
    <div :class="styles.formGrid">
      <div :class="styles.formRow">
        <h5 :class="styles.sectionLabel">Treble Side (High E)</h5>
        <div :class="shared.inputRow">
          <label>Action at 12th</label>
          <input
            v-model.number="store.trebleActionMeasurement"
            type="number"
            step="0.05"
            min="0.5"
            max="4"
            :class="shared.inputNumber"
          >
          <span :class="shared.unit">mm</span>
        </div>
        <div :class="styles.targetRow">
          <label>Target</label>
          <input
            v-model.number="store.trebleActionTargetMin"
            type="number"
            step="0.05"
            min="0.5"
            max="3"
            :class="styles.targetInput"
          >
          <span :class="styles.targetSeparator">–</span>
          <input
            v-model.number="store.trebleActionTargetMax"
            type="number"
            step="0.05"
            min="1"
            max="4"
            :class="styles.targetInput"
          >
          <span :class="shared.unit">mm</span>
        </div>
      </div>

      <div :class="styles.formRow">
        <h5 :class="styles.sectionLabel">Bass Side (Low E)</h5>
        <div :class="shared.inputRow">
          <label>Action at 12th</label>
          <input
            v-model.number="store.bassActionMeasurement"
            type="number"
            step="0.05"
            min="0.5"
            max="5"
            :class="shared.inputNumber"
          >
          <span :class="shared.unit">mm</span>
        </div>
        <div :class="styles.targetRow">
          <label>Target</label>
          <input
            v-model.number="store.bassActionTargetMin"
            type="number"
            step="0.05"
            min="1"
            max="4"
            :class="styles.targetInput"
          >
          <span :class="styles.targetSeparator">–</span>
          <input
            v-model.number="store.bassActionTargetMax"
            type="number"
            step="0.05"
            min="1.5"
            max="5"
            :class="styles.targetInput"
          >
          <span :class="shared.unit">mm</span>
        </div>
      </div>
    </div>

    <div :class="styles.helpText">
      Measure string height at 12th fret, from fret crown to bottom of string.
    </div>

    <button
      :disabled="store.actionWorkflowLoading"
      :class="shared.btnSecondary"
      @click="store.evaluateActionWorkflow"
    >
      <span v-if="store.actionWorkflowLoading">Evaluating...</span>
      <span v-else>Evaluate Action</span>
    </button>

    <!-- Error -->
    <div
      v-if="store.actionWorkflowError"
      :class="shared.bannerError"
    >
      {{ store.actionWorkflowError }}
    </div>

    <!-- Results -->
    <div
      v-if="store.actionWorkflowResult"
      :class="styles.results"
    >
      <!-- Overall Gate -->
      <div :class="styles.gateHeader">
        <span
          :class="[styles.gateBadge, overallGateClass]"
        >{{ store.actionWorkflowResult.overall_gate.toUpperCase() }}</span>
        <span :class="styles.summary">Overall action evaluation</span>
      </div>

      <!-- Individual Diagnostics (stacked) -->
      <div :class="styles.diagnosticsList">
        <div
          v-for="diag in store.actionWorkflowResult.diagnostics"
          :key="diag.id"
          :class="[styles.diagnosticCard, diagnosticGateClass(diag.gate)]"
        >
          <div :class="styles.diagHeader">
            <span :class="[styles.diagBadge, diagnosticGateClass(diag.gate)]">
              {{ diag.gate.toUpperCase() }}
            </span>
            <span :class="styles.diagPosition">
              {{ diag.id.includes('treble') ? 'Treble' : 'Bass' }}
            </span>
          </div>

          <div :class="styles.diagMessage">{{ diag.message }}</div>

          <div :class="styles.diagMeasurement">
            <span :class="styles.measurementValue">
              {{ diag.measurement?.toFixed(2) ?? '—' }} mm
            </span>
            <span :class="styles.measurementRange">
              (target: {{ diag.target_min?.toFixed(2) }}–{{ diag.target_max?.toFixed(2) }} mm)
            </span>
          </div>

          <!-- Probable Causes -->
          <div
            v-if="diag.probable_causes.length > 0"
            :class="styles.causesSection"
          >
            <strong>Probable Causes:</strong>
            <ul>
              <li
                v-for="(cause, idx) in diag.probable_causes"
                :key="idx"
              >
                {{ cause }}
              </li>
            </ul>
          </div>

          <!-- Recommended Actions -->
          <div
            v-if="diag.recommended_actions.length > 0"
            :class="styles.actionsSection"
          >
            <strong>Recommended Actions:</strong>
            <ul>
              <li
                v-for="(action, idx) in diag.recommended_actions"
                :key="idx"
              >
                {{ action }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useInstrumentGeometryStore, type DiagnosticGate } from "@/stores/instrumentGeometryStore";
import shared from "@/styles/dark-theme-shared.module.css";
import styles from "./SetupWorkflowActionPanel.module.css";

const store = useInstrumentGeometryStore();

const overallGateClass = computed(() => {
  switch (store.actionWorkflowResult?.overall_gate) {
    case "green": return styles.gateGreen;
    case "yellow": return styles.gateYellow;
    case "red": return styles.gateRed;
    default: return "";
  }
});

function diagnosticGateClass(gate: DiagnosticGate) {
  switch (gate) {
    case "green": return styles.gateGreen;
    case "yellow": return styles.gateYellow;
    case "red": return styles.gateRed;
    default: return "";
  }
}
</script>
