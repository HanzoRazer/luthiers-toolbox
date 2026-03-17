<script setup lang="ts">
/**
 * @deprecated — superseded by InlayWorkspaceShell Stage 2 (ArtStudioInlay.vue).
 * FretMarkersView was a stub with no backend.
 * Resolves INLAY-03.
 *
 * FretMarkersView - Fretboard Position Marker Designer
 * Design inlay patterns for fret position markers (dots, blocks, custom shapes)
 *
 * This is a simplified version focused on markers only.
 * For full inlay design, see InlayDesignerView.
 *
 * Planned API endpoints:
 *   GET  /api/art-studio/fret-markers/patterns
 *   POST /api/art-studio/fret-markers/preview
 *   POST /api/art-studio/fret-markers/export-dxf
 */
import { ref, computed } from 'vue'

// Form state
const markerStyle = ref('dots')  // dots, blocks, diamonds, custom
const scaleLength = ref(648)  // mm
const fretCount = ref(22)
const markerSize = ref(6)  // mm diameter or width
const sideDotSize = ref(2)  // mm

// Standard marker positions
const standardPositions = [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]
const selectedPositions = ref([...standardPositions])

// Double marker options
const doubleAt12 = ref(true)
const doubleAt24 = ref(true)

// Side dots
const includeSideDots = ref(true)
const sideDotOffset = ref(3)  // mm from edge

const markerStyles = ref([
  { id: 'dots', name: 'Classic Dots', icon: '●' },
  { id: 'blocks', name: 'Block Inlays', icon: '■' },
  { id: 'diamonds', name: 'Diamond', icon: '◆' },
  { id: 'trapezoid', name: 'Trapezoid', icon: '⬡' },
  { id: 'split-parallelogram', name: 'Split Parallelogram', icon: '◇' },
  { id: 'custom', name: 'Custom Shape', icon: '★' },
])

const loading = ref(false)
const previewSvg = ref('')

// Computed
const markerCount = computed(() => {
  let count = selectedPositions.value.length
  if (doubleAt12.value && selectedPositions.value.includes(12)) count++
  if (doubleAt24.value && selectedPositions.value.includes(24)) count++
  return count
})

// Methods
function togglePosition(fret: number) {
  const index = selectedPositions.value.indexOf(fret)
  if (index > -1) {
    selectedPositions.value.splice(index, 1)
  } else {
    selectedPositions.value.push(fret)
    selectedPositions.value.sort((a, b) => a - b)
  }
}

function selectStyle(styleId: string) {
  markerStyle.value = styleId
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
  <div class="fret-markers-view">
    <div class="header">
      <h1>Fret Markers</h1>
      <p class="subtitle">Design fretboard position markers and side dots</p>
    </div>

    <div class="content">
      <!-- Style Panel -->
      <div class="panel styles-panel">
        <h3>Marker Style</h3>
        <div class="style-grid">
          <button
            v-for="style in markerStyles"
            :key="style.id"
            class="style-btn"
            :class="{ active: markerStyle === style.id }"
            @click="selectStyle(style.id)"
          >
            <span class="style-icon">{{ style.icon }}</span>
            <span class="style-name">{{ style.name }}</span>
          </button>
        </div>
      </div>

      <!-- Parameters Panel -->
      <div class="panel params-panel">
        <h3>Fretboard</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Scale Length (mm)</label>
            <input type="number" v-model.number="scaleLength" step="1" min="500" max="800" />
          </div>
          <div class="form-group">
            <label>Fret Count</label>
            <input type="number" v-model.number="fretCount" step="1" min="12" max="27" />
          </div>
        </div>

        <h3>Marker Size</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Face Marker (mm)</label>
            <input type="number" v-model.number="markerSize" step="0.5" min="3" max="15" />
          </div>
          <div class="form-group">
            <label>Side Dot (mm)</label>
            <input type="number" v-model.number="sideDotSize" step="0.25" min="1" max="4" />
          </div>
        </div>

        <h3>Positions</h3>
        <div class="fret-selector">
          <button
            v-for="fret in fretCount"
            :key="fret"
            class="fret-btn"
            :class="{ active: selectedPositions.includes(fret) }"
            @click="togglePosition(fret)"
          >
            {{ fret }}
          </button>
        </div>

        <div class="form-group checkbox-group">
          <label>
            <input type="checkbox" v-model="doubleAt12" />
            Double marker at 12th fret
          </label>
        </div>
        <div class="form-group checkbox-group">
          <label>
            <input type="checkbox" v-model="includeSideDots" />
            Include side dots
          </label>
        </div>

        <p class="marker-count">Total markers: {{ markerCount }}</p>
      </div>

      <!-- Preview Panel -->
      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating preview...</div>
          <div v-else-if="previewSvg" v-html="previewSvg" class="svg-preview"></div>
          <div v-else class="placeholder">
            <span class="icon">🎸</span>
            <p>Configure markers and click Generate Preview</p>
            <p class="positions">
              Positions: {{ selectedPositions.join(', ') }}
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
.fret-markers-view {
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

.style-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.style-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem 0.5rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.15s;
}

.style-btn:hover {
  background: #333;
  border-color: #444;
}

.style-btn.active {
  background: #1e3a5f;
  border-color: #60a5fa;
}

.style-icon {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.style-name {
  font-size: 0.7rem;
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

.form-group input {
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
  font-size: 0.875rem;
}

.fret-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 1rem;
}

.fret-btn {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.25rem;
  color: #888;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.fret-btn:hover {
  background: #333;
}

.fret-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}

.marker-count {
  font-size: 0.875rem;
  color: #60a5fa;
  margin-top: 0.5rem;
}

.preview-container {
  aspect-ratio: 3/1;
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

.positions {
  font-size: 0.75rem;
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
