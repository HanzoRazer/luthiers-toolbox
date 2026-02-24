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
    <InstrumentGeometryForm
      :engine="engine"
      @compute="onComputeInstrumentGeometry"
    />

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
import { useArtStudioEngine } from "@/stores/useArtStudioEngine";
import ArtStudioFeasibilityPanel from "./ArtStudioFeasibilityPanel.vue";
import { InstrumentGeometryForm } from "./sidebar";

const engine = useArtStudioEngine();

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

interface InstrumentGeometryParams {
  scale_length_mm: number
  fret_count: number
  nut_width_mm: number
  heel_width_mm: number
  base_radius_mm?: number
  end_radius_mm?: number
}

function onComputeInstrumentGeometry(params: InstrumentGeometryParams) {
  engine.computeInstrumentGeometry(params).catch(console.error);
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
