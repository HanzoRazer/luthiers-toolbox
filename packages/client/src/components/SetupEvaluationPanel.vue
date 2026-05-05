<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">Setup Evaluation</h4>

    <!-- Input Form -->
    <div :class="styles.formGrid">
      <div :class="shared.inputRow">
        <label>Neck Angle</label>
        <input
          v-model.number="store.setupRequest.neck_angle_deg"
          type="number"
          step="0.1"
          min="0"
          max="5"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">deg</span>
      </div>

      <div :class="shared.inputRow">
        <label>Relief (7th fret)</label>
        <input
          v-model.number="store.setupRequest.truss_rod_relief_mm"
          type="number"
          step="0.05"
          min="0"
          max="1"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">mm</span>
      </div>

      <div :class="shared.inputRow">
        <label>Action at Nut</label>
        <input
          v-model.number="store.setupRequest.action_at_nut_mm"
          type="number"
          step="0.1"
          min="0.2"
          max="1.5"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">mm</span>
      </div>

      <div :class="shared.inputRow">
        <label>12th Treble</label>
        <input
          v-model.number="store.setupRequest.action_at_12th_treble_mm"
          type="number"
          step="0.1"
          min="1.0"
          max="4.0"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">mm</span>
      </div>

      <div :class="shared.inputRow">
        <label>12th Bass</label>
        <input
          v-model.number="store.setupRequest.action_at_12th_bass_mm"
          type="number"
          step="0.1"
          min="1.5"
          max="4.5"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">mm</span>
      </div>

      <div :class="shared.inputRow">
        <label>Saddle Height</label>
        <input
          v-model.number="store.setupRequest.saddle_height_mm"
          type="number"
          step="0.5"
          min="1"
          max="10"
          :class="shared.inputNumber"
        >
        <span :class="shared.unit">mm</span>
      </div>
    </div>

    <button
      :disabled="store.setupLoading"
      :class="shared.btnSecondary"
      @click="store.evaluateSetup"
    >
      <span v-if="store.setupLoading">Evaluating...</span>
      <span v-else>Evaluate Setup</span>
    </button>

    <!-- Error -->
    <div
      v-if="store.setupError"
      :class="shared.bannerError"
    >
      {{ store.setupError }}
    </div>

    <!-- Results -->
    <div
      v-if="store.setupEvaluation"
      :class="styles.results"
    >
      <div :class="styles.gateHeader">
        <span
          :class="[styles.gateBadge, gateClass]"
        >{{ store.setupEvaluation.overall_gate }}</span>
        <span :class="styles.summary">{{ store.setupEvaluation.summary }}</span>
      </div>

      <!-- Issues -->
      <div
        v-if="store.setupEvaluation.issues.length > 0"
        :class="styles.issuesList"
      >
        <div
          v-for="issue in store.setupEvaluation.issues"
          :key="issue.parameter"
          :class="[styles.issueRow, issueGateClass(issue.gate)]"
        >
          <span :class="styles.issueParam">{{ issue.parameter }}</span>
          <span :class="styles.issueValue">{{ issue.current_value.toFixed(2) }}</span>
          <span :class="styles.issueRange">
            ({{ issue.recommended_range[0].toFixed(2) }} - {{ issue.recommended_range[1].toFixed(2) }})
          </span>
          <span :class="styles.issueFix">{{ issue.fix }}</span>
        </div>
      </div>

      <!-- Suggestions -->
      <div
        v-if="store.setupEvaluation.suggestions.length > 0"
        :class="styles.suggestions"
      >
        <strong>Suggestions:</strong>
        <ul>
          <li
            v-for="(sug, idx) in store.setupEvaluation.suggestions"
            :key="idx"
          >
            {{ sug }}
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
import styles from "./SetupEvaluationPanel.module.css";

const store = useInstrumentGeometryStore();

const gateClass = computed(() => {
  switch (store.setupEvaluation?.overall_gate) {
    case "GREEN": return styles.gateGreen;
    case "YELLOW": return styles.gateYellow;
    case "RED": return styles.gateRed;
    default: return "";
  }
});

function issueGateClass(gate: string) {
  switch (gate) {
    case "GREEN": return styles.issueGreen;
    case "YELLOW": return styles.issueYellow;
    case "RED": return styles.issueRed;
    default: return "";
  }
}
</script>
