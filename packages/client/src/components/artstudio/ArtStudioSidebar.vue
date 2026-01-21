<template>
  <aside class="artstudio-sidebar">
    <!-- Tools & Materials -->
    <section class="sidebar-section">
      <h3>Tools & Materials</h3>
      <div class="button-row">
        <button
          :disabled="engine.loading.tools"
          @click="onLoadTools"
        >
          {{ engine.loading.tools ? "Loading..." : "Load Tools" }}
        </button>
        <button
          :disabled="engine.loading.materials"
          @click="onLoadMaterials"
        >
          {{ engine.loading.materials ? "Loading..." : "Load Materials" }}
        </button>
      </div>

      <div
        v-if="engine.tools.value.length"
        class="list-section"
      >
        <h4>Tools ({{ engine.tools.value.length }})</h4>
        <ul class="item-list">
          <li
            v-for="t in engine.tools.value.slice(0, 5)"
            :key="t.tool_id"
          >
            {{ t.name }} ({{ t.diameter_mm ?? "?" }}mm)
          </li>
          <li
            v-if="engine.tools.value.length > 5"
            class="more"
          >
            +{{ engine.tools.value.length - 5 }} more...
          </li>
        </ul>
      </div>

      <div
        v-if="engine.materials.value.length"
        class="list-section"
      >
        <h4>Materials ({{ engine.materials.value.length }})</h4>
        <ul class="item-list">
          <li
            v-for="m in engine.materials.value.slice(0, 5)"
            :key="m.material_id"
          >
            {{ m.name }}
          </li>
          <li
            v-if="engine.materials.value.length > 5"
            class="more"
          >
            +{{ engine.materials.value.length - 5 }} more...
          </li>
        </ul>
      </div>
    </section>

    <!-- Geometry Generation -->
    <section class="sidebar-section">
      <h3>Geometry</h3>
      <div class="button-row">
        <button
          :disabled="engine.loading.geometry"
          @click="onGenerateRosette"
        >
          Rosette
        </button>
        <button
          :disabled="engine.loading.geometry"
          @click="onGenerateRelief"
        >
          Relief
        </button>
        <button
          :disabled="engine.loading.geometry"
          @click="onGenerateVCarve"
        >
          V-Carve
        </button>
      </div>

      <div
        v-if="engine.hasGeometry.value"
        class="status-info"
      >
        ✓ {{ engine.currentPaths.value.length }} paths loaded
      </div>
    </section>

    <!-- Feasibility & Toolpaths -->
    <section class="sidebar-section">
      <h3>RMOS Feasibility</h3>
      <div class="button-row">
        <button
          :disabled="engine.loading.feasibility"
          @click="onEvaluateFeasibility"
        >
          Evaluate
        </button>
        <button
          :disabled="engine.loading.toolpaths"
          @click="onPlanToolpaths"
        >
          Plan Toolpaths
        </button>
      </div>

      <!-- Wave 9: Feasibility Panel with Risk Overlays -->
      <ArtStudioFeasibilityPanel />

      <div
        v-if="engine.hasToolpaths.value"
        class="status-info"
      >
        ✓ {{ engine.toolpaths.value.length }} toolpaths generated
      </div>
    </section>

    <!-- Instrument Geometry -->
    <section class="sidebar-section">
      <h3>Instrument Geometry</h3>

      <!-- Presets -->
      <div class="form-row">
        <label>Preset</label>
        <select
          v-model="selectedPreset"
          @change="onPresetChange"
        >
          <option value="">
            Custom
          </option>
          <option value="fender_25.5">
            Fender 25.5"
          </option>
          <option value="gibson_24.75">
            Gibson 24.75"
          </option>
          <option value="prs_25">
            PRS 25"
          </option>
          <option value="classical">
            Classical
          </option>
        </select>
      </div>

      <div class="form-row">
        <label>Scale Length (mm)</label>
        <input
          v-model.number="scaleLengthMm"
          type="number"
          step="0.1"
        >
      </div>

      <div class="form-row">
        <label>Fret Count</label>
        <input
          v-model.number="fretCount"
          type="number"
          min="1"
          max="36"
        >
      </div>

      <div class="form-row">
        <label>Nut Width (mm)</label>
        <input
          v-model.number="nutWidthMm"
          type="number"
          step="0.1"
        >
      </div>

      <div class="form-row">
        <label>Heel Width (mm)</label>
        <input
          v-model.number="heelWidthMm"
          type="number"
          step="0.1"
        >
      </div>

      <details class="advanced-options">
        <summary>Compound Radius</summary>
        <div class="form-row">
          <label>Base Radius (mm)</label>
          <input
            v-model.number="baseRadiusMm"
            type="number"
            step="1"
            placeholder="e.g., 184 (7.25in)"
          >
        </div>
        <div class="form-row">
          <label>End Radius (mm)</label>
          <input
            v-model.number="endRadiusMm"
            type="number"
            step="1"
            placeholder="e.g., 305 (12in)"
          >
        </div>
      </details>

      <button
        :disabled="engine.loading.instrument"
        class="primary-button"
        @click="onComputeInstrumentGeometry"
      >
        {{ engine.loading.instrument ? "Computing..." : "Compute Geometry" }}
      </button>

      <!-- Results -->
      <div
        v-if="engine.fretPositions.value.length"
        class="instrument-results"
      >
        <p>✓ {{ engine.fretPositions.value.length }} frets calculated</p>
        <p v-if="engine.bridgeLocationMm.value !== null">
          Bridge @ {{ engine.bridgeLocationMm.value?.toFixed(2) }}mm
        </p>
        <p v-if="engine.fretboardLengthMm.value !== null">
          Fretboard length: {{ engine.fretboardLengthMm.value?.toFixed(2) }}mm
        </p>
        <p v-if="engine.radiusProfile.value.length">
          Compound radius: {{ engine.radiusProfile.value[0]?.toFixed(1) }}mm →
          {{
            engine.radiusProfile.value[
              engine.radiusProfile.value.length - 1
            ]?.toFixed(1)
          }}mm
        </p>
      </div>
    </section>

    <!-- Error display -->
    <div
      v-if="engine.lastError.value"
      class="error-banner"
    >
      {{ engine.lastError.value }}
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useArtStudioEngine } from "@/stores/useArtStudioEngine";
import ArtStudioFeasibilityPanel from "./ArtStudioFeasibilityPanel.vue";

