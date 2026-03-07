<script setup lang="ts">
/**
 * PocketClearingView - Pocket Clearing Toolpath Generator
 * Generate adaptive/spiral/zigzag pocket clearing toolpaths
 *
 * Connected to API endpoints:
 *   POST /api/cam/pocket/preview
 *   POST /api/cam/pocket/generate
 *   GET  /api/cam/pocket/strategies
 */
import { ref, computed } from 'vue'

// Strategy options
const strategies = ref([
  { id: 'adaptive', name: 'Adaptive Clearing', description: 'Optimal load, minimal wear' },
  { id: 'spiral', name: 'Spiral', description: 'Inside-out spiral pattern' },
  { id: 'zigzag', name: 'Zigzag', description: 'Parallel passes' },
  { id: 'offset', name: 'Offset', description: 'Contour offset pattern' },
])

const selectedStrategy = ref('adaptive')
const toolDiameter = ref(6.0)  // mm
const stepover = ref(40)  // % of tool diameter
const stepdown = ref(3.0)  // mm
const feedRate = ref(1500)  // mm/min
const plungeRate = ref(500)  // mm/min
const spindleSpeed = ref(18000)  // rpm
const safeHeight = ref(5)  // mm
const pocketDepth = ref(10)  // mm

const dxfFile = ref<File | null>(null)
const loading = ref(false)
const previewGcode = ref('')
const estimatedTime = ref<number | null>(null)

// Computed
const effectiveStepover = computed(() => (stepover.value / 100) * toolDiameter.value)

// Methods
function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    dxfFile.value = input.files[0]
  }
}

async function generatePreview() {
  if (!dxfFile.value) return
  loading.value = true
  // TODO: Call API
  await new Promise(resolve => setTimeout(resolve, 1000))
  estimatedTime.value = 12.5  // mock
  loading.value = false
}

async function downloadGcode() {
  alert('G-code download coming soon')
}
</script>

<template>
  <div class="pocket-clearing-view">
    <div class="header">
      <h1>Pocket Clearing</h1>
      <p class="subtitle">Generate optimized pocket clearing toolpaths</p>
    </div>

    <div class="content">
      <!-- File Upload Panel -->
      <div class="panel upload-panel">
        <h3>Input Geometry</h3>
        <div class="upload-zone" @click="($refs.fileInput as HTMLInputElement).click()">
          <input
            type="file"
            ref="fileInput"
            accept=".dxf,.svg"
            @change="handleFileUpload"
            hidden
          />
          <span class="upload-icon">📁</span>
          <p v-if="dxfFile">{{ dxfFile.name }}</p>
          <p v-else>Click to upload DXF or SVG</p>
        </div>

        <h3>Strategy</h3>
        <div class="strategy-list">
          <button
            v-for="strategy in strategies"
            :key="strategy.id"
            class="strategy-btn"
            :class="{ active: selectedStrategy === strategy.id }"
            @click="selectedStrategy = strategy.id"
          >
            <span class="strategy-name">{{ strategy.name }}</span>
            <span class="strategy-desc">{{ strategy.description }}</span>
          </button>
        </div>
      </div>

      <!-- Parameters Panel -->
      <div class="panel params-panel">
        <h3>Tool Parameters</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Tool Diameter (mm)</label>
            <input type="number" v-model.number="toolDiameter" step="0.1" min="0.5" max="25" />
          </div>
          <div class="form-group">
            <label>Stepover (%)</label>
            <input type="number" v-model.number="stepover" step="5" min="10" max="90" />
            <span class="hint">{{ effectiveStepover.toFixed(2) }}mm</span>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Stepdown (mm)</label>
            <input type="number" v-model.number="stepdown" step="0.5" min="0.1" max="20" />
          </div>
          <div class="form-group">
            <label>Pocket Depth (mm)</label>
            <input type="number" v-model.number="pocketDepth" step="0.5" min="0.5" max="50" />
          </div>
        </div>

        <h3>Feeds & Speeds</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Feed Rate (mm/min)</label>
            <input type="number" v-model.number="feedRate" step="100" min="100" max="5000" />
          </div>
          <div class="form-group">
            <label>Plunge Rate (mm/min)</label>
            <input type="number" v-model.number="plungeRate" step="50" min="50" max="2000" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Spindle Speed (RPM)</label>
            <input type="number" v-model.number="spindleSpeed" step="1000" min="5000" max="30000" />
          </div>
          <div class="form-group">
            <label>Safe Height (mm)</label>
            <input type="number" v-model.number="safeHeight" step="1" min="1" max="25" />
          </div>
        </div>
      </div>

      <!-- Preview Panel -->
      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating toolpath...</div>
          <div v-else class="placeholder">
            <span class="icon">⚙️</span>
            <p>Upload geometry and configure parameters</p>
            <p v-if="estimatedTime" class="estimate">
              Estimated time: {{ estimatedTime.toFixed(1) }} min
            </p>
          </div>
        </div>
        <div class="action-buttons">
          <button
            class="btn btn-primary"
            @click="generatePreview"
            :disabled="!dxfFile || loading"
          >
            Generate Toolpath
          </button>
          <button class="btn btn-secondary" @click="downloadGcode">
            Download G-code
          </button>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full adaptive clearing with RMOS feasibility checking coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.pocket-clearing-view {
  min-height: 100vh;
  background: #0a0a0a;
  color: #e5e5e5;
  padding: 2rem;
}

.header {
  max-width: 1400px;
  margin: 0 auto 2rem;
}

.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 280px 1fr 1fr;
  gap: 1.5rem;
}

.panel {
  background: #1a1a1a;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.panel h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 1rem;
}

.panel h3:not(:first-child) { margin-top: 1.5rem; }

.upload-zone {
  border: 2px dashed #333;
  border-radius: 0.5rem;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
}

.upload-zone:hover { border-color: #60a5fa; background: #1a1a1a; }
.upload-icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }

.strategy-list { display: flex; flex-direction: column; gap: 0.5rem; }

.strategy-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0.75rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.5rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}

.strategy-btn:hover { background: #333; border-color: #444; }
.strategy-btn.active { background: #1e3a5f; border-color: #60a5fa; }
.strategy-name { font-weight: 500; color: #e5e5e5; }
.strategy-desc { font-size: 0.75rem; color: #888; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.form-group input {
  width: 100%;
  padding: 0.5rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.375rem;
  color: #e5e5e5;
  font-size: 0.875rem;
}
.hint { font-size: 0.75rem; color: #60a5fa; }

.preview-container {
  aspect-ratio: 4/3;
  background: #0d0d0d;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.placeholder { text-align: center; color: #666; }
.placeholder .icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }
.estimate { font-size: 0.875rem; color: #60a5fa; margin-top: 0.5rem; }

.action-buttons { display: flex; gap: 0.75rem; }
.btn { flex: 1; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; cursor: not-allowed; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }

.coming-soon-notice {
  max-width: 1400px;
  margin: 2rem auto 0;
  padding: 1rem;
  background: #1e3a5f;
  border-radius: 0.5rem;
  text-align: center;
  color: #60a5fa;
}

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
