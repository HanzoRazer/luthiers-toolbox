<template>
  <div :class="$style['cam-essentials-lab']">
    <h1>CAM Essentials Lab</h1>
    <p :class="$style.subtitle">
      N10 Essential CAM operations for CNC guitar lutherie
    </p>

    <div :class="$style['operations-grid']">
      <!-- Roughing Operation -->
      <div :class="$style['operation-card']">
        <div :class="$style['card-header']">
          <h2>🪓 Roughing</h2>
          <span :class="$style.badge">N10</span>
        </div>
        <p>Simple rectangular roughing for pocket clearing</p>

        <div :class="$style.params">
          <div :class="$style['param-row']">
            <label>Width (mm):</label>
            <input
              v-model.number="roughing.params.value.width"
              type="number"
              step="0.1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Height (mm):</label>
            <input
              v-model.number="roughing.params.value.height"
              type="number"
              step="0.1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Stepdown (mm):</label>
            <input
              v-model.number="roughing.params.value.stepdown"
              type="number"
              step="0.1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Feed (mm/min):</label>
            <input
              v-model.number="roughing.params.value.feed"
              type="number"
              step="10"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Post:</label>
            <select v-model="roughing.params.value.post">
              <option value="GRBL">
                GRBL
              </option>
              <option value="Mach4">
                Mach4
              </option>
              <option value="LinuxCNC">
                LinuxCNC
              </option>
              <option value="PathPilot">
                PathPilot
              </option>
              <option value="MASSO">
                MASSO
              </option>
            </select>
          </div>
        </div>

        <button
          :class="$style['export-btn']"
          @click="roughing.exportGcode"
        >
          Export G-code
        </button>
      </div>

      <!-- Drilling Operation -->
      <div :class="$style['operation-card']">
        <div :class="$style['card-header']">
          <h2>🔩 Drilling (G81/G83)</h2>
          <span :class="$style.badge">N10</span>
        </div>
        <p>Modal drilling cycles for hole arrays</p>

        <div :class="$style.params">
          <div :class="$style['param-row']">
            <label>Cycle:</label>
            <select v-model="drilling.params.value.cycle">
              <option value="G81">
                G81 (Simple)
              </option>
              <option value="G83">
                G83 (Peck)
              </option>
            </select>
          </div>
          <div :class="$style['param-row']">
            <label>Depth (mm):</label>
            <input
              v-model.number="drilling.params.value.depth"
              type="number"
              step="0.1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Feed (mm/min):</label>
            <input
              v-model.number="drilling.params.value.feed"
              type="number"
              step="10"
            >
          </div>
          <div
            v-if="drilling.params.value.cycle === 'G83'"
            :class="$style['param-row']"
          >
            <label>Peck Depth (mm):</label>
            <input
              v-model.number="drilling.params.value.peck_q"
              type="number"
              step="0.1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Holes (JSON):</label>
            <textarea
              v-model="drilling.params.value.holesJson"
              rows="3"
              placeholder="[{&quot;x&quot;:10,&quot;y&quot;:10},{&quot;x&quot;:20,&quot;y&quot;:10}]"
            />
          </div>
        </div>

        <button
          :class="$style['export-btn']"
          @click="drilling.exportGcode"
        >
          Export G-code
        </button>
      </div>

      <!-- Drill Pattern Operation -->
      <PatternOperationCard
        :pattern="pattern"
        :styles="$style"
      />

      <!-- Bi-Arc Contour -->
      <div :class="$style['operation-card']">
        <div :class="$style['card-header']">
          <h2>🔺 Contour Following</h2>
          <span :class="$style.badge">N10</span>
        </div>
        <p>Linear contour following from point array</p>

        <div :class="$style.params">
          <div :class="$style['param-row']">
            <label>Points (JSON):</label>
            <textarea
              v-model="contour.params.value.pathJson"
              rows="4"
              placeholder="[{&quot;x&quot;:0,&quot;y&quot;:0},{&quot;x&quot;:50,&quot;y&quot;:0},{&quot;x&quot;:50,&quot;y&quot;:30}]"
            />
          </div>
          <div :class="$style['param-row']">
            <label>Depth (mm):</label>
            <input
              v-model.number="contour.params.value.depth"
              type="number"
              step="0.1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Feed (mm/min):</label>
            <input
              v-model.number="contour.params.value.feed"
              type="number"
              step="10"
            >
          </div>
        </div>

        <button
          :class="$style['export-btn']"
          @click="contour.exportGcode"
        >
          Export G-code
        </button>
      </div>

      <!-- Probe Patterns (N09) -->
      <ProbeOperationCard
        :probe="probe"
        :styles="$style"
      />

      <!-- Retract Patterns (N08) -->
      <RetractOperationCard
        :retract="retract"
        :styles="$style"
      />
    </div>

    <!-- Info Section -->
    <div :class="$style['info-section']">
      <h3>ℹ️ About CAM Essentials (N0-N10)</h3>
      <p>
        <strong>Roughing (N01):</strong> Simple rectangular boundary milling for pocket clearing and face milling.<br>
        <strong>Drilling (N06):</strong> Modal cycles (G81 simple, G83 peck) for efficient hole drilling.<br>
        <strong>Patterns (N07):</strong> Parametric hole arrays (grid, circular, linear) for mounting holes, bridge pins, etc.<br>
        <strong>Contour (N10):</strong> Basic linear interpolation for simple contour following.<br>
        <strong>Probe Patterns (N09):</strong> Touch probe routines for work offset establishment (corner, boss, surface).<br>
        <strong>Retract Patterns (N08):</strong> Safe retract strategies (direct, ramped, helical) for tool changes.
      </p>
      <p><strong>Post-Processor Support:</strong> All operations support GRBL, Mach4, LinuxCNC, PathPilot, and MASSO with proper headers/footers.</p>
      <p><strong>Industrial Features (N05):</strong> Fanuc and Haas post-processors include R-mode arcs, G4 S dwell, and modal cycle expansion.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * CAM Essentials Lab - Essential CAM operations for CNC lutherie.
 *
 * Operations:
 * - Roughing (N10): Rectangular pocket clearing
 * - Drilling (N06): G81/G83 modal cycles
 * - Patterns (N07): Grid/circle/line drill patterns
 * - Contour (N10): Bi-arc contour following
 * - Probe (N09): Touch probe work offset routines
 * - Retract (N08): Safe retract strategies
 */
import {
  useRoughingOperation,
  useDrillingOperation,
  usePatternOperation,
  useContourOperation,
  useProbeOperation,
  useRetractOperation
} from './cam-essentials'
import PatternOperationCard from './cam-essentials/PatternOperationCard.vue'
import ProbeOperationCard from './cam-essentials/ProbeOperationCard.vue'
import RetractOperationCard from './cam-essentials/RetractOperationCard.vue'

// Initialize all operation composables
const roughing = useRoughingOperation()
const drilling = useDrillingOperation()
const pattern = usePatternOperation()
const contour = useContourOperation()
const probe = useProbeOperation()
const retract = useRetractOperation()
</script>

<style module src="./CAMEssentialsLab.module.css"></style>
