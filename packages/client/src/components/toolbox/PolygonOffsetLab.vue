<template>
  <div class="polygon-offset-lab">
    <h2>Polygon Offset (N17)</h2>
    <p class="subtitle">Robust polygon offsetting with pyclipper • Arc linkers (G2/G3) • Feed management</p>

    <div class="lab-grid">
      <!-- Left: Parameters -->
      <div class="params-panel">
        <h3>Parameters</h3>

        <div class="param-group">
          <h4>Geometry</h4>
          <label>
            Polygon (test square):
            <textarea v-model="polygonStr" rows="4" placeholder="[[0,0], [100,0], [100,60], [0,60]]"></textarea>
          </label>
        </div>

        <div class="param-group">
          <h4>Tool</h4>
          <label>
            Tool Diameter (mm):
            <input type="number" v-model.number="toolDia" step="0.5" min="1" />
          </label>
          <label>
            Stepover (mm):
            <input type="number" v-model.number="stepover" step="0.1" min="0.1" />
          </label>
          <label>
            <input type="checkbox" v-model="inward" /> Inward (pocketing)
          </label>
        </div>

        <div class="param-group">
          <h4>Offset Settings</h4>
          <label>
            Join Type:
            <select v-model="joinType">
              <option value="miter">Miter</option>
              <option value="round">Round</option>
              <option value="bevel">Bevel</option>
            </select>
          </label>
          <label>
            Arc Tolerance (mm):
            <input type="number" v-model.number="arcTolerance" step="0.05" min="0.05" />
          </label>
        </div>

        <div class="param-group">
          <h4>Linking</h4>
          <label>
            Link Mode:
            <select v-model="linkMode">
              <option value="arc">Arc (G2/G3)</option>
              <option value="line">Linear (G1)</option>
            </select>
          </label>
          <label v-if="linkMode === 'arc'">
            Link Radius (mm):
            <input type="number" v-model.number="linkRadius" step="0.1" min="0.1" />
          </label>
        </div>

        <div class="param-group">
          <h4>Feeds & Speeds</h4>
          <label>
            Feed (mm/min):
            <input type="number" v-model.number="feed" step="100" min="100" />
          </label>
          <label v-if="linkMode === 'arc'">
            Arc Feed (mm/min, optional):
            <input type="number" v-model.number="feedArc" step="100" min="0" />
          </label>
          <label v-if="linkMode === 'arc'">
            Feed Floor (mm/min, optional):
            <input type="number" v-model.number="feedFloor" step="50" min="0" />
          </label>
          <label v-if="linkMode === 'line'">
            Spindle RPM:
            <input type="number" v-model.number="spindle" step="1000" min="1000" />
          </label>
        </div>

        <div class="param-group">
          <h4>Depth</h4>
          <label>
            Z Depth (mm):
            <input type="number" v-model.number="z" step="0.5" />
          </label>
          <label>
            Safe Z (mm):
            <input type="number" v-model.number="safeZ" step="1" min="0" />
          </label>
        </div>

        <button @click="generate" :disabled="loading" class="btn-primary">
          {{ loading ? 'Generating...' : 'Generate G-code' }}
        </button>
      </div>

      <!-- Right: Output -->
      <div class="output-panel">
        <h3>G-code Preview</h3>
        
        <div v-if="error" class="error-banner">
          <strong>⚠️ Error:</strong> {{ error }}
        </div>

        <div v-if="gcode" class="gcode-preview">
          <pre>{{ gcodePreview }}</pre>
        </div>

        <div v-if="gcode" class="actions">
          <button @click="download" class="btn-secondary">Download</button>
          <button @click="copy" class="btn-secondary">Copy</button>
        </div>

        <div v-if="stats" class="stats">
          <h4>Statistics</h4>
          <div><b>Passes:</b> {{ stats.passes }}</div>
          <div><b>Total Lines:</b> {{ stats.lines }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Parameters
const polygonStr = ref('[[0,0], [100,0], [100,60], [0,60]]')
const toolDia = ref(6.0)
const stepover = ref(2.0)
const inward = ref(true)
const joinType = ref('round')
const arcTolerance = ref(0.25)
const linkMode = ref('arc')
const linkRadius = ref(1.0)
const feed = ref(600)
const feedArc = ref(0)
const feedFloor = ref(0)
const spindle = ref(12000)
const z = ref(-1.5)
const safeZ = ref(5.0)

// State
const loading = ref(false)
const error = ref('')
const gcode = ref('')
const stats = ref<{ passes: number; lines: number } | null>(null)

// Computed
const gcodePreview = computed(() => {
  if (!gcode.value) return ''
  const lines = gcode.value.split('\n')
  if (lines.length <= 50) return gcode.value
  return lines.slice(0, 50).join('\n') + '\n... (' + (lines.length - 50) + ' more lines)'
})

// Generate G-code
async function generate() {
  loading.value = true
  error.value = ''
  gcode.value = ''
  stats.value = null

  try {
    // Parse polygon
    let polygon: [number, number][]
    try {
      polygon = JSON.parse(polygonStr.value)
      if (!Array.isArray(polygon) || polygon.length < 3) {
        throw new Error('Polygon must have at least 3 points')
      }
    } catch (e) {
      throw new Error('Invalid polygon JSON: ' + (e as Error).message)
    }

    // Build request
    const req: any = {
      polygon,
      tool_dia: toolDia.value,
      stepover: stepover.value,
      inward: inward.value,
      z: z.value,
      safe_z: safeZ.value,
      units: 'mm',
      feed: feed.value,
      join_type: joinType.value,
      arc_tolerance: arcTolerance.value,
      link_mode: linkMode.value
    }

    if (linkMode.value === 'arc') {
      if (feedArc.value > 0) req.feed_arc = feedArc.value
      if (feedFloor.value > 0) req.feed_floor = feedFloor.value
      req.link_radius = linkRadius.value
    } else {
      req.spindle = spindle.value
    }

    // Call API
    const response = await fetch('/api/cam/polygon_offset.nc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    const result = await response.text()
    gcode.value = result

    // Calculate stats
    const lines = result.split('\n').filter(l => l.trim() && !l.startsWith('('))
    const passes = result.split('G0 Z').length - 1
    stats.value = { passes, lines: lines.length }

  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

// Download G-code
function download() {
  const blob = new Blob([gcode.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `polygon_offset_${linkMode.value}.nc`
  a.click()
  URL.revokeObjectURL(url)
}

// Copy G-code
async function copy() {
  try {
    await navigator.clipboard.writeText(gcode.value)
    alert('G-code copied to clipboard!')
  } catch (e) {
    alert('Failed to copy: ' + (e as Error).message)
  }
}
</script>

<style scoped>
.polygon-offset-lab {
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.subtitle {
  color: #666;
  margin-bottom: 1.5rem;
}

.lab-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 2rem;
}

.params-panel, .output-panel {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.param-group {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.param-group:last-child {
  border-bottom: none;
}

h3 {
  margin-top: 0;
  color: #333;
  font-size: 1.2rem;
}

h4 {
  margin: 0 0 0.5rem 0;
  color: #555;
  font-size: 0.95rem;
  font-weight: 600;
}

label {
  display: block;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  color: #555;
}

input[type="number"],
input[type="text"],
textarea,
select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

textarea {
  font-family: monospace;
  resize: vertical;
}

input[type="checkbox"] {
  width: auto;
  margin-right: 0.5rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.gcode-preview {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  max-height: 500px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.gcode-preview pre {
  margin: 0;
  white-space: pre-wrap;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: #64748b;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #475569;
}

.stats {
  background: #f1f5f9;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #cbd5e1;
}

.stats h4 {
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.stats div {
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

@media (max-width: 1024px) {
  .lab-grid {
    grid-template-columns: 1fr;
  }
}
</style>
