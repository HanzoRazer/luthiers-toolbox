<script setup lang="ts">
/**
 * VCarveView - V-Carve Text and Decorative Lettering
 * Connected to API endpoints:
 *   POST /api/art-studio/vcarve/preview
 *   POST /api/cam/toolpath/vcarve/preview_infill
 *   POST /api/cam/toolpath/vcarve/gcode
 */
import { ref, computed, watch } from 'vue'

// API bases
const ART_STUDIO_API = '/api/art-studio/vcarve'
const CAM_API = '/api/cam/toolpath/vcarve'

// Text input state
const textContent = ref('Luthier')
const fontSize = ref(48)
const fontFamily = ref('serif')
const isBold = ref(false)
const isItalic = ref(false)

// V-Carve parameters
const vbitAngle = ref(60)
const maxDepth = ref(1.5)
const safeZ = ref(5.0)
const feedRate = ref(800)
const plungeRate = ref(300)

// Infill parameters
const infillMode = ref<'raster' | 'contour'>('raster')
const rasterAngle = ref(0)
const flatStepover = ref(1.2)

// SVG state
const svgContent = ref('')
const previewSvg = ref('')
const infillSvg = ref('')

// Result state
const gcode = ref('')
const runId = ref('')
const stats = ref<{ path_count?: number; total_length?: number; bounds?: any } | null>(null)
const infillStats = ref<{ total_spans?: number; total_len?: number } | null>(null)

// UI state
const previewMode = ref<'text' | 'infill' | 'gcode'>('text')
const isGeneratingPreview = ref(false)
const isGeneratingInfill = ref(false)
const isGeneratingGcode = ref(false)
const error = ref('')

// Templates
const templates = [
  { name: 'Classic Headstock', text: 'Martin', font: 'serif' },
  { name: 'Modern Brand', text: 'ACOUSTIC', font: 'sans-serif' },
  { name: 'Date Stamp', text: 'Est. 2024', font: 'serif' },
  { name: 'Serial Number', text: 'No. 001', font: 'monospace' },
  { name: 'Custom Logo', text: 'Custom', font: 'script' },
]

// Computed
const hasPreview = computed(() => previewSvg.value.length > 0 || infillSvg.value.length > 0)
const hasGcode = computed(() => gcode.value.length > 0)
const gcodeLineCount = computed(() => gcode.value.split('\n').length)

// Generate SVG from text
function textToSvg(text: string): string {
  const weight = isBold.value ? 'bold' : 'normal'
  const style = isItalic.value ? 'italic' : 'normal'
  const lines = text.split('\n')
  const lineHeight = fontSize.value * 1.2
  const width = Math.max(200, text.length * fontSize.value * 0.6)
  const height = lines.length * lineHeight + 20

  const textElements = lines.map((line, i) => {
    const y = 10 + fontSize.value + i * lineHeight
    return `<text x="10" y="${y}" font-family="${fontFamily.value}" font-size="${fontSize.value}" font-weight="${weight}" font-style="${style}" fill="none" stroke="black" stroke-width="1">${escapeXml(line)}</text>`
  }).join('\n  ')

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  ${textElements}
</svg>`
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// Watch text changes and update SVG
watch([textContent, fontSize, fontFamily, isBold, isItalic], () => {
  if (textContent.value) {
    svgContent.value = textToSvg(textContent.value)
  }
}, { immediate: true })

// API calls
async function generatePreview() {
  if (!svgContent.value) {
    error.value = 'Please enter some text first'
    return
  }

  isGeneratingPreview.value = true
  error.value = ''

  try {
    const response = await fetch(`${ART_STUDIO_API}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        svg: svgContent.value,
        normalize: true,
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to generate preview')
    }

    const data = await response.json()
    stats.value = data.stats
    previewSvg.value = svgContent.value
    previewMode.value = 'text'
  } catch (e: any) {
    error.value = e.message || 'Failed to generate preview'
  } finally {
    isGeneratingPreview.value = false
  }
}

