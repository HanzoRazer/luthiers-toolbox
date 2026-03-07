<script setup lang="ts">
/**
 * PurflingDesignerView - Decorative Purfling Channel Designer
 * Designs purfling channels around soundholes and body edges
 *
 * Planned API endpoints:
 *   GET  /api/art-studio/purfling/patterns
 *   POST /api/art-studio/purfling/preview
 *   POST /api/art-studio/purfling/export-dxf
 */
import { ref, computed } from 'vue'

// Form state
const purflingType = ref('body-edge')  // body-edge, soundhole, custom
const channelWidth = ref(2.5)  // mm
const channelDepth = ref(2.0)  // mm
const insetFromEdge = ref(5)  // mm
const cornerRadius = ref(3)  // mm for body edge purfling

// Strip configuration
const stripLayers = ref([
  { type: 'bwb', description: 'Black-White-Black' },
])

const patterns = ref([
  { id: 'simple-line', name: 'Simple Line', description: 'Single purfling channel' },
  { id: 'double-line', name: 'Double Line', description: 'Parallel purfling channels' },
  { id: 'herringbone', name: 'Herringbone', description: 'Classic herringbone pattern' },
  { id: 'rope', name: 'Rope Pattern', description: 'Twisted rope design' },
  { id: 'abalone', name: 'Abalone Strip', description: 'Shell strip channel' },
])

const selectedPattern = ref('simple-line')
const loading = ref(false)
const previewSvg = ref('')

// Methods
function selectPattern(patternId: string) {
  selectedPattern.value = patternId
}

async function generatePreview() {
  loading.value = true
  await new Promise(resolve => setTimeout(resolve, 500))
  loading.value = false
}

async function exportDxf() {
  alert('Export functionality coming soon')
}
</script>

<template>
  <div class="purfling-designer-view">
    <div class="header">
      <h1>Purfling Designer</h1>
      <p class="subtitle">Design decorative purfling channels for body edges and soundholes</p>
    </div>

    <div class="content">
      <!-- Patterns Panel -->
      <div class="panel patterns-panel">
        <h3>Patterns</h3>
        <div class="pattern-list">
          <button
            v-for="pattern in patterns"
            :key="pattern.id"
            class="pattern-btn"
            :class="{ active: selectedPattern === pattern.id }"
            @click="selectPattern(pattern.id)"
          >
            <span class="pattern-name">{{ pattern.name }}</span>
            <span class="pattern-desc">{{ pattern.description }}</span>
          </button>
        </div>
      </div>

      <!-- Parameters Panel -->
      <div class="panel params-panel">
        <h3>Location</h3>
        <div class="form-group">
          <label>Purfling Type</label>
          <select v-model="purflingType">
            <option value="body-edge">Body Edge</option>
            <option value="soundhole">Soundhole Rosette</option>
            <option value="custom">Custom Path</option>
          </select>
        </div>

        <h3>Channel Dimensions</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Width (mm)</label>
            <input type="number" v-model.number="channelWidth" step="0.1" min="0.5" max="10" />
          </div>
          <div class="form-group">
            <label>Depth (mm)</label>
            <input type="number" v-model.number="channelDepth" step="0.1" min="0.5" max="5" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Inset from Edge (mm)</label>
            <input type="number" v-model.number="insetFromEdge" step="0.5" min="0" max="20" />
          </div>
          <div class="form-group" v-if="purflingType === 'body-edge'">
            <label>Corner Radius (mm)</label>
            <input type="number" v-model.number="cornerRadius" step="0.5" min="0" max="20" />
          </div>
        </div>

        <h3>Strip Configuration</h3>
        <div class="strip-preview">
          <div
            v-for="(layer, index) in stripLayers"
            :key="index"
            class="strip-item"
          >
            <span>{{ layer.description }}</span>
          </div>
        </div>
      </div>

      <!-- Preview Panel -->
      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating preview...</div>
          <div v-else-if="previewSvg" v-html="previewSvg" class="svg-preview"></div>
          <div v-else class="placeholder">
            <span class="icon">✨</span>
            <p>Configure parameters and click Generate Preview</p>
          </div>
        </div>
        <div class="action-buttons">
          <button class="btn btn-primary" @click="generatePreview" :disabled="loading">
            Generate Preview
          </button>
          <button class="btn btn-secondary" @click="exportDxf">
            Export DXF
          </button>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>This feature is under development. Full API integration coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.purfling-designer-view {
  min-height: 100vh;
  background: #0a0a0a;
  color: #e5e5e5;
  padding: 2rem;
}

.header {
  max-width: 1400px;
  margin: 0 auto 2rem;
}

.header h1 {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
}

.subtitle {
  color: #888;
  margin: 0;
}

.content {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 250px 1fr 1fr;
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

.panel h3:not(:first-child) {
  margin-top: 1.5rem;
}

.pattern-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pattern-btn {
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

.pattern-btn:hover {
  background: #333;
  border-color: #444;
}

.pattern-btn.active {
  background: #1e3a5f;
  border-color: #60a5fa;
}

.pattern-name {
  font-weight: 500;
  color: #e5e5e5;
}

.pattern-desc {
  font-size: 0.75rem;
  color: #888;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  color: #888;
  margin-bottom: 0.25rem;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.375rem;
  color: #e5e5e5;
  font-size: 0.875rem;
}

.strip-preview {
  background: #262626;
  border-radius: 0.375rem;
  padding: 0.75rem;
}

.strip-item {
  font-size: 0.875rem;
  color: #e5e5e5;
}

.preview-container {
  aspect-ratio: 4/3;
  background: #0d0d0d;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.placeholder {
  text-align: center;
  color: #666;
}

.placeholder .icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.5rem;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
}

.btn {
  flex: 1;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: #2563eb;
  color: #fff;
}

.btn-secondary {
  background: #262626;
  color: #e5e5e5;
  border: 1px solid #333;
}

.coming-soon-notice {
  max-width: 1400px;
  margin: 2rem auto 0;
  padding: 1rem;
  background: #1e3a5f;
  border-radius: 0.5rem;
  text-align: center;
  color: #60a5fa;
}

@media (max-width: 1200px) {
  .content {
    grid-template-columns: 1fr;
  }
}
</style>
