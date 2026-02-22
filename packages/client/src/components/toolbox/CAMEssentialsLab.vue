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
              <option value="GRBL">GRBL</option>
              <option value="Mach4">Mach4</option>
              <option value="LinuxCNC">LinuxCNC</option>
              <option value="PathPilot">PathPilot</option>
              <option value="MASSO">MASSO</option>
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
              <option value="G81">G81 (Simple)</option>
              <option value="G83">G83 (Peck)</option>
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
      <div :class="$style['operation-card']">
        <div :class="$style['card-header']">
          <h2>📐 Drill Patterns</h2>
          <span :class="$style.badge">N10</span>
        </div>
        <p>Generate drilling patterns (grid, circle, line)</p>

        <div :class="$style.params">
          <div :class="$style['param-row']">
            <label>Pattern:</label>
            <select v-model="pattern.params.value.type">
              <option value="grid">Grid</option>
              <option value="circle">Circle</option>
              <option value="line">Line</option>
            </select>
          </div>

          <!-- Grid Pattern -->
          <template v-if="pattern.params.value.type === 'grid'">
            <div :class="$style['param-row']">
              <label>Rows:</label>
              <input
                v-model.number="pattern.params.value.grid.rows"
                type="number"
                min="1"
              >
            </div>
            <div :class="$style['param-row']">
              <label>Columns:</label>
              <input
                v-model.number="pattern.params.value.grid.cols"
                type="number"
                min="1"
              >
            </div>
            <div :class="$style['param-row']">
              <label>X Spacing (mm):</label>
              <input
                v-model.number="pattern.params.value.grid.dx"
                type="number"
                step="0.1"
              >
            </div>
            <div :class="$style['param-row']">
              <label>Y Spacing (mm):</label>
              <input
                v-model.number="pattern.params.value.grid.dy"
                type="number"
                step="0.1"
              >
            </div>
          </template>

          <!-- Circle Pattern -->
          <template v-if="pattern.params.value.type === 'circle'">
            <div :class="$style['param-row']">
              <label>Count:</label>
              <input
                v-model.number="pattern.params.value.circle.count"
                type="number"
                min="1"
              >
            </div>
            <div :class="$style['param-row']">
              <label>Radius (mm):</label>
              <input
                v-model.number="pattern.params.value.circle.radius"
                type="number"
                step="0.1"
              >
            </div>
            <div :class="$style['param-row']">
              <label>Start Angle (°):</label>
              <input
                v-model.number="pattern.params.value.circle.start_angle_deg"
                type="number"
                step="1"
              >
            </div>
          </template>

          <!-- Line Pattern -->
          <template v-if="pattern.params.value.type === 'line'">
            <div :class="$style['param-row']">
              <label>Count:</label>
              <input
                v-model.number="pattern.params.value.line.count"
                type="number"
                min="1"
              >
            </div>
            <div :class="$style['param-row']">
              <label>X Increment (mm):</label>
              <input
                v-model.number="pattern.params.value.line.dx"
                type="number"
                step="0.1"
              >
            </div>
            <div :class="$style['param-row']">
              <label>Y Increment (mm):</label>
              <input
                v-model.number="pattern.params.value.line.dy"
                type="number"
                step="0.1"
              >
            </div>
          </template>

          <div :class="$style['param-row']">
            <label>Depth (mm):</label>
            <input
              v-model.number="pattern.params.value.depth"
              type="number"
              step="0.1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Feed (mm/min):</label>
            <input
              v-model.number="pattern.params.value.feed"
              type="number"
              step="10"
            >
          </div>
        </div>

        <button
          :class="$style['export-btn']"
          @click="pattern.exportGcode"
        >
          Export G-code
        </button>
      </div>

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
      <div :class="$style['operation-card']">
        <div :class="$style['card-header']">
          <h2>🎯 Probe Patterns</h2>
          <span :class="$style.badge">N09</span>
        </div>
        <p>Work offset establishment with touch probes</p>

        <div :class="$style.params">
          <div :class="$style['param-row']">
            <label>Pattern:</label>
            <select v-model="probe.params.value.pattern">
              <option value="corner_outside">Corner (Outside)</option>
              <option value="corner_inside">Corner (Inside)</option>
              <option value="boss_circular">Boss (Circular)</option>
              <option value="hole_circular">Hole (Circular)</option>
              <option value="surface_z">Surface Z</option>
            </select>
          </div>
          <div :class="$style['param-row']">
            <label>Probe Feed (mm/min):</label>
            <input
              v-model.number="probe.params.value.feed_probe"
              type="number"
              step="10"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Safe Z (mm):</label>
            <input
              v-model.number="probe.params.value.safe_z"
              type="number"
              step="0.5"
            >
          </div>
          <div
            v-if="probe.params.value.pattern.includes('circular')"
            :class="$style['param-row']"
          >
            <label>Est. Diameter (mm):</label>
            <input
              v-model.number="probe.params.value.diameter"
              type="number"
              step="1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Work Offset:</label>
            <select v-model="probe.params.value.work_offset">
              <option value="1">G54 (1)</option>
              <option value="2">G55 (2)</option>
              <option value="3">G56 (3)</option>
              <option value="4">G57 (4)</option>
              <option value="5">G58 (5)</option>
              <option value="6">G59 (6)</option>
            </select>
          </div>
        </div>

        <div :class="$style['button-group']">
          <button
            :class="[$style['export-btn'], $style.half]"
            @click="probe.exportGcode"
          >
            Export G-code
          </button>
          <button
            :class="[$style['export-btn'], $style.half, $style.secondary]"
            @click="probe.exportSVG"
          >
            Export Setup Sheet
          </button>
        </div>
      </div>

      <!-- Retract Patterns (N08) -->
      <div :class="$style['operation-card']">
        <div :class="$style['card-header']">
          <h2>↑ Retract Patterns</h2>
          <span :class="$style.badge">N08</span>
        </div>
        <p>Safe retract strategies for tool changes</p>

        <div :class="$style.params">
          <div :class="$style['param-row']">
            <label>Strategy:</label>
            <select v-model="retract.params.value.strategy">
              <option value="direct">Direct (G0)</option>
              <option value="ramped">Ramped (Linear)</option>
              <option value="helical">Helical (Spiral)</option>
            </select>
          </div>
          <div :class="$style['param-row']">
            <label>Current Z (mm):</label>
            <input
              v-model.number="retract.params.value.current_z"
              type="number"
              step="0.1"
            >
          </div>
          <div :class="$style['param-row']">
            <label>Safe Z (mm):</label>
            <input
              v-model.number="retract.params.value.safe_z"
              type="number"
              step="0.5"
            >
          </div>
          <div
            v-if="retract.params.value.strategy === 'ramped'"
            :class="$style['param-row']"
          >
            <label>Ramp Feed (mm/min):</label>
            <input
              v-model.number="retract.params.value.ramp_feed"
              type="number"
              step="10"
            >
          </div>
          <div
            v-if="retract.params.value.strategy === 'helical'"
            :class="$style['param-row']"
          >
            <label>Helix Radius (mm):</label>
            <input
              v-model.number="retract.params.value.helix_radius"
              type="number"
              step="0.5"
            >
          </div>
          <div
            v-if="retract.params.value.strategy === 'helical'"
            :class="$style['param-row']"
          >
            <label>Pitch (mm/rev):</label>
            <input
              v-model.number="retract.params.value.helix_pitch"
              type="number"
              step="0.1"
            >
          </div>
        </div>

        <button
          :class="$style['export-btn']"
          @click="retract.exportGcode"
        >
          Export Sample G-code
        </button>
      </div>
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

// Initialize all operation composables
const roughing = useRoughingOperation()
const drilling = useDrillingOperation()
const pattern = usePatternOperation()
const contour = useContourOperation()
const probe = useProbeOperation()
const retract = useRetractOperation()
</script>

<style module src="./CAMEssentialsLab.module.css"></style>
