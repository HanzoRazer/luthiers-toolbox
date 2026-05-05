<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">Saddle Compensation</h4>

    <!-- Mode Selector -->
    <div :class="styles.modeSelector">
      <button
        :class="[styles.modeBtn, store.saddleCompensationMode === 'design' && styles.modeBtnActive]"
        @click="store.saddleCompensationMode = 'design'"
      >
        Design Mode
      </button>
      <button
        :class="[styles.modeBtn, store.saddleCompensationMode === 'setup' && styles.modeBtnActive]"
        @click="store.saddleCompensationMode = 'setup'"
      >
        Setup Mode
      </button>
    </div>

    <!-- Design Mode -->
    <div
      v-if="store.saddleCompensationMode === 'design'"
      :class="styles.modeContent"
    >
      <p :class="styles.modeDesc">
        Estimate compensation from string specs and action height.
      </p>

      <button
        :disabled="store.saddleLoading"
        :class="shared.btnSecondary"
        @click="store.calculateSaddleCompensationDesign"
      >
        <span v-if="store.saddleLoading">Calculating...</span>
        <span v-else>Calculate Design Compensation</span>
      </button>

      <!-- Design Results -->
      <div
        v-if="store.saddleDesignResult"
        :class="styles.results"
      >
        <div :class="styles.compensationGrid">
          <div
            v-for="str in store.saddleDesignResult.string_results"
            :key="str.name"
            :class="styles.compRow"
          >
            <span :class="styles.compString">{{ str.name }}</span>
            <span :class="styles.compValue">+{{ str.compensation_mm.toFixed(2) }} mm</span>
          </div>
        </div>

        <div :class="styles.fitInfo">
          <span>Fit angle: {{ store.saddleDesignResult.saddle_fit.slant_angle_deg.toFixed(1) }}°</span>
          <span>R²: {{ store.saddleDesignResult.saddle_fit.r_squared.toFixed(3) }}</span>
        </div>

        <div :class="styles.recommendation">
          {{ store.saddleDesignResult.recommendation }}
        </div>
      </div>
    </div>

    <!-- Setup Mode -->
    <div
      v-if="store.saddleCompensationMode === 'setup'"
      :class="styles.modeContent"
    >
      <p :class="styles.modeDesc">
        Enter measured cents errors to calculate saddle adjustments.
      </p>

      <div :class="styles.measurementForm">
        <div
          v-for="(_, idx) in setupMeasurements"
          :key="idx"
          :class="styles.measurementRow"
        >
          <span :class="styles.measurementLabel">String {{ idx + 1 }}</span>
          <input
            v-model.number="setupMeasurements[idx].current_compensation_mm"
            type="number"
            step="0.1"
            placeholder="Current mm"
            :class="styles.measurementInput"
          >
          <input
            v-model.number="setupMeasurements[idx].cents_error"
            type="number"
            step="1"
            placeholder="Cents error"
            :class="styles.measurementInput"
          >
        </div>
      </div>

      <button
        :disabled="store.saddleLoading"
        :class="shared.btnSecondary"
        @click="calculateSetupAdjustments"
      >
        <span v-if="store.saddleLoading">Calculating...</span>
        <span v-else>Calculate Adjustments</span>
      </button>

      <!-- Setup Results -->
      <div
        v-if="store.saddleSetupResult"
        :class="styles.results"
      >
        <div :class="styles.compensationGrid">
          <div
            v-for="str in store.saddleSetupResult.string_results"
            :key="str.name"
            :class="styles.compRow"
          >
            <span :class="styles.compString">{{ str.name }}</span>
            <span :class="[styles.compAdjust, str.delta_L_mm > 0 ? styles.adjustBack : styles.adjustForward]">
              {{ str.delta_L_mm > 0 ? '+' : '' }}{{ str.delta_L_mm.toFixed(2) }} mm
            </span>
            <span :class="styles.compNew">→ {{ str.new_comp_mm.toFixed(2) }} mm</span>
          </div>
        </div>

        <div :class="styles.adjustStats">
          <span>Avg: {{ store.saddleSetupResult.avg_adjustment_mm.toFixed(2) }} mm</span>
          <span>Max: {{ store.saddleSetupResult.max_adjustment_mm.toFixed(2) }} mm</span>
        </div>

        <div :class="styles.recommendation">
          {{ store.saddleSetupResult.recommendation }}
        </div>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="store.saddleError"
      :class="shared.bannerError"
    >
      {{ store.saddleError }}
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive } from "vue";
import { useInstrumentGeometryStore } from "@/stores/instrumentGeometryStore";
import shared from "@/styles/dark-theme-shared.module.css";
import styles from "./SaddleCompensationPanel.module.css";

const store = useInstrumentGeometryStore();

const setupMeasurements = reactive([
  { current_compensation_mm: 2.0, cents_error: 0 },
  { current_compensation_mm: 2.2, cents_error: 0 },
  { current_compensation_mm: 2.4, cents_error: 0 },
  { current_compensation_mm: 2.8, cents_error: 0 },
  { current_compensation_mm: 3.2, cents_error: 0 },
  { current_compensation_mm: 3.5, cents_error: 0 },
]);

function calculateSetupAdjustments() {
  store.calculateSaddleCompensationSetup(setupMeasurements);
}
</script>
