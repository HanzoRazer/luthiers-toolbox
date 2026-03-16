<script setup lang="ts">
/**
 * HeadstockDesignerView - Guitar Headstock Shape & Overlay Designer
 * Design headstock outlines, tuner holes, and decorative overlays
 *
 * Wired to:
 *   GET  /api/instruments/guitar/headstock-inlay/templates
 *   GET  /api/instruments/guitar/headstock-inlay/styles
 *   POST /api/instruments/guitar/headstock-inlay/generate-prompt
 */
import { ref, computed, onMounted } from 'vue'
import {
  listHeadstockTemplates,
  generateHeadstockPrompt,
  type HeadstockTemplateInfo,
} from '@/api/art-studio'

// Headstock types
const headstockStyle = ref('3x3')  // 3x3, 6-inline, 4x2
const headstockLength = ref(180)  // mm
const headstockWidth = ref(90)  // mm
const tunerHoleDiameter = ref(10)  // mm
const tunerSpacing = ref(35)  // mm
const stringSpacing = ref(7.5)  // mm at nut

// Templates from API (mapped to { id, name, style } for template grid)
const templates = ref<Array<{ id: string; name: string; style: string }>>([])
const templatesLoadError = ref<string | null>(null)

const selectedTemplate = ref('')
const includeOverlay = ref(true)
const overlayInset = ref(2)  // mm
const loading = ref(false)
const previewSvg = ref('')
const generatedPrompt = ref('')

// Computed
const tunerLayout = computed(() => {
  if (headstockStyle.value === '3x3') return { bass: 3, treble: 3 }
  if (headstockStyle.value === '6-inline') return { bass: 0, treble: 6 }
  if (headstockStyle.value === '4x2') return { bass: 2, treble: 2 }
  return { bass: 0, treble: 0 }
})

function mapStyleToTunerLayout(style: string): string {
  const s = style.toLowerCase()
  if (s.includes('strat') || s === '6-inline' || s === 'fender') return '6-inline'
  if (s.includes('3x3') || s.includes('gibson') || s.includes('prs')) return '3x3'
  if (s.includes('4x2') || s.includes('music man')) return '4x2'
  if (s.includes('slotted') || s.includes('classical')) return 'slotted'
  return '3x3'
}

// Methods
function selectTemplate(templateId: string) {
  selectedTemplate.value = templateId
  const template = templates.value.find(t => t.id === templateId)
  if (template) {
    headstockStyle.value = template.style
  }
}

async function loadTemplates() {
  templatesLoadError.value = null
  try {
    const list = await listHeadstockTemplates()
    templates.value = list.map((t: HeadstockTemplateInfo) => ({
      id: t.id,
      name: t.name,
      style: mapStyleToTunerLayout(t.headstock_style),
    }))
    if (templates.value.length > 0 && !selectedTemplate.value) {
      selectedTemplate.value = templates.value[0].id
      headstockStyle.value = templates.value[0].style
    }
  } catch (e: any) {
    templatesLoadError.value = e.message || 'Failed to load templates'
    templates.value = []
  }
}

async function generatePreview() {
  loading.value = true
  generatedPrompt.value = ''
  try {
    const template = templates.value.find(t => t.id === selectedTemplate.value)
    const style = template?.style ?? headstockStyle.value
    const styleApi = style === '6-inline' ? 'stratocaster' : style === '3x3' ? 'les_paul' : style === '4x2' ? 'prs' : 'les_paul'
    const res = await generateHeadstockPrompt({
      style: styleApi,
      headstock_wood: 'mahogany',
      inlay_design: 'dove',
      inlay_material: 'mother_of_pearl',
    })
    generatedPrompt.value = res.prompt
    previewSvg.value = ''
  } catch (e: any) {
    generatedPrompt.value = `Error: ${e.message || 'Preview failed'}`
  } finally {
    loading.value = false
  }
}

async function exportDxf() {
  loading.value = true
  try {
    const template = templates.value.find(t => t.id === selectedTemplate.value)
    const style = template?.style ?? headstockStyle.value
    const styleApi = style === '6-inline' ? 'stratocaster' : style === '3x3' ? 'les_paul' : style === '4x2' ? 'prs' : 'les_paul'
    const res = await generateHeadstockPrompt({
      style: styleApi,
      headstock_wood: 'mahogany',
      inlay_design: 'dove',
      inlay_material: 'mother_of_pearl',
    })
    await navigator.clipboard.writeText(res.prompt)
    generatedPrompt.value = res.prompt
    alert('Prompt copied to clipboard. Use it with an image generator or the Neck Generator for geometry export.')
  } catch (e: any) {
    alert(e.message || 'Export failed')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTemplates()
})
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
        <p v-if="templatesLoadError" class="error-text">{{ templatesLoadError }}</p>
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
          <div v-else-if="generatedPrompt" class="prompt-preview">
            <p class="prompt-label">Generated prompt</p>
            <pre class="prompt-text">{{ generatedPrompt }}</pre>
          </div>
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

.error-text {
  color: #f87171;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.prompt-preview {
  text-align: left;
  padding: 0.75rem;
  background: #1e293b;
  border-radius: 0.5rem;
  max-height: 200px;
  overflow: auto;
}

.prompt-preview .prompt-label {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}

.prompt-text {
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  color: #e2e8f0;
}

@media (max-width: 1200px) {
  .content {
    grid-template-columns: 1fr;
  }
}
</style>
