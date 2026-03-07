<script setup lang="ts">
/**
 * HeadstockDesignerView - Guitar Headstock Shape & Overlay Designer
 * Design headstock outlines, tuner holes, and decorative overlays
 *
 * Planned API endpoints:
 *   GET  /api/art-studio/headstock/templates
 *   GET  /api/art-studio/headstock/tuner-layouts
 *   POST /api/art-studio/headstock/preview
 *   POST /api/art-studio/headstock/export-dxf
 */
import { ref, computed } from 'vue'

// Headstock types
const headstockStyle = ref('3x3')  // 3x3, 6-inline, 4x2
const headstockLength = ref(180)  // mm
const headstockWidth = ref(90)  // mm
const tunerHoleDiameter = ref(10)  // mm
const tunerSpacing = ref(35)  // mm
const stringSpacing = ref(7.5)  // mm at nut

const templates = ref([
  { id: 'fender-strat', name: 'Stratocaster Style', style: '6-inline' },
  { id: 'gibson-les-paul', name: 'Les Paul Style', style: '3x3' },
  { id: 'prs-style', name: 'PRS Style', style: '3x3' },
  { id: 'classical', name: 'Classical/Slotted', style: 'slotted' },
  { id: 'paddle', name: 'Paddle Blank', style: 'blank' },
])

const selectedTemplate = ref('')
const includeOverlay = ref(true)
const overlayInset = ref(2)  // mm
const loading = ref(false)
const previewSvg = ref('')

// Computed
const tunerLayout = computed(() => {
  if (headstockStyle.value === '3x3') return { bass: 3, treble: 3 }
  if (headstockStyle.value === '6-inline') return { bass: 0, treble: 6 }
  if (headstockStyle.value === '4x2') return { bass: 2, treble: 2 }
  return { bass: 0, treble: 0 }
})

// Methods
function selectTemplate(templateId: string) {
  selectedTemplate.value = templateId
  const template = templates.value.find(t => t.id === templateId)
  if (template) {
    headstockStyle.value = template.style
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
  <div class="headstock-designer-view">
    <div class="header">
      <h1>Headstock Designer</h1>
      <p class="subtitle">Design headstock shapes, tuner layouts, and decorative overlays</p>
    </div>

    <div class="content">
      <!-- Templates Panel -->
      <div class="panel templates-panel">
        <h3>Templates</h3>
        <div class="template-grid">
          <button
            v-for="template in templates"
            :key="template.id"
            class="template-btn"
            :class="{ active: selectedTemplate === template.id }"
            @click="selectTemplate(template.id)"
          >
            <span class="template-icon">🎸</span>
            <span class="template-name">{{ template.name }}</span>
          </button>
        </div>
      </div>

      <!-- Parameters Panel -->
      <div class="panel params-panel">
        <h3>Dimensions</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Length (mm)</label>
            <input type="number" v-model.number="headstockLength" step="5" min="100" max="250" />
          </div>
          <div class="form-group">
            <label>Width (mm)</label>
            <input type="number" v-model.number="headstockWidth" step="5" min="60" max="150" />
          </div>
        </div>

        <h3>Tuner Layout</h3>
        <div class="form-group">
          <label>Style</label>
          <select v-model="headstockStyle">
            <option value="3x3">3+3 (Gibson style)</option>
            <option value="6-inline">6 Inline (Fender style)</option>
            <option value="4x2">4+2 (Music Man style)</option>
            <option value="slotted">Slotted (Classical)</option>
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Tuner Hole Ø (mm)</label>
            <input type="number" v-model.number="tunerHoleDiameter" step="0.5" min="6" max="15" />
          </div>
          <div class="form-group">
            <label>Tuner Spacing (mm)</label>
            <input type="number" v-model.number="tunerSpacing" step="1" min="25" max="50" />
          </div>
        </div>

        <h3>Overlay</h3>
        <div class="form-group checkbox-group">
          <label>
            <input type="checkbox" v-model="includeOverlay" />
            Include decorative overlay
          </label>
        </div>
        <div class="form-group" v-if="includeOverlay">
          <label>Inset from edge (mm)</label>
          <input type="number" v-model.number="overlayInset" step="0.5" min="0" max="10" />
        </div>
      </div>

      <!-- Preview Panel -->
      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating preview...</div>
          <div v-else-if="previewSvg" v-html="previewSvg" class="svg-preview"></div>
          <div v-else class="placeholder">
            <span class="icon">🎸</span>
            <p>Select a template or configure dimensions</p>
            <p class="layout-info">
              Layout: {{ tunerLayout.bass }} bass / {{ tunerLayout.treble }} treble
            </p>
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
.headstock-designer-view {
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

.panel h3:not(:first-child) {
  margin-top: 1.5rem;
}

.template-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.template-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0.5rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.5rem;
  cursor: pointer;
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
  margin-bottom: 0.25rem;
}

.template-name {
  font-size: 0.75rem;
  color: #e5e5e5;
  text-align: center;
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

.layout-info {
  font-size: 0.875rem;
  color: #888;
  margin-top: 0.5rem;
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
