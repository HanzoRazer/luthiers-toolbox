<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">
      Expert Setup Diagnostics
      <span :class="styles.badge">NECK-A v2</span>
    </h4>

    <!-- Prerequisite Notice -->
    <div
      v-if="!store.canEvaluateCombined()"
      :class="styles.prerequisiteNotice"
    >
      Evaluate Relief, Action, and Nut workflows first.
    </div>

    <!-- Symptom Selection -->
    <div :class="styles.symptomSection">
      <div :class="styles.symptomLabel">Reported Symptoms</div>
      <div :class="styles.symptomGrid">
        <label
          v-for="symptom in symptomOptions"
          :key="symptom.value"
          :class="[styles.symptomCheckbox, isSelected(symptom.value) && styles.selected]"
        >
          <input
            type="checkbox"
            :checked="isSelected(symptom.value)"
            @change="store.toggleExpertSymptom(symptom.value)"
          >
          <span>{{ symptom.label }}</span>
        </label>
      </div>
    </div>

    <button
      :disabled="store.expertDiagnosticsLoading || !store.canEvaluateCombined() || store.expertSymptoms.length === 0"
      :class="shared.btnSecondary"
      @click="store.evaluateExpertDiagnostics"
    >
      <span v-if="store.expertDiagnosticsLoading">Analyzing...</span>
      <span v-else>Evaluate Expert Diagnostics</span>
    </button>

    <!-- Error -->
    <div
      v-if="store.expertDiagnosticsError"
      :class="shared.bannerError"
    >
      {{ store.expertDiagnosticsError }}
    </div>

    <!-- Results -->
    <div
      v-if="store.expertDiagnosticsResult"
      :class="styles.results"
    >
      <!-- Overall Gate -->
      <div :class="styles.gateHeader">
        <span
          :class="[styles.gateBadge, overallGateClass]"
        >{{ store.expertDiagnosticsResult.overall_gate.toUpperCase() }}</span>
        <span :class="styles.summary">Expert diagnosis based on symptoms</span>
      </div>

      <!-- Diagnostics List -->
      <div :class="styles.diagnosticsList">
        <div
          v-for="diag in store.expertDiagnosticsResult.diagnostics"
          :key="diag.id"
          :class="[styles.diagnosticCard, diagnosticGateClass(diag.gate)]"
        >
          <div :class="styles.diagHeader">
            <span :class="[styles.diagBadge, diagnosticGateClass(diag.gate)]">
              {{ diag.gate.toUpperCase() }}
            </span>
            <span :class="styles.diagSymptom">
              {{ formatSymptom(diag.symptom) }}
            </span>
            <span :class="styles.diagConfidence">
              {{ (diag.confidence * 100).toFixed(0) }}% confidence
            </span>
          </div>

          <div :class="styles.diagMessage">{{ diag.message }}</div>

          <!-- Probable Causes -->
          <div
            v-if="diag.probable_causes.length > 0"
            :class="styles.diagSection"
          >
            <div :class="styles.diagSectionLabel">Probable Causes</div>
            <ul :class="[styles.diagList, styles.causesList]">
              <li
                v-for="(cause, idx) in diag.probable_causes"
                :key="idx"
              >
                {{ cause }}
              </li>
            </ul>
          </div>

          <!-- Recommended Checks -->
          <div
            v-if="diag.recommended_checks.length > 0"
            :class="styles.diagSection"
          >
            <div :class="styles.diagSectionLabel">Recommended Checks</div>
            <ul :class="[styles.diagList, styles.checksList]">
              <li
                v-for="(check, idx) in diag.recommended_checks"
                :key="idx"
              >
                {{ check }}
              </li>
            </ul>
          </div>

          <!-- Recommended Actions -->
          <div
            v-if="diag.recommended_actions.length > 0"
            :class="styles.diagSection"
          >
            <div :class="styles.diagSectionLabel">Recommended Actions</div>
            <ul :class="[styles.diagList, styles.actionsList]">
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
import { useInstrumentGeometryStore, type DiagnosticGate, type PlayerSymptom } from "@/stores/instrumentGeometryStore";
import shared from "@/styles/dark-theme-shared.module.css";
import styles from "./SetupWorkflowExpertPanel.module.css";

const store = useInstrumentGeometryStore();

const symptomOptions: { value: PlayerSymptom; label: string }[] = [
  { value: "buzz_open_strings", label: "Open strings buzz" },
  { value: "buzz_low_frets", label: "Buzz on low frets" },
  { value: "buzz_middle_frets", label: "Buzz on middle frets" },
  { value: "buzz_upper_frets", label: "Buzz on upper frets" },
  { value: "fretted_notes_buzz", label: "Fretted notes buzz" },
  { value: "first_position_hard", label: "First position hard to play" },
  { value: "first_position_sharp", label: "First position plays sharp" },
  { value: "feels_stiff", label: "Feels stiff" },
  { value: "feels_slinky", label: "Feels slinky/loose" },
];

function isSelected(symptom: PlayerSymptom): boolean {
  return store.expertSymptoms.includes(symptom);
}

function formatSymptom(symptom: string): string {
  return symptom.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const overallGateClass = computed(() => {
  switch (store.expertDiagnosticsResult?.overall_gate) {
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