const engine = useArtStudioEngine();

// Instrument geometry state
const selectedPreset = ref("");
const scaleLengthMm = ref(648); // 25.5"
const fretCount = ref(22);
const nutWidthMm = ref(42);
const heelWidthMm = ref(56);
const baseRadiusMm = ref<number | undefined>(undefined);
const endRadiusMm = ref<number | undefined>(undefined);

// Preset configurations
const PRESETS: Record<string, { scale: number; nut: number; heel: number }> = {
  "fender_25.5": { scale: 647.7, nut: 42.86, heel: 56 },
  "gibson_24.75": { scale: 628.65, nut: 43.05, heel: 55 },
  prs_25: { scale: 635, nut: 42.5, heel: 55.5 },
  classical: { scale: 650, nut: 52, heel: 62 },
};

// Handlers
function onLoadTools() {
  engine.loadTools().catch(console.error);
}

function onLoadMaterials() {
  engine.loadMaterials().catch(console.error);
}

function onGenerateRosette() {
  engine
    .generateRosetteGeometry({
      pattern: "concentric",
      outer_diameter_mm: 100,
      inner_diameter_mm: 80,
    } as any)
    .catch(console.error);
}

function onGenerateRelief() {
  engine
    .generateReliefGeometry({
      width_mm: 50,
      height_mm: 30,
      depth_mm: 2,
    })
    .catch(console.error);
}

function onGenerateVCarve() {
  engine
    .generateVCarveGeometry({
      text: "ToolBox",
      depth_mm: 1.5,
      font: "Arial",
    })
    .catch(console.error);
}

