<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">
      Nut Slot Clearance Workflow
      <span :class="styles.badge">NECK-A v2</span>
    </h4>

    <!-- String Clearance Inputs -->
    <div :class="styles.formGrid">
      <div :class="styles.stringGrid">
        <div
          v-for="(label, idx) in stringLabels"
          :key="idx"
          :class="styles.stringInput"
        >
          <span :class="styles.stringLabel">{{ label }}</span>
          <input
            v-model.number="store.nutClearancesMm[idx]"
            type="number"
            step="0.01"
            min="0"
            max="1"
            :class="styles.clearanceInput"
          >
        </div>
      </div>
      <div :class="shared.unit" style="text-align: center; margin-top: -8px;">
        mm (first-fret clearance)
      </div>

      <!-- Target Ranges -->
      <div :class="styles.targetSection">
        <h5 :class="styles.sectionLabel">Target Ranges</h5>
        <div :class="styles.targetRow">
          <label>Treble (1-3)</label>
          <input
            v-model.number="store.nutTrebleTargetMin"
            type="number"
            step="0.01"
            min="0.10"
            max="0.50"
            :class="styles.targetInput"
          >
          <span :class="styles.targetSeparator">–</span>
          <input
            v-model.number="store.nutTrebleTargetMax"
            type="number"
            step="0.01"
            min="0.15"
            max="0.60"
            :class="styles.targetInput"
          >
          <span :class="shared.unit">mm</span>
        </div>
        <div :class="styles.targetRow">
          <label>Bass (4-6)</label>
          <input
            v-model.number="store.nutBassTargetMin"
            type="number"
            step="0.01"
            min="0.15"
            max="0.60"
            :class="styles.targetInput"
          >
          <span :class="styles.targetSeparator">–</span>
          <input
            v-model.number="store.nutBassTargetMax"
            type="number"
            step="0.01"
            min="0.20"
            max="0.80"
            :class="styles.targetInput"
          >
          <span :class="shared.unit">mm</span>
        </div>
      </div>
    </div>

    <div :class="styles.helpText">
      Fret string at 3rd fret, measure gap between string and 1st fret crown.
    </div>

    <button
      :disabled="store.nutWorkflowLoading"
      :class="shared.btnSecondary"
      @click="store.evaluateNutWorkflow"
    >
      <span v-if="store.nutWorkflowLoading">Evaluating...</span>
      <span v-else>Evaluate Nut Slots</span>
    </button>

    <!-- Error -->
    <div
      v-if="store.nutWorkflowError"
      :class="shared.bannerError"
    >
      {{ store.nutWorkflowError }}
    </div>

    <!-- Results -->
    <div
      v-if="store.nutWorkflowResult"
      :class="styles.results"
    >
      <!-- Overall Gate -->
      <div :class="styles.gateHeader">
        <span
          :class="[styles.gateBadge, overallGateClass]"
        >{{ store.nutWorkflowResult.overall_gate.toUpperCase() }}</span>
        <span :class="styles.summary">Overall nut slot evaluation</span>
      </div>

      <!-- Individual String Diagnostics (grid) -->
      <div :class="styles.diagnosticsList">
        <div
          v-for="(diag, idx) in store.nutWorkflowResult.diagnostics"
          :key="diag.id"
          :class="[styles.diagnosticCard, diagnosticGateClass(diag.gate)]"
        >
          <div :class="styles.diagHeader">
            <span :class="[styles.diagBadge, diagnosticGateClass(diag.gate)]">
              {{ diag.gate.toUpperCase() }}
            </span>
            <span :class="styles.diagPosition">
              {{ stringLabels[idx] }}
            </span>
          </div>

          <div :class="styles.diagMessage">{{ diag.message }}</div>

          <div :class="styles.diagMeasurement">
            <span :class="styles.measurementValue">
              {{ diag.measurement?.toFixed(2) ?? '—' }} mm
            </span>
            <span :class="styles.measurementRange">
              target: {{ diag.target_min?.toFixed(2) }}–{{ diag.target_max?.toFixed(2) }} mm
            </span>
          </div>

          <!-- Probable Causes -->
          <div
            v-if="diag.probable_causes.length > 0"
            :class="styles.causesSection"
          >
            <strong>Causes:</strong>
            <ul>
              <li
                v-for="(cause, cidx) in diag.probable_causes"
                :key="cidx"
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
            <strong>Actions:</strong>
            <ul>
              <li
                v-for="(action, aidx) in diag.recommended_actions"
                :key="aidx"
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
import styles from "./SetupWorkflowNutPanel.module.css";

const store = useInstrumentGeometryStore();

const stringLabels = ["1 (E)", "2 (B)", "3 (G)", "4 (D)", "5 (A)", "6 (E)"];

const overallGateClass = computed(() => {
  switch (store.nutWorkflowResult?.overall_gate) {
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
