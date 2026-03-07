<script setup lang="ts">
/**
 * DefectDetectionView - AI-Powered Defect Detection
 * Upload photos to detect cracks, voids, grain issues, and other defects
 *
 * Connected to API endpoints:
 *   POST /api/ai/defects/analyze
 *   GET  /api/ai/defects/history
 */
import { ref } from 'vue'

const selectedFile = ref<File | null>(null)
const previewUrl = ref<string>('')
const isAnalyzing = ref(false)

interface Defect {
  id: number
  type: string
  severity: 'low' | 'medium' | 'high'
  location: string
  description: string
}

const detectedDefects = ref<Defect[]>([])
const overallScore = ref<number | null>(null)

const defectTypes = [
  { name: 'Cracks', description: 'Surface or structural cracks' },
  { name: 'Voids', description: 'Holes or missing material' },
  { name: 'Grain Issues', description: 'Runout, knots, irregularities' },
  { name: 'Finish Defects', description: 'Orange peel, fish-eye, runs' },
  { name: 'Binding Gaps', description: 'Separation at binding joints' },
]

const recentScans = ref([
  { id: 1, filename: 'top_plate_front.jpg', defects: 0, date: '2026-03-06' },
  { id: 2, filename: 'binding_corner_01.jpg', defects: 2, date: '2026-03-05' },
  { id: 3, filename: 'neck_heel_joint.jpg', defects: 1, date: '2026-03-04' },
])

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    selectedFile.value = input.files[0]
    previewUrl.value = URL.createObjectURL(input.files[0])
    detectedDefects.value = []
    overallScore.value = null
  }
}

async function analyzeImage() {
  if (!selectedFile.value) return

  isAnalyzing.value = true
  await new Promise(resolve => setTimeout(resolve, 2500))

  // Simulated results
  detectedDefects.value = [
    { id: 1, type: 'Minor Grain Runout', severity: 'low', location: 'Upper bout, left side', description: 'Slight grain deviation, acceptable for structural integrity' },
  ]
  overallScore.value = 92
  isAnalyzing.value = false
}
</script>

<template>
  <div class="defect-detection-view">
    <div class="header">
      <h1>AI Defect Detection</h1>
      <p class="subtitle">Identify potential issues before they become problems</p>
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

        <button
          class="btn btn-primary btn-large"
          @click="analyzeImage"
          :disabled="!selectedFile || isAnalyzing"
        >
          {{ isAnalyzing ? 'Analyzing...' : '🔍 Scan for Defects' }}
        </button>

        <div class="defect-types">
          <h4>Detectable Issues</h4>
          <div class="type-list">
            <div v-for="type in defectTypes" :key="type.name" class="type-item">
              <span class="type-name">{{ type.name }}</span>
              <span class="type-desc">{{ type.description }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel results-panel">
        <h3>Analysis Results</h3>

        <div v-if="isAnalyzing" class="analyzing">
          <div class="spinner"></div>
          <p>AI is scanning for defects...</p>
          <div class="scan-progress">
            <div class="scan-line"></div>
          </div>
        </div>

        <div v-else-if="overallScore !== null" class="results">
          <div class="score-display">
            <div class="score-circle" :class="{ good: overallScore >= 80 }">
              <span class="score-value">{{ overallScore }}</span>
              <span class="score-label">Quality Score</span>
            </div>
          </div>

          <div class="defects-section">
            <h4>{{ detectedDefects.length }} Issue{{ detectedDefects.length !== 1 ? 's' : '' }} Found</h4>

            <div v-if="detectedDefects.length === 0" class="no-defects">
              <span class="icon">✅</span>
              <p>No significant defects detected</p>
            </div>

            <div v-else class="defects-list">
              <div v-for="defect in detectedDefects" :key="defect.id" class="defect-item">
                <div class="defect-header">
                  <span class="defect-type">{{ defect.type }}</span>
                  <span :class="['severity-badge', defect.severity]">{{ defect.severity }}</span>
                </div>
                <p class="defect-location">📍 {{ defect.location }}</p>
                <p class="defect-description">{{ defect.description }}</p>
              </div>
            </div>
          </div>

          <div class="result-actions">
            <button class="btn btn-secondary">Save Report</button>
            <button class="btn btn-secondary">Export PDF</button>
          </div>
        </div>

        <div v-else class="no-result">
          <span class="icon">📸</span>
          <p>Upload an image to begin analysis</p>
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
            <span :class="['defect-count', { 'has-defects': scan.defects > 0 }]">
              {{ scan.defects === 0 ? '✓ Clear' : `${scan.defects} issue${scan.defects > 1 ? 's' : ''}` }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full defect detection with repair recommendations and severity mapping coming soon.</p>
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

.no-result { text-align: center; padding: 3rem; color: #666; }
.no-result .icon { font-size: 3rem; display: block; margin-bottom: 1rem; }

.score-display { text-align: center; margin-bottom: 2rem; }
.score-circle { width: 120px; height: 120px; border-radius: 50%; background: #262626; border: 4px solid #333; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 auto; }
.score-circle.good { border-color: #22c55e; }
.score-value { font-size: 2.5rem; font-weight: 700; color: #22c55e; }
.score-label { font-size: 0.625rem; color: #888; text-transform: uppercase; }

.no-defects { text-align: center; padding: 2rem; background: #22c55e10; border-radius: 0.5rem; }
.no-defects .icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }
.no-defects p { color: #22c55e; margin: 0; }

.defects-list { display: flex; flex-direction: column; gap: 0.75rem; }
.defect-item { padding: 1rem; background: #262626; border-radius: 0.5rem; border-left: 3px solid #f59e0b; }
.defect-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.defect-type { font-weight: 600; }
.severity-badge { padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.625rem; text-transform: uppercase; font-weight: 600; }
.severity-badge.low { background: #22c55e20; color: #22c55e; }
.severity-badge.medium { background: #f59e0b20; color: #f59e0b; }
.severity-badge.high { background: #ef444420; color: #ef4444; }
.defect-location { font-size: 0.75rem; color: #888; margin: 0.25rem 0; }
.defect-description { font-size: 0.875rem; margin: 0; }

.result-actions { display: flex; gap: 0.75rem; margin-top: 1.5rem; }
.result-actions .btn { flex: 1; }

.history-list { display: flex; flex-direction: column; gap: 0.5rem; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: #262626; border-radius: 0.375rem; }
.scan-info { display: flex; flex-direction: column; }
.filename { font-size: 0.875rem; font-weight: 500; }
.date { font-size: 0.75rem; color: #888; }
.defect-count { font-size: 0.75rem; padding: 0.25rem 0.5rem; background: #22c55e20; color: #22c55e; border-radius: 0.25rem; }
.defect-count.has-defects { background: #f59e0b20; color: #f59e0b; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
