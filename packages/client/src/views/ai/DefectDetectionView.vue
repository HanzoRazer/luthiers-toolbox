<script setup lang="ts">
/**
 * DefectDetectionView - AI-Powered Defect Detection (E-3)
 * Upload photos to observe grain, runout, and surface anomalies
 *
 * Connected to API endpoints:
 *   POST /api/ai/defects/analyze
 *
 * Session E-3: Visual observation endpoint, no grading
 */
import { ref, onMounted } from 'vue'
import { useAgenticEvents } from '@/composables/useAgenticEvents'

// E-1/E-3: Agentic Spine event emission
const { emitViewRendered, emitAnalysisCompleted, emitAnalysisFailed } = useAgenticEvents()

// E-1/E-3: Emit view_rendered on mount
onMounted(() => {
  emitViewRendered('defect_detection')
})

const selectedFile = ref<File | null>(null)
const previewUrl = ref<string>('')
const isAnalyzing = ref(false)
const woodSpecies = ref<string>('')

interface AnalysisResult {
  observations: string
  grain_spacing_estimate: string
  runout_visible: boolean
  anomalies_detected: boolean
  confidence: string
}

const analysisResult = ref<AnalysisResult | null>(null)
const errorMessage = ref<string>('')

const defectTypes = [
  { name: 'Grain Spacing', description: 'Lines per inch/mm estimation' },
  { name: 'Runout', description: 'Grain angle deviation' },
  { name: 'Checking', description: 'Surface cracks or splits' },
  { name: 'Discoloration', description: 'Staining or mineral streaks' },
  { name: 'Knots', description: 'Branch inclusion areas' },
]

const recentScans = ref([
  { id: 1, filename: 'top_plate_front.jpg', anomalies: false, date: '2026-03-21' },
  { id: 2, filename: 'binding_corner_01.jpg', anomalies: true, date: '2026-03-20' },
  { id: 3, filename: 'neck_heel_joint.jpg', anomalies: false, date: '2026-03-19' },
])

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    selectedFile.value = input.files[0]
    previewUrl.value = URL.createObjectURL(input.files[0])
    analysisResult.value = null
    errorMessage.value = ''
  }
}

async function analyzeImage() {
  if (!selectedFile.value) return

  isAnalyzing.value = true
  errorMessage.value = ''
  analysisResult.value = null

  try {
    // Convert file to base64
    const reader = new FileReader()
    const base64Promise = new Promise<string>((resolve, reject) => {
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
    })
    reader.readAsDataURL(selectedFile.value)
    const dataUrl = await base64Promise

    // Call API
    const res = await fetch('/api/ai/defects/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: dataUrl,
        wood_species: woodSpecies.value || null,
      }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Service unavailable' }))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }

    const data = await res.json()
    analysisResult.value = data

    // E-3: Emit analysis_completed for agentic spine
    emitAnalysisCompleted(['defect_observation_v1'])

  } catch (e: any) {
    errorMessage.value = e.message || 'Analysis failed'
    // E-3: Emit analysis_failed for agentic spine
    emitAnalysisFailed(e.message || 'Analysis failed', 'DEFECT_DETECTION_ERROR')
  } finally {
    isAnalyzing.value = false
  }
}
</script>

