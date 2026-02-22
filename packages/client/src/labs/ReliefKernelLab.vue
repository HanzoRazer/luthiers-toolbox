<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Relief Kernel Lab - Development Prototyping

Phase 24.6: Dynamic scallop (slope-aware spacing)
Phase 24.7: Relief Preset Comparator (Safe/Standard/Aggressive)

Repository: HanzoRazer/luthiers-toolbox
Updated: January 2025

Features:
- Rapid relief toolpath prototyping with canvas preview
- Dynamic scallop optimizer (slope-aware stepover)
- Preset comparison testing (Safe/Standard/Aggressive)
- Stock thickness control for material removal simulation
- Load hotspot visualization (orange, intensity-based)
- Thin floor zone detection (red circles)
- Snapshot persistence to Risk Timeline

REFACTORED: Uses composables for cleaner separation of concerns.
-->

<script setup lang="ts">
import ParametersGrid from './relief_kernel_lab/ParametersGrid.vue'
import RunButtonsPanel from './relief_kernel_lab/RunButtonsPanel.vue'
import PresetComparisonTable from './relief_kernel_lab/PresetComparisonTable.vue'
import SimBridgeResultsPanel from './relief_kernel_lab/SimBridgeResultsPanel.vue'
import {
  useReliefKernelState,
  useReliefKernelCanvas,
  useReliefKernelApi
} from './relief_kernel_lab/composables'

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
  file,
  map,
  result,
  reliefSimBridgeOut,
  toolD,
  stepdown,
  scallop,
  stockThickness,
  units,
  useDynamicScallop,
  comparisons,
  isComparing,
  selectedComparisonName
} = useReliefKernelState()

// Canvas
const { canvas, drawCanvas } = useReliefKernelCanvas(map, result, reliefSimBridgeOut)

// API operations
const {
  onFileChange,
  runFinish,
  runSimBridge,
  runPresetComparison,
  pushSnapshot
} = useReliefKernelApi(
  file,
  map,
  result,
  reliefSimBridgeOut,
  toolD,
  stepdown,
  scallop,
  stockThickness,
  units,
  useDynamicScallop,
  comparisons,
  isComparing,
  drawCanvas
)

// =============================================================================
// ACTIONS
// =============================================================================

function selectComparison(name: string) {
  selectedComparisonName.value = name
}
</script>

<template>
  <div class="p-4 max-w-6xl mx-auto space-y-4">
    <h1 class="text-2xl font-bold">
      Relief Kernel Lab
    </h1>
    <p class="text-sm text-gray-600">
      Phase 24.6: Dynamic scallop optimizer<br>
      Phase 24.7: Preset comparator (Safe/Standard/Aggressive)
    </p>

    <!-- Upload -->
    <div class="border rounded p-3 space-y-2">
      <label class="block text-sm font-medium">Heightmap (PNG/JPEG):</label>
      <input
        type="file"
        accept="image/*"
        @change="onFileChange"
      >

      <!-- Units selector (before upload) -->
      <div class="flex items-center gap-2 text-xs">
        <span class="text-gray-600">Units:</span>
        <label class="flex items-center gap-1">
          <input
            v-model="units"
            type="radio"
            value="mm"
          >
          <span>mm</span>
        </label>
        <label class="flex items-center gap-1">
          <input
            v-model="units"
            type="radio"
            value="inch"
          >
          <span>inch</span>
        </label>
        <span class="text-gray-500 ml-2">(Set before uploading)</span>
      </div>
    </div>

    <!-- Parameters -->
    <ParametersGrid
      v-if="map"
      v-model:tool-d="toolD"
      v-model:stepdown="stepdown"
      v-model:scallop="scallop"
      v-model:stock-thickness="stockThickness"
      v-model:use-dynamic-scallop="useDynamicScallop"
      :units="map.units"
    />

    <!-- Run Buttons -->
    <RunButtonsPanel
      v-if="map"
      :has-result="!!result"
      :has-sim-bridge-out="!!reliefSimBridgeOut"
      :is-comparing="isComparing"
      @run-finish="runFinish"
      @run-sim-bridge="runSimBridge"
      @push-snapshot="pushSnapshot"
      @run-preset-comparison="runPresetComparison"
    />

    <!-- Phase 24.7: Comparison Results -->
    <PresetComparisonTable
      v-if="comparisons.length > 0"
      :comparisons="comparisons"
      :selected-name="selectedComparisonName"
      @select="selectComparison"
    />

    <!-- Canvas -->
    <div
      v-if="map"
      class="border rounded p-2 bg-black"
    >
      <canvas
        ref="canvas"
        class="max-w-full h-auto"
      />
    </div>

    <!-- Results -->
    <div
      v-if="result"
      class="text-xs border rounded p-3 space-y-1"
    >
      <div><strong>Moves:</strong> {{ result.moves.length }}</div>
      <div><strong>Length XY:</strong> {{ result.stats.length_xy.toFixed(2) }} mm</div>
      <div><strong>Time Est:</strong> {{ result.stats.est_time_s.toFixed(1) }} s</div>
      <div><strong>Z Range:</strong> {{ result.stats.min_z.toFixed(2) }} to {{ result.stats.max_z.toFixed(2) }} mm</div>
    </div>

    <!-- Sim Bridge Results (Phase 24.4) -->
    <SimBridgeResultsPanel
      v-if="reliefSimBridgeOut"
      :sim-bridge-out="reliefSimBridgeOut"
    />

    <!-- Map Info -->
    <div
      v-if="map"
      class="text-xs text-gray-600 mt-2"
    >
      <div><strong>Map:</strong> {{ map.width }}x{{ map.height }} cells</div>
      <div><strong>Z Range:</strong> {{ map.z_min.toFixed(2) }} to {{ map.z_max.toFixed(2) }} mm</div>
      <div><strong>Cell Size:</strong> {{ map.cell_size_xy.toFixed(2) }} mm</div>
    </div>
  </div>
</template>

<style scoped>
input[type="number"] {
  font-variant-numeric: tabular-nums;
}
</style>
