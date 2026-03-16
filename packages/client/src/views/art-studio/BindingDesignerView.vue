<script setup lang="ts">
/**
 * BindingDesignerView - Guitar Body Binding & Purfling Strip Designer
 * @deprecated Prefer SoundholeRosetteShell at /art-studio/soundhole-rosette-workspace (Stage 4).
 *
 * Designs binding channel dimensions and strip stacking patterns
 *
 * Planned API endpoints:
 *   GET  /api/art-studio/binding/presets
 *   GET  /api/art-studio/binding/materials
 *   POST /api/art-studio/binding/preview
 *   POST /api/art-studio/binding/export-dxf
 */
import { ref, computed } from 'vue'

// Form state
const bindingWidth = ref(6.0)  // mm
const bindingDepth = ref(2.0)  // mm
const channelOffset = ref(0.1)  // mm tolerance
const stripLayers = ref([
  { material: 'maple', thickness: 1.5, color: '#f5deb3' },
  { material: 'rosewood', thickness: 0.5, color: '#4a3728' },
  { material: 'maple', thickness: 1.5, color: '#f5deb3' },
])

const presets = ref([
  { name: 'Simple White', description: 'Single white binding strip' },
  { name: 'Black/White/Black', description: 'Classic multi-layer binding' },
  { name: 'Herringbone', description: 'Traditional herringbone pattern' },
  { name: 'Abalone', description: 'Abalone shell strip binding' },
])

const selectedPreset = ref('')
const previewSvg = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

// Computed
const totalStackHeight = computed(() => {
  return stripLayers.value.reduce((sum, layer) => sum + layer.thickness, 0)
})

// Methods
function addLayer() {
  stripLayers.value.push({ material: 'maple', thickness: 0.5, color: '#f5deb3' })
}

function removeLayer(index: number) {
  stripLayers.value.splice(index, 1)
}

function loadPreset(presetName: string) {
  // TODO: Load preset from API
  selectedPreset.value = presetName
}

async function generatePreview() {
  loading.value = true
  error.value = null
  // TODO: Call API
  await new Promise(resolve => setTimeout(resolve, 500))
  loading.value = false
}

async function exportDxf() {
  // TODO: Export DXF via API
  alert('Export functionality coming soon')
}
</script>

<template>
  <div class="binding-designer-view">
    <div class="header">
      <h1>Binding Designer</h1>
      <p class="subtitle">Design binding channels and multi-layer strip patterns</p>
    </div>

    <div class="content">
      <!-- Presets Panel -->
      <div class="panel presets-panel">
        <h3>Presets</h3>
        <div class="preset-list">
          <button
            v-for="preset in presets"
            :key="preset.name"
            class="preset-btn"
            :class="{ active: selectedPreset === preset.name }"
            @click="loadPreset(preset.name)"
          >
            <span class="preset-name">{{ preset.name }}</span>
            <span class="preset-desc">{{ preset.description }}</span>
          </button>
        </div>
      </div>

      <!-- Parameters Panel -->
      <div class="panel params-panel">
        <h3>Channel Dimensions</h3>
        <div class="form-group">
          <label>Binding Width (mm)</label>
          <input type="number" v-model.number="bindingWidth" step="0.5" min="1" max="20" />
        </div>
        <div class="form-group">
          <label>Channel Depth (mm)</label>
          <input type="number" v-model.number="bindingDepth" step="0.1" min="0.5" max="10" />
        </div>
        <div class="form-group">
          <label>Tolerance Offset (mm)</label>
          <input type="number" v-model.number="channelOffset" step="0.05" min="0" max="1" />
        </div>

        <h3>Strip Stack</h3>
        <div class="stack-preview">
          <div
            v-for="(layer, index) in stripLayers"
            :key="index"
            class="strip-layer"
            :style="{
              backgroundColor: layer.color,
              height: `${layer.thickness * 10}px`
            }"
          >
            <span class="layer-label">{{ layer.material }} ({{ layer.thickness }}mm)</span>
            <button class="remove-btn" @click="removeLayer(index)">&times;</button>
          </div>
        </div>
        <p class="stack-total">Total: {{ totalStackHeight.toFixed(1) }}mm</p>
        <button class="add-layer-btn" @click="addLayer">+ Add Layer</button>
      </div>

      <!-- Preview Panel -->
      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating preview...</div>
          <div v-else-if="error" class="error">{{ error }}</div>
          <div v-else-if="previewSvg" v-html="previewSvg" class="svg-preview"></div>
          <div v-else class="placeholder">
            <span class="icon">🎸</span>
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
.binding-designer-view {
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

.preset-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preset-btn {
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

.preset-btn:hover {
  background: #333;
  border-color: #444;
}

.preset-btn.active {
  background: #1e3a5f;
  border-color: #60a5fa;
}

.preset-name {
  font-weight: 500;
  color: #e5e5e5;
}

.preset-desc {
  font-size: 0.75rem;
  color: #888;
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

.form-group input {
  width: 100%;
  padding: 0.5rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.375rem;
  color: #e5e5e5;
  font-size: 0.875rem;
}

.stack-preview {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: #333;
  padding: 1px;
  border-radius: 0.375rem;
  margin-bottom: 0.5rem;
}

.strip-layer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0.5rem;
  min-height: 20px;
  font-size: 0.75rem;
  color: #333;
}

.remove-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 1rem;
}

.stack-total {
  font-size: 0.875rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.add-layer-btn {
  width: 100%;
  padding: 0.5rem;
  background: #262626;
  border: 1px dashed #444;
  border-radius: 0.375rem;
  color: #888;
  cursor: pointer;
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
