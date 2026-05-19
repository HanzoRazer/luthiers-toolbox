<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">
      Combined Setup Diagnostics
      <span :class="[styles.badge, styles.badgeExpert]">NECK-A v2</span>
    </h4>

    <!-- Prerequisite Notice -->
    <div
      v-if="!store.canEvaluateCombined()"
      :class="styles.prerequisiteNotice"
    >
      <p :class="styles.prerequisiteText">
        Evaluate all three workflow steps before running combined diagnostics:
      </p>
      <ul :class="styles.prerequisiteList">
        <li :class="store.reliefWorkflowResult ? styles.completed : styles.pending">
          Relief Workflow {{ store.reliefWorkflowResult ? '(done)' : '(pending)' }}
        </li>
        <li :class="store.actionWorkflowResult ? styles.completed : styles.pending">
          Action Workflow {{ store.actionWorkflowResult ? '(done)' : '(pending)' }}
        </li>
        <li :class="store.nutWorkflowResult ? styles.completed : styles.pending">
          Nut Slot Workflow {{ store.nutWorkflowResult ? '(done)' : '(pending)' }}
        </li>
      </ul>
    </div>

    <button
      :disabled="store.combinedDiagnosticsLoading || !store.canEvaluateCombined()"
      :class="shared.btnSecondary"
      @click="store.evaluateCombinedSetup"
    >
      <span v-if="store.combinedDiagnosticsLoading">Analyzing...</span>
      <span v-else>Evaluate Combined Setup</span>
    </button>

    <!-- Error -->
    <div
      v-if="store.combinedDiagnosticsError"
      :class="shared.bannerError"
    >
      {{ store.combinedDiagnosticsError }}
    </div>

    <!-- Results -->
    <div
      v-if="store.combinedDiagnosticsResult"
      :class="styles.results"
    >
      <!-- Overall Gate -->
      <div :class="styles.gateHeader">
        <span
          :class="[styles.gateBadge, overallGateClass]"
        >{{ store.combinedDiagnosticsResult.overall_gate.toUpperCase() }}</span>
        <span :class="styles.summary">Combined setup analysis</span>
      </div>

      <!-- Diagnostics List -->
      <div
        v-if="store.combinedDiagnosticsResult.diagnostics.length > 0"
        :class="styles.diagnosticsList"
      >
        <div
          v-for="diag in store.combinedDiagnosticsResult.diagnostics"
          :key="diag.id"
          :class="[styles.diagnosticCard, diagnosticGateClass(diag.gate)]"
        >
          <div :class="styles.diagHeader">
            <span :class="[styles.diagBadge, diagnosticGateClass(diag.gate)]">
              {{ diag.gate.toUpperCase() }}
            </span>
            <span :class="styles.diagId">{{ diag.id }}</span>
          </div>

          <div :class="styles.diagMessage">{{ diag.message }}</div>

          <!-- Contributing Factors -->
          <div
            v-if="diag.contributing_factors.length > 0"
            :class="styles.factorsSection"
          >
            <div :class="styles.factorsLabel">Contributing Factors</div>
            <div :class="styles.factorsList">
              <span
                v-for="(factor, idx) in diag.contributing_factors"
                :key="idx"
                :class="styles.factorTag"
              >
                {{ factor }}
              </span>
            </div>
          </div>

          <!-- Recommendation -->
          <div
            v-if="diag.recommendation"
            :class="styles.recommendationSection"
          >
            <div :class="styles.recommendationLabel">Recommendation</div>
            <div :class="styles.recommendationText">{{ diag.recommendation }}</div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else
        :class="styles.emptyState"
      >
        No cross-step issues detected. Individual workflow diagnostics may still apply.
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useInstrumentGeometryStore, type DiagnosticGate } from "@/stores/instrumentGeometryStore";
import shared from "@/styles/dark-theme-shared.module.css";
import styles from "./SetupWorkflowCombinedPanel.module.css";

const store = useInstrumentGeometryStore();

const overallGateClass = computed(() => {
  switch (store.combinedDiagnosticsResult?.overall_gate) {
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
