<template>
  <div class="cam-essentials-lab">
    <h1>CAM Essentials Lab</h1>
    <p class="subtitle">
      N10 Essential CAM operations for CNC guitar lutherie
    </p>

    <div class="operations-grid">
      <!-- Roughing Operation -->
      <div class="operation-card">
        <div class="card-header">
          <h2>🪓 Roughing</h2>
          <span class="badge">N10</span>
        </div>
        <p>Simple rectangular roughing for pocket clearing</p>
        
        <div class="params">
          <div class="param-row">
            <label>Width (mm):</label>
            <input
              v-model.number="roughing.width"
              type="number"
              step="0.1"
            >
          </div>
          <div class="param-row">
            <label>Height (mm):</label>
            <input
              v-model.number="roughing.height"
              type="number"
              step="0.1"
            >
          </div>
          <div class="param-row">
            <label>Stepdown (mm):</label>
            <input
              v-model.number="roughing.stepdown"
              type="number"
              step="0.1"
            >
          </div>
          <div class="param-row">
            <label>Feed (mm/min):</label>
            <input
              v-model.number="roughing.feed"
              type="number"
              step="10"
            >
          </div>
          <div class="param-row">
            <label>Post:</label>
            <select v-model="roughing.post">
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
          class="export-btn"
          @click="exportRoughing"
        >
          Export G-code
        </button>
      </div>

      <!-- Drilling Operation -->
      <div class="operation-card">
        <div class="card-header">
          <h2>🔩 Drilling (G81/G83)</h2>
          <span class="badge">N10</span>
        </div>
        <p>Modal drilling cycles for hole arrays</p>
        
        <div class="params">
          <div class="param-row">
            <label>Cycle:</label>
            <select v-model="drilling.cycle">
              <option value="G81">
                G81 (Simple)
              </option>
              <option value="G83">
                G83 (Peck)
              </option>
            </select>
          </div>
          <div class="param-row">
            <label>Depth (mm):</label>
            <input
              v-model.number="drilling.depth"
              type="number"
              step="0.1"
            >
          </div>
          <div class="param-row">
            <label>Feed (mm/min):</label>
            <input
              v-model.number="drilling.feed"
              type="number"
              step="10"
            >
          </div>
          <div
            v-if="drilling.cycle === 'G83'"
            class="param-row"
          >
            <label>Peck Depth (mm):</label>
            <input
              v-model.number="drilling.peck_q"
              type="number"
              step="0.1"
            >
          </div>
          <div class="param-row">
            <label>Holes (JSON):</label>
            <textarea
              v-model="drilling.holesJson"
              rows="3"
              placeholder="[{&quot;x&quot;:10,&quot;y&quot;:10},{&quot;x&quot;:20,&quot;y&quot;:10}]"
            />
          </div>
        </div>
        
        <button
          class="export-btn"
          @click="exportDrilling"
        >
          Export G-code
        </button>
      </div>

      <!-- Drill Pattern Operation -->
      <div class="operation-card">
        <div class="card-header">
          <h2>📐 Drill Patterns</h2>
          <span class="badge">N10</span>
        </div>
        <p>Generate drilling patterns (grid, circle, line)</p>
        
        <div class="params">
          <div class="param-row">
            <label>Pattern:</label>
            <select v-model="pattern.type">
              <option value="grid">
                Grid
              </option>
              <option value="circle">
                Circle
              </option>
              <option value="line">
                Line
              </option>
            </select>
          </div>
          
          <!-- Grid Pattern -->
          <template v-if="pattern.type === 'grid'">
            <div class="param-row">
              <label>Rows:</label>
              <input
                v-model.number="pattern.grid.rows"
                type="number"
                min="1"
              >
            </div>
            <div class="param-row">
              <label>Columns:</label>
              <input
                v-model.number="pattern.grid.cols"
                type="number"
                min="1"
              >
            </div>
            <div class="param-row">
              <label>X Spacing (mm):</label>
              <input
                v-model.number="pattern.grid.dx"
                type="number"
                step="0.1"
              >
            </div>
            <div class="param-row">
              <label>Y Spacing (mm):</label>
              <input
                v-model.number="pattern.grid.dy"
                type="number"
                step="0.1"
              >
            </div>
          </template>
          
          <!-- Circle Pattern -->
          <template v-if="pattern.type === 'circle'">
            <div class="param-row">
              <label>Count:</label>
              <input
                v-model.number="pattern.circle.count"
                type="number"
                min="1"
              >
            </div>
            <div class="param-row">
              <label>Radius (mm):</label>
              <input
                v-model.number="pattern.circle.radius"
                type="number"
                step="0.1"
              >
            </div>
            <div class="param-row">
              <label>Start Angle (°):</label>
              <input
                v-model.number="pattern.circle.start_angle_deg"
                type="number"
                step="1"
              >
            </div>
          </template>
          
          <!-- Line Pattern -->
          <template v-if="pattern.type === 'line'">
            <div class="param-row">
              <label>Count:</label>
              <input
                v-model.number="pattern.line.count"
                type="number"
                min="1"
              >
            </div>
            <div class="param-row">
              <label>X Increment (mm):</label>
              <input
                v-model.number="pattern.line.dx"
                type="number"
                step="0.1"
              >
            </div>
            <div class="param-row">
              <label>Y Increment (mm):</label>
              <input
                v-model.number="pattern.line.dy"
                type="number"
                step="0.1"
              >
            </div>
          </template>
          
          <div class="param-row">
            <label>Depth (mm):</label>
            <input
              v-model.number="pattern.depth"
              type="number"
              step="0.1"
            >
          </div>
          <div class="param-row">
            <label>Feed (mm/min):</label>
            <input
              v-model.number="pattern.feed"
              type="number"
              step="10"
            >
          </div>
        </div>
        
        <button
          class="export-btn"
          @click="exportPattern"
        >
          Export G-code
        </button>
      </div>

      <!-- Bi-Arc Contour -->
      <div class="operation-card">
        <div class="card-header">
          <h2>🔺 Contour Following</h2>
          <span class="badge">N10</span>
        </div>
        <p>Linear contour following from point array</p>
        
        <div class="params">
          <div class="param-row">
            <label>Points (JSON):</label>
            <textarea
              v-model="biarc.pathJson"
              rows="4"
              placeholder="[{&quot;x&quot;:0,&quot;y&quot;:0},{&quot;x&quot;:50,&quot;y&quot;:0},{&quot;x&quot;:50,&quot;y&quot;:30}]"
            />
          </div>
          <div class="param-row">
            <label>Depth (mm):</label>
            <input
              v-model.number="biarc.depth"
              type="number"
              step="0.1"
            >
          </div>
          <div class="param-row">
            <label>Feed (mm/min):</label>
            <input
              v-model.number="biarc.feed"
              type="number"
              step="10"
            >
          </div>
        </div>
        
        <button
          class="export-btn"
          @click="exportBiarc"
        >
          Export G-code
        </button>
      </div>

      <!-- Probe Patterns (N09) -->
      <div class="operation-card">
        <div class="card-header">
          <h2>🎯 Probe Patterns</h2>
          <span class="badge">N09</span>
        </div>
        <p>Work offset establishment with touch probes</p>
        
        <div class="params">
          <div class="param-row">
            <label>Pattern:</label>
            <select v-model="probe.pattern">
              <option value="corner_outside">
                Corner (Outside)
              </option>
              <option value="corner_inside">
                Corner (Inside)
              </option>
              <option value="boss_circular">
                Boss (Circular)
              </option>
              <option value="hole_circular">
                Hole (Circular)
              </option>
              <option value="surface_z">
                Surface Z
              </option>
            </select>
          </div>
          <div class="param-row">
            <label>Probe Feed (mm/min):</label>
            <input
              v-model.number="probe.feed_probe"
              type="number"
              step="10"
            >
          </div>
          <div class="param-row">
            <label>Safe Z (mm):</label>
            <input
              v-model.number="probe.safe_z"
              type="number"
              step="0.5"
            >
          </div>
          <div
            v-if="probe.pattern.includes('circular')"
            class="param-row"
          >
            <label>Est. Diameter (mm):</label>
            <input
              v-model.number="probe.diameter"
              type="number"
              step="1"
            >
          </div>
          <div class="param-row">
            <label>Work Offset:</label>
            <select v-model="probe.work_offset">
              <option value="1">
                G54 (1)
              </option>
              <option value="2">
                G55 (2)
              </option>
              <option value="3">
                G56 (3)
              </option>
              <option value="4">
                G57 (4)
              </option>
              <option value="5">
                G58 (5)
              </option>
              <option value="6">
                G59 (6)
              </option>
            </select>
          </div>
        </div>
        
        <div class="button-group">
          <button
            class="export-btn half"
            @click="exportProbeGcode"
          >
            Export G-code
          </button>
          <button
            class="export-btn half secondary"
            @click="exportProbeSVG"
          >
            Export Setup Sheet
          </button>
        </div>
      </div>

      <!-- Retract Patterns (N08) -->
      <div class="operation-card">
        <div class="card-header">
          <h2>↑ Retract Patterns</h2>
          <span class="badge">N08</span>
        </div>
        <p>Safe retract strategies for tool changes</p>
        
        <div class="params">
          <div class="param-row">
            <label>Strategy:</label>
            <select v-model="retract.strategy">
              <option value="direct">
                Direct (G0)
              </option>
              <option value="ramped">
                Ramped (Linear)
              </option>
              <option value="helical">
                Helical (Spiral)
              </option>
            </select>
          </div>
          <div class="param-row">
            <label>Current Z (mm):</label>
            <input
              v-model.number="retract.current_z"
              type="number"
              step="0.1"
            >
          </div>
          <div class="param-row">
            <label>Safe Z (mm):</label>
            <input
              v-model.number="retract.safe_z"
              type="number"
              step="0.5"
            >
          </div>
          <div
            v-if="retract.strategy === 'ramped'"
            class="param-row"
          >
            <label>Ramp Feed (mm/min):</label>
            <input
              v-model.number="retract.ramp_feed"
              type="number"
              step="10"
            >
          </div>
          <div
            v-if="retract.strategy === 'helical'"
            class="param-row"
          >
            <label>Helix Radius (mm):</label>
            <input
              v-model.number="retract.helix_radius"
              type="number"
              step="0.5"
            >
          </div>
          <div
            v-if="retract.strategy === 'helical'"
            class="param-row"
          >
            <label>Pitch (mm/rev):</label>
            <input
              v-model.number="retract.helix_pitch"
              type="number"
              step="0.1"
            >
          </div>
        </div>
        
        <button
          class="export-btn"
          @click="exportRetractGcode"
        >
          Export Sample G-code
        </button>
      </div>
    </div>

    <!-- Info Section -->
    <div class="info-section">
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
import { ref } from 'vue'

