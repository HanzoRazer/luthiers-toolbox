<script setup lang="ts">
/**
 * WoodGradingView - AI-Powered Wood Quality Grading
 * Upload photos of wood stock for AI analysis and grading
 *
 * Connected to API endpoints:
 *   POST /api/ai/wood-grading/analyze
 *   GET  /api/ai/wood-grading/history
 */
import { ref } from 'vue'

const selectedFile = ref<File | null>(null)
const previewUrl = ref<string>('')
const isAnalyzing = ref(false)
const analysisResult = ref<{
  grade: string
  confidence: number
  characteristics: string[]
  recommendations: string[]
} | null>(null)

const recentAnalyses = ref([
  { id: 1, filename: 'sitka_top_001.jpg', grade: 'AAA', date: '2026-03-06', species: 'Sitka Spruce' },
  { id: 2, filename: 'rosewood_set_12.jpg', grade: 'AA', date: '2026-03-05', species: 'Indian Rosewood' },
  { id: 3, filename: 'maple_neck_03.jpg', grade: 'A', date: '2026-03-05', species: 'Hard Maple' },
])

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    selectedFile.value = input.files[0]
    previewUrl.value = URL.createObjectURL(input.files[0])
    analysisResult.value = null
  }
}

async function analyzeWood() {
  if (!selectedFile.value) return

  isAnalyzing.value = true
  // Simulated API call
  await new Promise(resolve => setTimeout(resolve, 2000))

  analysisResult.value = {
    grade: 'AAA',
    confidence: 94,
    characteristics: [
      'Tight, even grain pattern',
      'Excellent medullary rays',
      'No visible defects',
      'Optimal stiffness-to-weight ratio',
    ],
    recommendations: [
      'Ideal for classical guitar tops',
      'Suitable for fingerstyle instruments',
      'Premium-grade material',
    ],
  }
  isAnalyzing.value = false
}
</script>

<template>
  <div class="wood-grading-view">
    <div class="header">
      <h1>AI Wood Grading</h1>
      <p class="subtitle">Upload photos for instant tonewood quality analysis</p>
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
          <img v-if="previewUrl" :src="previewUrl" alt="Wood preview" class="preview-image" />
          <div v-else class="upload-placeholder">
            <span class="upload-icon">📷</span>
            <p>Click to upload wood photo</p>
            <p class="hint">JPG, PNG up to 10MB</p>
          </div>
        </div>

        <div class="guidelines">
          <h4>Photo Guidelines</h4>
          <ul>
            <li>Good lighting, avoid shadows</li>
            <li>Include the entire piece</li>
            <li>Show grain pattern clearly</li>
            <li>Include a size reference if possible</li>
          </ul>
        </div>

        <button
          class="btn btn-primary btn-large"
          @click="analyzeWood"
          :disabled="!selectedFile || isAnalyzing"
        >
          {{ isAnalyzing ? 'Analyzing...' : '🔍 Analyze Wood' }}
        </button>
      </div>

      <div class="panel results-panel">
        <h3>Analysis Results</h3>

        <div v-if="isAnalyzing" class="analyzing">
          <div class="spinner"></div>
          <p>AI is analyzing the wood grain...</p>
        </div>

        <div v-else-if="analysisResult" class="analysis-result">
          <div class="grade-display">
            <span class="grade-label">Grade</span>
            <span class="grade-value">{{ analysisResult.grade }}</span>
            <span class="confidence">{{ analysisResult.confidence }}% confidence</span>
          </div>

          <div class="result-section">
            <h4>Characteristics</h4>
            <ul>
              <li v-for="char in analysisResult.characteristics" :key="char">✓ {{ char }}</li>
            </ul>
          </div>

          <div class="result-section">
            <h4>Recommendations</h4>
            <ul>
              <li v-for="rec in analysisResult.recommendations" :key="rec">→ {{ rec }}</li>
            </ul>
          </div>

          <div class="result-actions">
            <button class="btn btn-secondary">Save to Library</button>
            <button class="btn btn-secondary">Export Report</button>
          </div>
        </div>

        <div v-else class="no-result">
          <span class="icon">🌲</span>
          <p>Upload a photo to begin analysis</p>
        </div>
      </div>

      <div class="panel history-panel">
        <h3>Recent Analyses</h3>
        <div class="history-list">
          <div v-for="item in recentAnalyses" :key="item.id" class="history-item">
            <div class="history-info">
              <span class="filename">{{ item.filename }}</span>
              <span class="species">{{ item.species }}</span>
            </div>
            <div class="history-meta">
              <span class="history-grade">{{ item.grade }}</span>
              <span class="date">{{ item.date }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full AI wood grading with species identification and defect detection coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.wood-grading-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 300px 1fr 280px; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h4 { font-size: 0.75rem; color: #888; margin: 1rem 0 0.5rem; }

.upload-zone { border: 2px dashed #333; border-radius: 0.5rem; padding: 2rem; text-align: center; cursor: pointer; min-height: 200px; display: flex; align-items: center; justify-content: center; }
.upload-zone:hover { border-color: #60a5fa; }
.upload-zone.has-image { padding: 0; border-style: solid; }
.preview-image { width: 100%; height: auto; border-radius: 0.375rem; }
.upload-placeholder .upload-icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }
.upload-placeholder .hint { font-size: 0.75rem; color: #666; }

.guidelines { margin: 1rem 0; }
.guidelines ul { padding-left: 1.5rem; margin: 0; }
.guidelines li { font-size: 0.875rem; color: #888; margin: 0.25rem 0; }

.btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; cursor: not-allowed; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }
.btn-large { width: 100%; padding: 1rem; font-size: 1rem; margin-top: 1rem; }

.analyzing { text-align: center; padding: 3rem; }
.spinner { width: 40px; height: 40px; border: 3px solid #333; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }

.no-result { text-align: center; padding: 3rem; color: #666; }
.no-result .icon { font-size: 3rem; display: block; margin-bottom: 1rem; }

.grade-display { text-align: center; padding: 2rem; background: #262626; border-radius: 0.5rem; margin-bottom: 1.5rem; }
.grade-label { display: block; font-size: 0.75rem; color: #888; text-transform: uppercase; }
.grade-value { display: block; font-size: 4rem; font-weight: 700; color: #22c55e; }
.confidence { font-size: 0.875rem; color: #888; }

.result-section { margin-bottom: 1.5rem; }
.result-section ul { padding-left: 1rem; margin: 0; }
.result-section li { font-size: 0.875rem; margin: 0.5rem 0; }

.result-actions { display: flex; gap: 0.75rem; }
.result-actions .btn { flex: 1; }

.history-list { display: flex; flex-direction: column; gap: 0.5rem; }
.history-item { display: flex; justify-content: space-between; padding: 0.75rem; background: #262626; border-radius: 0.375rem; }
.history-info { display: flex; flex-direction: column; }
.filename { font-size: 0.875rem; font-weight: 500; }
.species { font-size: 0.75rem; color: #888; }
.history-meta { text-align: right; }
.history-grade { display: block; font-weight: 600; color: #22c55e; }
.date { font-size: 0.75rem; color: #888; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
