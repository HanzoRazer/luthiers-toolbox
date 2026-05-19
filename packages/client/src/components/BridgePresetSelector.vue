<template>
  <section :class="shared.cardDarker">
    <h4 :class="styles.panelTitle">Bridge Preset</h4>

    <!-- Bridge Style Selector -->
    <div :class="styles.controls">
      <div :class="shared.inputRow">
        <label>Body Style</label>
        <select
          v-model="store.selectedBridgeStyle"
          :class="shared.selectDark"
          @change="store.calculateBridge"
        >
          <option
            v-for="style in store.bridgeOptions"
            :key="style"
            :value="style"
          >
            {{ formatStyleName(style) }}
          </option>
        </select>
      </div>

      <button
        :disabled="store.bridgeLoading"
        :class="shared.btnSecondary"
        @click="store.calculateBridge"
      >
        <span v-if="store.bridgeLoading">Loading...</span>
        <span v-else>Calculate</span>
      </button>
    </div>

    <!-- Error -->
    <div
      v-if="store.bridgeError"
      :class="shared.bannerError"
    >
      {{ store.bridgeError }}
    </div>

    <!-- Results -->
    <div
      v-if="store.bridgeSpec"
      :class="styles.results"
    >
      <div :class="styles.specGrid">
        <div :class="styles.specRow">
          <span :class="styles.specLabel">String Spacing</span>
          <span :class="styles.specValue">{{ store.bridgeSpec.string_spacing_mm.toFixed(1) }} mm</span>
        </div>
        <div :class="styles.specRow">
          <span :class="styles.specLabel">Bridge Size</span>
          <span :class="styles.specValue">
            {{ store.bridgeSpec.bridge_length_mm.toFixed(1) }} × {{ store.bridgeSpec.bridge_width_mm.toFixed(1) }} mm
          </span>
        </div>
        <div :class="styles.specRow">
          <span :class="styles.specLabel">Saddle Slot</span>
          <span :class="styles.specValue">
            {{ store.bridgeSpec.saddle_slot_width_mm.toFixed(1) }} × {{ store.bridgeSpec.saddle_slot_depth_mm.toFixed(1) }} mm
          </span>
        </div>
        <div :class="styles.specRow">
          <span :class="styles.specLabel">Pin Spacing</span>
          <span :class="styles.specValue">{{ store.bridgeSpec.pin_spacing_mm.toFixed(1) }} mm</span>
        </div>
        <div :class="styles.specRow">
          <span :class="styles.specLabel">Bridge Plate</span>
          <span :class="styles.specValue">
            {{ store.bridgeSpec.bridge_plate_length_mm.toFixed(0) }} × {{ store.bridgeSpec.bridge_plate_width_mm.toFixed(0) }} mm
          </span>
        </div>
        <div :class="styles.specRow">
          <span :class="styles.specLabel">Material</span>
          <span :class="styles.specValue">{{ store.bridgeSpec.material }}</span>
        </div>
      </div>

      <!-- Gate -->
      <div :class="[styles.gate, gateClass]">
        {{ store.bridgeSpec.gate }}
      </div>

      <!-- Notes -->
      <div
        v-if="store.bridgeSpec.notes.length > 0"
        :class="styles.notes"
      >
        <span
          v-for="(note, idx) in store.bridgeSpec.notes"
          :key="idx"
          :class="styles.note"
        >
          {{ note }}
        </span>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!store.bridgeLoading && !store.bridgeError"
      :class="styles.empty"
    >
      Select a body style to see bridge specs
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useInstrumentGeometryStore } from "@/stores/instrumentGeometryStore";
import shared from "@/styles/dark-theme-shared.module.css";
import styles from "./BridgePresetSelector.module.css";

const store = useInstrumentGeometryStore();

function formatStyleName(style: string): string {
  return style
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());
}

const gateClass = computed(() => {
  switch (store.bridgeSpec?.gate) {
    case "GREEN": return styles.gateGreen;
    case "YELLOW": return styles.gateYellow;
    case "RED": return styles.gateRed;
    default: return "";
  }
});

onMounted(() => {
  store.loadBridgeOptions();
});
</script>