// Roughing Parameters
const roughing = ref({
  width: 100.0,
  height: 60.0,
  stepdown: 3.0,
  stepover: 2.5,
  feed: 1200.0,
  post: 'GRBL'
})

// Drilling Parameters
const drilling = ref({
  cycle: 'G81',
  depth: -10.0,
  feed: 300.0,
  peck_q: 2.0,
  holesJson: '[{"x":10,"y":10,"z":-10,"feed":300},{"x":30,"y":10,"z":-10,"feed":300}]'
})

// Pattern Parameters
const pattern = ref({
  type: 'grid',
  grid: { rows: 3, cols: 4, dx: 10.0, dy: 10.0 },
  circle: { count: 6, radius: 20.0, start_angle_deg: 0.0 },
  line: { count: 5, dx: 5.0, dy: 0.0 },
  depth: -10.0,
  feed: 300.0
})

// Bi-Arc Parameters
const biarc = ref({
  pathJson: '[{"x":0,"y":0},{"x":50,"y":0},{"x":50,"y":30},{"x":0,"y":30}]',
  depth: -3.0,
  feed: 1200.0
})

// Probe Parameters (N09)
const probe = ref({
  pattern: 'corner_outside',
  feed_probe: 100.0,
  safe_z: 10.0,
  diameter: 50.0,
  work_offset: 1
})