async function generateInfill() {
  if (!svgContent.value) {
    error.value = 'Please enter some text first'
    return
  }

  isGeneratingInfill.value = true
  error.value = ''

  try {
    const response = await fetch(`${CAM_API}/preview_infill`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode: infillMode.value,
        centerlines_svg: svgContent.value,
        approx_stroke_width_mm: maxDepth.value * 2,
        raster_angle_deg: rasterAngle.value,
        flat_stepover_mm: flatStepover.value,
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to generate infill preview')
    }

    const data = await response.json()
    if (data.ok) {
      infillSvg.value = data.svg
      infillStats.value = data.stats
      previewMode.value = 'infill'
    } else {
      throw new Error('Infill generation failed')
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to generate infill preview'
  } finally {
    isGeneratingInfill.value = false
  }
}

async function generateGcode() {
  if (!svgContent.value) {
    error.value = 'Please enter some text first'
    return
  }

  isGeneratingGcode.value = true
  error.value = ''

  try {
    const response = await fetch(`${CAM_API}/gcode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        svg: svgContent.value,
        bit_angle_deg: vbitAngle.value,
        depth_mm: maxDepth.value,
        safe_z_mm: safeZ.value,
        feed_rate_mm_min: feedRate.value,
        plunge_rate_mm_min: plungeRate.value,
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      if (err.detail?.error === 'SAFETY_BLOCKED') {
        throw new Error(`Safety blocked: ${err.detail.message}`)
      }
      throw new Error(err.detail?.message || err.detail || 'Failed to generate G-code')
    }

    const data = await response.json()
    gcode.value = data.gcode
    runId.value = data.run_id || ''
    previewMode.value = 'gcode'
  } catch (e: any) {
    error.value = e.message || 'Failed to generate G-code'
  } finally {
    isGeneratingGcode.value = false
  }
}

function downloadGcode() {
  if (!gcode.value) return

  const blob = new Blob([gcode.value], { type: 'text/plain' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `vcarve_${textContent.value.replace(/[^a-zA-Z0-9]/g, '_')}.nc`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

function applyTemplate(template: typeof templates[0]) {
  textContent.value = template.text
  fontFamily.value = template.font
}

function toggleBold() {
  isBold.value = !isBold.value
}

function toggleItalic() {
  isItalic.value = !isItalic.value
}
</script>

<template>
  <div class="vcarve-view">
    <header class="view-header">
      <h1>V-Carve Designer</h1>
      <p class="subtitle">Create V-carved text, logos, and decorative elements for headstocks and labels</p>
    </header>

    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = ''" class="dismiss-btn">&times;</button>
    </div>

    <div class="content-grid">
      <!-- Text Input -->
      <section class="panel text-panel">
        <h2>Text Input</h2>
        <div class="text-input-group">
          <textarea
            v-model="textContent"
            placeholder="Enter text to carve..."
            rows="3"
          ></textarea>
          <div class="font-controls">
            <label>
              Font
              <select v-model="fontFamily">
                <option value="serif">Serif (Classic)</option>
                <option value="sans-serif">Sans-Serif (Modern)</option>
                <option value="monospace">Monospace</option>
                <option value="cursive">Script (Elegant)</option>
              </select>
            </label>
            <label>
              Size (px)
              <input v-model.number="fontSize" type="number" min="12" max="200" step="4" />
            </label>
            <div class="style-buttons">
              <button
                class="style-btn"
                :class="{ active: isBold }"
                title="Bold"
                @click="toggleBold"
              >B</button>
              <button
                class="style-btn"
                :class="{ active: isItalic }"
                title="Italic"
                @click="toggleItalic"
              >I</button>
            </div>
          </div>
        </div>
        <button
          class="btn-secondary"
          :disabled="!textContent || isGeneratingPreview"
          @click="generatePreview"
        >
          {{ isGeneratingPreview ? 'Analyzing...' : 'Analyze Text' }}
        </button>
      </section>

      <!-- V-Carve Parameters -->
      <section class="panel params-panel">
        <h2>V-Carve Parameters</h2>
        <div class="param-group">
          <label>
            V-Bit Angle
            <select v-model.number="vbitAngle">
              <option :value="30">30°</option>
              <option :value="45">45°</option>
              <option :value="60">60° (Recommended)</option>
              <option :value="90">90°</option>
            </select>
          </label>
          <label>
            Cut Depth (mm)
            <input v-model.number="maxDepth" type="number" step="0.1" min="0.1" max="10" />
          </label>
          <label>
            Safe Z (mm)
            <input v-model.number="safeZ" type="number" step="1" min="1" max="50" />
          </label>
          <label>
            Feed Rate (mm/min)
            <input v-model.number="feedRate" type="number" step="50" min="100" max="5000" />
          </label>
          <label>
            Plunge Rate (mm/min)
            <input v-model.number="plungeRate" type="number" step="25" min="50" max="2000" />
          </label>
        </div>

        <div class="infill-section">
          <h3>Infill Mode</h3>
          <div class="infill-options">
            <label class="radio-label">
              <input type="radio" v-model="infillMode" value="raster" />
              Raster
            </label>
            <label class="radio-label">
              <input type="radio" v-model="infillMode" value="contour" />
              Contour
            </label>
          </div>
          <div v-if="infillMode === 'raster'" class="infill-params">
            <label>
              Raster Angle (°)
              <input v-model.number="rasterAngle" type="number" step="15" min="0" max="180" />
            </label>
          </div>
          <label>
            Stepover (mm)
            <input v-model.number="flatStepover" type="number" step="0.1" min="0.1" max="5" />
          </label>
        </div>

        <div class="button-group">
          <button
            class="btn-secondary"
            :disabled="!textContent || isGeneratingInfill"
            @click="generateInfill"
          >
            {{ isGeneratingInfill ? 'Generating...' : 'Preview Infill' }}
          </button>
          <button
            class="btn-primary"
            :disabled="!textContent || isGeneratingGcode"
            @click="generateGcode"
          >
            {{ isGeneratingGcode ? 'Generating...' : 'Generate G-Code' }}
          </button>
        </div>
      </section>

      <!-- Preview -->
      <section class="panel preview-panel">
        <h2>Preview</h2>
        <div class="preview-tabs">
          <button
            class="tab"
            :class="{ active: previewMode === 'text' }"
            @click="previewMode = 'text'"
          >Text</button>
          <button
            class="tab"
            :class="{ active: previewMode === 'infill' }"
            @click="previewMode = 'infill'"
            :disabled="!infillSvg"
          >Infill</button>
          <button
            class="tab"
            :class="{ active: previewMode === 'gcode' }"
            @click="previewMode = 'gcode'"
            :disabled="!hasGcode"
          >G-Code</button>
        </div>

        <div class="preview-container">
          <!-- Text Preview -->
          <div v-if="previewMode === 'text'" class="text-preview-area">
            <div class="text-preview" :style="{ fontFamily: fontFamily }">
              <span
                :style="{
                  fontWeight: isBold ? 'bold' : 'normal',
                  fontStyle: isItalic ? 'italic' : 'normal',
                  fontSize: `${Math.min(fontSize, 72)}px`
                }"
              >{{ textContent || 'Preview' }}</span>
            </div>
          </div>

          <!-- Infill Preview -->
          <div v-else-if="previewMode === 'infill' && infillSvg" class="svg-preview" v-html="infillSvg"></div>

          <!-- G-Code Preview -->
          <div v-else-if="previewMode === 'gcode' && hasGcode" class="gcode-preview">
            <pre>{{ gcode.slice(0, 2000) }}{{ gcode.length > 2000 ? '\n...' : '' }}</pre>
          </div>

          <!-- Empty state -->
          <div v-else class="preview-placeholder">
            <span>Preview will appear here</span>
          </div>
        </div>

        <!-- Stats -->
        <div v-if="stats && previewMode === 'text'" class="preview-stats">
          <span v-if="stats.path_count">Paths: {{ stats.path_count }}</span>
          <span v-if="stats.total_length">Length: {{ stats.total_length.toFixed(1) }}mm</span>
        </div>

        <div v-if="infillStats && previewMode === 'infill'" class="preview-stats">
          <span>Spans: {{ infillStats.total_spans }}</span>
          <span>Total Length: {{ infillStats.total_len?.toFixed(1) }}mm</span>
        </div>

        <div v-if="hasGcode && previewMode === 'gcode'" class="gcode-actions">
          <span class="gcode-info">{{ gcodeLineCount }} lines</span>
          <span v-if="runId" class="run-id">Run: {{ runId }}</span>
          <button class="btn-download" @click="downloadGcode">
            Download .nc
          </button>
        </div>
      </section>

      <!-- Templates -->
      <section class="panel templates-panel">
        <h2>Templates</h2>
        <div class="template-list">
          <div
            v-for="template in templates"
            :key="template.name"
            class="template-item"
            @click="applyTemplate(template)"
          >
            <span class="template-preview" :style="{ fontFamily: template.font }">
              {{ template.text }}
            </span>
            <span class="template-name">{{ template.name }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.vcarve-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dismiss-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #dc2626;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.panel h2 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1e293b;
}

.panel h3 {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #475569;
}

/* Text Input */
.text-input-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 1rem;
  resize: vertical;
  margin-bottom: 1rem;
  font-family: inherit;
}

.font-controls {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  margin-bottom: 1rem;
}

.font-controls label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

.font-controls select,
.font-controls input {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
}

.style-buttons {
  display: flex;
  gap: 0.25rem;
}

.style-btn {
  width: 2.25rem;
  height: 2.25rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s;
}

.style-btn:hover {
  border-color: #2563eb;
  color: #2563eb;
}

.style-btn.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

/* Parameters */
.param-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.param-group label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

.param-group input,
.param-group select {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.infill-section {
  padding: 1rem;
  background: #f8fafc;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
}

.infill-options {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 0.75rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.infill-params {
  margin-bottom: 0.75rem;
}

.infill-params label,
.infill-section > label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

.infill-params input,
.infill-section > label input {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Preview */
.preview-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.tab:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tab.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.preview-container {
  min-height: 200px;
  background: #f8fafc;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  overflow: hidden;
}

.text-preview-area {
  width: 100%;
  padding: 2rem;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.text-preview {
  color: #f8fafc;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
  text-align: center;
  word-break: break-word;
  max-width: 100%;
}

.svg-preview {
  width: 100%;
  padding: 1rem;
  background: white;
}

.svg-preview :deep(svg) {
  width: 100%;
  height: auto;
  max-height: 300px;
}

.gcode-preview {
  width: 100%;
  max-height: 300px;
  overflow: auto;
  padding: 1rem;
  background: #1e293b;
}

.gcode-preview pre {
  margin: 0;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.75rem;
  color: #94a3b8;
  white-space: pre-wrap;
}

.preview-placeholder {
  color: #94a3b8;
  text-align: center;
  padding: 2rem;
}

.preview-stats {
  display: flex;
  gap: 1.5rem;
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 1rem;
}

.gcode-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.gcode-info {
  font-size: 0.875rem;
  color: #64748b;
}

.run-id {
  font-size: 0.75rem;
  color: #94a3b8;
  font-family: monospace;
}

.btn-download {
  margin-left: auto;
  padding: 0.5rem 1rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-download:hover {
  background: #059669;
}

/* Templates */
.template-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.template-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.template-preview {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e293b;
  min-width: 100px;
}

.template-name {
  font-size: 0.875rem;
  color: #64748b;
}
</style>