function onEvaluateFeasibility() {
  engine
    .evaluateFeasibility({
      design_id: "current",
      paths: engine.currentPaths.value,
    })
    .catch(console.error);
}

function onPlanToolpaths() {
  engine
    .planToolpathsForCurrentDesign({
      design_id: "current",
      paths: engine.currentPaths.value,
    })
    .catch(console.error);
}

function onPresetChange() {
  if (selectedPreset.value && PRESETS[selectedPreset.value]) {
    const preset = PRESETS[selectedPreset.value];
    scaleLengthMm.value = preset.scale;
    nutWidthMm.value = preset.nut;
    heelWidthMm.value = preset.heel;
  }
}

function onComputeInstrumentGeometry() {
  engine
    .computeInstrumentGeometry({
      scale_length_mm: scaleLengthMm.value,
      fret_count: fretCount.value,
      nut_width_mm: nutWidthMm.value,
      heel_width_mm: heelWidthMm.value,
      base_radius_mm: baseRadiusMm.value,
      end_radius_mm: endRadiusMm.value,
    })
    .catch(console.error);
}
</script>

<style scoped>
.artstudio-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
  font-size: 0.85rem;
  overflow-y: auto;
}

.sidebar-section {
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 0.75rem;
}

.sidebar-section h3 {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #212529;
}

.sidebar-section h4 {
  font-size: 0.8rem;
  font-weight: 500;
  margin-top: 0.5rem;
  margin-bottom: 0.25rem;
  color: #495057;
}

.button-row {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.button-row button {
  flex: 1;
  min-width: 60px;
  padding: 0.35rem 0.5rem;
  font-size: 0.75rem;
  border: 1px solid #ced4da;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.button-row button:hover:not(:disabled) {
  background: #e9ecef;
}

.button-row button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary-button {
  width: 100%;
  padding: 0.5rem;
  font-size: 0.8rem;
  font-weight: 500;
  border: none;
  background: #0d6efd;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.5rem;
}

.primary-button:hover:not(:disabled) {
  background: #0b5ed7;
}

.primary-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.form-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 0.35rem;
}

.form-row label {
  font-size: 0.75rem;
  color: #6c757d;
  margin-bottom: 0.15rem;
}

.form-row input,
.form-row select {
  padding: 0.3rem 0.4rem;
  font-size: 0.8rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
}

.advanced-options {
  margin: 0.5rem 0;
  padding: 0.25rem;
  background: #f1f3f4;
  border-radius: 4px;
}

.advanced-options summary {
  font-size: 0.75rem;
  color: #495057;
  cursor: pointer;
  padding: 0.25rem;
}

.item-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.75rem;
}

.item-list li {
  padding: 0.15rem 0;
  color: #495057;
  border-bottom: 1px solid #f1f3f4;
}

.item-list .more {
  color: #6c757d;
  font-style: italic;
}

.status-info {
  font-size: 0.75rem;
  color: #198754;
  padding: 0.25rem;
  background: #d1e7dd;
  border-radius: 4px;
  margin-top: 0.25rem;
}

.feasibility-result {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

.feasibility-result .score {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.score-good {
  color: #198754;
}
.score-warn {
  color: #ffc107;
}
.score-bad {
  color: #dc3545;
}

.feasibility-result .failures,
.feasibility-result .warnings {
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.feasibility-result .failures {
  color: #dc3545;
}
.feasibility-result .warnings {
  color: #856404;
}

.feasibility-result ul {
  margin: 0.25rem 0 0 1rem;
  padding: 0;
}

.instrument-results {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #d1e7dd;
  border-radius: 4px;
  font-size: 0.75rem;
}

.instrument-results p {
  margin: 0.15rem 0;
}

.error-banner {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f8d7da;
  border: 1px solid #f5c2c7;
  border-radius: 4px;
  color: #842029;
  font-size: 0.75rem;
}
</style>