<template>
  <div class="defect-detection-view">
    <div class="header">
      <h1>AI Surface Observer</h1>
      <p class="subtitle">Visual observations of wood grain and surface characteristics</p>
    </div>

    <div class="content">
      <div class="panel upload-panel">
        <h3>Upload Image</h3>
        <div
          class="upload-zone"
          :class="{ 'has-image': previewUrl }"
          @click="($refs.fileInput as HTMLInputElement).click()"
        >
          <input type="file" ref="fileInput" accept="image/*" @change="handleFileSelect" hidden />
          <img v-if="previewUrl" :src="previewUrl" alt="Preview" class="preview-image" />
          <div v-else class="upload-placeholder">
            <span class="upload-icon">🔍</span>
            <p>Click to upload image</p>
            <p class="hint">High resolution recommended</p>
          </div>
        </div>

        <div class="species-input">
          <label for="wood-species">Wood Species (optional)</label>
          <input
            id="wood-species"
            type="text"
            v-model="woodSpecies"
            placeholder="e.g., sitka spruce, mahogany"
          />
        </div>

        <button
          class="btn btn-primary btn-large"
          @click="analyzeImage"
          :disabled="!selectedFile || isAnalyzing"
        >
          {{ isAnalyzing ? 'Analyzing...' : '🔍 Observe Surface' }}
        </button>

        <div class="defect-types">
          <h4>Observable Characteristics</h4>
          <div class="type-list">
            <div v-for="type in defectTypes" :key="type.name" class="type-item">
              <span class="type-name">{{ type.name }}</span>
              <span class="type-desc">{{ type.description }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel results-panel">
        <h3>Observations</h3>

        <div v-if="isAnalyzing" class="analyzing">
          <div class="spinner"></div>
          <p>AI is observing surface characteristics...</p>
          <div class="scan-progress">
            <div class="scan-line"></div>
          </div>
        </div>

        <div v-else-if="errorMessage" class="error-display">
          <span class="icon">⚠️</span>
          <p>{{ errorMessage }}</p>
          <button class="btn btn-secondary" @click="analyzeImage">Retry</button>
        </div>

        <div v-else-if="analysisResult" class="results">
          <div class="observation-summary">
            <div class="summary-badges">
              <span class="badge" :class="{ active: analysisResult.runout_visible }">
                {{ analysisResult.runout_visible ? '⚠️ Runout Visible' : '✓ No Runout' }}
              </span>
              <span class="badge" :class="{ active: analysisResult.anomalies_detected }">
                {{ analysisResult.anomalies_detected ? '⚠️ Anomalies Found' : '✓ Surface Clear' }}
              </span>
              <span class="confidence-badge">
                Confidence: {{ analysisResult.confidence }}
              </span>
            </div>
          </div>

          <div class="observation-section">
            <h4>Grain Spacing</h4>
            <p class="grain-estimate">{{ analysisResult.grain_spacing_estimate }}</p>
          </div>

          <div class="observation-section">
            <h4>Detailed Observations</h4>
            <p class="observations-text">{{ analysisResult.observations }}</p>
          </div>

          <div class="result-actions">
            <button class="btn btn-secondary">Save Report</button>
            <button class="btn btn-secondary">Export PDF</button>
          </div>
        </div>

        <div v-else class="no-result">
          <span class="icon">📸</span>
          <p>Upload an image to begin observation</p>
        </div>
      </div>

      <div class="panel history-panel">
        <h3>Recent Scans</h3>
        <div class="history-list">
          <div v-for="scan in recentScans" :key="scan.id" class="history-item">
            <div class="scan-info">
              <span class="filename">{{ scan.filename }}</span>
              <span class="date">{{ scan.date }}</span>
            </div>
            <span :class="['status-badge', { 'has-anomalies': scan.anomalies }]">
              {{ scan.anomalies ? '⚠️ Anomalies' : '✓ Clear' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="notice">
      <p>This tool provides visual observations only — it does not assign quality grades. Use observations to inform your own assessment.</p>
    </div>
  </div>
</template>

<style scoped>
.defect-detection-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 300px 1fr 280px; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h4 { font-size: 0.875rem; color: #888; margin: 1rem 0 0.75rem; }

.upload-zone { border: 2px dashed #333; border-radius: 0.5rem; padding: 2rem; text-align: center; cursor: pointer; min-height: 180px; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }
.upload-zone:hover { border-color: #60a5fa; }
.upload-zone.has-image { padding: 0; border-style: solid; }
.preview-image { width: 100%; height: auto; border-radius: 0.375rem; }
.upload-placeholder .upload-icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }
.upload-placeholder .hint { font-size: 0.75rem; color: #666; }

.species-input { margin-bottom: 1rem; }
.species-input label { display: block; font-size: 0.75rem; color: #888; margin-bottom: 0.25rem; }
.species-input input { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }

.btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }
.btn-large { width: 100%; padding: 1rem; font-size: 1rem; }

.defect-types { margin-top: 1.5rem; }
.type-list { display: flex; flex-direction: column; gap: 0.5rem; }
.type-item { padding: 0.5rem; background: #262626; border-radius: 0.375rem; }
.type-name { display: block; font-size: 0.875rem; font-weight: 500; }
.type-desc { font-size: 0.75rem; color: #888; }

.analyzing { text-align: center; padding: 3rem; }
.spinner { width: 40px; height: 40px; border: 3px solid #333; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.scan-progress { height: 4px; background: #333; border-radius: 2px; overflow: hidden; margin-top: 1rem; }
.scan-line { width: 30%; height: 100%; background: #2563eb; animation: scan 1.5s ease-in-out infinite; }
@keyframes scan { 0% { transform: translateX(-100%); } 100% { transform: translateX(400%); } }

.error-display { text-align: center; padding: 2rem; background: #ef444420; border-radius: 0.5rem; }
.error-display .icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }
.error-display p { color: #ef4444; margin: 0 0 1rem; }

.no-result { text-align: center; padding: 3rem; color: #666; }
.no-result .icon { font-size: 3rem; display: block; margin-bottom: 1rem; }

.observation-summary { margin-bottom: 1.5rem; }
.summary-badges { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.badge { padding: 0.5rem 0.75rem; background: #22c55e20; color: #22c55e; border-radius: 0.375rem; font-size: 0.875rem; }
.badge.active { background: #f59e0b20; color: #f59e0b; }
.confidence-badge { padding: 0.5rem 0.75rem; background: #262626; color: #888; border-radius: 0.375rem; font-size: 0.75rem; text-transform: capitalize; }

.observation-section { margin-bottom: 1.5rem; padding: 1rem; background: #262626; border-radius: 0.5rem; }
.observation-section h4 { margin: 0 0 0.5rem; color: #60a5fa; }
.grain-estimate { font-size: 1.25rem; font-weight: 600; margin: 0; color: #e5e5e5; }
.observations-text { margin: 0; line-height: 1.6; white-space: pre-wrap; }

.result-actions { display: flex; gap: 0.75rem; margin-top: 1.5rem; }
.result-actions .btn { flex: 1; }

.history-list { display: flex; flex-direction: column; gap: 0.5rem; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: #262626; border-radius: 0.375rem; }
.scan-info { display: flex; flex-direction: column; }
.filename { font-size: 0.875rem; font-weight: 500; }
.date { font-size: 0.75rem; color: #888; }
.status-badge { font-size: 0.75rem; padding: 0.25rem 0.5rem; background: #22c55e20; color: #22c55e; border-radius: 0.25rem; }
.status-badge.has-anomalies { background: #f59e0b20; color: #f59e0b; }

.notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #262626; border-radius: 0.5rem; text-align: center; color: #888; border-left: 3px solid #60a5fa; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