// Retract Parameters (N08)
const retract = ref({
  strategy: 'direct',
  current_z: -10.0,
  safe_z: 5.0,
  ramp_feed: 600.0,
  helix_radius: 5.0,
  helix_pitch: 1.0
})

// Export Functions
async function exportRoughing() {
  try {
    const response = await fetch('/api/cam/toolpath/roughing/gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(roughing.value)
    })
    
    const gcode = await response.text()
    downloadFile(gcode, `roughing_${roughing.value.post}.nc`)
  } catch (err) {
    console.error('Roughing export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

async function exportDrilling() {
  try {
    const holes = JSON.parse(drilling.value.holesJson)
    const body = {
      holes,
      cycle: drilling.value.cycle,
      peck_q: drilling.value.cycle === 'G83' ? drilling.value.peck_q : undefined,
      post: 'GRBL'
    }
    
    const response = await fetch('/api/cam/drilling/gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    const gcode = await response.text()
    downloadFile(gcode, `drilling_${drilling.value.cycle}.nc`)
  } catch (err) {
    console.error('Drilling export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

async function exportPattern() {
  try {
    const patternSpec: any = {
      type: pattern.value.type,
      origin_x: 0.0,
      origin_y: 0.0
    }
    
    if (pattern.value.type === 'grid') {
      patternSpec.grid = pattern.value.grid
    } else if (pattern.value.type === 'circle') {
      patternSpec.circle = pattern.value.circle
    } else if (pattern.value.type === 'line') {
      patternSpec.line = pattern.value.line
    }
    
    const drillParams = {
      z: pattern.value.depth,
      feed: pattern.value.feed,
      cycle: 'G81',
      post: 'GRBL'
    }
    
    const url = `/api/cam/drilling/pattern/gcode?${new URLSearchParams(drillParams as any).toString()}`
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patternSpec)
    })
    
    const gcode = await response.text()
    downloadFile(gcode, `pattern_${pattern.value.type}.nc`)
  } catch (err) {
    console.error('Pattern export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

async function exportBiarc() {
  try {
    const path = JSON.parse(biarc.value.pathJson)
    const body = {
      path,
      z: biarc.value.depth,
      feed: biarc.value.feed,
      post: 'GRBL'
    }
    
    const response = await fetch('/api/cam/toolpath/biarc/gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    const gcode = await response.text()
    downloadFile(gcode, 'contour_biarc.nc')
  } catch (err) {
    console.error('Bi-arc export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

async function exportProbeGcode() {
  try {
    let endpoint = ''
    let body: any = {
      feed_probe: probe.value.feed_probe,
      safe_z: probe.value.safe_z,
      work_offset: probe.value.work_offset,
      approach_distance: 10.0,
      retract_distance: 2.0
    }
    
    if (probe.value.pattern.includes('corner')) {
      endpoint = '/api/cam/probe/corner'
      body.pattern = probe.value.pattern
    } else if (probe.value.pattern.includes('circular')) {
      endpoint = '/api/cam/probe/boss'
      body.pattern = probe.value.pattern
      body.estimated_diameter = probe.value.diameter
      body.estimated_center_x = 0.0
      body.estimated_center_y = 0.0
      body.probe_count = 4
    } else if (probe.value.pattern === 'surface_z') {
      endpoint = '/api/cam/probe/surface_z'
      body.z_clearance = probe.value.safe_z
    }
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    const data = await response.json()
    downloadFile(data.gcode, `probe_${probe.value.pattern}.nc`)
  } catch (err) {
    console.error('Probe export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

async function exportProbeSVG() {
  try {
    const body = {
      pattern: probe.value.pattern,
      estimated_diameter: probe.value.diameter
    }
    
    const response = await fetch('/api/cam/probe/svg_setup_sheet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    const svg = await response.text()
    downloadFile(svg, `probe_setup_${probe.value.pattern}.svg`)
  } catch (err) {
    console.error('Probe SVG export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

async function exportRetractGcode() {
  try {
    const body = {
      strategy: retract.value.strategy,
      current_z: retract.value.current_z,
      safe_z: retract.value.safe_z,
      ramp_feed: retract.value.ramp_feed,
      helix_radius: retract.value.helix_radius,
      helix_pitch: retract.value.helix_pitch
    }
    
    const response = await fetch('/api/cam/retract/gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    const gcode = await response.text()
    downloadFile(gcode, `retract_${retract.value.strategy}.nc`)
  } catch (err) {
    console.error('Retract export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

function downloadFile(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.cam-essentials-lab {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  color: #2c3e50;
  margin-bottom: 5px;
}

.subtitle {
  color: #7f8c8d;
  margin-bottom: 30px;
}

.operations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.operation-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-header h2 {
  margin: 0;
  font-size: 1.3em;
  color: #2c3e50;
}

.badge {
  background: #3498db;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75em;
  font-weight: bold;
}

.params {
  margin: 15px 0;
}

.param-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.param-row label {
  font-weight: 500;
  color: #555;
  min-width: 120px;
}

.param-row input,
.param-row select,
.param-row textarea {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9em;
}

.param-row textarea {
  font-family: monospace;
  resize: vertical;
}

.export-btn {
  width: 100%;
  padding: 10px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1em;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.export-btn:hover {
  background: #229954;
}

.export-btn.secondary {
  background: #3498db;
}

.export-btn.secondary:hover {
  background: #2980b9;
}

.button-group {
  display: flex;
  gap: 10px;
}

.export-btn.half {
  width: calc(50% - 5px);
}

.info-section {
  background: #f8f9fa;
  border-left: 4px solid #3498db;
  padding: 20px;
  border-radius: 4px;
}

.info-section h3 {
  margin-top: 0;
  color: #2c3e50;
}

.info-section p {
  line-height: 1.6;
  color: #555;
}
</style>
