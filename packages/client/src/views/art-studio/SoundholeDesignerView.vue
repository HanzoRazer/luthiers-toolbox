<script setup lang="ts">
/**
 * SoundholeDesignerView - Acoustic Guitar Soundhole Designer
 * @deprecated Prefer SoundholeRosetteShell at /art-studio/soundhole-rosette-workspace (Stage 2).
 *
 * Design soundhole shapes, rosettes, and decorative rings
 *
 * Planned API endpoints:
 *   GET  /api/art-studio/soundhole/templates
 *   GET  /api/art-studio/soundhole/rosette-patterns
 *   POST /api/art-studio/soundhole/preview
 *   POST /api/art-studio/soundhole/export-dxf
 */
import { ref, computed } from 'vue'

// Form state
const soundholeType = ref('round')  // round, oval, f-hole, d-hole
const diameter = ref(100)  // mm for round holes
const ovalWidth = ref(120)  // mm
const ovalHeight = ref(80)  // mm
const centerX = ref(0)  // offset from centerline
const centerY = ref(0)  // offset from bridge

// Rosette options
const includeRosette = ref(true)
const rosetteStyle = ref('concentric')
const rosetteWidth = ref(12)  // mm
const rosetteRings = ref(3)

const templates = ref([
  { id: 'classical-round', name: 'Classical Round', type: 'round', diameter: 85 },
  { id: 'dreadnought', name: 'Dreadnought', type: 'round', diameter: 100 },
  { id: 'parlor-oval', name: 'Parlor Oval', type: 'oval' },
  { id: 'archtop-f', name: 'Archtop F-Hole', type: 'f-hole' },
  { id: 'd-hole', name: 'D-Hole (Maccaferri)', type: 'd-hole' },
])

const rosettePatterns = ref([
  { id: 'concentric', name: 'Concentric Rings' },
  { id: 'herringbone', name: 'Herringbone' },
  { id: 'mosaic', name: 'Mosaic Pattern' },
  { id: 'abalone', name: 'Abalone Inlay' },
  { id: 'marquetry', name: 'Wood Marquetry' },
])

const selectedTemplate = ref('')
const loading = ref(false)
const previewSvg = ref('')

// Methods
function selectTemplate(templateId: string) {
  selectedTemplate.value = templateId
  const template = templates.value.find(t => t.id === templateId)
  if (template) {
    soundholeType.value = template.type
    if (template.diameter) diameter.value = template.diameter
  }
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
  <div class="soundhole-designer-view">
    <div class="header">
      <h1>Soundhole Designer</h1>
      <p class="subtitle">Design soundhole shapes and decorative rosettes</p>
    </div>

    <div class="content">
      <!-- Templates Panel -->
      <div class="panel templates-panel">
        <h3>Templates</h3>
        <div class="template-list">
          <button
            v-for="template in templates"
            :key="template.id"
            class="template-btn"
            :class="{ active: selectedTemplate === template.id }"
            @click="selectTemplate(template.id)"
          >
            <span class="template-icon">
              {{ template.type === 'f-hole' ? '𝑓' : '○' }}
            </span>
            <span class="template-name">{{ template.name }}</span>
          </button>
        </div>
      </div>

      <!-- Parameters Panel -->
      <div class="panel params-panel">
        <h3>Soundhole Shape</h3>
        <div class="form-group">
          <label>Type</label>
          <select v-model="soundholeType">
            <option value="round">Round</option>
            <option value="oval">Oval</option>
            <option value="f-hole">F-Hole</option>
            <option value="d-hole">D-Hole</option>
          </select>
        </div>

        <div v-if="soundholeType === 'round'" class="form-group">
          <label>Diameter (mm)</label>
          <input type="number" v-model.number="diameter" step="1" min="50" max="150" />
        </div>

        <div v-if="soundholeType === 'oval'" class="form-row">
          <div class="form-group">
            <label>Width (mm)</label>
            <input type="number" v-model.number="ovalWidth" step="1" min="60" max="180" />
          </div>
          <div class="form-group">
            <label>Height (mm)</label>
            <input type="number" v-model.number="ovalHeight" step="1" min="40" max="120" />
          </div>
        </div>

        <h3>Rosette</h3>
        <div class="form-group checkbox-group">
          <label>
            <input type="checkbox" v-model="includeRosette" />
            Include decorative rosette
          </label>
        </div>

        <div v-if="includeRosette">
          <div class="form-group">
            <label>Style</label>
            <select v-model="rosetteStyle">
              <option v-for="pattern in rosettePatterns" :key="pattern.id" :value="pattern.id">
                {{ pattern.name }}
              </option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Width (mm)</label>
              <input type="number" v-model.number="rosetteWidth" step="1" min="5" max="30" />
            </div>
            <div class="form-group">
              <label>Rings</label>
              <input type="number" v-model.number="rosetteRings" step="1" min="1" max="10" />
            </div>
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
            <span class="icon">🎵</span>
            <p>Select a template or configure dimensions</p>
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
.soundhole-designer-view {
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

.template-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.template-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.5rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}

.template-btn:hover {
  background: #333;
  border-color: #444;
}

.template-btn.active {
  background: #1e3a5f;
  border-color: #60a5fa;
}

.template-icon {
  font-size: 1.5rem;
  width: 2rem;
  text-align: center;
}

.template-name {
  font-weight: 500;
  color: #e5e5e5;
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

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.preview-container {
  aspect-ratio: 1;
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
