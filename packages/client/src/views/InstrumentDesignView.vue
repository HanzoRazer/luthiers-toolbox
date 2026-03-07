<template>
  <div class="instrument-design-view">
    <div class="header">
      <router-link to="/design-hub" class="back-link">
        &larr; Back to Design Hub
      </router-link>
      <h1>{{ instrument?.name || 'Loading...' }}</h1>
      <p v-if="instrument" class="category-badge">{{ instrument.category }}</p>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading instrument data...</p>
    </div>

    <div v-else-if="error" class="error">
      <h2>Instrument Not Found</h2>
      <p>{{ error }}</p>
      <router-link to="/design-hub" class="btn btn-primary">
        Browse All Instruments
      </router-link>
    </div>

    <div v-else-if="instrument" class="content">
      <!-- Main Preview Panel -->
      <div class="preview-panel">
        <div class="preview-container">
          <img
            v-if="previewUrl"
            :src="previewUrl"
            :alt="instrument.name"
            class="preview-image"
          />
          <div v-else class="preview-placeholder">
            <span class="icon">🎸</span>
            <p>Preview loading...</p>
          </div>
        </div>
        <div class="dimensions">
          <div class="dimension">
            <span class="label">Width</span>
            <span class="value">{{ instrument.dimensions_mm?.width?.toFixed(1) }} mm</span>
          </div>
          <div class="dimension">
            <span class="label">Height</span>
            <span class="value">{{ instrument.dimensions_mm?.height?.toFixed(1) }} mm</span>
          </div>
          <div class="dimension">
            <span class="label">Points</span>
            <span class="value">{{ instrument.points }}</span>
          </div>
        </div>
      </div>

      <!-- Actions Panel -->
      <div class="actions-panel">
        <h3>Actions</h3>
        <div class="action-buttons">
          <button class="btn btn-primary" @click="exportDxf">
            <span class="icon">📥</span> Export DXF
          </button>
          <button class="btn btn-secondary" @click="sendToCam">
            <span class="icon">⚙️</span> Send to CAM
          </button>
          <button class="btn btn-secondary" @click="openInEditor">
            <span class="icon">✏️</span> Edit Parameters
          </button>
        </div>

        <h3>Related Tools</h3>
        <div class="related-tools">
          <router-link to="/design-hub" class="tool-link">
            <span class="icon">🎸</span> Body Outline Generator
          </router-link>
          <router-link to="/instrument-geometry" class="tool-link">
            <span class="icon">📏</span> Fretboard Calculator
          </router-link>
          <router-link to="/lab/bridge" class="tool-link">
            <span class="icon">🌉</span> Bridge Calculator
          </router-link>
          <router-link to="/art-studio/inlay" class="tool-link">
            <span class="icon">💎</span> Inlay Designer
          </router-link>
        </div>

        <h3>Specifications</h3>
        <div class="specs">
          <div class="spec-row">
            <span class="label">Source</span>
            <span class="value">{{ instrument.source || 'DXF extraction' }}</span>
          </div>
          <div class="spec-row" v-if="instrument.dxf">
            <span class="label">DXF File</span>
            <span class="value">{{ instrument.dxf }}</span>
          </div>
          <div class="spec-row" v-if="instrument.has_bulge_data">
            <span class="label">Arc Data</span>
            <span class="value">Yes (smooth curves)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Instrument Gallery -->
    <div class="gallery-section" v-if="!loading && !error">
      <h3>Other {{ instrument?.category }} Instruments</h3>
      <div class="gallery">
        <router-link
          v-for="(inst, id) in relatedInstruments"
          :key="id"
          :to="`/design/${id}`"
          class="gallery-item"
          :class="{ active: id === instrumentId }"
        >
          <span class="name">{{ inst.name }}</span>
          <span class="dims">{{ inst.dimensions_mm?.width?.toFixed(0) }} × {{ inst.dimensions_mm?.height?.toFixed(0) }} mm</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface InstrumentBody {
  name: string
  category: string
  dimensions_mm: {
    width: number
    height: number
  }
  points: number
  dxf?: string
  source?: string
  has_bulge_data?: boolean
}

interface Catalog {
  bodies: Record<string, InstrumentBody>
}

const route = useRoute()
const router = useRouter()

const instrumentId = computed(() => route.params.instrumentId as string)
const loading = ref(true)
const error = ref<string | null>(null)
const catalog = ref<Catalog | null>(null)
const instrument = computed(() => catalog.value?.bodies[instrumentId.value])
const previewUrl = ref<string | null>(null)

