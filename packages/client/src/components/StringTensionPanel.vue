<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">String Tension</h4>

    <!-- String Set Selector -->
    <div :class="styles.controls">
      <div :class="shared.inputRow">
        <label>String Set</label>
        <select
          v-model="store.selectedStringSet"
          :class="shared.selectDark"
          @change="store.calculateStringTension"
        >
          <option
            v-for="preset in store.stringPresets"
            :key="preset"
            :value="preset"
          >
            {{ formatPresetName(preset) }}
          </option>
        </select>
      </div>

      <button
        :disabled="store.stringTensionLoading"
        :class="shared.btnSecondary"
        @click="store.calculateStringTension"
      >
        <span v-if="store.stringTensionLoading">Calculating...</span>
        <span v-else>Calculate</span>
      </button>
    </div>

    <!-- Error -->
    <div
      v-if="store.stringTensionError"
      :class="shared.bannerError"
    >
      {{ store.stringTensionError }}
    </div>

    <!-- Results -->
    <div
      v-if="store.stringTensionResult"
      :class="styles.results"
    >
      <!-- Total -->
      <div :class="styles.totalRow">
        <span :class="styles.totalLabel">Total Tension</span>
        <span :class="styles.totalValue">
          {{ store.stringTensionResult.total_tension_lb.toFixed(1) }} lb
        </span>
        <span :class="styles.totalValueSub">
          ({{ store.stringTensionResult.total_tension_n.toFixed(0) }} N)
        </span>
      </div>

      <!-- Per-string -->
      <div :class="styles.stringsGrid">
        <div
          v-for="str in store.stringTensionResult.strings"
          :key="str.name"
          :class="styles.stringRow"
        >
          <span :class="styles.stringName">{{ str.name }}</span>
          <span :class="styles.stringNote">{{ str.note }}</span>
          <span :class="styles.stringGauge">{{ str.gauge_inch.toFixed(3) }}"</span>
          <span :class="styles.stringTension">{{ str.tension_lb.toFixed(1) }} lb</span>
        </div>
      </div>

      <div :class="styles.meta">
        Scale: {{ store.stringTensionResult.scale_length_mm.toFixed(1) }} mm
        | Set: {{ store.stringTensionResult.set_name }}
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!store.stringTensionLoading && !store.stringTensionError"
      :class="styles.empty"
    >
      Select a string set and click Calculate
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useInstrumentGeometryStore } from "@/stores/instrumentGeometryStore";
import shared from "@/styles/dark-theme-shared.module.css";
import styles from "./StringTensionPanel.module.css";

const store = useInstrumentGeometryStore();

function formatPresetName(preset: string): string {
  return preset
    .replace(/_/g, " ")
    .replace(/(\d+)$/, " ($1)")
    .replace(/\b\w/g, c => c.toUpperCase());
}

onMounted(() => {
  store.loadStringPresets();
});
</script>
