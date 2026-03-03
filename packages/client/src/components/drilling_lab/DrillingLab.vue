<template>
  <div :class="styles.drillingLab">
    <!-- Header -->
    <div :class="styles.labHeader">
      <h2>Drilling Lab</h2>
      <div :class="styles.headerActions">
        <button
          :class="styles.btnPrimary"
          :disabled="holes.length === 0"
          @click="exportGCode"
        >
          Export G-Code
        </button>
        <button
          :class="styles.btnSecondary"
          @click="clearAll"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div :class="styles.labContent">
      <!-- Left Panel -->
      <div :class="styles.leftPanel">
        <!-- Tool Setup -->
        <DrillToolSetup
          v-model:tool-type="params.toolType"
          v-model:tool-diameter="params.toolDiameter"
          v-model:spindle-rpm="params.spindleRpm"
          v-model:feed-rate="params.feedRate"
          :styles="styles"
          @update:tool-type="updatePreview"
          @update:tool-diameter="updatePreview"
          @update:spindle-rpm="updatePreview"
          @update:feed-rate="updatePreview"
        />

        <!-- Cycle Type -->
        <DrillCycleType
          v-model:cycle-value="params.cycle"
          v-model:peck-depth="params.peckDepth"
          v-model:thread-pitch="params.threadPitch"
          :styles="styles"
          @update:cycle-value="updatePreview"
          @update:peck-depth="updatePreview"
          @update:thread-pitch="updatePreview"
        />

        <!-- Depth Settings -->
        <DrillDepthSettings
          v-model:depth="params.depth"
          v-model:retract="params.retract"
          v-model:safe-z="params.safeZ"
          :styles="styles"
          @update:depth="updatePreview"
          @update:retract="updatePreview"
          @update:safe-z="updatePreview"
        />

        <!-- Pattern Generator -->
        <DrillPatternSelector
          v-model:pattern-type="patternType"
          v-model:csv-input="csvInput"
          :styles="styles"
          :linear-pattern="linearPattern"
          :circular-pattern="circularPattern"
          :grid-pattern="gridPattern"
          @generate-linear="generateLinearPattern"
          @generate-circular="generateCircularPattern"
          @generate-grid="generateGridPattern"
          @import-csv="importCsv"
        />

        <!-- Hole List -->
        <DrillHoleList
          :styles="styles"
          :holes="holes"
          :selected-hole="selectedHole"
          @select-hole="selectHole"
          @remove-hole="removeHole"
          @toggle-hole="toggleHole"
        />

        <!-- Post Processor -->
        <section :class="styles.panelSection">
          <h3>Post Processor</h3>
          <select
            v-model="params.postId"
            :class="styles.postSelector"
            @change="updatePreview"
          >
            <option value="GRBL">
              GRBL (Expanded)
            </option>
            <option value="LinuxCNC">
              LinuxCNC (Modal)
            </option>
            <option value="Mach4">
              Mach4 (Modal)
            </option>
            <option value="PathPilot">
              PathPilot (Modal)
            </option>
            <option value="Haas">
              Haas (Modal)
            </option>
          </select>
        </section>
      </div>

      <!-- Canvas Preview -->
      <div :class="styles.canvasContainer">
        <canvas
          ref="canvas"
          width="600"
          height="600"
          @click="onCanvasClick"
          @mousemove="onCanvasHover"
        />

        <!-- Stats Overlay -->
        <div :class="styles.statsOverlay">
          <div :class="styles.stat">
            <strong>Holes:</strong> {{ enabledHoles.length }}
          </div>
          <div :class="styles.stat">
            <strong>Depth:</strong> {{ totalDepth.toFixed(1) }} mm
          </div>
          <div :class="styles.stat">
            <strong>Time:</strong> {{ estimatedTime.toFixed(1) }} min
          </div>
        </div>
      </div>
    </div>

    <!-- G-Code Preview (Collapsible) -->
    <div
      :class="[styles.bottomPanel, { [styles.bottomPanelCollapsed]: gcodeCollapsed }]"
    >
      <div
        :class="styles.panelHeader"
        @click="gcodeCollapsed = !gcodeCollapsed"
      >
        <h3>G-Code Preview</h3>
        <div :class="styles.panelActions">
          <button
            :class="styles.btnIcon"
            title="Copy to clipboard"
            @click.stop="copyGCode"
          >
            Copy
          </button>
          <button :class="styles.btnIcon">
            {{ gcodeCollapsed ? '▲' : '▼' }}
          </button>
        </div>
      </div>
      <div
        v-if="!gcodeCollapsed"
        :class="styles.gcodeContent"
      >
        <pre>{{ gcodePreview }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * DrillingLab - Drill pattern and G-code generation lab.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { onMounted, watch } from 'vue'
import styles from '../DrillingLab.module.css'
import DrillToolSetup from '../drilling/DrillToolSetup.vue'
import DrillCycleType from '../drilling/DrillCycleType.vue'
import DrillDepthSettings from '../drilling/DrillDepthSettings.vue'
import DrillPatternSelector from '../drilling/DrillPatternSelector.vue'
import DrillHoleList from '../drilling/DrillHoleList.vue'
import {
  useDrillingState,
  useDrillingHoles,
  useDrillingCanvas,
  useDrillingGcode
} from './composables'

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
  params,
  holes,
  selectedHole,
  patternType,
  linearPattern,
  circularPattern,
  gridPattern,
  csvInput,
  gcodePreview,
  gcodeCollapsed,
  canvas,
  enabledHoles,
  totalDepth,
  estimatedTime
} = useDrillingState()

// Canvas
const { drawCanvas, onCanvasClick, onCanvasHover } = useDrillingCanvas(
  canvas,
  holes,
  selectedHole,
  patternType,
  updatePreview
)

// G-code
const { generateGCodePreview, exportGCode, copyGCode } = useDrillingGcode(
  params,
  enabledHoles,
  gcodePreview
)

// Hole management
const {
  selectHole,
  toggleHole,
  removeHole,
  clearAll,
  generateLinearPattern,
  generateCircularPattern,
  generateGridPattern,
  importCsv
} = useDrillingHoles(
  holes,
  selectedHole,
  linearPattern,
  circularPattern,
  gridPattern,
  csvInput,
  updatePreview
)

// =============================================================================
// METHODS
// =============================================================================

async function updatePreview(): Promise<void> {
  drawCanvas()
  await generateGCodePreview()
}

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(() => {
  updatePreview()
})

// Watch for parameter changes
watch(params, () => updatePreview(), { deep: true })
</script>