const relatedInstruments = computed(() => {
  if (!catalog.value || !instrument.value) return {}
  const category = instrument.value.category
  return Object.fromEntries(
    Object.entries(catalog.value.bodies)
      .filter(([id, inst]) => inst.category === category && id !== instrumentId.value)
      .slice(0, 6)
  )
})

async function loadCatalog() {
  loading.value = true
  error.value = null

  try {
    const response = await fetch('/api/instrument/geometry/catalog')
    if (!response.ok) throw new Error('Failed to load catalog')
    catalog.value = await response.json()

    if (!catalog.value?.bodies[instrumentId.value]) {
      error.value = `Instrument "${instrumentId.value}" not found in catalog.`
    } else {
      // Load preview SVG
      loadPreview()
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
  } finally {
    loading.value = false
  }
}

async function loadPreview() {
  try {
    const response = await fetch(`/api/instrument/geometry/body/${instrumentId.value}/preview.svg`)
    if (response.ok) {
      const blob = await response.blob()
      previewUrl.value = URL.createObjectURL(blob)
    }
  } catch {
    // Preview not available
  }
}

function exportDxf() {
  window.open(`/api/instrument/geometry/body/${instrumentId.value}/download.dxf`, '_blank')
}

function sendToCam() {
  router.push({
    path: '/cam/dxf-to-gcode',
    query: { instrument: instrumentId.value }
  })
}

function openInEditor() {
  router.push({
    path: '/guitar-dimensions',
    query: { preset: instrumentId.value }
  })
}

onMounted(loadCatalog)

watch(instrumentId, () => {
  loadCatalog()
})
</script>

<style scoped>
.instrument-design-view {
  min-height: 100vh;
  background: #0a0a0a;
  color: #e5e5e5;
  padding: 2rem;
}

.header {
  max-width: 1200px;
  margin: 0 auto 2rem;
}

.back-link {
  color: #60a5fa;
  text-decoration: none;
  font-size: 0.875rem;
  display: inline-block;
  margin-bottom: 1rem;
}

.back-link:hover {
  text-decoration: underline;
}

.header h1 {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
}

.category-badge {
  display: inline-block;
  background: #1e3a5f;
  color: #60a5fa;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.loading, .error {
  max-width: 600px;
  margin: 4rem auto;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error h2 {
  color: #ef4444;
  margin-bottom: 1rem;
}

.content {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

.preview-panel {
  background: #1a1a1a;
  border-radius: 1rem;
  padding: 2rem;
}

.preview-container {
  aspect-ratio: 4/3;
  background: #0d0d0d;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-placeholder {
  text-align: center;
  color: #666;
}

.preview-placeholder .icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1rem;
}

.dimensions {
  display: flex;
  gap: 2rem;
  justify-content: center;
}

.dimension {
  text-align: center;
}

.dimension .label {
  display: block;
  font-size: 0.75rem;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.dimension .value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
}

.actions-panel {
  background: #1a1a1a;
  border-radius: 1rem;
  padding: 1.5rem;
}

.actions-panel h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 1rem;
}

.actions-panel h3:not(:first-child) {
  margin-top: 1.5rem;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
}

.btn-primary {
  background: #2563eb;
  color: #fff;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #262626;
  color: #e5e5e5;
  border: 1px solid #333;
}

.btn-secondary:hover {
  background: #333;
  border-color: #444;
}

.related-tools {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tool-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #262626;
  border-radius: 0.5rem;
  color: #e5e5e5;
  text-decoration: none;
  font-size: 0.875rem;
  transition: background 0.15s;
}

.tool-link:hover {
  background: #333;
}

.tool-link .icon {
  font-size: 1.25rem;
}

.specs {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.spec-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #262626;
}

.spec-row .label {
  color: #888;
}

.spec-row .value {
  color: #e5e5e5;
}

.gallery-section {
  max-width: 1200px;
  margin: 3rem auto 0;
}

.gallery-section h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #888;
  margin-bottom: 1rem;
}

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.gallery-item {
  background: #1a1a1a;
  border: 1px solid #262626;
  border-radius: 0.5rem;
  padding: 1rem;
  text-decoration: none;
  transition: all 0.15s;
}

.gallery-item:hover {
  border-color: #60a5fa;
  background: #1e3a5f;
}

.gallery-item.active {
  border-color: #60a5fa;
  background: #1e3a5f;
}

.gallery-item .name {
  display: block;
  color: #e5e5e5;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.gallery-item .dims {
  font-size: 0.75rem;
  color: #888;
}

@media (max-width: 900px) {
  .content {
    grid-template-columns: 1fr;
  }
}
</style>
